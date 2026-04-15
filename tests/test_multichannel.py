import numpy as np
import pytest
import soundfile as sf
from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.io_loader import load_audio_multichannel
from scripts.multichannel import multichannel_summary


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


def test_multichannel_714():
    mc = load_audio_multichannel(FIXTURES_DIR / "multichannel_714.wav")
    assert mc["n_channels"] == 12
    assert mc["layout"] == "7.1.4"
    summary = multichannel_summary(mc)
    per_ch = summary["per_channel"]
    labels = [r["label"] for r in per_ch]
    assert labels[0] == "L"
    assert labels[1] == "R"
    assert labels[3] == "LFE"
    assert "Tfl" in labels
    assert "Trr" in labels
    comp = summary["comparison"]
    assert comp["loudest_channel"]
    assert comp["quietest_channel"]


def test_load_multichannel_resample_44100_to_48000_no_off_by_one(tmp_path):
    """Regressione v0.4.1: file stereo 44100 Hz risampleato a 48000 Hz non
    deve piu' scatenare ValueError da off-by-one della pre-allocazione.

    Durata ~88 sec per riprodurre il crash originale con input length che
    genera int(n * 48000/44100) = N e librosa che restituisce N+1.
    """
    sr_orig = 44100
    sr_target = 48000
    duration_s = 88.0
    n = int(duration_s * sr_orig)
    rng = np.random.default_rng(42)
    data = (rng.standard_normal((n, 2)) * 0.05).astype(np.float32)
    wav_path = tmp_path / "stereo_44k.wav"
    sf.write(str(wav_path), data, sr_orig)

    mc = load_audio_multichannel(wav_path, sr=sr_target)
    assert mc["sr"] == sr_target
    assert mc["n_channels"] == 2
    expected = int(n * sr_target / sr_orig)
    assert abs(len(mc["channels"][0]) - expected) <= 2
    # I due canali devono avere la stessa lunghezza dopo l'allineamento
    assert len(mc["channels"][0]) == len(mc["channels"][1])
    # Anche il downmix deve essere coerente
    assert len(mc["downmix_mono"]) == len(mc["channels"][0])


def test_load_multichannel_no_resample_when_sr_matches(tmp_path):
    """Se sr_orig == target sr, la funzione non deve risamplare e deve
    restituire esattamente gli stessi campioni del file originale."""
    sr = 48000
    n = int(2.0 * sr)
    rng = np.random.default_rng(7)
    data = (rng.standard_normal((n, 2)) * 0.05).astype(np.float32)
    wav_path = tmp_path / "stereo_48k.wav"
    # subtype FLOAT per preservare i float32 bit-wise (default WAV e' PCM_16)
    sf.write(str(wav_path), data, sr, subtype="FLOAT")

    mc = load_audio_multichannel(wav_path, sr=sr)
    assert mc["sr"] == sr
    assert len(mc["channels"][0]) == n
    assert len(mc["channels"][1]) == n
    # Verifica bit-wise che i dati siano invariati (nessun resample applicato)
    np.testing.assert_array_equal(mc["channels"][0], data[:, 0])
    np.testing.assert_array_equal(mc["channels"][1], data[:, 1])
