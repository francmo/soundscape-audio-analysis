"""Test v0.20.0 - P2 addendum heritage: gate di dominio interpretativo per
indici ecoacustici e famiglie Krause su materiale antropofonico puro.
"""
from __future__ import annotations

from scripts import report_styles
from scripts.agent_payload import build_agent_payload
from scripts.ecoacoustic import domain_gate
from scripts.report_pdf import _build_eco_table, _format_academic_hints


def _classifier(top):
    return {"top_global": [{"name": n, "score": s} for n, s in top]}


def test_gate_scatta_su_palinsesto_puro():
    gate = domain_gate(_classifier([("Music", 0.62), ("Speech", 0.20)]))
    assert gate["out_of_domain"] is True
    assert gate["dominant_class"] == "Music"
    assert "non sono interpretabili" in gate["reason"]


def test_gate_non_scatta_con_biofonia():
    gate = domain_gate(_classifier([("Music", 0.5), ("Bird", 0.12)]))
    assert gate["out_of_domain"] is False
    assert "Bird" in gate["reason"]


def test_gate_non_scatta_con_geofonia():
    gate = domain_gate(_classifier([("Speech", 0.4), ("Rain", 0.09)]))
    assert gate["out_of_domain"] is False


def test_gate_non_scatta_su_top_non_palinsesto():
    gate = domain_gate(_classifier([("Wind", 0.5), ("Music", 0.3)]))
    assert gate["out_of_domain"] is False


def test_gate_non_scatta_su_score_debole():
    gate = domain_gate(_classifier([("Music", 0.10)]))
    assert gate["out_of_domain"] is False


def test_gate_senza_classificatore():
    gate = domain_gate(None)
    assert gate["out_of_domain"] is False
    assert "non valutabile" in gate["reason"]


def test_tabella_eco_dichiara_il_gate():
    styles = report_styles.build_styles(report_styles.register_fonts())
    eco = {"aci": 120.0, "ndsi": {"ndsi": -0.9}, "bi": 4.2,
           "h_entropy": {"h_total": 0.5},
           "domain_gate": {"out_of_domain": True, "dominant_class": "Music",
                           "reason": "..."}}
    tabella = _build_eco_table(eco, styles)
    testo = str(tabella._cellvalues)
    assert "fuori dominio" in testo
    senza = dict(eco)
    senza["domain_gate"] = {"out_of_domain": False, "reason": ""}
    assert "fuori dominio" not in str(_build_eco_table(senza, styles)._cellvalues)


def test_hints_krause_fuori_dominio_nel_pdf():
    hints = {"available": True,
             "krause": {"distribution": {"antropofonia": 0.9},
                        "out_of_domain": True,
                        "out_of_domain_reason": "..."}}
    testo = _format_academic_hints(hints)
    assert "fuori dominio" in testo
    hints_ok = {"available": True,
                "krause": {"distribution": {"biofonia": 0.7}}}
    assert "fuori dominio" not in _format_academic_hints(hints_ok)


def test_payload_agente_porta_il_gate():
    summary = {
        "metadata": {"filename": "x.wav", "duration_s": 60.0},
        "ecoacoustic": {"aci": 100.0, "bi": 2.0,
                        "domain_gate": {"out_of_domain": True,
                                        "dominant_class": "Speech",
                                        "reason": "r"}},
    }
    payload = build_agent_payload(summary, "")
    assert payload["ecoacoustic"]["domain_gate"]["out_of_domain"] is True
