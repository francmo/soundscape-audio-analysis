"""Test: hum check con baseline locale.

Regressione principale: baseline locale, non globale.
Fixture:
- sine_50hz.wav: seno 50 Hz + pink noise basso. Atteso: verdetto 'forte' o 'presente' a 50 Hz.
- pink_noise.wav: solo pink noise. Atteso: verdetto 'trascurabile' ovunque (no falso positivo).
"""
from pathlib import Path
import pytest

from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.hum import hum_check, interpret_in_context


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


def test_hum_positive_on_sine_50hz():
    path = FIXTURES_DIR / "sine_50hz.wav"
    result = hum_check(path)
    peak_50 = next((p for p in result["peaks"] if p["target_hz"] == 50), None)
    assert peak_50 is not None
    assert peak_50["verdict"] in {"presente", "forte"}, f"atteso presente/forte, ottenuto {peak_50['verdict']}"
    assert peak_50["ratio_db"] > 10, f"ratio_db troppo basso: {peak_50['ratio_db']}"


def test_hum_negative_on_pink_noise():
    """Anti falso-positivo: baseline locale impedisce che rumore rosa triggeri hum."""
    path = FIXTURES_DIR / "pink_noise.wav"
    result = hum_check(path)
    for p in result["peaks"]:
        # Il verdetto deve essere 'trascurabile' su tutti i target
        assert p["verdict"] == "trascurabile", (
            f"Falso positivo su {p['target_hz']} Hz: verdetto={p['verdict']}, "
            f"ratio_db={p['ratio_db']}"
        )
    assert result["overall_verdict"] == "trascurabile"


def test_hum_baseline_bands_metadata():
    """Verifica che la baseline sia locale (bande 30-45 e 70-95)."""
    path = FIXTURES_DIR / "pink_noise.wav"
    result = hum_check(path)
    assert result["baseline_bands"] == [(30, 45), (70, 95)]


def test_interpret_in_context_flags_musical_flute():
    """Caso VB_Flauto: hum 'presente' su materiale tonale (flatness 0.021)
    classificato come Flute (0.66). interpretation_hint deve marcare
    likely_musical_harmonic=True per evitare falso positivo."""
    hum_res = {
        "overall_verdict": "presente",
        "peaks": [
            {"target_hz": 150, "verdict": "presente", "ratio_db": 11.57},
            {"target_hz": 50, "verdict": "trascurabile", "ratio_db": -3.87},
        ],
    }
    spectral = {"timbre": {"spectral_flatness": 0.0208}}
    classifier = {"top_global": [{"name": "Flute", "score": 0.6564}]}
    out = interpret_in_context(hum_res, spectral, classifier)
    hint = out["interpretation_hint"]
    assert hint["likely_musical_harmonic"] is True
    assert "Flute" in hint["reason"]
    assert "150 Hz" in hint["reason"]
    # Verdict numerico non e' cambiato
    assert out["overall_verdict"] == "presente"


def test_interpret_in_context_no_flag_on_environmental():
    """Scena urbana con Traffic dominante: flatness alta, non marcare
    come armonica musicale."""
    hum_res = {
        "overall_verdict": "presente",
        "peaks": [{"target_hz": 50, "verdict": "presente", "ratio_db": 22.0}],
    }
    spectral = {"timbre": {"spectral_flatness": 0.35}}
    classifier = {"top_global": [{"name": "Traffic", "score": 0.72}]}
    out = interpret_in_context(hum_res, spectral, classifier)
    assert out["interpretation_hint"]["likely_musical_harmonic"] is False


def test_interpret_in_context_no_flag_if_all_trascurabile():
    """Se il verdict complessivo e' gia' trascurabile, l'hint non si applica."""
    hum_res = {
        "overall_verdict": "trascurabile",
        "peaks": [{"target_hz": 50, "verdict": "trascurabile", "ratio_db": -5.0}],
    }
    spectral = {"timbre": {"spectral_flatness": 0.02}}
    classifier = {"top_global": [{"name": "Flute", "score": 0.8}]}
    out = interpret_in_context(hum_res, spectral, classifier)
    assert out["interpretation_hint"]["likely_musical_harmonic"] is False


def test_interpret_in_context_no_flag_if_score_too_low():
    """Se top PANNs ha score sotto soglia, non propone hint musicale."""
    hum_res = {
        "overall_verdict": "presente",
        "peaks": [{"target_hz": 150, "verdict": "presente", "ratio_db": 12.0}],
    }
    spectral = {"timbre": {"spectral_flatness": 0.02}}
    classifier = {"top_global": [{"name": "Flute", "score": 0.35}]}
    out = interpret_in_context(hum_res, spectral, classifier)
    assert out["interpretation_hint"]["likely_musical_harmonic"] is False


def test_interpret_in_context_safe_with_missing_data():
    """Dict incompleti non devono far crashare la funzione."""
    hum_res = {"overall_verdict": "presente", "peaks": []}
    out = interpret_in_context(hum_res, None, None)
    assert out["interpretation_hint"]["likely_musical_harmonic"] is False
    # Anche con spectral vuoto
    out = interpret_in_context(hum_res, {}, {})
    assert out["interpretation_hint"]["likely_musical_harmonic"] is False
