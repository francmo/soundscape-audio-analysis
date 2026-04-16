"""Riduzione del summary per il payload dell'agente compositivo (v0.2.2).

Invece di passare tutto il summary JSON all'agente (che includeva la
timeline completa di PANNs/YAMNet e poteva far scattare timeout), si
costruisce un payload ridotto focalizzato su quello che serve per la
lettura critica: metadata essenziali, livelli, hum overall, spectral
macro, top-10 PANNs globali, top-20 CLAP globali, narrativa markdown.

v0.4.0: aggiunto `clap.academic_hints` con distribuzioni pesate per score
cosine su tassonomie Schafer/Truax/Krause/Schaeffer/Smalley/Chion/Westerkamp,
calcolate da `scripts.clap_mapping.aggregate_academic_hints`. Se il mapping
non e caricabile (file mancante o malformato), il campo ritorna
`{"available": False, "reason": "..."}` senza rompere la pipeline.

v0.5.0: aggiunto campo `speech` quando la trascrizione e' attiva.
Contiene lingua rilevata, durate, trascritto italiano capped a 3000 char
e top-15 segmenti VAD. Se speech non abilitato o skipped, il campo resta
compatto con solo enabled=False + skipped_reason.

v0.5.3: aggiunto campo `signature` (feature di alto livello sintetizzate
per facilitare il riconoscimento di brani noti del repertorio): durata
MM:SS, dynamic range, flatness, Krause dominante, top-5 PANNs frame
dominanti, top-5 CLAP prompts, presenza di parlato. L'agente usa la
signature nel primo passo "Identificazione preliminare" (v0.5.3
obbligatorio).
"""
from __future__ import annotations
from pathlib import Path

from . import config
from .serialization import dump as dump_json


def _build_signature(
    meta: dict,
    tech: dict,
    spec: dict,
    classifier: dict,
    clap: dict,
    speech: dict,
) -> dict:
    """Feature di alto livello sintetizzate per il riconoscimento brani (v0.5.3).

    Non inventa etichette (es. "porto peschereccio"): fornisce all'agente
    dati grezzi ordinati in modo leggibile. Il riconoscimento del brano e'
    responsabilita' del ragionamento LLM, non della skill.
    """
    duration_s = float(meta.get("duration_s", 0) or 0)
    mins = int(duration_s // 60)
    secs = int(round(duration_s % 60))
    duration_mmss = f"{mins}:{secs:02d}"

    levels = (tech or {}).get("levels", {}) or {}
    timbre = (spec or {}).get("timbre", {}) or {}

    top_frames = (classifier.get("top_dominant_frames", []) or [])[:5]
    top_clap = (clap.get("top_global", []) or [])[:5]

    academic = clap.get("academic_hints") or {}
    krause_dom = None
    if isinstance(academic, dict) and academic.get("available"):
        krause_dom = ((academic.get("krause") or {}).get("dominant") or {}).get("value")

    return {
        "duration_mmss": duration_mmss,
        "duration_s": duration_s,
        "dynamic_range_db": levels.get("dynamic_range_db"),
        "integrated_lufs": (tech or {}).get("lufs", {}).get("integrated_lufs"),
        "flatness_mean": timbre.get("spectral_flatness"),
        "krause_dominant": krause_dom,
        "top_panns_dominant_frames": [
            {"name": f.get("name"), "pct": f.get("pct")} for f in top_frames
        ],
        "top_clap_prompts": [
            {
                "prompt": t.get("prompt", ""),
                "category": t.get("category", ""),
                "score": round(float(t.get("score", 0) or 0), 3),
            }
            for t in top_clap
        ],
        "speech_presence": {
            "enabled": bool(speech.get("enabled", False)),
            "duration_speech_s": float(speech.get("duration_speech_s", 0) or 0),
            "language_detected": speech.get("language_detected", ""),
        },
    }


def build_agent_payload(summary: dict, narrative_md: str) -> dict:
    """Estrae il payload minimo ma sufficiente per l'agente."""
    meta = summary.get("metadata", {})
    tech = summary.get("technical", {})
    hum = summary.get("hum", {})
    spec = summary.get("spectral", {})
    eco = summary.get("ecoacoustic", {})
    classifier = (summary.get("semantic", {}) or {}).get("classifier", {}) or {}
    clap = summary.get("clap", {}) or {}
    speech = summary.get("speech", {}) or {}
    mc = summary.get("multichannel", {}) or {}

    payload = {
        "file": {
            "name": meta.get("filename", ""),
            "duration_s": meta.get("duration_s", 0),
            "sample_rate": meta.get("sr", 0),
            "channels": meta.get("channels", 0),
            "layout": (mc or {}).get("layout") or "stereo",
        },
        "signature": _build_signature(meta, tech, spec, classifier, clap, speech),
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
            "vocabulary_version": clap.get("vocabulary_version"),
            "academic_mapping_version": clap.get("academic_mapping_version", ""),
            "top_global": clap.get("top_global", [])[:20],
            "academic_hints": clap.get("academic_hints", {"available": False}),
        },
        "speech": {
            "enabled": speech.get("enabled", False),
            "model_name": speech.get("model_name", ""),
            "language_detected": speech.get("language_detected", ""),
            "language_probability": speech.get("language_probability", 0),
            "duration_speech_s": speech.get("duration_speech_s", 0),
            "duration_total_s": speech.get("duration_total_s", 0),
            "n_vad_segments": speech.get("n_vad_segments", 0),
            "transcript_it": (speech.get("transcript_it") or "")[:3000],
            "segments": speech.get("segments", [])[:15],
            "skipped_reason": speech.get("skipped_reason", ""),
            "translation_fallback": speech.get("translation_fallback", False),
        },
        "narrative_markdown": narrative_md,
    }
    return payload


def write_agent_payload(summary: dict, narrative_md: str, out_path: Path) -> Path:
    payload = build_agent_payload(summary, narrative_md)
    dump_json(payload, out_path)
    return out_path
