"""Test su scripts/narrative.py (v0.6.0).

Cattura il comportamento atteso DOPO il refactor delta-based:
- Feature timbriche calcolate per finestra, non globali (bug v0.5.x).
- Logica delta-based: finestre senza variazione significativa accumulate
  in plateau, descritte con una sola riga.

I test marcati `@pytest.mark.xfail(reason="prima del Commit 2 v0.6.0...")`
sono espressioni del comportamento atteso post-fix. Quando il refactor
e' applicato, lo `xfail` va rimosso e devono passare.
"""
from __future__ import annotations

import numpy as np
import pytest

from scripts import config, narrative


def _make_synthetic_waveform(sr: int = 22050) -> np.ndarray:
    """Costruisce 90 s di audio eterogeneo: silenzio (30 s) +
    tono puro 440 Hz (30 s) + rumore bianco (30 s).

    Le tre finestre da 30 s devono avere feature timbriche
    significativamente diverse: silenzio (centroide ~0, flatness ~0),
    tono puro (centroide ~440, flatness bassa), rumore bianco
    (centroide medio-alto, flatness alta).
    """
    n_window = 30 * sr
    silence = np.zeros(n_window, dtype=np.float32)
    t = np.arange(n_window, dtype=np.float32) / sr
    tone = (0.3 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
    rng = np.random.default_rng(42)
    noise = (0.3 * rng.standard_normal(n_window)).astype(np.float32)
    return np.concatenate([silence, tone, noise])


def _make_minimal_summary(duration_s: float) -> dict:
    """Summary minimo per `narrative_summary`. Le timeline PANNs/CLAP
    sono vuote: non e' compito di questo test verificare aggregazione
    timeline, solo il calcolo per-finestra delle feature timbriche."""
    return {
        "metadata": {"duration_s": duration_s, "sr": 22050},
        "spectral": {
            "bands_schafer": {
                "Sub-bass": {"energy_pct": 0.05},
                "Bass": {"energy_pct": 0.10},
                "Low-mid": {"energy_pct": 0.15},
                "Mid": {"energy_pct": 0.30},
                "High-mid": {"energy_pct": 0.20},
                "Presence": {"energy_pct": 0.15},
                "Brilliance": {"energy_pct": 0.05},
            },
            "timbre": {
                "spectral_centroid_hz": 1500.0,
                "spectral_flatness": 0.10,
                "spectral_rolloff_hz": 4000.0,
                "zero_crossing_rate": 0.08,
            },
            "onsets": {"events_per_sec": 1.0, "n_events": 90},
        },
        "semantic": {"classifier": {"timeline": []}},
        "clap": {"timeline": []},
    }


def test_config_delta_constants_present():
    """Costanti delta-based v0.6.0 caricate in config."""
    assert hasattr(config, "NARRATIVE_DELTA_CENTROID_PCT")
    assert hasattr(config, "NARRATIVE_DELTA_FLATNESS_PCT")
    assert hasattr(config, "NARRATIVE_DELTA_RMS_DB")
    assert config.NARRATIVE_DELTA_CENTROID_PCT == 0.15
    assert config.NARRATIVE_DELTA_FLATNESS_PCT == 0.30
    assert config.NARRATIVE_DELTA_RMS_DB == 6.0


def test_config_structure_constants_present():
    """Costanti segmentazione strutturale v0.6.0 caricate in config."""
    assert hasattr(config, "STRUCTURE_WINDOW_S")
    assert hasattr(config, "STRUCTURE_MIN_SECTIONS")
    assert hasattr(config, "STRUCTURE_MAX_SECTIONS")
    assert hasattr(config, "STRUCTURE_MIN_SECTION_DURATION_S")
    assert hasattr(config, "STRUCTURE_GRADIENT_THRESHOLD_MAD_K")
    assert hasattr(config, "STRUCTURE_TIMELINE_COLORS")
    assert config.STRUCTURE_WINDOW_S == 10.0
    assert config.STRUCTURE_MIN_SECTIONS >= 1
    assert config.STRUCTURE_MAX_SECTIONS >= config.STRUCTURE_MIN_SECTIONS


def test_narrative_summary_disabled_mode():
    """Mode 'none' ritorna dict {enabled: False}."""
    result = narrative.narrative_summary({}, np.zeros(1000, dtype=np.float32), 22050, mode="none")
    assert result == {"enabled": False, "mode": "none"}


def test_narrative_summary_full_mode_returns_segments():
    """Mode 'full' produce segmenti per ogni finestra di 30 s."""
    sr = 22050
    waveform = _make_synthetic_waveform(sr)
    duration_s = len(waveform) / sr
    summary = _make_minimal_summary(duration_s)
    result = narrative.narrative_summary(summary, waveform, sr, mode="full")
    assert result["enabled"] is True
    assert result["mode"] == "full"
    assert len(result["segments"]) >= 3, f"attesi >=3 segmenti, trovati {len(result['segments'])}"


def _extract_centroid_hz(narrative_text: str) -> int | None:
    """Estrae il valore di centroide stampato dalla narrativa
    (formato `_describe_spectrum`: 'il centroide si colloca a 1500 Hz')."""
    import re
    m = re.search(r"centroide si colloca a (\d+) Hz", narrative_text)
    return int(m.group(1)) if m else None


def test_narrative_centroid_varies_per_window_after_fix():
    """v0.6.0: il centroide spettrale stampato nella narrativa deve
    cambiare fra finestra silenzio (centroide ~0), tono puro 440 Hz
    (centroide ~440), rumore bianco (centroide ~5000+ Hz).

    Verifica che le feature timbriche siano calcolate per finestra,
    non lette dal dict globale (bug v0.5.x).
    """
    sr = 22050
    waveform = _make_synthetic_waveform(sr)
    duration_s = len(waveform) / sr
    summary = _make_minimal_summary(duration_s)
    result = narrative.narrative_summary(summary, waveform, sr, mode="full")
    segments = result["segments"]
    assert len(segments) >= 3
    centroids = [_extract_centroid_hz(s["narrative_it"]) for s in segments[:3]]
    assert all(c is not None for c in centroids), f"centroide non trovato in narrativa: {centroids}"
    # Tono puro 440 Hz vs rumore bianco: differenza di centroide >= 1000 Hz
    c_tone = centroids[1]
    c_noise = centroids[2]
    assert abs(c_noise - c_tone) >= 1000, (
        f"centroide tono ({c_tone} Hz) e rumore ({c_noise} Hz) "
        f"identici o quasi: feature globali invece che per-finestra"
    )


def test_narrative_delta_based_collapses_homogeneous_windows_after_fix():
    """v0.6.0: su file omogeneo (3 finestre identiche di rumore bianco)
    la narrativa deve collassare le finestre senza variazione in un
    plateau, producendo meno paragrafi del numero di finestre.

    Verifica che la logica delta-based riconosca l'assenza di variazione
    e accumuli.
    """
    sr = 22050
    n_window = 30 * sr
    rng = np.random.default_rng(42)
    chunk = (0.3 * rng.standard_normal(n_window)).astype(np.float32)
    # 3 finestre identiche di rumore bianco
    waveform = np.concatenate([chunk, chunk, chunk])
    duration_s = len(waveform) / sr
    summary = _make_minimal_summary(duration_s)
    result = narrative.narrative_summary(summary, waveform, sr, mode="full")
    segments = result["segments"]
    # Su materiale omogeneo, delta-based deve produrre 1-2 segmenti, non 3
    assert len(segments) <= 2, (
        f"materiale omogeneo (3 chunk identici) produce {len(segments)} "
        f"segmenti, atteso <=2 con delta-based"
    )
