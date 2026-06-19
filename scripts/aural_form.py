"""Aural Sonology (Thoresen): assi formali derivati dall'analisi automatica.

Fase 1: due dimensioni che la skill non esponeva ancora come oggetti dedicati,
costruite a partire da dati che la pipeline gia calcola.

- ``build_time_fields``: segmentazione gerarchica diacronica (time-fields).
  Mappa le sezioni e le sub_sections prodotte da ``structure.compute_structure``
  in una lista piatta con ``parentId`` (level 0 = campi principali, level 1 =
  sub-campi), nelle chiavi camelCase del contratto interchange v1.2.
- ``build_dynamic_form``: forma dinamica (curva energetica). Ricalcola l'RMS
  frame-by-frame con gli stessi parametri di ``technical.compute_levels``
  (frame_length=4096, hop=config.HOP_LENGTH), cosi la curva e coerente con
  dynamic_range/noise_floor, poi la riduce a una risoluzione leggibile.

Entrambe le funzioni sono additive e prive di effetti collaterali: nessun
modulo esistente viene modificato. Riferimento teorico: Lasse Thoresen,
"Emergent Musical Forms: Aural Explorations" (2015) e auralsonology.com.
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np

from . import config


# --------------------------------------------------------------------------- #
# Time-fields (segmentazione gerarchica diacronica)
# --------------------------------------------------------------------------- #

def build_time_fields(structure_res: Optional[dict]) -> list[dict]:
    """Costruisce i time-fields gerarchici dal risultato di compute_structure.

    Ritorna una lista piatta di campi: ogni sezione e un campo ``level=0``,
    ogni sua sub_section un campo ``level=1`` con ``parentId`` = id della
    sezione padre. Lista vuota se non c'e segmentazione.
    """
    if not structure_res or not structure_res.get("sections"):
        return []

    fields: list[dict] = []
    for section in structure_res["sections"]:
        fields.append(_field_from_section(section, level=0, parent_id=None))
        for sub in section.get("sub_sections") or []:
            parent_id = sub.get("parent_id") or section.get("id")
            fields.append(_field_from_section(sub, level=1, parent_id=parent_id))
    return fields


def _field_from_section(sec: dict, level: int, parent_id: Optional[str]) -> dict:
    """Mappa una sezione (o sub_section) di structure.py allo shape interchange."""
    field: dict[str, Any] = {
        "id": sec["id"],
        "level": level,
        "parentId": parent_id,
        "startSec": _round(sec.get("t_start_s"), 3),
        "endSec": _round(sec.get("t_end_s"), 3),
    }

    label = sec.get("signature_label")
    if label is not None:
        field["label"] = label

    # Stringhe descrittive, copiate solo se presenti.
    for src, dst in (
        ("krause", "krause"),
        ("dominant_panns", "dominantPanns"),
        ("dominant_clap_prompt", "dominantClap"),
    ):
        val = sec.get(src)
        if val is not None:
            field[dst] = val

    # Feature numeriche, arrotondate.
    for src, dst, ndigits in (
        ("mean_rms_db", "meanRmsDb", 2),
        ("mean_centroid_hz", "meanCentroidHz", 1),
        ("mean_flatness", "meanFlatness", 4),
        ("events_per_sec", "eventsPerSec", 3),
    ):
        val = sec.get(src)
        if val is not None:
            field[dst] = _round(val, ndigits)

    hi_fi = sec.get("hi_fi_lo_fi")
    if isinstance(hi_fi, dict):
        score = hi_fi.get("score_5", hi_fi.get("score5"))
        entry: dict[str, Any] = {}
        if hi_fi.get("label") is not None:
            entry["label"] = hi_fi["label"]
        if score is not None:
            entry["score5"] = int(score)
        field["hiFiLoFi"] = entry or None

    # Sorgenti simultanee del campo (Fase 2): top-k PANNs mappati a Krause.
    topk = sec.get("panns_topk")
    if topk:
        field["sources"] = [
            {"label": lbl, "krause": _krause_for(lbl)} for lbl in topk if lbl
        ]

    return field


# --------------------------------------------------------------------------- #
# Dynamic form (curva energetica)
# --------------------------------------------------------------------------- #

def build_dynamic_form(
    y: np.ndarray,
    sr: int,
    *,
    hop: Optional[int] = None,
    frame_length: int = 4096,
    target_hz: float = 2.0,
    max_points: int = 500,
) -> Optional[dict]:
    """Costruisce la forma dinamica (curva energetica) dall'inviluppo RMS.

    La curva e in dBFS, downsampled a ``target_hz`` (con cap a ``max_points``).
    Restituisce anche ``peakSec`` (istante del massimo energetico) e ``phases``
    riservato a None (la tipizzazione della gestalt e demandata all'agente).
    Ritorna None se l'audio e vuoto.
    """
    if hop is None:
        hop = config.HOP_LENGTH
    if y is None or getattr(y, "size", 0) == 0 or not sr:
        return None

    import librosa

    frame_rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop)[0]
    frame_db = 20.0 * np.log10(frame_rms + 1e-12)
    times = librosa.frames_to_time(np.arange(len(frame_db)), sr=sr, hop_length=hop)

    peak_sec = round(float(times[int(np.argmax(frame_db))]), 3) if len(frame_db) else 0.0

    t_ds, db_ds = _downsample(times, frame_db, target_hz, max_points)
    energy = [
        {"tSec": round(float(t), 3), "db": round(float(d), 2)}
        for t, d in zip(t_ds, db_ds)
    ]

    return {
        "resolutionHz": float(target_hz),
        "unit": "dbfs",
        "energy": energy,
        "peakSec": peak_sec,
        "phases": None,
    }


def _downsample(
    times: np.ndarray, values: np.ndarray, target_hz: float, max_points: int
) -> tuple[np.ndarray, np.ndarray]:
    """Media a bin temporali uniformi; cap del numero di punti a max_points."""
    n = len(times)
    if n == 0:
        return np.array([]), np.array([])
    if n == 1:
        return times.copy(), values.copy()

    duration = float(times[-1] - times[0])
    n_bins = int(np.ceil(duration * target_hz)) if duration > 0 else 1
    n_bins = max(1, min(n_bins, max_points, n))

    edges = np.linspace(times[0], times[-1], n_bins + 1)
    idx = np.clip(np.digitize(times, edges) - 1, 0, n_bins - 1)

    t_out: list[float] = []
    v_out: list[float] = []
    for b in range(n_bins):
        mask = idx == b
        if not mask.any():
            continue
        t_out.append(float(np.mean(times[mask])))
        v_out.append(float(np.mean(values[mask])))
    return np.array(t_out), np.array(v_out)


def _round(value: Any, ndigits: int) -> Any:
    """round() tollerante: None resta None, non numerici passano invariati."""
    if value is None:
        return None
    try:
        return round(float(value), ndigits)
    except (TypeError, ValueError):
        return value


# --------------------------------------------------------------------------- #
# Suggested layers (stratificazione sincronica: sorgenti simultanee)
# --------------------------------------------------------------------------- #

def build_suggested_layers(summary: dict, *, max_layers: int = 6,
                           score_min: float = 0.05) -> list[dict]:
    """Sorgenti simultanee candidate, da proporre come strati (Fase 2).

    Risponde alla "singolarita' dell'etichetta": invece del solo dominante,
    espone i top-k sorgenti PANNs co-presenti nel brano, ciascuno mappato alla
    famiglia Krause. Sono SUGGERIMENTI macchina; la curatela degli strati resta
    all'annotatore nell'Atelier.
    """
    semantic = summary.get("semantic") or {}
    sem = (
        (semantic.get("classifier") or {}).get("top_global")
        or semantic.get("top_global")
        or []
    )
    layers: list[dict] = []
    seen: set[str] = set()
    for item in sem:
        name = item.get("name") or item.get("label")
        score = item.get("score")
        if not name or score is None:
            continue
        try:
            score = float(score)
        except (TypeError, ValueError):
            continue
        if score < score_min:
            continue
        key = name.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        layers.append({
            "id": f"L{len(layers) + 1}",
            "label": name,
            "source": "panns",
            "score": round(score, 4),
            "krause": _krause_for(name),
        })
        if len(layers) >= max_layers:
            break
    return layers


# --------------------------------------------------------------------------- #
# Form-building (Fase 4): fasi della gestalt energetica e relazioni candidate
# --------------------------------------------------------------------------- #

def infer_phases(dynamic_form: Optional[dict]) -> Optional[list[dict]]:
    """Tipizzazione euristica (baseline) della gestalt energetica in 4 fasi.

    Deterministica, dal solo profilo energetico: anacrusi (breve preludio),
    crescita (fino al picco), climax (finestra attorno al picco), risoluzione
    (coda). E' un baseline citabile che l'agente form-building puo' raffinare;
    ritorna None se la curva e' troppo corta.
    """
    if not dynamic_form:
        return None
    energy = dynamic_form.get("energy") or []
    if len(energy) < 4:
        return None
    try:
        dur = float(energy[-1]["tSec"])
    except (KeyError, TypeError, ValueError):
        return None
    if dur <= 0:
        return None
    peak = max(0.0, min(float(dynamic_form.get("peakSec") or 0.0), dur))
    pre = round(min(0.08 * dur, peak), 3)
    post = round(min(peak + 0.10 * dur, dur), 3)
    phases: list[dict] = []
    if pre > 0:
        phases.append({"name": "anacrusi", "startSec": 0.0, "endSec": pre})
    if peak > pre:
        phases.append({"name": "crescita", "startSec": pre, "endSec": round(peak, 3)})
    if post > peak:
        phases.append({"name": "climax", "startSec": round(peak, 3), "endSec": post})
    if dur > post:
        phases.append({"name": "risoluzione", "startSec": post, "endSec": round(dur, 3)})
    return phases or None


def build_suggested_relations(
    time_fields: Optional[list[dict]],
    dynamic_form: Optional[dict] = None,
    *,
    max_relations: int = 8,
) -> list[dict]:
    """Relazioni form-building candidate (baseline euristica) fra time-field.

    Confronta i campi di livello 0: stessa sorgente dominante -> ripetizione o
    variazione (per somiglianza di timbro); famiglia o sorgente diverse ->
    contrasto; ricorrenza di una label non adiacente -> ritorno; energia
    crescente verso il climax -> progressione. Riferimenti per id di time-field.
    Sono SUGGERIMENTI: la curatela resta all'annotatore; l'agente li raffina.
    """
    if not time_fields:
        return []
    fields = [f for f in time_fields if f.get("level") == 0]
    if len(fields) < 2:
        return []
    rels: list[dict] = []

    def add(rtype: str, a: dict, b: dict, score: float, rationale: str) -> None:
        rels.append({
            "id": f"R{len(rels) + 1}",
            "type": rtype,
            "fromRef": a["id"],
            "toRef": b["id"],
            "score": round(float(score), 3),
            "rationale": rationale,
        })

    for a, b in zip(fields, fields[1:]):
        pa, pb = a.get("dominantPanns"), b.get("dominantPanns")
        ka, kb = a.get("krause"), b.get("krause")
        ca, cb = a.get("meanCentroidHz"), b.get("meanCentroidHz")
        if pa and pb and pa == pb:
            if _close(ca, cb, 0.25):
                add("repetition", a, b, 0.6, f"stessa sorgente dominante ({pa}), timbro simile")
            else:
                add("variation", a, b, 0.55, f"stessa sorgente dominante ({pa}), timbro diverso")
        elif (ka and kb and ka != kb) or (pa and pb and pa != pb and not _close(ca, cb, 0.5)):
            add("contrast", a, b, 0.5, "famiglia o sorgente dominante diverse")

    first_seen: dict[str, int] = {}
    for i, f in enumerate(fields):
        lab = f.get("label") or f.get("dominantPanns")
        if not lab:
            continue
        if lab in first_seen and i - first_seen[lab] >= 2:
            add("return", fields[first_seen[lab]], f, 0.5, f"ricorrenza di '{lab}'")
        first_seen.setdefault(lab, i)

    if dynamic_form and dynamic_form.get("peakSec") is not None:
        peak = float(dynamic_form["peakSec"])
        climax = next(
            (
                f for f in fields
                if f.get("startSec") is not None and f.get("endSec") is not None
                and f["startSec"] <= peak <= f["endSec"]
            ),
            None,
        )
        if climax is not None and climax is not fields[0]:
            r0, rp = fields[0].get("meanRmsDb"), climax.get("meanRmsDb")
            if r0 is not None and rp is not None and rp > r0:
                add("progression", fields[0], climax, 0.5, "energia crescente verso il climax")

    return rels[:max_relations]


def _close(a: Any, b: Any, rel: float) -> bool:
    """True se a e b sono entro una tolleranza relativa rel (None -> False)."""
    if a is None or b is None:
        return False
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if a == 0 and b == 0:
        return True
    return abs(a - b) <= rel * max(abs(a), abs(b), 1.0)


def _krause_for(panns_label: str) -> str:
    """Mappa un label PANNs alla famiglia Krause, riusando structure.py."""
    try:
        from .structure import _krause_from_panns
        return _krause_from_panns(panns_label)
    except Exception:
        return "mista"
