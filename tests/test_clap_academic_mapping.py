"""Test del layer di mapping accademico CLAP (v0.4.0).

Copre: caricamento e validazione enum, coerenza categoria-defaults,
risoluzione prompt con ereditarieta, aggregazione hint pesata per score,
gestione segnale debole.
"""
import pytest

from scripts.clap_mapping import (
    load_academic_mapping,
    get_prompt_mapping,
    aggregate_academic_hints,
)
from scripts.semantic_clap import load_vocabulary


def test_mapping_loads_and_has_required_keys():
    m = load_academic_mapping()
    assert m["version"] == "1.0"
    assert "enums" in m and "category_defaults" in m and "prompts" in m
    for name, values in m["enums"].items():
        assert isinstance(values, list) and len(values) > 0, (
            f"enum '{name}' vuoto"
        )


def test_every_vocabulary_category_has_defaults():
    vocab = load_vocabulary()
    mapping = load_academic_mapping()
    categories_in_vocab = set(p["category"] for p in vocab["prompts"])
    defaults = set(mapping["category_defaults"].keys())
    missing = categories_in_vocab - defaults
    assert not missing, f"Categorie senza defaults nel mapping: {missing}"


def test_every_prompt_resolves_to_mapping():
    vocab = load_vocabulary()
    mapping = load_academic_mapping()
    for p in vocab["prompts"]:
        resolved = get_prompt_mapping(p["id"], vocab, mapping)
        assert resolved, f"Prompt {p['id']} non risolve"
        for field in ("krause", "schafer_role", "schafer_fidelity", "chion"):
            assert field in resolved, (
                f"Prompt {p['id']} manca del campo {field}"
            )


def test_resolved_values_are_in_enums():
    vocab = load_vocabulary()
    mapping = load_academic_mapping()
    enums = mapping["enums"]
    for p in vocab["prompts"]:
        resolved = get_prompt_mapping(p["id"], vocab, mapping)
        for field in (
            "krause", "schafer_role", "schafer_fidelity",
            "chion", "truax", "schaeffer_type", "smalley_motion",
        ):
            v = resolved.get(field)
            if v is None:
                continue
            assert v in enums[field], (
                f"{p['id']}.{field}={v!r} non in enum {enums[field]}"
            )


def test_prompt_override_beats_category_default():
    """urb_03 (campane chiesa) ha schafer_role=soundmark via override,
    categoria antropofonia urbana ha default signal."""
    vocab = load_vocabulary()
    mapping = load_academic_mapping()
    resolved = get_prompt_mapping("urb_03", vocab, mapping)
    assert resolved["schafer_role"] == "soundmark"


def test_aggregate_hints_produces_valid_structure():
    vocab = load_vocabulary()
    mapping = load_academic_mapping()
    fake_top = [
        {"id": "geo_01", "score": 0.45},
        {"id": "geo_06", "score": 0.38},
        {"id": "bio_01", "score": 0.35},
        {"id": "urb_01", "score": 0.28},
        {"id": "urb_03", "score": 0.22},
        {"id": "mec_01", "score": 0.18},
    ]
    h = aggregate_academic_hints(fake_top, vocab, mapping)
    assert h["available"] is True
    assert h["n_tags_used"] >= 3
    assert "krause" in h and "distribution" in h["krause"]
    assert "geofonia" in h["krause"]["distribution"]
    assert h["krause"]["dominant"]["confidence"] in (
        "high", "medium", "low", "insufficient"
    )
    assert "schaeffer_type" in h
    assert "top_2" in h["schaeffer_type"]
    assert h["truax"]["tentative"] is True
    assert h["westerkamp_soundwalk_relevance"]["tentative"] is True


def test_aggregate_returns_false_on_weak_signal():
    vocab = load_vocabulary()
    mapping = load_academic_mapping()
    weak_top = [
        {"id": "geo_01", "score": 0.10},
        {"id": "bio_01", "score": 0.12},
    ]
    h = aggregate_academic_hints(weak_top, vocab, mapping)
    assert h["available"] is False
    assert "reason" in h


def test_paesaggi_italiani_expanded_to_20_plus():
    vocab = load_vocabulary()
    paesaggi = [
        p for p in vocab["prompts"]
        if p["category"] == "paesaggi italiani specifici"
    ]
    assert len(paesaggi) >= 20, (
        f"Solo {len(paesaggi)} prompt in 'paesaggi italiani specifici'"
    )


def test_mark_speech_hallucinations_flags_voice_keywords_when_no_panns_speech():
    """Caso SheLiesDown citato da Gemini: drone musicale, CLAP propone
    'Discussione di vicini' ma PANNs non vede Speech."""
    from scripts.clap_mapping import mark_speech_hallucinations
    top_global = [
        {"id": "ita_03", "prompt": "Discussione di vicini dalle finestre",
         "category": "paesaggi italiani specifici", "score": 0.32},
        {"id": "elx_07", "prompt": "Drone elettronico continuo",
         "category": "trasformazioni elettroacustiche", "score": 0.55},
    ]
    classifier = {
        "top_global": [{"name": "Music", "score": 0.74},
                       {"name": "Speech", "score": 0.05}],
        "top_dominant_frames": [{"name": "Music", "pct": 78.0}],
    }
    out = mark_speech_hallucinations(top_global, classifier)
    halluc = [t for t in out if t.get("likely_hallucination")]
    assert len(halluc) == 1
    assert halluc[0]["prompt"].startswith("Discussione")
    assert "Drone" not in halluc[0]["prompt"]


def test_mark_speech_hallucinations_no_flag_when_panns_has_speech():
    """Se PANNs rileva Speech sopra soglia, i tag CLAP voce non sono
    allucinazioni."""
    from scripts.clap_mapping import mark_speech_hallucinations
    top_global = [
        {"id": "ita_15", "prompt": "Voci di mercato in dialetto locale",
         "category": "paesaggi italiani specifici", "score": 0.42},
    ]
    classifier = {
        "top_global": [{"name": "Speech", "score": 0.65}],
        "top_dominant_frames": [{"name": "Speech", "pct": 60.0}],
    }
    out = mark_speech_hallucinations(top_global, classifier)
    assert out[0]["likely_hallucination"] is False


def test_mark_speech_hallucinations_safe_with_no_classifier():
    """Se classifier e' None o vuoto, nessun crash. Tutti marcati come
    allucinazioni se contengono keyword voce (PANNs ipoteticamente assente)."""
    from scripts.clap_mapping import mark_speech_hallucinations
    top_global = [
        {"id": "x", "prompt": "Voci di mercato", "score": 0.3},
        {"id": "y", "prompt": "Drone musicale", "score": 0.4},
    ]
    out = mark_speech_hallucinations(top_global, None)
    # Voci flaggato (ha keyword), Drone no
    assert out[0]["likely_hallucination"] is True
    assert out[1]["likely_hallucination"] is False
    out2 = mark_speech_hallucinations(top_global, {})
    assert out2[0]["likely_hallucination"] is True


def test_sacralita_sonora_category_exists():
    vocab = load_vocabulary()
    mapping = load_academic_mapping()
    sacra = [p for p in vocab["prompts"] if p["category"] == "sacralita sonora"]
    assert len(sacra) >= 8, f"Categoria sacralita sonora con solo {len(sacra)} prompt"
    assert "sacralita sonora" in mapping["category_defaults"]
    defaults = mapping["category_defaults"]["sacralita sonora"]
    assert defaults["schafer_role"] == "soundmark"
    assert defaults["westerkamp_soundwalk_relevance"] is True
