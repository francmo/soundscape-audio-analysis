"""Test del loader annotation/interchange (contratto INTEROP v1.1).

Coprono la regola reader del contratto (templates/INTEROP.md): accettare ogni
schemaVersion 1.x, rifiutare le major diverse, preservare i blocchi top-level
sconosciuti per il round-trip senza perdita.
"""
from __future__ import annotations

import json

import pytest

from scripts.load_annotation import (
    AnnotationSchemaError,
    load_annotation,
    validate_annotation_dict,
)


def _base_payload(**overrides):
    payload = {
        "schemaVersion": "1.0",
        "id": "prj-test",
        "audio": {
            "filename": "campo_lungo.wav",
            "durationSeconds": 42.5,
            "sampleRate": 48000,
            "channels": 2,
            "sha256": "ab" * 32,
        },
        "metadata": {
            "language": "it",
            "startedAt": "2026-06-11T10:00:00Z",
            "title": "Campo lungo",
        },
        "annotations": [
            {
                "id": "ann-1",
                "startSec": 1.0,
                "endSec": 4.0,
                "taxonomy": "schafer",
                "termId": "keynote",
                "termLabel": "Tonica",
                "color": "#aa0000",
                "note": "",
                "createdAt": "2026-06-11T10:01:00Z",
                "updatedAt": "2026-06-11T10:01:00Z",
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_accepts_v10():
    validate_annotation_dict(_base_payload())


def test_accepts_v11_with_interchange_blocks():
    payload = _base_payload(
        schemaVersion="1.1",
        recording={
            "recordingId": "rec-1",
            "recordedAt": "2026-06-11T07:30:00Z",
            "gps": {"lat": 44.6, "lng": 10.9},
        },
        analysis={
            "engine": {"name": "soundscape-critic-web", "version": "0.1.0"},
            "analyzedAt": "2026-06-11T08:00:00Z",
            "levels": {"integratedLufs": -23.1},
        },
    )
    validate_annotation_dict(payload)


def test_accepts_future_minor():
    validate_annotation_dict(_base_payload(schemaVersion="1.7"))


@pytest.mark.parametrize("version", ["2.0", "0.9", "", None, 1.1])
def test_rejects_other_majors(version):
    payload = _base_payload()
    payload["schemaVersion"] = version
    with pytest.raises(AnnotationSchemaError):
        validate_annotation_dict(payload)


def test_extra_blocks_preserved_round_trip(tmp_path):
    payload = _base_payload(
        schemaVersion="1.1",
        recording={"recordingId": "rec-1"},
        analysis={"engine": {"name": "skill", "version": "0.15.0"}},
        bloccoFuturo={"x": 1},
    )
    src = tmp_path / "round.annotation.json"
    src.write_text(json.dumps(payload), encoding="utf-8")

    project = load_annotation(src)
    assert set(project.extra_blocks) == {"recording", "analysis", "bloccoFuturo"}
    assert project.extra_blocks["recording"]["recordingId"] == "rec-1"
    # round-trip: chi riscrive il file deve poter reinserire i blocchi intatti
    assert project.extra_blocks["analysis"]["engine"]["version"] == "0.15.0"


def test_v10_has_empty_extra_blocks(tmp_path):
    src = tmp_path / "plain.annotation.json"
    src.write_text(json.dumps(_base_payload()), encoding="utf-8")
    assert load_annotation(src).extra_blocks == {}


def test_schema_file_acceptance_matrix():
    """Lo schema JSON 1.1 deve accettare 1.0 e 1.1+blocchi, rifiutare 2.0."""
    jsonschema = pytest.importorskip("jsonschema")
    with open("templates/interchange_schema_v1.1.json", encoding="utf-8") as fh:
        schema = json.load(fh)

    jsonschema.validate(_base_payload(), schema)
    jsonschema.validate(
        _base_payload(
            schemaVersion="1.1",
            recording={
                "recordingId": "r",
                "recordedAt": "2026-06-11T07:30:00Z",
                "campoFuturo12": True,
            },
        ),
        schema,
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_payload(schemaVersion="2.0"), schema)
