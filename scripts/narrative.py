"""Generatore di descrizione italiana segmentata (v0.2.2).

Non fa inferenza nuova. Prende il summary completo (technical, spectral,
ecoacoustic, classifier PANNs, clap) e compone una prosa descrittiva
italiana per finestre di 30 secondi.

Il risultato alimenta due cose:
1. Una nuova sezione "Descrizione segmentata" nel PDF.
2. Il payload passato all'agente compositivo (sostituisce la timeline
   grezza YAMNet/PANNs che causava timeout su file lunghi).
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import hashlib
import numpy as np

from . import config
from .locale_it import sanitize_italiano
from .serialization import load as load_json


PANNS_TAX_PATH = config.REFERENCES_DIR / "panns_taxonomy_it.json"

_OPENINGS_LEVELS = [
    "Il segmento si colloca",
    "Qui il materiale si presenta",
    "Questo blocco temporale",
    "Il contenuto",
]
_OPENINGS_SPECTRUM = [
    "Spettralmente",
    "Sul piano timbrico",
    "La distribuzione in frequenza",
]
_OPENINGS_EVENTS = [
    "Dal punto di vista degli eventi,",
    "A livello di attività,",
    "La grana temporale",
]


def _seed_int(key: str) -> int:
    """Hash stabile per selezionare varianti di apertura in modo deterministico."""
    return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)


def _pick(options: list[str], key: str) -> str:
    return options[_seed_int(key) % len(options)]


def _load_panns_taxonomy() -> dict[str, str]:
    try:
        data = load_json(PANNS_TAX_PATH)
        return data.get("translations", {})
    except Exception:
        return {}


_PANNS_IT: dict[str, str] = _load_panns_taxonomy()


def _translate_label(label: str) -> str:
    """Traduce una categoria AudioSet in italiano, fallback al nome originale."""
    return _PANNS_IT.get(label, label.lower())


@dataclass
class SegmentNarrative:
    t_start_s: float
    t_end_s: float
    t_start_str: str
    t_end_str: str
    narrative_it: str

    def to_dict(self) -> dict:
        return asdict(self)


def _fmt_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


def _describe_levels(rms_db: float, peak_db: float, seed_key: str) -> str:
    opening = _pick(_OPENINGS_LEVELS, seed_key + "_lev")
    if rms_db < -50:
        return f"{opening} su livelli molto bassi (RMS {rms_db:.1f} dBFS), in regione di quasi silenzio"
    if rms_db < -35:
        return f"{opening} a livelli ridotti (RMS {rms_db:.1f} dBFS, picco {peak_db:.1f} dBFS), senza saturazione"
    if rms_db < -20:
        return f"{opening} su dinamica moderata (RMS {rms_db:.1f} dBFS, picco {peak_db:.1f} dBFS)"
    return f"{opening} su livelli sostenuti (RMS {rms_db:.1f} dBFS, picco {peak_db:.1f} dBFS)"


def _describe_spectrum(centroid_hz: float, flatness: float,
                       dominant_band: str, seed_key: str) -> str:
    opening = _pick(_OPENINGS_SPECTRUM, seed_key + "_sp")
    if flatness < 0.05:
        flat_label = "spettro molto tonale"
    elif flatness < 0.2:
        flat_label = "spettro tendenzialmente tonale"
    elif flatness < 0.5:
        flat_label = "spettro misto tra tonale e rumoroso"
    else:
        flat_label = "spettro molto rumoroso"
    return (f"{opening} il centroide si colloca a {centroid_hz:.0f} Hz "
            f"sulla banda {dominant_band}, con {flat_label} (flatness {flatness:.3f})")


def _describe_events(n_events: int, density: float, seed_key: str) -> str:
    opening = _pick(_OPENINGS_EVENTS, seed_key + "_ev")
    if density < 0.3:
        return f"{opening} è rarefatta, nessun evento transiente significativo"
    if density < 1.0:
        return f"{opening} è sparsa con circa {n_events} onset ({density:.1f}/s)"
    if density < 2.5:
        return f"{opening} è media con {n_events} onset ({density:.1f}/s)"
    return f"{opening} è densa con {n_events} onset ({density:.1f}/s), sovrapposizioni frequenti"


def _describe_panns(top_categories: list[dict]) -> str:
    if not top_categories:
        return ""
    names = []
    for cat in top_categories[:3]:
        name = _translate_label(cat["name"])
        score = cat.get("score", 0.0)
        if score > 0.15:
            names.append(f"<b>{name}</b> ({score:.2f})")
        elif score > 0.03:
            names.append(f"{name} ({score:.2f})")
    if not names:
        return ""
    if len(names) == 1:
        return f"Il classificatore identifica prevalentemente {names[0]}"
    joined = ", ".join(names[:-1]) + f", più {names[-1]}"
    return f"Il classificatore identifica {joined}"


def _describe_clap(top_tags: list[dict]) -> str:
    if not top_tags:
        return ""
    names = []
    for t in top_tags[:3]:
        prompt = t.get("prompt") or ""
        score = t.get("score", 0.0)
        if score > 0.4:
            names.append(f"<i>{prompt}</i>")
        elif score > 0.25:
            names.append(prompt)
    if not names:
        # anche con score bassi mostriamo i tag principali come ipotesi di lavoro
        names = [t.get("prompt", "") for t in top_tags[:2]]
    return f"CLAP associa prevalentemente {', '.join(names)}"


def _classify_bands_dominant(bands: dict) -> str:
    if not bands:
        return "non determinata"
    dom = max(bands.items(), key=lambda kv: kv[1].get("energy_pct", 0))
    return dom[0]


def _rms_per_segment(waveform: np.ndarray, sr: int,
                     window_seconds: float) -> list[tuple[float, float, float, float]]:
    """Ritorna lista di (t_start, t_end, rms_db, peak_db) per ogni finestra."""
    import librosa
    chunk_samples = int(window_seconds * sr)
    n_chunks = max(1, int(np.ceil(len(waveform) / chunk_samples)))
    out = []
    for i in range(n_chunks):
        a = i * chunk_samples
        b = min(a + chunk_samples, len(waveform))
        chunk = waveform[a:b]
        if len(chunk) < sr * 0.1:
            continue
        rms = float(np.sqrt(np.mean(chunk ** 2)) + 1e-12)
        peak = float(np.max(np.abs(chunk)) + 1e-12)
        rms_db = 20 * np.log10(rms)
        peak_db = 20 * np.log10(peak)
        out.append((a / sr, b / sr, rms_db, peak_db))
    return out


def _aggregate_timeline_for_window(timeline: list[dict], t_start: float, t_end: float,
                                    key: str = "top") -> list[dict]:
    """Aggrega le top-K entries della timeline (PANNs o CLAP) che rientrano nella
    finestra [t_start, t_end] in un'unica lista top-3 ordinata per score medio."""
    scores: dict[str, tuple[float, int, str]] = {}
    # (total_score, count, category/label)
    label_key = "name" if key == "top" else "prompt"

    for entry in timeline:
        seg_start = entry.get("t_start_s", 0)
        seg_end = entry.get("t_end_s", 0)
        if seg_end <= t_start or seg_start >= t_end:
            continue
        for item in entry.get(key, []):
            name = item.get(label_key, "")
            score = float(item.get("score", 0.0))
            if name not in scores:
                scores[name] = (0.0, 0, item.get("category", ""))
            total, cnt, cat = scores[name]
            scores[name] = (total + score, cnt + 1, cat)

    out = []
    for name, (total, cnt, cat) in scores.items():
        avg = total / max(cnt, 1)
        out.append({
            "name": name,
            "prompt": name,
            "category": cat,
            "score": round(avg, 4),
        })
    out.sort(key=lambda x: -x["score"])
    return out[:5]


def build_full_narrative(
    summary: dict,
    waveform: np.ndarray,
    sr: int,
    window_seconds: float = config.NARRATIVE_WINDOW_S,
) -> list[SegmentNarrative]:
    """Costruisce la narrativa segmentata per tutto il file.

    `waveform` e `sr` devono essere coerenti (tipicamente la mono 22050 Hz
    usata nella pipeline tecnica).
    """
    bands = summary.get("spectral", {}).get("bands_schafer", {})
    dominant_band_global = _classify_bands_dominant(bands)
    timbre = summary.get("spectral", {}).get("timbre", {})
    centroid_global = timbre.get("spectral_centroid_hz", 0)
    flatness_global = timbre.get("spectral_flatness", 0)
    onsets = summary.get("spectral", {}).get("onsets", {})
    density_global = onsets.get("events_per_sec", 0)

    classifier_timeline = (summary.get("semantic", {}).get("classifier") or {}).get("timeline", [])
    clap_timeline = (summary.get("clap") or {}).get("timeline", [])

    segments = _rms_per_segment(waveform, sr, window_seconds)
    narratives: list[SegmentNarrative] = []
    for idx, (t_start, t_end, rms_db, peak_db) in enumerate(segments):
        seed_key = f"{idx}_{int(t_start)}"

        lev = _describe_levels(rms_db, peak_db, seed_key)
        spec = _describe_spectrum(centroid_global, flatness_global,
                                   dominant_band_global, seed_key)
        ev = _describe_events(
            int((t_end - t_start) * density_global),
            density_global, seed_key,
        )

        panns_win = _aggregate_timeline_for_window(classifier_timeline, t_start, t_end, key="top")
        panns_desc = _describe_panns(panns_win)

        clap_win = _aggregate_timeline_for_window(clap_timeline, t_start, t_end, key="tags")
        clap_desc = _describe_clap(clap_win)

        pieces = [lev, spec, ev]
        if panns_desc:
            pieces.append(panns_desc)
        if clap_desc:
            pieces.append(clap_desc)
        paragraph = ". ".join(pieces) + "."
        paragraph = sanitize_italiano(paragraph)

        narratives.append(SegmentNarrative(
            t_start_s=round(t_start, 2),
            t_end_s=round(t_end, 2),
            t_start_str=_fmt_time(t_start),
            t_end_str=_fmt_time(t_end),
            narrative_it=paragraph,
        ))

    return narratives


def narrative_to_markdown(narratives: list[SegmentNarrative | dict]) -> str:
    """Formato markdown con header '### MM:SS - MM:SS' e paragrafo."""
    lines: list[str] = []
    for n in narratives:
        d = n if isinstance(n, dict) else n.to_dict()
        lines.append(f"### {d['t_start_str']} - {d['t_end_str']}")
        lines.append("")
        lines.append(d["narrative_it"])
        lines.append("")
    return "\n".join(lines)


def narrative_summary(
    summary: dict,
    waveform: np.ndarray,
    sr: int,
    window_seconds: float = config.NARRATIVE_WINDOW_S,
    mode: str = "full",
) -> dict:
    """Wrapper che ritorna il dict serializzabile da inserire in summary['narrative']."""
    if mode == "none":
        return {"enabled": False, "mode": "none"}
    narratives = build_full_narrative(summary, waveform, sr, window_seconds)
    if mode == "summary" and len(narratives) > 12:
        # In summary mode, prende 12 finestre equispaziate per file molto lunghi
        step = max(1, len(narratives) // 12)
        narratives = narratives[::step][:12]
    return {
        "enabled": True,
        "mode": mode,
        "window_seconds": window_seconds,
        "segments": [n.to_dict() for n in narratives],
        "markdown": narrative_to_markdown(narratives),
    }
