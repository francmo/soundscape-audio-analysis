"""Test della release v0.19.3 (robustezza corpus, addendum performance 12/07).

Retry adattivo della sintesi (timeout raddoppiato + modello di riserva),
comando report-resynth, stima di durata calibrata.
"""
import json
import subprocess
from pathlib import Path

import pytest

from scripts import config
from scripts import report_cmd as rc
from scripts import report_synthesizer as rs


# ------------------------------------------ retry adattivo sintesi (C1+C3)

class _FakeRun:
    """Simula subprocess.run: timeout al primo tentativo, successo al secondo."""

    def __init__(self):
        self.calls: list[dict] = []

    def __call__(self, cmd, input=None, capture_output=True, text=True,
                 timeout=None, encoding=None):
        self.calls.append({"cmd": list(cmd), "timeout": timeout})
        if len(self.calls) == 1:
            raise subprocess.TimeoutExpired(cmd, timeout)
        class R:
            returncode = 0
            stdout = "# Report\n\nContenuto della sintesi."
            stderr = ""
        return R()


def test_synth_retry_doubles_timeout_and_switches_model(monkeypatch):
    fake = _FakeRun()
    monkeypatch.setattr(rs.subprocess, "run", fake)
    monkeypatch.setattr(rs.shutil, "which", lambda name: "/usr/local/bin/claude")

    out = rs.invoke_corpus_synthesizer(
        "prompt", model="opus", timeout_s=100, retries=1,
        fallback_model="sonnet",
    )
    assert not out["fallback_used"]
    assert out["attempts"] == 2
    assert out["model"] == "sonnet"          # modello effettivo del retry
    assert out["model_requested"] == "opus"
    assert fake.calls[0]["timeout"] == 100
    assert fake.calls[1]["timeout"] == 200   # timeout raddoppiato
    assert "--model" in fake.calls[1]["cmd"]
    assert fake.calls[1]["cmd"][fake.calls[1]["cmd"].index("--model") + 1] == "sonnet"
    assert out["text"].startswith("# Report")


def test_synth_no_fallback_model_keeps_requested(monkeypatch):
    fake = _FakeRun()
    monkeypatch.setattr(rs.subprocess, "run", fake)
    monkeypatch.setattr(rs.shutil, "which", lambda name: "/usr/local/bin/claude")

    out = rs.invoke_corpus_synthesizer(
        "prompt", model="opus", timeout_s=50, retries=1,
    )
    assert out["model"] == "opus"
    assert fake.calls[1]["cmd"][fake.calls[1]["cmd"].index("--model") + 1] == "opus"


def test_synth_all_timeouts_reports_resynth_hint(monkeypatch):
    def _always_timeout(cmd, input=None, capture_output=True, text=True,
                        timeout=None, encoding=None):
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr(rs.subprocess, "run", _always_timeout)
    monkeypatch.setattr(rs.shutil, "which", lambda name: "/usr/local/bin/claude")
    out = rs.invoke_corpus_synthesizer("prompt", model="opus", timeout_s=10,
                                       retries=1, fallback_model="sonnet")
    assert out["fallback_used"]
    assert "report-resynth" in out["text"]
    assert out["attempts"] == 2


# --------------------------------------------------- report-resynth (C2)

def test_resynth_corpus_regenerates_md_and_pdf(monkeypatch, tmp_path):
    # Prepara una cartella di report finta con metadata e prompt salvati
    pdf_path = tmp_path / "Corpus_test_corpus_report.pdf"
    pdf_path.write_bytes(b"%PDF-fake")
    prompt_path = tmp_path / "corpus_synth_prompt.md"
    prompt_path.write_text("PROMPT", encoding="utf-8")
    meta = {
        "corpus_title": "Corpus test",
        "n_files": 1,
        "duration_total_s": 10.0,
        "summary_paths": [],
        "plot_paths": {},
        "prompt_path": str(prompt_path),
        "pdf_path": str(pdf_path),
        "synth_fallback": True,
        "synth_error": "timeout dopo 300s",
    }
    (tmp_path / "corpus_run_metadata.json").write_text(
        json.dumps(meta), encoding="utf-8")

    monkeypatch.setattr(
        rc.rs, "invoke_corpus_synthesizer",
        lambda *a, **k: {"text": "# Sintesi\n\nOk.", "fallback_used": False,
                         "error": None, "model": "opus", "attempts": 1,
                         "elapsed_s": 1.0},
    )
    merged = {}
    monkeypatch.setattr(
        rc, "merge_markdown_into_pdf",
        lambda pdf, md: merged.setdefault("args", (Path(pdf), Path(md))) or Path(pdf),
    )

    out_meta = rc.resynth_corpus(tmp_path)
    md_path = tmp_path / "REPORT_ANALISI_Corpus_test.md"
    assert md_path.exists()
    assert md_path.read_text(encoding="utf-8").startswith("# Sintesi")
    assert merged["args"][0] == pdf_path
    assert out_meta["synth_model"] == "opus"


def test_resynth_corpus_requires_metadata(tmp_path):
    with pytest.raises(Exception):
        rc.resynth_corpus(tmp_path)


# ------------------------------------------------- stima calibrata (C5)

def test_estimate_uses_calibrated_coefficients(monkeypatch):
    """La conferma sopra soglia usa la stima calibrata, non durata x 1,2."""
    shown = {}

    def _fake_confirm(msg, default=False):
        return True

    def _fake_echo(msg="", **kw):
        text = str(msg)
        if "stimato" in text:
            shown["est"] = text

    monkeypatch.setattr(rc.click, "confirm", _fake_confirm)
    monkeypatch.setattr(rc.click, "echo", _fake_echo)
    # 200 min di audio, 10 file: formula storica dava ~242 min; la
    # calibrata deve stare sotto i 45 min.
    assert rc._require_confirm(10, 200 * 60.0, yes=False)
    est = shown.get("est", "")
    import re
    m = re.search(r"circa (\d+) minuti", est)
    assert m, est
    assert int(m.group(1)) < 45
