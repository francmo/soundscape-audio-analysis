"""Generazione grafici matplotlib per il report PDF.

Backend Agg (non-interattivo), palette ABTEC40.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import config


def _style(ax):
    ax.grid(alpha=0.3)
    for spine in ax.spines.values():
        spine.set_color(config.PALETTE["muted_gray"])


def plot_waveform(y: np.ndarray, sr: int, out_path: Path, title: str = "Forma d'onda") -> Path:
    dur = len(y) / sr
    t = np.linspace(0, dur, len(y))
    fig, ax = plt.subplots(figsize=(12, 2.5))
    ax.plot(t, y, linewidth=0.3, color=config.PALETTE["dark"])
    ax.set_title(title, fontsize=10, color=config.PALETTE["dark"])
    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel("Ampiezza")
    ax.set_xlim(0, dur)
    _style(ax)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_spectrogram(y: np.ndarray, sr: int, out_path: Path, title: str = "Spettrogramma") -> Path:
    import librosa, librosa.display
    D = librosa.amplitude_to_db(
        np.abs(librosa.stft(y, n_fft=2048, hop_length=512)), ref=np.max
    )
    fig, ax = plt.subplots(figsize=(12, 4))
    img = librosa.display.specshow(D, sr=sr, hop_length=512, x_axis="time", y_axis="log",
                                    ax=ax, cmap="magma")
    ax.set_title(title, fontsize=10, color=config.PALETTE["dark"])
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_spectrum_mean(spectrum: np.ndarray, freqs: np.ndarray, out_path: Path,
                       title: str = "Spettro medio") -> Path:
    fig, ax = plt.subplots(figsize=(12, 3.2))
    y_db = 20 * np.log10(spectrum + 1e-12)
    ax.semilogx(freqs[1:], y_db[1:], color=config.PALETTE["teal"], linewidth=1.0)
    for name, lo, hi in config.SCHAFER_BANDS:
        ax.axvspan(lo, hi, alpha=0.04, color=config.PALETTE["terracotta"])
    ax.set_title(title, fontsize=10, color=config.PALETTE["dark"])
    ax.set_xlabel("Frequenza (Hz)")
    ax.set_ylabel("Modulo (dB)")
    ax.set_xlim(20, freqs[-1])
    _style(ax)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_bands_bar(bands: dict, out_path: Path, title: str = "Energia per banda") -> Path:
    names = list(bands.keys())
    vals = [bands[n]["energy_pct"] for n in names]
    fig, ax = plt.subplots(figsize=(10, 3.5))
    bars = ax.bar(names, vals, color=config.PALETTE["terracotta"], edgecolor=config.PALETTE["dark_mid"])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.3, f"{v:.1f}%",
                ha="center", va="bottom", fontsize=8, color=config.PALETTE["dark"])
    ax.set_title(title, fontsize=10, color=config.PALETTE["dark"])
    ax.set_ylabel("% energia")
    _style(ax)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_hum_zoom(peaks: list[dict], baseline_db: float, out_path: Path,
                  max_hz: int = 200) -> Path:
    fig, ax = plt.subplots(figsize=(10, 3.2))
    xs = [p["found_hz"] for p in peaks]
    ys = [p["magnitude_db"] for p in peaks]
    ax.bar(xs, ys, width=3, color=config.PALETTE["terracotta"], label="picchi misurati")
    ax.axhline(baseline_db, color=config.PALETTE["teal"], linestyle="--", label="baseline locale")
    ax.set_title("Hum check 0-200 Hz (baseline locale)", fontsize=10, color=config.PALETTE["dark"])
    ax.set_xlabel("Frequenza (Hz)")
    ax.set_ylabel("Modulo (dB)")
    ax.set_xlim(0, max_hz)
    ax.legend(fontsize=8)
    _style(ax)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_radar_profiles(summary_vec: dict, profile_vecs: dict[str, dict],
                        out_path: Path, title: str = "Confronto profili GRM") -> Path:
    """Radar chart su 7 bande Schafer."""
    bands = [b[0] for b in config.SCHAFER_BANDS]
    angles = np.linspace(0, 2 * np.pi, len(bands), endpoint=False).tolist()
    angles += angles[:1]

    def get_band(vec, band):
        return vec.get(f"band_{band}", 0) or 0

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    vals_file = [get_band(summary_vec, b) for b in bands]
    vals_file += vals_file[:1]
    ax.plot(angles, vals_file, color=config.PALETTE["dark"], linewidth=2, label="file analizzato")
    ax.fill(angles, vals_file, color=config.PALETTE["dark"], alpha=0.15)

    colors = [config.PALETTE["terracotta"], config.PALETTE["teal"],
              config.PALETTE["beige_warm"], config.PALETTE["dark_mid"]]
    for i, (pid, pvec) in enumerate(profile_vecs.items()):
        vals = [get_band(pvec, b) for b in bands]
        vals += vals[:1]
        ax.plot(angles, vals, color=colors[i % len(colors)], linewidth=1.5, label=pid)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(bands, fontsize=9)
    ax.set_ylim(0, max(40, max([max(vals_file)] + [1])) + 5)
    ax.set_title(title, fontsize=11, color=config.PALETTE["dark"], pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_structure_timeline(sections: list[dict], total_duration_s: float,
                             out_path: Path,
                             title: str = "Sezioni strutturali") -> Path:
    """Visualizza le sezioni strutturali (Blocco 2 v0.6.0) come bande
    orizzontali colorate per Krause dominante. Etichetta in alto:
    signature_label + range MM:SS-MM:SS. Per sezioni < 5% del totale,
    omette il range nella label per evitare sovrapposizioni."""
    fig, ax = plt.subplots(figsize=(12, 1.6))
    ax.set_xlim(0, total_duration_s)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def _fmt(t: float) -> str:
        m = int(t) // 60
        s = int(t) % 60
        return f"{m:02d}:{s:02d}"

    palette = config.STRUCTURE_TIMELINE_COLORS
    # Banda colorata per ogni sezione
    for s in sections:
        t0 = float(s["t_start_s"])
        t1 = float(s["t_end_s"])
        krause = s.get("krause", "mista")
        color = palette.get(krause, palette["mista"])
        ax.axvspan(t0, t1, ymin=0.10, ymax=0.70, color=color, alpha=0.85)
        # Linea verticale come confine sezione (eccetto inizio file)
        if t0 > 0.5:
            ax.axvline(t0, color=config.PALETTE["dark"], linewidth=0.7, alpha=0.6)

    # Etichette sopra le bande
    for s in sections:
        t0 = float(s["t_start_s"])
        t1 = float(s["t_end_s"])
        mid = (t0 + t1) / 2.0
        sig = (s.get("signature_label") or "")[:30]
        pct = (t1 - t0) / max(total_duration_s, 1e-6)
        if pct < 0.05:
            label = sig
        else:
            label = f"{sig}\n{_fmt(t0)}-{_fmt(t1)}"
        ax.text(mid, 0.85, label, ha="center", va="center",
                 fontsize=7, color=config.PALETTE["dark"], wrap=True)

    # Asse temporale schematico in basso
    ax.text(0, 0.02, "00:00", ha="left", va="bottom",
             fontsize=7, color=config.PALETTE["muted_gray"])
    ax.text(total_duration_s, 0.02, _fmt(total_duration_s),
             ha="right", va="bottom",
             fontsize=7, color=config.PALETTE["muted_gray"])
    ax.set_title(title, fontsize=10, color=config.PALETTE["dark"])

    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_tags_timeline(dominant_windows: list[dict], total_duration_s: float,
                       out_path: Path,
                       title: str = "Timeline famiglie semantiche CLAP") -> Path:
    """v0.12.1: timeline grafica delle famiglie semantiche CLAP.

    Input: lista di `{t_start_s, t_end_s, family, label, color, score}`
    come prodotta da `clap_families.dominant_family_per_window`.

    Rende una barra orizzontale continua con colori per famiglia dominante.
    Legenda compatta sotto. Sostituisce le tabelle "top-3 per segmento"
    che oggi occupano 5+ pagine del PDF.
    """
    if not dominant_windows:
        return out_path
    fig, ax = plt.subplots(figsize=(12, 1.8))
    ax.set_xlim(0, total_duration_s)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Raccolta famiglie uniche per legenda
    family_seen: dict[str, tuple[str, str]] = {}  # key -> (label, color)
    for w in dominant_windows:
        fam = w.get("family")
        if fam and fam not in family_seen:
            family_seen[fam] = (w.get("label", fam), w.get("color", "#808080"))

    # Banda colorata per ogni finestra
    for w in dominant_windows:
        t0 = float(w["t_start_s"])
        t1 = float(w["t_end_s"])
        color = w.get("color", "#808080")
        score = float(w.get("score", 0.0))
        alpha = min(0.35 + score, 1.0)  # score piu' alto = piu' saturo
        ax.axvspan(t0, t1, ymin=0.25, ymax=0.80, color=color, alpha=alpha)

    # Asse temporale
    def _fmt(t: float) -> str:
        m = int(t) // 60
        s = int(t) % 60
        return f"{m:02d}:{s:02d}"

    ax.text(0, 0.90, "00:00", ha="left", va="bottom",
            fontsize=7, color=config.PALETTE["muted_gray"])
    ax.text(total_duration_s, 0.90, _fmt(total_duration_s),
            ha="right", va="bottom",
            fontsize=7, color=config.PALETTE["muted_gray"])

    # Legenda in basso
    legend_patches = [
        plt.Rectangle((0, 0), 1, 1, color=col, alpha=0.85, label=lab)
        for (lab, col) in family_seen.values()
    ]
    ax.legend(
        handles=legend_patches,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.20),
        ncol=min(len(legend_patches), 4),
        fontsize=7,
        frameon=False,
    )
    ax.set_title(title, fontsize=10, color=config.PALETTE["dark"])
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_all_plots(y: np.ndarray, sr: int, spectrum: np.ndarray, freqs: np.ndarray,
                      bands: dict, hum_result: dict, out_dir: Path, base: str) -> dict:
    """Genera tutti i grafici standard e ritorna mapping nome -> path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    files["waveform"] = plot_waveform(y, sr, out_dir / f"{base}_waveform.png",
                                       title=f"Forma d'onda - {base}")
    files["spectrogram"] = plot_spectrogram(y, sr, out_dir / f"{base}_spettrogramma.png")
    files["spectrum_mean"] = plot_spectrum_mean(spectrum, freqs, out_dir / f"{base}_spettro_medio.png")
    files["bands_bar"] = plot_bands_bar(bands, out_dir / f"{base}_bande.png")
    files["hum_zoom"] = plot_hum_zoom(hum_result["peaks"], hum_result["baseline_db"],
                                       out_dir / f"{base}_hum.png")
    return files
