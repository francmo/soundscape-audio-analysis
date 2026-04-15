"""Test smoke di `semantic_clap.py` (v0.2.1).

Il primo run scarica il checkpoint LAION-CLAP (~2.2 GB) in ~/.cache/clap/.
I test sono marchiati `clap` e possono essere saltati con
`pytest -m 'not clap'` per skip selettivo.
"""
import pytest
from pathlib import Path

from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.semantic_clap import (
    clap_summary, load_vocabulary, embed_prompts, VOCAB_PATH, CLAP_CHECKPOINT_FILE
)
from scripts.io_loader import load_audio_mono


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


def test_vocabulary_load():
    """v0.5.2: il vocabolario v1.3 ha almeno 190 prompt."""
    vocab = load_vocabulary()
    assert "prompts" in vocab
    assert vocab["version"] == "1.3"
    assert len(vocab["prompts"]) >= 190
    # Ogni prompt ha i campi obbligatori
    for p in vocab["prompts"]:
        assert "id" in p and "text" in p and "category" in p
        assert isinstance(p["text"], str)
        assert len(p["text"]) > 0
    # Gli id sono unici
    ids = [p["id"] for p in vocab["prompts"]]
    assert len(ids) == len(set(ids)), "id duplicati nel vocabolario"
    # v0.5.2: nuova categoria 'paesaggi mediterranei generici' presente
    cats = set(p["category"] for p in vocab["prompts"])
    assert "paesaggi mediterranei generici" in cats


@pytest.mark.skipif(not CLAP_CHECKPOINT_FILE.exists(),
                     reason="Checkpoint CLAP non scaricato")
def test_clap_summary_smoke():
    """Smoke test: clap_summary gira senza errori e ritorna struttura attesa."""
    y, sr = load_audio_mono(FIXTURES_DIR / "pink_noise.wav")
    out = clap_summary(y, sr, enable=True, include_embeddings=False)
    assert out["enabled"]
    assert out["vocabulary_size"] >= 40
    assert len(out["timeline"]) >= 1
    # Ogni segmento ha top-3 tag con prompt italiano
    seg = out["timeline"][0]
    assert "tags" in seg
    assert len(seg["tags"]) == 3
    assert seg["tags"][0]["score"] >= seg["tags"][1]["score"]
    assert seg["tags"][1]["score"] >= seg["tags"][2]["score"]
    # Top-global non vuoto
    assert len(out["top_global"]) > 0


@pytest.mark.skipif(not CLAP_CHECKPOINT_FILE.exists(),
                     reason="Checkpoint CLAP non scaricato")
def test_clap_embeddings_encoded_when_requested():
    """Se include_embeddings=True, gli embedding sono serializzati in base64."""
    y, sr = load_audio_mono(FIXTURES_DIR / "transient_dense.wav")
    out = clap_summary(y, sr, enable=True, include_embeddings=True)
    assert out["embeddings_audio_b64"]
    assert out["embeddings_prompts_b64"]
    assert len(out["embeddings_shape"]) == 2


def test_clap_disabled_returns_stub():
    out = clap_summary(None, 0, enable=False)
    assert not out["enabled"]
    assert out["reason"] == "disabled"
