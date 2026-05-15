"""Distinzione parlato diretto vs mediato (v0.12.6, P1 caso A).

Quando PANNs marca Speech come dominante in una sezione, la skill non distingue
voce in scena (microfono in presa diretta) da voce mediata (TV in stanza
adiacente, radio, telefono, altoparlante PA). La differenza e' cruciale per
l'inferenza di ambientazione: parlato diretto = persona in scena, parlato
mediato = apparecchio domestico o PA, persona NON necessariamente presente.

Driver: caso A 15/05/2026, primi 30 s del file letti come "soglia
domestica" (qualcuno arriva e parla) mentre erano un telegiornale TV
nell'altra stanza filtrato dalla parete del bagno.

Approccio: euristica deterministica numpy/librosa su 4 feature spettrali
del segmento di Speech, con override su override PANNs label `Television`,
`Radio`, `Telephone bell ringing`, `Loudspeaker` quando presenti nei
top-10 globali.
"""
from __future__ import annotations
from typing import Any
import numpy as np

from . import config


# Label AudioSet (PANNs) che testimoniano in modo diretto una mediazione:
# se la skill le rileva nei top-10 globali, override automatico a 'mediated'.
PANNS_MEDIATED_LABELS = {
    "Television",
    "Radio",
    "Telephone",
    "Telephone bell ringing",
    "Telephone dialing, DTMF",
    "Loudspeaker",
    "Public address system",
    "Mechanical fan",  # spesso copre TV/radio in stanza adiacente
}


def _segment_rolloff_85(segment: np.ndarray, sr: int) -> float:
    """Frequenza al 85% dell'energia cumulata. Parlato diretto in stanza
    piccola ha rolloff ~5-8 kHz (consonanti aspirate). Parlato TV filtrato
    da parete crolla sotto 3-4 kHz."""
    import librosa
    # mean across frames per robustezza su segmenti non-stazionari
    rolloff = librosa.feature.spectral_rolloff(y=segment, sr=sr, roll_percent=0.85)
    return float(np.mean(rolloff))


def _shoulder_slope_db(segment: np.ndarray, sr: int) -> float:
    """Pendenza in dB/ottava fra 2.5 kHz e 5 kHz. Parlato filtrato da parete
    perde 6-12 dB/ottava in piu' rispetto a parlato secco. Valore in dB
    (negativo = decay verso l'alto = filtro passa-basso indotto)."""
    import librosa
    n_fft = 4096
    stft = np.abs(librosa.stft(segment, n_fft=n_fft, hop_length=n_fft // 4))
    spectrum = np.mean(stft, axis=1)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    # Energy mediana fra 2.0-3.0 kHz vs 4.0-5.0 kHz (octave-like step)
    mask_lo = (freqs >= 2000) & (freqs < 3000)
    mask_hi = (freqs >= 4000) & (freqs < 5000)
    if not mask_lo.any() or not mask_hi.any():
        return 0.0
    e_lo = float(np.mean(spectrum[mask_lo] ** 2)) + 1e-12
    e_hi = float(np.mean(spectrum[mask_hi] ** 2)) + 1e-12
    return float(10 * np.log10(e_hi / e_lo))


def _hnr_proxy(segment: np.ndarray, sr: int) -> float:
    """Proxy di Harmonic-to-Noise Ratio in dB. Usa la varianza dei chroma
    come surrogato della struttura armonica. Parlato secco ha HNR > 10 dB,
    parlato mediato/distante ha HNR < 5 dB.

    Implementazione semplificata: rapporto energia bande [200-1000Hz] (armonica
    formant region) vs [4000-8000Hz] (rumore di canale + aspirate). Valore in
    dB positivo grande = molta voce strutturata, piccolo o negativo = molto
    rumore di canale.
    """
    import librosa
    n_fft = 4096
    stft = np.abs(librosa.stft(segment, n_fft=n_fft, hop_length=n_fft // 4))
    spectrum = np.mean(stft, axis=1)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    mask_voice = (freqs >= 200) & (freqs < 1000)
    mask_noise = (freqs >= 4000) & (freqs < 8000)
    if not mask_voice.any() or not mask_noise.any():
        return 0.0
    e_v = float(np.mean(spectrum[mask_voice] ** 2)) + 1e-12
    e_n = float(np.mean(spectrum[mask_noise] ** 2)) + 1e-12
    return float(10 * np.log10(e_v / e_n))


def _stationarity_score(segment: np.ndarray, sr: int) -> float:
    """Misura la stazionarietà del segmento. Parlato TV/radio (telegiornale)
    ha presenza continua, parlato in presa diretta ha pause respiratorie
    naturali.

    Ritorna 0-1: 0 = molto variabile (pause/onset), 1 = molto stazionario
    (continuo). Calcola la varianza normalizzata dell'RMS su frame di 100ms.
    """
    frame_samples = int(0.1 * sr)
    if len(segment) < frame_samples * 4:
        return 0.5
    frames = []
    for i in range(0, len(segment) - frame_samples, frame_samples):
        frame = segment[i:i + frame_samples]
        rms = float(np.sqrt(np.mean(frame ** 2)) + 1e-12)
        frames.append(rms)
    frames = np.array(frames)
    mean = float(np.mean(frames))
    if mean < 1e-9:
        return 0.5
    cv = float(np.std(frames) / mean)
    # Coefficient of variation: 0.0 = stazionario, > 1.0 = molto variabile
    # Normalizziamo: 1.0 = stazionario (cv vicino a 0), 0.0 = variabile (cv >= 1)
    return float(max(0.0, min(1.0, 1.0 - cv)))


def classify_speech_mediation(
    waveform: np.ndarray,
    sr: int,
    classifier_result: dict | None = None,
    flatness: float = 0.0,
) -> dict:
    """Classifica un segmento di parlato come `direct`, `mediated`, `uncertain`.

    Strategia:
    1. Override PANNs: se nei top-10 globali compare una label in
       `PANNS_MEDIATED_LABELS` con score >= 0.05, ritorna `mediated` con
       confidence high.
    2. Su materiale molto trasformato (flatness > 0.3) la distinzione non
       ha senso: ritorna `uncertain`.
    3. Altrimenti applica euristica spettrale composita su 4 feature:
       rolloff_85, shoulder_slope_db, hnr_proxy, stationarity_score.

    Returns
    -------
    dict con keys:
        label: 'direct' | 'mediated' | 'uncertain'
        confidence: 'high' | 'medium' | 'low'
        features: dict con valori delle 4 feature
        reason: stringa di motivazione
    """
    # 1. Override PANNs
    if classifier_result:
        top_global = (classifier_result.get("top_global") or [])[:10]
        for entry in top_global:
            name = entry.get("name", "")
            score = float(entry.get("score", 0) or 0)
            if name in PANNS_MEDIATED_LABELS and score >= 0.05:
                return {
                    "label": "mediated",
                    "confidence": "high",
                    "features": {},
                    "reason": f"PANNs label '{name}' (score {score:.3f}) testimonia mediazione tecnologica",
                }

    # 2. Materiale molto trasformato
    if flatness > 0.3:
        return {
            "label": "uncertain",
            "confidence": "low",
            "features": {"flatness": round(flatness, 4)},
            "reason": "materiale ad alta flatness (>0.3): possibile trasformazione acusmatica, distinzione direct/mediated non significativa",
        }

    # 3. Euristica spettrale
    rolloff = _segment_rolloff_85(waveform, sr)
    shoulder = _shoulder_slope_db(waveform, sr)
    hnr = _hnr_proxy(waveform, sr)
    stat = _stationarity_score(waveform, sr)

    # Scoring composito (somma di indicatori binari, max 4)
    # Ciascun indicatore vale +1 verso 'mediated', -1 verso 'direct'
    score = 0
    reasons = []
    # Rolloff basso = filtro acustico (parete, speaker piccolo)
    if rolloff < 3500:
        score += 1
        reasons.append(f"rolloff 85% basso ({rolloff:.0f} Hz)")
    elif rolloff > 5500:
        score -= 1
        reasons.append(f"rolloff 85% alto ({rolloff:.0f} Hz)")
    # Shoulder slope negativo grande = decay marcato verso l'alto
    if shoulder < -6.0:
        score += 1
        reasons.append(f"decay 2.5-5 kHz pronunciato ({shoulder:.1f} dB)")
    elif shoulder > -2.0:
        score -= 1
        reasons.append(f"decay 2.5-5 kHz lieve ({shoulder:.1f} dB)")
    # HNR proxy basso = rumore di canale prevalente
    if hnr < 5.0:
        score += 1
        reasons.append(f"struttura armonica debole (HNR proxy {hnr:.1f} dB)")
    elif hnr > 12.0:
        score -= 1
        reasons.append(f"struttura armonica forte (HNR proxy {hnr:.1f} dB)")
    # Stazionarieta alta = telegiornale, broadcast continuo
    if stat > 0.75:
        score += 1
        reasons.append(f"continuita alta (stazionarieta {stat:.2f})")
    elif stat < 0.4:
        score -= 1
        reasons.append(f"pause respiratorie marcate (stazionarieta {stat:.2f})")

    if score >= 2:
        label = "mediated"
        confidence = "high" if score >= 3 else "medium"
    elif score <= -2:
        label = "direct"
        confidence = "high" if score <= -3 else "medium"
    else:
        label = "uncertain"
        confidence = "low"

    return {
        "label": label,
        "confidence": confidence,
        "features": {
            "rolloff_85_hz": round(rolloff, 1),
            "shoulder_slope_2_5_to_5_khz_db": round(shoulder, 2),
            "hnr_proxy_db": round(hnr, 2),
            "stationarity_score": round(stat, 3),
        },
        "reason": "; ".join(reasons) if reasons else "indicatori spettrali ambigui",
    }


def speech_mediation_summary(
    waveform: np.ndarray,
    sr: int,
    summary: dict,
    speech_threshold_pct: float = 5.0,
) -> dict:
    """Pipeline-level wrapper. Decide se applicare la classificazione e su
    quali porzioni del file.

    Strategia: se PANNs top_dominant_frames contiene Speech con pct >=
    `speech_threshold_pct`, applica `classify_speech_mediation` (a) sul file
    intero come stima globale e (b) sui frame Speech-dominanti come stima
    localizzata. Altrimenti ritorna `{enabled: False, reason: ...}`.
    """
    classifier = (summary.get("semantic", {}) or {}).get("classifier", {}) or {}
    dom_frames = classifier.get("top_dominant_frames", []) or []

    speech_pct = 0.0
    for entry in dom_frames:
        if entry.get("name") == "Speech":
            speech_pct = float(entry.get("pct", 0) or 0)
            break

    if speech_pct < speech_threshold_pct:
        return {
            "enabled": False,
            "reason": f"PANNs Speech dominante presente in solo il {speech_pct:.1f}% dei frame (soglia {speech_threshold_pct:.1f}%)",
        }

    timbre = (summary.get("spectral", {}) or {}).get("timbre", {}) or {}
    flatness = float(timbre.get("spectral_flatness", 0) or 0)

    global_result = classify_speech_mediation(
        waveform, sr, classifier_result=classifier, flatness=flatness,
    )

    return {
        "enabled": True,
        "speech_dominant_pct": speech_pct,
        "global": global_result,
    }
