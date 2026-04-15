"""Renderer markdown → flowable ReportLab (v0.3.1).

Sostituisce il precedente `_markdown_to_story` di report_pdf.py con un
parser markdown robusto basato su mistune 3.x. Differenza chiave:
**gestisce le tabelle GFM rendendole come `Table` ReportLab vere** invece
di stampare il testo letterale con pipe e trattini (bug v0.3.0).

La regola tipografica della CLAUDE.md (v. "Regola sulla tipografia dei
documenti generati", punto 6) vieta di pubblicare documenti con artefatti
di rendering visibili. Questo modulo risolve il punto.
"""
from __future__ import annotations
import re
from typing import Any
import mistune
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, Preformatted, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable

from . import config


_PARSER = mistune.create_markdown(
    renderer=None,
    plugins=["table", "strikethrough"],
)


def render_markdown(md: str, styles: dict) -> list:
    """Converte testo markdown in una lista di flowable ReportLab.

    Args:
        md: sorgente markdown (GFM + strikethrough).
        styles: dict di ParagraphStyle restituito da
            `report_styles.build_styles`.

    Returns:
        Lista di flowable pronti per `doc.build(story)`.
    """
    if not md or not md.strip():
        return []
    tokens = _PARSER(md)
    return _render_tokens(tokens, styles)


# ---------- Dispatch block-level ----------

def _render_tokens(tokens: list[dict], styles: dict) -> list:
    story: list = []
    for tok in tokens:
        ttype = tok.get("type")
        if ttype == "blank_line":
            continue
        handler = _BLOCK_HANDLERS.get(ttype)
        if handler is None:
            # Fallback: emetti il raw come paragrafo
            raw = tok.get("raw", "")
            if raw:
                story.append(Paragraph(_escape(raw), styles["body"]))
            continue
        result = handler(tok, styles)
        if result is None:
            continue
        if isinstance(result, list):
            story.extend(result)
        else:
            story.append(result)
    return story


def _render_heading(tok: dict, styles: dict):
    level = (tok.get("attrs") or {}).get("level", 1)
    text = _render_inline(tok.get("children", []))
    key = f"h{min(level, 3)}" if level <= 3 else "h3"
    style = styles.get(key) or styles["body"]
    return Paragraph(text, style)


def _render_paragraph(tok: dict, styles: dict):
    text = _render_inline(tok.get("children", []))
    return Paragraph(text, styles["body"])


def _render_block_text(tok: dict, styles: dict):
    # usato dentro list_item
    text = _render_inline(tok.get("children", []))
    return Paragraph(text, styles["body"])


def _render_list(tok: dict, styles: dict):
    items: list = []
    ordered = (tok.get("attrs") or {}).get("ordered", False)
    for idx, child in enumerate(tok.get("children", []), 1):
        if child.get("type") != "list_item":
            continue
        marker = f"{idx}." if ordered else "•"
        items.extend(_render_list_item(child, styles, marker))
    return items


def _render_list_item(tok: dict, styles: dict, marker: str) -> list:
    out: list = []
    # Il list_item contiene figli che possono essere block_text o paragraph
    # o anche sottoliste annidate.
    children = tok.get("children", [])
    first_text_emitted = False
    for sub in children:
        stype = sub.get("type")
        if stype in ("block_text", "paragraph"):
            text = _render_inline(sub.get("children", []))
            if not first_text_emitted:
                out.append(Paragraph(f"{marker} {text}", styles["body"]))
                first_text_emitted = True
            else:
                # Paragrafi aggiuntivi nello stesso item: indenta senza marker
                out.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{text}", styles["body"]))
        elif stype == "list":
            # Sottolista: rendila inset
            sub_items = _render_list(sub, styles)
            # Semplice indentazione prefissa con spazi
            for it in sub_items:
                if isinstance(it, Paragraph):
                    it.style = styles["body"]
                out.append(it)
        else:
            # fallback
            handler = _BLOCK_HANDLERS.get(stype)
            if handler:
                res = handler(sub, styles)
                if isinstance(res, list):
                    out.extend(res)
                elif res is not None:
                    out.append(res)
    return out


def _render_block_quote(tok: dict, styles: dict):
    # Ogni child è un block (tipicamente paragraph). Li rendiamo con quote_text.
    out: list = []
    for child in tok.get("children", []):
        if child.get("type") == "paragraph":
            text = _render_inline(child.get("children", []))
            out.append(Paragraph(text, styles.get("quote_text", styles["body"])))
        else:
            handler = _BLOCK_HANDLERS.get(child.get("type"))
            if handler:
                res = handler(child, styles)
                if isinstance(res, list):
                    out.extend(res)
                elif res is not None:
                    out.append(res)
    return out


def _render_block_code(tok: dict, styles: dict):
    raw = tok.get("raw", "")
    # Rimuovi trailing newline
    if raw.endswith("\n"):
        raw = raw[:-1]
    pre_style = styles.get("body").clone("pre_tmp") if "body" in styles else None
    if pre_style is not None:
        pre_style.fontName = "Courier"
        pre_style.fontSize = 9
        pre_style.leading = 11
    return Preformatted(raw, pre_style or styles["body"])


def _render_thematic_break(tok: dict, styles: dict):
    return HRFlowable(
        width="100%", thickness=0.5,
        color=HexColor("#1A1A1A"),
        spaceBefore=6, spaceAfter=6,
    )


def _render_table(tok: dict, styles: dict):
    """Costruisce una Table ReportLab a partire dal token mistune.

    Il token table ha children [table_head, table_body]. Ogni row è
    table_row con children table_cell. Gli align possono essere left,
    right, center, None.
    """
    head_rows: list = []
    body_rows: list = []
    alignments: list[str] = []

    for section in tok.get("children", []):
        stype = section.get("type")
        if stype == "table_head":
            # mistune 3.x: table_head ha direttamente table_cell come children,
            # non racchiusi in un table_row.
            cells = section.get("children", [])
            if not alignments:
                alignments = [
                    (c.get("attrs") or {}).get("align") or "left"
                    for c in cells
                ]
            head_rows.append(_render_table_row(
                cells, styles, is_header=True, aligns=alignments
            ))
        elif stype == "table_body":
            for row in section.get("children", []):
                if row.get("type") != "table_row":
                    continue
                cells = row.get("children", [])
                body_rows.append(_render_table_row(
                    cells, styles, is_header=False, aligns=alignments
                ))

    rows = head_rows + body_rows
    if not rows:
        return None

    n_cols = max(len(r) for r in rows)
    # Normalizza righe alla stessa lunghezza
    for r in rows:
        while len(r) < n_cols:
            r.append(Paragraph("", styles["table_cell"]))

    # Col widths proporzionali (spazio utile A4 con margini: ~165mm)
    total_width = 165 * mm
    col_widths = [total_width / n_cols] * n_cols

    tbl = Table(rows, colWidths=col_widths, repeatRows=1 if head_rows else 0)

    # Stile: header scuro bianco, righe alternate beige, border fine
    ts_cmds = [
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, HexColor(config.PALETTE["bg_muted"])),
    ]
    if head_rows:
        ts_cmds.append(("BACKGROUND", (0, 0), (-1, 0), HexColor(config.PALETTE["dark"])))
    # Allineamento colonne
    for col_idx, align in enumerate(alignments[:n_cols]):
        if align == "right":
            ts_cmds.append(("ALIGN", (col_idx, 0), (col_idx, -1), "RIGHT"))
        elif align == "center":
            ts_cmds.append(("ALIGN", (col_idx, 0), (col_idx, -1), "CENTER"))
        else:
            ts_cmds.append(("ALIGN", (col_idx, 0), (col_idx, -1), "LEFT"))
    # Zebra sul body
    start_body = 1 if head_rows else 0
    for r_idx in range(start_body, len(rows)):
        if (r_idx - start_body) % 2 == 1:
            ts_cmds.append(("BACKGROUND", (0, r_idx), (-1, r_idx),
                             HexColor(config.PALETTE["bg_light"])))

    tbl.setStyle(TableStyle(ts_cmds))
    return tbl


def _render_table_row(cells: list[dict], styles: dict, is_header: bool,
                       aligns: list[str]) -> list:
    row: list = []
    cell_style_name = "table_header" if is_header else "table_cell"
    for idx, c in enumerate(cells):
        text = _render_inline(c.get("children", []))
        align = (c.get("attrs") or {}).get("align") or (
            aligns[idx] if idx < len(aligns) else "left"
        )
        # Allineamento via ParagraphStyle clone
        style = styles[cell_style_name].clone(f"cell_{idx}_{id(c)}")
        if align == "right":
            style.alignment = TA_RIGHT
        elif align == "center":
            style.alignment = TA_CENTER
        else:
            style.alignment = TA_LEFT
        row.append(Paragraph(text, style))
    return row


# ---------- Dispatch inline ----------

def _render_inline(children: list[dict]) -> str:
    """Compila inline tokens in una stringa con tag ReportLab markup."""
    parts: list[str] = []
    for tok in children:
        ttype = tok.get("type")
        if ttype == "text":
            parts.append(_escape(tok.get("raw", "")))
        elif ttype == "strong":
            inner = _render_inline(tok.get("children", []))
            parts.append(f"<b>{inner}</b>")
        elif ttype == "emphasis":
            inner = _render_inline(tok.get("children", []))
            parts.append(f"<i>{inner}</i>")
        elif ttype == "codespan":
            raw = _escape(tok.get("raw", ""))
            parts.append(f"<font face='Courier'>{raw}</font>")
        elif ttype == "link":
            url = (tok.get("attrs") or {}).get("url", "")
            inner = _render_inline(tok.get("children", []))
            if url:
                parts.append(f'<link href="{url}" color="#000000"><u>{inner}</u></link>')
            else:
                parts.append(inner)
        elif ttype == "strikethrough":
            inner = _render_inline(tok.get("children", []))
            parts.append(f"<strike>{inner}</strike>")
        elif ttype == "linebreak" or ttype == "softbreak":
            parts.append("<br/>")
        elif ttype == "image":
            # Le immagini inline non le supportiamo qui, emetti alt text
            alt = _escape(tok.get("alt", "") or "immagine")
            parts.append(f"[{alt}]")
        else:
            # Fallback
            parts.append(_escape(tok.get("raw", "")))
    return "".join(parts)


def _escape(text: str) -> str:
    """Escape minimo per ReportLab Paragraph markup."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


_BLOCK_HANDLERS = {
    "heading": _render_heading,
    "paragraph": _render_paragraph,
    "block_text": _render_block_text,
    "list": _render_list,
    "block_quote": _render_block_quote,
    "block_code": _render_block_code,
    "thematic_break": _render_thematic_break,
    "table": _render_table,
}
