"""Test della release v0.19.2 (compute-once, addendum performance 12/07/2026).

Parity leggera senza modelli reali: bundle di decodifica unica contro i load
storici, compute_timbre con STFT condivisa, spectral_summary con spettro
precomputato, batching dell'inferenza su un classifier fittizio.
"""
import numpy as np
import pytest

from tests.conftest import ensure_fixtures, FIXTURES_DIR
from scripts import config
from scripts import io_loader
from scripts import spectral
from scripts import semantic


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


# ------------------------------------------------------- bundle (A4b)

def test_bundle_matches_legacy_mono():
    import librosa
    p = FIXTURES_DIR / "pink_noise.wav"
    meta = io_loader.load_metadata(p)
    b = io_loader.load_audio_bundle(p, channels_meta=1,
                                    want_panns=True, want_clap=True)
    assert b is not None and b["mc"] is None
    y_old, sr_old = io_loader.load_audio_mono(p)
    assert sr_old == b["sr"]
    assert np.array_equal(b["y"], y_old)
    for key, sr_t in (("y_hum", config.SR_HUM), ("y_panns", config.PANNS_SR),
                      ("y_clap", 48000)):
        y_ref, _ = librosa.load(str(p), sr=sr_t, mono=True)
        assert len(b[key]) == len(y_ref)
        assert np.max(np.abs(b[key] - y_ref)) < 1e-6, key


def test_bundle_matches_legacy_multichannel():
    p = FIXTURES_DIR / "multichannel_714.wav"
    meta = io_loader.load_metadata(p)
    b = io_loader.load_audio_bundle(p, channels_meta=meta["channels"])
    assert b is not None and b["mc"] is not None
    mc_old = io_loader.load_audio_multichannel(p)
    assert b["mc"]["n_channels"] == mc_old["n_channels"]
    assert b["mc"]["layout"] == mc_old["layout"]
    assert np.array_equal(b["mc"]["downmix_mono"], mc_old["downmix_mono"])
    for a, c in zip(b["mc"]["channels"], mc_old["channels"]):
        assert np.array_equal(a, c)


def test_bundle_skips_unsupported_extension(tmp_path):
    fake = tmp_path / "brano.mp3"
    fake.write_bytes(b"not really audio")
    assert io_loader.load_audio_bundle(fake, channels_meta=1) is None


def test_bundle_optional_waveforms():
    p = FIXTURES_DIR / "pink_noise.wav"
    b = io_loader.load_audio_bundle(p, channels_meta=1,
                                    want_panns=False, want_clap=False)
    assert "y_panns" not in b and "y_clap" not in b
    assert "y_hum" in b


# ------------------------------------------- spectral condivisa (A4c)

def test_spectral_summary_with_precomputed_spectrum_identical():
    rng = np.random.default_rng(3)
    sr = 22050
    y = (rng.standard_normal(sr * 6) * 0.2).astype(np.float32)
    dur = len(y) / sr
    base = spectral.spectral_summary(y, sr, dur)
    _S, spectrum, freqs = spectral.compute_stft_mean(y, sr)
    shared = spectral.spectral_summary(y, sr, dur, spectrum=spectrum, freqs=freqs)
    assert base == shared


# -------------------------------------------------- precheck (A4a)

def test_precheck_loudness_uses_provided_lufs(monkeypatch):
    calls = {"n": 0}

    def _boom(path):
        calls["n"] += 1
        return {"integrated_lufs": -50.0}

    monkeypatch.setattr(semantic, "compute_lufs", _boom)
    pre = semantic.precheck_loudness(
        "/non/esiste.wav", lufs_data={"integrated_lufs": -50.0}
    )
    assert calls["n"] == 0  # nessun ffmpeg rilanciato
    assert pre["requires_normalization"] is True
    assert pre["gain_db"] > 0


# ------------------------------------------------- batching (A3)

class _FakeAT:
    """Simula panns_inference.AudioTagging: score = media assoluta del chunk."""

    def __init__(self):
        self.batch_sizes: list[int] = []

    def inference(self, batch):
        self.batch_sizes.append(batch.shape[0])
        n_classes = 527
        out = np.zeros((batch.shape[0], n_classes), dtype=np.float32)
        for i in range(batch.shape[0]):
            out[i, :] = np.mean(np.abs(batch[i]))
        return out, None


def _run_classify(monkeypatch, batch_size, waveform, sr):
    clf = semantic.PANNsClassifier(device="cpu")
    fake = _FakeAT()
    clf._at = fake
    clf._labels = [f"class_{i}" for i in range(527)]
    monkeypatch.setattr(clf, "_ensure_loaded", lambda: None)
    monkeypatch.setattr(config, "INFERENCE_BATCH_SIZE", batch_size)
    res = clf.classify(waveform, sr=sr, segment_seconds=10.0)
    return res, fake


def test_panns_batching_same_results_as_batch1(monkeypatch):
    rng = np.random.default_rng(11)
    sr = 32000
    # 3 chunk pieni + coda di 4 s
    y = (rng.standard_normal(sr * 34) * 0.1).astype(np.float32)
    res1, fake1 = _run_classify(monkeypatch, 1, y, sr)
    res8, fake8 = _run_classify(monkeypatch, 8, y, sr)
    assert fake1.batch_sizes == [1, 1, 1, 1]
    assert fake8.batch_sizes == [3, 1]  # 3 pieni in un batch + coda da sola
    assert res1.frames_total == res8.frames_total == 4
    assert res1.timeline == res8.timeline
    assert res1.top_global == res8.top_global


def test_panns_batching_discards_short_tail(monkeypatch):
    rng = np.random.default_rng(12)
    sr = 32000
    # 2 chunk pieni + coda di 0.3 s (sotto la soglia 0.5 s: scartata)
    y = (rng.standard_normal(int(sr * 20.3)) * 0.1).astype(np.float32)
    res, fake = _run_classify(monkeypatch, 8, y, sr)
    assert res.frames_total == 2
    assert fake.batch_sizes == [2]
