"""Test su scripts/speech_mediation.py (v0.12.6, P1 caso A).

Verifica i tre rami principali della classificazione:
1. Override PANNs su label mediated (Television, Radio, Loudspeaker, ecc.).
2. Fallback `uncertain` su materiale acusmatico (flatness > 0.3).
3. Euristica spettrale composita su 4 feature.

Le fixture audio sono sintetiche, generate al volo, per garantire
riproducibilità senza dipendere da file esterni.
"""
from __future__ import annotations

import numpy as np
import pytest

from scripts import speech_mediation as sm


def _voice_like_segment(sr: int = 22050, duration_s: float = 5.0,
                         f0_hz: float = 180.0,
                         lowpass_cut_hz: float | None = None,
                         seed: int = 0) -> np.ndarray:
    """Genera un segmento voice-like: tono con armoniche + rumore di canale.

    Se `lowpass_cut_hz` non e' None, applica un filtro passa-basso analogico
    semplificato per simulare il filtraggio acustico di una parete (parlato
    mediato TV/radio).
    """
    n = int(duration_s * sr)
    t = np.arange(n, dtype=np.float32) / sr
    rng = np.random.default_rng(seed)
    # Tono fondamentale + armoniche (formant region)
    signal = 0.0
    for harmonic in (1, 2, 3, 5, 7):
        amp = 0.2 / harmonic
        signal = signal + amp * np.sin(2 * np.pi * (f0_hz * harmonic) * t)
    # Rumore di fondo realistico
    signal = signal + 0.05 * rng.standard_normal(n)
    if lowpass_cut_hz is not None:
        # Filtro passa-basso analogico semplificato (one-pole)
        rc = 1.0 / (2 * np.pi * lowpass_cut_hz)
        dt = 1.0 / sr
        alpha = dt / (rc + dt)
        filtered = np.zeros_like(signal)
        filtered[0] = signal[0]
        for i in range(1, n):
            filtered[i] = filtered[i - 1] + alpha * (signal[i] - filtered[i - 1])
        signal = filtered
    return signal.astype(np.float32)


def test_override_panns_television_returns_mediated():
    """Se PANNs top_global contiene `Television` >= 0.05, override immediato
    a `mediated` con confidence high."""
    waveform = _voice_like_segment(duration_s=3.0)
    classifier = {
        "top_global": [
            {"name": "Speech", "score": 0.30},
            {"name": "Television", "score": 0.12},
            {"name": "Inside, small room", "score": 0.08},
        ]
    }
    result = sm.classify_speech_mediation(waveform, 22050,
                                           classifier_result=classifier,
                                           flatness=0.05)
    assert result["label"] == "mediated"
    assert result["confidence"] == "high"
    assert "Television" in result["reason"]


def test_override_panns_loudspeaker_returns_mediated():
    """Loudspeaker (PA) e' anch'esso label mediated."""
    waveform = _voice_like_segment(duration_s=3.0)
    classifier = {
        "top_global": [
            {"name": "Speech", "score": 0.40},
            {"name": "Loudspeaker", "score": 0.07},
        ]
    }
    result = sm.classify_speech_mediation(waveform, 22050,
                                           classifier_result=classifier,
                                           flatness=0.05)
    assert result["label"] == "mediated"
    assert result["confidence"] == "high"


def test_override_panns_below_threshold_no_override():
    """Label mediated con score < 0.05 non attiva override."""
    waveform = _voice_like_segment(duration_s=3.0)
    classifier = {
        "top_global": [
            {"name": "Speech", "score": 0.50},
            {"name": "Television", "score": 0.03},  # sotto soglia
        ]
    }
    result = sm.classify_speech_mediation(waveform, 22050,
                                           classifier_result=classifier,
                                           flatness=0.05)
    # Non e' override PANNs: cade in euristica spettrale
    assert "Television" not in result.get("reason", "")


def test_high_flatness_returns_uncertain():
    """Materiale con flatness > 0.3 (acusmatica trasformata) torna `uncertain`
    perche' la distinzione direct/mediated non e' significativa."""
    waveform = _voice_like_segment(duration_s=3.0)
    result = sm.classify_speech_mediation(waveform, 22050,
                                           classifier_result=None,
                                           flatness=0.45)
    assert result["label"] == "uncertain"
    assert result["confidence"] == "low"
    assert "flatness" in result["reason"].lower()


def test_heuristic_lowpass_voice_classified_mediated():
    """Segmento voice-like passato attraverso un passa-basso a 2.5 kHz
    (simulazione filtro parete) deve essere classificato come mediated
    o uncertain (mai direct), perche' rolloff e shoulder slope diventano
    sintomi di mediazione."""
    waveform = _voice_like_segment(duration_s=4.0, f0_hz=180.0,
                                     lowpass_cut_hz=2500.0, seed=1)
    result = sm.classify_speech_mediation(waveform, 22050,
                                           classifier_result=None,
                                           flatness=0.08)
    assert result["label"] in ("mediated", "uncertain")


def test_summary_wrapper_disabled_when_speech_below_threshold():
    """Se PANNs top_dominant_frames Speech < 5%, lo speech_mediation non si
    attiva (enabled=False) per non sprecare calcoli."""
    waveform = _voice_like_segment(duration_s=3.0)
    summary = {
        "semantic": {
            "classifier": {
                "top_dominant_frames": [
                    {"name": "Water", "pct": 80.0},
                    {"name": "Speech", "pct": 2.0},  # < soglia 5%
                ],
                "top_global": [],
            },
        },
        "spectral": {"timbre": {"spectral_flatness": 0.05}},
    }
    result = sm.speech_mediation_summary(waveform, 22050, summary)
    assert result["enabled"] is False
    assert "2.0" in result["reason"]


def test_summary_wrapper_active_when_speech_dominant():
    """Se PANNs Speech >= 5% dei dominant_frames, lo speech_mediation
    si attiva e produce un global classification."""
    waveform = _voice_like_segment(duration_s=3.0)
    summary = {
        "semantic": {
            "classifier": {
                "top_dominant_frames": [
                    {"name": "Speech", "pct": 21.05},  # caso A
                    {"name": "Water", "pct": 31.58},
                ],
                "top_global": [
                    {"name": "Water", "score": 0.16},
                    {"name": "Speech", "score": 0.154},
                ],
            },
        },
        "spectral": {"timbre": {"spectral_flatness": 0.10}},
    }
    result = sm.speech_mediation_summary(waveform, 22050, summary)
    assert result["enabled"] is True
    assert result["speech_dominant_pct"] == 21.05
    assert "global" in result
    assert result["global"]["label"] in ("direct", "mediated", "uncertain")


def test_features_are_serializable():
    """Il dict ritornato dalla classify_speech_mediation deve essere JSON
    serializable (numeri Python, non numpy)."""
    import json
    waveform = _voice_like_segment(duration_s=2.0)
    result = sm.classify_speech_mediation(waveform, 22050,
                                           classifier_result=None,
                                           flatness=0.05)
    # Non deve sollevare
    serialized = json.dumps(result, ensure_ascii=False)
    assert len(serialized) > 0
