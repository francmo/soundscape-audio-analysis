"""Analisi multicanale: per-canale + downmix, con identificazione del layout.

Gestisce fino a 7.1.4 (12 canali). Oltre, usa etichette generiche ChN.
"""
from typing import Any
import numpy as np

from . import config
from .io_loader import channel_label
from .technical import compute_levels
from .spectral import compute_stft_mean, compute_bands, compute_timbre


def analyze_channels(channels: list[np.ndarray], sr: int, layout: str) -> list[dict]:
    """Esegue analisi tecnica + spettrale (leggera) su ciascun canale."""
    results: list[dict] = []
    for idx, ch in enumerate(channels):
        label = channel_label(idx, layout)
        if ch.size == 0:
            results.append({"index": idx, "label": label, "empty": True})
            continue
        levels = compute_levels(ch)
        _S, spectrum, freqs = compute_stft_mean(ch, sr)
        bands = compute_bands(spectrum, freqs, sr)
        timbre = compute_timbre(ch, sr)
        dominant = max(bands.items(), key=lambda kv: kv[1]["energy_pct"])[0]
        results.append({
            "index": idx,
            "label": label,
            "levels": levels,
            "bands_schafer": bands,
            "timbre": timbre,
            "dominant_band": dominant,
        })
    return results


def compare_channels(results: list[dict]) -> dict:
    """Differenze rilevanti tra canali: dominanza, squilibrio energia, correlazione tra L/R."""
    active = [r for r in results if not r.get("empty")]
    if not active:
        return {"warning": "nessun canale valido"}

    peaks = [r["levels"]["peak_dbfs"] for r in active]
    rms = [r["levels"]["rms_dbfs"] for r in active]
    centroids = [r["timbre"]["spectral_centroid_hz"] for r in active]
    labels = [r["label"] for r in active]

    # Canale più attivo e più silenzioso
    idx_loud = int(np.argmax(rms))
    idx_quiet = int(np.argmin(rms))

    # Delta front vs surround vs height
    groups = {"front": [], "surround": [], "height": [], "lfe": [], "center": [], "other": []}
    for r in active:
        lbl = r["label"]
        if lbl in ("L", "R"):
            groups["front"].append(r)
        elif lbl == "C":
            groups["center"].append(r)
        elif lbl == "LFE":
            groups["lfe"].append(r)
        elif lbl in ("Ls", "Rs", "Lb", "Rb"):
            groups["surround"].append(r)
        elif lbl in ("Tfl", "Tfr", "Trl", "Trr"):
            groups["height"].append(r)
        else:
            groups["other"].append(r)

    def avg_rms(items):
        if not items:
            return None
        return round(float(np.mean([it["levels"]["rms_dbfs"] for it in items])), 2)

    return {
        "loudest_channel": labels[idx_loud],
        "quietest_channel": labels[idx_quiet],
        "rms_spread_db": round(max(rms) - min(rms), 2),
        "centroid_spread_hz": round(max(centroids) - min(centroids), 1),
        "avg_rms_front": avg_rms(groups["front"]),
        "avg_rms_center": avg_rms(groups["center"]),
        "avg_rms_lfe": avg_rms(groups["lfe"]),
        "avg_rms_surround": avg_rms(groups["surround"]),
        "avg_rms_height": avg_rms(groups["height"]),
    }


def downmix_equal_weight(channels: list[np.ndarray]) -> np.ndarray:
    """Downmix lineare equal-weight (media aritmetica)."""
    stacked = np.stack(channels, axis=1)
    return np.mean(stacked, axis=1).astype(np.float32)


def multichannel_summary(mc: dict) -> dict:
    """Orchestrazione: analisi per canale + confronto di gruppo.

    `mc` è il dict ritornato da io_loader.load_audio_multichannel.
    """
    channels = mc["channels"]
    sr = mc["sr"]
    layout = mc["layout"]
    per_channel = analyze_channels(channels, sr, layout)
    comparison = compare_channels(per_channel)
    return {
        "n_channels": mc["n_channels"],
        "layout": layout,
        "per_channel": per_channel,
        "comparison": comparison,
    }
