"""Test dei 5 grafici comparativi (v0.3.0).

Genera summary fittizi minimi, produce i PNG e verifica dimensione minima.
Valida anche la funzione helper `wcag_contrast_ratio`.
"""
import pytest
from pathlib import Path
from tests.conftest import FIXTURES_DIR, ensure_fixtures  # noqa
from scripts import comparison_plots as cp


def _fake_summary(i: int, with_clap: bool = True) -> dict:
    return {
        "metadata": {"filename": f"file_{i:02d}.wav", "duration_s": 60 + i * 10},
        "technical": {
            "levels": {"dynamic_range_db": 15 + i, "rms_dbfs": -20 - i,
                        "peak_dbfs": -3, "crest_db": 15, "noise_floor_db": -50},
            "lufs": {"integrated_lufs": -23 - i, "true_peak_db": -1, "lra": 10},
            "clipping": {"verdict": "assente"},
            "dc_offset": {"verdict": "ok"},
        },
        "hum": {"overall_verdict": "trascurabile"},
        "spectral": {
            "timbre": {"spectral_centroid_hz": 1200 + i * 200,
                        "spectral_rolloff_hz": 4000, "spectral_flatness": 0.1 + i * 0.05},
            "bands_schafer": {
                "Sub-bass": {"energy_pct": 5 + i, "energy_db": -10, "range_hz": [20, 60]},
                "Bass": {"energy_pct": 20 + i * 2, "energy_db": -5, "range_hz": [60, 250]},
                "Low-mid": {"energy_pct": 15, "energy_db": -7, "range_hz": [250, 500]},
                "Mid": {"energy_pct": 25 - i, "energy_db": -5, "range_hz": [500, 2000]},
                "High-mid": {"energy_pct": 15 - i, "energy_db": -8, "range_hz": [2000, 4000]},
                "Presence": {"energy_pct": 10, "energy_db": -12, "range_hz": [4000, 6000]},
                "Brilliance": {"energy_pct": 10 - i, "energy_db": -15, "range_hz": [6000, 20000]},
            },
            "hifi_lofi": {"label": "Medio", "score_5": 3},
            "top_peaks_hz": [],
            "onsets": {"events_per_sec": 1.5},
        },
        "ecoacoustic": {
            "aci": 1500 + i * 500,
            "ndsi": {"ndsi": -0.3 + i * 0.2},
            "h_entropy": {"h_total": 0.5 + i * 0.1, "h_spectral": 0.6, "h_temporal": 0.8},
            "bi": 6000 + i * 1000,
        },
        "semantic": {"enabled": False},
        "clap": (
            {
                "enabled": True,
                "model_name": "LAION-CLAP",
                "vocabulary_size": 70,
                "top_global": [{"prompt": "test", "score": 0.3}],
                "embeddings_audio_b64": "",
                "embeddings_shape": [],
            }
            if with_clap else {"enabled": False}
        ),
    }


def test_wcag_contrast_ratio_black_on_white():
    r = cp.wcag_contrast_ratio("#000000", "#ffffff")
    assert r >= 20  # massimo teorico 21


def test_wcag_contrast_ratio_equal_colors():
    r = cp.wcag_contrast_ratio("#1a2a3a", "#1a2a3a")
    assert r == pytest.approx(1.0, abs=0.01)


def test_wcag_white_on_palette_dark():
    from scripts.config import PALETTE
    r = cp.wcag_contrast_ratio(PALETTE["white"], PALETTE["dark"])
    assert r >= 4.5


def test_plot_lufs_bar(tmp_path):
    summaries = [_fake_summary(i) for i in range(3)]
    out = tmp_path / "lufs.png"
    cp.plot_lufs_bar(cp.extract_entries(summaries), out)
    assert out.exists() and out.stat().st_size > 3000


def test_plot_dynamic_range_bar(tmp_path):
    summaries = [_fake_summary(i) for i in range(3)]
    out = tmp_path / "dr.png"
    cp.plot_dynamic_range_bar(cp.extract_entries(summaries), out)
    assert out.exists() and out.stat().st_size > 3000


def test_plot_schafer_heatmap(tmp_path):
    summaries = [_fake_summary(i) for i in range(3)]
    out = tmp_path / "schafer.png"
    cp.plot_schafer_heatmap(cp.extract_entries(summaries), out)
    assert out.exists() and out.stat().st_size > 5000


def test_plot_ecoacoustic_radar(tmp_path):
    summaries = [_fake_summary(i) for i in range(3)]
    out = tmp_path / "radar.png"
    cp.plot_ecoacoustic_radar(cp.extract_entries(summaries), out)
    assert out.exists() and out.stat().st_size > 5000


def test_plot_clap_similarity_returns_none_without_embeddings(tmp_path):
    summaries = [_fake_summary(i) for i in range(3)]  # embeddings_audio_b64=""
    out = tmp_path / "clap.png"
    result = cp.plot_clap_similarity_heatmap(cp.extract_entries(summaries), out)
    # None perché gli embedding sono vuoti
    assert result is None


def test_generate_all_comparison_plots_full(tmp_path):
    summaries = [_fake_summary(i) for i in range(3)]
    paths = cp.generate_all_comparison_plots(summaries, tmp_path)
    # Almeno 4 grafici (clap skippato senza embedding)
    assert len(paths) >= 4
    for name, p in paths.items():
        assert Path(p).exists(), f"{name}: file non creato"
