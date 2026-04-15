"""Test del modulo report_synthesizer (v0.3.1).

Verifica `_strip_preamble` che rimuove righe prima del primo H1. I test
sull'invocazione subprocess `claude` non sono inclusi perché richiederebbero
un binario claude disponibile o un mock pesante.
"""
import pytest
from scripts.report_synthesizer import _strip_preamble


def test_strip_preamble_with_preamble():
    text = (
        "Ho tutti i dati necessari. Procedo con il report.\n"
        "\n"
        "# Titolo\n"
        "\n"
        "Contenuto del primo paragrafo."
    )
    result = _strip_preamble(text)
    assert result.startswith("# Titolo")
    assert "Ho tutti i dati" not in result
    assert "Contenuto del primo paragrafo" in result


def test_strip_preamble_without_preamble():
    text = "# Titolo diretto\n\nContenuto."
    result = _strip_preamble(text)
    assert result == "# Titolo diretto\n\nContenuto."


def test_strip_preamble_with_leading_whitespace_then_h1():
    text = "\n\n   \n# Titolo\n\nX"
    result = _strip_preamble(text)
    assert result.startswith("# Titolo")


def test_strip_preamble_no_h1_returns_text():
    """Se non c'è H1, la funzione non deve rimuovere contenuto."""
    text = "Solo paragrafi.\n\n## Solo H2\n\nAltro."
    result = _strip_preamble(text)
    assert "Solo paragrafi" in result
    assert "## Solo H2" in result


def test_strip_preamble_empty():
    assert _strip_preamble("") == ""
    assert _strip_preamble(None) is None


def test_strip_preamble_preserves_everything_after_h1():
    text = (
        "Preamble\n"
        "Altra riga di preambolo\n"
        "# Titolo\n"
        "\n"
        "## Sottosezione\n"
        "\n"
        "Paragrafo con **bold** e *italic*.\n"
        "\n"
        "- item 1\n"
        "- item 2\n"
    )
    result = _strip_preamble(text)
    assert result.startswith("# Titolo")
    assert "## Sottosezione" in result
    assert "**bold**" in result
    assert "item 1" in result
    assert "Preamble" not in result
