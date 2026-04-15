"""Benchmark interno PANNs CNN14: MPS vs CPU (v0.3.2).

Saltato di default per evitare di rallentare i run CI/test standard.
Per eseguirlo: `SOUNDSCAPE_BENCHMARK=1 pytest tests/test_panns_benchmark.py -s`.

Sanity check: su un segnale da ~60 secondi, MPS deve essere almeno 30% più
veloce di CPU. Se il margine è inferiore c'è qualcosa che non va nel device
routing (es. il modello non è stato effettivamente spostato su MPS).
"""
import os
import time

import numpy as np
import pytest

from tests.conftest import FIXTURES_DIR, ensure_fixtures
from scripts.semantic import PANNsClassifier
from scripts.io_loader import load_audio_mono


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    ensure_fixtures()


def _mps_available() -> bool:
    try:
        import torch
        return hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    except Exception:
        return False


@pytest.mark.skipif(
    os.environ.get("SOUNDSCAPE_BENCHMARK") != "1",
    reason="Benchmark saltato. Per eseguirlo: SOUNDSCAPE_BENCHMARK=1 pytest -s",
)
def test_panns_mps_vs_cpu_speedup():
    if not _mps_available():
        pytest.skip("MPS non disponibile su questo host")

    y, sr = load_audio_mono(FIXTURES_DIR / "transient_dense.wav")
    target_samples = max(len(y), 60 * sr)
    repeats = max(1, target_samples // len(y))
    y_long = np.tile(y, repeats)[:target_samples]

    clf_cpu = PANNsClassifier(device="cpu")
    clf_cpu.classify(y_long[:sr], sr, segment_seconds=10.0)
    t0 = time.perf_counter()
    clf_cpu.classify(y_long, sr, segment_seconds=10.0)
    t_cpu = time.perf_counter() - t0

    clf_mps = PANNsClassifier(device="mps")
    clf_mps.classify(y_long[:sr], sr, segment_seconds=10.0)
    t0 = time.perf_counter()
    clf_mps.classify(y_long, sr, segment_seconds=10.0)
    t_mps = time.perf_counter() - t0

    speedup = t_cpu / t_mps if t_mps > 0 else float("inf")
    print(
        f"\nPANNs CNN14 benchmark su {len(y_long)/sr:.1f} sec di audio: "
        f"cpu={t_cpu:.2f}s mps={t_mps:.2f}s speedup={speedup:.2f}x"
    )
    assert t_mps < t_cpu * 0.7, (
        f"Speedup MPS insufficiente: cpu={t_cpu:.2f}s mps={t_mps:.2f}s "
        f"({speedup:.2f}x, atteso >=1.43x)"
    )
