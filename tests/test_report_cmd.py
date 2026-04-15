"""Test del sotto-comando `soundscape report` (v0.3.0).

I test lavorano sulle fixture audio esistenti in `tests/fixtures/`.
Non richiedono `claude` nel PATH: usano `--no-synth` oppure simulano il
fallback.
"""
import json
import pytest
from pathlib import Path

from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts import report_cmd as rc
from scripts import comparison_plots as cp


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


def test_iter_audio_paths(tmp_path):
    # Crea tre wav fittizi + un txt da ignorare
    (tmp_path / "a.wav").write_bytes(b"RIFF")
    (tmp_path / "b.mp3").write_bytes(b"ID3")
    (tmp_path / "ignoreme.txt").write_text("not audio")
    (tmp_path / "c.flac").write_bytes(b"fLaC")
    paths = rc._iter_audio_paths(tmp_path)
    names = [p.name for p in paths]
    assert set(names) == {"a.wav", "b.mp3", "c.flac"}


def test_summary_cache_valid_true(tmp_path):
    audio = tmp_path / "file.wav"
    audio.write_bytes(b"x")
    summary = tmp_path / "file_summary.json"
    summary.write_text("{}")
    # Summary è appena scritto quindi è più recente del wav
    import time
    time.sleep(0.01)
    import os
    os.utime(summary, None)  # forza mtime corrente
    assert rc._summary_cache_valid(audio, summary)


def test_summary_cache_valid_false_when_audio_newer(tmp_path):
    audio = tmp_path / "file.wav"
    summary = tmp_path / "file_summary.json"
    summary.write_text("{}")
    # Tocca l'audio dopo: summary è più vecchio
    import time
    time.sleep(0.02)
    audio.write_bytes(b"x")
    assert not rc._summary_cache_valid(audio, summary)


def test_summary_cache_valid_false_when_missing(tmp_path):
    audio = tmp_path / "file.wav"
    audio.write_bytes(b"x")
    summary = tmp_path / "file_summary.json"
    assert not rc._summary_cache_valid(audio, summary)


def test_run_corpus_report_smoke(tmp_path):
    """Smoke test: due fixture audio + no_synth, verifica artefatti prodotti.

    Non invoca claude. Verifica che il PDF di corpus viene prodotto con
    placeholder per la sintesi.
    """
    # Prepara corpus con 2 fixture WAV
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    import shutil
    shutil.copy(FIXTURES_DIR / "pink_noise.wav", corpus_dir / "pink_noise.wav")
    shutil.copy(FIXTURES_DIR / "transient_dense.wav", corpus_dir / "transient_dense.wav")

    out_dir = tmp_path / "out"
    meta = rc.run_corpus_report(
        folder=corpus_dir,
        output_dir=out_dir,
        corpus_title="Test Corpus",
        rerun=False,
        yes=True,
        model="opus",
        no_synth=True,
    )

    assert meta["n_files"] == 2
    assert meta["synth_fallback"] is True  # no_synth attivo
    pdf_path = Path(meta["pdf_path"])
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 20_000  # almeno 20 KB

    # Verifica almeno 4 grafici comparativi (CLAP skippato se no embedding)
    plots_dir = out_dir / "comparison"
    assert plots_dir.exists()
    pngs = list(plots_dir.glob("*.png"))
    assert len(pngs) >= 4

    # Verifica metadata di run
    run_meta_path = out_dir / "corpus_run_metadata.json"
    assert run_meta_path.exists()

    # Verifica prompt salvato
    prompt_path = out_dir / "corpus_synth_prompt.md"
    assert prompt_path.exists()
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "Test Corpus" in prompt_text
    assert "{GOLDEN_PATH}" not in prompt_text  # tutti i placeholder risolti
    assert "{CORPUS_TITLE}" not in prompt_text


def test_merge_markdown_into_pdf(tmp_path):
    """Genera PDF parziale, scrive un markdown fittizio, lancia merge, verifica."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    import shutil
    shutil.copy(FIXTURES_DIR / "pink_noise.wav", corpus_dir / "pink_noise.wav")
    shutil.copy(FIXTURES_DIR / "sine_50hz.wav", corpus_dir / "sine_50hz.wav")

    out_dir = tmp_path / "out"
    meta = rc.run_corpus_report(
        folder=corpus_dir,
        output_dir=out_dir,
        corpus_title="Merge Test",
        yes=True,
        no_synth=True,
    )

    pdf_path = Path(meta["pdf_path"])
    size_before = pdf_path.stat().st_size

    # Scrivi un markdown fittizio con contenuti riconoscibili
    md_path = out_dir / "fake_synth.md"
    md_path.write_text(
        "# Sintesi di test\n\n"
        "Questo è un paragrafo che contiene la stringa riconoscibile XYZMERGE123.\n\n"
        "## Sezione 2\n\n"
        "Altro contenuto con accenti: perché, più, già.\n",
        encoding="utf-8"
    )

    new_pdf = rc.merge_markdown_into_pdf(pdf_path, md_path)
    assert new_pdf.exists()

    # Il PDF dovrebbe essere cambiato (contiene ora il testo della sintesi)
    size_after = new_pdf.stat().st_size
    assert size_after != size_before

    # Ricarica metadata
    run_meta = json.loads((out_dir / "corpus_run_metadata.json").read_text())
    assert run_meta["synth_fallback"] is False
    assert run_meta["synth_md_path"] == str(md_path)
