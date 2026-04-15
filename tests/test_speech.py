"""Test del modulo scripts/speech.py (v0.5.0).

Copre disabled/empty, pre-filtro VAD su silenzio (Whisper NON caricato),
no-op traduzione se lingua italiana, fallback se claude non in PATH,
chunking sopra soglia. Il test Whisper reale e' skippato se fixture
`tests/fixtures/speech_italian.wav` non esiste.
"""
import subprocess
import sys

import numpy as np
import pytest

from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts import speech, config
from scripts.io_loader import load_audio_mono


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Ogni test parte con singleton ripuliti per isolamento."""
    speech._TRANSCRIBER_SINGLETON = None
    speech._VAD_SINGLETON = None
    yield


def test_speech_summary_disabled():
    out = speech.speech_summary(None, 0, enable=False, duration_total_s=0)
    assert out["enabled"] is False
    assert out["reason"] == "disabled"


def test_speech_summary_empty_waveform():
    out = speech.speech_summary(
        np.array([], dtype=np.float32), 16000, enable=True, duration_total_s=0
    )
    assert out["enabled"] is True
    assert out["reason"] == "empty_waveform"


def test_silero_vad_skip_on_silence(monkeypatch):
    """Fixture silence_low.wav (4 s pink noise basso): VAD non deve trovare
    parlato, Whisper NON deve essere caricato."""
    y, sr = load_audio_mono(FIXTURES_DIR / "silence_low.wav")

    # Monkeypatch: se Whisper viene caricato, solleva per fare fallire il test
    def _boom(*args, **kwargs):
        raise AssertionError("Whisper caricato su audio senza parlato!")
    monkeypatch.setattr(speech.SpeechTranscriber, "_ensure_loaded", _boom)

    out = speech.speech_summary(
        y, sr, enable=True, duration_total_s=len(y) / sr
    )
    assert out["enabled"] is True
    assert out["skipped_reason"] == "insufficient_speech"
    assert out["duration_speech_s"] < config.SILERO_VAD_MIN_TOTAL_SPEECH_S
    assert out["segments"] == []


def test_translation_noop_if_italian():
    speech_dict = {
        "enabled": True,
        "transcript": "Ciao, questa e' una trascrizione.",
        "language_detected": "it",
    }
    out = speech.translate_transcript(speech_dict)
    assert out["transcript_it"] == speech_dict["transcript"]
    assert out["translation_fallback"] is False
    assert out["translation_model"] == ""


def test_translation_fallback_if_claude_missing(monkeypatch, capsys):
    """Se shutil.which('claude') ritorna None, fallback con warning stderr."""
    monkeypatch.setattr(speech.shutil, "which", lambda _: None)
    speech_dict = {
        "enabled": True,
        "transcript": "Hello, this is a test.",
        "language_detected": "en",
    }
    out = speech.translate_transcript(speech_dict)
    assert out["transcript_it"] == speech_dict["transcript"]
    assert out["translation_fallback"] is True
    captured = capsys.readouterr()
    assert "claude non in PATH" in captured.err


def test_translation_chunking_above_threshold(monkeypatch):
    """Transcript di 10000 caratteri deve essere spezzato in piu' chiamate
    a claude -p. Monkeypatch cattura chiamate subprocess."""
    calls: list[str] = []

    def fake_run(cmd, input=None, capture_output=None, text=None,
                  encoding=None, timeout=None):
        calls.append(input)

        class _R:
            returncode = 0
            stdout = "traduzione_" + str(len(calls))
            stderr = ""
        return _R()

    monkeypatch.setattr(speech.shutil, "which", lambda _: "/usr/bin/claude")
    monkeypatch.setattr(speech.subprocess, "run", fake_run)

    long_text = ("parola " * 2000)[:10000]  # ~10000 caratteri
    speech_dict = {
        "enabled": True,
        "transcript": long_text,
        "language_detected": "en",
    }
    out = speech.translate_transcript(speech_dict)
    assert out["translation_fallback"] is False
    # Con soglia 8000, size 6000, overlap 500 -> almeno 2 chunk
    assert len(calls) >= 2, f"Chunking non avvenuto: {len(calls)} chiamate"


def test_translation_short_single_call(monkeypatch):
    """Transcript corto: una sola chiamata a claude -p."""
    calls: list[str] = []

    def fake_run(cmd, input=None, **kwargs):
        calls.append(input)

        class _R:
            returncode = 0
            stdout = "Ciao, questo e' un test."
            stderr = ""
        return _R()

    monkeypatch.setattr(speech.shutil, "which", lambda _: "/usr/bin/claude")
    monkeypatch.setattr(speech.subprocess, "run", fake_run)

    speech_dict = {
        "enabled": True,
        "transcript": "Hello, this is a test.",
        "language_detected": "en",
    }
    out = speech.translate_transcript(speech_dict)
    assert len(calls) == 1
    assert out["transcript_it"] == "Ciao, questo e' un test."
    assert out["translation_model"] == config.TRANSLATION_MODEL


def test_translation_timeout_fallback(monkeypatch, capsys):
    """Se claude -p va in timeout, fallback a transcript originale."""
    def fake_run(cmd, input=None, timeout=None, **kwargs):
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr(speech.shutil, "which", lambda _: "/usr/bin/claude")
    monkeypatch.setattr(speech.subprocess, "run", fake_run)

    speech_dict = {
        "enabled": True,
        "transcript": "Hello world.",
        "language_detected": "en",
    }
    out = speech.translate_transcript(speech_dict)
    assert out["translation_fallback"] is True
    assert out["transcript_it"] == "Hello world."
    captured = capsys.readouterr()
    assert "Traduzione fallita" in captured.err


def test_check_speech_suggestion_returns_pct_when_dominant():
    """PANNs ha Speech con pct > soglia, flag non attivo: ritorna pct."""
    semantic_res = {
        "classifier": {
            "top_dominant_frames": [
                {"name": "Speech", "pct": 62.5},
                {"name": "Music", "pct": 15.0},
            ]
        }
    }
    pct = speech.check_speech_suggestion(semantic_res, flag_active=False)
    assert pct == 62.5


def test_check_speech_suggestion_none_if_flag_active():
    """Se il flag --speech e' gia' attivo, nessun suggerimento."""
    semantic_res = {
        "classifier": {
            "top_dominant_frames": [{"name": "Speech", "pct": 80.0}]
        }
    }
    pct = speech.check_speech_suggestion(semantic_res, flag_active=True)
    assert pct is None


def test_check_speech_suggestion_none_below_threshold():
    """Speech presente ma sotto soglia 25%: nessun suggerimento."""
    semantic_res = {
        "classifier": {
            "top_dominant_frames": [{"name": "Speech", "pct": 10.0}]
        }
    }
    pct = speech.check_speech_suggestion(semantic_res, flag_active=False)
    assert pct is None


def test_check_speech_suggestion_none_if_no_speech_label():
    """top_dominant_frames senza 'Speech': nessun suggerimento."""
    semantic_res = {
        "classifier": {
            "top_dominant_frames": [
                {"name": "Music", "pct": 40.0},
                {"name": "Vehicle", "pct": 30.0},
            ]
        }
    }
    pct = speech.check_speech_suggestion(semantic_res, flag_active=False)
    assert pct is None


def test_check_speech_suggestion_none_if_semantic_disabled():
    """Se semantic_res e' vuoto o senza classifier, nessun crash e nessun suggerimento."""
    assert speech.check_speech_suggestion({}, flag_active=False) is None
    assert speech.check_speech_suggestion(
        {"enabled": False}, flag_active=False
    ) is None


@pytest.mark.skipif(
    not (FIXTURES_DIR / "speech_italian.wav").exists(),
    reason="Fixture speech_italian.wav non disponibile. Vedi piano v0.5.0 "
           "per generarla da Common Voice IT (CC0).",
)
def test_whisper_real_transcribe():
    """Test end-to-end su clip reale di parlato italiano (~10 s).

    Scarica automaticamente il checkpoint Whisper large-v3 al primo run
    (~3 GB in ~/.cache/huggingface). Skippato se fixture assente.
    """
    y, sr = load_audio_mono(FIXTURES_DIR / "speech_italian.wav")
    out = speech.speech_summary(
        y, sr, enable=True, duration_total_s=len(y) / sr
    )
    assert out["enabled"] is True
    assert out.get("skipped_reason", "") == ""
    assert out["language_detected"] == "it"
    assert len(out["transcript"]) > 0
    assert len(out["segments"]) > 0
