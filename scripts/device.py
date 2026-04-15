"""Helper device condiviso per moduli torch-based (PANNs CNN14, LAION-CLAP).

Introdotto in v0.3.2 per deduplicare la logica di risoluzione del device e
per centralizzare il logging "Using device: <device>" su stderr. In v0.3.1
ogni modulo aveva un proprio `_resolve_device` con priorità leggermente
diverse (PANNs: mps > cuda, CLAP: cuda > mps).
"""
from __future__ import annotations

import contextlib
import io
import sys
from typing import Iterator


def resolve_device(requested: str | None, prefer_mps: bool = True) -> str:
    """Risolve 'auto' al miglior device disponibile.

    Se `requested` è esplicito (cpu, mps, cuda) lo ritorna invariato. Se
    è `None` o `"auto"`, sceglie MPS su Apple Silicon (quando `prefer_mps`),
    altrimenti CUDA su sistemi NVIDIA, altrimenti CPU.

    Questa logica assume che MPS e CUDA non siano mai disponibili
    contemporaneamente (Mac vs Linux/Windows server). `prefer_mps` copre
    lo scenario ibrido teorico.
    """
    if requested and requested != "auto":
        return requested
    try:
        import torch
        mps_available = (
            hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        )
        cuda_available = torch.cuda.is_available()
        if prefer_mps and mps_available:
            return "mps"
        if cuda_available:
            return "cuda"
        if mps_available:
            return "mps"
    except Exception:
        pass
    return "cpu"


def log_device(component: str, device: str) -> None:
    """Stampa `[<component>] Using device: <device>` su stderr.

    Usato da PANNsClassifier e load_clap_model al termine del caricamento
    per rendere trasparente all'utente quale backend hardware è in uso.
    """
    print(f"[{component}] Using device: {device}", file=sys.stderr, flush=True)


@contextlib.contextmanager
def suppress_stdout() -> Iterator[None]:
    """Sopprime stdout all'interno del blocco.

    Necessario per nascondere le print informative di `panns_inference`
    durante la costruzione di `AudioTagging` (es. "Using CPU.",
    "Checkpoint path: ..."). Agisce a livello di `sys.stdout` e non
    interferisce con `pytest.capfd` (che intercetta a livello di file
    descriptor OS).
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield
