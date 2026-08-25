"""Test v0.20.0 - famiglia di valutazione `vocab-eval` (lezioni 8-9 addendum
heritage). Corpus sintetico, nessun modello reale: embed_prompts e
checkpoint_fingerprint sono monkeypatchati.
"""
from __future__ import annotations

import base64
import json

import numpy as np
import pytest

from scripts import semantic_clap, vocab_eval
from scripts.vocab_eval import (
    VocabEvalError,
    concentrazione,
    forma_proxy,
    mcnemar_esatto,
    run_vocab_eval,
    verifica_checkpoint,
    verifica_split,
)

CK = "c" * 64

# Vettori dei prompt: il fake di embed_prompts risolve per testo.
_PROMPT_VECS = {
    "alpha": [1.0, 0.0, 0.0, 0.0],
    "beta": [0.0, 1.0, 0.0, 0.0],
    "rumore": [0.0, 0.0, 0.0, 1.0],
}


def _fake_embed_prompts(texts, device=None, use_cache=True):
    return np.asarray([_PROMPT_VECS[t] for t in texts], dtype=np.float32)


@pytest.fixture()
def fake_model(monkeypatch):
    monkeypatch.setattr(semantic_clap, "embed_prompts", _fake_embed_prompts)
    monkeypatch.setattr(semantic_clap, "checkpoint_fingerprint", lambda p=None: CK)


def _scrivi_summary(dir_, stem, emb_rows, panns_names,
                    duration=60.0, ck=CK):
    dir_.mkdir(parents=True, exist_ok=True)
    emb = np.asarray(emb_rows, dtype=np.float16)
    d = {
        "metadata": {"duration_s": duration},
        "semantic": {"classifier": {"top_global": [
            {"name": n, "score": 0.5} for n in panns_names]}},
        "clap": {
            "enabled": True,
            "embeddings_audio_b64": base64.b64encode(emb.tobytes()).decode(),
            "embeddings_shape": [list(emb.shape), [3, 4]],
            "checkpoint_sha256": ck,
        },
    }
    (dir_ / f"{stem}_summary.json").write_text(
        json.dumps(d), encoding="utf-8")


def _scrivi_vocab(path, name, con_distrattore=True, dev_until=""):
    prompts = [
        {"id": "a1", "text": "alpha", "category": "trad_a"},
        {"id": "b1", "text": "beta", "category": "trad_b"},
    ]
    if con_distrattore:
        prompts.append({"id": "d1", "text": "rumore", "category": "_distrattore"})
    voc = {"name": name, "version": "1.0", "language": "en", "prompts": prompts}
    if dev_until:
        voc["dev_until"] = dev_until
    path.write_text(json.dumps(voc), encoding="utf-8")
    return path


def _scrivi_truth(path):
    path.write_text(
        "id,etichetta\nstA,trad_a\nstB,trad_b\n", encoding="utf-8")
    return path


def _corpus(tmp_path):
    """Quattro campioni eval (20/08) piu' uno di sviluppo (10/08)."""
    root = tmp_path / "corpus"
    dev = root / "20260810-h11"
    ev = root / "20260820-h11"
    # stA-*: embedding vicino ad alpha -> trad_a; PANNs canto
    _scrivi_summary(ev, "stA-uno", [[1, 0, 0, 0]], ["Singing", "Music"])
    _scrivi_summary(ev, "stA-due", [[0.9, 0.1, 0, 0]], ["Music", "Choir"])
    # stB-*: vicino a beta -> trad_b; uno parlato, uno musicale
    _scrivi_summary(ev, "stB-uno", [[0, 1, 0, 0]], ["Speech"])
    _scrivi_summary(ev, "stB-corto", [[0.1, 0.9, 0, 0]], ["Music"],
                    duration=12.0)
    _scrivi_summary(dev, "stA-dev", [[1, 0, 0, 0]], ["Singing"])
    return root


# ------------------------------------------------------------- unita' pure

def test_mcnemar_esatto_valori_noti():
    # Ancore dalla tabella mcnemar_24ago della campagna heritage.
    assert mcnemar_esatto(111, 57) == pytest.approx(3.75e-05, rel=0.05)
    assert mcnemar_esatto(1, 17) == pytest.approx(1.45e-04, rel=0.05)
    assert mcnemar_esatto(0, 0) == 1.0
    assert mcnemar_esatto(5, 5) == 1.0
    assert mcnemar_esatto(3, 9) == mcnemar_esatto(9, 3)


def test_forma_proxy():
    assert forma_proxy(["Speech", "Music"]) == "parlato"
    assert forma_proxy(["Music", "Mantra"]) == "cantabile"
    assert forma_proxy(["Music", "Guitar"]) == "musicale"
    assert forma_proxy([]) == "ignoto"
    # il ramo parlato vince sul cantabile solo se dominante
    assert forma_proxy(["Singing", "Speech"]) == "cantabile"


def test_concentrazione_warning():
    conc = concentrazione(["x"] * 8 + ["y"] * 2, n_classi=5)
    assert conc["classe_modale"] == "x"
    assert conc["quota_modale"] == 0.8
    assert conc["warning"] is True
    equilibrata = concentrazione(["a", "b", "c", "d", "e"] * 4, n_classi=5)
    assert equilibrata["warning"] is False
    assert concentrazione([], n_classi=5)["n"] == 0


# ----------------------------------------------------------------- rifiuti

def test_split_obbligatorio():
    with pytest.raises(VocabEvalError, match="split obbligatorio"):
        verifica_split([{"data": "20260820", "rel": "x"}], None, None,
                       {"name": "a"}, None)


def test_split_rifiuta_sviluppo_che_interseca():
    voc = {"name": "v2", "dev_until": "20260821"}
    with pytest.raises(VocabEvalError, match="sviluppo fino al"):
        verifica_split([{"data": "20260822", "rel": "x"}], "20260820", None,
                       voc, None)


def test_split_rifiuta_selezione_vuota():
    with pytest.raises(VocabEvalError, match="vuoto"):
        verifica_split([{"data": "20260810", "rel": "x"}], "20260820", None,
                       {"name": "a"}, None)


def test_checkpoint_misti_rifiutati(fake_model):
    campioni = [{"checkpoint_sha256": "a" * 64},
                {"checkpoint_sha256": "b" * 64}]
    with pytest.raises(VocabEvalError, match="checkpoint CLAP diversi"):
        verifica_checkpoint(campioni)


def test_checkpoint_diverso_dal_corrente(fake_model):
    campioni = [{"checkpoint_sha256": "a" * 64}]
    with pytest.raises(VocabEvalError, match="checkpoint corrente"):
        verifica_checkpoint(campioni)


def test_checkpoint_assente_solo_warning(fake_model, capsys):
    verifica_checkpoint([{"checkpoint_sha256": ""}])
    out = capsys.readouterr().out
    assert "senza impronta del checkpoint" in out


# ------------------------------------------------------------- end-to-end

def test_run_vocab_eval_confronto(fake_model, tmp_path, capsys):
    root = _corpus(tmp_path)
    va = _scrivi_vocab(tmp_path / "va.json", "va")
    vb = _scrivi_vocab(tmp_path / "vb.json", "vb", con_distrattore=False)
    truth = _scrivi_truth(tmp_path / "truth.csv")

    out = run_vocab_eval(
        summaries_dir=root, vocab_path=va, truth_path=truth,
        vocab_b_path=vb, eval_da="20260815",
        output_dir=tmp_path / "out",
    )
    testo = capsys.readouterr().out
    # il campione di sviluppo (10/08) e' fuori
    assert "campioni valutati 4" in testo
    # quota fuori criterio riportata anche senza --durata-min
    assert "catture troncate note" in testo
    # tabelle scritte
    import csv as _csv
    dettaglio = list(_csv.DictReader(open(out["dettaglio"], encoding="utf-8")))
    assert len(dettaglio) == 4
    assert {r["id"] for r in dettaglio} == {"stA-uno", "stA-due",
                                            "stB-uno", "stB-corto"}
    # verita' via prefisso di stazione e predizioni giuste con entrambi
    r = next(r for r in dettaglio if r["id"] == "stA-uno")
    assert r["etichetta_vera"] == "trad_a"
    assert r["va_top1"] == "trad_a" and r["vb_top1"] == "trad_a"
    assert r["gruppo"] == "cantabile"
    mc = list(_csv.DictReader(open(out["mcnemar"], encoding="utf-8")))
    tot = next(m for m in mc if m["confronto"] == "top-1 totale")
    assert tot["n"] == "4"
    assert float(tot["p_mcnemar_esatto"]) == 1.0  # stessi risultati, pari


def test_run_vocab_eval_durata_min(fake_model, tmp_path, capsys):
    root = _corpus(tmp_path)
    va = _scrivi_vocab(tmp_path / "va.json", "va")
    truth = _scrivi_truth(tmp_path / "truth.csv")
    run_vocab_eval(summaries_dir=root, vocab_path=va, truth_path=truth,
                   eval_da="20260815", durata_min=54.0,
                   output_dir=tmp_path / "out2")
    testo = capsys.readouterr().out
    assert "esclusi 1 campioni su 4" in testo


def test_run_vocab_eval_con_scheda(fake_model, tmp_path, capsys):
    root = _corpus(tmp_path)
    va = _scrivi_vocab(tmp_path / "va.json", "va")
    truth = _scrivi_truth(tmp_path / "truth.csv")
    scheda = tmp_path / "scheda.csv"
    scheda.write_text(
        "stazione,forma\nstA-uno,recitazione_cantillata\nstB-uno,parlato\n",
        encoding="utf-8")
    run_vocab_eval(summaries_dir=root, vocab_path=va, truth_path=truth,
                   eval_da="20260815", sheet_path=scheda,
                   output_dir=tmp_path / "out3")
    testo = capsys.readouterr().out
    assert "accordo scheda umana vs indicatore proxy" in testo


def test_load_sheet_forma_non_riconosciuta(tmp_path):
    scheda = tmp_path / "scheda.csv"
    scheda.write_text("id,forma\nx,urlato\n", encoding="utf-8")
    with pytest.raises(VocabEvalError, match="non riconosciuta"):
        vocab_eval.load_sheet(scheda)
