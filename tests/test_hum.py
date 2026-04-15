"""Test: hum check con baseline locale.

Regressione principale: baseline locale, non globale.
Fixture:
- sine_50hz.wav: seno 50 Hz + pink noise basso. Atteso: verdetto 'forte' o 'presente' a 50 Hz.
- pink_noise.wav: solo pink noise. Atteso: verdetto 'trascurabile' ovunque (no falso positivo).
"""
from pathlib import Path
import pytest

from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.hum import hum_check


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
