"""Hum check con baseline locale, canonico.

Porting integrale da ~/audio-analyzer/hum_and_timeline.py::hum_analysis().

Lezione critica appresa su Villa Ficana: la baseline DEVE essere locale,
calcolata come mediana nelle bande 30-45 e 70-95 Hz, non globale sullo
spettro. Le versioni globali producono falsi positivi su sorgenti tonali.
"""
from pathlib import Path
from typing import Any
import numpy as np

from . import config
from .locale_it import verdetto_hum


def hum_check(
    path: str | Path,
    sr_target: int = config.SR_HUM,
    n_fft: int = config.N_FFT_HUM,
    targets_hz: list[int] | None = None,
    bandwidth_hz: float = config.HUM_PEAK_BW,
) -> dict:
    """Analisi mirata delle frequenze di rete elettrica e loro armoniche.

    FFT ad alta risoluzione, baseline LOCALE nelle bande 30-45 e 70-95 Hz.
    """
    import librosa

    y, sr = librosa.load(str(path), sr=sr_target, mono=True)
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=n_fft // 4))
    spectrum = np.mean(S, axis=1)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    bin_hz = float(freqs[1] - freqs[0])

    # Baseline LOCALE (non globale)
    base_mask = np.zeros_like(freqs, dtype=bool)
    for lo, hi in config.HUM_BASELINE_BANDS:
        base_mask |= (freqs >= lo) & (freqs <= hi)
    baseline = float(np.median(spectrum[base_mask])) if base_mask.any() else 0.0
    baseline_db = 20 * np.log10(baseline + 1e-12)

    if targets_hz is None:
        targets_hz = list(config.HUM_TARGET_HZ)

    def peak_at(target: float, half_bw: float = bandwidth_hz):
        mask = (freqs >= target - half_bw) & (freqs <= target + half_bw)
        if not mask.any():
            return None, 0.0
        idx = np.where(mask)[0]
        local = spectrum[idx]
        i = idx[int(np.argmax(local))]
        return float(freqs[i]), float(spectrum[i])

    peaks = []
    for f0 in targets_hz:
        f_exact, magnitude = peak_at(f0)
        if f_exact is None:
            continue
        ratio = magnitude / (baseline + 1e-12)
        ratio_db = 20 * np.log10(ratio + 1e-12)
        peaks.append({
            "target_hz": int(f0),
            "found_hz": round(f_exact, 2),
            "magnitude_db": round(20 * np.log10(magnitude + 1e-12), 2),
            "ratio": round(ratio, 2),
            "ratio_db": round(ratio_db, 2),
            "verdict": verdetto_hum(ratio_db),
        })

    overall = _aggregate_verdict(peaks)

    return {
        "sr_target": sr,
        "n_fft": n_fft,
        "bin_hz": round(bin_hz, 3),
        "baseline_db": round(baseline_db, 2),
        "baseline_bands": config.HUM_BASELINE_BANDS,
        "peaks": peaks,
        "overall_verdict": overall,
    }


def _aggregate_verdict(peaks: list[dict]) -> str:
    """Verdetto complessivo: prende il massimo dei verdetti su 50 Hz + armoniche
    e 60 Hz + armoniche. Il più severo vince.
    """
    if not peaks:
        return "trascurabile"
    order = {"trascurabile": 0, "presente": 1, "forte": 2}
    worst = max((p["verdict"] for p in peaks), key=lambda v: order.get(v, 0))
    return worst
