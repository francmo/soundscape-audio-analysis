"""Test su scripts/agent_payload._compute_inference_confidence (v0.12.6, P6
caso Marozzi).

Verifica la formula `top1/(top1+top2+top3)` e l'aggregazione PANNs/CLAP nel
campo `aggregate: low|medium|high`. Tiene presente che `aggregate` e' il
minimo (peggiore) fra i due bucket, perche' le inferenze di scena richiedono
accordo fra le due fonti semantiche.
"""
from __future__ import annotations

import pytest

from scripts.agent_payload import _compute_inference_confidence


def _classifier(top_pcts: list[float]) -> dict:
    """Mock classifier con top_dominant_frames a partire dai pct dati."""
    return {
        "top_dominant_frames": [
            {"name": f"L{i}", "pct": p}
            for i, p in enumerate(top_pcts)
        ]
    }


def _clap(top_scores: list[float]) -> dict:
    """Mock clap.top_global con score dati."""
    return {
        "top_global": [
            {"prompt": f"P{i}", "score": s}
            for i, s in enumerate(top_scores)
        ]
    }


def test_high_concentration_returns_high_bucket():
    """top1 = 80% degli score top-3 -> bucket high (>= 0.75)."""
    panns = _classifier([80, 10, 10])
    clap = _clap([0.50, 0.05, 0.10])
    result = _compute_inference_confidence(panns, clap)
    assert result["panns_bucket"] == "high"
    assert result["panns_concentration"] == pytest.approx(0.8, abs=0.01)


def test_medium_concentration_returns_medium_bucket():
    """top1 ~ 60% degli score top-3 -> bucket medium (>= 0.5, < 0.75)."""
    panns = _classifier([60, 25, 15])
    clap = _clap([0.30, 0.15, 0.10])
    result = _compute_inference_confidence(panns, clap)
    assert result["panns_bucket"] == "medium"


def test_dispersed_returns_low_bucket():
    """Distribuzione molto piatta -> bucket low (< 0.5)."""
    panns = _classifier([35, 33, 32])
    clap = _clap([0.20, 0.20, 0.20])
    result = _compute_inference_confidence(panns, clap)
    assert result["panns_bucket"] == "low"
    assert result["clap_bucket"] == "low"


def test_aggregate_is_minimum_of_panns_and_clap():
    """aggregate e' il bucket peggiore (min in rank) fra PANNs e CLAP."""
    # PANNs high, CLAP low -> aggregate low
    panns = _classifier([90, 5, 5])
    clap = _clap([0.20, 0.20, 0.20])
    result = _compute_inference_confidence(panns, clap)
    assert result["panns_bucket"] == "high"
    assert result["clap_bucket"] == "low"
    assert result["aggregate"] == "low"


def test_aggregate_medium_when_one_medium_one_high():
    """aggregate medium quando uno e' medium e l'altro high."""
    panns = _classifier([60, 25, 15])
    clap = _clap([0.50, 0.05, 0.05])
    result = _compute_inference_confidence(panns, clap)
    assert result["aggregate"] == "medium"


def test_empty_classifier_returns_low():
    """Distribuzioni vuote (zero score utili) -> bucket low aggregato.

    Nota: la guardia per "summary vuoto = nessun hint" sta in
    contextual_hints._check_low_inference_confidence, non qui."""
    result = _compute_inference_confidence({}, {})
    assert result["panns_bucket"] == "low"
    assert result["clap_bucket"] == "low"
    assert result["aggregate"] == "low"


def test_marozzi_case_returns_low_aggregate():
    """Caso reale Marozzi 15/05/2026: PANNs Water 31.58/Speech 21.05/Env 10.53
    + CLAP 0.226/0.185/0.182. Aggregate atteso: low (per il bucket CLAP).

    Questo test e' la fixture del primo case study didattico documentato."""
    panns = _classifier([31.58, 21.05, 10.53])
    clap = _clap([0.226, 0.185, 0.182])
    result = _compute_inference_confidence(panns, clap)
    assert result["panns_bucket"] == "medium"  # 31.58 / 63.16 ~ 0.5
    assert result["clap_bucket"] == "low"      # 0.226 / 0.593 ~ 0.38
    assert result["aggregate"] == "low"


def test_method_field_present_for_documentation():
    """Il campo method e' obbligatorio: il payload propaga la formula
    all'agente per trasparenza."""
    result = _compute_inference_confidence(
        _classifier([50, 30, 20]),
        _clap([0.30, 0.10, 0.10]),
    )
    assert "method" in result
    assert "top1" in result["method"]


def test_values_are_rounded_to_three_decimals():
    """Concentrazioni arrotondate a 3 cifre decimali per leggibilita'."""
    panns = _classifier([33.333, 33.333, 33.334])
    clap = _clap([0.1, 0.1, 0.1])
    result = _compute_inference_confidence(panns, clap)
    # round(0.3333.../1.0, 3)
    assert result["panns_concentration"] == pytest.approx(0.333, abs=0.001)


def test_partial_data_panns_only_clap_empty():
    """PANNs con dati, CLAP vuoto: PANNs bucket calcolato, CLAP a 0/low,
    aggregate dominato da CLAP (peggiore)."""
    panns = _classifier([90, 5, 5])
    clap = _clap([])
    result = _compute_inference_confidence(panns, clap)
    assert result["panns_bucket"] == "high"
    assert result["clap_bucket"] == "low"
    assert result["aggregate"] == "low"
