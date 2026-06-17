"""Writer del blocco interchange ``analysis`` (Soundscape Interchange v1.2).

Completa il bridge skill -> Atelier: a partire dal ``summary`` prodotto dalla
pipeline, costruisce il blocco ``analysis`` conforme allo schema v1.2 (engine,
analyzedAt, levels, spectral, tags, timeFields, dynamicForm, summaryRef) e lo
inietta in un file di annotazione dell'Atelier preservando ogni altro blocco
(round-trip senza perdita, come da contratto INTEROP).

Mapping verificato sulla shape reale del summary:
- levels   <- summary["technical"]["levels"] e ["lufs"]
- spectral <- summary["spectral"]["timbre"]
- tags     <- summary["clap"]/["semantic"] top_global (best-effort, score 0-1)
- timeFields / dynamicForm <- summary["time_fields"] / ["dynamic_form"]

bandsSchafer e' rinviato (la scala di energy_pct non e' garantita 0-1).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

ENGINE_NAME = "soundscape-audio-analysis"
SCHEMA_VERSION = "1.2"


def build_analysis_block(
    summary: dict,
    *,
    engine_version: Optional[str] = None,
    summary_ref: Optional[str] = None,
) -> dict:
    """Costruisce il blocco interchange ``analysis`` dal summary della skill."""
    tech = summary.get("technical") or {}
    levels_src = tech.get("levels") or {}
    lufs_src = tech.get("lufs") or {}
    spec_root = summary.get("spectral") or {}
    timbre = spec_root.get("timbre") or {}

    levels = _compact({
        "lufsIntegrated": lufs_src.get("integrated_lufs"),
        "truePeakDb": lufs_src.get("true_peak_db"),
        "peakDb": levels_src.get("peak_dbfs"),
        "rmsDb": levels_src.get("rms_dbfs"),
        "crestDb": levels_src.get("crest_db"),
    })
    spectral = _compact({
        "centroidHz": timbre.get("spectral_centroid_hz"),
        "rolloffHz": timbre.get("spectral_rolloff_hz"),
        "flatness": timbre.get("spectral_flatness"),
    })
    # bandsSchafer in 0-1 (energy_pct e' in percentuale 0-100).
    bands_raw = spec_root.get("bands_schafer") or {}
    bands_schafer = {
        name: round(float(b["energy_pct"]) / 100.0, 4)
        for name, b in bands_raw.items()
        if isinstance(b, dict) and b.get("energy_pct") is not None
    }
    if bands_schafer:
        spectral["bandsSchafer"] = bands_schafer

    block: dict[str, Any] = {
        "engine": {
            "name": ENGINE_NAME,
            "version": str(engine_version or summary.get("version") or "0"),
        },
        "analyzedAt": summary.get("generated_at") or datetime.now().isoformat(timespec="seconds"),
    }
    if levels:
        block["levels"] = levels
    if spectral:
        block["spectral"] = spectral

    tags = _build_tags(summary)
    if tags:
        block["tags"] = tags

    time_fields = summary.get("time_fields")
    if time_fields:
        block["timeFields"] = time_fields
    dynamic_form = summary.get("dynamic_form")
    if dynamic_form:
        block["dynamicForm"] = dynamic_form

    suggested = summary.get("suggested_layers")
    if suggested:
        block["suggestedLayers"] = suggested

    if summary_ref:
        block["summaryRef"] = summary_ref
    return block


def enrich_annotation_file(
    in_path: str | Path,
    summary: dict,
    *,
    out_path: Optional[str | Path] = None,
    engine_version: Optional[str] = None,
    summary_ref: Optional[str] = None,
) -> Path:
    """Inietta il blocco ``analysis`` in un file di annotazione, round-trip safe.

    Carica il JSON grezzo, sostituisce solo ``analysis`` e porta ``schemaVersion``
    a 1.2: ogni altro blocco (annotations, structure, recording, metadata, blocchi
    sconosciuti) e' preservato per costruzione. Scrive in ``out_path`` o sovrascrive
    ``in_path``.
    """
    in_path = Path(in_path)
    data = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"File annotazione non valido (root non oggetto): {in_path}")

    prev_ref = (data.get("analysis") or {}).get("summaryRef") if isinstance(data.get("analysis"), dict) else None
    data["analysis"] = build_analysis_block(
        summary, engine_version=engine_version, summary_ref=summary_ref or prev_ref
    )
    data["schemaVersion"] = SCHEMA_VERSION

    out = Path(out_path) if out_path else in_path
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def _build_tags(summary: dict, limit: int = 10) -> list[dict]:
    """Tag globali best-effort da CLAP e PANNs, con score normalizzato a [0,1]."""
    tags: list[dict] = []
    for item in ((summary.get("clap") or {}).get("top_global") or [])[:limit]:
        label = item.get("label") or item.get("prompt") or item.get("name")
        score = _norm_score(item.get("score", item.get("similarity")))
        if label and score is not None:
            tags.append({"label": str(label), "score": score, "source": "clap"})
    semantic = summary.get("semantic") or {}
    panns_top = (
        (semantic.get("classifier") or {}).get("top_global")
        or semantic.get("top_global")
        or []
    )
    for item in panns_top[:limit]:
        label = item.get("label") or item.get("name")
        score = _norm_score(item.get("score", item.get("pct")))
        if label and score is not None:
            tags.append({"label": str(label), "score": score, "source": "panns"})
    return tags


def _norm_score(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v > 1.0:  # percentuale 0-100 -> 0-1
        v = v / 100.0
    return round(max(0.0, min(1.0, v)), 4)


def _compact(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}
