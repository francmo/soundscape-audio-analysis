"""Layer di mapping accademico post-hoc per i tag CLAP italiani (v0.4.0).

Carica `references/clap_academic_mapping_it.json` e fornisce:

- `load_academic_mapping(path)`: carica il JSON con validazione base degli enum.
- `get_prompt_mapping(prompt_id, vocabulary, mapping)`: risolve il mapping
  completo di un prompt con merge superficiale
  category_defaults[categoria] + prompts[prompt_id].
- `aggregate_academic_hints(top_global, vocabulary, mapping, min_score)`:
  produce hint accademici aggregati sui top-K CLAP pesati per score cosine,
  da iniettare nel payload dell'agente soundscape-composer-analyst.

Il mapping NON e verita empirica: l'agente lo usa come punto di partenza
da validare con narrativa, dati tecnici (flatness, NDSI) e timeline.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from . import config
from .serialization import load as load_json


ACADEMIC_MAPPING_PATH = config.REFERENCES_DIR / "clap_academic_mapping_it.json"


_REQUIRED_ENUMS = (
    "schafer_role",
    "schafer_fidelity",
    "krause",
    "schaeffer_type",
    "smalley_motion",
    "chion",
    "truax",
)


def load_academic_mapping(path: Path | None = None) -> dict:
    """Carica il file di mapping e valida la presenza degli enum chiave."""
    mapping = load_json(path or ACADEMIC_MAPPING_PATH)
    if "enums" not in mapping:
        raise ValueError(f"Mapping accademico senza sezione 'enums': {path}")
    for enum_name in _REQUIRED_ENUMS:
        values = mapping["enums"].get(enum_name)
        if not isinstance(values, list) or not values:
            raise ValueError(
                f"Enum '{enum_name}' mancante o vuoto in {path or ACADEMIC_MAPPING_PATH}"
            )
    if "category_defaults" not in mapping:
        raise ValueError("Mapping accademico senza 'category_defaults'")
    return mapping


def get_prompt_mapping(prompt_id: str, vocabulary: dict, mapping: dict) -> dict:
    """Risolve il mapping di un prompt con ereditarieta da category_defaults.

    Strategia: prende la categoria del prompt dal vocabolario, legge i default
    di quella categoria in mapping['category_defaults'], poi sovrascrive con
    i campi specificati in mapping['prompts'][prompt_id]. Merge superficiale.
    Ritorna dict vuoto se il prompt non esiste nel vocabolario.
    """
    prompt = next(
        (p for p in vocabulary.get("prompts", []) if p["id"] == prompt_id), None
    )
    if prompt is None:
        return {}
    category = prompt.get("category", "")
    defaults = mapping.get("category_defaults", {}).get(category, {})
    override = mapping.get("prompts", {}).get(prompt_id, {})
    resolved = dict(defaults)
    resolved.update(override)
    return resolved


def aggregate_academic_hints(
    top_global: list[dict],
    vocabulary: dict,
    mapping: dict,
    min_score: float = 0.15,
) -> dict:
    """Aggrega hint accademici dai top-K tag CLAP, pesando per score cosine.

    Per ogni dimensione (krause, schafer_role, schafer_fidelity, schaeffer_type,
    smalley_motion, chion, truax) produce una distribuzione percentuale
    normalizzata e un valore dominante con label di confidence. Tag con score
    < `min_score` sono filtrati come rumore. Se restano meno di 3 tag utili,
    ritorna `{"available": False}` con il motivo.
    """
    filtered = [t for t in top_global if float(t.get("score", 0)) >= min_score]
    if len(filtered) < 3:
        return {
            "available": False,
            "reason": "meno di 3 tag con score sufficiente",
            "n_tags_used": len(filtered),
            "min_score": min_score,
        }

    resolved = []
    for t in filtered:
        m = get_prompt_mapping(t["id"], vocabulary, mapping)
        if not m:
            continue
        entry = dict(m)
        entry["_score"] = float(t["score"])
        resolved.append(entry)

    if len(resolved) < 3:
        return {
            "available": False,
            "reason": "meno di 3 tag con mapping risolto",
            "n_tags_used": len(resolved),
        }

    def weighted_distribution(field: str) -> dict[str, float]:
        by_value: dict[str, float] = defaultdict(float)
        total = 0.0
        for r in resolved:
            v = r.get(field)
            if v is None or v == "n/a":
                continue
            by_value[v] += r["_score"]
            total += r["_score"]
        if total == 0:
            return {}
        return {k: round(v / total, 3) for k, v in by_value.items()}

    def dominant_with_confidence(
        dist: dict[str, float], high: float = 0.5, medium: float = 0.33
    ) -> dict:
        if not dist:
            return {"value": None, "confidence": "insufficient"}
        top_value, top_pct = max(dist.items(), key=lambda kv: kv[1])
        if top_pct >= high:
            conf = "high"
        elif top_pct >= medium:
            conf = "medium"
        else:
            conf = "low"
        return {"value": top_value, "pct": top_pct, "confidence": conf}

    def present_values(dist: dict[str, float], min_pct: float) -> list[str]:
        return [v for v, p in dist.items() if p >= min_pct]

    def top_n(dist: dict[str, float], n: int) -> list[list]:
        items = sorted(dist.items(), key=lambda kv: -kv[1])[:n]
        return [[v, p] for v, p in items]

    krause_dist = weighted_distribution("krause")
    schafer_role_dist = weighted_distribution("schafer_role")
    schafer_fid_dist = weighted_distribution("schafer_fidelity")
    schaeffer_dist = weighted_distribution("schaeffer_type")
    smalley_dist = weighted_distribution("smalley_motion")
    chion_dist = weighted_distribution("chion")
    truax_dist = weighted_distribution("truax")

    soundwalk_w = 0.0
    total_w = 0.0
    for r in resolved:
        total_w += r["_score"]
        if r.get("westerkamp_soundwalk_relevance"):
            soundwalk_w += r["_score"]
    soundwalk_pct = round(soundwalk_w / total_w, 3) if total_w > 0 else 0.0

    mean_score = round(
        sum(r["_score"] for r in resolved) / len(resolved), 3
    )

    return {
        "available": True,
        "n_tags_used": len(resolved),
        "mean_score_top_used": mean_score,
        "min_score": min_score,
        "krause": {
            "distribution": krause_dist,
            "dominant": dominant_with_confidence(krause_dist),
        },
        "schafer_role": {
            "distribution": schafer_role_dist,
            "present": present_values(schafer_role_dist, 0.10),
        },
        "schafer_fidelity": dominant_with_confidence(
            schafer_fid_dist, high=0.55, medium=0.35
        ),
        "schaeffer_type": {
            "distribution": schaeffer_dist,
            "top_2": top_n(schaeffer_dist, 2),
        },
        "smalley_motion": {
            "distribution": smalley_dist,
            "top_2": top_n(smalley_dist, 2),
        },
        "chion_modes_present": present_values(chion_dist, 0.15),
        "truax": {
            **dominant_with_confidence(truax_dist),
            "tentative": True,
        },
        "westerkamp_soundwalk_relevance": {
            "value": soundwalk_pct >= 0.4,
            "pct": soundwalk_pct,
            "tentative": True,
        },
    }
