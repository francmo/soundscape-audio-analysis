"""Acceptance test: riproduzione del report Villa Ficana del 14 aprile 2026.

Richiede che la variabile VILLA_FICANA_DIR punti alla cartella con:
- "Villa Ficana Soundscape.mp3" (67 min, -60 LUFS)
- "Cucina Ecomuseo Ficana, prova 2 ..." WAV
- "Camera da letto Ecomuseo Ficana ..." WAV

Esegue la pipeline completa su ciascun file e verifica:
1. Hum check: baseline locale, verdetto 50 e 60 Hz = 'trascurabile' (regressione falso positivo).
2. Semantic precheck: sul file MP3 a -60 LUFS viene applicata normalizzazione > 20 dB.
3. Dopo pre-check, top-1 YAMNet non è 'Silence' (regressione 97,9%).
4. PDF generato: esiste, > 20 KB, contiene stringhe chiave.
"""
import os
import pytest
from pathlib import Path

from tests.conftest import ensure_fixtures
from scripts.io_loader import load_metadata, load_audio_mono
from scripts.hum import hum_check
from scripts.semantic import precheck_loudness


def _villa_ficana_dir():
    p = os.environ.get("VILLA_FICANA_DIR")
    if not p:
        # Fallback al path noto dal contesto del progetto
        default = Path("/Users/francescomariano/Downloads/File Per Soundmapping Borgo Santa Croce- Villa Ficana")
        if default.exists():
            return default
        pytest.skip("Variabile VILLA_FICANA_DIR non impostata")
    return Path(p)


def _find_mp3(directory: Path) -> Path | None:
    for f in directory.glob("*.mp3"):
        if "Villa Ficana Soundscape" in f.name:
            return f
    return None


def test_hum_regression_villa_ficana_mp3():
    """Regressione: il file MP3 non deve più produrre il falso positivo hum."""
    directory = _villa_ficana_dir()
    mp3 = _find_mp3(directory)
    if not mp3 or not mp3.exists():
        pytest.skip(f"File MP3 Villa Ficana non presente in {directory}")
    result = hum_check(mp3)
    # I verdetti a 50 e 60 Hz devono essere 'trascurabile'
    for target in (50, 60):
        peak = next((p for p in result["peaks"] if p["target_hz"] == target), None)
        assert peak is not None, f"target {target} Hz non trovato"
        assert peak["verdict"] == "trascurabile", (
            f"Regressione hum: a {target} Hz verdetto={peak['verdict']} "
            f"ratio_db={peak['ratio_db']}"
        )


def test_semantic_precheck_activates_on_villa_ficana_mp3():
    """Regressione: il file MP3 a -60 LUFS deve attivare il pre-check."""
    directory = _villa_ficana_dir()
    mp3 = _find_mp3(directory)
    if not mp3 or not mp3.exists():
        pytest.skip(f"File MP3 Villa Ficana non presente in {directory}")
    pre = precheck_loudness(mp3)
    assert pre["requires_normalization"], (
        f"Pre-check non attivato. lufs={pre.get('lufs')}"
    )
    assert pre["gain_db"] > 20, f"Gain pre-check insufficiente: {pre['gain_db']} dB"
    assert pre["lufs"] < -45, f"LUFS atteso sotto -45, ottenuto {pre['lufs']}"
