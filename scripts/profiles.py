"""Profili di riferimento GRM.

Gestione caricamento/validazione/costruzione di profili di riferimento per
opere chiave della tradizione musique concrète, soundscape composition e
biofonia. I profili iniziali sono letteratura-based; possono essere rifiniti
da audio reale con il comando `soundscape profile build`.
"""
from datetime import date
from pathlib import Path
import shutil
import numpy as np

from . import config
from .serialization import load as load_json, dump as dump_json

SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GRM Reference Profile",
    "type": "object",
    "required": ["id", "title", "author", "year", "source_type", "spectral", "dynamic"],
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "author": {"type": "string"},
        "year": {"type": "integer"},
        "tradition": {"type": "string"},
        "source_type": {"enum": ["literature_based", "audio_derived"]},
        "sources_audio": {"type": "array", "items": {"type": "string"}},
        "generated_at": {"type": "string"},
        "notes_it": {"type": "string"},
        "spectral": {
            "type": "object",
            "required": ["centroid_hz_mean", "flatness_mean", "bands_pct"],
            "properties": {
                "centroid_hz_mean": {"type": "number"},
                "centroid_hz_std": {"type": "number"},
                "rolloff_85_hz_mean": {"type": "number"},
                "flatness_mean": {"type": "number"},
                "bands_pct": {
                    "type": "object",
                    "properties": {
                        "Sub-bass": {"type": "number"},
                        "Bass": {"type": "number"},
                        "Low-mid": {"type": "number"},
                        "Mid": {"type": "number"},
                        "High-mid": {"type": "number"},
                        "Presence": {"type": "number"},
                        "Brilliance": {"type": "number"},
                    },
                },
            },
        },
        "dynamic": {
            "type": "object",
            "properties": {
                "dynamic_range_db": {"type": "number"},
                "crest_db": {"type": "number"},
                "integrated_lufs": {"type": "number"},
            },
        },
        "ecoacoustic": {
            "type": "object",
            "properties": {
                "aci": {"type": "number"},
                "ndsi": {"type": "number"},
                "h_entropy": {"type": "number"},
            },
        },
        "density": {
            "type": "object",
            "properties": {
                "onset_per_sec": {"type": "number"},
                "qualitative": {"type": "string"},
            },
        },
    },
}


def write_schema() -> None:
    dump_json(SCHEMA, config.PROFILES_DIR / "schema.json")


def load_profile(name: str) -> dict:
    path = config.PROFILES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Profilo GRM '{name}' non trovato in {config.PROFILES_DIR}")
    return load_json(path)


def load_all_profiles() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not config.PROFILES_DIR.exists():
        return out
    for p in config.PROFILES_DIR.glob("*.json"):
        if p.name == "schema.json":
            continue
        try:
            data = load_json(p)
            out[data.get("id", p.stem)] = data
        except Exception:
            continue
    return out


def validate_profile(profile: dict) -> list[str]:
    """Validazione leggera manuale, ritorna lista errori."""
    errors: list[str] = []
    required_top = ["id", "title", "author", "year", "source_type", "spectral", "dynamic"]
    for field in required_top:
        if field not in profile:
            errors.append(f"manca campo obbligatorio: {field}")
    if "spectral" in profile:
        spec = profile["spectral"]
        for f in ["centroid_hz_mean", "flatness_mean", "bands_pct"]:
            if f not in spec:
                errors.append(f"manca spectral.{f}")
    if "source_type" in profile and profile["source_type"] not in ("literature_based", "audio_derived"):
        errors.append(f"source_type non valido: {profile['source_type']}")
    return errors


def build_profile_from_audio(
    audio_paths: list[str],
    output_name: str,
    metadata: dict,
) -> dict:
    """Costruisce profilo audio-derived da N file audio di riferimento.

    Normalizza temporaneamente a target LUFS, aggrega feature con media + std,
    salva JSON, backup del profilo letteratura-based originale se presente.
    """
    from .io_loader import load_audio_mono
    from .technical import compute_levels, compute_lufs
    from .spectral import spectral_summary
    from .ecoacoustic import ecoacoustic_summary

    centroids: list[float] = []
    flatness_list: list[float] = []
    dr_list: list[float] = []
    lufs_list: list[float] = []
    bands_list: list[dict] = []
    aci_list: list[float] = []
    ndsi_list: list[float] = []
    onsets: list[float] = []

    for p in audio_paths:
        y, sr = load_audio_mono(p)
        duration_s = len(y) / sr
        lvl = compute_levels(y)
        lufs = compute_lufs(p).get("integrated_lufs")
        spec = spectral_summary(y, sr, duration_s)
        eco = ecoacoustic_summary(y, sr)
        centroids.append(spec["timbre"]["spectral_centroid_hz"])
        flatness_list.append(spec["timbre"]["spectral_flatness"])
        dr_list.append(lvl["dynamic_range_db"])
        if lufs is not None:
            lufs_list.append(lufs)
        bands_list.append({k: v["energy_pct"] for k, v in spec["bands_schafer"].items()})
        aci_list.append(eco["aci"])
        ndsi_list.append(eco["ndsi"]["ndsi"])
        onsets.append(spec["onsets"]["events_per_sec"])

    def avg(vals):
        return round(float(np.mean(vals)), 3) if vals else None

    def std(vals):
        return round(float(np.std(vals)), 3) if vals else None

    merged_bands = {}
    if bands_list:
        for band in bands_list[0].keys():
            merged_bands[band] = round(float(np.mean([b[band] for b in bands_list])), 2)

    profile = {
        "id": output_name,
        "title": metadata.get("title", output_name),
        "author": metadata.get("author", ""),
        "year": int(metadata.get("year", 0)) or None,
        "tradition": metadata.get("tradition"),
        "source_type": "audio_derived",
        "sources_audio": [str(p) for p in audio_paths],
        "generated_at": date.today().isoformat(),
        "notes_it": metadata.get("notes", ""),
        "spectral": {
            "centroid_hz_mean": avg(centroids),
            "centroid_hz_std": std(centroids),
            "flatness_mean": avg(flatness_list),
            "bands_pct": merged_bands,
        },
        "dynamic": {
            "dynamic_range_db": avg(dr_list),
            "integrated_lufs": avg(lufs_list),
        },
        "ecoacoustic": {
            "aci": avg(aci_list),
            "ndsi": avg(ndsi_list),
        },
        "density": {
            "onset_per_sec": avg(onsets),
        },
    }

    out_path = config.PROFILES_DIR / f"{output_name}.json"
    backup_dir = config.PROFILES_DIR / "literature_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        existing = load_json(out_path)
        if existing.get("source_type") == "literature_based":
            backup_path = backup_dir / f"{output_name}_{date.today().isoformat()}.json"
            shutil.copy2(out_path, backup_path)

    dump_json(profile, out_path)
    return profile


# Profili letteratura-based iniziali, popolati da write_initial_profiles()

def _init_de_natura_sonorum() -> dict:
    return {
        "id": "de_natura_sonorum",
        "title": "De Natura Sonorum",
        "author": "Bernard Parmegiani",
        "year": 1975,
        "tradition": "musique concrète GRM",
        "source_type": "literature_based",
        "sources_audio": [],
        "generated_at": date.today().isoformat(),
        "notes_it": (
            "Ciclo di studi spettrali e morfologici, estetica GRM matura. "
            "Montaggio stretto, trasformazioni concrete, uso della sintesi, "
            "equilibrio tra fonti riconoscibili e astrazione."
        ),
        "spectral": {
            "centroid_hz_mean": 2000,
            "centroid_hz_std": 400,
            "rolloff_85_hz_mean": 6500,
            "flatness_mean": 0.18,
            "bands_pct": {
                "Sub-bass": 3, "Bass": 12, "Low-mid": 15, "Mid": 28,
                "High-mid": 22, "Presence": 13, "Brilliance": 7,
            },
        },
        "dynamic": {"dynamic_range_db": 38, "crest_db": 18, "integrated_lufs": -20},
        "ecoacoustic": {"aci": 1800, "ndsi": -0.3, "h_entropy": 0.72},
        "density": {"onset_per_sec": 3.2, "qualitative": "densa"},
    }


def _init_kits_beach_soundwalk() -> dict:
    return {
        "id": "kits_beach_soundwalk",
        "title": "Kits Beach Soundwalk",
        "author": "Hildegard Westerkamp",
        "year": 1989,
        "tradition": "soundscape composition",
        "source_type": "literature_based",
        "sources_audio": [],
        "generated_at": date.today().isoformat(),
        "notes_it": (
            "Soundwalk con voce narrante che guida l'ascolto attraverso un "
            "paesaggio costiero di Vancouver. Presenza di biofonia (uccelli, "
            "acqua), antropofonia urbana distante, voce umana come elemento "
            "drammaturgico."
        ),
        "spectral": {
            "centroid_hz_mean": 2600,
            "centroid_hz_std": 500,
            "rolloff_85_hz_mean": 7500,
            "flatness_mean": 0.14,
            "bands_pct": {
                "Sub-bass": 2, "Bass": 10, "Low-mid": 14, "Mid": 28,
                "High-mid": 24, "Presence": 14, "Brilliance": 8,
            },
        },
        "dynamic": {"dynamic_range_db": 32, "crest_db": 17, "integrated_lufs": -23},
        "ecoacoustic": {"aci": 2200, "ndsi": 0.1, "h_entropy": 0.78},
        "density": {"onset_per_sec": 2.0, "qualitative": "media"},
    }


def _init_presque_rien() -> dict:
    return {
        "id": "presque_rien",
        "title": "Presque Rien N. 1 - Le lever du jour au bord de la mer",
        "author": "Luc Ferrari",
        "year": 1970,
        "tradition": "musique anecdotique",
        "source_type": "literature_based",
        "sources_audio": [],
        "generated_at": date.today().isoformat(),
        "notes_it": (
            "Alba in un villaggio di pescatori di Vela Luka (Croazia), "
            "compressa in 21 minuti. Keynote di mare e silenzio, progressiva "
            "apparizione di voci e segnali umani. Editing concettualmente "
            "documentaristico ma compositivamente rigoroso."
        ),
        "spectral": {
            "centroid_hz_mean": 1600,
            "centroid_hz_std": 350,
            "rolloff_85_hz_mean": 5500,
            "flatness_mean": 0.22,
            "bands_pct": {
                "Sub-bass": 5, "Bass": 18, "Low-mid": 18, "Mid": 26,
                "High-mid": 18, "Presence": 10, "Brilliance": 5,
            },
        },
        "dynamic": {"dynamic_range_db": 35, "crest_db": 20, "integrated_lufs": -26},
        "ecoacoustic": {"aci": 1500, "ndsi": 0.05, "h_entropy": 0.8},
        "density": {"onset_per_sec": 0.9, "qualitative": "media"},
    }


def _init_great_animal_orchestra() -> dict:
    return {
        "id": "great_animal_orchestra",
        "title": "The Great Animal Orchestra (field recording corpus)",
        "author": "Bernie Krause",
        "year": 2012,
        "tradition": "ecoacoustica / biofonia",
        "source_type": "literature_based",
        "sources_audio": [],
        "generated_at": date.today().isoformat(),
        "notes_it": (
            "Corpus di field recording naturali in habitat intatti. Alta "
            "biofonia, nicchie acustiche occupate da specie diverse che "
            "evitano sovrapposizioni (ipotesi della nicchia acustica)."
        ),
        "spectral": {
            "centroid_hz_mean": 3200,
            "centroid_hz_std": 700,
            "rolloff_85_hz_mean": 9500,
            "flatness_mean": 0.12,
            "bands_pct": {
                "Sub-bass": 2, "Bass": 7, "Low-mid": 10, "Mid": 22,
                "High-mid": 28, "Presence": 20, "Brilliance": 11,
            },
        },
        "dynamic": {"dynamic_range_db": 28, "crest_db": 15, "integrated_lufs": -28},
        "ecoacoustic": {"aci": 2600, "ndsi": 0.6, "h_entropy": 0.85},
        "density": {"onset_per_sec": 4.5, "qualitative": "densa"},
    }


PROFILI_INIZIALI = {
    "de_natura_sonorum": _init_de_natura_sonorum,
    "kits_beach_soundwalk": _init_kits_beach_soundwalk,
    "presque_rien": _init_presque_rien,
    "great_animal_orchestra": _init_great_animal_orchestra,
}


def write_initial_profiles(overwrite: bool = False) -> list[str]:
    """Scrive i 4 profili letteratura-based se non esistono già (o se overwrite=True)."""
    config.PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    write_schema()
    created: list[str] = []
    for name, builder in PROFILI_INIZIALI.items():
        out = config.PROFILES_DIR / f"{name}.json"
        if out.exists() and not overwrite:
            continue
        dump_json(builder(), out)
        created.append(name)
    return created
