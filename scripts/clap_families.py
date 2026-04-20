"""Famiglie semantiche CLAP (v0.12.2).

Traduce i 251 prompt iper-specifici del vocabolario CLAP italiano in un numero
piu' ridotto di macro-famiglie semantiche (biofonia, geofonia, antropofonia
umana, antropofonia meccanica, paesaggio urbano, paesaggio geografico, musica
e processing, oggetti astratti). L'aggregazione serve per:

- Timeline grafica (v0.12.1): una barra colorata per famiglia invece di
  tabelle con 250+ righe.
- Narrativa per sezione (v0.12.0): famiglia dominante invece di prompt
  iper-specifico ("biofonia" invece di "Gallo che canta all'alba in
  villaggio costiero").

Il prompt originale resta visibile in `summary.json` e nella Lettura
compositiva (input al sub-agent) per tracciabilita'.
"""
from __future__ import annotations

import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path


_MAPPING_PATH = Path(__file__).resolve().parent.parent / "references" / "clap_families_it.json"
_VOCAB_PATH = Path(__file__).resolve().parent.parent / "references" / "clap_vocabulary_it.json"


@lru_cache(maxsize=1)
def load_families() -> dict:
    """Carica il mapping family di riferimento. Cache singola."""
    with _MAPPING_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)


@lru_cache(maxsize=1)
def _prompt_to_category() -> dict[str, str]:
    """Mappa `prompt text -> category` dal vocabolario CLAP."""
    with _VOCAB_PATH.open("r", encoding="utf-8") as fp:
        vocab = json.load(fp)
    mapping: dict[str, str] = {}
    for p in vocab.get("prompts", []):
        text = (p.get("text") or "").strip()
        cat = p.get("category", "")
        if text:
            mapping[text] = cat
    return mapping


def family_for_prompt(prompt_text: str) -> str | None:
    """Ritorna la famiglia semantica per un prompt text, o None se sconosciuto.

    Il match e' esatto sul testo del prompt. I prompt non presenti nel
    vocabolario ritornano None e vanno gestiti dal chiamante.
    """
    cat = _prompt_to_category().get(prompt_text.strip())
    if cat is None:
        return None
    families = load_families()
    return families.get("category_to_family", {}).get(cat)


def family_meta(family_key: str) -> dict:
    """Metadati visivi della famiglia (label leggibile, colore hex)."""
    families = load_families()
    return (families.get("families") or {}).get(family_key) or {}


def aggregate_timeline_to_families(clap_timeline: list[dict]) -> list[dict]:
    """Converte una timeline CLAP per-finestra in scores per-famiglia.

    Input: lista di entry `{t_start_s, t_end_s, top: [{prompt, score}, ...]}`
    come prodotto da `semantic_clap.py`.

    Output: lista di entry `{t_start_s, t_end_s, families: {key: score}}`
    dove `families` aggrega i top prompt raggruppandoli per famiglia
    (somma dei cosine score, clip a 1.0 per famiglia). Le entry senza
    match alla famiglia vengono ignorate.
    """
    families = load_families()
    cat_to_fam = families.get("category_to_family", {}) or {}
    out: list[dict] = []
    for entry in clap_timeline:
        family_scores: dict[str, float] = defaultdict(float)
        # Accept both "top" (vecchio schema) e "tags" (schema attuale v0.6+).
        tags = entry.get("tags") or entry.get("top") or []
        for tag in tags:
            score = float(tag.get("score", 0.0))
            if score <= 0:
                continue
            # Prefer the category already written in the timeline entry
            # (piu' affidabile di un lookup testuale sul prompt).
            cat = (tag.get("category") or "").strip()
            fam = cat_to_fam.get(cat) if cat else None
            if fam is None:
                fam = family_for_prompt(tag.get("prompt", ""))
            if fam is None:
                continue
            family_scores[fam] += score
        if not family_scores:
            continue
        out.append({
            "t_start_s": float(entry.get("t_start_s", 0.0)),
            "t_end_s": float(entry.get("t_end_s", 0.0)),
            "families": {k: min(v, 1.0) for k, v in family_scores.items()},
        })
    return out


def dominant_family_per_window(clap_timeline: list[dict]) -> list[dict]:
    """Ritorna per ogni finestra la famiglia dominante (score max).

    Output: `[{t_start_s, t_end_s, family, score, label}, ...]`. Le finestre
    senza alcuna famiglia riconosciuta sono omesse.
    """
    out: list[dict] = []
    for entry in aggregate_timeline_to_families(clap_timeline):
        fams = entry["families"]
        if not fams:
            continue
        dom_key = max(fams.items(), key=lambda kv: kv[1])[0]
        meta = family_meta(dom_key)
        out.append({
            "t_start_s": entry["t_start_s"],
            "t_end_s": entry["t_end_s"],
            "family": dom_key,
            "label": meta.get("label", dom_key),
            "color": meta.get("color", "#808080"),
            "score": fams[dom_key],
        })
    return out
