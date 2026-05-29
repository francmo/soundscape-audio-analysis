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


# =====================================================================
# v0.12.6 (P3 + P5 caso A): test caveat sezioni brevi e
# sub-segmentazione interna su famiglie geofoniche/biofoniche.
# =====================================================================


def test_panns_confidence_for_duration_thresholds():
    """Le soglie di durata mappano correttamente in low/medium/high."""
    assert structure._panns_confidence_for_duration(0.5) == "low"
    assert structure._panns_confidence_for_duration(1.9) == "low"
    assert structure._panns_confidence_for_duration(2.0) == "medium"
    assert structure._panns_confidence_for_duration(4.9) == "medium"
    assert structure._panns_confidence_for_duration(5.0) == "high"
    assert structure._panns_confidence_for_duration(30.0) == "high"


def test_short_section_signature_label_is_impulse_when_low_conf():
    """Sezione < 2s con confidence low e Krause `mista` (gia' neutralizzato):
    signature_label = 'impulso e coda'. Caso scuola: S5 A 0.74s."""
    section = {
        "duration_s": 0.74,
        "dominant_panns_confidence": "low",
        "krause": "mista",
        "mean_rms_db": -26.5,
        "mean_flatness": 0.003,
    }
    label = structure._label_section_signature(section)
    assert label == "impulso e coda"


def test_short_section_krause_neutralized_in_build_sections():
    """Su sezione costruita con durata < 2s, la famiglia Krause antropofonia
    (derivata da `Music`) viene neutralizzata a `mista` per non propagare
    una classificazione inaffidabile."""
    # Feature singola di 1s con dominant `Music` (PANNs antropofonia)
    features = [{
        "t_start_s": 0.0, "t_end_s": 1.0,
        "rms_db": -26.0, "centroid_hz": 1050.0, "flatness": 0.003,
        "panns_top1": "Music", "panns_top3": ["Music", "Tap", "Silence"],
        "clap_top1": "oggetto impulsivo breve",
    }]
    sections = structure._build_sections(features, boundaries=[])
    assert len(sections) == 1
    assert sections[0]["dominant_panns"] == "Music"
    assert sections[0]["dominant_panns_confidence"] == "low"
    # Krause neutralizzata
    assert sections[0]["krause"] == "mista"


def test_subsegment_section_splits_water_shower_vs_sink():
    """Caso scuola A S3: 80s di Water con top-3 PANNs che cambia
    a meta'. Aspettiamo 2 sub-sezioni S3a (doccia: Water tap, Bathtub) +
    S3b (lavandino: Sink, Fill)."""
    features = []
    for i in range(8):  # 8 finestre da 10s = 80s
        t0 = 70 + i * 10
        if i < 4:
            top3 = ["Water", "Water tap, faucet", "Bathtub (filling or washing)"]
        else:
            top3 = ["Water", "Sink (filling or washing)", "Fill (with liquid)"]
        features.append({
            "t_start_s": t0, "t_end_s": t0 + 10,
            "rms_db": -40, "centroid_hz": 4500, "flatness": 0.23,
            "panns_top1": "Water", "panns_top3": top3,
            "clap_top1": "acqua",
        })
    section = {
        "id": "S3", "t_start_s": 70.0, "t_end_s": 150.0,
        "duration_s": 80.0, "krause": "geofonia",
    }
    subs = structure._subsegment_section(section, features, window_seconds=10.0)
    assert len(subs) == 2
    assert subs[0]["id"] == "S3a"
    assert subs[1]["id"] == "S3b"
    # S3a deve contenere le sub-class della doccia
    assert "Water tap, faucet" in subs[0]["sub_class_top"]
    # S3b deve contenere le sub-class del lavandino
    assert "Sink (filling or washing)" in subs[1]["sub_class_top"]
    # Entrambe ereditano la famiglia Krause del padre
    assert subs[0]["krause"] == "geofonia"
    assert subs[1]["krause"] == "geofonia"


def test_subsegment_section_skips_short_parent():
    """Sezione padre < 30s non viene sub-segmentata (vincolo di stabilita')."""
    features = [{
        "t_start_s": 0, "t_end_s": 10,
        "rms_db": -40, "centroid_hz": 4500, "flatness": 0.23,
        "panns_top1": "Water", "panns_top3": ["Water", "Splash, splatter", "Drip"],
        "clap_top1": "acqua",
    }]
    section = {
        "id": "S1", "t_start_s": 0.0, "t_end_s": 20.0,
        "duration_s": 20.0, "krause": "geofonia",
    }
    subs = structure._subsegment_section(section, features, window_seconds=10.0)
    assert subs == []


def test_subsegment_section_skips_non_geo_bio_families():
    """Sezione antropofonia: non sub-segmentata. P5 si applica solo a
    geofonia/biofonia (decisione di design: famiglie omogenee con sub-class
    PANNs distintive)."""
    features = []
    for i in range(8):
        features.append({
            "t_start_s": i * 10, "t_end_s": (i + 1) * 10,
            "rms_db": -30, "centroid_hz": 1500, "flatness": 0.01,
            "panns_top1": "Speech",
            "panns_top3": ["Speech", "Conversation", "Music"] if i < 4
                          else ["Speech", "Singing", "Narration"],
            "clap_top1": "voce",
        })
    section = {
        "id": "S1", "t_start_s": 0.0, "t_end_s": 80.0,
        "duration_s": 80.0, "krause": "antropofonia",
    }
    subs = structure._subsegment_section(section, features, window_seconds=10.0)
    assert subs == []


def test_subsegment_section_no_cut_when_top3_stable():
    """Se il top-3 PANNs resta sostanzialmente invariato, niente sub-cut."""
    features = []
    for i in range(8):
        features.append({
            "t_start_s": i * 10, "t_end_s": (i + 1) * 10,
            "rms_db": -40, "centroid_hz": 4500, "flatness": 0.23,
            "panns_top1": "Water",
            "panns_top3": ["Water", "Stream", "Splash, splatter"],
            "clap_top1": "acqua",
        })
    section = {
        "id": "S3", "t_start_s": 0.0, "t_end_s": 80.0,
        "duration_s": 80.0, "krause": "geofonia",
    }
    subs = structure._subsegment_section(section, features, window_seconds=10.0)
    assert subs == []


def test_subsegment_caps_at_max_per_parent():
    """Anche con molti cut potenziali, il numero di sub-sezioni non supera
    SUBSEGMENT_MAX_PER_PARENT."""
    # 12 finestre, top-3 cambia ogni 2 finestre (-> 6 cut potenziali)
    features = []
    rotations = [
        ["Water", "Drip", "Splash, splatter"],
        ["Water", "Stream", "Gurgling"],
        ["Water", "Water tap, faucet", "Bathtub (filling or washing)"],
        ["Water", "Sink (filling or washing)", "Fill (with liquid)"],
        ["Water", "Ocean", "Waves, surf"],
        ["Water", "Pour", "Waterfall"],
    ]
    for i in range(12):
        top3 = rotations[i // 2]
        features.append({
            "t_start_s": i * 10, "t_end_s": (i + 1) * 10,
            "rms_db": -40, "centroid_hz": 4500, "flatness": 0.23,
            "panns_top1": "Water", "panns_top3": top3,
            "clap_top1": "acqua",
        })
    section = {
        "id": "S1", "t_start_s": 0.0, "t_end_s": 120.0,
        "duration_s": 120.0, "krause": "geofonia",
    }
    subs = structure._subsegment_section(section, features, window_seconds=10.0)
    assert len(subs) <= config.SUBSEGMENT_MAX_PER_PARENT


def test_compute_structure_propagates_sub_sections_in_output():
    """compute_structure deve registrare `has_sub_sections` + `sub_sections`
    nei record padre quando applicabile, e contare `n_sub_sections` nel top-
    level. Su brano sintetico senza variazione top-3 PANNs (non vengono
    iniettate timeline), niente sub-sections."""
    sr = 22050
    waveform = _make_synthetic_waveform_three_sections(sr)
    result = structure.compute_structure(waveform, sr, summary={})
    # Senza summary.semantic/clap, le timeline sono vuote, niente sub-sections
    assert result.get("n_sub_sections", 0) == 0


# =====================================================================
# v0.13.0 (Intervento D dossier P&T): signature_label a 4 dimensioni con
# correlazione onset/sezione e soglie tonale piu' fini.
# =====================================================================


def test_events_per_sec_in_section_counts_onset_within_window():
    """_events_per_sec_in_section: 5 onset in 10 s -> 0.5 eventi/s. Vincolo
    di intervallo semi-aperto [t_start, t_end)."""
    onset_times = [1.0, 3.0, 5.0, 7.0, 9.0, 11.0]
    rate = structure._events_per_sec_in_section(onset_times, 0.0, 10.0)
    # 5 onset (1,3,5,7,9) cadono in [0,10); 11.0 e' escluso.
    assert rate == pytest.approx(0.5, abs=0.01)


def test_events_per_sec_in_section_empty_returns_zero():
    """Se non ci sono onset, ritorna 0 senza errori."""
    assert structure._events_per_sec_in_section([], 0.0, 30.0) == 0.0
    assert structure._events_per_sec_in_section(None, 0.0, 30.0) == 0.0


def test_signature_label_4d_includes_centroid_band_and_density():
    """Con tutte e 4 le dimensioni popolate, la signature deve riflettere
    krause + intensita + banda + densita. Esempio: bar urbano antropofonico
    con voci, centroide medio (1500 Hz), eventi densi (2.5/s) -> attesa
    "antropofonia moderata chiara densa" o equivalente."""
    section = {
        "duration_s": 30.0,
        "dominant_panns_confidence": "high",
        "krause": "antropofonia",
        "mean_rms_db": -25.0,         # moderata
        "mean_flatness": 0.02,        # tonale (>0.015, <0.05)
        "mean_centroid_hz": 1500.0,   # chiara (>1000, <4000)
        "events_per_sec": 2.5,        # densa (>2.0)
    }
    label = structure._label_section_signature(section)
    assert "antropofonia" in label
    assert "moderata" in label
    assert "chiara" in label
    assert "densa" in label
    assert len(label) <= 50


def test_signature_label_differs_between_two_antropofonia_sections():
    """Pattern 5 caso B: con il nuovo template a 4 dimensioni, due
    sezioni antropofoniche con caratteristiche timbriche/onset diverse
    devono ricevere etichette diverse (prima v0.13.0 davano "antropofonia
    moderata tonale" entrambe)."""
    s1 = structure._label_section_signature({
        "duration_s": 30.0,
        "dominant_panns_confidence": "high",
        "krause": "antropofonia",
        "mean_rms_db": -25.0,
        "mean_flatness": 0.02,
        "mean_centroid_hz": 1500.0,
        "events_per_sec": 0.3,        # sparsa
    })
    s2 = structure._label_section_signature({
        "duration_s": 30.0,
        "dominant_panns_confidence": "high",
        "krause": "antropofonia",
        "mean_rms_db": -25.0,
        "mean_flatness": 0.02,
        "mean_centroid_hz": 1500.0,
        "events_per_sec": 2.5,        # densa
    })
    assert s1 != s2


def test_signature_label_omits_density_on_short_section():
    """Sotto 5s di durata, la stima di onset_density e' rumorosa: l'etichetta
    omette la 4a dimensione per non aggiungere rumore."""
    section = {
        "duration_s": 3.0,
        "dominant_panns_confidence": "medium",
        "krause": "antropofonia",
        "mean_rms_db": -25.0,
        "mean_flatness": 0.02,
        "mean_centroid_hz": 1500.0,
        "events_per_sec": 3.0,  # densa, ma non deve apparire
    }
    label = structure._label_section_signature(section)
    assert "densa" not in label and "sparsa" not in label and "media" not in label.split()


def test_signature_label_fallback_when_events_per_sec_missing():
    """Retrocompatibilita': sezioni senza `events_per_sec` (output v0.12.x)
    producono comunque un'etichetta valida sulle 3 dimensioni base."""
    section = {
        "duration_s": 30.0,
        "dominant_panns_confidence": "high",
        "krause": "biofonia",
        "mean_rms_db": -30.0,
        "mean_flatness": 0.1,
        "mean_centroid_hz": 4500.0,   # brillante
        # events_per_sec assente
    }
    label = structure._label_section_signature(section)
    assert "biofonia" in label
    assert "brillante" in label
    assert len(label) <= 50


def test_signature_label_silence_overrides_other_dimensions():
    """Su RMS molto basso resta 'quasi-silenzio' anche con krause/centroide
    diversi (override storico v0.12.x preservato)."""
    section = {
        "duration_s": 30.0,
        "dominant_panns_confidence": "high",
        "krause": "geofonia",
        "mean_rms_db": -55.0,
        "mean_flatness": 0.4,
        "mean_centroid_hz": 8000.0,
        "events_per_sec": 0.1,
    }
    label = structure._label_section_signature(section)
    assert label == "quasi-silenzio"


def test_compute_structure_populates_events_per_sec_per_section():
    """compute_structure deve popolare `events_per_sec` in ogni sezione,
    leggendo gli onset da summary.spectral.onsets.events_times_s. Sul
    brano sintetico (silenzio + tono + rumore) gli onset sono distribuiti
    soprattutto nei due segmenti non-silenziosi, quindi la prima sezione
    deve avere events_per_sec basso o nullo."""
    sr = 22050
    waveform = _make_synthetic_waveform_three_sections(sr)
    # Iniettiamo onset solo nel secondo segmento (30-60s) per controllarne
    # la distribuzione: 5 onset uniformi in [35, 55].
    summary = {
        "spectral": {
            "onsets": {
                "events_times_s": [35.0, 40.0, 45.0, 50.0, 55.0],
            }
        }
    }
    result = structure.compute_structure(waveform, sr, summary=summary)
    for s in result["sections"]:
        assert "events_per_sec" in s, f"sezione {s['id']} senza events_per_sec"
    # La sezione che copre il segmento di silenzio iniziale (0-30) non deve
    # ricevere alcun onset iniettato.
    first = result["sections"][0]
    assert first["events_per_sec"] == 0.0


def test_signature_centroid_band_thresholds():
    """Verifica le 4 fasce di banda centroide per signature_label."""
    from scripts import locale_it as L
    assert L.signature_centroid_band(100.0) == "scura"
    assert L.signature_centroid_band(500.0) == "media"
    assert L.signature_centroid_band(2000.0) == "chiara"
    assert L.signature_centroid_band(8000.0) == "brillante"


def test_signature_tonality_thresholds_pattern_6():
    """Pattern 6 caso B: le nuove soglie discriminano fra 'molto
    tonale' (<0.005) e 'moderatamente tonale' (0.005-0.015) etc. La
    flatness 0.010 (tipica del bar Mamo') non deve essere 'molto tonale'."""
    from scripts import locale_it as L
    assert L.signature_tonality(0.001) == "molto tonale"
    assert L.signature_tonality(0.010) == "moderatamente tonale"  # caso B
    assert L.signature_tonality(0.030) == "tonale"
    assert L.signature_tonality(0.100) == "tendenzialmente tonale"
    assert L.signature_tonality(0.300) == "misto"
    assert L.signature_tonality(0.700) == "molto rumoroso"


# =====================================================================
# v0.13.0 (Intervento A dossier P&T): hi-fi/lo-fi per sezione.
# =====================================================================


def test_annotate_sections_with_hifi_lofi_populates_field():
    """_annotate_sections_with_hifi_lofi popola il campo hi_fi_lo_fi in
    ciascuna sezione con label + score."""
    sr = 22050
    waveform = _make_synthetic_waveform_three_sections(sr)
    sections = [
        {"id": "S1", "t_start_s": 0.0, "t_end_s": 30.0,
         "duration_s": 30.0, "mean_flatness": 0.5},
        {"id": "S2", "t_start_s": 30.0, "t_end_s": 60.0,
         "duration_s": 30.0, "mean_flatness": 0.01},
        {"id": "S3", "t_start_s": 60.0, "t_end_s": 90.0,
         "duration_s": 30.0, "mean_flatness": 0.5},
    ]
    structure._annotate_sections_with_hifi_lofi(sections, waveform, sr)
    for s in sections:
        assert "hi_fi_lo_fi" in s
        assert s["hi_fi_lo_fi"] is not None
        assert "label" in s["hi_fi_lo_fi"]
        assert "score_5" in s["hi_fi_lo_fi"]


def test_annotate_sections_with_hifi_lofi_fallback_on_short_slice():
    """Sezione con slice di waveform troppo corto (<0.2s): hi_fi_lo_fi None."""
    sr = 22050
    waveform = np.zeros(sr * 90, dtype=np.float32)
    sections = [
        {"id": "S1", "t_start_s": 0.0, "t_end_s": 0.1,
         "duration_s": 0.1, "mean_flatness": 0.1},
    ]
    structure._annotate_sections_with_hifi_lofi(sections, waveform, sr)
    assert sections[0]["hi_fi_lo_fi"] is None


def test_compute_structure_populates_hifi_lofi_per_section():
    """Integrazione end-to-end: compute_structure deve popolare hi_fi_lo_fi
    in ciascuna sezione del brano sintetico (3 segmenti netti)."""
    sr = 22050
    waveform = _make_synthetic_waveform_three_sections(sr)
    result = structure.compute_structure(waveform, sr, summary={})
    assert result["n_sections"] >= 2
    for s in result["sections"]:
        # Tutte le sezioni del brano sintetico sono >= 30s, niente fallback
        assert s.get("hi_fi_lo_fi") is not None
        assert isinstance(s["hi_fi_lo_fi"]["score_5"], int)
        assert 1 <= s["hi_fi_lo_fi"]["score_5"] <= 5
