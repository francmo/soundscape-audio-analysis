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
from scripts.report_pdf import build_report, _build_speech_block, _build_executive_summary
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


def test_speech_block_escapes_xml_dynamic_text(tmp_path):
    """Trascritti, segmenti e nome file con '&' o '<' non devono rompere il
    ParaParser (v0.18.1, finding audit). Il build del documento forza il
    parsing del markup, senza escape solleverebbe ValueError."""
    from reportlab.platypus import SimpleDocTemplate
    styles = report_styles.build_styles(report_styles.register_fonts())
    speech = {
        "enabled": True,
        "model_name": "Whisper large-v3",
        "device": "cpu",
        "compute_type": "int8",
        "language_detected": "it",
        "language_probability": 0.96,
        "duration_speech_s": 4.0,
        "duration_total_s": 10.0,
        "n_vad_segments": 1,
        "segments": [
            {"t_start_s": 0.0, "t_end_s": 2.0, "text": "vento & onde <soffio>"},
        ],
        "transcript": "vento & onde <soffio>",
        "transcript_it": "vento & onde <soffio>",
        "translation_fallback": False,
    }
    flowables = _build_speech_block(speech, "vento & onde", styles)
    out = tmp_path / "speech_escape.pdf"
    SimpleDocTemplate(str(out)).build(flowables)
    assert out.exists()


def test_executive_summary_reads_real_summary_keys():
    """La sintesi iniziale legge le chiavi reali del summary (v0.18.1):
    score_5, lufs.true_peak_db, hum.overall_verdict,
    clap.academic_hints.krause.distribution, classifier.top_global."""
    from reportlab.platypus import Table as RLTable
    styles = report_styles.build_styles(report_styles.register_fonts())
    summary = {
        "metadata": {"duration_s": 62.0, "sr": 48000, "channels": 2},
        "technical": {
            "levels": {"dynamic_range_db": 18.4},
            "lufs": {"integrated_lufs": -23.5, "lra": 6.0, "true_peak_db": -1.27},
        },
        "spectral": {"hifi_lofi": {"label": "hi-fi", "score_5": 4}},
        "hum": {"overall_verdict": "sospetto"},
        "ecoacoustic": {},
        "clap": {
            "academic_hints": {
                "krause": {"distribution": {
                    "biofonia": 0.62, "antropofonia": 0.28, "geofonia": 0.10,
                }},
            },
            "top_global": [{"prompt": "canto di uccelli & vento", "score": 0.41}],
        },
        "semantic": {"classifier": {"top_global": [{"name": "Bird", "score": 0.35}]}},
        "structure": {"sections": [{}]},
    }
    flow = _build_executive_summary(summary, styles)
    table = next(f for f in flow if isinstance(f, RLTable))
    cells = []
    for row in table._cellvalues:
        for c in row:
            cells.append(getattr(c, "text", str(c)))
    joined = " | ".join(cells)
    assert "4/5" in joined and "None/5" not in joined
    assert "-1.27" in joined             # true peak reale, non "n.d."
    assert "sospetto" in joined          # verdetto hum reale, non "entro baseline"
    assert "biofonia 62%" in joined      # triade Krause dagli academic hints
    assert "uccelli (0.35)" in joined    # top_global PANNs tradotto
    assert "canto di uccelli" in joined  # riga CLAP presente, escapata senza crash


def test_merge_panns_timeline_compacts_consecutive_top1():
    """La timeline compattata unisce i segmenti consecutivi con lo stesso
    top-1 e conserva gli score per la media (v0.19.0)."""
    from scripts.report_pdf import _merge_panns_timeline
    tl = [
        {"t_start_s": 0, "t_end_s": 10,
         "top": [{"name": "Bird", "score": 0.4}, {"name": "Wind", "score": 0.1}]},
        {"t_start_s": 10, "t_end_s": 20,
         "top": [{"name": "Bird", "score": 0.2}, {"name": "Water", "score": 0.1}]},
        {"t_start_s": 20, "t_end_s": 30,
         "top": [{"name": "Vehicle", "score": 0.5}]},
    ]
    merged = _merge_panns_timeline(tl)
    assert len(merged) == 2
    assert merged[0]["top1"] == "Bird"
    assert merged[0]["t_end_s"] == 20
    assert merged[0]["scores"] == [0.4, 0.2]
    assert sorted(merged[0]["others"]) == ["Water", "Wind"]
    assert merged[1]["top1"] == "Vehicle"


def test_semantic_block_renders_citable_timeline_table(tmp_path):
    """La sezione semantica include la tabella timeline citabile e regge
    label con caratteri XML speciali (v0.19.0)."""
    from reportlab.platypus import SimpleDocTemplate
    from scripts.report_pdf import _build_semantic_block
    styles = report_styles.build_styles(report_styles.register_fonts())
    semantic = {
        "enabled": True,
        "classifier": {
            "model_name": "PANNs CNN14",
            "top_global": [{"name": "Bird", "score": 0.4}],
            "top_dominant_frames": [],
            "timeline": [
                {"t_start_s": 0, "t_end_s": 10,
                 "top": [{"name": "Bird", "score": 0.4}]},
                {"t_start_s": 10, "t_end_s": 20,
                 "top": [{"name": "Vehicle & co", "score": 0.3}]},
            ],
        },
    }
    flow = _build_semantic_block(semantic, styles)
    rendered = ""
    for f in flow:
        if hasattr(f, "text"):
            rendered += f.text + "\n"
    assert "Timeline per segmento" in rendered
    out = tmp_path / "semantic_timeline.pdf"
    SimpleDocTemplate(str(out)).build(flow)
    assert out.exists()


def test_build_pdf_with_xml_specials_in_filename(tmp_path):
    """Un nome file con '&' e '<' deve produrre il PDF senza errori del
    ParaParser (copertina + tabella metadati, v0.18.1)."""
    path = FIXTURES_DIR / "pink_noise.wav"
    y, sr = load_audio_mono(path)
    duration = len(y) / sr
    meta = dict(load_metadata(path))
    meta["filename"] = "vento & onde <prova>.wav"
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
                               tmp_path / "graphics", "amp")
    summary = {
        "metadata": meta, "technical": tech, "hum": hum,
        "spectral": spec, "ecoacoustic": eco,
        "semantic": {"enabled": False}, "multichannel": None,
    }
    out = tmp_path / "amp_report.pdf"
    build_report(summary, out, rank_grm=[], agent_text=None, plot_paths=plots)
    assert out.exists()
