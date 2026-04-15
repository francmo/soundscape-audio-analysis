"""Stili ReportLab per PDF stile ABTEC40.

Palette, font registration, costruttori di box, tabelle.
"""
from pathlib import Path
from typing import Callable
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image
)

from . import config
from .locale_it import MESSAGGI_SISTEMA


def register_fonts(assets_dir: Path | None = None) -> dict:
    """Registra Libre Baskerville + Source Sans Pro.

    Fallback: sistema (Baskerville/Helvetica) e infine Helvetica core.
    """
    assets_dir = assets_dir or config.FONTS_DIR
    registrations = {
        "Baskerville": assets_dir / "LibreBaskerville-Regular.ttf",
        "Baskerville-Bold": assets_dir / "LibreBaskerville-Bold.ttf",
        "Baskerville-Italic": assets_dir / "LibreBaskerville-Italic.ttf",
        "SourceSans": assets_dir / "SourceSansPro-Regular.ttf",
        "SourceSans-Bold": assets_dir / "SourceSansPro-Semibold.ttf",
        "SourceSans-Italic": assets_dir / "SourceSansPro-Italic.ttf",
    }
    registered = {}
    any_missing = False
    for name, path in registrations.items():
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(path)))
                registered[name] = str(path)
            except Exception:
                registered[name] = "fallback"
                any_missing = True
        else:
            registered[name] = "fallback"
            any_missing = True

    if any_missing:
        # Fallback ai font core: usiamo Helvetica per tutto per sicurezza unicode
        # nota: Helvetica core ReportLab gestisce latin-1 completo per accenti italiani
        fallback_map = {
            "Baskerville": "Helvetica",
            "Baskerville-Bold": "Helvetica-Bold",
            "Baskerville-Italic": "Helvetica-Oblique",
            "SourceSans": "Helvetica",
            "SourceSans-Bold": "Helvetica-Bold",
            "SourceSans-Italic": "Helvetica-Oblique",
        }
        for k, v in registrations.items():
            if registered.get(k) == "fallback":
                registered[k] = fallback_map[k]

    # Mappa famiglie per comodità
    registered["family_serif"] = "Baskerville" if registered["Baskerville"] != "Helvetica" else "Helvetica"
    registered["family_sans"] = "SourceSans" if registered["SourceSans"] != "Helvetica" else "Helvetica"
    return registered


def build_styles(fonts: dict) -> dict[str, ParagraphStyle]:
    serif = fonts["family_serif"]
    serif_bold = "Baskerville-Bold" if fonts.get("Baskerville-Bold") != "Helvetica-Bold" else "Helvetica-Bold"
    sans = fonts["family_sans"]
    sans_bold = "SourceSans-Bold" if fonts.get("SourceSans-Bold") != "Helvetica-Bold" else "Helvetica-Bold"
    sans_italic = "SourceSans-Italic" if fonts.get("SourceSans-Italic") != "Helvetica-Oblique" else "Helvetica-Oblique"

    PAL = config.PALETTE
    styles = {
        "h1_cover": ParagraphStyle(
            name="h1_cover", fontName=serif_bold, fontSize=32, leading=38,
            textColor=HexColor(PAL["white"]), alignment=TA_LEFT, spaceAfter=10,
        ),
        "h2_cover": ParagraphStyle(
            name="h2_cover", fontName=sans, fontSize=16, leading=22,
            textColor=HexColor(PAL["beige_warm"]), alignment=TA_LEFT, spaceAfter=20,
        ),
        "meta_cover": ParagraphStyle(
            name="meta_cover", fontName=sans, fontSize=11, leading=16,
            textColor=HexColor(PAL["white"]), alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            name="h1", fontName=serif_bold, fontSize=22, leading=28,
            textColor=HexColor(PAL["dark"]), alignment=TA_LEFT, spaceBefore=14, spaceAfter=8,
            borderPadding=3, borderWidth=0, borderColor=HexColor(PAL["terracotta"]),
        ),
        "h2": ParagraphStyle(
            name="h2", fontName=serif_bold, fontSize=16, leading=22,
            textColor=HexColor(PAL["dark"]), alignment=TA_LEFT, spaceBefore=12, spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            name="h3", fontName=sans_bold, fontSize=12, leading=18,
            textColor=HexColor(PAL["terracotta_dk"]), alignment=TA_LEFT, spaceBefore=8, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            name="body", fontName=sans, fontSize=10, leading=14,
            textColor=HexColor("#000000"), alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "body_it": ParagraphStyle(
            name="body_it", fontName=sans_italic, fontSize=10, leading=14,
            textColor=HexColor("#000000"), alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "caption": ParagraphStyle(
            name="caption", fontName=sans_italic, fontSize=8, leading=11,
            textColor=HexColor("#1A1A1A"), alignment=TA_CENTER, spaceAfter=6,
        ),
        "quote_text": ParagraphStyle(
            name="quote_text", fontName=sans_italic, fontSize=11, leading=16,
            textColor=HexColor("#000000"), alignment=TA_JUSTIFY,
            leftIndent=12, rightIndent=12, spaceBefore=6, spaceAfter=3,
        ),
        "quote_attr": ParagraphStyle(
            name="quote_attr", fontName=sans, fontSize=9, leading=12,
            textColor=HexColor("#1A1A1A"), alignment=TA_RIGHT,
            leftIndent=12, rightIndent=12, spaceAfter=10,
        ),
        "box_white": ParagraphStyle(
            name="box_white", fontName=sans, fontSize=10, leading=14,
            textColor=HexColor(PAL["white"]), alignment=TA_LEFT, spaceAfter=6,
        ),
        "box_white_bold": ParagraphStyle(
            name="box_white_bold", fontName=sans_bold, fontSize=11, leading=14,
            textColor=HexColor(PAL["beige_warm"]), alignment=TA_LEFT, spaceAfter=4,
        ),
        "table_cell": ParagraphStyle(
            name="table_cell", fontName=sans, fontSize=9, leading=12,
            textColor=HexColor("#000000"), alignment=TA_LEFT,
        ),
        "table_header": ParagraphStyle(
            name="table_header", fontName=sans_bold, fontSize=9, leading=12,
            textColor=HexColor(PAL["white"]), alignment=TA_LEFT,
        ),
    }
    return styles


def box_quote(text: str, attribution: str, styles: dict) -> KeepTogether:
    """Citazione v0.3.1: sfondo bianco (conforme regola punto 1), barra
    sinistra terracotta come accento motivato (regola punto 2), testo nero.
    """
    PAL = config.PALETTE
    data = [
        [Paragraph(text, styles["quote_text"])],
        [Paragraph(attribution, styles["quote_attr"])] if attribution else [Paragraph("", styles["quote_attr"])],
    ]
    t = Table(data, colWidths=[165 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#FFFFFF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE", (0, 0), (0, -1), 3, HexColor(PAL["terracotta_dk"])),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return KeepTogether(t)


def box_info(title: str, text: str, styles: dict) -> KeepTogether:
    PAL = config.PALETTE
    data = [
        [Paragraph(title, styles["box_white_bold"])],
        [Paragraph(text, styles["box_white"])],
    ]
    t = Table(data, colWidths=[165 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(PAL["dark_mid"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return KeepTogether(t)


def box_accent(title: str, text: str, styles: dict) -> KeepTogether:
    PAL = config.PALETTE
    data = [
        [Paragraph(title, styles["box_white_bold"])],
        [Paragraph(text, styles["box_white"])],
    ]
    t = Table(data, colWidths=[165 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(PAL["terracotta_dk"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return KeepTogether(t)


def box_highlight(title: str, text: str, styles: dict) -> KeepTogether:
    PAL = config.PALETTE
    data = [
        [Paragraph(title, styles["box_white_bold"])],
        [Paragraph(text, styles["box_white"])],
    ]
    t = Table(data, colWidths=[165 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(PAL["teal"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return KeepTogether(t)


def box_neutral(title: str, text: str, styles: dict) -> KeepTogether:
    """Box bianco con border-top terracotta."""
    PAL = config.PALETTE
    data = [
        [Paragraph(title, styles["h3"])],
        [Paragraph(text, styles["body"])],
    ]
    t = Table(data, colWidths=[165 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(PAL["white"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEABOVE", (0, 0), (-1, 0), 2, HexColor(PAL["terracotta"])),
    ]))
    return KeepTogether(t)


def styled_table(data: list[list], col_widths: list[float], styles: dict,
                 header: bool = True) -> Table:
    """Tabella ABTEC40: header DARK bianco, celle padding 10pt, zebra."""
    PAL = config.PALETTE

    def _wrap(v):
        if isinstance(v, str):
            return Paragraph(v, styles["table_cell"])
        return v

    wrapped = []
    for r_idx, row in enumerate(data):
        if header and r_idx == 0:
            wrapped.append([Paragraph(str(c), styles["table_header"]) for c in row])
        else:
            wrapped.append([_wrap(c) for c in row])

    t = Table(wrapped, colWidths=col_widths, repeatRows=1 if header else 0)
    ts = [
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, HexColor(PAL["bg_muted"])),
    ]
    if header:
        ts += [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(PAL["dark"])),
        ]
        for col in range(len(data[0])):
            ts.append(("TEXTCOLOR", (col, 0), (col, 0), HexColor(PAL["white"])))
    # zebra
    for r in range(1 if header else 0, len(data)):
        if (r - (1 if header else 0)) % 2 == 1:
            ts.append(("BACKGROUND", (0, r), (-1, r), HexColor(PAL["bg_light"])))
    t.setStyle(TableStyle(ts))
    return t
