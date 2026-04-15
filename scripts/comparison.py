"""Confronto tra summary di un file e profili GRM di riferimento.

Cosine similarity su feature vector standard. Ranking dei profili.
Narrativa italiana che rende leggibile il confronto nel PDF.
"""
from typing import Any
import numpy as np

from . import config


FEATURE_KEYS = [
    "centroid_hz", "flatness", "dynamic_range_db", "integrated_lufs",
    "ndsi", "onset_per_sec",
    "band_Sub-bass", "band_Bass", "band_Low-mid", "band_Mid",
    "band_High-mid", "band_Presence", "band_Brilliance",
]


def extract_vector(summary: dict) -> dict:
    """Estrae le feature numeriche confrontabili dal summary del file analizzato."""
    spec = summary.get("spectral", {})
    tech = summary.get("technical", {})
    eco = summary.get("ecoacoustic", {})
    bands = spec.get("bands_schafer", {})
    vec = {
        "centroid_hz": spec.get("timbre", {}).get("spectral_centroid_hz"),
        "flatness": spec.get("timbre", {}).get("spectral_flatness"),
        "dynamic_range_db": tech.get("levels", {}).get("dynamic_range_db"),
        "integrated_lufs": tech.get("lufs", {}).get("integrated_lufs"),
        "ndsi": (eco.get("ndsi") or {}).get("ndsi"),
        "onset_per_sec": spec.get("onsets", {}).get("events_per_sec"),
    }
    for band, info in bands.items():
        vec[f"band_{band}"] = info.get("energy_pct")
    return vec


def extract_profile_vector(profile: dict) -> dict:
    """Estrae il feature vector da un profilo GRM."""
    ps = profile.get("spectral", {})
    pd = profile.get("dynamic", {})
    pe = profile.get("ecoacoustic", {})
    pn = profile.get("density", {})
    vec = {
        "centroid_hz": ps.get("centroid_hz_mean"),
        "flatness": ps.get("flatness_mean"),
        "dynamic_range_db": pd.get("dynamic_range_db"),
        "integrated_lufs": pd.get("integrated_lufs"),
        "ndsi": pe.get("ndsi"),
        "onset_per_sec": pn.get("onset_per_sec"),
    }
    for band, pct in (ps.get("bands_pct") or {}).items():
        vec[f"band_{band}"] = pct
    return vec


def _vectorize(vec: dict) -> np.ndarray:
    return np.array([vec.get(k, np.nan) for k in FEATURE_KEYS], dtype=float)


def _zscore_normalize(matrix: np.ndarray) -> np.ndarray:
    mean = np.nanmean(matrix, axis=0)
    std = np.nanstd(matrix, axis=0) + 1e-12
    return (matrix - mean) / std


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    mask = ~np.isnan(a) & ~np.isnan(b)
    if mask.sum() == 0:
        return 1.0
    aa = a[mask]
    bb = b[mask]
    denom = (np.linalg.norm(aa) * np.linalg.norm(bb)) + 1e-12
    cos_sim = float(np.dot(aa, bb) / denom)
    return 1.0 - cos_sim  # distanza: 0 identici, 2 opposti


def compare_to_profile(summary: dict, profile: dict) -> dict:
    """Confronto: distanza cosine + delta per feature + narrativa italiana."""
    v_file = extract_vector(summary)
    v_prof = extract_profile_vector(profile)
    a = _vectorize(v_file)
    b = _vectorize(v_prof)

    matrix = np.vstack([a, b])
    z = _zscore_normalize(matrix)
    z = np.nan_to_num(z, nan=0.0)
    dist = cosine_distance(z[0], z[1])

    deltas = {}
    for key in FEATURE_KEYS:
        vf = v_file.get(key)
        vp = v_prof.get(key)
        if vf is None or vp is None:
            continue
        deltas[key] = round(float(vf) - float(vp), 3)

    narrative = _narrative(profile, v_file, v_prof, deltas)

    return {
        "profile_id": profile.get("id"),
        "profile_title": profile.get("title"),
        "profile_author": profile.get("author"),
        "source_type": profile.get("source_type"),
        "cosine_distance": round(dist, 4),
        "deltas": deltas,
        "narrative_it": narrative,
    }


def _narrative(profile: dict, v_file: dict, v_prof: dict, deltas: dict) -> str:
    """Genera un paragrafo italiano che interpreta il confronto."""
    pieces: list[str] = []
    author = profile.get("author", "riferimento")
    title = profile.get("title", "")

    cent_d = deltas.get("centroid_hz")
    if cent_d is not None:
        if cent_d > 400:
            pieces.append(f"centroide spettrale più alto di {cent_d:.0f} Hz rispetto a {author}, timbro più brillante")
        elif cent_d < -400:
            pieces.append(f"centroide spettrale più basso di {abs(cent_d):.0f} Hz rispetto a {author}, timbro più scuro")
        else:
            pieces.append(f"centroide timbrico comparabile a {author}")

    dr_d = deltas.get("dynamic_range_db")
    if dr_d is not None:
        if dr_d > 5:
            pieces.append(f"dinamica più ampia di {dr_d:.1f} dB")
        elif dr_d < -5:
            pieces.append(f"dinamica più ridotta di {abs(dr_d):.1f} dB")

    ndsi_d = deltas.get("ndsi")
    if ndsi_d is not None and abs(ndsi_d) > 0.15:
        if ndsi_d > 0:
            pieces.append("maggiore presenza biofonica")
        else:
            pieces.append("maggiore presenza antropofonica")

    onset_d = deltas.get("onset_per_sec")
    if onset_d is not None:
        if onset_d > 1.5:
            pieces.append("densità di eventi molto superiore")
        elif onset_d < -1.5:
            pieces.append("densità di eventi inferiore")

    if not pieces:
        return f"Profilo paragonabile a {title} di {author} nei parametri principali."
    return f"Rispetto a {title} di {author}: " + ", ".join(pieces) + "."


def rank_profiles(summary: dict, profiles: dict[str, dict]) -> list[dict]:
    """Ordina i profili dal più simile al meno simile."""
    results = [compare_to_profile(summary, p) for p in profiles.values()]
    results.sort(key=lambda r: r["cosine_distance"])
    return results


def compare_multi(summaries: list[dict]) -> dict:
    """Per N file, confronto reciproco: distanze, outlier, clustering gerarchico."""
    if len(summaries) < 2:
        return {"reason": "meno di 2 file, confronto incrociato non applicabile"}

    matrix = np.array([_vectorize(extract_vector(s)) for s in summaries])
    z = _zscore_normalize(matrix)
    z = np.nan_to_num(z, nan=0.0)
    n = len(summaries)
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = cosine_distance(z[i], z[j])
            dist_matrix[i, j] = d
            dist_matrix[j, i] = d

    z_scores_per_file = np.nanmean(np.abs(z), axis=1)
    outlier_idx = [int(i) for i, zs in enumerate(z_scores_per_file) if zs > 2.0]

    return {
        "filenames": [s.get("metadata", {}).get("filename", f"file_{i}") for i, s in enumerate(summaries)],
        "distance_matrix": dist_matrix.tolist(),
        "outlier_indexes": outlier_idx,
    }
