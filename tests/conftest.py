"""Configurazione pytest condivisa."""
import sys
from pathlib import Path

# Aggiunge la skill root al sys.path per import scripts.*
SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def ensure_fixtures():
    """Genera le fixture se non esistono ancora."""
    wavs = ["sine_50hz.wav", "pink_noise.wav", "silence_low.wav",
            "transient_dense.wav", "multichannel_714.wav"]
    missing = [w for w in wavs if not (FIXTURES_DIR / w).exists()]
    if missing:
        from tests.fixtures.make_fixtures import main as make_main
        make_main()
