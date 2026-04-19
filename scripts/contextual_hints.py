"""Suggerimenti contestuali di parentela (v0.7.3).

Motivazione: v0.7.2 aveva aggiunto al prompt agente una lista piatta di scuole
contemporanee. Ha funzionato sui brani prima scarsi ma ha causato regressione
sui brani dove la skill era già buona (Ferrari -13, Winderen -10, Lopez -9).
Pattern di non-monotonicità dell'LLM agent già osservato in v0.6.9.

Soluzione v0.7.3: invece di un prompt monolitico, selezionare le parentele
**condizionalmente** in base ai marker acustici effettivamente presenti nel
payload. Ogni regola ispeziona campi specifici e restituisce un suggerimento
solo quando i marker coincidono. Risultato: prompt più corto, focalizzato,
che non distrae su casi dove la skill già funziona.

Regole implementate (tutte evidence-based su pattern osservati nel corpus
golden v1):

- R1 underwater: idrofono + biofonia marina (Winderen/Watson/Lockwood)
- R2 contact_mic_ice: geofonia pura + durata lunga (Watson/Köner)
- R3 urban_drone: hum + antropofonia + dinamica compressa (Nilsen/López)
- R4 sonic_journalism: durata >40min + mix biofonia/antropofonia + parlato
  inglese (Cusack/CRiSAP)
- R5 drone_metal: flatness bassa + marker metal PANNs + durata lunga (Earth/
  Sunn O)))/Boris; López *Untitled #104* atipico)
- R6 river_long: materiali acquatici + durata >60min (Lockwood/Oliveros)
- R7 hum_no_fonologia: hum 50Hz presente ma speech non-italiano (contro-
  regola: evita attribuzione automatica a Fonologia RAI)

Design: se nessuna regola matcha, il prompt non riceve blocco hints
(comportamento v0.7.1 preservato).
"""
from __future__ import annotations


def _top_names(items: list | None, k: int = 10) -> set[str]:
    if not items:
        return set()
    out = set()
    for x in items[:k]:
        name = x.get("name", "") if isinstance(x, dict) else ""
        if name:
            out.add(str(name).lower())
    return out


def _clap_prompts_lower(items: list | None, k: int = 20) -> list[str]:
    if not items:
        return []
    out = []
    for x in items[:k]:
        p = x.get("prompt", "") if isinstance(x, dict) else ""
        if p:
            out.append(str(p).lower())
    return out


def _has_hum_at(data: dict, target_hz: int) -> bool:
    """Rileva hum alla frequenza target. Supporta sia summary.json (hum.peaks
    dettagliati) che agent_payload.json (technical.hum_overall stringa)."""
    peaks = (data.get("hum", {}) or {}).get("peaks", []) or []
    if peaks:
        for p in peaks:
            if p.get("target_hz") == target_hz and p.get("verdict") == "presente":
                if float(p.get("ratio_db", 0) or 0) > 2.5:
                    return True
        return False
    # payload ridotto: solo technical.hum_overall
    overall = ((data.get("technical") or {}).get("hum_overall") or "").lower()
    return overall == "presente"


def _duration_s(data: dict) -> float:
    md = data.get("metadata") or {}
    if md.get("duration_s") is not None:
        return float(md.get("duration_s") or 0)
    # payload ridotto: file.duration_s o signature.duration_s
    f = data.get("file") or {}
    if f.get("duration_s") is not None:
        return float(f.get("duration_s") or 0)
    sig = data.get("signature") or {}
    return float(sig.get("duration_s", 0) or 0)


def _speech_lang(data: dict) -> str:
    sp = data.get("speech") or {}
    if sp.get("language_detected"):
        return str(sp.get("language_detected") or "")
    # payload signature.speech_presence.language_detected
    sig_speech = (data.get("signature") or {}).get("speech_presence") or {}
    return str(sig_speech.get("language_detected", "") or "")


def _speech_ratio(data: dict) -> float:
    sp = data.get("speech") or {}
    v = sp.get("duration_speech_ratio")
    if v is not None:
        return float(v)
    # payload ridotto: duration_speech_s / duration_total_s
    dur_sp = sp.get("duration_speech_s")
    dur_tot = sp.get("duration_total_s")
    if dur_sp and dur_tot:
        try:
            return float(dur_sp) / float(dur_tot)
        except Exception:  # noqa: BLE001
            return 0.0
    return 0.0


def _flatness(data: dict) -> float:
    sp = data.get("spectral") or {}
    # payload ridotto: spectral.flatness
    if "flatness" in sp:
        return float(sp.get("flatness") or 0.5)
    # summary: spectral.timbre.spectral_flatness
    return float((sp.get("timbre") or {}).get("spectral_flatness", 0.5) or 0.5)


def _onset_per_s(data: dict) -> float:
    return float(((data.get("spectral") or {}).get("onsets") or {}).get("events_per_sec", 0) or 0)


def _dynamic_range(data: dict) -> float:
    tech = data.get("technical") or {}
    # payload ridotto: technical.dynamic_range_db
    if "dynamic_range_db" in tech:
        return float(tech.get("dynamic_range_db", 30) or 30)
    # summary: technical.levels.dynamic_range_db
    return float((tech.get("levels") or {}).get("dynamic_range_db", 30) or 30)


def _ndsi(data: dict) -> float:
    eco = data.get("ecoacoustic") or {}
    n = eco.get("ndsi")
    if n is None:
        return 0.0
    # summary: dict con chiave "ndsi"; payload ridotto: float direttamente
    if isinstance(n, dict):
        return float(n.get("ndsi", 0) or 0)
    return float(n or 0)


def _structure_n(data: dict) -> int:
    return int((data.get("structure") or {}).get("n_sections", 0) or 0)


def _classifier(data: dict) -> dict:
    """Ritorna il blocco classifier normalizzato.

    summary: semantic.classifier; payload ridotto: classifier (top-level)."""
    sem = (data.get("semantic") or {}).get("classifier")
    if sem:
        return sem
    return data.get("classifier") or {}


def _check_underwater(summary: dict) -> tuple[bool, str]:
    cls = _classifier(summary)
    panns_dom = _top_names(cls.get("top_dominant_frames"), 15)
    panns_global = _top_names(cls.get("top_global"), 10)
    clap = _clap_prompts_lower((summary.get("clap") or {}).get("top_global"), 20)
    underwater_panns_direct = {
        "whale vocalization", "underwater sound", "dolphin", "porpoise",
    } & (panns_dom | panns_global)
    fluid_panns = {"water", "stream", "pour", "splash, splatter", "gurgling", "drip"} & (panns_dom | panns_global)
    underwater_clap = any(
        kw in p for p in clap
        for kw in ("idrofon", "subacqu", "fondal", "crostace", "balena", "cetace", "gamberett", "merluzz")
    )
    if underwater_panns_direct or (underwater_clap and fluid_panns):
        return True, (
            "Materiale con evidenza subacquea/idrofono (PANNs: "
            f"{sorted(underwater_panns_direct | fluid_panns)[:3]}; "
            f"CLAP underwater: {underwater_clap}). "
            "Parentela forte: Jana Winderen (*Energy Field*, Touch 2010, Mar di Barents); "
            "Chris Watson (sezione idrofono in *Vatnajökull*); "
            "Annea Lockwood (*Sound Map* fluviali, idrofono continuo)."
        )
    return False, ""


def _check_contact_mic_ice(summary: dict) -> tuple[bool, str]:
    cls = _classifier(summary)
    panns_dom = _top_names(cls.get("top_dominant_frames"), 15)
    panns_global = _top_names(cls.get("top_global"), 10)
    cold_panns = {"wind", "rumble", "crackling fire", "crumpling crinkling", "ice"} & (panns_dom | panns_global)
    dur = _duration_s(summary)
    if len(cold_panns) >= 2 and _speech_ratio(summary) < 0.05 and dur >= 600:
        msg = (
            f"Lunga geofonia con marker freddo/strutturale (PANNs: {sorted(cold_panns)[:3]}) "
            f"e parlato assente. Durata {dur/60:.0f} min. "
            "Parentela forte: Chris Watson (*Vatnajökull*, *Weather Report*, Touch 2003, "
            "contact microphone + idrofono); Thomas Köner (*Permafrost* 1993, *Nuuk* 1997, drone glaciale)."
        )
        return True, msg
    return False, ""


def _check_urban_drone(summary: dict) -> tuple[bool, str]:
    has_50 = _has_hum_at(summary, 50)
    has_100 = _has_hum_at(summary, 100)
    cls = _classifier(summary)
    panns_dom = _top_names(cls.get("top_dominant_frames"), 15)
    panns_global = _top_names(cls.get("top_global"), 10)
    urban_panns = {
        "traffic noise, roadway noise", "vehicle", "engine", "mechanisms",
        "inside, large room or hall", "hum"
    } & (panns_dom | panns_global)
    dr = _dynamic_range(summary)
    ndsi = _ndsi(summary)
    lang = _speech_lang(summary)
    # evita di triggerare su brani italiani: questo è per Nilsen/López NON Nono
    if (has_50 or has_100) and urban_panns and dr < 25 and ndsi < 0 and lang != "it":
        msg = (
            f"Hum di rete + antropofonia urbana (PANNs: {sorted(urban_panns)[:2]}) "
            f"+ dinamica compressa (DR {dr:.0f} dB) + NDSI {ndsi:.2f}, speech non italiano. "
            "Parentela forte: BJ Nilsen (*The Invisible City*, Touch 2010); "
            "Francisco López (drone-field urbano); Thomas Köner (dark ambient)."
        )
        return True, msg
    return False, ""


def _check_sonic_journalism(summary: dict) -> tuple[bool, str]:
    dur = _duration_s(summary)
    cls = _classifier(summary)
    panns_dom = _top_names(cls.get("top_dominant_frames"), 15)
    has_speech = "speech" in panns_dom
    has_fauna = bool({"bird", "animal", "insect", "frog", "fowl", "owl", "chirp, tweet"} & panns_dom)
    has_vehicle = bool({"vehicle", "train", "boat, water vehicle"} & panns_dom)
    lang = _speech_lang(summary)
    structure_n = _structure_n(summary)
    # atlante microritratti: durata lunga + mix biofonia/antropofonia + parlato presente
    if dur >= 2400 and has_speech and has_fauna and has_vehicle and lang in ("en", "", "unknown") and structure_n >= 5:
        msg = (
            f"Atlante documentario lungo ({dur/60:.0f} min) con mix di parlato, biofonia, "
            f"antropofonia veicolare e {structure_n} sezioni strutturali. Parlato non italiano. "
            "Parentela forte: Peter Cusack (*Sounds from Dangerous Places*, *Favourite Sounds of London*), "
            "area CRiSAP / London Sound Survey; "
            "Luc Ferrari *Far-West News* per il formato diaristico esteso."
        )
        return True, msg
    return False, ""


def _check_drone_metal(summary: dict) -> tuple[bool, str]:
    cls = _classifier(summary)
    panns_dom = _top_names(cls.get("top_dominant_frames"), 15)
    panns_global = _top_names(cls.get("top_global"), 10)
    all_panns = panns_dom | panns_global
    metal_markers = {
        "heavy metal", "punk rock", "progressive rock", "angry music",
        "guitar", "electric guitar", "rock music", "music"
    } & all_panns
    hard_markers = {"heavy metal", "punk rock", "progressive rock", "angry music"} & all_panns
    dur = _duration_s(summary)
    # hard markers richiesti: almeno 3 dei 4 hard markers (evita falsi positivi su
    # materiali dove uno solo affiora con score basso)
    if len(hard_markers) >= 3 and dur >= 1500:
        msg = (
            f"Marker rock-metal forti in PANNs ({sorted(hard_markers)}), durata {dur/60:.0f} min. "
            "Parentela forte: Earth (*Earth 2*, 1993), Sunn O))) (*Black One*, *Monoliths*), "
            "Boris (modalità statiche). Francisco López *Untitled #104* come caso atipico di "
            "absolute concrete music applicata al materiale metal."
        )
        return True, msg
    return False, ""


def _check_river_long(summary: dict) -> tuple[bool, str]:
    cls = _classifier(summary)
    panns_global = _top_names(cls.get("top_global"), 10)
    panns_dom = _top_names(cls.get("top_dominant_frames"), 15)
    water_markers = {
        "water", "stream", "pour", "splash, splatter", "gurgling",
        "boat, water vehicle", "rowboat, canoe, kayak"
    } & (panns_global | panns_dom)
    dur = _duration_s(summary)
    structure_n = _structure_n(summary)
    if len(water_markers) >= 3 and dur >= 3600 and structure_n >= 6:
        msg = (
            f"Materiali acquatici multipli (PANNs: {sorted(water_markers)[:3]}), "
            f"durata {dur/60:.0f} min, {structure_n} sezioni strutturali. "
            "Parentela forte: Annea Lockwood (*Sound Map of the Hudson*, *Danube*, *Housatonic*, "
            "Lovely Music 1982-2010, idrofono fluviale); "
            "area deep listening (Pauline Oliveros)."
        )
        return True, msg
    return False, ""


def _check_hum_without_fonologia(summary: dict) -> tuple[bool, str]:
    has_hum = _has_hum_at(summary, 50) or _has_hum_at(summary, 100)
    lang = _speech_lang(summary)
    dur = _duration_s(summary)
    if has_hum and lang and lang != "it" and dur > 120:
        msg = (
            f"Hum 50/100 Hz presente MA speech detectato in lingua '{lang}' (non italiano). "
            "NON attribuire automaticamente alla Fonologia RAI: l'hum di rete è comune a qualunque "
            "catena analogica europea. Pesa piuttosto scuole Touch (Nilsen/Watson/Köner), dark "
            "ambient, drone-field contemporaneo."
        )
        return True, msg
    return False, ""


CHECKS = (
    ("underwater", _check_underwater),
    ("contact_mic_ice", _check_contact_mic_ice),
    ("urban_drone", _check_urban_drone),
    ("sonic_journalism", _check_sonic_journalism),
    ("drone_metal", _check_drone_metal),
    ("river_long", _check_river_long),
    ("hum_no_fonologia", _check_hum_without_fonologia),
)


def build_hints(summary: dict) -> str:
    """Restituisce blocco markdown condizionato ai segnali del payload.

    Selezione dinamica: attiva SOLO le regole che matchano effettivamente il
    materiale. Se nessuna matcha, restituisce stringa vuota e il prompt resta
    quello base (comportamento v0.7.1 preservato).
    """
    hints: list[str] = []
    for _name, check in CHECKS:
        ok, msg = check(summary)
        if ok:
            hints.append(f"- {msg}")
    if not hints:
        return ""
    header = (
        "\n## Suggerimenti contestuali di parentela (v0.7.3)\n\n"
        "Le parentele seguenti sono state pre-selezionate automaticamente dal "
        "payload in base ai marker acustici effettivamente presenti. NON "
        "sostituiscono il tuo giudizio: considerale **ipotesi forti** da "
        "pesare contro gli altri indicatori (flatness, centroide, Schaeffer "
        "detail, lingua del parlato). Se contraddicono segnali più robusti, "
        "ignorale esplicitamente in \"Parentele stilistiche\".\n\n"
    )
    return header + "\n".join(hints) + "\n"


def which_fired(summary: dict) -> list[str]:
    """Utility per test e ispezione: ritorna la lista dei nomi delle regole attivate."""
    fired = []
    for name, check in CHECKS:
        ok, _ = check(summary)
        if ok:
            fired.append(name)
    return fired
