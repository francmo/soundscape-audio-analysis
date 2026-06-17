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
from . import clap_mapping


def _dominant_clap_excluding_marked(
    clap_values: list[str], marked_texts,
) -> tuple[str, bool]:
    """Moda dei prompt CLAP per sezione escludendo le categorie marcate
    (v0.14, INT-2). Se la moda grezza e' un prompt marcato (geografico remoto o
    storico-sociale) ma esistono prompt non marcati, promuove il piu' frequente
    non marcato e segnala la soppressione. Caso B: "Sessantotto" non piu'
    dominante di tutte le sezioni. Ritorna (dominant, marcato).
    """
    def _m(vals: list[str]) -> str:
        counts: dict[str, int] = {}
        for v in vals:
            if v:
                counts[v] = counts.get(v, 0) + 1
        return max(counts.items(), key=lambda kv: kv[1])[0] if counts else ""

    raw = _m(clap_values)
    non_marked = [v for v in clap_values if v and v not in marked_texts]
    if raw in marked_texts and non_marked:
        return _m(non_marked), True
    return raw, bool(raw) and raw in marked_texts


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


def _aggregate_topk_for_window(timeline: list[dict], t_start: float, t_end: float,
                                key: str = "top", k: int = 3,
                                score_min: float = 0.05) -> list[str]:
    """v0.12.6 (P5 caso A): estrae i top-k tag PANNs/CLAP della finestra
    (per score medio) sopra `score_min`. Ritorna lista di etichette ordinate.

    Usato per la sub-segmentazione interna su famiglie geofoniche/biofoniche:
    il segnale di cut e' il cambio del *set* di sub-class fra finestre
    adiacenti, anche quando il top-1 resta invariato (caso doccia -> lavandino:
    top-1 sempre `Water`, ma top-3 cambia da {Water tap, Bathtub} a {Sink}).
    """
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
            score = float(item.get("score", 0.0))
            if score < score_min:
                continue
            scores.setdefault(name, []).append(score)
    if not scores:
        return []
    means = [(n, sum(v) / len(v)) for n, v in scores.items()]
    means.sort(key=lambda nv: -nv[1])
    return [n for n, _ in means[:k]]


def _extract_features_per_window(waveform: np.ndarray, sr: int,
                                   window_seconds: float,
                                   classifier_timeline: list[dict],
                                   clap_timeline: list[dict]) -> list[dict]:
    """Per ogni finestra calcola [rms_db, centroide, flatness, top-1 PANNs,
    top-1 CLAP, top-3 PANNs (v0.12.6)]. Vettore base per il changepoint
    detection globale; il top-3 PANNs alimenta la sub-segmentazione interna
    delle sezioni geofoniche/biofoniche."""
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
        panns_top3 = _aggregate_topk_for_window(
            classifier_timeline, t_start, t_end, key="top",
            k=3, score_min=config.SUBSEGMENT_PANNS_TOP3_SCORE_MIN,
        )
        clap_top1 = _aggregate_top1_for_window(clap_timeline, t_start, t_end, key="tags")
        out.append({
            "t_start_s": t_start,
            "t_end_s": t_end,
            "rms_db": rms_db,
            "centroid_hz": centroid,
            "flatness": flatness,
            "panns_top1": panns_top1,
            "panns_top3": panns_top3,
            "clap_top1": clap_top1,
        })
    return out


def _subsegment_section(section: dict, features: list[dict],
                         window_seconds: float) -> list[dict]:
    """v0.12.6 (P5 caso A): sub-segmenta una sezione lunga su famiglia
    geofonica/biofonica usando il cambiamento del top-3 PANNs nel tempo.

    Algoritmo:
    1. Estrai le finestre `features` interne alla sezione.
    2. Per ogni coppia adiacente calcola Jaccard similarity dei top-3 PANNs.
    3. Cut potenziali dove Jaccard < `SUBSEGMENT_JACCARD_CUT_MAX` (default 0.5).
    4. Vincolo: ciascuna sub-sezione deve durare almeno `window_seconds` * 2
       (cioe' 20 s con window=10s) per evitare frammentazione eccessiva.
    5. Cap a `SUBSEGMENT_MAX_PER_PARENT` (default 3) sub-sezioni; tieni i
       cut con Jaccard piu' basso (massima dissimilarita').

    Ritorna lista di dict con `id_suffix: 'a'|'b'|'c'`, range, dominante,
    aggiornati. Se non ci sono cut significativi, ritorna lista vuota.
    """
    krause = section.get("krause", "")
    duration = section.get("duration_s", 0.0)
    if krause not in config.SUBSEGMENT_FAMILIES:
        return []
    if duration < config.SUBSEGMENT_MIN_PARENT_DURATION_S:
        return []

    t0 = section.get("t_start_s", 0.0)
    t1 = section.get("t_end_s", 0.0)
    inner = [f for f in features if f["t_start_s"] >= t0 and f["t_end_s"] <= t1]
    if len(inner) < 3:
        return []

    def _jaccard(a: list[str], b: list[str]) -> float:
        sa, sb = set(a or []), set(b or [])
        if not sa and not sb:
            return 1.0
        u = sa | sb
        if not u:
            return 1.0
        return len(sa & sb) / len(u)

    # Identifica i candidati di cut: indici interni dove Jaccard < soglia
    candidates: list[tuple[int, float]] = []
    min_distance_windows = 2  # almeno 2 finestre fra cut consecutivi
    for i in range(1, len(inner)):
        j = _jaccard(inner[i - 1]["panns_top3"], inner[i]["panns_top3"])
        if j < config.SUBSEGMENT_JACCARD_CUT_MAX:
            candidates.append((i, j))

    if not candidates:
        return []

    # Tieni i cut con Jaccard piu' basso, rispettando min_distance
    candidates.sort(key=lambda c: c[1])
    max_cuts = config.SUBSEGMENT_MAX_PER_PARENT - 1
    accepted: list[int] = []
    for idx, _ in candidates:
        if any(abs(idx - a) < min_distance_windows for a in accepted):
            continue
        accepted.append(idx)
        if len(accepted) >= max_cuts:
            break
    if not accepted:
        return []
    accepted.sort()

    # Costruisci sub-sezioni
    cuts = [0] + accepted + [len(inner)]
    suffixes = "abcdefgh"
    parent_id = section.get("id", "")
    sub_sections: list[dict] = []
    for k in range(len(cuts) - 1):
        a, b = cuts[k], cuts[k + 1]
        chunk = inner[a:b]
        if not chunk:
            continue
        sub_t0 = chunk[0]["t_start_s"]
        sub_t1 = chunk[-1]["t_end_s"]
        # Top-1 PANNs aggregato (mode) e top-3 unione delle finestre
        def _mode(values: list[str]) -> str:
            counts: dict[str, int] = {}
            for v in values:
                if not v:
                    continue
                counts[v] = counts.get(v, 0) + 1
            if not counts:
                return ""
            return max(counts.items(), key=lambda kv: kv[1])[0]
        dom_panns = _mode([c["panns_top1"] for c in chunk])
        # Le sub-class che caratterizzano la sub-sezione (top-3 per frequenza
        # in finestre interne, esclusa la dominante stessa per evitare
        # ridondanza).
        sub_class_counts: dict[str, int] = {}
        for c in chunk:
            for lbl in (c.get("panns_top3") or []):
                if lbl and lbl != dom_panns:
                    sub_class_counts[lbl] = sub_class_counts.get(lbl, 0) + 1
        top_subclass = sorted(sub_class_counts.items(), key=lambda kv: -kv[1])[:2]
        sub_class_names = [n for n, _ in top_subclass]
        sub_sections.append({
            "id": f"{parent_id}{suffixes[k]}",
            "parent_id": parent_id,
            "t_start_s": round(sub_t0, 2),
            "t_end_s": round(sub_t1, 2),
            "duration_s": round(sub_t1 - sub_t0, 2),
            "dominant_panns": dom_panns,
            "sub_class_top": sub_class_names,
            "krause": krause,  # eredita la famiglia del padre
        })
    return sub_sections


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
    """Genera una stringa breve italiana che descrive la sezione, basata su
    quattro dimensioni: krause x intensita x centroide_banda x onset_density.
    Max ~50 caratteri (vincolo tabella PDF).

    v0.12.6 (P3 caso A): override su sezioni brevissime con
    classificazione PANNs inaffidabile. Se la sezione coincide con un onset
    isolato + decadimento, evita di assegnare Krause antropofonia/biofonia/
    geofonia e ritorna 'impulso e coda'.

    v0.13.0 (P5 caso B, Intervento D dossier P&T): il template a 3
    dimensioni produceva etichette ripetute fra sezioni distinte (S1 e S2
    bar Mamo' entrambe "antropofonia moderata tonale"). Aggiunte le
    dimensioni centroide_banda (4 valori: scura/media/chiara/brillante) e
    onset_density (3 valori: sparsa/media/densa). 3 x 3 x 4 x 3 = 108
    combinazioni utili (escludendo silenzio/impulso che restano fissi).
    onset_density si aggiunge solo se `events_per_sec` e' presente nel
    section (assente -> retrocompatibilita' con l'output v0.12.x).
    """
    krause = section.get("krause", "mista")
    rms_db = section.get("mean_rms_db", -60.0)
    flatness = section.get("mean_flatness", 0.5)
    centroid_hz = section.get("mean_centroid_hz", 0.0)
    events_per_sec = section.get("events_per_sec")
    duration_s = section.get("duration_s", 0.0)
    panns_conf = section.get("dominant_panns_confidence", "high")

    # Sezione molto breve con classificazione inaffidabile: regola di override.
    # Tipico: impulso meccanico finale (caso A S5) o click di stop
    # registrazione, dove PANNs scambia la coda armonica per "Music".
    if duration_s < config.STRUCTURE_PANNS_CONF_LOW_MAX_S and panns_conf == "low":
        return "impulso e coda"

    if rms_db < -50.0 or krause == "silenzio":
        return "quasi-silenzio"

    # Aggettivo dinamico (3 livelli oltre quasi-silenzio)
    if rms_db < -35.0:
        dyn = "soffusa"
    elif rms_db < -20.0:
        dyn = "moderata"
    else:
        dyn = "intensa"

    # Banda centroide (4 valori), via locale_it per coerenza
    from . import locale_it as L
    timbro = L.signature_centroid_band(centroid_hz)

    # Prefisso di famiglia
    if krause in ("biofonia", "antropofonia", "geofonia"):
        prefix = krause
    else:
        prefix = "sezione mista"

    base = f"{prefix} {dyn} {timbro}"

    # Onset density (3 valori) appesa solo se calcolabile. Sotto un piancito
    # minimo di durata (5s) la stima e' rumorosa: in quel caso omettiamo per
    # non introdurre rumore nel label.
    if events_per_sec is not None and duration_s >= 5.0:
        density = L.signature_density(float(events_per_sec))
        candidate = f"{base} {density}"
        if len(candidate) <= 50:
            return candidate

    return base


def _panns_confidence_for_duration(duration_s: float) -> str:
    """v0.12.6 (P3 caso A): mappa durata in confidence del top-1 PANNs.

    Sotto 2s: la classificazione e' costruita su 0-1 frame PANNs (lo schema
    segmenta in finestre da 1s), inaffidabile. Fra 2-5s: cautela. Oltre 5s:
    robusta.
    """
    if duration_s < config.STRUCTURE_PANNS_CONF_LOW_MAX_S:
        return "low"
    if duration_s < config.STRUCTURE_PANNS_CONF_MEDIUM_MAX_S:
        return "medium"
    return "high"


def _events_per_sec_in_section(onset_times: list[float], t_start: float,
                                  t_end: float) -> float:
    """v0.13.0 (Intervento D dossier P&T): conta gli onset cadenti
    nell'intervallo [t_start, t_end) e ritorna la densita' (eventi/sec).
    Ritorna 0.0 se `onset_times` e' vuoto o la durata e' nulla.
    """
    duration = max(t_end - t_start, 1e-6)
    if not onset_times:
        return 0.0
    count = sum(1 for t in onset_times if t_start <= t < t_end)
    return count / duration


def _build_sections(features: list[dict],
                     boundaries: list[int],
                     onset_times: list[float] | None = None) -> list[dict]:
    """Costruisce le sezioni a partire dalle feature per finestra e dai
    confini. Aggrega medie e dominanti per ciascuna sezione.

    v0.13.0: accetta `onset_times` opzionale (lista di timestamp di onset
    in secondi, esposti da spectral.onset_analysis come `events_times_s`)
    per calcolare la densita' locale di onset per sezione. Il campo
    risultante `events_per_sec` alimenta la 4a dimensione di
    `_label_section_signature`.
    """
    n = len(features)
    if n == 0:
        return []
    onset_times = onset_times or []
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
        # v0.14 (INT-2): non promuovere un prompt di categoria marcata come
        # dominante di sezione (caso B "Sessantotto" su tutte le sezioni);
        # usa il piu' frequente non marcato e segnala la soppressione.
        dominant_clap, dominant_clap_marked = _dominant_clap_excluding_marked(
            [f["clap_top1"] for f in chunk], clap_mapping.marked_prompt_texts()
        )
        krause = _krause_from_panns(dominant_panns) if dominant_panns else "mista"
        if mean_rms < -50.0:
            krause = "silenzio"

        # v0.12.6 (P3): confidence sul dominant_panns basata su durata.
        duration = t_end - t_start
        panns_conf = _panns_confidence_for_duration(duration)
        # Quando la classificazione e' inaffidabile, evita di forzare la
        # famiglia Krause antropofonia/biofonia/geofonia (es. impulso 1s
        # classificato Music -> falsa antropofonia). Lascia 'silenzio' se
        # gia' assegnato per RMS.
        if panns_conf == "low" and krause != "silenzio":
            krause = "mista"

        events_per_sec = _events_per_sec_in_section(onset_times, t_start, t_end)

        # Sorgenti simultanee della sezione (Fase 2): top-k PANNs per frequenza
        # nelle finestre interne, dominante inclusa. Additivo, mirror del pattern
        # sub_class_top delle sub-sezioni.
        panns_counts: dict[str, int] = {}
        for f in chunk:
            for lbl in (f.get("panns_top3") or []):
                if lbl:
                    panns_counts[lbl] = panns_counts.get(lbl, 0) + 1
        panns_topk = [n for n, _ in sorted(panns_counts.items(), key=lambda kv: -kv[1])[:4]]

        section = {
            "id": f"S{k + 1}",
            "t_start_s": round(t_start, 2),
            "t_end_s": round(t_end, 2),
            "duration_s": round(duration, 2),
            "mean_rms_db": round(mean_rms, 2),
            "mean_centroid_hz": round(mean_centroid, 1),
            "mean_flatness": round(mean_flatness, 4),
            "events_per_sec": round(events_per_sec, 3),
            "dominant_panns": dominant_panns,
            "panns_topk": panns_topk,
            "dominant_panns_confidence": panns_conf,
            "dominant_clap_prompt": dominant_clap,
            "dominant_clap_marked": dominant_clap_marked,
            "krause": krause,
        }
        section["signature_label"] = _label_section_signature(section)
        sections.append(section)
    return sections


def _annotate_sections_with_hifi_lofi(sections: list[dict], waveform: np.ndarray,
                                         sr: int) -> None:
    """v0.13.0 (Intervento A dossier P&T): popola `hi_fi_lo_fi` per ciascuna
    sezione in-place. Mutate `sections`.

    Strategia: per ogni sezione prende lo slice di waveform sull'intervallo
    [t_start_s, t_end_s], calcola il dynamic_range locale (P95 - P10 dei
    frame RMS via technical.compute_levels), combina con la `mean_flatness`
    gia' calcolata e applica `categoria_hifi` per ottenere label + score.
    Il campo globale `hi_fi_lo_fi` in summary.spectral resta invariato.

    Robustezza: sezioni con slice troppo corto per librosa (sotto ~0.2s,
    raro ma possibile su sub-sezioni) ricadono sul global; la fallback non
    contamina il dato ma evita NaN nella tabella PDF.
    """
    from . import technical as tech_mod
    from . import spectral as spec_mod

    for section in sections:
        t_start = float(section.get("t_start_s", 0.0))
        t_end = float(section.get("t_end_s", 0.0))
        a = max(0, int(t_start * sr))
        b = min(len(waveform), int(t_end * sr))
        if b - a < int(0.2 * sr):
            section["hi_fi_lo_fi"] = None
            continue
        slice_y = waveform[a:b]
        levels = tech_mod.compute_levels(slice_y)
        dr_local = levels.get("dynamic_range_db", 0.0)
        flat_local = float(section.get("mean_flatness", 0.5))
        section["hi_fi_lo_fi"] = spec_mod.hifi_lofi_score(dr_local, flat_local)


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
                "events_per_sec": 0.0,
                "dominant_panns": "",
                "dominant_panns_confidence": _panns_confidence_for_duration(duration_s),
                "dominant_clap_prompt": "",
                "krause": "mista",
                "signature_label": "sezione unica",
            }],
        }

    classifier_timeline = (summary.get("semantic", {}).get("classifier") or {}).get("timeline", [])
    clap_timeline = (summary.get("clap") or {}).get("timeline", [])
    # v0.13.0 (Intervento D dossier P&T): lista degli onset timestamps esposta
    # da spectral.onset_analysis come `events_times_s` in summary.spectral.onsets.
    # La passiamo a _build_sections per calcolare `events_per_sec` per sezione.
    onset_times = ((summary.get("spectral") or {}).get("onsets") or {}).get("events_times_s") or []

    features = _extract_features_per_window(
        waveform, sr, window_seconds, classifier_timeline, clap_timeline
    )
    boundaries = _detect_changepoints(features, window_seconds)
    sections = _build_sections(features, boundaries, onset_times=onset_times)

    # v0.13.0 (Intervento A dossier P&T): hi-fi/lo-fi per sezione. Riusa
    # compute_levels su slice di waveform per dynamic_range locale, combinato
    # con mean_flatness gia' presente. Necessario per soundscape con marcata
    # variabilita' strutturale (caso B bar Mamo': S1 distinguibile,
    # S2 chiacchiericcio infittito, S3 ricostruito hi-fi).
    if config.HIFI_LOFI_PER_SECTION:
        _annotate_sections_with_hifi_lofi(sections, waveform, sr)

    # v0.12.6 (P5 caso A): secondo passo di sub-segmentazione interna
    # sulle sezioni geofoniche/biofoniche lunghe, usando il cambio del top-3
    # PANNs nel tempo. Le sub-sezioni si aggiungono alla lista padre con id
    # "S3a", "S3b" etc., preservando la sezione padre come record di alto
    # livello (gli agenti che leggono solo le S1..Sn continuano a funzionare).
    sub_sections_all: list[dict] = []
    for s in sections:
        sub = _subsegment_section(s, features, window_seconds)
        if sub:
            s["has_sub_sections"] = True
            s["sub_sections"] = sub
            sub_sections_all.extend(sub)

    return {
        "enabled": True,
        "n_sections": len(sections),
        "n_sub_sections": len(sub_sections_all),
        "window_seconds": window_seconds,
        "sections": sections,
    }
