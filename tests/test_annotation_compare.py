"""Test del confronto annotazione umana vs analisi skill (v0.19.0).

Copre le primitive (kappa, confini, proiezione famiglia), l'orchestrazione
end-to-end su dati sintetici deterministici e le rese markdown/PDF.
"""
import json

import pytest

from scripts import annotation_compare as ac
from scripts.load_annotation import load_annotation

# Timeline PANNs sintetica. Bird -> biofonia; Wind e Water -> geofonia
# (mappature reali di config.PANNS_LABEL_TO_KRAUSE, alto segnale).
TIMELINE = [
    {"t_start_s": 0.0, "t_end_s": 5.0,
     "top": [{"name": "Bird", "score": 0.4}, {"name": "Wind", "score": 0.1}]},
    {"t_start_s": 5.0, "t_end_s": 10.0,
     "top": [{"name": "Wind", "score": 0.3}, {"name": "Water", "score": 0.1}]},
]


def _ann(i, start, end, taxonomy="krause", term_id="krause.biophony",
         label="Biofonia"):
    return {
        "id": f"a{i}", "startSec": start, "endSec": end,
        "taxonomy": taxonomy, "termId": term_id, "termLabel": label,
        "color": "#ffffff", "note": "", "createdAt": "2026-07-02T10:00:00Z",
        "updatedAt": "2026-07-02T10:00:00Z",
    }


def _project(tmp_path, annotations, structure=None, duration=60.0):
    payload = {
        "schemaVersion": "1.0",
        "id": "proj-1",
        "audio": {"filename": "test.wav", "durationSeconds": duration,
                  "sampleRate": 48000, "channels": 1},
        "metadata": {"language": "it", "startedAt": "2026-07-02T10:00:00Z",
                     "annotator": "Francesco"},
        "annotations": annotations,
        "structure": structure or [],
    }
    p = tmp_path / "test.annotation.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return load_annotation(p)


def _summary(duration=60.0):
    return {
        "metadata": {"duration_s": duration},
        "semantic": {"classifier": {"timeline": TIMELINE}},
        "structure": {"sections": [
            {"id": "S1", "t_start_s": 0.0, "t_end_s": 11.0,
             "signature_label": "biofonia mattutina", "krause": "biofonia"},
            {"id": "S2", "t_start_s": 11.0, "t_end_s": 60.0,
             "signature_label": "vento e acqua", "krause": "geofonia"},
        ]},
    }


def test_cohen_kappa_known_values():
    assert ac.cohen_kappa(["a", "b", "a"], ["a", "b", "a"]) == pytest.approx(1.0)
    # Caso costruito a mano: observed 0.8, expected 0.5 -> kappa 0.6.
    a = ["x"] * 5 + ["y"] * 5
    b = ["x", "x", "x", "x", "y", "x", "y", "y", "y", "y"]
    assert ac.cohen_kappa(a, b) == pytest.approx(0.6)
    # Degenere (accordo atteso 1) e input vuoto: kappa indefinito.
    assert ac.cohen_kappa(["x", "x"], ["x", "x"]) is None
    assert ac.cohen_kappa([], []) is None


def test_boundary_agreement_with_tolerance():
    res = ac.boundary_agreement([10.0, 20.0], [11.0, 35.0], tolerance_s=3.0)
    assert res["n_matched"] == 1
    assert res["precision"] == pytest.approx(0.5)
    assert res["recall"] == pytest.approx(0.5)
    assert res["f1"] == pytest.approx(0.5)


def test_segment_families_respects_min_score():
    top = [{"name": "Bird", "score": 0.4}, {"name": "Wind", "score": 0.01}]
    fams = ac._segment_families(top)
    assert fams == {"biofonia"}  # Wind sotto soglia non concorre
    assert ac._segment_dominant_family(top) == "biofonia"
    assert ac._segment_dominant_family([{"name": "Sconosciuto", "score": 0.9}]) == "mista"


def test_compare_end_to_end(tmp_path):
    project = _project(tmp_path, [
        _ann(1, 0.0, 10.0),
        _ann(2, 2.0, 4.0, taxonomy="schaeffer", term_id="massa.tonica",
             label="Massa tonica"),
    ], structure=[
        {"id": "s1", "startSec": 0.0, "endSec": 12.0, "label": "prima parte"},
        {"id": "s2", "startSec": 12.0, "endSec": 60.0, "label": "seconda parte"},
    ])
    result = ac.compare(project, _summary())

    # Confini: taglio umano a 12 s contro taglio macchina a 11 s, entro 3 s.
    assert result["boundary"]["f1"] == pytest.approx(1.0)

    # Krause per bin: 10 bin umani (0-10 s), accordo su 0-5 (Bird -> biofonia),
    # disaccordo su 5-10 (Wind -> geofonia).
    kb = result["krause_bins"]
    assert kb["n_bins_confrontabili"] == 10
    assert kb["percent_agreement"] == pytest.approx(0.5)
    assert kb["kappa"] == pytest.approx(0.0)

    # Copertura: l'unica annotazione di famiglia copre 5 s su 10 (soglia 0.5).
    cov = result["coverage"]
    assert cov["family_recall"] == pytest.approx(1.0)
    family_entries = [e for e in cov["per_annotation"] if e.get("family")]
    assert family_entries[0]["covered_fraction"] == pytest.approx(0.5)
    assert family_entries[0]["machine_agrees"] is True

    # La tassonomia non-sorgente resta descrittiva, ancorata alla sezione S1.
    desc = [e for e in cov["per_annotation"] if e.get("descriptive_only")]
    assert desc and desc[0]["machine_section"] == "S1"


def test_compare_renders_markdown_and_pdf(tmp_path):
    project = _project(tmp_path, [_ann(1, 0.0, 10.0)], structure=[
        {"id": "s1", "startSec": 0.0, "endSec": 12.0, "label": "prima parte"},
        {"id": "s2", "startSec": 12.0, "endSec": 60.0, "label": "seconda parte"},
    ])
    result = ac.compare(project, _summary())

    md = ac.render_markdown(result)
    assert "Cohen's kappa" in md
    assert "Confini strutturali" in md
    assert "biofonia" in md.lower()

    out_pdf = tmp_path / "confronto.pdf"
    ac.build_compare_pdf(result, out_pdf)
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 1000


def test_compare_without_timeline_degrades_gracefully(tmp_path):
    project = _project(tmp_path, [_ann(1, 0.0, 10.0)])
    result = ac.compare(project, {"metadata": {"duration_s": 60.0}})
    assert result["krause_bins"] is None
    assert result["boundary"] is None
    assert any("imeline" in n for n in result["notes"])
    # La resa markdown non deve rompersi sui rami None.
    md = ac.render_markdown(result)
    assert "Non calcolabile" in md
