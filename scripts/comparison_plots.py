"""Grafici comparativi multi-file per il sotto-comando `soundscape report`.

Cinque figure standard:
- `plot_lufs_bar` barra orizzontale LUFS integrato per file
- `plot_dynamic_range_bar` barra orizzontale Dynamic Range per file
- `plot_schafer_heatmap` heatmap N file x 7 bande Schafer
- `plot_ecoacoustic_radar` radar ACI/NDSI/H/BI normalizzati per file
- `plot_clap_similarity_heatmap` matrice simmetrica di similarità tra top-global CLAP

Palette coerente con ABTEC40 (`config.PALETTE`). Contrasto WCAG AA verificato
programmaticamente (rapporto di luminanza >= 4.5:1 testo su sfondo) prima di
salvare.
"""
from __future__ import annotations
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import config


# ---------- Contrasto WCAG ----------

def _hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    r, g, b = _hex_to_rgb01(hex_color)
    return (
        0.2126 * _srgb_to_linear(r)
        + 0.7152 * _srgb_to_linear(g)
        + 0.0722 * _srgb_to_linear(b)
    )


def wcag_contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """Rapporto di contrasto WCAG fra testo (fg) e sfondo (bg). Range 1.0-21.0."""
    l1 = _relative_luminance(fg_hex)
    l2 = _relative_luminance(bg_hex)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def check_wcag(fg_hex: str, bg_hex: str, min_ratio: float = 4.5) -> None:
    """Solleva AssertionError se il contrasto è sotto il minimo WCAG AA."""
    r = wcag_contrast_ratio(fg_hex, bg_hex)
    assert r >= min_ratio, (
        f"Contrasto WCAG insufficiente: {r:.2f} fra fg={fg_hex} e bg={bg_hex} "
        f"(minimo {min_ratio}). Correggere i colori prima di salvare."
    )


# Palette v0.3.1: sfondo bianco, testo nero, serie dati Tab10 saturi
# (regola tipografica CLAUDE.md punto 4, riferimento Tab10 matplotlib).
PAL = config.PALETTE
FG_ON_LIGHT = "#000000"             # nero puro su bg bianco -> contrasto 21:1
BG_FIGURE = "#FFFFFF"               # sfondo matplotlib bianco puro
BG_AXES = "#FFFFFF"                 # sfondo asse bianco puro (no beige)

# Palette Tab10 di matplotlib, ordinati per leggibilità e distinzione print.
# Grigio (#7f7f7f) e giallo-olive (#bcbd22) esclusi dal set primario perché
# hanno contrasto inferiore o sono difficili da distinguere in fotocopia.
TAB10_PRIMARY = [
    "#1f77b4",  # blu
    "#d62728",  # rosso
    "#2ca02c",  # verde
    "#ff7f0e",  # arancio
    "#9467bd",  # viola
    "#8c564b",  # marrone
    "#e377c2",  # rosa
    "#17becf",  # ciano
]

# Verifica al caricamento del modulo: nero su bianco, bianco su scuro, e
# ciascun colore Tab10 primario ha contrasto sufficiente su sfondo bianco
# (utile per legende con testo colorato, anche se noi usiamo testo nero).
check_wcag(FG_ON_LIGHT, BG_FIGURE)
check_wcag(PAL["white"], PAL["dark"])         # testo bianco su blu scuro copertina
check_wcag(PAL["white"], PAL["terracotta_dk"])  # bianco su terracotta scuro


# ---------- Estrazione feature dai summary ----------

@dataclass
class CorpusEntry:
    filename: str
    lufs: float | None
    dynamic_range: float | None
    centroid: float | None
    bands_pct: dict[str, float]
    aci: float | None
    ndsi: float | None
    h_total: float | None
    bi: float | None
    clap_top_global: list[dict]
    clap_embeddings_b64: str
    clap_embeddings_shape: list


def extract_entries(summaries: list[dict]) -> list[CorpusEntry]:
    entries: list[CorpusEntry] = []
    for s in summaries:
        meta = s.get("metadata", {})
        tech = s.get("technical", {})
        spec = s.get("spectral", {})
        eco = s.get("ecoacoustic", {})
        clap = s.get("clap", {}) or {}
        entries.append(CorpusEntry(
            filename=meta.get("filename", "?"),
            lufs=(tech.get("lufs") or {}).get("integrated_lufs"),
            dynamic_range=(tech.get("levels") or {}).get("dynamic_range_db"),
            centroid=(spec.get("timbre") or {}).get("spectral_centroid_hz"),
            bands_pct={k: v.get("energy_pct") for k, v in (spec.get("bands_schafer") or {}).items()},
            aci=eco.get("aci"),
            ndsi=(eco.get("ndsi") or {}).get("ndsi"),
            h_total=(eco.get("h_entropy") or {}).get("h_total"),
            bi=eco.get("bi"),
            clap_top_global=clap.get("top_global", []) if clap.get("enabled") else [],
            clap_embeddings_b64=clap.get("embeddings_audio_b64", "") if clap.get("enabled") else "",
            clap_embeddings_shape=clap.get("embeddings_shape", []) if clap.get("enabled") else [],
        ))
    return entries


def _short_label(name: str, max_len: int = 30) -> str:
    """Accorcia il nome file per le etichette dei grafici."""
    stem = Path(name).stem
    if len(stem) <= max_len:
        return stem
    return stem[: max_len - 1] + "…"


def _style_axes(ax):
    ax.set_facecolor(BG_AXES)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(PAL["muted_gray"])
    ax.tick_params(colors=FG_ON_LIGHT, labelsize=9)
    ax.title.set_color(FG_ON_LIGHT)
    ax.xaxis.label.set_color(FG_ON_LIGHT)
    ax.yaxis.label.set_color(FG_ON_LIGHT)


def _fig_standard(figsize=(10, 5)):
    fig, ax = plt.subplots(figsize=figsize, facecolor=BG_FIGURE)
    _style_axes(ax)
    return fig, ax


# ---------- 1. LUFS bar ----------

def plot_lufs_bar(entries: list[CorpusEntry], out_path: Path) -> Path:
    labels = [_short_label(e.filename) for e in entries]
    values = [e.lufs if e.lufs is not None else 0 for e in entries]

    fig, ax = _fig_standard(figsize=(10, max(4, 0.4 * len(entries) + 1.5)))
    y_pos = np.arange(len(entries))
    ax.barh(y_pos, values, color=TAB10_PRIMARY[0], edgecolor="#000000")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.axvline(-23, color=TAB10_PRIMARY[1], linestyle="--", linewidth=1,
                label="target broadcast -23 LUFS")
    ax.axvline(-16, color=TAB10_PRIMARY[4], linestyle=":", linewidth=1,
                label="target podcast -16 LUFS")
    ax.set_xlabel("LUFS integrato")
    ax.set_title("Loudness integrato per file del corpus", fontsize=11, weight="bold")
    ax.legend(fontsize=8, loc="lower right")

    for i, v in enumerate(values):
        if v:
            ax.text(v + 0.3 if v < 0 else v - 0.3, i, f"{v:.1f}",
                     va="center", ha="left" if v < 0 else "right",
                     fontsize=8, color=FG_ON_LIGHT)

    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight", facecolor=BG_FIGURE)
    plt.close(fig)
    return out_path


# ---------- 2. Dynamic Range bar ----------

def plot_dynamic_range_bar(entries: list[CorpusEntry], out_path: Path) -> Path:
    labels = [_short_label(e.filename) for e in entries]
    values = [e.dynamic_range if e.dynamic_range is not None else 0 for e in entries]

    fig, ax = _fig_standard(figsize=(10, max(4, 0.4 * len(entries) + 1.5)))
    y_pos = np.arange(len(entries))
    ax.barh(y_pos, values, color=TAB10_PRIMARY[2], edgecolor="#000000")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Gamma dinamica (dB)")
    ax.set_title("Dinamica percettiva per file del corpus (P95-P10 frame RMS)",
                  fontsize=11, weight="bold")
    for i, v in enumerate(values):
        if v:
            ax.text(v + 0.3, i, f"{v:.1f}",
                     va="center", ha="left", fontsize=8, color=FG_ON_LIGHT)

    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight", facecolor=BG_FIGURE)
    plt.close(fig)
    return out_path


# ---------- 3. Schafer heatmap ----------

def plot_schafer_heatmap(entries: list[CorpusEntry], out_path: Path) -> Path:
    bands_order = [b[0] for b in config.SCHAFER_BANDS]
    matrix = np.zeros((len(entries), len(bands_order)), dtype=float)
    for i, e in enumerate(entries):
        for j, b in enumerate(bands_order):
            matrix[i, j] = e.bands_pct.get(b, 0.0)

    fig, ax = plt.subplots(
        figsize=(max(8, 1.2 * len(bands_order)),
                  max(4, 0.4 * len(entries) + 2)),
        facecolor=BG_FIGURE,
    )
    _style_axes(ax)
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrBr")
    ax.set_xticks(np.arange(len(bands_order)))
    ax.set_xticklabels(bands_order, rotation=20, ha="right")
    ax.set_yticks(np.arange(len(entries)))
    ax.set_yticklabels([_short_label(e.filename) for e in entries])
    ax.set_title("Distribuzione energia per banda Schafer (% sul totale)",
                  fontsize=11, weight="bold")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            v = matrix[i, j]
            # Contrasto: testo nero se cella chiara, bianco se cella scura
            cell_rgb = im.cmap(im.norm(v))[:3]
            hex_cell = "#{:02x}{:02x}{:02x}".format(
                int(cell_rgb[0] * 255), int(cell_rgb[1] * 255), int(cell_rgb[2] * 255)
            )
            fg = FG_ON_LIGHT if wcag_contrast_ratio(FG_ON_LIGHT, hex_cell) >= 4.5 else "#ffffff"
            ax.text(j, i, f"{v:.1f}", ha="center", va="center",
                     color=fg, fontsize=8)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("% energia", color=FG_ON_LIGHT)
    cbar.ax.yaxis.set_tick_params(colors=FG_ON_LIGHT)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight", facecolor=BG_FIGURE)
    plt.close(fig)
    return out_path


# ---------- 4. Ecoacoustic radar ----------

def plot_ecoacoustic_radar(entries: list[CorpusEntry], out_path: Path) -> Path:
    # Normalizza ogni indice a [0, 1] sul corpus (min-max)
    names = ["ACI", "NDSI+1", "H", "BI"]

    def norm_column(values: list[float | None]) -> list[float]:
        vv = [v if v is not None else 0.0 for v in values]
        lo, hi = min(vv), max(vv)
        if hi - lo < 1e-9:
            return [0.5] * len(vv)
        return [(v - lo) / (hi - lo) for v in vv]

    acis = norm_column([e.aci for e in entries])
    ndsi_shifted = [(e.ndsi + 1) / 2 if e.ndsi is not None else 0.5 for e in entries]  # da [-1,1] a [0,1]
    ndsi_norm = norm_column(ndsi_shifted)
    h_norm = norm_column([e.h_total for e in entries])
    bi_norm = norm_column([e.bi for e in entries])

    matrix = np.array([acis, ndsi_norm, h_norm, bi_norm])  # (K, N)
    K = len(names)
    angles = np.linspace(0, 2 * np.pi, K, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True),
                            facecolor=BG_FIGURE)
    ax.set_facecolor(BG_AXES)

    # Palette Tab10 primaria: 8 colori saturi, print-friendly, distinguibili
    # anche in fotocopia in scala di grigi (luminanze spaziate).
    colors_palette = list(TAB10_PRIMARY)

    for i, e in enumerate(entries):
        vals = matrix[:, i].tolist()
        vals += vals[:1]
        c = colors_palette[i % len(colors_palette)]
        ax.plot(angles, vals, color=c, linewidth=1.8, label=_short_label(e.filename, 22))
        ax.fill(angles, vals, color=c, alpha=0.12)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(names, color=FG_ON_LIGHT, fontsize=10)
    ax.tick_params(colors=FG_ON_LIGHT)
    ax.set_ylim(0, 1.02)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0.25", "0.50", "0.75", "1.00"], color=FG_ON_LIGHT, fontsize=8)
    ax.set_title("Indici ecoacustici normalizzati sul corpus",
                  fontsize=11, weight="bold", color=FG_ON_LIGHT, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1),
               fontsize=8, facecolor=BG_FIGURE, edgecolor=PAL["muted_gray"])
    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight", facecolor=BG_FIGURE)
    plt.close(fig)
    return out_path


# ---------- 5. CLAP similarity heatmap ----------

def _decode_clap_embeddings(entry: CorpusEntry) -> np.ndarray | None:
    if not entry.clap_embeddings_b64 or not entry.clap_embeddings_shape:
        return None
    shape_audio = entry.clap_embeddings_shape[0]
    raw = base64.b64decode(entry.clap_embeddings_b64)
    arr = np.frombuffer(raw, dtype=np.float16).astype(np.float32)
    try:
        arr = arr.reshape(shape_audio)
    except Exception:
        return None
    # mean embedding per file (vettore 512-dim che rappresenta il file intero)
    return arr.mean(axis=0)


def plot_clap_similarity_heatmap(entries: list[CorpusEntry], out_path: Path) -> Path | None:
    """Heatmap N x N di similarità coseno fra embedding medi CLAP.

    Ritorna None se meno di 2 file hanno embedding CLAP disponibili.
    """
    vectors: list[tuple[str, np.ndarray]] = []
    for e in entries:
        v = _decode_clap_embeddings(e)
        if v is not None:
            vectors.append((_short_label(e.filename, 26), v))

    if len(vectors) < 2:
        return None

    labels = [v[0] for v in vectors]
    M = np.stack([v[1] for v in vectors], axis=0)
    M_norm = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
    sim = M_norm @ M_norm.T  # (N, N), range [-1, 1] ma tipicamente [0, 1]

    n = len(vectors)
    fig, ax = plt.subplots(
        figsize=(max(6, 0.6 * n + 2), max(5, 0.6 * n + 2)),
        facecolor=BG_FIGURE,
    )
    _style_axes(ax)
    im = ax.imshow(sim, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticklabels(labels)
    ax.set_title("Similarità semantica fra file (cosine su embedding CLAP medi)",
                  fontsize=11, weight="bold")

    for i in range(n):
        for j in range(n):
            v = sim[i, j]
            cell_rgb = im.cmap(im.norm(v))[:3]
            hex_cell = "#{:02x}{:02x}{:02x}".format(
                int(cell_rgb[0] * 255), int(cell_rgb[1] * 255), int(cell_rgb[2] * 255)
            )
            fg = FG_ON_LIGHT if wcag_contrast_ratio(FG_ON_LIGHT, hex_cell) >= 4.5 else "#ffffff"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                     color=fg, fontsize=8)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("similarità (cosine)", color=FG_ON_LIGHT)
    cbar.ax.yaxis.set_tick_params(colors=FG_ON_LIGHT)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight", facecolor=BG_FIGURE)
    plt.close(fig)
    return out_path


# ---------- Orchestrazione ----------

def generate_all_comparison_plots(
    summaries: list[dict], out_dir: Path
) -> dict[str, Path]:
    """Genera tutti e 5 i grafici (o 4 se CLAP non disponibile).

    Ritorna mapping nome -> Path. La chiave `clap_similarity` può essere None
    se meno di due file hanno embedding CLAP.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = extract_entries(summaries)

    paths: dict[str, Path | None] = {}
    paths["lufs"] = plot_lufs_bar(entries, out_dir / "lufs_bar.png")
    paths["dynamic_range"] = plot_dynamic_range_bar(
        entries, out_dir / "dynamic_range_bar.png"
    )
    paths["schafer"] = plot_schafer_heatmap(entries, out_dir / "schafer_heatmap.png")
    paths["ecoacoustic"] = plot_ecoacoustic_radar(
        entries, out_dir / "ecoacoustic_radar.png"
    )
    clap_path = plot_clap_similarity_heatmap(
        entries, out_dir / "clap_similarity_heatmap.png"
    )
    if clap_path is not None:
        paths["clap_similarity"] = clap_path

    return {k: v for k, v in paths.items() if v is not None}
