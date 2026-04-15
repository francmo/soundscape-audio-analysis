"""Test del refactor v0.2.0: interfaccia Classifier e PANNsClassifier.

Il primo invocation di PANNs scarica il checkpoint CNN14 (~330 MB) in
~/panns_data/. I test successivi usano la cache.
"""
import numpy as np
import pytest
from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.semantic import (
    ClassificationResult, Classifier, PANNsClassifier, get_classifier, semantic_summary
)
from scripts.io_loader import load_audio_mono


def _mps_available() -> bool:
    try:
        import torch
        return hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    except Exception:
        return False


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


def test_get_classifier_factory():
    """La factory ritorna istanze concrete di Classifier."""
    p = get_classifier("panns")
    assert isinstance(p, PANNsClassifier)
    assert p.required_sr == 32000
    assert p.model_name == "PANNs CNN14"


def test_get_classifier_unknown_backend():
    with pytest.raises(ValueError):
        get_classifier("nonexistent")


def test_panns_classifier_result_shape():
    """Smoke test: la classificazione ritorna ClassificationResult coerente."""
    y, sr = load_audio_mono(FIXTURES_DIR / "transient_dense.wav")
    classifier = PANNsClassifier()
    result = classifier.classify(y, sr, segment_seconds=10.0)
    assert isinstance(result, ClassificationResult)
    assert result.model_name == "PANNs CNN14"
    assert result.n_classes == 527
    assert len(result.top_global) > 0
    assert len(result.top_global) <= 15
    # Top_global è ordinato per score decrescente
    scores = [t["score"] for t in result.top_global]
    assert scores == sorted(scores, reverse=True)
    # Ogni elemento ha name + score
    for t in result.top_global:
        assert "name" in t and "score" in t
        assert isinstance(t["name"], str)
        assert 0 <= t["score"] <= 1


def test_semantic_summary_panns_backend():
    """Il summary completo con backend=panns contiene precheck e classifier."""
    out = semantic_summary(FIXTURES_DIR / "transient_dense.wav",
                            backend="panns", enable=True)
    assert out["enabled"]
    assert out["backend"] == "panns"
    assert "precheck" in out
    assert "classifier" in out
    cls = out["classifier"]
    assert cls["model_name"] == "PANNs CNN14"
    assert cls["n_classes"] == 527
    assert "timeline" in cls


def test_panns_timeline_on_silence_low_applies_precheck():
    """Regressione anti 97% Silence: il pre-check attiva su file sotto soglia."""
    out = semantic_summary(FIXTURES_DIR / "silence_low.wav",
                            backend="panns", enable=True)
    pre = out["precheck"]
    assert pre["requires_normalization"], (
        f"Pre-check non attivato, lufs={pre.get('lufs')}"
    )
    # Dopo il pre-check la top-1 non deve essere "Silence"
    top1 = out["classifier"]["top_global"][0]["name"] if out["classifier"]["top_global"] else ""
    assert top1.lower() != "silence", (
        f"Regressione Silence: top-1={top1} dopo pre-check +{pre['gain_db']} dB"
    )


def test_semantic_summary_disabled():
    out = semantic_summary(FIXTURES_DIR / "pink_noise.wav", enable=False)
    assert not out["enabled"]


def test_panns_uses_mps_when_available():
    """v0.3.2: su Apple Silicon con MPS, PANNs deve caricare su MPS
    invece di forzare CPU come faceva v0.3.1."""
    if not _mps_available():
        pytest.skip("MPS non disponibile su questo host")
    y, sr = load_audio_mono(FIXTURES_DIR / "transient_dense.wav")
    clf = PANNsClassifier(device="mps")
    clf.classify(y, sr, segment_seconds=10.0)
    assert clf.device == "mps", (
        f"PANNs non ha usato MPS come richiesto: device={clf.device}"
    )
    first_param = next(clf._at.model.parameters())
    assert first_param.device.type == "mps", (
        f"I parametri del modello non sono su MPS: {first_param.device}"
    )


def test_panns_result_consistent_mps_vs_cpu():
    """Gli output MPS e CPU differiscono per aritmetica FP ma devono
    concordare sul top-5 e avere drift numerico contenuto."""
    if not _mps_available():
        pytest.skip("MPS non disponibile su questo host")
    y, sr = load_audio_mono(FIXTURES_DIR / "transient_dense.wav")

    clf_cpu = PANNsClassifier(device="cpu")
    r_cpu = clf_cpu.classify(y, sr, segment_seconds=10.0)
    clf_mps = PANNsClassifier(device="mps")
    r_mps = clf_mps.classify(y, sr, segment_seconds=10.0)

    names_cpu = [t["name"] for t in r_cpu.top_global[:5]]
    names_mps = [t["name"] for t in r_mps.top_global[:5]]
    overlap = len(set(names_cpu) & set(names_mps))
    assert overlap >= 4, (
        f"Top-5 MPS e CPU differiscono troppo: cpu={names_cpu} mps={names_mps}"
    )

    cpu_by_name = {t["name"]: t["score"] for t in r_cpu.top_global}
    mps_by_name = {t["name"]: t["score"] for t in r_mps.top_global}
    shared = set(cpu_by_name) & set(mps_by_name)
    diffs = [abs(cpu_by_name[n] - mps_by_name[n]) for n in shared]
    assert max(diffs) < 0.02, (
        f"Drift numerico MPS vs CPU troppo alto: max_diff={max(diffs):.4f}"
    )
