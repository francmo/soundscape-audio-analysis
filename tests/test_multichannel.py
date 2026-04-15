import pytest
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
