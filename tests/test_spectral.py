import pytest
from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.io_loader import load_audio_mono
from scripts.spectral import (
    spectral_summary, compute_stft_mean, compute_bands, onset_analysis,
    compute_bands_schafer_alert,
)


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


def test_spectral_summary_pink():
    y, sr = load_audio_mono(FIXTURES_DIR / "pink_noise.wav")
    duration = len(y) / sr
    out = spectral_summary(y, sr, duration)
    # Almeno le 7 bande
    assert set(out["bands_schafer"].keys()) == {
        "Sub-bass", "Bass", "Low-mid", "Mid", "High-mid", "Presence", "Brilliance"
    }
    # Le 7 bande (20 Hz-sr/2) coprono la maggior parte dell'energia audio.
    # Per pink noise una quota resta sotto 20 Hz, accettiamo >50%.
    total = sum(b["energy_pct"] for b in out["bands_schafer"].values())
    assert 50 < total <= 100, f"somma bande anomala: {total}"


def test_bands_dominant_on_sine_50():
    y, sr = load_audio_mono(FIXTURES_DIR / "sine_50hz.wav")
    _S, spec, freqs = compute_stft_mean(y, sr)
    bands = compute_bands(spec, freqs, sr)
    # La banda Sub-bass deve essere dominante
    dominant = max(bands.items(), key=lambda kv: kv[1]["energy_pct"])[0]
    assert dominant == "Sub-bass", f"dominant era {dominant}"


def test_onset_density_label_sparse_vs_dense():
    y1, sr1 = load_audio_mono(FIXTURES_DIR / "pink_noise.wav")
    d1 = len(y1) / sr1
    o1 = onset_analysis(y1, sr1, d1)
    y2, sr2 = load_audio_mono(FIXTURES_DIR / "transient_dense.wav")
    d2 = len(y2) / sr2
    o2 = onset_analysis(y2, sr2, d2)
    # I transient_dense devono avere density maggiore o uguale al pink
    assert o2["events_per_sec"] >= o1["events_per_sec"]


# =====================================================================
# v0.13.0 (Intervento B dossier P&T): alert sub-bass+bass anomalo.
# =====================================================================


def test_bands_alert_triggers_above_threshold():
    """Quando Sub-bass + Bass > 60%, alert ritorna dict con warning e
    messaggio italiano. Caso scuola: B 41.48 + 40.66 = 82.14%."""
    bands = {
        "Sub-bass": {"energy_pct": 41.48},
        "Bass": {"energy_pct": 40.66},
        "Low-mid": {"energy_pct": 5.0},
        "Mid": {"energy_pct": 5.0},
        "High-mid": {"energy_pct": 4.0},
        "Presence": {"energy_pct": 2.0},
        "Brilliance": {"energy_pct": 1.86},
    }
    alert = compute_bands_schafer_alert(bands)
    assert alert is not None
    assert alert["level"] == "warning"
    assert alert["low_sum_pct"] == pytest.approx(82.14, abs=0.01)
    assert "sub-bass+bass" in alert["message"].lower()
    assert "handling" in alert["message"]


def test_bands_alert_silent_below_threshold():
    """Sotto soglia, alert ritorna None. Caso tipico: A bagno
    domestico, distribuzione bilanciata."""
    bands = {
        "Sub-bass": {"energy_pct": 12.0},
        "Bass": {"energy_pct": 18.0},
        "Low-mid": {"energy_pct": 15.0},
        "Mid": {"energy_pct": 20.0},
        "High-mid": {"energy_pct": 18.0},
        "Presence": {"energy_pct": 10.0},
        "Brilliance": {"energy_pct": 7.0},
    }
    alert = compute_bands_schafer_alert(bands)
    assert alert is None


def test_bands_alert_custom_threshold():
    """Soglia configurabile."""
    bands = {
        "Sub-bass": {"energy_pct": 25.0},
        "Bass": {"energy_pct": 20.0},
    }
    # 45% sub+bass: sotto default 60%, sopra soglia custom 40%
    assert compute_bands_schafer_alert(bands) is None
    assert compute_bands_schafer_alert(bands, threshold_pct=40.0) is not None


def test_spectral_summary_includes_bands_alert_field():
    """spectral_summary deve sempre includere il campo bands_schafer_alert,
    None se sotto soglia. Su pink_noise (distribuzione roughly piatta),
    sub-bass+bass non dovrebbe superare 60%."""
    y, sr = load_audio_mono(FIXTURES_DIR / "pink_noise.wav")
    duration = len(y) / sr
    out = spectral_summary(y, sr, duration)
    assert "bands_schafer_alert" in out
