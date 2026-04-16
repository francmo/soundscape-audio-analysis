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
    assert m["version"] == "1.2"
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


def test_paesaggi_mediterranei_generici_category_exists():
    """v0.5.2: nuova categoria per materiale mediterraneo non italo-specifico."""
    vocab = load_vocabulary()
    mapping = load_academic_mapping()
    pmd = [
        p for p in vocab["prompts"]
        if p["category"] == "paesaggi mediterranei generici"
    ]
    assert len(pmd) >= 8, (
        f"Categoria paesaggi mediterranei generici con solo {len(pmd)} prompt"
    )
    assert "paesaggi mediterranei generici" in mapping["category_defaults"]
    defaults = mapping["category_defaults"]["paesaggi mediterranei generici"]
    assert defaults["westerkamp_soundwalk_relevance"] is True


def test_mark_geo_specific_flags_italian_category():
    """Tag appartenenti a 'paesaggi italiani specifici' devono essere
    marcati geo_specific=True."""
    from scripts.clap_mapping import mark_geo_specific_tags
    top_global = [
        {"id": "ita_05", "prompt": "Conservatorio italiano in pausa lezione",
         "category": "paesaggi italiani specifici", "score": 0.31},
    ]
    out = mark_geo_specific_tags(top_global)
    assert out[0]["geo_specific"] is True


def test_mark_geo_specific_flags_keyword_in_prompt():
    """Tag con keyword italo-specifica nel prompt (anche fuori categoria
    dedicata) vanno marcati."""
    from scripts.clap_mapping import mark_geo_specific_tags
    top_global = [
        {"id": "x1", "prompt": "Cicale nella campagna estiva del sud Italia",
         "category": "biofonia mediterranea", "score": 0.40},
        {"id": "x2", "prompt": "Vicolo di borgo medievale al tramonto",
         "category": "paesaggi urbani antichi", "score": 0.28},
    ]
    out = mark_geo_specific_tags(top_global)
    assert out[0]["geo_specific"] is True
    assert out[1]["geo_specific"] is True


def test_mark_geo_specific_no_flag_on_generic():
    """Prompt geograficamente neutri non devono essere flaggati."""
    from scripts.clap_mapping import mark_geo_specific_tags
    top_global = [
        {"id": "geo_01", "prompt": "Vento fra alberi in foresta temperata",
         "category": "geofonia", "score": 0.33},
        {"id": "pmd_01", "prompt": "Porto peschereccio mediterraneo all'alba",
         "category": "paesaggi mediterranei generici", "score": 0.45},
    ]
    out = mark_geo_specific_tags(top_global)
    assert out[0]["geo_specific"] is False
    assert out[1]["geo_specific"] is False


def test_schaeffer_detail_enum_present_v060():
    """v0.6.0: nuovo enum schaeffer_detail con 22 valori (TARTYP esteso)."""
    m = load_academic_mapping()
    assert "schaeffer_detail" in m["enums"]
    detail = m["enums"]["schaeffer_detail"]
    assert isinstance(detail, list)
    assert len(detail) >= 20, f"schaeffer_detail con solo {len(detail)} valori"
    # Famiglie attese presenti come prefisso o esattamente
    expected_families = ["impulsivo", "iterativo", "tenuto", "trama", "campione"]
    families_present = set()
    for value in detail:
        for fam in expected_families:
            if value.startswith(fam):
                families_present.add(fam)
    assert len(families_present) >= 4, (
        f"famiglie schaeffer presenti in detail: {families_present}, "
        f"attese almeno 4 di {expected_families}"
    )


def test_smalley_growth_enum_present_v060():
    """v0.6.0: nuovo enum smalley_growth con 6 valori (Spectromorphology 1997)."""
    m = load_academic_mapping()
    assert "smalley_growth" in m["enums"]
    growth = m["enums"]["smalley_growth"]
    assert set(growth) == {
        "dilation", "accumulation", "dissipation",
        "exogeny", "endogeny", "contraction",
    }


def test_utterance_category_defaults_present_v060():
    """v0.6.0: nuova categoria utterance ha category_defaults coerenti
    con la teoria di Wishart (sound-object, ridotto, search)."""
    m = load_academic_mapping()
    assert "utterance" in m["category_defaults"]
    defaults = m["category_defaults"]["utterance"]
    assert defaults["krause"] == "antropofonia"
    assert defaults["schafer_role"] == "sound-object"
    assert defaults["chion"] == "ridotto"
    assert defaults["truax"] == "search"


def test_aggregate_hints_includes_schaeffer_detail_and_smalley_growth_v060():
    """v0.6.0: aggregate_academic_hints espone i due nuovi campi."""
    vocab = load_vocabulary()
    mapping = load_academic_mapping()
    # 5 prompt utterance pertinenti per popolare i nuovi enum
    fake_top = [
        {"id": "utt_01", "score": 0.45},
        {"id": "utt_02", "score": 0.38},
        {"id": "utt_03", "score": 0.35},
        {"id": "utt_04", "score": 0.28},
        {"id": "utt_05", "score": 0.22},
    ]
    h = aggregate_academic_hints(fake_top, vocab, mapping)
    assert h["available"] is True
    assert "schaeffer_detail" in h
    assert "smalley_growth" in h
    assert h["schaeffer_detail"]["tentative"] is True
    assert h["smalley_growth"]["tentative"] is True
    # Soglie dinamiche: per N=22 enum, high = 2/22 = 0.09. Distribuzione
    # su prompt utterance multiformi, almeno un valore dominante con
    # confidence non insufficient.
    assert h["schaeffer_detail"]["confidence"] in ("high", "medium", "low")
