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
from scripts.report_pdf import build_report, _build_speech_block
from scripts import report_styles


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


def test_build_speech_block_empty_on_disabled():
    """Se speech e' disabled o skipped, la sezione non produce flowables."""
    styles = report_styles.build_styles(report_styles.register_fonts())
    assert _build_speech_block({}, "file", styles) == []
    assert _build_speech_block(
        {"enabled": False, "reason": "disabled"}, "file", styles
    ) == []
    assert _build_speech_block(
        {"enabled": True, "skipped_reason": "insufficient_speech"},
        "file", styles
    ) == []


def test_build_speech_block_italian_accents():
    """Il block gestisce correttamente accenti italiani senza crash
    ReportLab (verifica font OFL con Unicode)."""
    styles = report_styles.build_styles(report_styles.register_fonts())
    speech = {
        "enabled": True,
        "model_name": "Whisper large-v3",
        "device": "cpu",
        "compute_type": "int8",
        "language_detected": "it",
        "language_probability": 0.96,
        "duration_speech_s": 12.0,
        "duration_total_s": 30.0,
        "n_vad_segments": 3,
        "segments": [
            {"t_start_s": 0.0, "t_end_s": 4.5,
             "text": "Perché la città è silenziosa?"},
            {"t_start_s": 5.0, "t_end_s": 9.0,
             "text": "Ciò che già avveniva più spesso."},
        ],
        "transcript": "Perché la città è silenziosa?\nCiò che già avveniva più spesso.",
        "transcript_it": "Perché la città è silenziosa?\nCiò che già avveniva più spesso.",
        "translation_fallback": False,
    }
    flowables = _build_speech_block(speech, "test_base", styles)
    assert len(flowables) > 0


def test_build_speech_block_long_transcript_uses_companion():
    """Se transcript supera TRANSCRIPT_PDF_MAX_CHARS, il block fa riferimento
    al file .txt companion invece di inlinearlo."""
    from scripts import config
    styles = report_styles.build_styles(report_styles.register_fonts())
    long_transcript = "x " * (config.TRANSCRIPT_PDF_MAX_CHARS // 2 + 100)
    speech = {
        "enabled": True,
        "model_name": "Whisper large-v3",
        "device": "cpu",
        "compute_type": "int8",
        "language_detected": "en",
        "language_probability": 0.99,
        "duration_speech_s": 120.0,
        "duration_total_s": 180.0,
        "n_vad_segments": 15,
        "segments": [
            {"t_start_s": 0.0, "t_end_s": 5.0, "text": "Hello everyone."},
        ],
        "transcript": long_transcript,
        "transcript_it": "Ciao a tutti.",
        "translation_fallback": False,
    }
    flowables = _build_speech_block(speech, "audio_file", styles)
    # Estraiamo il testo di tutti i Paragraph per cercare il riferimento al .txt
    rendered_text = ""
    for f in flowables:
        if hasattr(f, "text"):
            rendered_text += f.text + "\n"
    assert "audio_file_transcript.txt" in rendered_text
