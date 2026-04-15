"""Smoke test: il PDF viene generato, ha dimensione minima, contiene stringhe italiane."""
from pathlib import Path
import pytest

from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.io_loader import load_metadata, load_audio_mono
from scripts.technical import technical_summary
from scripts.hum import hum_check
from scripts.spectral import spectral_summary, compute_stft_mean, hifi_lofi_score
from scripts.ecoacoustic import ecoacoustic_summary
from scripts.plotting import generate_all_plots
from scripts.report_pdf import build_report


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


def test_build_pdf_pink(tmp_path):
    path = FIXTURES_DIR / "pink_noise.wav"
    y, sr = load_audio_mono(path)
    duration = len(y) / sr
    meta = load_metadata(path)
    tech = technical_summary(path, y)
    hum = hum_check(path)
    spec = spectral_summary(y, sr, duration)
    spec["hifi_lofi"] = hifi_lofi_score(
        tech["levels"]["dynamic_range_db"],
        spec["timbre"]["spectral_flatness"],
    )
    eco = ecoacoustic_summary(y, sr)
    S, spectrum, freqs = compute_stft_mean(y, sr)
    plots = generate_all_plots(y, sr, spectrum, freqs,
                               spec["bands_schafer"], hum,
                               tmp_path / "graphics", "pink")
    summary = {
        "metadata": meta, "technical": tech, "hum": hum,
        "spectral": spec, "ecoacoustic": eco,
        "semantic": {"enabled": False}, "multichannel": None,
    }
    out = tmp_path / "pink_report.pdf"
    build_report(summary, out, rank_grm=[], agent_text=None, plot_paths=plots)
    assert out.exists()
    assert out.stat().st_size > 20_000  # almeno 20 KB
