"""Entry point CLI unificato: `soundscape`.

Orchestrazione della pipeline completa: io -> technical -> hum -> spectral ->
ecoacoustic -> semantic (con pre-check) -> multichannel -> comparison GRM ->
plotting -> agente compositivo -> PDF ReportLab.
"""
import json
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
    do_transcribe_speech: bool = False,
    known_piece: str = "",
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

    click.echo(f"\n[1/10] Metadati e caricamento audio: {audio_path.name}")
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

    click.echo(f"[2/10] Livelli, dinamica, LUFS")
    tech = technical.technical_summary(audio_path, y)

    click.echo(f"[3/10] Hum check (baseline locale)")
    hum_res = hum.hum_check(audio_path)

    click.echo(f"[4/10] Spettrale (bande Schafer, feature, onset)")
    spec = spectral.spectral_summary(y, sr, duration_s)
    from .spectral import hifi_lofi_score
    spec["hifi_lofi"] = hifi_lofi_score(
        tech["levels"]["dynamic_range_db"],
        spec["timbre"]["spectral_flatness"],
    )

    click.echo(f"[5/10] Indici ecoacustici ({ecoacoustic_mode})")
    extended = ecoacoustic_mode == "extended"
    eco = ecoacoustic.ecoacoustic_summary(y, sr, extended=extended)

    semantic_res = {"enabled": False}
    if do_semantic:
        backend_name = semantic_backend or config.SEMANTIC_BACKEND
        click.echo(f"[6/10] Semantica {backend_name.upper()} (con pre-check LUFS)")
        semantic_res = semantic.semantic_summary(
            audio_path, backend=backend_name, enable=True
        )

    # Contestualizza hum sulla base di flatness + top PANNs (v0.5.1):
    # evita falsi positivi su materiale musicale tonale (es. 150 Hz su flauto)
    hum_res = hum.interpret_in_context(
        hum_res, spec, semantic_res.get("classifier") if do_semantic else None
    )

    clap_res = {"enabled": False}
    if do_clap:
        from . import semantic_clap
        click.echo(f"[7/10] CLAP auto-tagging italiano")
        # Waveform caricata a 48 kHz per CLAP
        from .semantic import prepare_waveform
        clap_waveform = prepare_waveform(audio_path, sr=48000)
        # v0.6.6: passa classifier (PANNs) per calcolare krause_cross_check
        # dentro academic_hints.
        clap_res = semantic_clap.clap_summary(
            clap_waveform, 48000, enable=True,
            classifier=semantic_res.get("classifier") if do_semantic else None,
        )
        # v0.5.1: marca tag CLAP speech-related che PANNs non supporta
        # come likely_hallucination. Non rimuove, solo annota.
        # v0.5.2: marca anche i tag italo-specifici con flag geo_specific.
        if clap_res.get("enabled") and clap_res.get("top_global"):
            from .clap_mapping import (
                mark_speech_hallucinations,
                mark_geo_specific_tags,
                mark_plausibility_deterministic,
            )
            classifier_res = semantic_res.get("classifier") if do_semantic else None
            clap_res["top_global"] = mark_speech_hallucinations(
                clap_res["top_global"], classifier_res
            )
            clap_res["top_global"] = mark_geo_specific_tags(clap_res["top_global"])
            # v0.6.6: pre-filtro deterministico per 5 pattern di falso positivo
            # ricorrenti emersi dal confronto blind corpus Nottoli (acqua del
            # rubinetto, preghiera collettiva, spiaggia mediterranea, biofonia
            # su elettronico, treno su bande basse). Marca plausibility low/
            # medium/high in base al supporto PANNs sulle label correlate.
            clap_res["top_global"] = mark_plausibility_deterministic(
                clap_res["top_global"], classifier_res
            )

    # Check suggerimento --speech (v0.5.0): se PANNs rileva Speech dominante
    # nel top_dominant_frames oltre soglia e il flag non e' attivo, raccogliamo
    # un hint da stampare a fine analyze_cmd in giallo su stderr.
    from . import speech as _speech
    speech_suggestion_pct = _speech.check_speech_suggestion(
        semantic_res, flag_active=do_transcribe_speech
    )

    speech_res = {"enabled": False, "reason": "disabled"}
    if do_transcribe_speech:
        from . import speech
        click.echo(f"[8/10] Trascrizione dialoghi (Whisper large-v3 + Silero VAD)")
        speech_res = speech.speech_summary(
            y, sr, enable=True, duration_total_s=duration_s
        )
        if speech_res.get("enabled") and not speech_res.get("skipped_reason"):
            speech_res = speech.translate_transcript(speech_res)

    mc_res = None
    if is_multi:
        click.echo(f"[9/10] Analisi multicanale ({mc['n_channels']} canali, layout {mc['layout']})")
        mc_res = multichannel.multichannel_summary(mc)

    click.echo(f"[10/10] Grafici e profili")
    base = safe_filename(audio_path.stem)
    graphics_dir = output_dir / "graphics"
    ensure_dir(graphics_dir)

    S_stft, spectrum, freqs = spectral.compute_stft_mean(y, sr)
    plot_paths = plotting.generate_all_plots(
        y, sr, spectrum, freqs, spec["bands_schafer"], hum_res, graphics_dir, base
    )

    if known_piece:
        meta = dict(meta)
        meta["user_known_piece"] = known_piece.strip()

    summary = {
        "version": "0.6.1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "metadata": meta,
        "technical": tech,
        "hum": hum_res,
        "spectral": spec,
        "ecoacoustic": eco,
        "semantic": semantic_res,
        "clap": clap_res,
        "speech": speech_res,
        "multichannel": mc_res,
    }

    # Segmentazione strutturale (v0.6.0): identifica sezioni significative
    # del brano via changepoint detection deterministico. Output usato dal
    # PDF (timeline grafica + tabella) e dal payload agente.
    from . import structure as structure_mod
    click.echo(f"  Segmentazione strutturale (changepoint detection)")
    structure_res = structure_mod.compute_structure(
        waveform=y, sr=sr, summary=summary,
        window_seconds=config.STRUCTURE_WINDOW_S,
    )
    summary["structure"] = structure_res
    # Timeline grafica strutturale per il PDF
    if structure_res.get("enabled") and structure_res.get("sections"):
        timeline_path = graphics_dir / f"{base}_structure_timeline.png"
        plotting.plot_structure_timeline(
            structure_res["sections"],
            total_duration_s=duration_s,
            out_path=timeline_path,
        )
        plot_paths["structure_timeline"] = timeline_path

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

    # Export .txt companion dei trascritti (v0.5.0): accanto al PDF
    transcript_txt = None
    transcript_it_txt = None
    if speech_res.get("enabled") and speech_res.get("transcript"):
        transcript_txt = output_dir / f"{base}_transcript.txt"
        transcript_txt.write_text(speech_res["transcript"], encoding="utf-8")
        click.echo(f"Trascritto: {transcript_txt}")
        if (
            speech_res.get("transcript_it")
            and speech_res.get("language_detected", "") != "it"
            and speech_res.get("transcript_it") != speech_res["transcript"]
        ):
            transcript_it_txt = output_dir / f"{base}_transcript_it.txt"
            transcript_it_txt.write_text(
                speech_res["transcript_it"], encoding="utf-8"
            )
            click.echo(f"Traduzione italiana: {transcript_it_txt}")

    return {
        "audio": str(audio_path),
        "summary_json": str(json_path),
        "pdf": str(pdf_path) if pdf_path else None,
        "transcript_txt": str(transcript_txt) if transcript_txt else None,
        "transcript_it_txt": str(transcript_it_txt) if transcript_it_txt else None,
        "speech_suggestion_pct": speech_suggestion_pct,
        "graphics": {k: str(v) for k, v in plot_paths.items()},
    }


@click.group()
@click.version_option(version="0.6.1", prog_name="soundscape")
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
@click.option("--speech", is_flag=True, default=False,
              help="Trascrizione dialoghi via faster-whisper + Silero VAD, con traduzione italiana via claude -p (opt-in, v0.5.0)")
@click.option("--known-piece", "known_piece", type=str, default="",
              help="Attribuzione nota dell'opera nel formato 'Autore, Titolo, anno' "
                   "(es. 'Luc Ferrari, Presque Rien N°1, 1967-70'). Se fornito, l'agente "
                   "compositivo la usa come hint forte e salta la fase di indovinare. "
                   "v0.5.4: utile quando si analizza un brano di repertorio noto e si "
                   "vuole evitare attribuzioni errate del modello.")
@click.option("--lang", type=click.Choice(["it", "en"]), default="it", help="Lingua output")
def analyze_cmd(path, semantic, semantic_backend, birdnet, ecoacoustic_mode, compare_mode,
                report_format, output_dir, multichannel_mode, agent, clap, narrative_mode,
                speech, known_piece, lang):
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
                do_transcribe_speech=speech,
                known_piece=known_piece,
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

    # Suggerimento --speech (v0.5.0): stampato a fine pipeline in giallo su
    # stderr per visibilita' sopra il prompt, solo quando l'utente NON ha
    # passato --speech e PANNs ha rilevato Speech dominante nei frame.
    for r in results:
        pct = r.get("speech_suggestion_pct")
        if pct is not None:
            audio_name = Path(r.get("audio", "")).name
            click.echo(click.style(
                f"[soundscape] {audio_name}: PANNs rileva Speech dominante nel "
                f"{pct:.1f}% dei frame. Per trascrizione: rilancia con --speech",
                fg="yellow"
            ), err=True)


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


@cli.command("agent")
@click.argument("summary_path", type=click.Path(exists=True, path_type=Path))
@click.option("--pdf", is_flag=True, default=False,
              help="Rigenera il PDF completo usando il summary esistente (default: "
                   "stampa solo il markdown dell'agente su stdout e salva <base>_agent.md)")
@click.option("--output", "output_dir", type=click.Path(path_type=Path),
              default=None,
              help="Directory di output (default: accanto al summary.json)")
@click.option("--known-piece", "known_piece", type=str, default="",
              help="Attribuzione utente esplicita (come in analyze). Sovrascrive "
                   "eventuale valore gia' presente in summary.metadata.user_known_piece.")
def agent_cmd(summary_path: Path, pdf: bool, output_dir: Path | None,
              known_piece: str):
    """Invoca solo l'agente compositivo su un summary.json esistente (v0.6.1).

    Salta PANNs/CLAP/narrative/structure (gia' calcolati) e rigenera solo la
    "Lettura compositiva". Utile per iterare sul prompt dell'agente o per
    riprocessare l'analisi dopo aggiornamenti delle istruzioni, senza rifare
    l'intera pipeline (5-10 minuti -> 30-90 secondi).

    Modalita':
    - default: stampa il markdown dell'agente su stdout e salva `<base>_agent.md`
      accanto al summary.
    - `--pdf`: rigenera anche il PDF completo (richiede che `<base>_graphics/`
      con gli spettrogrammi esista gia' accanto al summary).
    """
    from . import agent_bridge, agent_payload, serialization, report_pdf

    if output_dir is None:
        output_dir = summary_path.parent
    output_dir = ensure_dir(output_dir)

    summary = serialization.load(summary_path)
    if not isinstance(summary, dict):
        click.echo(click.style(
            f"summary.json malformato: {summary_path}", fg="red"
        ), err=True)
        sys.exit(1)

    if known_piece:
        meta = summary.get("metadata") or {}
        meta = dict(meta)
        meta["user_known_piece"] = known_piece.strip()
        summary["metadata"] = meta

    base = summary_path.stem
    if base.endswith("_summary"):
        base = base[: -len("_summary")]

    narrative_md = (summary.get("narrative") or {}).get("markdown", "")
    payload_path = output_dir / f"{base}_agent_payload.json"
    agent_payload.write_agent_payload(summary, narrative_md, payload_path)
    click.echo(f"Payload agente: {payload_path}")

    click.echo(f"Invocazione agente compositivo soundscape-composer-analyst")
    ag = agent_bridge.invoke_composer_analyst(
        payload_path, narrative_md=narrative_md
    )
    agent_text = ag.get("text", "") or ""
    if ag.get("fallback_used"):
        click.echo(click.style(
            f"  (agente non invocato: {ag.get('error') or 'claude non disponibile'})",
            fg="yellow"
        ))
    if not agent_text:
        click.echo(click.style(
            "Agente non ha prodotto output utilizzabile", fg="red"
        ), err=True)
        sys.exit(1)

    md_path = output_dir / f"{base}_agent.md"
    md_path.write_text(agent_text, encoding="utf-8")
    click.echo(click.style(f"Markdown agente: {md_path}", fg="green"))

    summary["agent"] = ag
    if pdf:
        pdf_path = output_dir / f"{base}_report.pdf"
        # Ricostruisce plot_paths scansionando graphics_dir se esiste
        graphics_dir = output_dir / "graphics"
        plot_paths: dict = {}
        if graphics_dir.exists():
            for suffix, key in [
                ("waveform.png", "waveform"),
                ("spettrogramma.png", "spectrogram"),
                ("spettro_medio.png", "spectrum_mean"),
                ("bande.png", "bands_bar"),
                ("hum.png", "hum_zoom"),
                ("structure_timeline.png", "structure_timeline"),
            ]:
                candidate = graphics_dir / f"{base}_{suffix}"
                if candidate.exists():
                    plot_paths[key] = candidate
        click.echo(f"Generazione PDF: {pdf_path}")
        report_pdf.build_report(
            summary=summary,
            output_path=pdf_path,
            rank_grm=[],
            agent_text=agent_text,
            plot_paths=plot_paths,
        )
        click.echo(click.style(f"PDF finale: {pdf_path}", fg="green", bold=True))
    else:
        click.echo("")
        click.echo(agent_text)


@cli.command("benchmark")
@click.argument("audio", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--against",
    "gold_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path al file gold markdown (references/golden_analyses/<id>.md).",
)
@click.option(
    "--agent-source",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path al PDF report o al file agent_reading.md. Se omesso, cercato accanto all'audio.",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Path del markdown di report. Default: <audio_stem>_benchmark.md accanto all'audio.",
)
@click.option(
    "--json-out",
    "json_out",
    type=click.Path(path_type=Path),
    default=None,
    help="Path opzionale del JSON con il BenchmarkResult serializzato.",
)
def benchmark_cmd(audio: Path, gold_path: Path, agent_source: Path | None, output: Path | None, json_out: Path | None):
    """Benchmarka la lettura dell'agente contro un'analisi accademica di riferimento.

    Calcola precision/recall terminologici, Jaccard, precision/recall parentele
    stilistiche e score aggregato 0-100. Se l'output dell'agente non esiste,
    istruisce a lanciare `soundscape analyze` prima.
    """
    from . import benchmark as bench

    try:
        report_md, result = bench.run_benchmark(audio, gold_path, agent_source)
    except FileNotFoundError as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        raise SystemExit(2)

    out_md = output or audio.with_name(audio.stem + "_benchmark.md")
    out_md.write_text(report_md, encoding="utf-8")
    click.echo(click.style(f"Report benchmark: {out_md}", fg="green", bold=True))

    if json_out:
        json_out.write_text(
            json.dumps(bench.result_to_dict(result), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        click.echo(f"JSON: {json_out}")

    click.echo("")
    click.echo(f"Score aggregato: {result.score_aggregate:.1f}/100")
    click.echo(f"  precision term {result.precision_term:.3f}  recall term {result.recall_term:.3f}  jaccard {result.jaccard_term:.3f}")
    click.echo(f"  precision par  {result.precision_parent:.3f}  recall par  {result.recall_parent:.3f}  jaccard {result.jaccard_parent:.3f}")
    for w in result.warnings:
        click.echo(click.style(f"  AVVISO: {w}", fg="yellow"), err=True)


@cli.command("version")
def version_cmd():
    """Versione del toolkit."""
    click.echo("soundscape-audio-analysis 0.7.1")


def main():
    cli(prog_name="soundscape")


if __name__ == "__main__":
    main()
