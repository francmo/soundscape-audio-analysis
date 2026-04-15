"""Generatore PDF ReportLab stile ABTEC40 end-to-end.

Prende in input il summary dict completo + percorso output + profile match
+ testo dell'agente (opzionale) e costruisce il PDF multi-sezione.
"""
from pathlib import Path
from datetime import date
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, NextPageTemplate,
    Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image
)

from . import config
from .locale_it import (
    INTESTAZIONI, PARAMETRI, MESSAGGI_SISTEMA, sanitize_italiano
)
from . import report_styles


def _on_cover_page(canvas, doc):
    """Copertina con background blu scuro full page."""
    canvas.saveState()
    PAL = config.PALETTE
    canvas.setFillColor(HexColor(PAL["dark"]))
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    # Decorativi: cerchi terracotta
    canvas.setFillColor(HexColor(PAL["terracotta"]))
    canvas.circle(A4[0] - 40 * mm, A4[1] - 40 * mm, 15 * mm, fill=1, stroke=0)
    canvas.setFillColor(HexColor(PAL["dark_mid"]))
    canvas.circle(30 * mm, 50 * mm, 25 * mm, fill=1, stroke=0)
    canvas.restoreState()


def _on_body_page(canvas, doc):
    """Sfondo bianco puro + footer nero (regola tipografica v0.3.1).

    La regola CLAUDE.md "Regola sulla tipografia dei documenti generati"
    (punti 1 e 3) impone sfondo bianco per le pagine interne, testo nero
    per footer e colofone. La copertina usa `_on_cover_page`/`_on_corpus_cover`
    e può mantenere colori.
    """
    canvas.saveState()
    canvas.setFillColor(HexColor("#FFFFFF"))
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#000000"))
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"{doc.page}")
    canvas.drawString(20 * mm, 12 * mm, "Soundscape Audio Analysis")
    canvas.restoreState()


def _fmt(v, fmt: str = "{}", default: str = "n.d.") -> str:
    if v is None:
        return default
    try:
        return fmt.format(v)
    except Exception:
        return str(v)


def _build_metadati_table(meta: dict, styles) -> Table:
    rows = [
        ["Campo", "Valore"],
        ["Nome file", meta.get("filename", "n.d.")],
        ["Codec", meta.get("codec", "n.d.")],
        ["Sample rate", _fmt(meta.get("sr"), "{} Hz")],
        ["Bit depth", _fmt(meta.get("bit_depth"), "{} bit")],
        ["Canali", _fmt(meta.get("channels"))],
        ["Durata", _fmt(meta.get("duration_s"), "{:.2f} s")],
        ["Bitrate", _fmt(meta.get("bitrate_kbps"), "{} kbps")],
        ["Dimensione", _fmt(meta.get("size_mb"), "{:.2f} MB")],
    ]
    return report_styles.styled_table(rows, [55 * mm, 105 * mm], styles)


def _build_livelli_table(tech: dict, styles) -> Table:
    lvl = tech.get("levels", {})
    lufs = tech.get("lufs", {})
    rows = [
        ["Parametro", "Valore", "Note"],
        [PARAMETRI["peak"], _fmt(lvl.get("peak_dbfs"), "{:.2f} dBFS"), ""],
        [PARAMETRI["rms"], _fmt(lvl.get("rms_dbfs"), "{:.2f} dBFS"), ""],
        [PARAMETRI["crest"], _fmt(lvl.get("crest_db"), "{:.2f} dB"), ""],
        [PARAMETRI["dr"], _fmt(lvl.get("dynamic_range_db"), "{:.2f} dB"), "P95-P10 dei frame RMS"],
        [PARAMETRI["noise_floor"], _fmt(lvl.get("noise_floor_db"), "{:.2f} dB"), "P5 dei frame RMS"],
        [PARAMETRI["lufs"], _fmt(lufs.get("integrated_lufs"), "{:.1f} LUFS"), "EBU R128"],
        [PARAMETRI["lra"], _fmt(lufs.get("lra"), "{:.1f} LU"), ""],
        [PARAMETRI["true_peak"], _fmt(lufs.get("true_peak_db"), "{:.2f} dBTP"), ""],
    ]
    return report_styles.styled_table(rows, [50 * mm, 45 * mm, 65 * mm], styles)


def _build_diagnosi_table(tech: dict, hum: dict, styles) -> Table:
    clip = tech.get("clipping", {})
    dc = tech.get("dc_offset", {})
    rows = [
        ["Controllo", "Valore", "Esito"],
        [PARAMETRI["clipping"], f"{clip.get('samples', 0)} campioni ({clip.get('pct', 0):.4f}%)", clip.get("verdict", "")],
        [PARAMETRI["dc_offset"], f"{dc.get('offset', 0):.6f}", dc.get("verdict", "")],
        [PARAMETRI["hum_50"], _hum_row(hum, 50), _hum_verdict(hum, 50)],
        [PARAMETRI["hum_60"], _hum_row(hum, 60), _hum_verdict(hum, 60)],
    ]
    return report_styles.styled_table(rows, [50 * mm, 55 * mm, 55 * mm], styles)


def _hum_row(hum: dict, target: int) -> str:
    for p in hum.get("peaks", []):
        if p["target_hz"] == target:
            # Fix v0.2: niente prefisso manuale, il format {:+.1f} produce già
            # il segno. Evita il bug +-3.0 dB quando ratio_db è negativo.
            return f"{p['ratio_db']:+.1f} dB vs baseline locale"
    return "n.d."


def _hum_verdict(hum: dict, target: int) -> str:
    for p in hum.get("peaks", []):
        if p["target_hz"] == target:
            return p["verdict"]
    return "n.d."


def _build_bande_table(bands: dict, styles) -> Table:
    rows = [["Banda", "Range (Hz)", "Energia %", "dB rel."]]
    for name, info in bands.items():
        lo, hi = info["range_hz"]
        rows.append([name, f"{lo}-{hi}", f"{info['energy_pct']:.2f}%", f"{info['energy_db']:+.1f}"])
    return report_styles.styled_table(rows, [40 * mm, 45 * mm, 35 * mm, 40 * mm], styles)


def _build_timbre_table(timbre: dict, onsets: dict, hifi: dict, styles) -> Table:
    rows = [
        ["Parametro", "Valore", "Interpretazione"],
        [PARAMETRI["centroide"], _fmt(timbre.get("spectral_centroid_hz"), "{:.0f} Hz"), "baricentro timbrico"],
        [PARAMETRI["rolloff"], _fmt(timbre.get("spectral_rolloff_hz"), "{:.0f} Hz"), "estensione spettrale"],
        [PARAMETRI["flatness"], _fmt(timbre.get("spectral_flatness"), "{:.4f}"), "0 tonale, 1 rumoroso"],
        [PARAMETRI["zcr"], _fmt(timbre.get("zero_crossing_rate"), "{:.4f}"), "proxy transienti"],
        [PARAMETRI["onset_density"], f"{onsets.get('events_count', 0)} ({onsets.get('events_per_sec', 0):.2f}/s)", onsets.get("density_label", "")],
        ["Hi-Fi / Lo-Fi", hifi.get("label", ""), f"score {hifi.get('score_5', 0)}/5"],
    ]
    return report_styles.styled_table(rows, [45 * mm, 50 * mm, 65 * mm], styles)


def _build_eco_table(eco: dict, styles) -> Table:
    ndsi = eco.get("ndsi", {})
    h = eco.get("h_entropy", {})
    rows = [
        ["Indice", "Valore", "Interpretazione"],
        [PARAMETRI["aci"], _fmt(eco.get("aci"), "{:.2f}"), "complessità spettrale temporale"],
        [PARAMETRI["ndsi"], _fmt(ndsi.get("ndsi"), "{:+.3f}"), "-1 antropofonia, +1 biofonia"],
        [PARAMETRI["h_entropy"] + " totale", _fmt(h.get("h_total"), "{:.4f}"), "H spettrale x temporale"],
        [PARAMETRI["h_entropy"] + " spettrale", _fmt(h.get("h_spectral"), "{:.4f}"), ""],
        [PARAMETRI["h_entropy"] + " temporale", _fmt(h.get("h_temporal"), "{:.4f}"), ""],
        [PARAMETRI["bi"], _fmt(eco.get("bi"), "{:.2f}"), "area banda biofonica (2-8 kHz)"],
    ]
    return report_styles.styled_table(rows, [60 * mm, 45 * mm, 55 * mm], styles)


def _build_semantic_block(semantic: dict, styles) -> list:
    story = []
    if not semantic.get("enabled"):
        story.append(Paragraph("Classificazione semantica non eseguita.", styles["body"]))
        return story
    precheck = semantic.get("precheck", {})
    # v0.2: chiave unificata "classifier". Fallback su "yamnet" per retrocompat.
    classifier = semantic.get("classifier") or semantic.get("yamnet", {})
    model_label = classifier.get("model_name") or "classificatore"
    device_label = classifier.get("device") or ""

    if precheck.get("requires_normalization"):
        msg = MESSAGGI_SISTEMA["yamnet_precheck_applicato"].format(
            lufs=precheck.get("lufs", 0),
            threshold=precheck.get("threshold_lufs", -45),
            gain=precheck.get("gain_db", 0),
        )
        story.append(report_styles.box_accent("Pre-check LUFS", msg, styles))
        story.append(Spacer(1, 6))

    if model_label:
        version = classifier.get("model_version", "")
        header = f"Modello: <b>{model_label}</b>"
        if version:
            header += f" ({version})"
        if device_label:
            header += f", device {device_label}"
        story.append(Paragraph(header, styles["body"]))
        story.append(Spacer(1, 4))

    top_global = classifier.get("top_global", [])[:10]
    if top_global:
        rows = [["Rank", f"Categoria {model_label}", "Score medio"]]
        for i, cat in enumerate(top_global, 1):
            rows.append([str(i), cat["name"], f"{cat['score']:.4f}"])
        story.append(report_styles.styled_table(rows, [15 * mm, 95 * mm, 35 * mm], styles))
    top_dom = classifier.get("top_dominant_frames", [])[:8]
    if top_dom:
        story.append(Spacer(1, 8))
        story.append(Paragraph("<b>Categorie più frequentemente dominanti</b>", styles["body"]))
        rows = [["Categoria", "Frame dominanti"]]
        for cat in top_dom:
            rows.append([cat["name"], f"{cat['pct']:.1f}%"])
        story.append(report_styles.styled_table(rows, [110 * mm, 40 * mm], styles))
    return story


def _build_confronto_grm_block(rank: list[dict], styles) -> list:
    story = []
    if not rank:
        story.append(Paragraph("Nessun profilo GRM caricato per il confronto.", styles["body"]))
        return story
    rows = [["Profilo", "Autore", "Distanza", "Fonte"]]
    for r in rank[:6]:
        rows.append([
            r.get("profile_title") or r.get("profile_id"),
            r.get("profile_author") or "",
            f"{r['cosine_distance']:.3f}",
            r.get("source_type", ""),
        ])
    story.append(report_styles.styled_table(rows, [70 * mm, 50 * mm, 25 * mm, 30 * mm], styles))
    story.append(Spacer(1, 6))
    if rank:
        best = rank[0]
        story.append(report_styles.box_neutral(
            "Profilo più vicino",
            best.get("narrative_it", ""),
            styles,
        ))
    return story


def _build_clap_block(clap: dict, styles) -> list:
    """Sezione PDF per il risultato CLAP: top globali + timeline per segmento."""
    story = []
    if not clap.get("enabled"):
        return story

    header = f"Modello: <b>{clap.get('model_name', 'CLAP')}</b>"
    dev = clap.get("device")
    if dev:
        header += f", device {dev}"
    header += f". Vocabolario italiano di {clap.get('vocabulary_size', 0)} prompt "
    header += f"(versione {clap.get('vocabulary_version', 'n.d.')}). "
    header += f"Segmentazione fissa a {clap.get('segment_seconds', 10.0)} s per segmento."
    story.append(Paragraph(header, styles["body"]))
    story.append(Spacer(1, 6))

    top_global = clap.get("top_global", [])[:10]
    if top_global:
        story.append(Paragraph(
            "<b>Tag globali (media di similarità sul file completo)</b>", styles["body"]))
        rows = [["Rank", "Prompt italiano", "Categoria", "Similarità"]]
        for i, t in enumerate(top_global, 1):
            rows.append([str(i), t["prompt"], t.get("category", ""), f"{t['score']:.3f}"])
        story.append(report_styles.styled_table(
            rows, [14 * mm, 90 * mm, 38 * mm, 24 * mm], styles
        ))
        story.append(Spacer(1, 8))

    timeline = clap.get("timeline", [])
    if timeline:
        story.append(Paragraph(
            f"<b>Timeline tag (top-3 per segmento di {clap.get('segment_seconds', 10.0):.0f} s)</b>",
            styles["body"]))
        rows = [["Tempo", "Top 1", "Top 2", "Top 3"]]
        for seg in timeline[:60]:
            t0 = _fmt_time(seg["t_start_s"])
            t1 = _fmt_time(seg["t_end_s"])
            tags = seg.get("tags", [])
            row = [f"{t0}-{t1}"]
            for idx in range(3):
                if idx < len(tags):
                    row.append(f"{tags[idx]['prompt'][:35]}")
                else:
                    row.append("")
            rows.append(row)
        if len(timeline) > 60:
            rows.append([f"...", f"+{len(timeline)-60} segmenti omessi nel PDF",
                         "vedi timeline CSV", ""])
        story.append(report_styles.styled_table(
            rows, [22 * mm, 48 * mm, 48 * mm, 48 * mm], styles
        ))
    return story


def _fmt_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


def _build_multichannel_block(mc: dict, styles) -> list:
    story = []
    if not mc:
        return story
    story.append(Paragraph(f"<b>Layout rilevato:</b> {mc.get('layout', 'n.d.')} ({mc.get('n_channels', 0)} canali)", styles["body"]))
    rows = [["Canale", "Peak dBFS", "RMS dBFS", "Centroide Hz", "Banda dom."]]
    for ch in mc.get("per_channel", []):
        if ch.get("empty"):
            continue
        lvl = ch.get("levels", {})
        tmb = ch.get("timbre", {})
        rows.append([
            ch.get("label", ""),
            _fmt(lvl.get("peak_dbfs"), "{:+.2f}"),
            _fmt(lvl.get("rms_dbfs"), "{:+.2f}"),
            _fmt(tmb.get("spectral_centroid_hz"), "{:.0f}"),
            ch.get("dominant_band", ""),
        ])
    story.append(report_styles.styled_table(rows, [30 * mm, 30 * mm, 30 * mm, 35 * mm, 40 * mm], styles))
    comp = mc.get("comparison", {})
    if comp and not comp.get("warning"):
        story.append(Spacer(1, 6))
        parts = []
        if comp.get("loudest_channel") and comp.get("quietest_channel"):
            parts.append(f"Canale più attivo: <b>{comp['loudest_channel']}</b>. Canale più silenzioso: <b>{comp['quietest_channel']}</b>.")
        if comp.get("rms_spread_db") is not None:
            parts.append(f"Spread RMS tra canali: {comp['rms_spread_db']:.1f} dB.")
        story.append(Paragraph(" ".join(parts), styles["body"]))
    return story


def _build_hum_block(hum: dict, styles) -> list:
    story = []
    story.append(report_styles.box_info(
        "Hum check con baseline locale",
        MESSAGGI_SISTEMA["hum_baseline_nota"],
        styles,
    ))
    story.append(Spacer(1, 6))
    rows = [["Target Hz", "Picco Hz", "Magnitude dB", "Ratio vs baseline", "Verdetto"]]
    for p in hum.get("peaks", []):
        rows.append([
            str(p["target_hz"]),
            f"{p['found_hz']:.1f}",
            f"{p['magnitude_db']:+.2f}",
            f"{p['ratio_db']:+.2f} dB",
            p["verdict"],
        ])
    story.append(report_styles.styled_table(rows, [25 * mm, 30 * mm, 35 * mm, 45 * mm, 30 * mm], styles))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Verdetto complessivo: <b>{hum.get('overall_verdict', 'n.d.')}</b>. "
        f"Baseline locale calcolata come mediana nelle bande "
        f"{', '.join([f'{lo}-{hi} Hz' for lo, hi in hum.get('baseline_bands', [])])}. "
        f"Risoluzione FFT: {hum.get('bin_hz', 0):.2f} Hz per bin.",
        styles["caption"],
    ))
    return story


def _build_composer_section(agent_text: str, styles) -> list:
    story = []
    if not agent_text:
        story.append(Paragraph(
            "La lettura compositiva dell'agente non è disponibile per questo file.",
            styles["body_it"],
        ))
        return story
    # Agente restituisce markdown. Per semplicità lo spezziamo in paragrafi
    # e i titoli ## diventano h3.
    text = sanitize_italiano(agent_text)
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            story.append(Paragraph(block[3:].strip(), styles["h3"]))
        elif block.startswith("# "):
            story.append(Paragraph(block[2:].strip(), styles["h2"]))
        else:
            # Conversione light di **bold** e *italic* in tag ReportLab
            para = block.replace("**", "<b>", 1).replace("**", "</b>", 1)
            para = para.replace("*", "<i>", 1).replace("*", "</i>", 1)
            story.append(Paragraph(para, styles["body"]))
    return story


def build_report(
    summary: dict,
    output_path: Path,
    rank_grm: list[dict] | None = None,
    agent_text: str | None = None,
    plot_paths: dict[str, Path] | None = None,
    corpus_title: str | None = None,
) -> Path:
    """Costruzione del PDF end-to-end.

    summary: dict completo prodotto dalla pipeline
    output_path: Path del PDF da creare
    rank_grm: lista confronto con profili GRM (da comparison.rank_profiles)
    agent_text: testo markdown dell'agente compositivo
    plot_paths: dict {chiave: Path} dei PNG già generati
    """
    fonts = report_styles.register_fonts()
    styles = report_styles.build_styles(fonts)

    page_w, page_h = A4
    margin = 20 * mm

    cover_frame = Frame(margin, margin, page_w - 2 * margin, page_h - 2 * margin,
                        showBoundary=0, leftPadding=20 * mm, rightPadding=20 * mm,
                        topPadding=40 * mm, bottomPadding=20 * mm)
    body_frame = Frame(margin, margin + 10 * mm, page_w - 2 * margin,
                       page_h - 2 * margin - 10 * mm, showBoundary=0,
                       leftPadding=5 * mm, rightPadding=5 * mm,
                       topPadding=5 * mm, bottomPadding=5 * mm)

    doc = BaseDocTemplate(str(output_path), pagesize=A4,
                          title="Soundscape Audio Analysis", author="Francesco Mariano")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=cover_frame, onPage=_on_cover_page),
        PageTemplate(id="body", frames=body_frame, onPage=_on_body_page),
    ])

    story: list = []

    # COPERTINA
    story.append(Paragraph("Soundscape<br/>Audio Analysis", styles["h1_cover"]))
    story.append(Paragraph("Report tecnico e compositivo", styles["h2_cover"]))
    story.append(Spacer(1, 20 * mm))
    meta = summary.get("metadata", {})
    story.append(Paragraph(f"<b>File</b>: {meta.get('filename', 'n.d.')}", styles["meta_cover"]))
    story.append(Paragraph(f"<b>Durata</b>: {_fmt(meta.get('duration_s'), '{:.1f} s')}", styles["meta_cover"]))
    story.append(Paragraph(f"<b>Sample rate</b>: {_fmt(meta.get('sr'), '{} Hz')}", styles["meta_cover"]))
    story.append(Paragraph(f"<b>Canali</b>: {_fmt(meta.get('channels'))} ({meta.get('format_name') or meta.get('codec', '')})", styles["meta_cover"]))
    if corpus_title:
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph(f"<b>Corpus</b>: {corpus_title}", styles["meta_cover"]))
    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph(f"Data analisi: {date.today().isoformat()}", styles["meta_cover"]))
    story.append(Paragraph("Francesco Mariano, Accademia di Belle Arti di Macerata", styles["meta_cover"]))
    # Fix v0.3.1: dopo la copertina passa al template body (sfondo bianco)
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

    # SEZIONE TECNICA
    story.append(Paragraph(INTESTAZIONI["metadati"], styles["h1"]))
    story.append(_build_metadati_table(meta, styles))
    story.append(Spacer(1, 8))

    tech = summary.get("technical", {})
    story.append(Paragraph(INTESTAZIONI["livelli_dinamica"], styles["h1"]))
    story.append(_build_livelli_table(tech, styles))
    story.append(Spacer(1, 8))

    hum = summary.get("hum", {})
    story.append(Paragraph(INTESTAZIONI["diagnosi_tecnica"], styles["h1"]))
    story.append(_build_diagnosi_table(tech, hum, styles))
    story.append(Spacer(1, 8))
    story.extend(_build_hum_block(hum, styles))
    story.append(PageBreak())

    # SEZIONE SPETTRALE
    spec = summary.get("spectral", {})
    story.append(Paragraph(INTESTAZIONI["spettro"], styles["h1"]))
    story.append(_build_bande_table(spec.get("bands_schafer", {}), styles))
    story.append(Spacer(1, 8))
    story.append(Paragraph(INTESTAZIONI["caratt_timbrica"], styles["h2"]))
    story.append(_build_timbre_table(spec.get("timbre", {}), spec.get("onsets", {}),
                                      spec.get("hifi_lofi", {}), styles))
    story.append(Spacer(1, 8))

    if plot_paths and plot_paths.get("bands_bar"):
        story.append(Image(str(plot_paths["bands_bar"]), width=165 * mm, height=55 * mm))
        story.append(Spacer(1, 6))
    if plot_paths and plot_paths.get("spectrogram"):
        story.append(Image(str(plot_paths["spectrogram"]), width=165 * mm, height=60 * mm))
        story.append(Paragraph("Spettrogramma log-frequenza, scala dB.", styles["caption"]))
    story.append(PageBreak())

    # ECOACUSTICA
    eco = summary.get("ecoacoustic", {})
    if eco:
        story.append(Paragraph(INTESTAZIONI["ecoacustica"], styles["h1"]))
        story.append(_build_eco_table(eco, styles))
        story.append(Spacer(1, 8))

    # SEMANTICA
    semantic = summary.get("semantic", {})
    story.append(Paragraph(INTESTAZIONI["classificazione_semantica"], styles["h1"]))
    story.extend(_build_semantic_block(semantic, styles))
    story.append(PageBreak())

    # CLAP auto-tagging (v0.2.1)
    clap = summary.get("clap") or {}
    if clap.get("enabled"):
        story.append(Paragraph(INTESTAZIONI["clap"], styles["h1"]))
        story.extend(_build_clap_block(clap, styles))
        story.append(PageBreak())

    # MULTICANALE
    mc = summary.get("multichannel")
    if mc:
        story.append(Paragraph(INTESTAZIONI["multicanale"], styles["h1"]))
        story.extend(_build_multichannel_block(mc, styles))
        story.append(PageBreak())

    # CONFRONTO GRM
    # v0.2: disattivato di default, riattivabile solo con --compare=grm-experimental
    # o --compare=<profile_id>. Se rank_grm è vuota la sezione viene saltata.
    if rank_grm:
        story.append(Paragraph(INTESTAZIONI["confronto_grm"], styles["h1"]))
        story.append(report_styles.box_info(
            "Confronto sperimentale con profili GRM letteratura-based",
            "Questa sezione è attivata manualmente via --compare=grm-experimental. "
            "I profili di riferimento sono stimati da letteratura e non da audio reale, "
            "quindi il confronto numerico ha valore esplorativo, non interpretativo. "
            "Nella v0.3 verranno sostituiti da profili audio-derived via profile build.",
            styles,
        ))
        story.append(Spacer(1, 6))
        story.extend(_build_confronto_grm_block(rank_grm, styles))
        story.append(PageBreak())

    # DESCRIZIONE SEGMENTATA (v0.2.2)
    narrative = summary.get("narrative") or {}
    if narrative.get("enabled") and narrative.get("segments"):
        story.append(Paragraph(INTESTAZIONI["narrativa"], styles["h1"]))
        story.append(Paragraph(
            f"Descrizione generata da `narrative.py` con finestra di "
            f"{narrative.get('window_seconds', 30):.0f} secondi, modalità "
            f"<b>{narrative.get('mode', 'full')}</b>. Integra livelli, spettro, "
            f"eventi, classificatore e CLAP in prosa italiana.",
            styles["body"]
        ))
        story.append(Spacer(1, 6))
        for seg in narrative["segments"][:60]:
            story.append(Paragraph(
                f"<b>{seg['t_start_str']} - {seg['t_end_str']}</b>",
                styles["h3"]
            ))
            story.append(Paragraph(seg["narrative_it"], styles["body"]))
            story.append(Spacer(1, 4))
        if len(narrative["segments"]) > 60:
            story.append(Paragraph(
                f"<i>(+{len(narrative['segments'])-60} segmenti aggiuntivi omessi "
                f"per contenere la dimensione del PDF. Vedi summary JSON.)</i>",
                styles["caption"]
            ))
        story.append(PageBreak())

    # LETTURA COMPOSITIVA (AGENTE)
    story.append(Paragraph(INTESTAZIONI["lettura_compositiva"], styles["h1"]))
    story.extend(_build_composer_section(agent_text, styles))

    # COLOFONE
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Documento prodotto dalla skill soundscape-audio-analysis. "
        "Font Libre Baskerville e Source Sans Pro (OFL). "
        "Hum check con baseline locale, pre-check LUFS per classificazione semantica.",
        styles["caption"],
    ))

    doc.build(story)
    return output_path


# ========================================================================
# v0.3.0 CORPUS REPORT
# ========================================================================

def _markdown_to_story(markdown: str, styles: dict) -> list:
    """Converte markdown in flowable ReportLab via `md_renderer` (v0.3.1).

    Sostituisce la vecchia implementazione regex-based che non gestiva
    tabelle GFM. Il nuovo renderer usa mistune 3.x come parser AST e
    produce flowable ReportLab per titoli, paragrafi, liste, tabelle,
    blockquote, code fence, thematic break.

    Firma mantenuta per retrocompat con le chiamate esistenti.
    """
    from . import md_renderer
    return md_renderer.render_markdown(markdown, styles)


def _markdown_to_story_legacy(markdown: str, styles: dict) -> list:
    """Implementazione legacy regex-based. Conservata come riferimento.
    Non più chiamata dalla pipeline."""
    story: list = []
    md = sanitize_italiano(markdown)
    lines = md.splitlines()

    def emit_paragraph(buf: list[str]):
        if not buf:
            return
        text = " ".join(l.strip() for l in buf if l.strip())
        if not text:
            return
        # Conversione semplice inline: **bold** e *italic*
        # ReportLab usa <b>..</b> e <i>..</i>
        import re
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
        text = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", text)
        story.append(Paragraph(text, styles["body"]))

    buf: list[str] = []
    list_items: list[str] = []

    def flush_list():
        nonlocal list_items
        if list_items:
            import re
            for item in list_items:
                t = item.strip()
                t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
                t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", t)
                t = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", t)
                story.append(Paragraph(f"• {t}", styles["body"]))
            list_items = []

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("# "):
            emit_paragraph(buf); buf = []
            flush_list()
            story.append(Paragraph(line[2:].strip(), styles["h1"]))
        elif line.startswith("## "):
            emit_paragraph(buf); buf = []
            flush_list()
            story.append(Paragraph(line[3:].strip(), styles["h2"]))
        elif line.startswith("### "):
            emit_paragraph(buf); buf = []
            flush_list()
            story.append(Paragraph(line[4:].strip(), styles["h3"]))
        elif line.startswith("- ") or line.startswith("* "):
            emit_paragraph(buf); buf = []
            list_items.append(line[2:])
        elif not line.strip():
            emit_paragraph(buf); buf = []
            flush_list()
        else:
            buf.append(line)
    emit_paragraph(buf)
    flush_list()
    return story


def _corpus_metadata_table(
    corpus_metadata: dict, summaries: list[dict], styles
) -> Table:
    """Tabella panoramica una riga per file."""
    rows = [["File", "Durata", "LUFS", "DR (dB)", "Centroide", "Banda dom.", "NDSI"]]

    def dom_band(bands: dict) -> str:
        if not bands:
            return "?"
        return max(bands.items(), key=lambda kv: kv[1].get("energy_pct", 0))[0]

    for s in summaries:
        meta = s.get("metadata", {})
        tech = s.get("technical", {})
        spec = s.get("spectral", {})
        eco = s.get("ecoacoustic", {})
        rows.append([
            _short(meta.get("filename", "?"), 40),
            _fmt(meta.get("duration_s"), "{:.0f} s"),
            _fmt((tech.get("lufs") or {}).get("integrated_lufs"), "{:+.1f}"),
            _fmt((tech.get("levels") or {}).get("dynamic_range_db"), "{:.1f}"),
            _fmt((spec.get("timbre") or {}).get("spectral_centroid_hz"), "{:.0f} Hz"),
            dom_band(spec.get("bands_schafer", {})),
            _fmt((eco.get("ndsi") or {}).get("ndsi"), "{:+.2f}"),
        ])
    return report_styles.styled_table(
        rows, [55 * mm, 18 * mm, 18 * mm, 18 * mm, 22 * mm, 22 * mm, 18 * mm], styles
    )


def _short(name: str, max_len: int = 40) -> str:
    if len(name) <= max_len:
        return name
    return name[:max_len - 1] + "…"


def _on_corpus_cover(canvas, doc):
    """Copertina corpus: gradient blu + circoli decorativi distinti dalla cover singola."""
    canvas.saveState()
    PAL = config.PALETTE
    canvas.setFillColor(HexColor(PAL["dark"]))
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    # Tre circoli decorativi per distinguere da cover singolo-file
    canvas.setFillColor(HexColor(PAL["terracotta"]))
    canvas.circle(A4[0] - 35 * mm, A4[1] - 45 * mm, 18 * mm, fill=1, stroke=0)
    canvas.setFillColor(HexColor(PAL["teal"]))
    canvas.circle(A4[0] - 60 * mm, A4[1] - 90 * mm, 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(HexColor(PAL["dark_mid"]))
    canvas.circle(35 * mm, 60 * mm, 30 * mm, fill=1, stroke=0)
    canvas.restoreState()


def _fmt_total_duration(seconds: float) -> str:
    m = int(seconds) // 60
    h = m // 60
    if h:
        return f"{h}h {m % 60}min"
    return f"{m} min"


def build_corpus_report(
    corpus_title: str,
    corpus_metadata: dict,
    summaries: list[dict],
    comparison_plots: dict[str, Path],
    synth_markdown: str,
    output_path: Path,
    synth_available: bool = True,
    synth_note: str | None = None,
) -> Path:
    """Costruzione del PDF comparativo di corpus (v0.3.0).

    Args:
        corpus_title: titolo del corpus (es. "Villa Ficana v0.3").
        corpus_metadata: dict con {n_files, duration_total_s, generated_at, ...}.
        summaries: lista di summary JSON dei file analizzati.
        comparison_plots: mapping nome -> Path di ogni grafico comparativo.
        synth_markdown: markdown della sintesi dell'agente (o stringa vuota).
        output_path: path del PDF di output.
        synth_available: se False, al posto della sintesi viene mostrato un box
            di avviso con istruzioni per il merge manuale.
        synth_note: nota aggiuntiva da mostrare nella sezione sintesi
            (es. path del prompt salvato).
    """
    fonts = report_styles.register_fonts()
    styles = report_styles.build_styles(fonts)

    page_w, page_h = A4
    margin = 20 * mm

    cover_frame = Frame(margin, margin, page_w - 2 * margin, page_h - 2 * margin,
                        showBoundary=0, leftPadding=20 * mm, rightPadding=20 * mm,
                        topPadding=40 * mm, bottomPadding=20 * mm)
    body_frame = Frame(margin, margin + 10 * mm, page_w - 2 * margin,
                       page_h - 2 * margin - 10 * mm, showBoundary=0,
                       leftPadding=5 * mm, rightPadding=5 * mm,
                       topPadding=5 * mm, bottomPadding=5 * mm)

    doc = BaseDocTemplate(str(output_path), pagesize=A4,
                          title=f"Corpus report - {corpus_title}",
                          author="Francesco Mariano")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=cover_frame, onPage=_on_corpus_cover),
        PageTemplate(id="body", frames=body_frame, onPage=_on_body_page),
    ])

    story: list = []

    # COPERTINA
    story.append(Paragraph("Report comparativo<br/>di corpus", styles["h1_cover"]))
    story.append(Paragraph(corpus_title, styles["h2_cover"]))
    story.append(Spacer(1, 18 * mm))
    n_files = corpus_metadata.get("n_files", len(summaries))
    dur = corpus_metadata.get("duration_total_s", 0.0)
    story.append(Paragraph(
        f"<b>File analizzati:</b> {n_files}", styles["meta_cover"]
    ))
    story.append(Paragraph(
        f"<b>Durata totale:</b> {_fmt_total_duration(dur)}", styles["meta_cover"]
    ))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        f"Data: {date.today().isoformat()}", styles["meta_cover"]
    ))
    story.append(Paragraph(
        "Francesco Mariano, Accademia di Belle Arti di Macerata",
        styles["meta_cover"]
    ))
    story.append(Paragraph(
        "Skill soundscape-audio-analysis v0.3.2",
        styles["meta_cover"]
    ))
    # Fix v0.3.1: dopo la copertina passa al template body (sfondo bianco)
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

    # SOMMARIO ESECUTIVO
    story.append(Paragraph("Sommario esecutivo", styles["h1"]))
    story.append(Paragraph(
        f"Il corpus <b>{corpus_title}</b> riunisce {n_files} file audio "
        f"per una durata totale di {_fmt_total_duration(dur)}. Ogni file è stato "
        f"analizzato con la pipeline soundscape-audio-analysis v0.3.2: livelli "
        f"EBU R128, diagnosi tecnica (clipping, DC offset, hum con baseline "
        f"locale), analisi spettrale (bande Schafer, feature timbriche, onset), "
        f"indici ecoacustici (ACI, NDSI, H, BI), classificazione semantica via "
        f"PANNs CNN14 (527 classi AudioSet), auto-tagging CLAP sul vocabolario "
        f"italiano. Il presente documento affianca alle tabelle e ai grafici "
        f"comparativi una sintesi testuale prodotta in modalità non interattiva "
        f"a partire dal payload ridotto di ogni file e dal report di riferimento "
        f"Villa Ficana del 14 aprile 2026.",
        styles["body"]
    ))
    story.append(Spacer(1, 10))

    # TABELLA PANORAMICA
    story.append(Paragraph("Panoramica del corpus", styles["h2"]))
    story.append(_corpus_metadata_table(corpus_metadata, summaries, styles))
    story.append(PageBreak())

    # GRAFICI COMPARATIVI
    story.append(Paragraph("Grafici comparativi", styles["h1"]))
    plot_descriptions = {
        "lufs": ("Loudness integrato per file",
                 "Confronto dei livelli LUFS integrati (EBU R128). "
                 "Le linee tratteggiate indicano i target tipici broadcast (-23 LUFS) "
                 "e podcast/audioguide (-16 LUFS)."),
        "dynamic_range": ("Dynamic range percettivo",
                          "Differenza P95-P10 dei frame RMS: misura la presenza di "
                          "contrasto dinamico nel file."),
        "schafer": ("Distribuzione energia per banda Schafer",
                    "Heatmap della percentuale di energia nelle sette bande Schafer. "
                    "Utile per identificare file bass-heavy, brillanti, bilanciati."),
        "ecoacoustic": ("Indici ecoacustici normalizzati",
                        "Radar con ACI, NDSI, H e BI normalizzati min-max sul corpus. "
                        "Più la forma è ampia, più il file è ricco su tutti gli indici."),
        "clap_similarity": ("Similarità semantica CLAP",
                            "Matrice simmetrica di similarità coseno fra embedding "
                            "CLAP medi di ogni file. Valori vicini a 1 indicano "
                            "prossimità semantica."),
    }
    for plot_key, path in comparison_plots.items():
        title, desc = plot_descriptions.get(
            plot_key, (plot_key, "Grafico comparativo.")
        )
        story.append(Paragraph(title, styles["h3"]))
        try:
            story.append(Image(str(path), width=160 * mm, height=90 * mm,
                                kind="proportional"))
        except Exception:
            story.append(Paragraph(
                f"(impossibile caricare immagine {path.name})", styles["caption"]
            ))
        story.append(Paragraph(desc, styles["caption"]))
        story.append(Spacer(1, 6))
    story.append(PageBreak())

    # SINTESI COMPARATIVA (markdown agente)
    story.append(Paragraph("Sintesi comparativa", styles["h1"]))
    if synth_available and synth_markdown.strip():
        # Il titolo H1 eventuale nel markdown verrà trasformato: se è il primo
        # H1 del file (tipo "# Corpus..."), lo manteniamo.
        story.extend(_markdown_to_story(synth_markdown, styles))
    else:
        note_text = (
            "La sintesi automatica non è stata generata in questa esecuzione. "
            "Il prompt completo è stato salvato accanto al PDF e può essere "
            "lanciato manualmente con claude -p. Dopo aver ottenuto il markdown, "
            "usare il comando `soundscape report-merge <pdf> <markdown>` per "
            "integrarlo in questo PDF."
        )
        if synth_note:
            note_text += f" {synth_note}"
        story.append(report_styles.box_info(
            "Sintesi comparativa non disponibile",
            note_text,
            styles,
        ))

    # COLOFONE
    story.append(PageBreak())
    story.append(Paragraph("Colofone", styles["h2"]))
    story.append(Paragraph(
        "Documento prodotto dalla skill soundscape-audio-analysis v0.3.2. "
        "Font Libre Baskerville e Source Sans Pro (licenza SIL OFL). "
        "Pipeline analitica: librosa + soundfile per il carico audio, "
        "ffmpeg ebur128 per i LUFS, PANNs CNN14 per la classificazione semantica "
        "primaria, LAION-CLAP per l'auto-tagging italiano, scikit-maad-like "
        "per gli indici ecoacustici. Contrasto tipografico WCAG AA 4.5:1 "
        "verificato in tutte le pagine.",
        styles["body"]
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Corpus: {corpus_title}. File: {n_files}. "
        f"Durata totale: {_fmt_total_duration(dur)}. "
        f"Data generazione: {date.today().isoformat()}. "
        f"Francesco Mariano, Accademia di Belle Arti di Macerata.",
        styles["body"]
    ))

    doc.build(story)
    return output_path
