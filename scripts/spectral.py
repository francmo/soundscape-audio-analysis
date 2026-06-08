"""Analisi spettrale: STFT, bande Schafer, feature timbriche, onset density.

Porting da ~/audio-analyzer/analyze.py refactor in funzioni piccole.
"""
from typing import Any
import numpy as np

from . import config
from .locale_it import categoria_hifi, categoria_densita


def compute_stft_mean(y: np.ndarray, sr: int, n_fft: int = config.N_FFT_ANALYSIS, hop: int = config.HOP_LENGTH):
    import librosa
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop))
    spectrum = np.mean(S, axis=1)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    return S, spectrum, freqs


def compute_bands(spectrum: np.ndarray, freqs: np.ndarray, sr: int) -> dict:
    """Distribuzione energia nelle 7 bande Schafer."""
    bands = {}
    total_e = float(np.sum(spectrum ** 2)) + 1e-12
    for name, lo, hi in config.SCHAFER_BANDS:
        hi_cap = min(hi, sr / 2)
        mask = (freqs >= lo) & (freqs < hi_cap)
        e = float(np.sum(spectrum[mask] ** 2))
        bands[name] = {
            "range_hz": [lo, round(hi_cap, 1)],
            "energy_pct": round(100 * e / total_e, 2),
            "energy_db": round(10 * np.log10(max(e / total_e, 1e-12)), 2),
        }
    return bands


def _spectral_flux(y: np.ndarray) -> float:
    """Spectral flux rettificato (half-wave), media sui frame STFT.

    Norma L2 delle differenze positive di magnitudine fra frame STFT
    consecutivi (default librosa n_fft=2048, hop=512). Misura quanto lo
    spettro cambia istante per istante: instabilita', attrito, onset.
    Ritorna 0.0 se il segnale ha meno di due frame.
    """
    import librosa
    S = np.abs(librosa.stft(y))
    if S.shape[1] < 2:
        return 0.0
    diff = np.diff(S, axis=1)
    diff[diff < 0] = 0.0
    flux_frames = np.sqrt(np.sum(diff ** 2, axis=0))
    return float(np.mean(flux_frames))


def compute_timbre(y: np.ndarray, sr: int) -> dict:
    """Centroide, spread, rolloff, flatness, flux, ZCR.

    spread = ampiezza di banda attorno al centroide (secondo momento,
    librosa.feature.spectral_bandwidth). flux = flusso spettrale
    rettificato (vedi _spectral_flux). Tutte le feature usano i default
    librosa (n_fft=2048, hop=512) per coerenza reciproca.
    """
    import librosa
    cent = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    spread = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
    rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)))
    flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))
    flux = _spectral_flux(y)
    return {
        "spectral_centroid_hz": round(cent, 1),
        "spectral_spread_hz": round(spread, 1),
        "spectral_rolloff_hz": round(rolloff, 1),
        "spectral_flatness": round(flatness, 4),
        "spectral_flux": round(flux, 4),
        "zero_crossing_rate": round(zcr, 4),
    }


def top_peaks(spectrum: np.ndarray, freqs: np.ndarray, k: int = 5, dedup_hz: float = 50.0) -> list[dict]:
    """Trova le k frequenze con magnitudine più alta, con dedup entro dedup_hz."""
    smooth = np.convolve(spectrum, np.ones(5) / 5, mode="same")
    idx_sorted = np.argsort(smooth)[-50:][::-1]
    seen: list[float] = []
    out: list[dict] = []
    for i in idx_sorted:
        f = float(freqs[i])
        if any(abs(f - s) < dedup_hz for s in seen):
            continue
        seen.append(f)
        out.append({
            "freq_hz": round(f, 1),
            "magnitude": float(smooth[i]),
            "magnitude_db": round(20 * np.log10(smooth[i] + 1e-12), 2),
        })
        if len(out) >= k:
            break
    return out


def onset_analysis(y: np.ndarray, sr: int, duration_s: float) -> dict:
    """Rileva onset e ritorna conteggi, densità, **lista di timestamp**
    (v0.12.6, P4 caso A).

    La lista `events_times_s` permette alla narrative di citare onset puntuali
    rilevanti senza dover ricalcolare l'onset detection. Capata a 200 elementi
    per evitare payload enormi su file molto densi (dawn chorus, mercato).
    """
    import librosa
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units="time")
    count = int(len(onsets))
    density = count / max(duration_s, 1e-6)
    times = [round(float(t), 2) for t in onsets[:200]]
    return {
        "events_count": count,
        "events_per_sec": round(density, 3),
        "density_label": categoria_densita(density),
        "events_times_s": times,
    }


def hifi_lofi_score(dynamic_range_db: float, flatness: float) -> dict:
    label, score = categoria_hifi(dynamic_range_db, flatness)
    return {"label": label, "score_5": score}


def compute_bands_schafer_alert(bands: dict,
                                  threshold_pct: float = None) -> dict | None:
    """v0.13.0 (Intervento B dossier P&T): rileva concentrazione spettrale
    anomala nelle basse e ritorna un warning interpretativo.

    Quando la somma delle bande Sub-bass + Bass supera la soglia (default
    60%), e' plausibile artefatto di handling/microfono mobile/vibrazione
    del piano d'appoggio, oppure DC offset basso non corretto. La skill
    riporta il warning ma non modifica i numeri sottostanti: l'interpretazione
    finale resta del lettore (puo' essere artefatto, oppure contenuto basso
    significativo come tuono lontano o motore).

    Driver caso scuola: B iPhone 8 tenuto in mano e poi appoggiato,
    Sub-bass 41.48% + Bass 40.66% = 82.14%, su soundscape urbano dominato da
    voci dove il contenuto basso non e' percettivamente significativo.

    Ritorna None se sotto soglia. Soglia configurabile via
    config.BANDS_SCHAFER_ALERT_LOW_SUM_PCT.
    """
    if threshold_pct is None:
        threshold_pct = config.BANDS_SCHAFER_ALERT_LOW_SUM_PCT
    sub_bass = ((bands.get("Sub-bass") or {}).get("energy_pct") or 0.0)
    bass = ((bands.get("Bass") or {}).get("energy_pct") or 0.0)
    low_sum = float(sub_bass) + float(bass)
    if low_sum < threshold_pct:
        return None
    return {
        "level": "warning",
        "low_sum_pct": round(low_sum, 2),
        "threshold_pct": threshold_pct,
        "message": (
            f"Distribuzione spettrale dominata dal sub-bass+bass ({low_sum:.1f}%): "
            "plausibile artefatto di handling/microfono mobile/vibrazione del "
            "piano d'appoggio, oppure DC offset basso non corretto. Verificare "
            "in cuffia se il contenuto basso e' percettivamente significativo, "
            "altrimenti applicare high-pass a 80-120 Hz in post."
        ),
    }


def spectral_summary(y: np.ndarray, sr: int, duration_s: float) -> dict:
    """Orchestrazione: ritorna bande + timbre + peaks + onset + hifi_lofi
    + bands_alert (v0.13.0).
    """
    S, spectrum, freqs = compute_stft_mean(y, sr)
    bands = compute_bands(spectrum, freqs, sr)
    timbre = compute_timbre(y, sr)
    peaks = top_peaks(spectrum, freqs)
    onset = onset_analysis(y, sr, duration_s)
    alert = compute_bands_schafer_alert(bands)
    return {
        "bands_schafer": bands,
        "bands_schafer_alert": alert,
        "timbre": timbre,
        "top_peaks_hz": peaks,
        "onsets": onset,
    }
