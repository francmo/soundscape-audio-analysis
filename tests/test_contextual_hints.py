"""Test regole contestuali v0.7.3 (scripts/contextual_hints.py).

Fixture minime: payload JSON ridotti con solo i campi necessari a ciascuna
regola, così i test restano leggibili e indipendenti.
"""
from __future__ import annotations

from scripts import contextual_hints as ch


def _summary(**overrides) -> dict:
    base = {
        "metadata": {"duration_s": 600},
        "technical": {"levels": {"dynamic_range_db": 30}},
        "hum": {"peaks": []},
        "spectral": {
            "timbre": {"spectral_flatness": 0.3},
            "onsets": {"events_per_sec": 1.0},
        },
        "semantic": {"classifier": {"top_global": [], "top_dominant_frames": []}},
        "clap": {"top_global": []},
        "speech": {"enabled": False},
        "ecoacoustic": {"ndsi": {"ndsi": 0.0}},
        "structure": {"n_sections": 4},
    }
    for k, v in overrides.items():
        # deep merge di primo livello per valori dict, sovrascrive altrimenti
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = {**base[k], **v}
        else:
            base[k] = v
    return base


def test_no_hints_on_empty_summary():
    assert ch.build_hints(_summary()) == ""
    assert ch.which_fired(_summary()) == []


def test_underwater_fires_on_whale():
    s = _summary(
        semantic={"classifier": {
            "top_global": [{"name": "Whale vocalization", "score": 0.5}],
            "top_dominant_frames": [{"name": "Whale vocalization", "pct": 20}],
        }},
    )
    assert "underwater" in ch.which_fired(s)
    assert "Winderen" in ch.build_hints(s)


def test_underwater_fires_on_idrofono_clap_plus_water():
    s = _summary(
        semantic={"classifier": {
            "top_global": [{"name": "Water", "score": 0.5}, {"name": "Stream", "score": 0.3}],
            "top_dominant_frames": [{"name": "Water", "pct": 30}],
        }},
        clap={"top_global": [{"prompt": "Registrazione idrofono di correnti subacquee"}]},
    )
    assert "underwater" in ch.which_fired(s)


def test_underwater_not_fired_on_generic_music():
    s = _summary(
        semantic={"classifier": {
            "top_global": [{"name": "Music", "score": 0.8}],
            "top_dominant_frames": [{"name": "Music", "pct": 80}],
        }},
    )
    assert "underwater" not in ch.which_fired(s)


def test_contact_mic_ice_fires_on_wind_rumble_long():
    s = _summary(
        metadata={"duration_s": 1200},
        semantic={"classifier": {
            "top_dominant_frames": [
                {"name": "Wind", "pct": 40},
                {"name": "Rumble", "pct": 25},
                {"name": "Ice", "pct": 10},
            ],
            "top_global": [],
        }},
    )
    assert "contact_mic_ice" in ch.which_fired(s)
    assert "Watson" in ch.build_hints(s)


def test_contact_mic_ice_not_fired_if_short():
    s = _summary(
        metadata={"duration_s": 120},
        semantic={"classifier": {
            "top_dominant_frames": [
                {"name": "Wind", "pct": 40},
                {"name": "Rumble", "pct": 25},
            ],
            "top_global": [],
        }},
    )
    assert "contact_mic_ice" not in ch.which_fired(s)


def test_urban_drone_requires_hum_and_antropic():
    s = _summary(
        technical={"levels": {"dynamic_range_db": 15}},
        hum={"peaks": [{"target_hz": 50, "verdict": "presente", "ratio_db": 4.0}]},
        ecoacoustic={"ndsi": {"ndsi": -0.4}},
        semantic={"classifier": {
            "top_dominant_frames": [{"name": "Vehicle", "pct": 30}],
            "top_global": [],
        }},
        speech={"language_detected": "en"},
    )
    assert "urban_drone" in ch.which_fired(s)


def test_urban_drone_blocked_on_italian_speech():
    """Deve NON triggerare su materiale italiano (rispetta regola lingua → scuola)."""
    s = _summary(
        technical={"levels": {"dynamic_range_db": 15}},
        hum={"peaks": [{"target_hz": 50, "verdict": "presente", "ratio_db": 4.0}]},
        ecoacoustic={"ndsi": {"ndsi": -0.4}},
        semantic={"classifier": {
            "top_dominant_frames": [{"name": "Vehicle", "pct": 30}],
            "top_global": [],
        }},
        speech={"language_detected": "it"},
    )
    assert "urban_drone" not in ch.which_fired(s)


def test_drone_metal_fires_on_hard_markers():
    s = _summary(
        metadata={"duration_s": 1800},
        semantic={"classifier": {
            "top_global": [
                {"name": "Heavy metal", "score": 0.5},
                {"name": "Angry music", "score": 0.4},
                {"name": "Punk rock", "score": 0.3},
            ],
            "top_dominant_frames": [{"name": "Music", "pct": 70}],
        }},
    )
    assert "drone_metal" in ch.which_fired(s)
    hint = ch.build_hints(s)
    assert "Earth" in hint and "Sunn" in hint


def test_drone_metal_not_fired_on_two_markers_only():
    s = _summary(
        metadata={"duration_s": 1800},
        semantic={"classifier": {
            "top_global": [
                {"name": "Heavy metal", "score": 0.5},
                {"name": "Angry music", "score": 0.4},
            ],
            "top_dominant_frames": [{"name": "Music", "pct": 70}],
        }},
    )
    # 2 soltanto, servono >= 3
    assert "drone_metal" not in ch.which_fired(s)


def test_hum_no_fonologia_fires_on_non_italian_lang():
    s = _summary(
        hum={"peaks": [{"target_hz": 50, "verdict": "presente", "ratio_db": 4.0}]},
        speech={"language_detected": "en"},
    )
    assert "hum_no_fonologia" in ch.which_fired(s)


def test_hum_no_fonologia_silent_on_italian():
    s = _summary(
        hum={"peaks": [{"target_hz": 50, "verdict": "presente", "ratio_db": 4.0}]},
        speech={"language_detected": "it"},
    )
    assert "hum_no_fonologia" not in ch.which_fired(s)


def test_sonic_journalism_requires_duration_and_mix():
    s = _summary(
        metadata={"duration_s": 3000},
        semantic={"classifier": {
            "top_dominant_frames": [
                {"name": "Speech", "pct": 30},
                {"name": "Bird", "pct": 10},
                {"name": "Vehicle", "pct": 15},
            ],
            "top_global": [],
        }},
        speech={"language_detected": "en"},
        structure={"n_sections": 6},
    )
    assert "sonic_journalism" in ch.which_fired(s)


def test_river_long_fires_with_water_markers_and_long_duration():
    s = _summary(
        metadata={"duration_s": 7200},
        semantic={"classifier": {
            "top_global": [
                {"name": "Water", "score": 0.5},
                {"name": "Stream", "score": 0.4},
                {"name": "Pour", "score": 0.3},
            ],
            "top_dominant_frames": [],
        }},
        structure={"n_sections": 8},
    )
    assert "river_long" in ch.which_fired(s)
    assert "Lockwood" in ch.build_hints(s)


def test_build_hints_returns_empty_when_none_match():
    assert ch.build_hints(_summary()) == ""


def test_build_hints_includes_header_when_any_match():
    s = _summary(
        metadata={"duration_s": 1800},
        semantic={"classifier": {
            "top_global": [
                {"name": "Heavy metal", "score": 0.5},
                {"name": "Angry music", "score": 0.4},
                {"name": "Punk rock", "score": 0.3},
            ],
            "top_dominant_frames": [],
        }},
    )
    out = ch.build_hints(s)
    assert "Suggerimenti contestuali" in out
    assert "Earth" in out
