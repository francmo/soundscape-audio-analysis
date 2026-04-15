"""Entry point CLI unificato: `soundscape`.

Orchestrazione della pipeline completa: io -> technical -> hum -> spectral ->
ecoacoustic -> semantic (con pre-check) -> multichannel -> comparison GRM ->
plotting -> agente compositivo -> PDF ReportLab.
"""
import sys
import traceback
from datetime import datetime
from pathlib import Path

import click

from . import config
from . import profiles as profiles_mod
from .utils import ensure_dir, check_binary, format_duration, safe_filename


# Estensioni accettate per scansione di cartelle
AUDIO_EXT = (".wav", ".mp3", ".flac", ".aiff", ".aif", ".ogg", ".m4a")


def _iter_audio_paths(path: Path):
    if path.is_file():
        yield path
        return
    if path.is_dir():
        for p in sorted(path.iterdir()):
            if p.is_file() and p.suffix.lower() in AUDIO_EXT:
                yield p


def _analyze_single(
    audio_path: Path,
    output_dir: Path,
    do_semantic: bool,
    do_birdnet: bool,
    ecoacoustic_mode: str,
    do_agent: bool,
    multichannel_mode: str,
    report_format: str,
    compare_mode: str,
    lang: str,
    semantic_backend: str | None = None,
    do_clap: bool = True,
    narrative_mode: str = "full",
) -> dict:
    """Pipeline analitica su un singolo file audio."""
    from . import io_loader, technical, hum, spectral, ecoacoustic, semantic
    from . import multichannel, comparison, plotting, report_pdf, agent_bridge
    from . import serialization

    missing = [b for b in ("ffprobe", "ffmpeg") if not check_binary(b)]
    if missing:
        raise RuntimeError(
            f"Binari mancanti: {', '.join(missing)}. Installa con: brew install ffmpeg"
        )

    click.echo(f"\n[1/8] Metadati e caricamento audio: {audio_path.name}")
    meta = io_loader.load_metadata(audio_path)

    is_multi = meta.get("channels", 1) > 1 and multichannel_mode != "downmix-only"
    if is_multi:
        mc = io_loader.load_audio_multichannel(audio_path)
        y = mc["downmix_mono"]
        sr = mc["sr"]
    else:
        y, sr = io_loader.load_audio_mono(audio_path)
        mc = None

    duration_s = len(y) / sr

    click.echo(f"[2/8] Livelli, dinamica, LUFS")
    tech = technical.technical_summary(audio_path, y)

    click.echo(f"[3/8] Hum check (baseline locale)")
    hum_res = hum.hum_check(audio_path)

    click.echo(f"[4/8] Spettrale (bande Schafer, feature, onset)")
    spec = spectral.spectral_summary(y, sr, duration_s)
    from .spectral import hifi_lofi_score
    spec["hifi_lofi"] = hifi_lofi_score(
        tech["levels"]["dynamic_range_db"],
        spec["timbre"]["spectral_flatness"],
    )

    click.echo(f"[5/8] Indici ecoacustici ({ecoacoustic_mode})")
    extended = ecoacoustic_mode == "extended"
    eco = ecoacoustic.ecoacoustic_summary(y, sr, extended=extended)

    semantic_res = {"enabled": False}
    if do_semantic:
        backend_name = semantic_backend or config.SEMANTIC_BACKEND
        click.echo(f"[6/9] Semantica {backend_name.upper()} (con pre-check LUFS)")
        semantic_res = semantic.semantic_summary(
            audio_path, backend=backend_name, enable=True
        )

    clap_res = {"enabled": False}
    if do_clap:
        from . import semantic_clap
        click.echo(f"[7/9] CLAP auto-tagging italiano (70 prompt)")
        # Waveform caricata a 48 kHz per CLAP
        from .semantic import prepare_waveform
        clap_waveform = prepare_waveform(audio_path, sr=48000)
        clap_res = semantic_clap.clap_summary(clap_waveform, 48000, enable=True)

    mc_res = None
    if is_multi:
        click.echo(f"[8/9] Analisi multicanale ({mc['n_channels']} canali, layout {mc['layout']})")
        mc_res = multichannel.multichannel_summary(mc)

    click.echo(f"[9/9] Grafici e profili")
    base = safe_filename(audio_path.stem)
    graphics_dir = output_dir / "graphics"
    ensure_dir(graphics_dir)

    S_stft, spectrum, freqs = spectral.compute_stft_mean(y, sr)
    plot_paths = plotting.generate_all_plots(
        y, sr, spectrum, freqs, spec["bands_schafer"], hum_res, graphics_dir, base
    )

    summary = {
        "version": "0.3.2",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "metadata": meta,
        "technical": tech,
        "hum": hum_res,
        "spectral": spec,
        "ecoacoustic": eco,
        "semantic": semantic_res,
        "clap": clap_res,
        "multichannel": mc_res,
    }

    # Narrativa segmentata (v0.2.2): prosa italiana 30s
    narrative_res = {"enabled": False}
    if narrative_mode != "none":
        from . import narrative as narrative_mod
        click.echo(f"  Costruzione narrativa segmentata (mode={narrative_mode})")
        narrative_res = narrative_mod.narrative_summary(
            summary, waveform=y, sr=sr, mode=narrative_mode
        )
    summary["narrative"] = narrative_res

    rank_grm: list = []
    if compare_mode not in ("none", None):
        # v0.2: i profili GRM letteratura-based sono disattivati di default.
        # Riattivazione esplicita solo via --compare=grm-experimental o <profile_id>.
        all_profiles = profiles_mod.load_all_profiles()
        if all_profiles:
            if compare_mode in ("all", "grm-experimental"):
                rank_grm = comparison.rank_profiles(summary, all_profiles)
            elif compare_mode in all_profiles:
                rank_grm = [comparison.compare_to_profile(summary, all_profiles[compare_mode])]
    summary["comparison_grm"] = rank_grm

    # Scrittura summary JSON
    json_path = output_dir / f"{base}_summary.json"
    serialization.dump(summary, json_path)
    click.echo(f"Summary JSON: {json_path}")

    # Agente compositivo (v0.2.2: payload ridotto + narrativa markdown)
    agent_text = ""
    if do_agent and report_format in ("pdf", "all"):
        from . import agent_payload
        click.echo(f"Invocazione agente compositivo soundscape-composer-analyst")
        narrative_md = summary.get("narrative", {}).get("markdown", "")
        payload_path = output_dir / f"{base}_agent_payload.json"
        agent_payload.write_agent_payload(summary, narrative_md, payload_path)
        ag = agent_bridge.invoke_composer_analyst(
            payload_path, narrative_md=narrative_md
        )
        agent_text = ag.get("text", "")
        if ag.get("fallback_used"):
            click.echo(f"  (agente non invocato: {ag.get('error') or 'claude non disponibile'})")
        summary["agent"] = ag

    # PDF
    pdf_path = None
    if report_format in ("pdf", "all"):
        pdf_path = output_dir / f"{base}_report.pdf"
        click.echo(f"Generazione PDF: {pdf_path}")
        report_pdf.build_report(
            summary=summary,
            output_path=pdf_path,
            rank_grm=rank_grm,
            agent_text=agent_text,
            plot_paths=plot_paths,
        )

    return {
        "audio": str(audio_path),
        "summary_json": str(json_path),
        "pdf": str(pdf_path) if pdf_path else None,
        "graphics": {k: str(v) for k, v in plot_paths.items()},
    }


@click.group()
@click.version_option(version="0.3.2", prog_name="soundscape")
def cli():
    """Soundscape Audio Analysis. Analisi tecnica, spettrale, ecoacustica,
    semantica e compositiva per file audio soundscape, field recording e
    composizione elettroacustica.
    """


@cli.command("analyze")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--semantic/--no-semantic", default=True, help="Classificazione semantica")
@click.option("--semantic-backend", "semantic_backend",
              type=click.Choice(["panns", "yamnet"]), default=None,
              help=f"Backend classificatore (default: {config.SEMANTIC_BACKEND})")
@click.option("--birdnet", is_flag=True, help="Riconoscimento avifauna BirdNET (opzionale)")
@click.option("--ecoacoustic", "ecoacoustic_mode", type=click.Choice(["basic", "extended"]),
              default="basic", help="Modalità indici ecoacustici")
@click.option("--compare", "compare_mode", default="none",
              help="all | <profile_id> | grm-experimental | none (default: none in v0.2)")
@click.option("--report", "report_format", type=click.Choice(["pdf", "md", "json", "all"]),
              default="pdf", help="Formato output report")
@click.option("--output", "output_dir", type=click.Path(path_type=Path),
              default=None, help="Directory di output (default: accanto al file audio)")
@click.option("--multichannel", "multichannel_mode",
              type=click.Choice(["auto", "split", "downmix-only"]),
              default="auto", help="Gestione file multicanale")
@click.option("--agent/--no-agent", default=True, help="Invoca agente compositivo")
@click.option("--clap/--no-clap", default=True, help="Auto-tagging CLAP con vocabolario italiano")
@click.option("--narrative", "narrative_mode", type=click.Choice(["full", "summary", "none"]),
              default="full", help="Descrizione segmentata italiana (v0.2.2)")
@click.option("--lang", type=click.Choice(["it", "en"]), default="it", help="Lingua output")
def analyze_cmd(path, semantic, semantic_backend, birdnet, ecoacoustic_mode, compare_mode,
                report_format, output_dir, multichannel_mode, agent, clap, narrative_mode, lang):
    """Analizza un file audio o una cartella di file audio.

    Esegue la pipeline completa: tecnica, hum, spettrale, ecoacustica,
    semantica (con pre-check LUFS), multicanale se applicabile, confronto con
    profili GRM, grafici, invocazione agente compositivo, PDF finale.
    """
    files = list(_iter_audio_paths(path))
    if not files:
        click.echo(click.style("Nessun file audio valido trovato.", fg="red"))
        sys.exit(1)

    if output_dir is None:
        output_dir = path.parent if path.is_file() else path
    output_dir = ensure_dir(output_dir)

    # Bootstrap profili se non esistono
    created = profiles_mod.write_initial_profiles(overwrite=False)
    if created:
        click.echo(f"Creati profili GRM iniziali: {', '.join(created)}")

    results = []
    for i, audio in enumerate(files, 1):
        click.echo(click.style(f"\n=== File {i}/{len(files)}: {audio.name} ===",
                                fg="cyan", bold=True))
        try:
            r = _analyze_single(
                audio_path=audio,
                output_dir=output_dir,
                do_semantic=semantic,
                do_birdnet=birdnet,
                ecoacoustic_mode=ecoacoustic_mode,
                do_agent=agent,
                multichannel_mode=multichannel_mode,
                report_format=report_format,
                compare_mode=compare_mode,
                lang=lang,
                semantic_backend=semantic_backend,
                do_clap=clap,
                narrative_mode=narrative_mode,
            )
            results.append(r)
            click.echo(click.style(f"  OK", fg="green"))
        except Exception as e:
            click.echo(click.style(f"  ERRORE: {e}", fg="red"))
            traceback.print_exc()
            results.append({"audio": str(audio), "error": str(e)})

    click.echo(click.style(f"\n=== Fine analisi: {len(results)} file processati ===",
                            fg="cyan", bold=True))
    for r in results:
        if r.get("pdf"):
            click.echo(f"  {r['pdf']}")


@cli.group("profile")
def profile_group():
    """Gestione profili GRM di riferimento."""


@profile_group.command("list")
def profile_list():
    """Elenca i profili GRM disponibili."""
    profs = profiles_mod.load_all_profiles()
    if not profs:
        click.echo("Nessun profilo disponibile. Esegui 'soundscape analyze' una volta per crearli.")
        return
    for pid, p in profs.items():
        click.echo(f"  {pid:30s}  {p.get('title', '')}  ({p.get('source_type', '')})")


@profile_group.command("show")
@click.argument("name")
def profile_show(name):
    """Mostra i dettagli di un profilo GRM."""
    try:
        p = profiles_mod.load_profile(name)
    except FileNotFoundError as e:
        click.echo(click.style(str(e), fg="red"))
        sys.exit(1)
    from . import serialization
    click.echo(serialization.dumps(p))


@profile_group.command("build")
@click.argument("name")
@click.argument("audio", type=click.Path(exists=True), nargs=-1, required=True)
@click.option("--title", required=True)
@click.option("--author", required=True)
@click.option("--year", type=int, required=True)
@click.option("--tradition", default="")
@click.option("--notes", default="")
def profile_build(name, audio, title, author, year, tradition, notes):
    """Rifinisce un profilo GRM da file audio reali."""
    meta = {"title": title, "author": author, "year": year,
            "tradition": tradition, "notes": notes}
    click.echo(f"Costruzione profilo {name} da {len(audio)} file...")
    p = profiles_mod.build_profile_from_audio(list(audio), name, meta)
    click.echo(f"Profilo salvato: {config.PROFILES_DIR / f'{name}.json'}")


@cli.command("init-profiles")
@click.option("--overwrite", is_flag=True, help="Sovrascrivi profili esistenti")
def init_profiles(overwrite):
    """Inizializza i 4 profili GRM letteratura-based."""
    created = profiles_mod.write_initial_profiles(overwrite=overwrite)
    if created:
        click.echo(f"Creati: {', '.join(created)}")
    else:
        click.echo("Tutti i profili esistono già. Usa --overwrite per ricreare.")


@cli.command("report")
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--output", "output_dir", type=click.Path(path_type=Path),
              default=None, help="Directory di output (default: <folder>/soundscape_report/)")
@click.option("--corpus-title", default=None,
              help="Titolo del corpus (default: nome cartella)")
@click.option("--rerun", is_flag=True,
              help="Forza riesecuzione analyze anche con cache valida")
@click.option("--yes", is_flag=True,
              help="Salta la conferma interattiva sopra soglia")
@click.option("--model", default=None,
              help=f"Modello Claude per la sintesi (default: {config.CORPUS_REPORT_MODEL})")
@click.option("--no-synth", is_flag=True,
              help="Salta la sintesi claude, produce PDF parziale + prompt")
@click.option("--golden", "golden_path", type=click.Path(exists=True, path_type=Path),
              default=None, help="Path custom al golden report di riferimento")
def report_command(folder, output_dir, corpus_title, rerun, yes, model,
                   no_synth, golden_path):
    """Report comparativo su un corpus di file audio.

    Lancia analyze su tutti i file della cartella (con cache di freschezza),
    raccoglie i summary, genera grafici comparativi e una sintesi testuale
    prodotta da una sessione Claude Code non interattiva. Infine compone un
    PDF finale in stile ABTEC40.
    """
    from . import report_cmd as rc
    rc.run_corpus_report(
        folder=folder,
        output_dir=output_dir,
        corpus_title=corpus_title,
        rerun=rerun,
        yes=yes,
        model=model or config.CORPUS_REPORT_MODEL,
        no_synth=no_synth,
        golden_path=golden_path,
    )


@cli.command("report-merge")
@click.argument("pdf_path", type=click.Path(exists=True, path_type=Path))
@click.argument("markdown_path", type=click.Path(exists=True, path_type=Path))
def report_merge_command(pdf_path, markdown_path):
    """Integra una sintesi markdown esterna in un PDF di corpus parziale.

    Utile quando la sessione claude è stata lanciata a parte (fuori dal
    comando `report`, ad esempio dopo un `--no-synth`). Richiede la presenza
    di `corpus_run_metadata.json` accanto al PDF.
    """
    from . import report_cmd as rc
    new_pdf = rc.merge_markdown_into_pdf(pdf_path, markdown_path)
    click.echo(click.style(f"PDF aggiornato: {new_pdf}", fg="green", bold=True))


@cli.command("version")
def version_cmd():
    """Versione del toolkit."""
    click.echo("soundscape-audio-analysis 0.3.2")


def main():
    cli(prog_name="soundscape")


if __name__ == "__main__":
    main()
