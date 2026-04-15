"""Orchestrazione del sotto-comando `soundscape report` (v0.3.0).

Flusso:
    1. Scan cartella per file audio (whitelist estensioni).
    2. Stima durata totale via ffprobe.
    3. Conferma interattiva sopra soglia (opt-out con `yes`).
    4. Loop di analisi in-process con cache freschezza timestamp.
    5. Raccolta summary + generazione grafici comparativi.
    6. Costruzione prompt + invocazione claude -p non interattivo.
    7. Composizione PDF via `report_pdf.build_corpus_report`.

Riusa `_analyze_single` importandolo da cli.py per non duplicare la pipeline
del singolo file.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime
from pathlib import Path

import click

from . import config
from . import comparison_plots as cp
from . import report_pdf
from . import report_synthesizer as rs
from .agent_payload import build_agent_payload, write_agent_payload
from .io_loader import load_metadata
from .serialization import dump as dump_json, load as load_json
from .utils import ensure_dir, safe_filename


AUDIO_EXT = (".wav", ".mp3", ".flac", ".aiff", ".aif", ".ogg", ".m4a")


def _iter_audio_paths(folder: Path) -> list[Path]:
    results: list[Path] = []
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix.lower() in AUDIO_EXT:
            results.append(p)
    return results


def _estimate_duration_s(path: Path) -> float:
    """Usa ffprobe per stimare la durata. Ritorna 0.0 se fallisce."""
    try:
        meta = load_metadata(path)
        return float(meta.get("duration_s") or 0.0)
    except Exception:
        return 0.0


def _summary_cache_valid(audio_path: Path, summary_path: Path) -> bool:
    """Ritorna True se il summary esiste ed è più recente del file audio."""
    if not summary_path.exists():
        return False
    try:
        return summary_path.stat().st_mtime >= audio_path.stat().st_mtime
    except OSError:
        return False


def _require_confirm(n_files: int, total_duration_s: float, yes: bool) -> bool:
    """Conferma interattiva sopra soglia. Ritorna True per continuare."""
    total_minutes = total_duration_s / 60.0
    if yes:
        return True
    if (n_files <= config.CORPUS_CONFIRM_THRESHOLD_FILES
            and total_minutes <= config.CORPUS_CONFIRM_THRESHOLD_MINUTES):
        return True
    # Stima tempo di elaborazione: ~ durata_audio + 2 min di sintesi
    est_min = total_minutes * 1.2 + 2
    click.echo()
    click.echo(click.style(
        f"Trovati {n_files} file audio, durata totale {total_minutes:.1f} min.",
        fg="yellow", bold=True,
    ))
    click.echo(click.style(
        f"Tempo di elaborazione stimato: circa {est_min:.0f} minuti "
        f"(analisi + sintesi claude).",
        fg="yellow",
    ))
    return click.confirm("Procedere con l'elaborazione?", default=False)


def _run_or_reuse_analyze(
    audio_paths: list[Path],
    output_dir: Path,
    rerun: bool,
) -> list[Path]:
    """Per ogni file: riusa summary se cache valida, altrimenti lancia
    _analyze_single. Ritorna la lista dei summary JSON prodotti (o trovati)."""
    from .cli import _analyze_single

    summary_paths: list[Path] = []
    for i, audio in enumerate(audio_paths, 1):
        base = safe_filename(audio.stem)
        expected_summary = output_dir / f"{base}_summary.json"

        if not rerun and _summary_cache_valid(audio, expected_summary):
            click.echo(click.style(
                f"[{i}/{len(audio_paths)}] {audio.name}: cache valida, skippo",
                fg="green",
            ))
            summary_paths.append(expected_summary)
            continue

        click.echo(click.style(
            f"[{i}/{len(audio_paths)}] Analisi di {audio.name}",
            fg="cyan", bold=True,
        ))
        try:
            r = _analyze_single(
                audio_path=audio,
                output_dir=output_dir,
                do_semantic=True,
                do_birdnet=False,
                ecoacoustic_mode="basic",
                do_agent=False,  # agente invocato una sola volta sul corpus
                multichannel_mode="auto",
                report_format="json",  # niente PDF per singolo file
                compare_mode="none",
                lang="it",
                semantic_backend=None,
                do_clap=True,
                narrative_mode="full",
            )
            summary_json = r.get("summary_json")
            if summary_json:
                summary_paths.append(Path(summary_json))
        except Exception as e:
            click.echo(click.style(
                f"  ERRORE su {audio.name}: {e}", fg="red"
            ))
            continue

    return summary_paths


def run_corpus_report(
    folder: Path,
    output_dir: Path | None = None,
    corpus_title: str | None = None,
    rerun: bool = False,
    yes: bool = False,
    model: str = "opus",
    no_synth: bool = False,
    golden_path: Path | None = None,
) -> dict:
    """Orchestrazione completa del comando `report`.

    Ritorna dict con path finali dei file prodotti.
    """
    folder = Path(folder).resolve()
    if not folder.is_dir():
        raise click.ClickException(f"La cartella {folder} non esiste.")

    corpus_title = corpus_title or folder.name

    # 1. Scansione
    audio_paths = _iter_audio_paths(folder)
    if not audio_paths:
        raise click.ClickException(
            f"Nessun file audio trovato in {folder} (estensioni accettate: {AUDIO_EXT})"
        )
    n_files = len(audio_paths)

    # 2. Stima durata
    click.echo(f"Scansione di {folder} in corso...")
    durations = [_estimate_duration_s(p) for p in audio_paths]
    total_duration_s = sum(durations)

    # 3. Conferma
    if not _require_confirm(n_files, total_duration_s, yes):
        click.echo(click.style("Operazione annullata dall'utente.", fg="yellow"))
        sys.exit(0)

    # 4. Output dir
    if output_dir is None:
        output_dir = folder / "soundscape_report"
    output_dir = ensure_dir(Path(output_dir).resolve())
    click.echo(f"Output in {output_dir}")

    # 5. Analisi dei file
    summary_paths = _run_or_reuse_analyze(audio_paths, output_dir, rerun)
    if not summary_paths:
        raise click.ClickException(
            "Nessun summary JSON prodotto. Controllare gli errori di analisi sopra."
        )

    # 6. Carica i summary
    summaries: list[dict] = []
    for p in summary_paths:
        try:
            summaries.append(load_json(p))
        except Exception as e:
            click.echo(click.style(
                f"Avviso: impossibile caricare {p.name}: {e}", fg="yellow"
            ))

    # 7. Grafici comparativi
    plots_dir = output_dir / "comparison"
    click.echo("Generazione grafici comparativi...")
    plot_paths = cp.generate_all_comparison_plots(summaries, plots_dir)
    for name, path in plot_paths.items():
        click.echo(f"  {name}: {path}")

    # 8. Payload per l'agente
    payloads_dir = output_dir / "agent_payloads"
    ensure_dir(payloads_dir)
    file_payload_paths: list[Path] = []
    for summary in summaries:
        meta = summary.get("metadata", {})
        stem = safe_filename(Path(meta.get("filename", "file")).stem)
        narrative_md = (summary.get("narrative") or {}).get("markdown", "")
        payload_path = payloads_dir / f"{stem}_agent_payload.json"
        write_agent_payload(summary, narrative_md, payload_path)
        file_payload_paths.append(payload_path)

    # 9. Prompt di sintesi
    golden = golden_path or config.GOLDEN_VILLA_FICANA
    template_path = config.TEMPLATES_DIR / "report_synth_prompt.md"
    prompt_text = rs.build_synth_prompt(
        template_path=template_path,
        golden_path=golden,
        corpus_title=corpus_title,
        n_files=n_files,
        total_duration_s=total_duration_s,
        payloads_dir=payloads_dir,
        plots_dir=plots_dir,
        file_payload_paths=file_payload_paths,
        plot_paths=plot_paths,
    )
    prompt_saved_path = output_dir / "corpus_synth_prompt.md"
    prompt_saved_path.write_text(prompt_text, encoding="utf-8")
    click.echo(f"Prompt salvato in {prompt_saved_path}")

    # 10. Sintesi via claude -p (se abilitata e disponibile)
    synth_result = {
        "text": "",
        "fallback_used": True,
        "error": "synthesis skipped (--no-synth)",
        "model": model,
        "elapsed_s": 0.0,
    }
    synth_md_path: Path | None = None
    if not no_synth:
        click.echo(f"Invocazione sintesi via claude (model {model}, timeout "
                   f"{config.CORPUS_REPORT_TIMEOUT_S}s)...")
        synth_result = rs.invoke_corpus_synthesizer(
            prompt_text,
            model=model,
            timeout_s=config.CORPUS_REPORT_TIMEOUT_S,
        )
        if synth_result["fallback_used"]:
            click.echo(click.style(
                f"  Sintesi non completata: {synth_result['error']}",
                fg="yellow",
            ))
        else:
            corpus_slug = safe_filename(corpus_title).replace(" ", "_")
            synth_md_path = output_dir / f"REPORT_ANALISI_{corpus_slug}.md"
            synth_md_path.write_text(synth_result["text"], encoding="utf-8")
            click.echo(click.style(
                f"  Sintesi markdown: {synth_md_path} ({synth_result['elapsed_s']}s)",
                fg="green",
            ))
    else:
        click.echo("Sintesi saltata (--no-synth attivo)")

    # 11. PDF finale
    corpus_slug = safe_filename(corpus_title).replace(" ", "_")
    pdf_path = output_dir / f"{corpus_slug}_corpus_report.pdf"
    corpus_metadata = {
        "n_files": n_files,
        "duration_total_s": total_duration_s,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    synth_note = None
    if synth_result["fallback_used"]:
        synth_note = (
            f"Prompt salvato in: {prompt_saved_path}. "
            f"Errore sintesi: {synth_result['error']}."
        )
    report_pdf.build_corpus_report(
        corpus_title=corpus_title,
        corpus_metadata=corpus_metadata,
        summaries=summaries,
        comparison_plots=plot_paths,
        synth_markdown=synth_result["text"] if not synth_result["fallback_used"] else "",
        output_path=pdf_path,
        synth_available=not synth_result["fallback_used"],
        synth_note=synth_note,
    )
    click.echo(click.style(f"PDF finale: {pdf_path}", fg="green", bold=True))

    # 12. Metadata di run
    run_meta = {
        "version": "0.5.2",
        "corpus_title": corpus_title,
        "n_files": n_files,
        "duration_total_s": total_duration_s,
        "output_dir": str(output_dir),
        "summary_paths": [str(p) for p in summary_paths],
        "plot_paths": {k: str(v) for k, v in plot_paths.items()},
        "prompt_path": str(prompt_saved_path),
        "synth_md_path": str(synth_md_path) if synth_md_path else None,
        "pdf_path": str(pdf_path),
        "synth_fallback": synth_result["fallback_used"],
        "synth_error": synth_result.get("error"),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    run_meta_path = output_dir / "corpus_run_metadata.json"
    dump_json(run_meta, run_meta_path)

    return run_meta


def merge_markdown_into_pdf(
    pdf_path: Path,
    markdown_path: Path,
) -> Path:
    """Ricostruisce un PDF parziale iniettando una sintesi markdown esterna.

    Usa il file `corpus_run_metadata.json` accanto al PDF per ritrovare
    i summary e i grafici originali.
    """
    pdf_path = Path(pdf_path).resolve()
    markdown_path = Path(markdown_path).resolve()
    output_dir = pdf_path.parent
    meta_path = output_dir / "corpus_run_metadata.json"
    if not meta_path.exists():
        raise click.ClickException(
            f"Metadata di run non trovati in {meta_path}. "
            "Per il merge servono i file generati dal comando `report` originale."
        )
    run_meta = load_json(meta_path)

    summaries = [load_json(Path(p)) for p in run_meta["summary_paths"]]
    plot_paths = {k: Path(v) for k, v in run_meta["plot_paths"].items()}

    synth_markdown = markdown_path.read_text(encoding="utf-8")

    # Il nuovo PDF sovrascrive il precedente
    corpus_metadata = {
        "n_files": run_meta["n_files"],
        "duration_total_s": run_meta["duration_total_s"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    report_pdf.build_corpus_report(
        corpus_title=run_meta["corpus_title"],
        corpus_metadata=corpus_metadata,
        summaries=summaries,
        comparison_plots=plot_paths,
        synth_markdown=synth_markdown,
        output_path=pdf_path,
        synth_available=True,
    )

    # Aggiorna metadata
    run_meta["synth_md_path"] = str(markdown_path)
    run_meta["synth_fallback"] = False
    run_meta["synth_error"] = None
    run_meta["merged_at"] = datetime.now().isoformat(timespec="seconds")
    dump_json(run_meta, meta_path)

    return pdf_path
