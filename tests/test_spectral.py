import pytest
from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.io_loader import load_audio_mono
from scripts.spectral import spectral_summary, compute_stft_mean, compute_bands, onset_analysis


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
