"""Valutazione onesta di vocabolari CLAP su un corpus di summary (v0.20.0).

Industrializza i tre prototipi della campagna heritage (lezioni 8 e 9
dell'addendum): esperimento sui vocabolari, stratificazione per forma
acustica, McNemar esatto appaiato. Il principio e' che il valutatore deve
rendere difficile ingannarsi da soli:

- split OBBLIGATORIO fra dati di sviluppo e dati di valutazione, con
  rifiuto esplicito se coincidono o mancano;
- stratificazione per forma acustica (proxy a zero parametri da PANNs,
  oppure scheda di ascolto compilata quando c'e'), perche' i numeri
  aggregati mescolano materiale attribuibile e palinsesto non pertinente;
- misura della concentrazione delle predizioni (quota della classe modale,
  entropia normalizzata): l'effetto calamita si deve denunciare da solo;
- quota dei campioni fuori criterio di durata SEMPRE riportata;
- rifiuto di confrontare embedding audio e dei prompt prodotti da
  checkpoint diversi (campo checkpoint_sha256 nel blocco clap).

Gli embedding audio arrivano dai summary (`clap.embeddings_audio_b64`),
quindi provare un vocabolario nuovo non richiede di ricatturare l'audio.
"""
from __future__ import annotations

import base64
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from . import config

# Ramo `Singing` di AudioSet piu' i nodi vocali di genere, scelto
# sull'ontologia e non sui dati (zero parametri tarati; validato contro
# l'ascolto umano con kappa 0,842 nella campagna heritage). `Song` e
# `Gospel music` restano fuori di proposito: il primo e' un nodo di genere
# generico, il secondo e' legato a una sola tradizione e sbilancerebbe la
# misura.
CLASSI_VOCALI = {
    "Singing", "Choir", "Yodeling", "Chant", "Mantra",
    "Male singing", "Female singing", "Child singing", "Synthetic singing",
    "Rapping", "Humming", "Opera", "Vocal music", "A capella",
}
CLASSI_PARLATO = {"Speech", "Conversation", "Narration, monologue",
                  "Male speech, man speaking", "Female speech, woman speaking",
                  "Child speech, kid speaking", "Speech synthesizer"}

# Forme della scheda di ascolto -> tre gruppi dell'indicatore.
GRUPPO_UMANO = {
    "recitazione_cantillata": "cantabile",
    "canto_a_cappella": "cantabile",
    "canto_con_strumenti": "cantabile",
    "musica_strumentale": "musicale",
    "parlato": "parlato",
    "parlato_su_musica": "parlato",
    "sigla_pubblicita": "musicale",
    "altro": "musicale",
}
GRUPPI = ("cantabile", "musicale", "parlato")

# Etichetta di categoria riservata ai prompt distrattori: esclusi dalla
# classifica, usati per il margine.
DISTRATTORE = "_distrattore"


class VocabEvalError(ValueError):
    """Errore di protocollo della valutazione (split, checkpoint, input)."""


# ------------------------------------------------------------------ forma

def forma_proxy(top5: list[str]) -> str:
    """Indicatore di forma acustica a priori sull'ontologia AudioSet."""
    if not top5:
        return "ignoto"
    if top5[0] in CLASSI_PARLATO:
        return "parlato"
    if any(c in CLASSI_VOCALI for c in top5):
        return "cantabile"
    return "musicale"


def cohen_kappa(a: list[str], b: list[str]) -> float:
    """Cohen's kappa su etichette nominali."""
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


# ---------------------------------------------------------------- mcnemar

def mcnemar_esatto(solo_a: int, solo_b: int) -> float:
    """p a due code dal binomiale sui soli discordanti (niente scipy,
    nessuna approssimazione asintotica)."""
    n = solo_a + solo_b
    if n == 0:
        return 1.0
    atteso = n / 2
    coda = 0.0
    for k in range(n + 1):
        p = math.comb(n, k) / 2 ** n
        if abs(k - atteso) >= abs(solo_a - atteso) - 1e-12:
            coda += p
    return min(1.0, coda)


# ------------------------------------------------------------- estrazione

_DATA_RE = re.compile(r"(\d{8})")


def _data_campione(summary_path: Path, root: Path) -> str:
    """Prima sequenza AAAAMMGG nel path relativo (cartella o nome file)."""
    rel = summary_path.relative_to(root)
    m = _DATA_RE.search(str(rel))
    return m.group(1) if m else ""


def carica_campioni(root: Path) -> tuple[list[dict], dict]:
    """Legge ricorsivamente i `*_summary.json` sotto root.

    Ritorna (campioni, diagnostica). Ogni campione: id (stem senza suffisso),
    rel (path relativo), data (AAAAMMGG dal path, vuota se assente), emb
    (matrice float32 segmenti x dim), panns_top5 (lista di nomi classe),
    durata_s, checkpoint_sha256 (vuoto nei summary pre-v0.20).
    """
    root = Path(root)
    campioni: list[dict] = []
    senza_embedding = 0
    for sommario in sorted(root.glob("**/*_summary.json")):
        try:
            d = json.loads(sommario.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            senza_embedding += 1
            continue
        clap = d.get("clap") or {}
        b64 = clap.get("embeddings_audio_b64")
        if not b64:
            senza_embedding += 1
            continue
        forma = clap.get("embeddings_shape") or [[0, 0]]
        emb = np.frombuffer(base64.b64decode(b64), dtype=np.float16).astype(np.float32)
        emb = emb.reshape(tuple(forma[0]))
        sem = ((d.get("semantic") or {}).get("classifier") or {}).get("top_global") or []
        campioni.append({
            "id": sommario.name.replace("_summary.json", ""),
            "rel": str(sommario.relative_to(root)),
            "data": _data_campione(sommario, root),
            "emb": emb,
            "panns_top5": [v.get("name") for v in sem[:5]],
            "durata_s": (d.get("metadata") or {}).get("duration_s"),
            "checkpoint_sha256": clap.get("checkpoint_sha256", ""),
        })
    diagnostica = {"summary_senza_embedding": senza_embedding}
    return campioni, diagnostica


def load_truth(path: Path) -> dict[str, str]:
    """CSV con colonne id (o chiave/stazione) ed etichetta (o label).

    La chiave puo' essere lo stem esatto del file oppure un suo prefisso
    (es. il nome della stazione senza timestamp).
    """
    righe = list(csv.DictReader(Path(path).open(encoding="utf-8")))
    if not righe:
        raise VocabEvalError(f"file di verita' vuoto: {path}")
    campi = righe[0].keys()
    col_id = next((c for c in ("id", "chiave", "stazione") if c in campi), None)
    col_lab = next((c for c in ("etichetta", "label", "tradizione") if c in campi), None)
    if not col_id or not col_lab:
        raise VocabEvalError(
            f"il CSV di verita' deve avere colonne id/chiave/stazione ed "
            f"etichetta/label/tradizione, trovate: {sorted(campi)}"
        )
    return {r[col_id].strip(): r[col_lab].strip() for r in righe if r.get(col_id)}


def match_truth(sample_id: str, truth: dict[str, str]) -> str | None:
    """Match esatto sullo stem, poi il prefisso piu' lungo."""
    if sample_id in truth:
        return truth[sample_id]
    best = ""
    for k in truth:
        if sample_id.startswith(k) and len(k) > len(best):
            best = k
    return truth[best] if best else None


def load_sheet(path: Path) -> dict[str, str]:
    """Scheda di ascolto compilata: colonne id (o stazione) e forma.

    Accetta sia i tre gruppi dell'indicatore sia le otto forme della scheda
    di ascolto della campagna heritage (mappate con GRUPPO_UMANO).
    """
    righe = list(csv.DictReader(Path(path).open(encoding="utf-8")))
    if not righe:
        raise VocabEvalError(f"scheda vuota: {path}")
    campi = righe[0].keys()
    col_id = next((c for c in ("id", "chiave", "stazione") if c in campi), None)
    if not col_id or "forma" not in campi:
        raise VocabEvalError(
            f"la scheda deve avere colonne id/stazione e forma, trovate: {sorted(campi)}"
        )
    out: dict[str, str] = {}
    for r in righe:
        forma = (r.get("forma") or "").strip()
        if not forma:
            continue
        if forma in GRUPPI:
            out[r[col_id].strip()] = forma
        elif forma in GRUPPO_UMANO:
            out[r[col_id].strip()] = GRUPPO_UMANO[forma]
        else:
            ammessi = sorted(set(GRUPPI) | set(GRUPPO_UMANO))
            raise VocabEvalError(
                f"forma '{forma}' non riconosciuta nella scheda; ammesse: {ammessi}"
            )
    return out


# ------------------------------------------------------------ valutazione

def _normalizza(a: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    return a / np.clip(n, 1e-8, None)


def evaluate_vocab(campioni: list[dict], vocab: dict,
                   prompt_emb: np.ndarray) -> list[dict]:
    """Punteggi per campione con un vocabolario normalizzato.

    Il punteggio di una classe e' il suo prompt migliore (max). I prompt di
    categoria `_distrattore` sono esclusi dalla classifica e usati per il
    margine; senza distrattori il margine e' sul secondo classificato.
    """
    prompts = vocab["prompts"]
    categorie = [p.get("category", "") for p in prompts]
    prompt_emb = _normalizza(np.asarray(prompt_emb, dtype=np.float32))

    righe = []
    for c in campioni:
        audio = _normalizza(c["emb"]).mean(axis=0)
        audio = audio / max(float(np.linalg.norm(audio)), 1e-8)
        sim = prompt_emb @ audio

        punteggi: dict[str, float] = {}
        for cat in set(categorie):
            valori = [float(s) for s, cc in zip(sim, categorie) if cc == cat]
            punteggi[cat] = max(valori)
        ordinate = sorted(punteggi.items(), key=lambda kv: -kv[1])
        classifica = [(t, s) for t, s in ordinate if t != DISTRATTORE]
        if not classifica:
            raise VocabEvalError("vocabolario con soli prompt distrattori")

        top1, top1_score = classifica[0]
        top3 = [t for t, _ in classifica[:3]]
        if DISTRATTORE in punteggi:
            margine = top1_score - punteggi[DISTRATTORE]
        elif len(classifica) > 1:
            margine = top1_score - classifica[1][1]
        else:
            margine = 0.0

        vera = c.get("etichetta_vera") or ""
        righe.append({
            "id": c["id"],
            "rel": c["rel"],
            "data": c["data"],
            "durata_s": c["durata_s"],
            "gruppo": c.get("gruppo", ""),
            "etichetta_vera": vera,
            "top1": top1,
            "top1_score": round(top1_score, 4),
            "top1_corretto": int(bool(vera) and top1 == vera),
            "top3": "|".join(top3),
            "top3_corretto": int(bool(vera) and vera in top3),
            "margine": round(margine, 4),
        })
    return righe


def concentrazione(predizioni: list[str], n_classi: int) -> dict:
    """Quota della classe modale ed entropia normalizzata delle top-1."""
    if not predizioni:
        return {"n": 0, "classe_modale": "", "quota_modale": 0.0,
                "entropia_norm": float("nan"), "warning": False}
    conte = Counter(predizioni)
    modale, n_modale = conte.most_common(1)[0]
    tot = len(predizioni)
    quota = n_modale / tot
    if n_classi > 1:
        h = -sum((v / tot) * math.log(v / tot) for v in conte.values())
        h_norm = h / math.log(n_classi)
    else:
        h_norm = float("nan")
    warning = quota > config.VOCAB_EVAL_MODAL_SHARE_WARN or (
        not math.isnan(h_norm) and h_norm < config.VOCAB_EVAL_ENTROPY_NORM_WARN
    )
    return {"n": tot, "classe_modale": modale, "quota_modale": round(quota, 3),
            "entropia_norm": round(h_norm, 3) if not math.isnan(h_norm) else "",
            "warning": warning}


# --------------------------------------------------------------- verifiche

def verifica_split(campioni: list[dict], eval_da: str | None,
                   eval_match: str | None, vocab_a: dict,
                   vocab_b: dict | None) -> list[dict]:
    """Applica la selezione di valutazione e rifiuta i protocolli disonesti."""
    if not eval_da and not eval_match:
        raise VocabEvalError(
            "split obbligatorio: indica --eval-da AAAAMMGG oppure --eval-match "
            "REGEX. Valutare un vocabolario sui dati su cui e' stato scritto "
            "produce numeri non credibili (protocollo antioverfitting)."
        )
    if eval_da and not re.fullmatch(r"\d{8}", eval_da):
        raise VocabEvalError(f"--eval-da vuole AAAAMMGG, ricevuto: {eval_da}")

    for voc in (vocab_a, vocab_b):
        if not voc:
            continue
        dev_until = str(voc.get("dev_until") or voc.get("sviluppo_fino") or "")
        if dev_until and eval_da and dev_until >= eval_da:
            raise VocabEvalError(
                f"il vocabolario '{voc.get('name')}' dichiara sviluppo fino al "
                f"{dev_until}, che interseca la finestra di valutazione da "
                f"{eval_da}: sposta --eval-da dopo la fine dello sviluppo."
            )

    selezionati = []
    senza_data = 0
    rx = re.compile(eval_match) if eval_match else None
    for c in campioni:
        if eval_da:
            if not c["data"]:
                senza_data += 1
                continue
            if c["data"] < eval_da:
                continue
        if rx and not rx.search(c["rel"]):
            continue
        selezionati.append(c)
    if senza_data:
        print(f"ATTENZIONE: {senza_data} campioni senza data AAAAMMGG nel path, "
              f"esclusi dalla selezione per data")
    if not selezionati:
        raise VocabEvalError(
            "insieme di valutazione vuoto dopo lo split: controlla --eval-da/"
            "--eval-match rispetto ai path dei summary"
        )
    return selezionati


def verifica_checkpoint(campioni: list[dict]) -> None:
    """Rifiuta il confronto fra embedding di checkpoint diversi."""
    from .semantic_clap import checkpoint_fingerprint
    dichiarate = {c["checkpoint_sha256"] for c in campioni if c["checkpoint_sha256"]}
    if len(dichiarate) > 1:
        raise VocabEvalError(
            "i summary dichiarano checkpoint CLAP diversi fra loro: "
            + ", ".join(sorted(s[:12] for s in dichiarate))
            + ". Embedding audio di checkpoint diversi non sono confrontabili."
        )
    corrente = checkpoint_fingerprint()
    if dichiarate:
        dichiarata = next(iter(dichiarate))
        if corrente and dichiarata != corrente:
            raise VocabEvalError(
                f"i summary dichiarano il checkpoint {dichiarata[:12]}… ma il "
                f"checkpoint corrente e' {corrente[:12]}…: gli embedding dei "
                f"prompt verrebbero da un modello diverso da quello degli "
                f"embedding audio. Ripristina il checkpoint originale."
            )
    else:
        n_vuoti = sum(1 for c in campioni if not c["checkpoint_sha256"])
        print(f"ATTENZIONE: {n_vuoti} summary senza impronta del checkpoint "
              f"(prodotti prima della v0.20): impossibile verificare che gli "
              f"embedding audio vengano dal checkpoint corrente"
              + (f" ({corrente[:12]}…)." if corrente else "."))


# ------------------------------------------------------------ orchestrare

def run_vocab_eval(
    summaries_dir: Path,
    vocab_path: Path,
    truth_path: Path,
    vocab_b_path: Path | None = None,
    eval_da: str | None = None,
    eval_match: str | None = None,
    sheet_path: Path | None = None,
    durata_min: float | None = None,
    output_dir: Path | None = None,
) -> dict:
    """Valutazione completa. Ritorna i path delle tabelle scritte."""
    from .semantic_clap import embed_prompts, load_user_vocabulary

    vocab_a = load_user_vocabulary(Path(vocab_path))
    vocab_b = load_user_vocabulary(Path(vocab_b_path)) if vocab_b_path else None
    truth = load_truth(Path(truth_path))
    sheet = load_sheet(Path(sheet_path)) if sheet_path else None

    campioni, diag = carica_campioni(Path(summaries_dir))
    if not campioni:
        raise VocabEvalError(
            f"nessun summary con embedding CLAP sotto {summaries_dir} "
            f"(scartati {diag['summary_senza_embedding']})"
        )
    if diag["summary_senza_embedding"]:
        print(f"summary senza embedding o illeggibili: "
              f"{diag['summary_senza_embedding']} (esclusi)")

    campioni = verifica_split(campioni, eval_da, eval_match, vocab_a, vocab_b)
    verifica_checkpoint(campioni)

    # Criterio di durata: la quota fuori criterio si riporta SEMPRE.
    soglia = durata_min if durata_min is not None else 0.0
    fuori = [c for c in campioni
             if c["durata_s"] is not None and c["durata_s"] < max(soglia, 54.0)]
    if durata_min is not None:
        prima = len(campioni)
        campioni = [c for c in campioni
                    if c["durata_s"] is not None and c["durata_s"] >= durata_min]
        print(f"criterio di durata >= {durata_min} s: esclusi "
              f"{prima - len(campioni)} campioni su {prima} "
              f"({(prima - len(campioni)) / prima:.1%})")
        if not campioni:
            raise VocabEvalError("nessun campione sopra la durata minima")
    else:
        print(f"campioni sotto i 54 s (catture troncate note): {len(fuori)} "
              f"su {len(campioni)} ({len(fuori) / len(campioni):.1%}), "
              f"inclusi (nessun --durata-min)")

    # Verita' e stratificazione.
    senza_verita = 0
    for c in campioni:
        etichetta = match_truth(c["id"], truth)
        if etichetta is None:
            senza_verita += 1
        c["etichetta_vera"] = etichetta or ""
        c["gruppo_proxy"] = forma_proxy(c["panns_top5"])
        if sheet is not None:
            annotata = sheet.get(c["id"]) or match_truth(c["id"], sheet)
            c["gruppo"] = annotata or "senza_annotazione"
        else:
            c["gruppo"] = c["gruppo_proxy"]
    if senza_verita:
        print(f"ATTENZIONE: {senza_verita} campioni senza etichetta di verita' "
              f"(esclusi dalle metriche di correttezza)")
    if sheet is not None:
        overlap = [c for c in campioni if c["gruppo"] != "senza_annotazione"]
        if overlap:
            k = cohen_kappa([c["gruppo"] for c in overlap],
                            [c["gruppo_proxy"] for c in overlap])
            print(f"accordo scheda umana vs indicatore proxy su "
                  f"{len(overlap)} campioni annotati: kappa {k:.3f}")

    # Valutazione dei vocabolari.
    def _n_classi(voc: dict) -> int:
        return len({p.get("category", "") for p in voc["prompts"]} - {DISTRATTORE})

    emb_a = embed_prompts([p["text"] for p in vocab_a["prompts"]])
    righe_a = evaluate_vocab(campioni, vocab_a, emb_a)
    per_vocab = {vocab_a["name"]: righe_a}
    n_classi = {vocab_a["name"]: _n_classi(vocab_a)}
    if vocab_b is not None:
        if vocab_b["name"] == vocab_a["name"]:
            vocab_b["name"] += "_b"
        emb_b = embed_prompts([p["text"] for p in vocab_b["prompts"]])
        per_vocab[vocab_b["name"]] = evaluate_vocab(campioni, vocab_b, emb_b)
        n_classi[vocab_b["name"]] = _n_classi(vocab_b)

    out_dir = Path(output_dir) if output_dir else Path(summaries_dir) / "vocab_eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    scritti = {}

    # 1. Dettaglio per campione (colonne per vocabolario, come le tabelle oos).
    nomi = list(per_vocab)
    dettaglio_path = out_dir / "vocab_eval_dettaglio.csv"
    with dettaglio_path.open("w", encoding="utf-8", newline="") as fh:
        base = per_vocab[nomi[0]]
        campi = ["id", "rel", "data", "durata_s", "gruppo", "etichetta_vera"]
        for nome in nomi:
            campi += [f"{nome}_top1", f"{nome}_top1_corretto",
                      f"{nome}_top3_corretto", f"{nome}_margine"]
        w = csv.DictWriter(fh, fieldnames=campi)
        w.writeheader()
        for i, r0 in enumerate(base):
            riga = {k: r0[k] for k in
                    ("id", "rel", "data", "durata_s", "gruppo", "etichetta_vera")}
            for nome in nomi:
                r = per_vocab[nome][i]
                riga.update({
                    f"{nome}_top1": r["top1"],
                    f"{nome}_top1_corretto": r["top1_corretto"],
                    f"{nome}_top3_corretto": r["top3_corretto"],
                    f"{nome}_margine": r["margine"],
                })
            w.writerow(riga)
    scritti["dettaglio"] = dettaglio_path

    # 2. Riepilogo per forma con concentrazione delle predizioni.
    con_verita_idx = [i for i, c in enumerate(campioni) if c["etichetta_vera"]]
    riepilogo_path = out_dir / "vocab_eval_per_forma.csv"
    righe_riep = []
    gruppi_presenti = [g for g in list(GRUPPI) + ["senza_annotazione", "ignoto"]
                       if any(c["gruppo"] == g for c in campioni)]
    print(f"\ncampioni valutati {len(campioni)}"
          + (f" (con verita' {len(con_verita_idx)})"
             if senza_verita else ""))
    for nome in nomi:
        righe = per_vocab[nome]
        for gruppo in ["totale"] + gruppi_presenti:
            idx = (con_verita_idx if gruppo == "totale"
                   else [i for i in con_verita_idx
                         if campioni[i]["gruppo"] == gruppo])
            preds_tutti = ([r["top1"] for r in righe] if gruppo == "totale"
                           else [r["top1"] for i, r in enumerate(righe)
                                 if campioni[i]["gruppo"] == gruppo])
            conc = concentrazione(preds_tutti, n_classi[nome])
            voce = {
                "vocabolario": nome,
                "gruppo": gruppo,
                "campioni": len(preds_tutti),
                "con_verita": len(idx),
                "top1_corretti": sum(righe[i]["top1_corretto"] for i in idx),
                "top3_corretti": sum(righe[i]["top3_corretto"] for i in idx),
                **{f"conc_{k}": v for k, v in conc.items() if k != "n"},
            }
            righe_riep.append(voce)
            if conc["warning"]:
                print(f"WARNING concentrazione [{nome} / {gruppo}]: classe "
                      f"modale '{conc['classe_modale']}' al "
                      f"{conc['quota_modale']:.0%}, entropia normalizzata "
                      f"{conc['entropia_norm']} (soglie: quota > "
                      f"{config.VOCAB_EVAL_MODAL_SHARE_WARN:.0%}, entropia < "
                      f"{config.VOCAB_EVAL_ENTROPY_NORM_WARN}). Possibile "
                      f"effetto calamita.")
    with riepilogo_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(righe_riep[0].keys()))
        w.writeheader()
        w.writerows(righe_riep)
    scritti["per_forma"] = riepilogo_path

    # 3. McNemar esatto appaiato, solo con due vocabolari.
    if vocab_b is not None:
        nome_a, nome_b = nomi
        righe_a, righe_b = per_vocab[nome_a], per_vocab[nome_b]
        esiti = []
        print(f"\nMcNemar esatto appaiato, A={nome_a}, B={nome_b}")
        for campo, tit in (("top1_corretto", "top-1"), ("top3_corretto", "top-3")):
            for gruppo in ["totale"] + [g for g in gruppi_presenti if g in GRUPPI]:
                idx = (con_verita_idx if gruppo == "totale"
                       else [i for i in con_verita_idx
                             if campioni[i]["gruppo"] == gruppo])
                if not idx:
                    continue
                solo_a = sum(1 for i in idx
                             if righe_a[i][campo] and not righe_b[i][campo])
                solo_b = sum(1 for i in idx
                             if righe_b[i][campo] and not righe_a[i][campo])
                p = mcnemar_esatto(solo_a, solo_b)
                n_a = sum(righe_a[i][campo] for i in idx)
                n_b = sum(righe_b[i][campo] for i in idx)
                verso = ("A meglio" if solo_a > solo_b
                         else "B meglio" if solo_b > solo_a else "pari")
                print(f"  {tit} {gruppo:<18} n={len(idx):>5}  A={n_a:>5} "
                      f"B={n_b:>5}  discordanti {solo_a}/{solo_b}  "
                      f"p={p:.3g}  {verso}")
                esiti.append({"confronto": f"{tit} {gruppo}", "n": len(idx),
                              "A_corretti": n_a, "B_corretti": n_b,
                              "solo_A": solo_a, "solo_B": solo_b,
                              "p_mcnemar_esatto": p})
        mcnemar_path = out_dir / "vocab_eval_mcnemar.csv"
        with mcnemar_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(esiti[0].keys()))
            w.writeheader()
            w.writerows(esiti)
        scritti["mcnemar"] = mcnemar_path

    print(f"\ntabelle scritte in {out_dir}/: "
          + ", ".join(p.name for p in scritti.values()))
    return {k: str(v) for k, v in scritti.items()}
