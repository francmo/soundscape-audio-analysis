"""Test della release v0.19.1 (addendum performance 12/07/2026).

Coprono i fix a rischio zero: cache dei classifier, cache degli embedding
dei prompt CLAP, cap dei thread, decimazione dei grafici. Tutti leggeri,
nessun modello reale caricato.
"""
import numpy as np
import pytest

from scripts import config
from scripts import runtime
from scripts import plotting
from scripts import semantic
from scripts import semantic_clap


# ------------------------------------------------------------------ runtime

def test_apply_thread_caps_sets_env(monkeypatch):
    for var in runtime._THREAD_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    n = runtime.apply_thread_caps(3)
    assert n == 3
    import os
    for var in runtime._THREAD_ENV_VARS:
        assert os.environ[var] == "3"
    assert runtime.effective_threads() == 3


def test_apply_thread_caps_respects_user_env(monkeypatch):
    monkeypatch.setenv("OMP_NUM_THREADS", "7")
    runtime.apply_thread_caps(2)
    import os
    # setdefault: il valore utente non viene sovrascritto
    assert os.environ["OMP_NUM_THREADS"] == "7"


def test_auto_threads_floor():
    assert runtime._auto_threads() >= 4


def test_set_low_impact_applies_cap_without_failing(monkeypatch):
    import os
    calls = {}
    monkeypatch.setattr(os, "setpriority",
                        lambda which, who, prio: calls.setdefault("prio", prio),
                        raising=False)
    for var in runtime._THREAD_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    n = runtime.set_low_impact(verbose=False)
    assert n == config.LOW_IMPACT_THREADS
    assert calls.get("prio") == config.LOW_IMPACT_NICE


# ------------------------------------------------- cache classifier (A1)

def test_get_classifier_cache_returns_same_instance():
    semantic.clear_classifier_cache()
    a = semantic.get_classifier("panns")
    b = semantic.get_classifier("panns")
    assert a is b
    semantic.clear_classifier_cache()
    c = semantic.get_classifier("panns")
    assert c is not a
    semantic.clear_classifier_cache()


def test_get_classifier_cache_unknown_backend_still_raises():
    with pytest.raises(ValueError):
        semantic.get_classifier("nonexistent")


# ------------------------------------------- cache embedding prompt (A2)

class _FakeClapModel:
    def __init__(self):
        self.calls = 0

    def get_text_embedding(self, prompts, use_tensor=False):
        self.calls += 1
        # embedding deterministico dipendente dal testo
        return np.stack([
            np.full(8, float(len(p)), dtype=np.float32) for p in prompts
        ])


@pytest.fixture()
def fake_clap(monkeypatch, tmp_path):
    fake = _FakeClapModel()
    monkeypatch.setattr(semantic_clap, "load_clap_model",
                        lambda device=None: (fake, "cpu"))
    monkeypatch.setattr(semantic_clap, "CLAP_CHECKPOINT_DIR", tmp_path)
    semantic_clap._PROMPT_EMB_CACHE.clear()
    yield fake
    semantic_clap._PROMPT_EMB_CACHE.clear()


def test_embed_prompts_memory_cache(fake_clap):
    prompts = ["mare calmo", "traffico urbano"]
    e1 = semantic_clap.embed_prompts(prompts)
    e2 = semantic_clap.embed_prompts(prompts)
    assert fake_clap.calls == 1
    assert np.array_equal(e1, e2)
    assert e1.shape == (2, 8)


def test_embed_prompts_disk_cache(fake_clap):
    prompts = ["campane lontane"]
    semantic_clap.embed_prompts(prompts)
    assert fake_clap.calls == 1
    # svuota la cache in memoria: la seconda chiamata deve leggere dal disco
    semantic_clap._PROMPT_EMB_CACHE.clear()
    e2 = semantic_clap.embed_prompts(prompts)
    assert fake_clap.calls == 1  # nessun nuovo forward
    assert e2.shape == (1, 8)


def test_embed_prompts_cache_key_changes_with_text(fake_clap):
    semantic_clap.embed_prompts(["uno"])
    semantic_clap.embed_prompts(["due"])
    assert fake_clap.calls == 2


def test_embed_prompts_no_cache_bypass(fake_clap):
    prompts = ["vento fra gli alberi"]
    semantic_clap.embed_prompts(prompts, use_cache=False)
    semantic_clap.embed_prompts(prompts, use_cache=False)
    assert fake_clap.calls == 2


def test_maybe_go_offline_respects_user_env(monkeypatch):
    monkeypatch.setenv("HF_HUB_OFFLINE", "0")
    semantic_clap._maybe_go_offline()
    import os
    assert os.environ["HF_HUB_OFFLINE"] == "0"
    assert "_SOUNDSCAPE_SET_HF_OFFLINE" not in os.environ


# ------------------------------------------------ decimazione grafici (B)

def test_minmax_envelope_preserves_extrema():
    rng = np.random.default_rng(42)
    y = rng.standard_normal(100_000).astype(np.float32)
    env_min, env_max = plotting._minmax_envelope(y, max_cols=500)
    assert len(env_min) == len(env_max) <= 500 + 1
    assert np.isclose(env_max.max(), y.max())
    assert np.isclose(env_min.min(), y.min())
    # l'inviluppo contiene il segnale
    assert (env_max >= env_min).all()


def test_plot_waveform_long_signal_decimated(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PLOT_WAVEFORM_MAX_COLS", 200)
    sr = 22050
    y = np.sin(np.linspace(0, 800 * np.pi, sr * 10)).astype(np.float32)
    out = tmp_path / "wf.png"
    plotting.plot_waveform(y, sr, out)
    assert out.exists() and out.stat().st_size > 1000


def test_plot_waveform_short_signal_unchanged_path(tmp_path):
    sr = 22050
    y = np.sin(np.linspace(0, 20 * np.pi, 2000)).astype(np.float32)
    out = tmp_path / "wf_short.png"
    plotting.plot_waveform(y, sr, out)
    assert out.exists()


def test_plot_spectrogram_decimated(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PLOT_SPECTROGRAM_MAX_FRAMES", 50)
    sr = 22050
    y = np.sin(np.linspace(0, 4000 * np.pi, sr * 8)).astype(np.float32)
    out = tmp_path / "spec.png"
    plotting.plot_spectrogram(y, sr, out)
    assert out.exists() and out.stat().st_size > 1000
