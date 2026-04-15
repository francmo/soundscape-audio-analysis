import pytest
from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.semantic import precheck_loudness


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


def test_precheck_triggers_on_silence_low():
    """Il fixture silence_low.wav è a ~-60 LUFS: precheck deve attivarsi."""
    pre = precheck_loudness(FIXTURES_DIR / "silence_low.wav")
    assert pre["requires_normalization"], (
        f"precheck non attivato. lufs={pre.get('lufs')}"
    )
    assert pre["gain_db"] > 20


def test_precheck_no_trigger_on_transient_dense():
    """Il fixture transient_dense.wav ha LUFS intorno a -25: precheck non deve attivarsi."""
    pre = precheck_loudness(FIXTURES_DIR / "transient_dense.wav")
    assert not pre["requires_normalization"], (
        f"precheck falso positivo. lufs={pre.get('lufs')}"
    )
