from pathlib import Path
import pytest

from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.io_loader import load_metadata, load_audio_mono
from scripts.technical import compute_levels, compute_lufs, detect_clipping, detect_dc_offset


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


def test_metadata_pink_noise():
    meta = load_metadata(FIXTURES_DIR / "pink_noise.wav")
    assert meta["codec"]
    assert meta["sr"] == 22050
    assert meta["channels"] == 1
    assert 2.5 < meta["duration_s"] < 3.5


def test_levels_pink_noise():
    y, sr = load_audio_mono(FIXTURES_DIR / "pink_noise.wav")
    lvl = compute_levels(y)
    # Peak vicino al livello target -10 dBFS
    assert -12 < lvl["peak_dbfs"] < -5
    # RMS sotto il peak
    assert lvl["rms_dbfs"] < lvl["peak_dbfs"]
    # Dinamica di un rumore costante è bassa
    assert lvl["dynamic_range_db"] < 15


def test_clipping_none():
    y, _ = load_audio_mono(FIXTURES_DIR / "pink_noise.wav")
    clip = detect_clipping(y)
    assert clip["samples"] == 0
    assert clip["verdict"] == "assente"


def test_dc_offset_negligible():
    y, _ = load_audio_mono(FIXTURES_DIR / "pink_noise.wav")
    dc = detect_dc_offset(y)
    assert abs(dc["offset"]) < 0.005
    assert dc["verdict"] == "ok"


def test_lufs_smoke():
    """Smoke test: LUFS deve ritornare un numero ragionevole."""
    lufs = compute_lufs(FIXTURES_DIR / "pink_noise.wav")
    assert lufs.get("integrated_lufs") is not None
    # pink_noise -20 dBFS ~ -25/-30 LUFS
    assert -40 < lufs["integrated_lufs"] < -10
