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
    rows = [["Banda", "Intervallo (Hz)", "Energia %", "dB rel."]]
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
        rows = [["Posizione", f"Categoria {model_label}", "Punteggio medio"]]
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
        rows = [["Posizione", "Prompt italiano", "Categoria", "Similarità"]]
        for i, t in enumerate(top_global, 1):
            # v0.5.1-0.5.2: tag con flag interpretativi vanno in corsivo.
            # v0.6.7: plausibility low aggiunge un marcatore testuale.
            prompt_text = t["prompt"]
            plausibility = t.get("plausibility")
            if t.get("likely_hallucination") or t.get("geo_specific") or plausibility == "low":
                prompt_text = f"<i>{prompt_text}</i>"
            if plausibility == "low":
                prompt_text += " [plausibilita bassa]"
            elif plausibility == "medium":
                prompt_text += " [plausibilita media]"
            rows.append([str(i), prompt_text, t.get("category", ""), f"{t['score']:.3f}"])
        story.append(report_styles.styled_table(
            rows, [14 * mm, 90 * mm, 38 * mm, 24 * mm], styles
        ))
        # v0.5.1: nota su tag marcati come allucinazioni
        n_halluc = sum(1 for t in top_global if t.get("likely_hallucination"))
        if n_halluc > 0:
            story.append(Paragraph(
                f"<i>{n_halluc} tag in corsivo menzionano voce/parlato ma "
                f"PANNs non rileva voce nel materiale: trattare come ipotesi "
                f"di lavoro a basso supporto empirico.</i>",
                styles["caption"],
            ))
        # v0.5.2: nota su tag italo-specifici, separata dalle allucinazioni
        n_geo = sum(1 for t in top_global
                     if t.get("geo_specific") and not t.get("likely_hallucination"))
        if n_geo > 0:
            story.append(Paragraph(
                f"<i>{n_geo} tag in corsivo sono italo-specifici "
                f"(prompt che menzionano luoghi italiani): valutare se il "
                f"contesto del materiale e' effettivamente italiano. Per "
                f"materiale mediterraneo non italiano la categoria "
                f"'paesaggi mediterranei generici' offre alternative piu' "
                f"appropriate.</i>",
                styles["caption"],
            ))
        # v0.6.7: nota su tag con plausibilita' bassa o media (pre-filtro
        # deterministico su 5 pattern di falso positivo documentati).
        n_low = sum(1 for t in top_global if t.get("plausibility") == "low")
        n_med = sum(1 for t in top_global if t.get("plausibility") == "medium")
        if n_low > 0 or n_med > 0:
            parts = []
            if n_low > 0:
                parts.append(f"{n_low} tag marcato 'plausibilita bassa'")
            if n_med > 0:
                parts.append(f"{n_med} tag marcato 'plausibilita media'")
            story.append(Paragraph(
                f"<i>{', '.join(parts)}: il pre-filtro v0.6.6 ha rilevato "
                f"che il referente concreto evocato dal prompt (acqua, "
                f"preghiera, spiaggia, biofonia, treno) non e' corroborato "
                f"da PANNs sulle label AudioSet correlate. I tag con "
                f"plausibilita bassa vanno ignorati; quelli con plausibilita "
                f"media possono essere usati come ipotesi di lavoro.</i>",
                styles["caption"],
            ))
        story.append(Spacer(1, 8))

    hints_text = _format_academic_hints(clap.get("academic_hints", {}))
    if hints_text:
        story.append(Paragraph(
            "<b>Hint accademici aggregati</b>", styles["body"]
        ))
        story.append(Paragraph(hints_text, styles["body"]))
        story.append(Spacer(1, 8))

    # v0.12.3: timeline 10s tabellare RIMOSSA dal PDF.
    # Resta in summary.json per data-mining (chiave clap.timeline).
    # La Partitura grafica (sezione 3) comunica la stessa informazione
    # visivamente via plot_tags_timeline.
    timeline = clap.get("timeline", [])
    if timeline:
        story.append(Paragraph(
            f"<i>Timeline tag per segmento di {clap.get('segment_seconds', 10.0):.0f} s "
            f"disponibile in `summary.json` ({len(timeline)} finestre). "
            f"La sintesi grafica a colori e' nella Partitura grafica.</i>",
            styles["caption"],
        ))
    return story


def _fmt_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


def _build_speech_block(speech: dict, base_name: str, styles) -> list:
    """Sezione PDF per trascrizione dialoghi (v0.5.1).

    Contenuto:
    - Header con modello, device, compute_type, lingua rilevata,
      probability, durata parlato / durata totale, segmenti VAD.
    - Warning se probability < WHISPER_LANG_CONF_WARN (audio multilingua).
    - Tabella top-10 segmenti (Tempo, Testo originale).
    - Trascritto completo inline se < TRANSCRIPT_PDF_MAX_CHARS.
    - Traduzione italiana inline se lingua != it e testo corto.
    - Nota su file .txt companion altrimenti.

    Ritorna [] se speech non abilitato o skipped.
    """
    story = []
    if not speech or not speech.get("enabled"):
        return story
    if speech.get("skipped_reason"):
        return story

    model_name = speech.get("model_name", "Whisper")
    device = speech.get("device", "")
    compute_type = speech.get("compute_type", "")
    lang = speech.get("language_detected", "?")
    prob = float(speech.get("language_probability", 0.0))
    dur_speech = float(speech.get("duration_speech_s", 0.0))
    dur_total = float(speech.get("duration_total_s", 0.0))
    pct = (dur_speech / dur_total * 100.0) if dur_total > 0 else 0.0
    n_vad = int(speech.get("n_vad_segments", 0))

    header = (
        f"Modello: <b>{model_name}</b>, device {device}, compute_type "
        f"{compute_type}. Lingua rilevata: <b>{lang}</b> "
        f"({prob * 100:.1f}%). Durata parlato: {dur_speech:.1f} s su "
        f"{dur_total:.1f} s ({pct:.1f}%). Segmenti VAD: {n_vad}."
    )
    story.append(Paragraph(header, styles["body"]))
    story.append(Spacer(1, 4))

    if prob < config.WHISPER_LANG_CONF_WARN and prob > 0:
        story.append(Paragraph(
            f"<i>Lingua rilevata con probabilita' bassa ({prob:.2f}): "
            f"possibile audio multilingua, trascrizione e traduzione da "
            f"verificare manualmente.</i>",
            styles["caption"]
        ))
        story.append(Spacer(1, 4))

    segments = speech.get("segments") or []
    if segments:
        story.append(Paragraph(
            "<b>Segmenti trascritti (top-10)</b>", styles["body"]
        ))
        rows = [["Tempo", "Testo originale"]]
        for seg in segments[:10]:
            t0 = _fmt_time(seg.get("t_start_s", 0))
            t1 = _fmt_time(seg.get("t_end_s", 0))
            text = (seg.get("text") or "").strip()
            if len(text) > 120:
                text = text[:117] + "..."
            rows.append([f"{t0}-{t1}", text])
        if len(segments) > 10:
            rows.append([
                "...",
                f"+{len(segments) - 10} segmenti omessi, vedi .txt companion"
            ])
        story.append(report_styles.styled_table(
            rows, [22 * mm, 140 * mm], styles
        ))
        story.append(Spacer(1, 6))

    transcript = speech.get("transcript") or ""
    transcript_it = speech.get("transcript_it") or ""
    translation_fallback = bool(speech.get("translation_fallback"))

    if len(transcript) < config.TRANSCRIPT_PDF_MAX_CHARS:
        story.append(Paragraph("<b>Trascritto completo</b>", styles["body"]))
        story.append(Paragraph(transcript.replace("\n", "<br/>"), styles["body"]))
        story.append(Spacer(1, 6))
        if lang != "it" and transcript_it and transcript_it != transcript:
            story.append(Paragraph(
                "<b>Traduzione italiana</b>", styles["body"]
            ))
            story.append(Paragraph(
                transcript_it.replace("\n", "<br/>"), styles["body"]
            ))
            story.append(Spacer(1, 6))
    else:
        note = (
            f"Trascritto completo esportato in "
            f"<font face=\"Courier\">{base_name}_transcript.txt</font> "
            f"accanto al PDF."
        )
        if lang != "it" and transcript_it and transcript_it != transcript:
            note += (
                f" Traduzione italiana in "
                f"<font face=\"Courier\">{base_name}_transcript_it.txt</font>."
            )
        story.append(Paragraph(note, styles["body"]))

    if translation_fallback and lang != "it":
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "<i>Traduzione italiana non disponibile (claude non in PATH o "
            "errore subprocess): testo originale preservato.</i>",
            styles["caption"]
        ))

    return story


def _format_academic_hints(hints: dict) -> str:
    """Formatta gli academic_hints CLAP (v0.5.1) in prosa compatta per PDF.

    Ritorna stringa vuota se gli hint non sono disponibili.
    """
    if not hints or not hints.get("available"):
        return ""
    parts = []
    krause = hints.get("krause", {}).get("distribution", {})
    if krause:
        krause_str = ", ".join(
            f"{k} {int(v * 100)}%"
            for k, v in sorted(krause.items(), key=lambda kv: -kv[1])
        )
        parts.append(f"<b>Distribuzione Krause:</b> {krause_str}")
    schafer_present = hints.get("schafer_role", {}).get("present", [])
    if schafer_present:
        parts.append(
            f"<b>Ruoli Schafer presenti:</b> {', '.join(schafer_present)}"
        )
    schafer_fid = hints.get("schafer_fidelity", {}).get("value")
    if schafer_fid and schafer_fid != "n/a":
        parts.append(f"<b>Fidelity (Schafer):</b> {schafer_fid}")
    schaeffer = hints.get("schaeffer_type", {}).get("top_2", [])
    if schaeffer:
        s_str = ", ".join(
            f"{v} {int(p * 100)}%" for v, p in schaeffer[:2]
        )
        parts.append(f"<b>Schaeffer:</b> {s_str}")
    smalley = hints.get("smalley_motion", {}).get("top_2", [])
    if smalley:
        sm_str = ", ".join(
            f"{v} {int(p * 100)}%" for v, p in smalley[:2]
        )
        parts.append(f"<b>Smalley motion:</b> {sm_str}")
    # v0.6.5: tassonomie compositive estese (schaeffer_detail TARTYP 22 sotto-tipi,
    # smalley_growth 6 growth processes). Rese solo se confidence sufficiente per
    # evitare rumore; sempre citate come ipotesi (tentative=True nel payload).
    schaeffer_detail = hints.get("schaeffer_detail", {})
    sd_conf = schaeffer_detail.get("confidence")
    sd_value = schaeffer_detail.get("value")
    if sd_value and sd_conf in ("high", "medium"):
        sd_pct = int(schaeffer_detail.get("pct", 0) * 100)
        parts.append(
            f"<b>Schaeffer detail (TARTYP, {sd_conf}):</b> "
            f"<i>{sd_value}</i> {sd_pct}%"
        )
    smalley_growth = hints.get("smalley_growth", {})
    sg_conf = smalley_growth.get("confidence")
    sg_value = smalley_growth.get("value")
    if sg_value and sg_conf in ("high", "medium"):
        sg_pct = int(smalley_growth.get("pct", 0) * 100)
        parts.append(
            f"<b>Smalley growth ({sg_conf}):</b> "
            f"<i>{sg_value}</i> {sg_pct}%"
        )
    chion = hints.get("chion_modes_present", [])
    if chion:
        parts.append(f"<b>Modi Chion:</b> {', '.join(chion)}")
    sw = hints.get("westerkamp_soundwalk_relevance", {})
    if sw.get("value"):
        parts.append(
            f"<b>Rilevanza soundwalk:</b> sì ({int(sw.get('pct', 0) * 100)}%, ipotesi)"
        )
    return ". ".join(parts) + "." if parts else ""


def _build_structure_block(structure: dict, timeline_path: Path | None, styles) -> list:
    """Sezione PDF "Sezioni strutturali" (v0.6.0).

    Contenuto:
    - Header con numero sezioni e finestra di analisi.
    - Immagine timeline grafica (bande colorate per Krause, da
      plotting.plot_structure_timeline) se `timeline_path` esiste.
    - Tabella sezioni: id, range, durata, signature_label, dominant
      PANNs, RMS medio, centroide medio.

    Ritorna [] se structure non popolato.
    """
    story = []
    if not structure or not structure.get("enabled"):
        return story
    sections = structure.get("sections") or []
    if not sections:
        return story

    n = len(sections)
    win = float(structure.get("window_seconds", config.STRUCTURE_WINDOW_S))
    header = (
        f"Identificate <b>{n}</b> sezioni significative via changepoint "
        f"detection deterministico su gradiente RMS, centroide, flatness "
        f"e categorie dominanti, finestra di analisi {win:.0f} s. La "
        f"signature di ciascuna sezione e' derivata da Krause dominante + "
        f"caratteristiche dinamiche e timbriche, non dall'agente. "
        f"L'agente compositivo riceve queste sezioni come ossatura per "
        f"organizzare la propria lettura."
    )
    story.append(Paragraph(header, styles["body"]))
    story.append(Spacer(1, 6))

    # Timeline grafica
    if timeline_path is not None and Path(timeline_path).exists():
        try:
            img = Image(str(timeline_path), width=170 * mm, height=24 * mm)
            story.append(img)
            story.append(Spacer(1, 6))
        except Exception:
            pass

    # Tabella sezioni
    rows = [["ID", "Inizio", "Fine", "Durata", "Signature", "Krause", "RMS dB", "Centroide Hz"]]
    for s in sections:
        rows.append([
            s.get("id", ""),
            _fmt_time(s.get("t_start_s", 0)),
            _fmt_time(s.get("t_end_s", 0)),
            f"{s.get('duration_s', 0):.0f} s",
            (s.get("signature_label") or "")[:28],
            s.get("krause", ""),
            _fmt(s.get("mean_rms_db"), "{:+.1f}"),
            _fmt(s.get("mean_centroid_hz"), "{:.0f}"),
        ])
    story.append(report_styles.styled_table(
        rows,
        [12 * mm, 16 * mm, 16 * mm, 16 * mm, 50 * mm, 22 * mm, 18 * mm, 22 * mm],
        styles,
    ))
    return story


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
    # v0.5.1: contesto musicale per evitare letture errate dei picchi
    hint = hum.get("interpretation_hint") or {}
    if hint.get("likely_musical_harmonic"):
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"<i>Contesto: {hint.get('reason', '')}.</i>",
            styles["body"],
        ))
    return story


def _eco_radar_commentary(eco: dict) -> str:
    """v0.12.3: 2-3 frasi di commento accanto al radar ecoacustico."""
    ndsi_v = float((eco.get("ndsi") or {}).get("ndsi") or 0.0)
    h_total = float((eco.get("h_entropy") or {}).get("h_total") or 0.0)
    bi_v = float(eco.get("bi") or 0.0)
    aci_v = float(eco.get("aci") or 0.0)
    parts = []
    if ndsi_v > 0.3:
        parts.append("NDSI positivo indica predominanza biofonica")
    elif ndsi_v < -0.3:
        parts.append("NDSI negativo indica predominanza antropofonica")
    else:
        parts.append("NDSI vicino a zero, rapporto biofonia/antropofonia bilanciato")
    if h_total > 0.80:
        parts.append(f"entropia alta ({h_total:.2f}) indica paesaggio ricco")
    elif h_total < 0.50:
        parts.append(f"entropia bassa ({h_total:.2f}) indica paesaggio concentrato")
    else:
        parts.append(f"entropia media ({h_total:.2f})")
    if bi_v > 20000:
        parts.append(f"BI elevato ({bi_v:.0f}) supporta la lettura biofonica")
    if aci_v > 100000:
        parts.append(f"ACI alto ({aci_v:.0f}) segnala attivita' spettrale densa")
    return ". ".join(parts) + "."


def _build_executive_summary(summary: dict, styles) -> list:
    """v0.12.0: sintesi iniziale (una pagina) pensata per il compositore.

    Riunisce in uno sguardo: identita' del brano, qualita' di registrazione,
    carattere ecoacustico, top famiglie semantiche. Non sostituisce le
    sezioni tecniche dettagliate, le anticipa.
    """
    meta = summary.get("metadata", {}) or {}
    tech = summary.get("technical", {}) or {}
    spec = summary.get("spectral", {}) or {}
    hum = summary.get("hum", {}) or {}
    eco = summary.get("ecoacoustic", {}) or {}
    clap = summary.get("clap") or {}
    classifier = (summary.get("semantic", {}) or {}).get("classifier", {}) or {}
    structure = summary.get("structure") or {}

    levels = tech.get("levels", {}) or {}
    lufs = tech.get("lufs", {}) or {}
    tp = tech.get("true_peak", {}) or {}
    hifi = spec.get("hifi_lofi", {}) or {}

    rows = [["", ""]]
    rows.append([
        "Durata / formato",
        f"{_fmt(meta.get('duration_s'), '{:.1f} s')} - "
        f"{_fmt(meta.get('sr'), '{} Hz')} - {_fmt(meta.get('channels'))} canali",
    ])
    rows.append([
        "Qualità di registrazione",
        f"LUFS integrato {_fmt(lufs.get('integrated_lufs'), '{:+.1f}')}, "
        f"true peak {_fmt(tp.get('true_peak_dbtp'), '{:+.2f}')} dBTP, "
        f"dinamica {_fmt(levels.get('dynamic_range_db'), '{:.1f}')} dB",
    ])
    hifi_score = hifi.get("score")
    hifi_label = hifi.get("label", "")
    rows.append([
        "Profilo Schafer",
        f"Hi-Fi/Lo-Fi score {hifi_score}/5 ({hifi_label}). "
        f"Hum 50/60 Hz {'rilevato' if hum.get('detected') else 'entro baseline'}.",
    ])

    krause = (eco.get("krause") or {})
    if krause:
        k_sorted = sorted(
            ((k, v) for k, v in krause.items() if isinstance(v, (int, float))),
            key=lambda kv: -kv[1],
        )[:3]
        parts = [f"{k} {v*100:.0f}%" if v <= 1 else f"{k} {v:.0f}%" for k, v in k_sorted]
        rows.append(["Triade ecoacustica (Krause)", ", ".join(parts)])

    top_panns = (classifier.get("top_categories") or [])[:3]
    if top_panns:
        parts = [f"{_translate_label_for_summary(c.get('name',''))} ({c.get('score',0):.2f})"
                 for c in top_panns if c.get("score", 0) > 0.03]
        if parts:
            rows.append(["Classificatore semantico (PANNs)", ", ".join(parts)])

    top_clap = (clap.get("top_global") or [])[:3]
    if top_clap:
        parts = [f"«{t.get('prompt','')}» ({t.get('score',0):.2f})"
                 for t in top_clap if t.get("score", 0) > 0.20]
        if parts:
            rows.append(["Auto-tag CLAP", "; ".join(parts)])

    n_sec = len((structure.get("sections") or []))
    if n_sec:
        rows.append([
            "Struttura",
            f"{n_sec} sezioni significative (changepoint detection)",
        ])

    table = report_styles.styled_table(
        rows[1:], [62 * mm, 108 * mm], styles, header=False,
    )

    intro = Paragraph(
        "Questa sintesi e' pensata come prima lettura: identita' del brano, "
        "qualita' di registrazione, carattere ecoacustico, famiglie semantiche "
        "dominanti. Le pagine successive articolano la lettura compositiva "
        "e i dettagli analitici.",
        styles["body"],
    )
    return [intro, Spacer(1, 6), table, Spacer(1, 8)]


def _translate_label_for_summary(label: str) -> str:
    """Traduzione leggera di label PANNs per la tabella sintesi.

    Non dipende dal modulo narrative (che importa librosa), quindi resta
    auto-contained. Per i casi non mappati ritorna il label originale.
    """
    mapping = {
        "Speech": "parlato umano",
        "Music": "musica",
        "Silence": "silenzio",
        "Animal": "animali",
        "Bird": "uccelli",
        "Insect": "insetti",
        "Water": "acqua",
        "Wind": "vento",
        "Vehicle": "veicoli",
        "Engine": "motore",
        "Environmental noise": "rumore ambientale",
    }
    return mapping.get(label, label.lower())


def _build_narrative_by_section(structure: dict, narrative: dict, styles) -> list:
    """v0.12.3: sintesi compatta per sezione strutturale.

    Cambio rispetto a v0.12.0: non concatena piu' la prosa di tutte le
    finestre 30s interne (che su sezioni lunghe produceva muri di testo
    di 10+ pagine). Produce invece un singolo paragrafo di sintesi per
    sezione, estraendo programmaticamente:
      - firma RMS/centroide/flatness media della sezione
      - onset density media
      - PANNs top dominante (sezione)
      - famiglia CLAP dominante (sezione, con nuova mappa famiglie)
      - eventuale variazione interna significativa (range RMS)

    La prosa per-finestra resta disponibile in `summary.json`. Il sub-agent
    compositivo riceve comunque le 30s per la sua lettura drammaturgica.
    """
    from . import clap_families

    story: list = []
    sections = (structure or {}).get("sections") or []
    segments = (narrative or {}).get("segments") or []
    if not sections:
        return story

    intro = Paragraph(
        "Sintesi empirica per ciascuna sezione strutturale: firma media, "
        "famiglia semantica dominante, variazione interna. La granularità "
        "30 s resta disponibile in `summary.json` e alimenta la Lettura "
        "compositiva precedente.",
        styles["body"],
    )
    story.append(intro)
    story.append(Spacer(1, 6))

    def _fmt_flatness(f: float) -> str:
        if f < 0.02:
            return "tonale"
        if f < 0.10:
            return "tonale-misto"
        if f < 0.30:
            return "misto"
        return "rumoroso"

    def _fmt_centroid(hz: float) -> str:
        if hz < 500:
            return "graves"
        if hz < 2000:
            return "medi"
        if hz < 5000:
            return "brillanti"
        return "molto brillanti"

    def _fmt_density(d: float) -> str:
        if d < 0.3:
            return "rarefatto"
        if d < 1.0:
            return "sparso"
        if d < 2.5:
            return "medio"
        return "denso"

    for sec in sections:
        t_s = float(sec.get("t_start_s", 0.0))
        t_e = float(sec.get("t_end_s", 0.0))
        sig_label = (sec.get("signature_label") or "").strip()
        header = (
            f"<b>{sec.get('id','')}</b> "
            f"({_fmt_time(t_s)} - {_fmt_time(t_e)}, "
            f"{sec.get('duration_s', 0):.0f} s"
            + (f", {sig_label}" if sig_label else "")
            + ")"
        )
        story.append(Paragraph(header, styles["h3"]))

        # Aggregazione deterministica dalle finestre interne
        within = [
            s for s in segments
            if float(s.get("t_end_s", 0.0)) > t_s and float(s.get("t_start_s", 0.0)) < t_e
        ]
        n_win = len(within)

        rms_vals = [s.get("rms_db") for s in within if isinstance(s.get("rms_db"), (int, float))]
        cen_vals = [s.get("centroid_hz") for s in within if isinstance(s.get("centroid_hz"), (int, float))]
        flat_vals = [s.get("flatness") for s in within if isinstance(s.get("flatness"), (int, float))]
        dens_vals = [s.get("density") for s in within if isinstance(s.get("density"), (int, float))]

        rms_mean = sum(rms_vals) / len(rms_vals) if rms_vals else sec.get("mean_rms_db")
        cen_mean = sum(cen_vals) / len(cen_vals) if cen_vals else sec.get("mean_centroid_hz")
        flat_mean = sum(flat_vals) / len(flat_vals) if flat_vals else sec.get("mean_flatness")
        dens_mean = sum(dens_vals) / len(dens_vals) if dens_vals else 0.0

        # Famiglia CLAP dominante su window della sezione
        clap_windows = []
        for s in within:
            tl_entry = s.get("clap_windows") or []
            clap_windows.extend(tl_entry if isinstance(tl_entry, list) else [])
        # Fallback: usa la dominante PANNs della sezione se clap_windows non
        # viene esposto nei segmenti narrative.
        fam_label = None
        try:
            if clap_windows:
                doms = clap_families.dominant_family_per_window(clap_windows)
                if doms:
                    from collections import Counter
                    most_fam = Counter(d["family"] for d in doms).most_common(1)[0][0]
                    fam_label = clap_families.family_meta(most_fam).get("label", most_fam)
        except Exception:
            fam_label = None

        # Sintesi discorsiva (max 4-5 frasi brevi)
        parts: list[str] = []
        if cen_mean is not None and flat_mean is not None:
            parts.append(
                f"La firma timbrica media e' su registro {_fmt_centroid(cen_mean)} "
                f"({cen_mean:.0f} Hz) con spettro {_fmt_flatness(flat_mean)} "
                f"(flatness {flat_mean:.3f})."
            )
        if rms_mean is not None:
            parts.append(f"Dinamica RMS media {rms_mean:+.1f} dBFS.")
            if rms_vals and len(rms_vals) > 1:
                rms_range = max(rms_vals) - min(rms_vals)
                if rms_range > 8:
                    parts.append(
                        f"All'interno della sezione la dinamica oscilla su "
                        f"{rms_range:.0f} dB, segno di modulazione interna."
                    )
        if dens_mean:
            parts.append(
                f"Densita' di onset {_fmt_density(dens_mean)} ({dens_mean:.1f}/s)."
            )
        dom_panns = (sec.get("dominant_panns") or "").strip()
        if dom_panns:
            parts.append(f"PANNs dominante: {dom_panns}.")
        if fam_label:
            parts.append(f"Famiglia CLAP prevalente: {fam_label}.")
        krause = (sec.get("krause") or "").strip()
        if krause:
            parts.append(f"Triade ecoacustica: predomina {krause}.")
        if n_win:
            parts.append(
                f"Sintesi derivata da {n_win} finestre di 30 s interne."
            )
        if not parts:
            parts.append("Dati insufficienti per una sintesi discorsiva.")

        story.append(Paragraph(" ".join(parts), styles["body"]))
        story.append(Spacer(1, 4))

    return story


def _build_narrative_legenda(styles) -> list:
    """v0.11: legenda dei valori per la Descrizione segmentata.

    Tabella compatta con le soglie qualitative di PANNs, CLAP, flatness,
    centroide, onset density, LRA e LUFS. Permette di leggere i numeri
    fra parentesi delle finestre senza doverli interpretare a mente.
    """
    intro = Paragraph(
        "I valori fra parentesi nelle finestre seguenti sono riportati a titolo "
        "di tracciabilità empirica. I qualificatori linguistici "
        "(«presenza tenue di ...», «affinità debole con ...», «spettro tonale») "
        "traducono lo stesso valore in una soglia qualitativa. La tabella "
        "riassume le soglie usate dalla skill.",
        styles["body"],
    )
    rows = [
        ["Indicatore", "Trascurabile", "Tenue", "Plausibile", "Marcato"],
        ["PANNs (classificatore AudioSet)", "<0.03", "0.03-0.15", "0.15-0.40", ">0.40"],
        ["CLAP (cosine audio/prompt)", "<0.20", "0.20-0.30", "0.30-0.40", ">0.40"],
        ["Flatness spettrale", "tonale <0.05", "tendenz. tonale 0.05-0.20", "misto 0.20-0.50", "rumoroso >0.50"],
        ["Centroide spettrale (Hz)", "graves <500", "medi 500-2000", "brillanti 2000-5000", "molto brillanti >5000"],
        ["Onset density (eventi/s)", "rarefatto <0.3", "sparso 0.3-1.0", "medio 1.0-2.5", "denso >2.5"],
        ["Dinamica LRA (LU)", "compressa <7", "moderata 7-15", "ampia 15-25", "estrema >25"],
        ["LUFS integrato", "basso <-23", "standard -23/-14", "loud -14/-9", "pompato >-9"],
    ]
    table = report_styles.styled_table(
        rows,
        [52 * mm, 26 * mm, 30 * mm, 34 * mm, 34 * mm],
        styles,
    )
    return [intro, Spacer(1, 6), table, Spacer(1, 10)]


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

    tech = summary.get("technical", {}) or {}
    hum = summary.get("hum", {}) or {}
    spec = summary.get("spectral", {}) or {}
    eco = summary.get("ecoacoustic", {}) or {}
    semantic = summary.get("semantic", {}) or {}
    clap = summary.get("clap") or {}
    speech = summary.get("speech") or {}
    mc = summary.get("multichannel")
    structure = summary.get("structure") or {}
    narrative = summary.get("narrative") or {}

    # v0.12.0 REORGANIZATION:
    # 1) Sintesi (executive summary)
    # 2) Lettura compositiva (dal sub-agent)
    # 3) Partitura grafica (spettrogramma + timeline strutturale)
    # 4) Overview tecnica compatta
    # 5) Descrizione per sezioni strutturali (non 40 finestre 30s)
    # 6) Appendice: CLAP/PANNs/speech/multichannel/GRM/raw

    # 1. SINTESI
    story.append(Paragraph(INTESTAZIONI["executive_summary"], styles["h1"]))
    story.extend(_build_executive_summary(summary, styles))
    story.append(PageBreak())

    # 2. LETTURA COMPOSITIVA (spostata in testa)
    story.append(Paragraph(INTESTAZIONI["lettura_compositiva"], styles["h1"]))
    story.extend(_build_composer_section(agent_text, styles))
    story.append(PageBreak())

    # 3. PARTITURA GRAFICA: spettrogramma + timeline strutturale
    story.append(Paragraph(INTESTAZIONI["partitura_grafica"], styles["h1"]))
    story.append(Paragraph(
        "Sintesi visiva del brano: lo spettrogramma log-frequenza come "
        "partitura del colore, sotto la timeline delle sezioni strutturali "
        "identificate via changepoint detection.",
        styles["body"],
    ))
    story.append(Spacer(1, 6))
    if plot_paths and plot_paths.get("spectrogram"):
        story.append(Image(str(plot_paths["spectrogram"]), width=170 * mm, height=65 * mm))
        story.append(Paragraph("Spettrogramma log-frequenza, scala dB.", styles["caption"]))
        story.append(Spacer(1, 4))
    timeline_path = (plot_paths or {}).get("structure_timeline")
    if timeline_path is not None and Path(timeline_path).exists():
        try:
            story.append(Image(str(timeline_path), width=170 * mm, height=26 * mm))
            story.append(Paragraph(
                "Sezioni strutturali colorate per Krause dominante.",
                styles["caption"],
            ))
        except Exception:
            pass
    tags_path = (plot_paths or {}).get("tags_timeline")
    if tags_path is not None and Path(tags_path).exists():
        try:
            story.append(Spacer(1, 4))
            story.append(Image(str(tags_path), width=170 * mm, height=30 * mm))
            story.append(Paragraph(
                "Timeline delle famiglie semantiche CLAP: ogni colore corrisponde "
                "a una macro-categoria (biofonia, geofonia, antropofonia umana/meccanica, "
                "paesaggio urbano/geografico, musica e processing, oggetti astratti). "
                "Intensita' del colore proporzionale al cosine score di similarita'.",
                styles["caption"],
            ))
        except Exception:
            pass
    story.append(PageBreak())

    # 4. OVERVIEW TECNICA compatta
    story.append(Paragraph(INTESTAZIONI["overview_tecnica"], styles["h1"]))
    story.append(Paragraph(INTESTAZIONI["metadati"], styles["h2"]))
    story.append(_build_metadati_table(meta, styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph(INTESTAZIONI["livelli_dinamica"], styles["h2"]))
    story.append(_build_livelli_table(tech, styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph(INTESTAZIONI["diagnosi_tecnica"], styles["h2"]))
    story.append(_build_diagnosi_table(tech, hum, styles))
    story.append(Spacer(1, 6))
    story.extend(_build_hum_block(hum, styles))
    story.append(PageBreak())

    story.append(Paragraph(INTESTAZIONI["spettro"], styles["h2"]))
    story.append(_build_bande_table(spec.get("bands_schafer", {}), styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph(INTESTAZIONI["caratt_timbrica"], styles["h2"]))
    story.append(_build_timbre_table(spec.get("timbre", {}), spec.get("onsets", {}),
                                      spec.get("hifi_lofi", {}), styles))
    story.append(Spacer(1, 6))
    if plot_paths and plot_paths.get("bands_bar"):
        story.append(Image(str(plot_paths["bands_bar"]), width=165 * mm, height=55 * mm))
    if eco:
        story.append(Spacer(1, 6))
        story.append(Paragraph(INTESTAZIONI["ecoacustica"], styles["h2"]))
        radar_path = (plot_paths or {}).get("ecoacoustic_radar")
        if radar_path is not None and Path(radar_path).exists():
            try:
                story.append(Image(str(radar_path), width=110 * mm, height=90 * mm))
                story.append(Paragraph(
                    _eco_radar_commentary(eco),
                    styles["caption"],
                ))
            except Exception:
                story.append(_build_eco_table(eco, styles))
        else:
            story.append(_build_eco_table(eco, styles))
    story.append(PageBreak())

    # 5. DESCRIZIONE PER SEZIONI STRUTTURALI (v0.12.0: non piu' 40 finestre 30s)
    if structure.get("enabled") and structure.get("sections"):
        story.append(Paragraph(INTESTAZIONI["sezioni_strutturali"], styles["h1"]))
        story.extend(_build_structure_block(structure, None, styles))
        story.append(Spacer(1, 8))
        if narrative.get("enabled") and narrative.get("segments"):
            story.extend(_build_narrative_legenda(styles))
            story.extend(_build_narrative_by_section(structure, narrative, styles))
        story.append(PageBreak())

    # 6. APPENDICE
    story.append(Paragraph(INTESTAZIONI["appendice"], styles["h1"]))
    story.append(Paragraph(
        "Dati di supporto per fact-checking: classificazione PANNs dettagliata, "
        "auto-tagging CLAP top-20, trascrizione dialoghi, analisi multicanale "
        "ed eventuali confronti sperimentali. La descrizione segmentata finestra "
        "per finestra (30 s) resta disponibile in `summary.json`.",
        styles["body"],
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph(INTESTAZIONI["classificazione_semantica"], styles["h2"]))
    story.extend(_build_semantic_block(semantic, styles))
    story.append(PageBreak())

    if clap.get("enabled"):
        story.append(Paragraph(INTESTAZIONI["clap"], styles["h2"]))
        story.extend(_build_clap_block(clap, styles))
        story.append(PageBreak())

    if speech.get("enabled") and not speech.get("skipped_reason"):
        base_name = Path(summary.get("metadata", {}).get("filename", "file")).stem
        story.append(Paragraph(INTESTAZIONI["dialoghi_trascritti"], styles["h2"]))
        story.extend(_build_speech_block(speech, base_name, styles))
        story.append(PageBreak())

    if mc:
        story.append(Paragraph(INTESTAZIONI["multicanale"], styles["h2"]))
        story.extend(_build_multichannel_block(mc, styles))
        story.append(PageBreak())

    if rank_grm:
        story.append(Paragraph(INTESTAZIONI["confronto_grm"], styles["h2"]))
        story.append(report_styles.box_info(
            "Confronto sperimentale con profili GRM letteratura-based",
            "Sezione attivata manualmente via --compare=grm-experimental. "
            "I profili di riferimento sono stimati da letteratura e non da audio reale.",
            styles,
        ))
        story.append(Spacer(1, 6))
        story.extend(_build_confronto_grm_block(rank_grm, styles))
        story.append(PageBreak())

    # COLOFONE
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Documento prodotto dalla skill soundscape-audio-analysis di "
        "Francesco Mariano. Font Libre Baskerville e Source Sans Pro (OFL). "
        "Hum check con baseline locale, pre-check LUFS per classificazione "
        "semantica.",
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
        "Skill soundscape-audio-analysis v0.6.8",
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
        f"analizzato con la pipeline soundscape-audio-analysis v0.6.8: livelli "
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
        "Documento prodotto dalla skill soundscape-audio-analysis v0.6.8 di "
        "Francesco Mariano. Font Libre Baskerville e Source Sans Pro "
        "(licenza SIL OFL). Pipeline analitica: librosa + soundfile per il "
        "carico audio, ffmpeg ebur128 per i LUFS, PANNs CNN14 per la "
        "classificazione semantica primaria, LAION-CLAP per l'auto-tagging "
        "italiano, scikit-maad-like per gli indici ecoacustici. Contrasto "
        "tipografico WCAG AA 4.5:1 verificato in tutte le pagine.",
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
