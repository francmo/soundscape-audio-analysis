"""Test v0.20.0 - P3 addendum heritage: estrazione tabellare `tabulate`."""
from __future__ import annotations

import csv
import json

import pytest

from scripts.corpus_csv import estrai_campione, run_tabulate


def _summary(lufs, aci, panns="Music", gate=False):
    return {
        "version": "0.20.0",
        "metadata": {"duration_s": 60.0},
        "technical": {"lufs": {"integrated_lufs": lufs, "lra": 4.0,
                               "true_peak_db": -1.0},
                      "levels": {"crest_db": 12.0, "dynamic_range_db": 30.0}},
        "spectral": {"timbre": {"spectral_centroid_hz": 1500.0,
                                "spectral_flatness": 0.02},
                     "onsets": {"events_per_sec": 1.2},
                     "hifi_lofi": {"score_5": 3}},
        "ecoacoustic": {"aci": aci, "ndsi": {"ndsi": -0.8},
                        "h_entropy": {"h_total": 0.5}, "bi": 3.0,
                        "domain_gate": {"out_of_domain": gate, "reason": ""}},
        "semantic": {"classifier": {"top_global": [
            {"name": panns, "score": 0.6}, {"name": "Speech", "score": 0.2}]}},
        "clap": {"top_global": [{"id": "x", "prompt": "coro in chiesa",
                                 "score": 0.41}],
                 "academic_hints": {"available": True,
                                    "krause": {"dominant": {"value": "antropofonia"}}},
                 "checkpoint_sha256": "c" * 64},
    }


def _scrivi(dir_, stem, summary):
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / f"{stem}_summary.json").write_text(json.dumps(summary),
                                               encoding="utf-8")


def test_estrai_campione_campi():
    r = estrai_campione(_summary(-23.0, 120.0, gate=True))
    assert r["lufs"] == -23.0
    assert r["aci"] == 120.0
    assert r["panns_top"] == "Music"
    assert r["panns_top5"] == "Music|Speech"
    assert r["clap_top"] == "coro in chiesa"
    assert r["krause_dominante"] == "antropofonia"
    assert r["eco_fuori_dominio"] == 1
    assert r["checkpoint_sha256"] == "c" * 64


def test_run_tabulate_con_gruppi_per_cartella(tmp_path, capsys):
    root = tmp_path / "corpus"
    _scrivi(root / "sess_a", "uno", _summary(-20.0, 100.0))
    _scrivi(root / "sess_a", "due", _summary(-30.0, 200.0))
    _scrivi(root / "sess_b", "tre", _summary(-25.0, 150.0, panns="Speech"))
    (root / "sess_b" / "rotto_summary.json").write_text("{non json",
                                                        encoding="utf-8")
    out = run_tabulate(root, group_by_parent=True)
    testo = capsys.readouterr().out
    assert "illeggibili" in testo and "1" in testo
    campioni = list(csv.DictReader(open(out["campioni"], encoding="utf-8")))
    assert len(campioni) == 3
    gruppi = {r["gruppo"]: r for r in
              csv.DictReader(open(out["gruppi"], encoding="utf-8"))}
    assert gruppi["sess_a"]["campioni"] == "2"
    assert float(gruppi["sess_a"]["lufs"]) == -25.0  # mediana di -20 e -30
    assert gruppi["sess_a"]["panns_prevalente"] == "Music"
    assert gruppi["sess_b"]["panns_prevalente"] == "Speech"


def test_run_tabulate_group_map(tmp_path):
    root = tmp_path / "corpus"
    _scrivi(root, "stA-uno", _summary(-20.0, 100.0))
    _scrivi(root, "stB-uno", _summary(-30.0, 200.0))
    out = run_tabulate(root, group_map={"stA": "gruppo_a", "stB": "gruppo_b"},
                       output_dir=tmp_path / "out")
    gruppi = {r["gruppo"] for r in
              csv.DictReader(open(out["gruppi"], encoding="utf-8"))}
    assert gruppi == {"gruppo_a", "gruppo_b"}


def test_run_tabulate_vuoto(tmp_path):
    with pytest.raises(ValueError, match="nessun summary"):
        run_tabulate(tmp_path)
