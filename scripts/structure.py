"""Segmentazione strutturale del brano (v0.6.0).

Identifica sezioni significative del file audio via changepoint detection
deterministico su feature multidimensionali per finestra: RMS, centroide
spettrale, flatness, top-1 PANNs, top-1 CLAP. La detection usa il
gradiente del vettore feature normalizzato e una soglia adattiva
(mediana + K*MAD del gradiente sull'intero file).

Driver: il chiarimento di scopo del 16/04/2026 ha richiesto che la skill
pre-digerisca le sezioni significative (es. "00:00-03:00 quasi-silenzio
notturno; 03:00-07:00 sezione antropofonica diurna") invece di lasciare
all'agente compositivo la deduzione manuale. Output usato sia nel PDF
(timeline grafica + tabella) sia nel payload agente.

Output di `compute_structure()`:
    {
        "enabled": True,
        "n_sections": int,
        "window_seconds": float,
        "sections": [
            {
                "id": "S1",
                "t_start_s": float,
                "t_end_s": float,
                "duration_s": float,
                "mean_rms_db": float,
                "mean_centroid_hz": float,
                "mean_flatness": float,
                "dominant_panns": str,
                "dominant_clap_prompt": str,
                "krause": "biofonia" | "antropofonia" | "geofonia" | "mista" | "silenzio",
                "signature_label": str,  # max 30 caratteri italiano
            },
            ...
        ],
    }
"""
from __future__ import annotations

from typing import Any
import numpy as np

from . import config


# Mapping PANNs label -> categoria Krause (semplificato).
# Usato per dedurre la signature di una sezione dal top-1 PANNs.
_PANNS_TO_KRAUSE = {
    # Antropofonia (voce + meccanico + musicale)
    "Speech": "antropofonia",
    "Conversation": "antropofonia",
    "Narration, monologue": "antropofonia",
    "Whispering": "antropofonia",
    "Shout": "antropofonia",
    "Yell": "antropofonia",
    "Laughter": "antropofonia",
    "Crying, sobbing": "antropofonia",
    "Singing": "antropofonia",
    "Choir": "antropofonia",
    "Vehicle": "antropofonia",
    "Car": "antropofonia",
    "Truck": "antropofonia",
    "Bus": "antropofonia",
    "Motorcycle": "antropofonia",
    "Engine": "antropofonia",
    "Engine starting": "antropofonia",
    "Idling": "antropofonia",
    "Train": "antropofonia",
    "Aircraft": "antropofonia",
    "Helicopter": "antropofonia",
    "Boat, Water vehicle": "antropofonia",
    "Ship": "antropofonia",
    "Music": "antropofonia",
    "Musical instrument": "antropofonia",
    "Drum": "antropofonia",
    "Guitar": "antropofonia",
    "Piano": "antropofonia",
    "Bell": "antropofonia",
    "Church bell": "antropofonia",
    "Tools": "antropofonia",
    "Hammer": "antropofonia",
    "Machine gun": "antropofonia",
    # Biofonia
    "Bird": "biofonia",
    "Bird vocalization, bird call, bird song": "biofonia",
    "Chirp, tweet": "biofonia",
    "Owl": "biofonia",
    "Crow": "biofonia",
    "Insect": "biofonia",
    "Cricket": "biofonia",
    "Mosquito": "biofonia",
    "Bee, wasp, etc.": "biofonia",
    "Animal": "biofonia",
    "Domestic animals, pets": "biofonia",
    "Dog": "biofonia",
    "Cat": "biofonia",
    "Frog": "biofonia",
    "Cattle, bovinae": "biofonia",
    "Horse": "biofonia",
    "Sheep": "biofonia",
    "Pig": "biofonia",
    "Rodents, rats, mice": "biofonia",
    # Geofonia
    "Wind": "geofonia",
    "Rustling leaves": "geofonia",
    "Rain": "geofonia",
    "Raindrop": "geofonia",
    "Thunder": "geofonia",
    "Thunderstorm": "geofonia",
    "Water": "geofonia",
    "Stream": "geofonia",
    "Waterfall": "geofonia",
    "Ocean": "geofonia",
    "Waves, surf": "geofonia",
    "Liquid": "geofonia",
    "Splash, splatter": "geofonia",
    "Outside, rural or natural": "geofonia",
    "Outside, urban or manmade": "antropofonia",
    "Silence": "silenzio",
}


def _krause_from_panns(panns_label: str) -> str:
    """Mappa un label PANNs alla categoria Krause. Fallback 'mista' per
    label non mappati."""
    if not panns_label:
        return "mista"
    return _PANNS_TO_KRAUSE.get(panns_label, "mista")


def _build_window_indices(n_samples: int, sr: int,
                           window_seconds: float) -> list[tuple[int, int, float, float]]:
    """Ritorna lista di (a, b, t_start_s, t_end_s) per ogni finestra.
    Skippa finestre piu' corte di 0.5 s."""
    chunk_samples = int(window_seconds * sr)
    n_chunks = max(1, int(np.ceil(n_samples / chunk_samples)))
    out: list[tuple[int, int, float, float]] = []
    min_samples = int(0.5 * sr)
    for i in range(n_chunks):
        a = i * chunk_samples
        b = min(a + chunk_samples, n_samples)
        if b - a < min_samples:
            continue
        out.append((a, b, a / sr, b / sr))
    return out


def _aggregate_top1_for_window(timeline: list[dict], t_start: float, t_end: float,
                                key: str = "top") -> str:
    """Estrae il top-1 (per score medio) dei tag/categorie cadenti nella
    finestra [t_start, t_end] della timeline PANNs (key='top') o CLAP
    (key='tags'). Ritorna stringa vuota se nessun tag presente."""
    label_key = "name" if key == "top" else "prompt"
    scores: dict[str, list[float]] = {}
    for entry in timeline:
        seg_start = entry.get("t_start_s", 0)
        seg_end = entry.get("t_end_s", 0)
        if seg_end <= t_start or seg_start >= t_end:
            continue
        for item in entry.get(key, []):
            name = item.get(label_key, "")
            if not name:
                continue
            scores.setdefault(name, []).append(float(item.get("score", 0.0)))
    if not scores:
        return ""
    best = max(scores.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
    return best[0]


def _extract_features_per_window(waveform: np.ndarray, sr: int,
                                   window_seconds: float,
                                   classifier_timeline: list[dict],
                                   clap_timeline: list[dict]) -> list[dict]:
    """Per ogni finestra calcola [rms_db, centroide, flatness, top-1 PANNs,
    top-1 CLAP]. Vettore base per il changepoint detection."""
    from . import spectral as spec_mod
    indices = _build_window_indices(len(waveform), sr, window_seconds)
    out: list[dict] = []
    for a, b, t_start, t_end in indices:
        chunk = waveform[a:b]
        rms = float(np.sqrt(np.mean(chunk ** 2)) + 1e-12)
        rms_db = float(20 * np.log10(rms))
        timbre = spec_mod.compute_timbre(chunk, sr)
        centroid = float(timbre["spectral_centroid_hz"])
        flatness = float(timbre["spectral_flatness"])
        panns_top1 = _aggregate_top1_for_window(classifier_timeline, t_start, t_end, key="top")
        clap_top1 = _aggregate_top1_for_window(clap_timeline, t_start, t_end, key="tags")
        out.append({
            "t_start_s": t_start,
            "t_end_s": t_end,
            "rms_db": rms_db,
            "centroid_hz": centroid,
            "flatness": flatness,
            "panns_top1": panns_top1,
            "clap_top1": clap_top1,
        })
    return out


def _detect_changepoints(features: list[dict],
                          window_seconds: float) -> list[int]:
    """Rileva indici di confine (boundary) usando gradiente delle feature
    normalizzate + cambi categoriali. Soglia adattiva mediana+K*MAD del
    gradiente sull'intero file. Vincoli: min distance fra confini in
    secondi configurabile, max numero confini.

    Ritorna lista ordinata di indici di feature dove inizia una nuova
    sezione (escluso 0 che e' implicito)."""
    n = len(features)
    if n < 2:
        return []

    rms = np.array([f["rms_db"] for f in features], dtype=np.float64)
    cent = np.array([f["centroid_hz"] for f in features], dtype=np.float64)
    flat = np.array([f["flatness"] for f in features], dtype=np.float64)

    def _zscore(x: np.ndarray) -> np.ndarray:
        std = float(np.std(x))
        if std < 1e-9:
            return np.zeros_like(x)
        return (x - float(np.mean(x))) / std

    rms_n = _zscore(rms)
    cent_n = _zscore(cent)
    flat_n = _zscore(flat)

    # Componenti categoriali: 1.0 se top-1 cambia, altrimenti 0.0
    panns_change = np.zeros(n, dtype=np.float64)
    clap_change = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        if features[i]["panns_top1"] and features[i]["panns_top1"] != features[i - 1]["panns_top1"]:
            panns_change[i] = 1.0
        if features[i]["clap_top1"] and features[i]["clap_top1"] != features[i - 1]["clap_top1"]:
            clap_change[i] = 1.0

    # Gradiente: somma delle differenze assolute sulle componenti normalizzate
    # piu' contributi categoriali (peso 1.0 ciascuno).
    grad = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        grad[i] = (
            abs(rms_n[i] - rms_n[i - 1])
            + abs(cent_n[i] - cent_n[i - 1])
            + abs(flat_n[i] - flat_n[i - 1])
            + panns_change[i]
            + clap_change[i]
        )

    # Soglia adattiva
    grad_nonzero = grad[1:]  # esclude indice 0
    if len(grad_nonzero) == 0:
        return []
    median = float(np.median(grad_nonzero))
    mad = float(np.median(np.abs(grad_nonzero - median)) + 1e-9)
    threshold = median + config.STRUCTURE_GRADIENT_THRESHOLD_MAD_K * mad

    # Candidati: indici dove gradiente supera soglia
    candidates = [i for i in range(1, n) if grad[i] > threshold]

    # Vincolo min distance: rimuovi candidati troppo vicini al precedente
    min_distance_windows = max(1, int(np.ceil(config.STRUCTURE_MIN_SECTION_DURATION_S / window_seconds)))
    filtered: list[int] = []
    last = -min_distance_windows - 1
    for i in candidates:
        if i - last >= min_distance_windows:
            filtered.append(i)
            last = i

    # Vincolo max sections: tieni i top-N per gradiente
    max_boundaries = config.STRUCTURE_MAX_SECTIONS - 1  # N sezioni = N-1 confini
    if len(filtered) > max_boundaries:
        filtered_sorted = sorted(filtered, key=lambda i: -grad[i])[:max_boundaries]
        filtered = sorted(filtered_sorted)

    # Vincolo min sections: se troppi pochi confini, forza una divisione
    # equispaziata per raggiungere STRUCTURE_MIN_SECTIONS.
    min_boundaries = config.STRUCTURE_MIN_SECTIONS - 1
    if len(filtered) < min_boundaries and n >= config.STRUCTURE_MIN_SECTIONS:
        # Genera confini equispaziati
        equal = [int(round(n * (k / config.STRUCTURE_MIN_SECTIONS)))
                 for k in range(1, config.STRUCTURE_MIN_SECTIONS)]
        # Merge senza duplicare
        union = sorted(set(filtered) | set(equal))
        filtered = union[:max_boundaries]

    return filtered


def _label_section_signature(section: dict) -> str:
    """Genera una stringa breve italiana che descrive la sezione, basata
    su krause + caratteristiche dinamiche e timbriche. Max ~40 caratteri."""
    krause = section.get("krause", "mista")
    rms_db = section.get("mean_rms_db", -60.0)
    flatness = section.get("mean_flatness", 0.5)

    if rms_db < -50.0:
        return "quasi-silenzio"

    # Aggettivo dinamico
    if rms_db < -35.0:
        dyn = "soffusa"
    elif rms_db < -20.0:
        dyn = "moderata"
    else:
        dyn = "intensa"

    # Carattere timbrico
    if flatness < 0.05:
        timbre = "tonale"
    elif flatness < 0.3:
        timbre = "mista"
    else:
        timbre = "rumorosa"

    if krause == "silenzio":
        return "quasi-silenzio"
    if krause == "biofonia":
        return f"biofonia {dyn} {timbre}"
    if krause == "antropofonia":
        return f"antropofonia {dyn} {timbre}"
    if krause == "geofonia":
        return f"geofonia {dyn} {timbre}"
    return f"sezione mista {dyn}"


def _build_sections(features: list[dict],
                     boundaries: list[int]) -> list[dict]:
    """Costruisce le sezioni a partire dalle feature per finestra e dai
    confini. Aggrega medie e dominanti per ciascuna sezione."""
    n = len(features)
    if n == 0:
        return []
    cuts = [0] + sorted(boundaries) + [n]
    sections: list[dict] = []
    for k in range(len(cuts) - 1):
        a, b = cuts[k], cuts[k + 1]
        if b <= a:
            continue
        chunk = features[a:b]
        t_start = chunk[0]["t_start_s"]
        t_end = chunk[-1]["t_end_s"]
        mean_rms = float(np.mean([f["rms_db"] for f in chunk]))
        mean_centroid = float(np.mean([f["centroid_hz"] for f in chunk]))
        mean_flatness = float(np.mean([f["flatness"] for f in chunk]))

        # Dominanti (mode) per categoriali
        def _mode(values: list[str]) -> str:
            counts: dict[str, int] = {}
            for v in values:
                if not v:
                    continue
                counts[v] = counts.get(v, 0) + 1
            if not counts:
                return ""
            return max(counts.items(), key=lambda kv: kv[1])[0]

        dominant_panns = _mode([f["panns_top1"] for f in chunk])
        dominant_clap = _mode([f["clap_top1"] for f in chunk])
        krause = _krause_from_panns(dominant_panns) if dominant_panns else "mista"
        if mean_rms < -50.0:
            krause = "silenzio"

        section = {
            "id": f"S{k + 1}",
            "t_start_s": round(t_start, 2),
            "t_end_s": round(t_end, 2),
            "duration_s": round(t_end - t_start, 2),
            "mean_rms_db": round(mean_rms, 2),
            "mean_centroid_hz": round(mean_centroid, 1),
            "mean_flatness": round(mean_flatness, 4),
            "dominant_panns": dominant_panns,
            "dominant_clap_prompt": dominant_clap,
            "krause": krause,
        }
        section["signature_label"] = _label_section_signature(section)
        sections.append(section)
    return sections


def compute_structure(waveform: np.ndarray, sr: int, summary: dict,
                       window_seconds: float | None = None) -> dict:
    """Entry point: identifica sezioni strutturali del brano.

    Ritorna dict con `enabled`, `n_sections`, `window_seconds`, `sections`.
    Se la waveform e' troppo corta (< 2 finestre) ritorna una sola sezione
    che copre l'intero file.
    """
    if window_seconds is None:
        window_seconds = config.STRUCTURE_WINDOW_S

    duration_s = len(waveform) / sr if sr > 0 else 0.0
    if duration_s < 2 * window_seconds:
        # File troppo corto: una sola sezione
        return {
            "enabled": True,
            "n_sections": 1,
            "window_seconds": window_seconds,
            "sections": [{
                "id": "S1",
                "t_start_s": 0.0,
                "t_end_s": round(duration_s, 2),
                "duration_s": round(duration_s, 2),
                "mean_rms_db": -60.0,
                "mean_centroid_hz": 0.0,
                "mean_flatness": 0.0,
                "dominant_panns": "",
                "dominant_clap_prompt": "",
                "krause": "mista",
                "signature_label": "sezione unica",
            }],
        }

    classifier_timeline = (summary.get("semantic", {}).get("classifier") or {}).get("timeline", [])
    clap_timeline = (summary.get("clap") or {}).get("timeline", [])

    features = _extract_features_per_window(
        waveform, sr, window_seconds, classifier_timeline, clap_timeline
    )
    boundaries = _detect_changepoints(features, window_seconds)
    sections = _build_sections(features, boundaries)

    return {
        "enabled": True,
        "n_sections": len(sections),
        "window_seconds": window_seconds,
        "sections": sections,
    }
