"""Test del modulo `scripts.device` (v0.3.2).

Helper condiviso introdotto per unificare la logica device di PANNs e CLAP.
"""
import sys

from scripts.device import resolve_device, log_device, suppress_stdout


def test_resolve_explicit_cpu_returns_cpu():
    assert resolve_device("cpu") == "cpu"


def test_resolve_explicit_mps_returns_mps():
    assert resolve_device("mps") == "mps"


def test_resolve_explicit_cuda_returns_cuda():
    assert resolve_device("cuda") == "cuda"


def test_resolve_auto_prefers_mps_when_available(monkeypatch):
    """Su sistema con MPS disponibile, 'auto' ritorna 'mps' (prefer_mps=True)."""
    import torch
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    assert resolve_device("auto", prefer_mps=True) == "mps"


def test_resolve_auto_falls_back_to_cpu_when_nothing_available(monkeypatch):
    import torch
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    assert resolve_device("auto") == "cpu"


def test_resolve_none_behaves_like_auto(monkeypatch):
    import torch
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    assert resolve_device(None) == "cpu"


def test_suppress_stdout_swallows_print(capsys):
    """Le print dentro il context manager non arrivano a stdout."""
    with suppress_stdout():
        print("questo non deve arrivare a stdout")
    captured = capsys.readouterr()
    assert "non deve arrivare" not in captured.out


def test_log_device_writes_to_stderr(capsys):
    log_device("PANNs CNN14", "mps")
    captured = capsys.readouterr()
    assert "[PANNs CNN14] Using device: mps" in captured.err
    assert captured.out == ""
