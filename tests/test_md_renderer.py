"""Test del renderer markdown → ReportLab (v0.3.1)."""
import pytest
from reportlab.platypus import Paragraph, Table, Preformatted
from reportlab.platypus.flowables import HRFlowable

from tests.conftest import ensure_fixtures  # noqa
from scripts.md_renderer import render_markdown
from scripts.report_styles import register_fonts, build_styles


@pytest.fixture(scope="module")
def styles():
    fonts = register_fonts()
    return build_styles(fonts)


def test_empty_markdown(styles):
    assert render_markdown("", styles) == []
    assert render_markdown("   \n", styles) == []


def test_heading_levels(styles):
    md = "# Primo\n\n## Secondo\n\n### Terzo"
    out = render_markdown(md, styles)
    # Tre Paragraph, uno per heading
    paragraphs = [x for x in out if isinstance(x, Paragraph)]
    assert len(paragraphs) == 3


def test_paragraph_with_inline_bold_italic(styles):
    md = "Questo è **grassetto** e *italico*."
    out = render_markdown(md, styles)
    para = next(x for x in out if isinstance(x, Paragraph))
    html = para.text
    assert "<b>grassetto</b>" in html
    assert "<i>italico</i>" in html


def test_inline_code(styles):
    md = "Questo ha `codice inline`."
    out = render_markdown(md, styles)
    para = next(x for x in out if isinstance(x, Paragraph))
    assert "Courier" in para.text


def test_unordered_list(styles):
    md = "- item uno\n- item due\n- item tre"
    out = render_markdown(md, styles)
    paragraphs = [x for x in out if isinstance(x, Paragraph)]
    assert len(paragraphs) == 3
    assert "•" in paragraphs[0].text


def test_ordered_list(styles):
    md = "1. primo\n2. secondo\n3. terzo"
    out = render_markdown(md, styles)
    paragraphs = [x for x in out if isinstance(x, Paragraph)]
    assert len(paragraphs) == 3
    assert "1." in paragraphs[0].text
    assert "2." in paragraphs[1].text


def test_table_gfm_basic(styles):
    md = """| Col A | Col B | Col C |
|-------|-------|-------|
| 1     | a     | X     |
| 2     | b     | Y     |
| 3     | c     | Z     |
"""
    out = render_markdown(md, styles)
    # Deve esserci esattamente una Table
    tables = [x for x in out if isinstance(x, Table)]
    assert len(tables) == 1
    t = tables[0]
    # 4 righe (header + 3 body), 3 colonne
    assert len(t._cellvalues) == 4
    assert len(t._cellvalues[0]) == 3


def test_table_with_alignment(styles):
    md = """| Sinistra | Centro | Destra |
|:---------|:------:|-------:|
| uno      | due    | tre    |
| quattro  | cinque | sei    |
"""
    out = render_markdown(md, styles)
    tables = [x for x in out if isinstance(x, Table)]
    assert len(tables) == 1
    # Il test verifica solo che la tabella sia creata, l'allineamento è nello stile
    t = tables[0]
    assert len(t._cellvalues) == 3  # header + 2 body


def test_blockquote(styles):
    md = "> Una citazione che occupa più righe,\n> distribuite su due linee."
    out = render_markdown(md, styles)
    paragraphs = [x for x in out if isinstance(x, Paragraph)]
    assert len(paragraphs) >= 1


def test_code_fence(styles):
    md = "```\nfoo = 1\nbar = 2\n```"
    out = render_markdown(md, styles)
    pre = [x for x in out if isinstance(x, Preformatted)]
    assert len(pre) == 1


def test_thematic_break(styles):
    md = "prima\n\n---\n\ndopo"
    out = render_markdown(md, styles)
    hrs = [x for x in out if isinstance(x, HRFlowable)]
    assert len(hrs) == 1


def test_mixed_document_with_table(styles):
    """Documento realistico: titolo, paragrafo, tabella, conclusione."""
    md = """# Report comparativo

Questo è un paragrafo introduttivo che descrive il corpus.

## Panoramica

| File | LUFS | Centroide |
|------|-----:|----------:|
| a.wav | -20.0 | 1200 |
| b.wav | -23.5 | 2100 |
| c.wav | -18.2 | 1850 |

Osservazione: **il secondo file** è quello con centroide più alto.
"""
    out = render_markdown(md, styles)
    # Heading + paragraph + heading + table + paragraph = 5 elementi
    types = [type(x).__name__ for x in out]
    assert "Table" in types
    assert types.count("Paragraph") >= 3
