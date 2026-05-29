import pytest
from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.io_loader import load_audio_mono
from scripts.ecoacoustic import ecoacoustic_summary, compute_aci, compute_ndsi, compute_entropy_h, ndsi_water_caveat


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


def test_summary_pink():
    y, sr = load_audio_mono(FIXTURES_DIR / "pink_noise.wav")
    out = ecoacoustic_summary(y, sr)
    assert "aci" in out
    assert "ndsi" in out
    assert "h_entropy" in out
    assert "bi" in out
    assert -1 <= out["ndsi"]["ndsi"] <= 1
    assert 0 <= out["h_entropy"]["h_total"] <= 1


def test_aci_sine_vs_transient():
    """Transient dense deve avere ACI più alto di un seno puro."""
    y1, sr = load_audio_mono(FIXTURES_DIR / "sine_50hz.wav")
    y2, _ = load_audio_mono(FIXTURES_DIR / "transient_dense.wav")
    aci_sine = compute_aci(y1, sr)
    aci_trans = compute_aci(y2, sr)
    assert aci_trans > aci_sine


def test_h_bounds():
    y, sr = load_audio_mono(FIXTURES_DIR / "pink_noise.wav")
    h = compute_entropy_h(y, sr)
    for k in ("h_total", "h_spectral", "h_temporal"):
        assert 0 <= h[k] <= 1


# --- v0.14 INT-5: caveat NDSI su ambienti idrici ---

def test_ndsi_caveat_fires_on_water_dominant_band():
    """Caso A: NDSI alto ma banda 2-8 kHz dominata dall'acqua."""
    nd = {"ndsi": 0.711, "biophony_energy": 16.7, "anthropophony_energy": 2.8}
    classifier = {"top_global": [{"name": "Water", "score": 0.1613},
                                 {"name": "Animal", "score": 0.045}]}
    out = ndsi_water_caveat(nd, classifier)
    assert "caveat" in out
    assert out["caveat"]["type"] == "water_dominant_biophony_band"
    assert out["ndsi"] == 0.711  # valore non alterato


def test_ndsi_caveat_absent_on_real_biophony():
    """Guardia: con biofonia animale reale (Bird) e poca acqua, niente caveat."""
    nd = {"ndsi": 0.6}
    classifier = {"top_global": [{"name": "Bird", "score": 0.34},
                                 {"name": "Water", "score": 0.02}]}
    out = ndsi_water_caveat(nd, classifier)
    assert "caveat" not in out


def test_ndsi_caveat_absent_on_low_ndsi():
    """Su NDSI basso (non biofonico) il caveat non si applica."""
    nd = {"ndsi": 0.1}
    classifier = {"top_global": [{"name": "Water", "score": 0.5}]}
    out = ndsi_water_caveat(nd, classifier)
    assert "caveat" not in out
