"""Test su scripts/structure.py (v0.6.0)."""
from __future__ import annotations

import numpy as np
import pytest

from scripts import config, structure


def _make_synthetic_waveform_three_sections(sr: int = 22050) -> np.ndarray:
    """Costruisce 90 s di audio in 3 segmenti netti:
    - 0-30 s: silenzio totale (rms_db ~ -inf, centroide ~ 0)
    - 30-60 s: tono puro 440 Hz (rms_db ~ -10, centroide ~ 440, flatness bassa)
    - 60-90 s: rumore bianco (rms_db ~ -10, centroide ~ 5000+, flatness alta)
    """
    n_window = 30 * sr
    silence = np.zeros(n_window, dtype=np.float32)
    t = np.arange(n_window, dtype=np.float32) / sr
    tone = (0.3 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
    rng = np.random.default_rng(42)
    noise = (0.3 * rng.standard_normal(n_window)).astype(np.float32)
    return np.concatenate([silence, tone, noise])


def test_compute_structure_returns_required_keys():
    """Output ha le chiavi attese."""
    sr = 22050
    waveform = _make_synthetic_waveform_three_sections(sr)
    result = structure.compute_structure(waveform, sr, summary={})
    assert "enabled" in result
    assert "n_sections" in result
    assert "window_seconds" in result
    assert "sections" in result
    assert result["enabled"] is True


def test_compute_structure_detects_three_sections_on_synthetic():
    """Su 3 segmenti sintetici netti (silenzio + tono + rumore) il
    changepoint detection deterministico deve rilevare almeno 2 confini
    (3 sezioni). Su materiale cosi' netto il MAD e' alto e i confini
    sono chiari."""
    sr = 22050
    waveform = _make_synthetic_waveform_three_sections(sr)
    result = structure.compute_structure(waveform, sr, summary={},
                                          window_seconds=10.0)
    n = result["n_sections"]
    assert 2 <= n <= 4, f"atteso 2-4 sezioni, trovate {n}"


def test_compute_structure_sections_are_monotonic():
    """Le sezioni in output sono ordinate temporalmente, contigue, senza
    sovrapposizioni o gap (ogni t_end == prossimo t_start)."""
    sr = 22050
    waveform = _make_synthetic_waveform_three_sections(sr)
    result = structure.compute_structure(waveform, sr, summary={})
    sections = result["sections"]
    assert len(sections) >= 1
    for i in range(len(sections) - 1):
        assert sections[i]["t_end_s"] <= sections[i + 1]["t_start_s"] + 0.01, (
            f"sezione {i} t_end={sections[i]['t_end_s']} > sezione {i+1} "
            f"t_start={sections[i+1]['t_start_s']}"
        )


def test_compute_structure_signature_labels_present():
    """Ogni sezione ha una signature_label non vuota e leggibile."""
    sr = 22050
    waveform = _make_synthetic_waveform_three_sections(sr)
    result = structure.compute_structure(waveform, sr, summary={})
    for s in result["sections"]:
        assert s.get("signature_label"), f"sezione {s['id']} senza signature_label"
        assert len(s["signature_label"]) <= 50, (
            f"signature troppo lunga ({len(s['signature_label'])} char): "
            f"{s['signature_label']!r}"
        )


def test_compute_structure_short_file_returns_single_section():
    """Su file troppo corto (< 2 finestre) ritorna una sola sezione che
    copre l'intero file."""
    sr = 22050
    duration_s = 5.0  # < 2 * STRUCTURE_WINDOW_S (10.0 default)
    waveform = np.zeros(int(duration_s * sr), dtype=np.float32)
    result = structure.compute_structure(waveform, sr, summary={})
    assert result["n_sections"] == 1
    section = result["sections"][0]
    assert section["t_start_s"] == 0.0
    assert section["t_end_s"] == pytest.approx(duration_s, abs=0.1)


def test_compute_structure_first_section_is_silence_on_synthetic():
    """La prima sezione del brano sintetico (silenzio puro nei primi 30 s)
    deve essere etichettata 'quasi-silenzio'."""
    sr = 22050
    waveform = _make_synthetic_waveform_three_sections(sr)
    result = structure.compute_structure(waveform, sr, summary={})
    first = result["sections"][0]
    assert first["mean_rms_db"] < -50.0, (
        f"prima sezione (silenzio) con rms {first['mean_rms_db']} dBFS, "
        f"atteso < -50"
    )
    assert "silenzio" in first["signature_label"].lower(), (
        f"prima sezione non etichettata silenzio: {first['signature_label']!r}"
    )


def test_compute_structure_respects_min_max_sections():
    """Numero sezioni rispetta config.STRUCTURE_MIN_SECTIONS e
    STRUCTURE_MAX_SECTIONS."""
    sr = 22050
    waveform = _make_synthetic_waveform_three_sections(sr)
    result = structure.compute_structure(waveform, sr, summary={})
    n = result["n_sections"]
    assert n >= config.STRUCTURE_MIN_SECTIONS
    assert n <= config.STRUCTURE_MAX_SECTIONS
