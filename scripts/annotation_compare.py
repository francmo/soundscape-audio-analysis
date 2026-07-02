"""Confronto fra annotazioni umane (PWA Annotation Atelier) e analisi della skill.

Chiude il verso mancante del loop di interscambio. Il comando `enrich` porta
l'analisi della skill dentro il file dell'Atelier (skill -> umano); questo
modulo misura invece l'accordo fra ciò che l'annotatore ha marcato first-hand
e ciò che la pipeline ha rilevato (umano vs macchina), su tre assi.

1. Accordo sui confini strutturali. Le sezioni umane (structure[]) contro le
   sezioni della skill (changepoint detection), con tolleranza temporale in
   stile MIREX (precision, recall, F1 sui punti di taglio interni).
2. Accordo per bin sulla famiglia Krause. Le annotazioni umane della
   tassonomia Krause (biofonia, antropofonia, geofonia) contro la timeline
   PANNs proiettata sulle famiglie via config.PANNS_LABEL_TO_KRAUSE.
   Percent agreement + Cohen's kappa multiclasse sui bin confrontabili.
3. Copertura per annotazione. Per ogni annotazione Krause di famiglia, la
   frazione temporale coperta da segmenti macchina concordi; per le altre
   tassonomie (Schaeffer, Smalley, ...) non esiste una proiezione onesta
   sulle etichette AudioSet, quindi il confronto resta descrittivo (sezione
   macchina di massimo overlap), senza verdetto numerico.

Limiti dichiarati (v1, decisioni di design della release 0.19.0):
- bin di default 1.0 s, tolleranza confini 3.0 s, soglia di copertura 0.5;
- proiezione famiglia solo dai top-3 PANNs per segmento con score >= 0.05;
- le tassonomie non-sorgente NON vengono forzate su Krause, per non
  fabbricare un accordo che non ha senso teorico.
"""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from . import config
from .load_annotation import AnnotationProject
from .version import skill_version

# Proiezione dei termId Krause dell'Atelier sulle famiglie usate dalla skill.
# Gli altri termini della tassonomia Krause (es. nicchia acustica) non sono
# famiglie di sorgente e restano fuori dal confronto quantitativo.
KRAUSE_TERM_TO_FAMILY = {
    "krause.biophony": "biofonia",
    "krause.anthrophony": "antropofonia",
    "krause.geophony": "geofonia",
}

FAMILIES = ("biofonia", "antropofonia", "geofonia")

# Sotto questo score il top-k PANNs non concorre alla proiezione di famiglia:
# a punteggi minori la label è rumore di fondo del classificatore.
PANNS_FAMILY_MIN_SCORE = 0.05

DEFAULT_BIN_S = 1.0
DEFAULT_TOLERANCE_S = 3.0
DEFAULT_MIN_OVERLAP = 0.5


# ---------------------------------------------------------------------------
# Primitive
# ---------------------------------------------------------------------------

def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    """Durata dell'intersezione fra due intervalli (0 se disgiunti)."""
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def cohen_kappa(rater_a: list[str], rater_b: list[str]) -> Optional[float]:
    """Cohen's kappa fra due sequenze di etichette della stessa lunghezza.

    Ritorna None se le sequenze sono vuote o se l'accordo atteso è 1
    (caso degenere, entrambe le distribuzioni concentrate sulla stessa
    classe: kappa non definito).
    """
    if not rater_a or len(rater_a) != len(rater_b):
        return None
    n = len(rater_a)
    observed = sum(1 for a, b in zip(rater_a, rater_b) if a == b) / n
    count_a = Counter(rater_a)
    count_b = Counter(rater_b)
    expected = sum(
        (count_a.get(c, 0) / n) * (count_b.get(c, 0) / n)
        for c in set(count_a) | set(count_b)
    )
    if math.isclose(expected, 1.0):
        return None
    return (observed - expected) / (1.0 - expected)


def _segment_families(top: list[dict]) -> set[str]:
    """Famiglie Krause proiettate dai top-k PANNs di un segmento timeline."""
    fams: set[str] = set()
    for entry in top or []:
        if float(entry.get("score") or 0.0) < PANNS_FAMILY_MIN_SCORE:
            continue
        fam = config.PANNS_LABEL_TO_KRAUSE.get(entry.get("name") or "")
        if fam in FAMILIES:
            fams.add(fam)
    return fams


def _segment_dominant_family(top: list[dict]) -> str:
    """Famiglia del primo label proiettabile (in ordine di score), o 'mista'."""
    for entry in top or []:
        if float(entry.get("score") or 0.0) < PANNS_FAMILY_MIN_SCORE:
            continue
        fam = config.PANNS_LABEL_TO_KRAUSE.get(entry.get("name") or "")
        if fam in FAMILIES:
            return fam
    return "mista"


# ---------------------------------------------------------------------------
# Assi di confronto
# ---------------------------------------------------------------------------

def boundary_agreement(
    human_bounds: list[float],
    machine_bounds: list[float],
    tolerance_s: float = DEFAULT_TOLERANCE_S,
) -> dict:
    """Accordo sui punti di taglio interni, con matching greedy 1-a-1.

    precision = tagli macchina confermati da un taglio umano entro tolleranza;
    recall = tagli umani ritrovati dalla macchina. Convenzione MIREX-like.
    """
    human = sorted(human_bounds)
    machine = sorted(machine_bounds)
    matched_machine: set[int] = set()
    matched_human: set[int] = set()
    for hi, h in enumerate(human):
        best_j, best_d = None, None
        for mj, m in enumerate(machine):
            if mj in matched_machine:
                continue
            d = abs(h - m)
            if d <= tolerance_s and (best_d is None or d < best_d):
                best_j, best_d = mj, d
        if best_j is not None:
            matched_machine.add(best_j)
            matched_human.add(hi)
    precision = len(matched_machine) / len(machine) if machine else None
    recall = len(matched_human) / len(human) if human else None
    f1 = None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "n_human": len(human),
        "n_machine": len(machine),
        "n_matched": len(matched_human),
        "tolerance_s": tolerance_s,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _internal_cuts(intervals: list[tuple[float, float]], duration: float,
                   edge_eps: float = 0.5) -> list[float]:
    """Punti di taglio interni da una lista di intervalli (start, end).

    Esclude i punti a ridosso di 0 e della durata totale (non sono scelte
    segmentative) e collassa i duplicati piu' vicini di edge_eps.
    """
    points: list[float] = []
    for start, end in intervals:
        for p in (start, end):
            if p <= edge_eps or p >= duration - edge_eps:
                continue
            if not any(abs(p - q) < edge_eps for q in points):
                points.append(p)
    return sorted(points)


def krause_bin_agreement(
    project: AnnotationProject,
    timeline: list[dict],
    duration: float,
    bin_size: float = DEFAULT_BIN_S,
) -> Optional[dict]:
    """Accordo per bin fra annotazioni Krause umane e famiglie PANNs.

    Considera solo i bin dove l'umano ha almeno un'annotazione di famiglia
    Krause e la timeline macchina copre il bin. Ritorna None se non esistono
    bin confrontabili (nessuna annotazione Krause o timeline assente).
    """
    family_anns = [
        a for a in project.annotations
        if a.taxonomy == "krause" and a.term_id in KRAUSE_TERM_TO_FAMILY
    ]
    if not family_anns or not timeline or duration <= 0:
        return None

    n_bins = max(1, int(math.ceil(duration / bin_size)))
    human_dom: list[str] = []
    machine_dom: list[str] = []
    n_hits = 0
    n_confrontabili = 0

    for i in range(n_bins):
        b_start = i * bin_size
        b_end = min(duration, b_start + bin_size)

        # Lato umano: famiglie presenti nel bin, dominante per copertura.
        cover: dict[str, float] = {}
        for a in family_anns:
            ov = _overlap(a.start_sec, a.end_sec, b_start, b_end)
            if ov > 0:
                fam = KRAUSE_TERM_TO_FAMILY[a.term_id]
                cover[fam] = cover.get(fam, 0.0) + ov
        if not cover:
            continue

        # Lato macchina: segmento timeline che copre il centro del bin.
        center = (b_start + b_end) / 2.0
        seg = next(
            (s for s in timeline
             if float(s.get("t_start_s", 0)) <= center < float(s.get("t_end_s", 0))),
            None,
        )
        if seg is None:
            continue

        n_confrontabili += 1
        human_families = set(cover)
        machine_families = _segment_families(seg.get("top") or [])
        if human_families & machine_families:
            n_hits += 1
        human_dom.append(max(cover.items(), key=lambda kv: kv[1])[0])
        machine_dom.append(_segment_dominant_family(seg.get("top") or []))

    if n_confrontabili == 0:
        return None
    return {
        "bin_size_s": bin_size,
        "n_bins_confrontabili": n_confrontabili,
        "percent_agreement": n_hits / n_confrontabili,
        "kappa": cohen_kappa(human_dom, machine_dom),
        "classi": sorted(set(human_dom) | set(machine_dom)),
    }


def annotation_coverage(
    project: AnnotationProject,
    timeline: list[dict],
    machine_sections: list[dict],
    min_overlap: float = DEFAULT_MIN_OVERLAP,
) -> dict:
    """Copertura per annotazione.

    Annotazioni Krause di famiglia: frazione temporale coperta da segmenti
    timeline concordi sulla famiglia, con verdetto sopra soglia. Altre
    tassonomie: confronto descrittivo con la sezione macchina di massimo
    overlap (id + signature), senza verdetto.
    """
    per_annotation: list[dict] = []
    n_family = 0
    n_covered = 0

    for a in sorted(project.annotations, key=lambda x: x.start_sec):
        dur = max(1e-9, a.end_sec - a.start_sec)
        entry: dict[str, Any] = {
            "id": a.id,
            "start_sec": a.start_sec,
            "end_sec": a.end_sec,
            "taxonomy": a.taxonomy,
            "term_id": a.term_id,
            "term_label": a.term_label,
        }
        fam = KRAUSE_TERM_TO_FAMILY.get(a.term_id) if a.taxonomy == "krause" else None
        if fam:
            n_family += 1
            covered = 0.0
            for seg in timeline or []:
                ov = _overlap(a.start_sec, a.end_sec,
                              float(seg.get("t_start_s", 0)),
                              float(seg.get("t_end_s", 0)))
                if ov > 0 and fam in _segment_families(seg.get("top") or []):
                    covered += ov
            fraction = min(1.0, covered / dur)
            verdict = fraction >= min_overlap
            n_covered += 1 if verdict else 0
            entry.update({
                "family": fam,
                "covered_fraction": round(fraction, 3),
                "machine_agrees": verdict,
            })
        else:
            best, best_ov = None, 0.0
            for sec in machine_sections or []:
                ov = _overlap(a.start_sec, a.end_sec,
                              float(sec.get("t_start_s", 0)),
                              float(sec.get("t_end_s", 0)))
                if ov > best_ov:
                    best, best_ov = sec, ov
            entry.update({
                "descriptive_only": True,
                "machine_section": (best or {}).get("id"),
                "machine_signature": (best or {}).get("signature_label"),
                "machine_krause": (best or {}).get("krause"),
            })
        per_annotation.append(entry)

    return {
        "min_overlap": min_overlap,
        "n_annotations": len(per_annotation),
        "n_family": n_family,
        "n_family_covered": n_covered,
        "family_recall": (n_covered / n_family) if n_family else None,
        "per_annotation": per_annotation,
    }


# ---------------------------------------------------------------------------
# Orchestrazione
# ---------------------------------------------------------------------------

def compare(
    project: AnnotationProject,
    summary: dict,
    bin_size: float = DEFAULT_BIN_S,
    tolerance_s: float = DEFAULT_TOLERANCE_S,
    min_overlap: float = DEFAULT_MIN_OVERLAP,
) -> dict:
    """Confronto completo annotazione umana vs summary della skill."""
    notes: list[str] = []
    duration = float(project.audio.duration_seconds or 0.0)
    meta = summary.get("metadata") or {}
    summary_dur = float(meta.get("duration_s") or 0.0)
    if duration <= 0:
        duration = summary_dur
    if summary_dur and abs(summary_dur - duration) > 1.0:
        notes.append(
            f"Durate divergenti fra annotazione ({duration:.1f} s) e summary "
            f"({summary_dur:.1f} s): verificare che i file coincidano."
        )

    classifier = ((summary.get("semantic") or {}).get("classifier")
                  or (summary.get("semantic") or {}).get("yamnet") or {})
    timeline = classifier.get("timeline") or []
    if not timeline:
        notes.append(
            "Timeline PANNs assente nel summary (semantica disattivata?): "
            "gli assi di famiglia Krause non sono calcolabili."
        )
    machine_sections = ((summary.get("structure") or {}).get("sections")) or []

    # Asse 1: confini strutturali (solo se entrambe le parti hanno sezioni).
    boundary = None
    human_struct = [(s.start_sec, s.end_sec) for s in project.structure]
    if human_struct and machine_sections and duration > 0:
        human_cuts = _internal_cuts(human_struct, duration)
        machine_cuts = _internal_cuts(
            [(float(s.get("t_start_s", 0)), float(s.get("t_end_s", 0)))
             for s in machine_sections],
            duration,
        )
        boundary = boundary_agreement(human_cuts, machine_cuts, tolerance_s)
    elif not human_struct:
        notes.append("Nessuna sezione strutturale umana: asse confini saltato.")

    # Asse 2: accordo per bin sulla famiglia Krause.
    krause_bins = krause_bin_agreement(project, timeline, duration, bin_size)
    if krause_bins is None:
        notes.append(
            "Nessun bin confrontabile sulla famiglia Krause (servono "
            "annotazioni krause.biophony/anthrophony/geophony e la timeline PANNs)."
        )

    # Asse 3: copertura per annotazione.
    coverage = annotation_coverage(project, timeline, machine_sections, min_overlap)

    return {
        "version": skill_version(),
        "audio": {
            "filename": project.audio.filename,
            "duration_s": duration,
        },
        "annotator": project.metadata.annotator,
        "params": {
            "bin_size_s": bin_size,
            "tolerance_s": tolerance_s,
            "min_overlap": min_overlap,
            "panns_family_min_score": PANNS_FAMILY_MIN_SCORE,
        },
        "counts": {
            "annotations": len(project.annotations),
            "annotations_krause_family": coverage["n_family"],
            "structure_human": len(project.structure),
            "sections_machine": len(machine_sections),
        },
        "boundary": boundary,
        "krause_bins": krause_bins,
        "coverage": coverage,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Rese (markdown + PDF)
# ---------------------------------------------------------------------------

def _fmt_ratio(v: Optional[float]) -> str:
    return "n.d." if v is None else f"{v:.3f}"


def render_markdown(result: dict) -> str:
    """Report markdown compatto del confronto (per lettura e per il paper)."""
    audio = result.get("audio") or {}
    params = result.get("params") or {}
    counts = result.get("counts") or {}
    lines: list[str] = []
    lines.append("# Confronto annotazione umana vs analisi skill")
    lines.append("")
    lines.append(f"- File audio - `{audio.get('filename', 'n.d.')}` "
                 f"({float(audio.get('duration_s') or 0):.1f} s)")
    if result.get("annotator"):
        lines.append(f"- Annotatore - {result['annotator']}")
    lines.append(f"- Skill v{result.get('version', 'n.d.')}, bin {params.get('bin_size_s')} s, "
                 f"tolleranza confini {params.get('tolerance_s')} s, "
                 f"soglia copertura {params.get('min_overlap')}")
    lines.append(f"- Annotazioni {counts.get('annotations', 0)} "
                 f"(di famiglia Krause {counts.get('annotations_krause_family', 0)}), "
                 f"sezioni umane {counts.get('structure_human', 0)}, "
                 f"sezioni macchina {counts.get('sections_machine', 0)}")
    lines.append("")

    boundary = result.get("boundary")
    lines.append("## Confini strutturali")
    lines.append("")
    if boundary:
        lines.append(f"- Tagli umani {boundary['n_human']}, tagli macchina "
                     f"{boundary['n_machine']}, accoppiati {boundary['n_matched']} "
                     f"(tolleranza {boundary['tolerance_s']} s)")
        lines.append(f"- Precision {_fmt_ratio(boundary['precision'])}, "
                     f"recall {_fmt_ratio(boundary['recall'])}, "
                     f"F1 {_fmt_ratio(boundary['f1'])}")
    else:
        lines.append("- Non calcolabile (sezioni mancanti da uno dei due lati).")
    lines.append("")

    kb = result.get("krause_bins")
    lines.append("## Famiglia Krause per bin")
    lines.append("")
    if kb:
        kappa = kb.get("kappa")
        lines.append(f"- Bin confrontabili {kb['n_bins_confrontabili']} "
                     f"(bin {kb['bin_size_s']} s)")
        lines.append(f"- Percent agreement {_fmt_ratio(kb['percent_agreement'])}")
        lines.append(f"- Cohen's kappa {_fmt_ratio(kappa)} "
                     f"(classi {', '.join(kb.get('classi') or [])})")
    else:
        lines.append("- Non calcolabile (nessun bin confrontabile).")
    lines.append("")

    cov = result.get("coverage") or {}
    lines.append("## Copertura per annotazione")
    lines.append("")
    fr = cov.get("family_recall")
    if cov.get("n_family"):
        lines.append(f"- Annotazioni Krause coperte dalla macchina "
                     f"{cov.get('n_family_covered', 0)}/{cov.get('n_family', 0)} "
                     f"(recall {_fmt_ratio(fr)}, soglia {cov.get('min_overlap')})")
    lines.append("")
    lines.append("| Intervallo | Tassonomia | Termine | Esito |")
    lines.append("|---|---|---|---|")
    for e in cov.get("per_annotation") or []:
        interval = f"{e['start_sec']:.1f}-{e['end_sec']:.1f} s"
        if e.get("descriptive_only"):
            sig = e.get("machine_signature") or "nessuna sezione"
            esito = f"descrittivo, sezione {e.get('machine_section') or '-'} ({sig})"
        else:
            esito = (f"famiglia {e.get('family')}, copertura "
                     f"{e.get('covered_fraction'):.0%}, "
                     f"{'concorde' if e.get('machine_agrees') else 'non concorde'}")
        lines.append(f"| {interval} | {e['taxonomy']} | {e['term_label']} | {esito} |")
    lines.append("")

    notes = result.get("notes") or []
    if notes:
        lines.append("## Note e limiti")
        lines.append("")
        for n in notes:
            lines.append(f"- {n}")
        lines.append("")
    lines.append(
        "Le tassonomie non-sorgente (Schaeffer, Smalley, Chion, Truax, "
        "Westerkamp, Wishart, Schafer) non hanno proiezione onesta sulle "
        "etichette AudioSet, quindi restano descrittive per scelta di design."
    )
    return "\n".join(lines) + "\n"


def build_compare_pdf(result: dict, output_path: Path) -> Path:
    """PDF compatto del confronto, con lo stile tipografico della skill."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    from . import report_styles
    from .report_pdf import _esc

    fonts = report_styles.register_fonts()
    styles = report_styles.build_styles(fonts)

    audio = result.get("audio") or {}
    counts = result.get("counts") or {}
    story: list = []
    story.append(Paragraph("Confronto annotazione umana vs analisi skill", styles["h1"]))
    story.append(Paragraph(
        f"File <b>{_esc(audio.get('filename', 'n.d.'))}</b> "
        f"({float(audio.get('duration_s') or 0):.1f} s). "
        f"Annotazioni {counts.get('annotations', 0)}, sezioni umane "
        f"{counts.get('structure_human', 0)}, sezioni macchina "
        f"{counts.get('sections_machine', 0)}. Skill v{result.get('version', 'n.d.')}.",
        styles["body"],
    ))
    story.append(Spacer(1, 6))

    rows = [["Asse", "Metrica", "Valore"]]
    boundary = result.get("boundary")
    if boundary:
        rows.append(["Confini strutturali", "Precision",
                     _fmt_ratio(boundary["precision"])])
        rows.append(["", "Recall", _fmt_ratio(boundary["recall"])])
        rows.append(["", "F1", _fmt_ratio(boundary["f1"])])
    kb = result.get("krause_bins")
    if kb:
        rows.append(["Famiglia Krause per bin", "Percent agreement",
                     _fmt_ratio(kb["percent_agreement"])])
        rows.append(["", "Cohen's kappa", _fmt_ratio(kb.get("kappa"))])
        rows.append(["", "Bin confrontabili", str(kb["n_bins_confrontabili"])])
    cov = result.get("coverage") or {}
    if cov.get("n_family"):
        rows.append(["Copertura annotazioni Krause", "Recall",
                     _fmt_ratio(cov.get("family_recall"))])
    if len(rows) > 1:
        story.append(report_styles.styled_table(
            rows, [62 * mm, 52 * mm, 40 * mm], styles))
        story.append(Spacer(1, 8))

    per_ann = (cov.get("per_annotation") or [])[:40]
    if per_ann:
        story.append(Paragraph("<b>Dettaglio per annotazione</b>", styles["body"]))
        rows = [["Intervallo", "Tassonomia", "Termine", "Esito"]]
        for e in per_ann:
            interval = f"{e['start_sec']:.1f}-{e['end_sec']:.1f} s"
            if e.get("descriptive_only"):
                esito = (f"descrittivo, sezione {e.get('machine_section') or '-'} "
                         f"({_esc(e.get('machine_signature') or 'n.d.')})")
            else:
                esito = (f"{e.get('family')}, copertura "
                         f"{e.get('covered_fraction'):.0%}, "
                         f"{'concorde' if e.get('machine_agrees') else 'non concorde'}")
            rows.append([interval, e["taxonomy"], _esc(e["term_label"]), esito])
        story.append(report_styles.styled_table(
            rows, [26 * mm, 24 * mm, 44 * mm, 60 * mm], styles))
        n_tot = len(cov.get("per_annotation") or [])
        if n_tot > 40:
            story.append(Paragraph(
                f"<i>Mostrate le prime 40 annotazioni su {n_tot}; elenco "
                f"completo nel JSON del confronto.</i>", styles["caption"]))
        story.append(Spacer(1, 6))

    for n in result.get("notes") or []:
        story.append(Paragraph(f"<i>{_esc(n)}</i>", styles["caption"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<i>Le tassonomie non-sorgente restano descrittive per scelta di "
        "design; il confronto quantitativo copre la famiglia Krause e i "
        "confini strutturali.</i>", styles["caption"]))

    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                            title="Confronto annotazione vs skill",
                            author="Francesco Mariano")
    doc.build(story)
    return output_path
