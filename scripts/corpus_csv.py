"""Estrazione tabellare da un corpus di summary (v0.20.0, P3 addendum
heritage, lezione 7).

Appiattisce i `*_summary.json` di una cartella (ricorsiva) in un CSV per
campione, con aggregazione mediana per gruppo opzionale. Terzo caso d'uso
reale che rilegge i summary in massa (dopo la PWA Annotation Atelier e i
prototipi del caso heritage), prima risolto ogni volta con uno script
esterno.
"""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

# Campi numerici aggregati per mediana nel CSV di gruppo.
CAMPI_NUMERICI = [
    "durata_s", "lufs", "lra", "true_peak_db", "crest_db",
    "dynamic_range_db", "centroide_hz", "spread_hz", "rolloff_hz",
    "flatness", "flux", "zcr", "onset_per_s", "hifi_score_5",
    "aci", "ndsi", "h_totale", "bi", "panns_score", "clap_score",
]


def _mediana(valori: list) -> float | None:
    puliti = [v for v in valori if isinstance(v, (int, float))]
    return round(statistics.median(puliti), 3) if puliti else None


def _primo(lista, campo_nome="name", campo_score="score"):
    if isinstance(lista, list) and lista:
        v = lista[0]
        if isinstance(v, dict):
            nome = (v.get(campo_nome) or v.get("name") or v.get("label")
                    or v.get("tag") or v.get("prompt"))
            return nome, v.get(campo_score) or v.get("prob") or v.get("value")
    return None, None


def estrai_campione(summary: dict) -> dict:
    """Appiattisce un summary nei campi tabellari (stessa selezione del
    prototipo aggrega.py della campagna heritage, piu' versione e impronta
    del checkpoint)."""
    tec = summary.get("technical") or {}
    spet = summary.get("spectral") or {}
    eco = summary.get("ecoacoustic") or {}
    sem = (summary.get("semantic") or {}).get("classifier") or {}
    clap = summary.get("clap") or {}
    hint = clap.get("academic_hints") or {}

    panns_nome, panns_score = _primo(sem.get("top_global"))
    clap_nome, clap_score = _primo(clap.get("top_global"), "prompt")
    top5 = "|".join(str(v.get("name")) for v in (sem.get("top_global") or [])[:5])

    def _dominante(campo: str):
        d = hint.get(campo)
        if isinstance(d, dict):
            dom = d.get("dominant")
            if isinstance(dom, dict):
                return dom.get("value")
            return dom
        return None

    gate = (eco.get("domain_gate") or {})
    return {
        "durata_s": (summary.get("metadata") or {}).get("duration_s"),
        "lufs": (tec.get("lufs") or {}).get("integrated_lufs"),
        "lra": (tec.get("lufs") or {}).get("lra"),
        "true_peak_db": (tec.get("lufs") or {}).get("true_peak_db"),
        "crest_db": (tec.get("levels") or {}).get("crest_db"),
        "dynamic_range_db": (tec.get("levels") or {}).get("dynamic_range_db"),
        "centroide_hz": (spet.get("timbre") or {}).get("spectral_centroid_hz"),
        "spread_hz": (spet.get("timbre") or {}).get("spectral_spread_hz"),
        "rolloff_hz": (spet.get("timbre") or {}).get("spectral_rolloff_hz"),
        "flatness": (spet.get("timbre") or {}).get("spectral_flatness"),
        "flux": (spet.get("timbre") or {}).get("spectral_flux"),
        "zcr": (spet.get("timbre") or {}).get("zero_crossing_rate"),
        "onset_per_s": (spet.get("onsets") or {}).get("events_per_sec"),
        "hifi_score_5": (spet.get("hifi_lofi") or {}).get("score_5"),
        "aci": eco.get("aci"),
        "ndsi": (eco.get("ndsi") or {}).get("ndsi"),
        "h_totale": (eco.get("h_entropy") or {}).get("h_total"),
        "bi": eco.get("bi"),
        "eco_fuori_dominio": int(bool(gate.get("out_of_domain"))),
        "panns_top": panns_nome,
        "panns_score": panns_score,
        "panns_top5": top5,
        "clap_top": clap_nome,
        "clap_score": clap_score,
        "krause_dominante": _dominante("krause"),
        "schafer_ruolo": _dominante("schafer_role"),
        "skill_version": summary.get("version"),
        "checkpoint_sha256": clap.get("checkpoint_sha256", ""),
    }


def run_tabulate(
    root: Path,
    output_dir: Path | None = None,
    group_by_parent: bool = False,
    group_map: dict[str, str] | None = None,
) -> dict:
    """Corpus di summary -> CSV per campione (+ aggregato per gruppo).

    `group_by_parent` raggruppa per cartella madre del summary;
    `group_map` mappa chiave (stem esatto o prefisso) -> gruppo.
    Ritorna i path scritti. I summary illeggibili sono contati e dichiarati,
    mai saltati in silenzio.
    """
    from .vocab_eval import match_truth

    root = Path(root)
    righe: list[dict] = []
    illeggibili = 0
    for sommario in sorted(root.glob("**/*_summary.json")):
        try:
            dati = json.loads(sommario.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            illeggibili += 1
            continue
        sid = sommario.name.replace("_summary.json", "")
        riga = {
            "id": sid,
            "rel": str(sommario.relative_to(root)),
            "cartella": sommario.parent.name if sommario.parent != root else "",
            **estrai_campione(dati),
        }
        if group_map is not None:
            riga["gruppo"] = match_truth(sid, group_map) or ""
        elif group_by_parent:
            riga["gruppo"] = riga["cartella"]
        righe.append(riga)

    if illeggibili:
        print(f"summary illeggibili, esclusi e dichiarati: {illeggibili}")
    if not righe:
        raise ValueError(f"nessun summary trovato sotto {root}")

    out_dir = Path(output_dir) if output_dir else root / "tabelle"
    out_dir.mkdir(parents=True, exist_ok=True)
    scritti = {}

    campioni_path = out_dir / "corpus_campioni.csv"
    with campioni_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(righe[0].keys()),
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(righe)
    print(f"scritto {campioni_path} ({len(righe)} righe)")
    scritti["campioni"] = campioni_path

    if group_map is not None or group_by_parent:
        per_gruppo: dict[str, list[dict]] = defaultdict(list)
        for r in righe:
            if r.get("gruppo"):
                per_gruppo[r["gruppo"]].append(r)
        senza_gruppo = sum(1 for r in righe if not r.get("gruppo"))
        if senza_gruppo:
            print(f"campioni senza gruppo, fuori dall'aggregato: {senza_gruppo}")
        righe_gruppi = []
        for gruppo, membri in sorted(per_gruppo.items(),
                                     key=lambda kv: -len(kv[1])):
            voce = {"gruppo": gruppo, "campioni": len(membri)}
            for campo in CAMPI_NUMERICI:
                voce[campo] = _mediana([m.get(campo) for m in membri])
            classi = [m.get("panns_top") for m in membri if m.get("panns_top")]
            voce["panns_prevalente"] = (max(set(classi), key=classi.count)
                                        if classi else None)
            voce["panns_classi_distinte"] = len(set(classi))
            voce["eco_fuori_dominio_pct"] = round(
                100 * sum(m.get("eco_fuori_dominio", 0) for m in membri)
                / len(membri), 1)
            righe_gruppi.append(voce)
        if righe_gruppi:
            gruppi_path = out_dir / "corpus_gruppi.csv"
            with gruppi_path.open("w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(righe_gruppi[0].keys()))
                w.writeheader()
                w.writerows(righe_gruppi)
            print(f"scritto {gruppi_path} ({len(righe_gruppi)} gruppi)")
            scritti["gruppi"] = gruppi_path

    return {k: str(v) for k, v in scritti.items()}
