"""Analisi tecnica: livelli, dinamica, LUFS EBU R128, clipping, DC offset.

Porting dal toolkit originale (analyze.py) con refactor in funzioni piccole,
riusabili e testabili separatamente.
"""
from pathlib import Path
import subprocess
from typing import Any
import numpy as np

from . import config
from .utils import run_cmd, check_binary
from .locale_it import DIAGNOSI_CLIPPING_OK, DIAGNOSI_CLIPPING_KO, DIAGNOSI_DC_OK, DIAGNOSI_DC_KO


def compute_levels(y: np.ndarray, hop: int = config.HOP_LENGTH) -> dict:
    """Calcola peak, RMS, crest, dynamic_range e noise_floor stimati.

    Dynamic range: P95 - P10 dei frame RMS (in dB).
    Noise floor: P5 dei frame RMS (in dB).
    """
    import librosa
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    peak_db = 20 * np.log10(peak + 1e-12)
    rms = float(np.sqrt(np.mean(y ** 2))) if y.size else 0.0
    rms_db = 20 * np.log10(rms + 1e-12)
    crest_db = peak_db - rms_db

    frame_rms = librosa.feature.rms(y=y, frame_length=4096, hop_length=hop)[0]
    frame_rms_db = 20 * np.log10(frame_rms + 1e-12)
    dyn_range = float(np.percentile(frame_rms_db, 95) - np.percentile(frame_rms_db, 10))
    noise_floor = float(np.percentile(frame_rms_db, 5))

    return {
        "peak_dbfs": round(peak_db, 2),
        "rms_dbfs": round(rms_db, 2),
        "crest_db": round(crest_db, 2),
        "dynamic_range_db": round(dyn_range, 2),
        "noise_floor_db": round(noise_floor, 2),
    }


def compute_lufs(path: str | Path) -> dict:
    """Calcola Integrated LUFS, LRA, True Peak via ffmpeg ebur128.

    Porting da analyze.py::ebur128().
    """
    if not check_binary("ffmpeg"):
        return {"integrated_lufs": None, "lra": None, "true_peak_db": None, "error": "ffmpeg non disponibile"}

    r = run_cmd([
        "ffmpeg", "-nostats", "-i", str(path),
        "-filter_complex", "ebur128=peak=true",
        "-f", "null", "-",
    ])
    out = r.stderr
    info = {"integrated_lufs": None, "lra": None, "true_peak_db": None}
    if "Summary:" not in out:
        return info
    block = out.split("Summary:")[-1]
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("I:"):
            try:
                info["integrated_lufs"] = float(line.split()[1])
            except (IndexError, ValueError):
                pass
        elif line.startswith("LRA:"):
            try:
                info["lra"] = float(line.split()[1])
            except (IndexError, ValueError):
                pass
        elif line.startswith("Peak:"):
            try:
                info["true_peak_db"] = float(line.split()[1])
            except (IndexError, ValueError):
                pass
    return info


def detect_clipping(y: np.ndarray, threshold: float = config.CLIPPING_THRESHOLD) -> dict:
    clipped = int(np.sum(np.abs(y) >= threshold))
    total = int(y.size)
    pct = 100.0 * clipped / max(total, 1)
    verdict = DIAGNOSI_CLIPPING_KO if pct > 0.001 else DIAGNOSI_CLIPPING_OK
    return {
        "samples": clipped,
        "total_samples": total,
        "pct": round(pct, 6),
        "threshold": threshold,
        "verdict": verdict,
    }


def detect_dc_offset(y: np.ndarray, threshold: float = config.DC_OFFSET_THRESHOLD) -> dict:
    dc = float(np.mean(y)) if y.size else 0.0
    verdict = DIAGNOSI_DC_KO if abs(dc) > threshold else DIAGNOSI_DC_OK
    return {
        "offset": round(dc, 6),
        "threshold": threshold,
        "verdict": verdict,
    }


def technical_summary(path: str | Path, y: np.ndarray) -> dict:
    """Orchestrazione: chiama levels + lufs + clipping + DC e ritorna tutto insieme."""
    levels = compute_levels(y)
    lufs = compute_lufs(path)
    clip = detect_clipping(y)
    dc = detect_dc_offset(y)
    return {
        "levels": levels,
        "lufs": lufs,
        "clipping": clip,
        "dc_offset": dc,
    }
