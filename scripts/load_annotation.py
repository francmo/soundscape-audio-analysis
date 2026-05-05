"""Loader per il formato JSON v1.0 della PWA Soundscape Annotation Atelier.

La PWA companion (https://soundscape-annotation-atelier.vercel.app/) esporta
file `*.annotation.json` con vocabolario controllato sulle 8 tassonomie
canoniche (Schaeffer, Smalley, Schafer, Krause, Chion, Truax, Westerkamp,
Wishart). Questo modulo li carica e li espone come dataclass Python utilizzabili
da `benchmark.py`, dal generatore di golden analyses e dal report PDF.

Schema completo: `templates/annotation_schema.json`.

Esempi:

    from scripts.load_annotation import load_annotation, validate_annotation

    project = load_annotation("./presque_rien.annotation.json")
    print(project.metadata.title, project.audio.duration_seconds)
    for ann in project.annotations:
        print(ann.start_sec, ann.term_label, ann.taxonomy)

    # Solo validazione (non parse), restituisce True/False
    is_ok = validate_annotation_dict(json.loads(text))
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

SCHEMA_VERSION = "1.0"

VALID_TAXONOMIES = frozenset({
    "schaeffer",
    "smalley",
    "schafer",
    "krause",
    "chion",
    "truax",
    "westerkamp",
    "wishart",
})


class AnnotationSchemaError(ValueError):
    """Errore di schema rilevato durante load/validate del JSON di annotazione."""


@dataclass
class AudioMeta:
    filename: str
    duration_seconds: float
    sample_rate: int
    channels: int
    sha256: Optional[str] = None


@dataclass
class ProjectMeta:
    language: str
    started_at: str
    title: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    annotator: Optional[str] = None


@dataclass
class Annotation:
    id: str
    start_sec: float
    end_sec: float
    taxonomy: str
    term_id: str
    term_label: str
    color: str
    note: str
    created_at: str
    updated_at: str


@dataclass
class StructuralSection:
    id: str
    start_sec: float
    end_sec: float
    label: str
    note: Optional[str] = None
    color: Optional[str] = None


@dataclass
class AnnotationProject:
    schema_version: str
    id: str
    audio: AudioMeta
    metadata: ProjectMeta
    annotations: List[Annotation] = field(default_factory=list)
    structure: List[StructuralSection] = field(default_factory=list)

    @property
    def annotations_by_taxonomy(self) -> dict[str, list[Annotation]]:
        out: dict[str, list[Annotation]] = {}
        for ann in self.annotations:
            out.setdefault(ann.taxonomy, []).append(ann)
        return out

    @property
    def expected_terms(self) -> list[str]:
        """Lista dei termId controllati, ordinata per occorrenza temporale.

        Compatibile con il formato atteso dal benchmark (vedi
        `references/golden_analyses/<id>.md` sezione "Terminologia attesa").
        """
        return [ann.term_id for ann in sorted(self.annotations, key=lambda a: a.start_sec)]


def load_annotation(path: str | Path) -> AnnotationProject:
    """Carica e valida un file JSON v1.0 esportato dalla PWA Annotation Atelier.

    Solleva AnnotationSchemaError se schema non valido.
    """
    text = Path(path).read_text(encoding="utf-8")
    payload = json.loads(text)
    validate_annotation_dict(payload)
    return _from_dict(payload)


def validate_annotation_dict(payload: Any) -> None:
    """Validazione strutturale minimale (no JSON Schema, ma deterministica)."""
    if not isinstance(payload, dict):
        raise AnnotationSchemaError(f"Root must be object, got {type(payload).__name__}")

    version = payload.get("schemaVersion")
    if version != SCHEMA_VERSION:
        raise AnnotationSchemaError(f"schemaVersion mismatch: expected {SCHEMA_VERSION}, got {version!r}")

    for required in ("id", "audio", "metadata", "annotations"):
        if required not in payload:
            raise AnnotationSchemaError(f"Missing required field: {required}")

    audio = payload["audio"]
    for required in ("filename", "durationSeconds", "sampleRate", "channels"):
        if required not in audio:
            raise AnnotationSchemaError(f"audio missing field: {required}")

    metadata = payload["metadata"]
    if "language" not in metadata or metadata["language"] not in ("it", "en"):
        raise AnnotationSchemaError("metadata.language must be 'it' or 'en'")
    if "startedAt" not in metadata:
        raise AnnotationSchemaError("metadata missing startedAt")

    annotations = payload["annotations"]
    if not isinstance(annotations, list):
        raise AnnotationSchemaError("annotations must be a list")
    for i, ann in enumerate(annotations):
        if not isinstance(ann, dict):
            raise AnnotationSchemaError(f"annotation #{i} not an object")
        for required in ("id", "startSec", "endSec", "taxonomy", "termId", "termLabel", "color", "note", "createdAt", "updatedAt"):
            if required not in ann:
                raise AnnotationSchemaError(f"annotation #{i} missing {required}")
        if ann["taxonomy"] not in VALID_TAXONOMIES:
            raise AnnotationSchemaError(f"annotation #{i} invalid taxonomy: {ann['taxonomy']!r}")

    structure = payload.get("structure", [])
    if not isinstance(structure, list):
        raise AnnotationSchemaError("structure must be a list")


def _from_dict(payload: dict[str, Any]) -> AnnotationProject:
    audio = payload["audio"]
    meta = payload["metadata"]

    return AnnotationProject(
        schema_version=payload["schemaVersion"],
        id=payload["id"],
        audio=AudioMeta(
            filename=audio["filename"],
            duration_seconds=float(audio["durationSeconds"]),
            sample_rate=int(audio["sampleRate"]),
            channels=int(audio["channels"]),
            sha256=audio.get("sha256"),
        ),
        metadata=ProjectMeta(
            language=meta["language"],
            started_at=meta["startedAt"],
            title=meta.get("title"),
            author=meta.get("author"),
            year=meta.get("year"),
            genre=meta.get("genre"),
            annotator=meta.get("annotator"),
        ),
        annotations=[
            Annotation(
                id=a["id"],
                start_sec=float(a["startSec"]),
                end_sec=float(a["endSec"]),
                taxonomy=a["taxonomy"],
                term_id=a["termId"],
                term_label=a["termLabel"],
                color=a["color"],
                note=a["note"],
                created_at=a["createdAt"],
                updated_at=a["updatedAt"],
            )
            for a in payload["annotations"]
        ],
        structure=[
            StructuralSection(
                id=s["id"],
                start_sec=float(s["startSec"]),
                end_sec=float(s["endSec"]),
                label=s["label"],
                note=s.get("note"),
                color=s.get("color"),
            )
            for s in payload.get("structure", [])
        ],
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 -m scripts.load_annotation <path/to/annotation.json>", file=sys.stderr)
        sys.exit(1)
    project = load_annotation(sys.argv[1])
    print(f"Schema: {project.schema_version}")
    print(f"Audio: {project.audio.filename} ({project.audio.duration_seconds:.1f}s, {project.audio.sample_rate} Hz, {project.audio.channels} ch)")
    print(f"Title: {project.metadata.title}")
    print(f"Author: {project.metadata.author}")
    print(f"Annotations: {len(project.annotations)} (by taxonomy: {[(k, len(v)) for k, v in project.annotations_by_taxonomy.items()]})")
    print(f"Structure: {len(project.structure)}")
