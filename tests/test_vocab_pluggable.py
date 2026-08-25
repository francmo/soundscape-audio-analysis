"""Test v0.20.0 - P1 addendum heritage: vocabolario CLAP innestabile,
impronta del checkpoint nelle chiavi di cache e nel summary, guardia
anti-allucinazione generalizzata, risoluzione path del wrapper.

Nessun modello reale: CLAP e' sostituito da fake, gli embedding dei prompt
vengono iniettati dove serve.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from scripts import config, semantic_clap
from scripts.clap_mapping import (
    mark_speech_hallucinations,
    vocal_keywords_for_language,
)


# ---------------------------------------------------------------- fixtures

class _FakeClapModel:
    def __init__(self):
        self.calls = 0

    def get_text_embedding(self, prompts, use_tensor=False):
        self.calls += 1
        return np.stack([
            np.full(8, float(len(p)), dtype=np.float32) for p in prompts
        ])


@pytest.fixture()
def fake_clap(monkeypatch, tmp_path):
    fake = _FakeClapModel()
    monkeypatch.setattr(semantic_clap, "load_clap_model",
                        lambda device=None: (fake, "cpu"))
    monkeypatch.setattr(semantic_clap, "CLAP_CHECKPOINT_DIR", tmp_path)
    semantic_clap._PROMPT_EMB_CACHE.clear()
    yield fake
    semantic_clap._PROMPT_EMB_CACHE.clear()


def _fake_checkpoint(tmp_path, name, content: bytes):
    p = tmp_path / name
    p.write_bytes(content)
    return p


# ------------------------------------------------- impronta del checkpoint

def test_checkpoint_fingerprint_su_file(tmp_path):
    ck = _fake_checkpoint(tmp_path, "ck.pt", b"pesi del modello A")
    fp = semantic_clap.checkpoint_fingerprint(ck)
    assert len(fp) == 64
    # memoizzata: stessa risposta, e cambia col contenuto
    assert semantic_clap.checkpoint_fingerprint(ck) == fp
    ck2 = _fake_checkpoint(tmp_path, "ck2.pt", b"pesi del modello B")
    assert semantic_clap.checkpoint_fingerprint(ck2) != fp


def test_checkpoint_fingerprint_file_mancante(tmp_path):
    assert semantic_clap.checkpoint_fingerprint(tmp_path / "assente.pt") == ""


def test_cache_key_cambia_con_il_checkpoint(monkeypatch, tmp_path):
    """Lezione 10: stessa lista di testi, checkpoint diverso, chiave diversa."""
    ck_a = _fake_checkpoint(tmp_path, "a.pt", b"checkpoint A")
    ck_b = _fake_checkpoint(tmp_path, "b.pt", b"checkpoint B")
    monkeypatch.setattr(semantic_clap, "CLAP_CHECKPOINT_FILE", ck_a)
    key_a = semantic_clap._prompts_cache_key(["mare calmo"])
    monkeypatch.setattr(semantic_clap, "CLAP_CHECKPOINT_FILE", ck_b)
    key_b = semantic_clap._prompts_cache_key(["mare calmo"])
    assert key_a != key_b
    # e resta sensibile al testo, come prima
    key_c = semantic_clap._prompts_cache_key(["mare mosso"])
    assert key_c not in (key_a, key_b)


def test_sweep_cache_legacy(fake_clap, tmp_path):
    """La scrittura di una cache nuova rimuove le npz legacy senza impronta."""
    legacy = tmp_path / ("prompt_embeddings_" + "0" * 32 + ".npz")
    np.savez_compressed(legacy, embeddings=np.zeros((1, 8), dtype=np.float32))
    semantic_clap.embed_prompts(["campane lontane"])
    assert not legacy.exists()
    v2 = list(tmp_path.glob("prompt_embeddings_v2_*.npz"))
    assert len(v2) == 1
    # una seconda scrittura non tocca le v2 esistenti
    semantic_clap.embed_prompts(["vento fra gli alberi"])
    assert all(p.exists() for p in v2)


# ------------------------------------------------------ vocabolario utente

def test_load_user_vocabulary_schema_nativo(tmp_path):
    path = tmp_path / "voc.json"
    path.write_text(json.dumps({
        "name": "prova", "version": "1.0", "language": "it",
        "prompts": [{"id": "p1", "text": "mare calmo", "category": "geofonia"}],
    }), encoding="utf-8")
    voc = semantic_clap.load_user_vocabulary(path)
    assert voc["name"] == "prova"
    assert voc["language"] == "it"
    assert voc["prompts"][0]["id"] == "p1"
    assert voc["prompts"][0]["text"] == "mare calmo"
    assert len(voc["content_sha256"]) == 64


def test_load_user_vocabulary_schema_paper(tmp_path):
    """Lo schema dei vocabolari del caso heritage (prompt+tradizione, lingua)
    si carica senza conversioni manuali."""
    path = tmp_path / "vocabolario_dominio.json"
    path.write_text(json.dumps({
        "version": "2.0", "lingua": "en",
        "prompts": [
            {"prompt": "a male voice reciting scripture", "tradizione": "islam"},
            {"prompt": "congregational hymn singing", "tradizione": "cristianesimo"},
        ],
    }), encoding="utf-8")
    voc = semantic_clap.load_user_vocabulary(path)
    assert voc["name"] == "vocabolario_dominio"
    assert voc["language"] == "en"
    assert [p["id"] for p in voc["prompts"]] == ["v001", "v002"]
    assert voc["prompts"][0]["text"] == "a male voice reciting scripture"
    assert voc["prompts"][0]["category"] == "islam"
    assert voc["prompts"][0]["tradizione"] == "islam"


def test_load_user_vocabulary_errori(tmp_path):
    vuoto = tmp_path / "vuoto.json"
    vuoto.write_text(json.dumps({"prompts": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        semantic_clap.load_user_vocabulary(vuoto)
    senza_testo = tmp_path / "senza_testo.json"
    senza_testo.write_text(json.dumps({"prompts": [{"id": "x"}]}), encoding="utf-8")
    with pytest.raises(ValueError):
        semantic_clap.load_user_vocabulary(senza_testo)


# ------------------------------------------------- guardia generalizzata

def _classifier_senza_voce():
    return {"top_global": [{"name": "Music", "score": 0.8}],
            "top_dominant_frames": [{"name": "Music", "pct": 90.0}]}


def test_vocal_keywords_per_lingua():
    assert vocal_keywords_for_language("it") == frozenset(config.SPEECH_KEYWORDS_IT)
    assert vocal_keywords_for_language("en") == frozenset(config.SPEECH_KEYWORDS_EN)
    assert vocal_keywords_for_language("English") == frozenset(config.SPEECH_KEYWORDS_EN)
    assert vocal_keywords_for_language("") == frozenset(config.SPEECH_KEYWORDS_IT)
    assert vocal_keywords_for_language("ar") == frozenset()


def test_guardia_keyword_inglesi():
    """Lezione 2: un prompt vocale inglese ora viene riconosciuto."""
    tags = [{"id": "v1", "prompt": "a male voice reciting the Quran", "score": 0.4}]
    out = mark_speech_hallucinations(
        tags, _classifier_senza_voce(),
        keywords=vocal_keywords_for_language("en"),
    )
    assert out[0]["likely_hallucination"] is True


def test_guardia_metadato_vocal_vince():
    tags = [
        {"id": "a", "prompt": "temple bells at dawn", "score": 0.3},
        {"id": "b", "prompt": "a capella chant", "score": 0.3},
    ]
    out = mark_speech_hallucinations(
        tags, _classifier_senza_voce(),
        keywords=vocal_keywords_for_language("en"),
        vocal_by_id={"a": True, "b": False},
    )
    # "a" non ha keyword vocali ma il metadato lo dichiara vocale
    assert out[0]["likely_hallucination"] is True
    # "b" avrebbe la keyword "chant" ma il metadato dichiara non vocale
    assert out[1]["likely_hallucination"] is False


def test_guardia_percorso_storico_invariato():
    """La chiamata a due argomenti (vocabolario nativo) non cambia."""
    tags = [{"id": "n1", "prompt": "Discussione di vicini nel cortile", "score": 0.5}]
    out = mark_speech_hallucinations(tags, _classifier_senza_voce())
    assert out[0]["likely_hallucination"] is True
    con_voce = {"top_global": [{"name": "Speech", "score": 0.6}],
                "top_dominant_frames": []}
    out2 = mark_speech_hallucinations(tags, con_voce)
    assert out2[0]["likely_hallucination"] is False


# ------------------------------------------- blocco vocabolario nel summary

def test_tag_custom_vocabulary_blocco(monkeypatch, tmp_path):
    ck = _fake_checkpoint(tmp_path, "ck.pt", b"pesi")
    monkeypatch.setattr(semantic_clap, "CLAP_CHECKPOINT_FILE", ck)
    voc = {
        "name": "dominio", "version": "2.0", "language": "en",
        "source_file": "dominio.json", "content_sha256": "f" * 64,
        "prompts": [
            {"id": "v001", "text": "a male voice reciting scripture",
             "category": "islam"},
            {"id": "v002", "text": "temple bells at dawn", "category": "buddhismo"},
        ],
    }
    audio_emb = np.random.default_rng(7).normal(size=(3, 8)).astype(np.float32)
    prompt_emb = np.random.default_rng(8).normal(size=(2, 8)).astype(np.float32)
    bounds = [(0.0, 10.0), (10.0, 20.0), (20.0, 30.0)]
    block = semantic_clap.tag_custom_vocabulary(
        voc, audio_emb, bounds,
        classifier=_classifier_senza_voce(), prompt_emb=prompt_emb,
    )
    assert block["name"] == "dominio"
    assert block["vocabulary_size"] == 2
    assert block["content_sha256"] == "f" * 64
    assert block["checkpoint_file"] == "ck.pt"
    assert len(block["checkpoint_sha256"]) == 64
    assert block["hallucination_guard"] == "attiva"
    assert len(block["timeline"]) == 3
    assert block["top_global"]
    # il prompt vocale senza supporto PANNs risulta marcato
    marcati = {t["id"]: t["likely_hallucination"] for t in block["top_global"]}
    assert marcati["v001"] is True
    assert block["embeddings_prompts_shape"] == [2, 8]


def test_tag_custom_vocabulary_guardia_inattiva_dichiarata():
    voc = {
        "name": "arabo", "version": "1.0", "language": "ar",
        "source_file": "ar.json", "content_sha256": "e" * 64,
        "prompts": [{"id": "v001", "text": "..."}],
    }
    audio_emb = np.ones((1, 8), dtype=np.float32)
    prompt_emb = np.ones((1, 8), dtype=np.float32)
    block = semantic_clap.tag_custom_vocabulary(
        voc, audio_emb, [(0.0, 10.0)], prompt_emb=prompt_emb,
    )
    assert block["hallucination_guard"].startswith("inattiva")


# --------------------------------------------------- risoluzione dei path

def test_resolve_user_path(monkeypatch, tmp_path):
    from scripts.cli import _resolve_user_path
    # assoluto: intatto
    assert _resolve_user_path(tmp_path / "x.json") == tmp_path / "x.json"
    # relativo esistente nella cwd corrente: intatto (compatibilita' storica)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "qui.json").write_text("{}", encoding="utf-8")
    from pathlib import Path
    assert _resolve_user_path("qui.json") == Path("qui.json")
    # relativo inesistente ma presente sotto la cwd del chiamante: risolto
    caller = tmp_path / "cartella_utente"
    caller.mkdir()
    (caller / "voc.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("SOUNDSCAPE_CALLER_CWD", str(caller))
    assert _resolve_user_path("voc.json") == caller / "voc.json"
    # inesistente ovunque: torna com'era (l'errore lo da' la validazione)
    assert _resolve_user_path("fantasma.json") == Path("fantasma.json")
