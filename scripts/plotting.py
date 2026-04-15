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
