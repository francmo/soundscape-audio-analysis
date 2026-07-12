"""Governo delle risorse di processo (v0.19.1).

Driver: addendum performance 12/07/2026. Senza cap, BLAS/Accelerate e torch
prendono tutti i core (800% CPU osservati su M4) e un run di corpus lungo
satura la macchina (load average 30, swap thrashing). Qui si centralizza:

- `apply_thread_caps(n)`: imposta le env var dei pool BLAS/OpenMP (solo se
  non già impostate dall'utente) e `torch.set_num_threads` quando torch è
  già caricato o verrà caricato dopo (le env valgono anche per lui).
- `set_low_impact()`: cap stretto + priorità di processo abbassata, per i
  run "di cortesia" che non devono monopolizzare la macchina.
- `effective_threads()`: il numero di thread deciso, riusabile dagli altri
  moduli (es. faster-whisper `cpu_threads`).

Le env var vanno impostate PRIMA che i pool si materializzino (prima della
prima operazione numpy pesante e del primo import torch): la pipeline usa
import lazy dentro `_analyze_single`, quindi chiamare `apply_thread_caps`
all'ingresso dei comandi CLI è sufficiente.
"""
from __future__ import annotations

import os
import sys

from . import config

_APPLIED_THREADS: int | None = None

_THREAD_ENV_VARS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def _auto_threads() -> int:
    """Default: lascia 4 core al sistema, mai sotto 4 thread."""
    n_cores = os.cpu_count() or 8
    return max(4, n_cores - 4)


def effective_threads() -> int:
    """Il cap deciso per questo processo (dopo apply_thread_caps)."""
    if _APPLIED_THREADS is not None:
        return _APPLIED_THREADS
    n = config.CPU_THREADS
    return n if n and n > 0 else _auto_threads()


def apply_thread_caps(n: int | None = None, verbose: bool = False) -> int:
    """Applica il cap ai pool di thread. Idempotente, ritorna il cap usato.

    Rispetta le env var già impostate dall'utente (setdefault). torch viene
    toccato solo se già importato; altrimenti erediteranno le env var i pool
    OpenMP interni al momento del primo import.
    """
    global _APPLIED_THREADS
    if n is None or n <= 0:
        n = config.CPU_THREADS if config.CPU_THREADS > 0 else _auto_threads()

    for var in _THREAD_ENV_VARS:
        os.environ.setdefault(var, str(n))

    if "torch" in sys.modules:
        try:
            sys.modules["torch"].set_num_threads(n)
        except Exception:
            pass

    _APPLIED_THREADS = n
    if verbose:
        print(f"[soundscape] cap thread CPU: {n}", file=sys.stderr, flush=True)
    return n


def set_low_impact(verbose: bool = True) -> int:
    """Modalità a basso impatto: pochi thread e priorità abbassata.

    Ritorna il cap applicato. La priorità (nice) riduce la contesa con le
    app interattive; su macOS sposta il lavoro verso gli E-core.
    """
    n = apply_thread_caps(config.LOW_IMPACT_THREADS)
    try:
        os.setpriority(os.PRIO_PROCESS, 0, config.LOW_IMPACT_NICE)
    except (OSError, AttributeError):
        pass
    if verbose:
        print(
            f"[soundscape] modalità a basso impatto: {n} thread, "
            f"nice +{config.LOW_IMPACT_NICE}",
            file=sys.stderr, flush=True,
        )
    return n
