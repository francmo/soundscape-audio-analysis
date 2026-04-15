"""Riduzione del summary per il payload dell'agente compositivo (v0.2.2).

Invece di passare tutto il summary JSON all'agente (che includeva la
timeline completa di PANNs/YAMNet e poteva far scattare timeout), si
costruisce un payload ridotto focalizzato su quello che serve per la
lettura critica: metadata essenziali, livelli, hum overall, spectral
macro, top-10 PANNs globali, top-20 CLAP globali, narrativa markdown.
"""
from __future__ import annotations
from pathlib import Path

from . import config
from .serialization import dump as dump_json


def build_agent_payload(summary: dict, narrative_md: str) -> dict:
    """Estrae il payload minimo ma sufficiente per l'agente."""
    meta = summary.get("metadata", {})
    tech = summary.get("technical", {})
    hum = summary.get("hum", {})
    spec = summary.get("spectral", {})
    eco = summary.get("ecoacoustic", {})
    classifier = (summary.get("semantic", {}) or {}).get("classifier", {}) or {}
    clap = summary.get("clap", {}) or {}
    mc = summary.get("multichannel", {}) or {}

    payload = {
        "file": {
            "name": meta.get("filename", ""),
            "duration_s": meta.get("duration_s", 0),
            "sample_rate": meta.get("sr", 0),
            "channels": meta.get("channels", 0),
            "layout": (mc or {}).get("layout") or "stereo",
        },
        "technical": {
            "peak_dbfs": tech.get("levels", {}).get("peak_dbfs"),
            "rms_dbfs": tech.get("levels", {}).get("rms_dbfs"),
            "crest_db": tech.get("levels", {}).get("crest_db"),
            "dynamic_range_db": tech.get("levels", {}).get("dynamic_range_db"),
            "noise_floor_db": tech.get("levels", {}).get("noise_floor_db"),
            "integrated_lufs": tech.get("lufs", {}).get("integrated_lufs"),
            "true_peak_db": tech.get("lufs", {}).get("true_peak_db"),
            "lra": tech.get("lufs", {}).get("lra"),
            "clipping_verdict": tech.get("clipping", {}).get("verdict"),
            "dc_offset_verdict": tech.get("dc_offset", {}).get("verdict"),
            "hum_overall": hum.get("overall_verdict", "n.d."),
        },
        "spectral": {
            "bands_schafer_pct": {
                k: v.get("energy_pct") for k, v in (spec.get("bands_schafer") or {}).items()
            },
            "centroid_hz": (spec.get("timbre") or {}).get("spectral_centroid_hz"),
            "rolloff_hz": (spec.get("timbre") or {}).get("spectral_rolloff_hz"),
            "flatness": (spec.get("timbre") or {}).get("spectral_flatness"),
            "hi_fi_lo_fi": spec.get("hifi_lofi", {}),
            "top_peaks_hz": spec.get("top_peaks_hz", []),
            "onsets": spec.get("onsets", {}),
        },
        "ecoacoustic": {
            "aci": eco.get("aci"),
            "ndsi": (eco.get("ndsi") or {}).get("ndsi"),
            "h_total": (eco.get("h_entropy") or {}).get("h_total"),
            "bi": eco.get("bi"),
        },
        "classifier": {
            "model_name": classifier.get("model_name"),
            "top_global": classifier.get("top_global", [])[:10],
            "top_dominant_frames": classifier.get("top_dominant_frames", [])[:8],
        },
        "clap": {
            "enabled": clap.get("enabled", False),
            "model_name": clap.get("model_name"),
            "vocabulary_size": clap.get("vocabulary_size"),
            "top_global": clap.get("top_global", [])[:20],
        },
        "narrative_markdown": narrative_md,
    }
    return payload


def write_agent_payload(summary: dict, narrative_md: str, out_path: Path) -> Path:
    payload = build_agent_payload(summary, narrative_md)
    dump_json(payload, out_path)
    return out_path
