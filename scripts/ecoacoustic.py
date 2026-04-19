"""Indici ecoacustici standard dell'ecoacustica.

Implementazione diretta delle formule per evitare la dipendenza scikit-maad
(manutenzione bassa) e per tenere il controllo sui parametri.

Indici implementati:
- ACI (Acoustic Complexity Index) - Pieretti, Farina, Morri 2011
- NDSI (Normalized Difference Soundscape Index) - Kasten, Gage, Fox, Joo 2012
- H (Acoustic Entropy) - Sueur, Aide, Pavoine 2008 (H temporale + H spettrale)
- BI (Bioacoustic Index) - Boelman, Asner, Hart, Martin 2007
- ADI (Acoustic Diversity Index) / AEI (Acoustic Evenness Index) - Villanueva-Rivera et al. 2011
"""
from typing import Any
import numpy as np

from . import config


def compute_aci(
    y: np.ndarray,
    sr: int,
    j_seconds: float = 5.0,
    min_freq: float = 2000,
    max_freq: float = 8000,
    n_fft: int = 2048,
) -> float:
    """Acoustic Complexity Index (Pieretti et al. 2011).

    Somma della variazione assoluta del contenuto spettrale tra frame
    successivi, normalizzata. Valori alti indicano complessità spettro-temporale
    (es. canti di uccelli), valori bassi rumore costante.
    """
    import librosa
    hop = n_fft // 2
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    band_mask = (freqs >= min_freq) & (freqs <= max_freq)
    if not band_mask.any():
        return 0.0
    Sb = S[band_mask, :]

    frames_per_j = max(int(j_seconds * sr / hop), 2)
    n_frames = Sb.shape[1]
    aci_total = 0.0
    for start in range(0, n_frames, frames_per_j):
        end = min(start + frames_per_j, n_frames)
        block = Sb[:, start:end]
        if block.shape[1] < 2:
            continue
        diff = np.abs(np.diff(block, axis=1))
        sums = np.sum(block[:, :-1], axis=1) + 1e-12
        D = np.sum(diff, axis=1)
        aci_total += float(np.sum(D / sums))
    return round(aci_total, 2)


def compute_ndsi(
    y: np.ndarray,
    sr: int,
    antro_band: tuple[float, float] = config.ECO_ANTHROPOPHONY_BAND,
    bio_band: tuple[float, float] = config.ECO_BIOPHONY_BAND,
    n_fft: int = 2048,
) -> dict:
    """NDSI (Kasten et al. 2012).

    Rapporto: (Biophony - Anthropophony) / (Biophony + Anthropophony)
    Intervallo -1 (solo antropofonia) a +1 (solo biofonia).
    """
    import librosa
    psd = np.mean(np.abs(librosa.stft(y, n_fft=n_fft, hop_length=n_fft // 2)) ** 2, axis=1)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    def band_energy(lo: float, hi: float) -> float:
        mask = (freqs >= lo) & (freqs < hi)
        return float(np.sum(psd[mask]))
    A = band_energy(*antro_band)
    B = band_energy(*bio_band)
    denom = A + B + 1e-12
    ndsi = (B - A) / denom
    return {
        "ndsi": round(ndsi, 3),
        "biophony_energy": round(B, 3),
        "anthropophony_energy": round(A, 3),
        "biophony_band_hz": list(bio_band),
        "anthropophony_band_hz": list(antro_band),
    }


def compute_entropy_h(y: np.ndarray, sr: int, n_fft: int = 2048) -> dict:
    """Acoustic Entropy (Sueur et al. 2008).

    H = Ht * Hf dove Ht è entropia temporale dell'envelope e Hf entropia
    spettrale della PSD media. Normalizzate a [0, 1]. H alto = "complessità"
    uniformemente distribuita.
    """
    import librosa

    # Entropia temporale (envelope di Hilbert normalizzato)
    env = np.abs(y)
    env_sum = np.sum(env) + 1e-12
    p_t = env / env_sum
    H_t = -np.sum(p_t * np.log2(p_t + 1e-12))
    H_t_norm = float(H_t / np.log2(len(env)))

    # Entropia spettrale (PSD media normalizzata)
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=n_fft // 2))
    psd = np.mean(S ** 2, axis=1)
    psd_sum = np.sum(psd) + 1e-12
    p_f = psd / psd_sum
    H_f = -np.sum(p_f * np.log2(p_f + 1e-12))
    H_f_norm = float(H_f / np.log2(len(psd)))

    H = H_t_norm * H_f_norm
    return {
        "h_total": round(H, 4),
        "h_temporal": round(H_t_norm, 4),
        "h_spectral": round(H_f_norm, 4),
    }


def compute_bioacoustic_index(
    y: np.ndarray, sr: int, lo: float = 2000, hi: float = 8000, n_fft: int = 2048
) -> float:
    """Bioacoustic Index (Boelman et al. 2007).

    Area sotto lo spettro nella banda biofonica (2-8 kHz), normalizzata
    rispetto al minimo della banda stessa.
    """
    import librosa
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=n_fft // 2))
    spectrum_db = 10 * np.log10(np.mean(S ** 2, axis=1) + 1e-12)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    mask = (freqs >= lo) & (freqs <= hi)
    if not mask.any():
        return 0.0
    band = spectrum_db[mask]
    bi = float(np.sum(band - band.min()))
    return round(bi, 2)


def compute_adi_aei(
    y: np.ndarray,
    sr: int,
    max_freq: float = 10000,
    db_threshold: float = -50.0,
    freq_step: float = 1000.0,
    n_fft: int = 2048,
) -> dict:
    """ADI e AEI (Villanueva-Rivera et al. 2011).

    Divide lo spettro in bande da freq_step Hz, calcola per ognuna la frazione
    di energia sopra db_threshold rispetto al massimo, applica entropia di
    Shannon (ADI) e indice di Gini (AEI).
    """
    import librosa
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=n_fft // 2))
    spec_db = 10 * np.log10(np.mean(S ** 2, axis=1) + 1e-12)
    spec_db = spec_db - np.max(spec_db)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    max_f = min(max_freq, sr / 2)
    band_edges = np.arange(0, max_f + freq_step, freq_step)
    proportions = []
    for lo, hi in zip(band_edges[:-1], band_edges[1:]):
        mask = (freqs >= lo) & (freqs < hi)
        if not mask.any():
            proportions.append(0.0)
            continue
        above = np.sum(spec_db[mask] > db_threshold)
        total = mask.sum()
        proportions.append(above / max(total, 1))

    p = np.array(proportions)
    p_sum = p.sum() + 1e-12
    p_norm = p / p_sum
    # ADI = Shannon entropy
    p_nz = p_norm[p_norm > 0]
    adi = float(-np.sum(p_nz * np.log(p_nz))) if p_nz.size else 0.0
    # AEI = Gini coefficient
    sorted_p = np.sort(p_norm)
    n = len(sorted_p)
    cum = np.cumsum(sorted_p)
    if n > 0 and cum[-1] > 0:
        aei = float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)
    else:
        aei = 0.0

    return {
        "adi": round(adi, 4),
        "aei": round(aei, 4),
        "bands_count": len(proportions),
        "freq_step_hz": freq_step,
        "db_threshold": db_threshold,
    }


def _ecoacoustic_summary_legacy(y: np.ndarray, sr: int, extended: bool = False) -> dict:
    """Implementazione custom storica (indici ricalcolati a mano dalle formule
    originali Pieretti/Kasten/Sueur/Boelman/Villanueva-Rivera). Restituisce
    dict con chiavi {aci, ndsi, h_entropy, bi, adi_aei?}."""
    out = {
        "aci": compute_aci(y, sr),
        "ndsi": compute_ndsi(y, sr),
        "h_entropy": compute_entropy_h(y, sr),
        "bi": compute_bioacoustic_index(y, sr),
    }
    if extended:
        out["adi_aei"] = compute_adi_aei(y, sr)
    return out


def ecoacoustic_summary(y: np.ndarray, sr: int, extended: bool = False,
                        backend: str | None = None) -> dict:
    """Orchestrazione: calcola tutti gli indici principali.

    Se `extended=True` include ADI/AEI (più costosi).

    Il parametro `backend` (v0.9.0 Step A) seleziona l'implementazione:
    - None (default): usa `config.ECO_BACKEND` ("legacy" fino a v0.9.x).
    - "legacy": implementazione custom storica.
    - "maad": thin wrapper su scikit-maad (Ulloa et al. 2021).

    L'API pubblica (chiavi del dict risultato) e' identica fra i backend. Il
    flag `--ecoacoustic-backend` del CLI permette di selezionare runtime.
    Il flip del default a "maad" avverra' in v0.10.0 se il parity test passa.
    """
    chosen = backend or config.ECO_BACKEND
    if chosen == "maad":
        from .ecoacoustic_maad import ecoacoustic_summary_maad
        return ecoacoustic_summary_maad(y, sr, extended=extended)
    return _ecoacoustic_summary_legacy(y, sr, extended=extended)
