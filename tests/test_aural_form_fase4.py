"""Fase 4 (form-building): baseline deterministica di infer_phases e
build_suggested_relations. L'agente, non deterministico, e' testato a parte."""
from scripts import aural_form, agent_payload


def _dyn(peak: float, dur: float) -> dict:
    energy = [{"tSec": round(i * dur / 10, 3), "db": -30.0} for i in range(11)]
    return {"resolutionHz": 2.0, "unit": "dbfs", "energy": energy, "peakSec": peak, "phases": None}


def test_infer_phases_quattro_fasi_picco_centrale():
    phases = aural_form.infer_phases(_dyn(peak=50.0, dur=100.0))
    assert phases is not None
    assert [p["name"] for p in phases] == ["anacrusi", "crescita", "climax", "risoluzione"]
    # fasi contigue e che coprono l'intera durata
    for a, b in zip(phases, phases[1:]):
        assert a["endSec"] == b["startSec"]
    assert phases[0]["startSec"] == 0.0
    assert phases[-1]["endSec"] == 100.0


def test_infer_phases_curva_corta_o_assente():
    assert aural_form.infer_phases(None) is None
    assert aural_form.infer_phases({"energy": [{"tSec": 0, "db": -30}], "peakSec": 0}) is None


def test_infer_phases_picco_iniziale_senza_anacrusi():
    phases = aural_form.infer_phases(_dyn(peak=0.0, dur=60.0))
    assert phases is not None
    names = [p["name"] for p in phases]
    assert "anacrusi" not in names
    assert names[-1] == "risoluzione"


def test_suggested_relations_ripetizione_e_contrasto():
    tf = [
        {"id": "S1", "level": 0, "startSec": 0, "endSec": 10, "dominantPanns": "Speech",
         "krause": "antropofonia", "meanCentroidHz": 1000, "meanRmsDb": -30, "label": "voce"},
        {"id": "S2", "level": 0, "startSec": 10, "endSec": 20, "dominantPanns": "Speech",
         "krause": "antropofonia", "meanCentroidHz": 1010, "meanRmsDb": -28, "label": "voce"},
        {"id": "S3", "level": 0, "startSec": 20, "endSec": 30, "dominantPanns": "Bird",
         "krause": "biofonia", "meanCentroidHz": 5000, "meanRmsDb": -20, "label": "uccelli"},
    ]
    rels = aural_form.build_suggested_relations(tf, {"peakSec": 25.0})
    types = {r["type"] for r in rels}
    assert "repetition" in types  # S1-S2: stessa sorgente, timbro simile
    assert "contrast" in types    # S2-S3: famiglia diversa
    for r in rels:
        assert r["id"] and r["fromRef"] and r["toRef"] and "score" in r


def test_suggested_relations_input_vuoto():
    assert aural_form.build_suggested_relations([], None) == []
    assert aural_form.build_suggested_relations(None, None) == []
    # un solo campo: nessuna relazione possibile
    assert aural_form.build_suggested_relations([{"id": "S1", "level": 0}], None) == []


# --- Parte 2: payload dell'agente (relazioni + fasi visibili all'agente) ---

def test_compact_dynamic_form_includes_phases():
    df = {
        "resolutionHz": 2.0, "unit": "dbfs", "peakSec": 5.0,
        "energy": [{"tSec": i, "db": -30.0} for i in range(6)],
        "phases": [{"name": "climax", "startSec": 4, "endSec": 6}],
    }
    out = agent_payload._compact_dynamic_form(df)
    assert out is not None
    assert out["phases"] == df["phases"]


def test_agent_payload_aural_form_includes_relations_and_phases():
    summary = {
        "metadata": {"filename": "x.wav", "duration_s": 10, "sr": 44100, "channels": 2},
        "time_fields": [{"id": "S1", "level": 0, "startSec": 0, "endSec": 10}],
        "dynamic_form": {
            "resolutionHz": 2.0, "unit": "dbfs", "peakSec": 5.0,
            "energy": [{"tSec": i, "db": -30.0} for i in range(6)],
            "phases": [{"name": "climax", "startSec": 4, "endSec": 6}],
        },
        "suggested_layers": [{"id": "L1", "label": "Speech"}],
        "suggested_relations": [{"id": "R1", "type": "contrast", "fromRef": "S1", "toRef": "S2"}],
    }
    payload = agent_payload.build_agent_payload(summary, "narrativa")
    af = payload["aural_form"]
    assert af["suggested_relations"] == summary["suggested_relations"]
    assert af["dynamic_form"]["phases"] == summary["dynamic_form"]["phases"]
