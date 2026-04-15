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


def compute_timbre(y: np.ndarray, sr: int) -> dict:
    """Centroide, rolloff, flatness, ZCR."""
    import librosa
    cent = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)))
    flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))
    return {
        "spectral_centroid_hz": round(cent, 1),
        "spectral_rolloff_hz": round(rolloff, 1),
        "spectral_flatness": round(flatness, 4),
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
    import librosa
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units="time")
    count = int(len(onsets))
    density = count / max(duration_s, 1e-6)
    return {
        "events_count": count,
        "events_per_sec": round(density, 3),
        "density_label": categoria_densita(density),
    }


def hifi_lofi_score(dynamic_range_db: float, flatness: float) -> dict:
    label, score = categoria_hifi(dynamic_range_db, flatness)
    return {"label": label, "score_5": score}


def spectral_summary(y: np.ndarray, sr: int, duration_s: float) -> dict:
    """Orchestrazione: ritorna bande + timbre + peaks + onset + hifi_lofi."""
    S, spectrum, freqs = compute_stft_mean(y, sr)
    bands = compute_bands(spectrum, freqs, sr)
    timbre = compute_timbre(y, sr)
    peaks = top_peaks(spectrum, freqs)
    onset = onset_analysis(y, sr, duration_s)
    return {
        "bands_schafer": bands,
        "timbre": timbre,
        "top_peaks_hz": peaks,
        "onsets": onset,
    }
