import pytest
from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.io_loader import load_audio_mono
from scripts.ecoacoustic import ecoacoustic_summary, compute_aci, compute_ndsi, compute_entropy_h


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
