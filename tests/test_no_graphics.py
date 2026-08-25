"""Test v0.20.0 - P4 addendum heritage: --no-graphics su analyze.

Pipeline reale end-to-end sul fixture pink_noise (stadi con modelli
disattivati), nessun PNG scritto e cartella graphics assente.
"""
from __future__ import annotations

import json

from click.testing import CliRunner

from scripts.cli import cli
from tests.conftest import ensure_fixtures, FIXTURES_DIR


def test_no_graphics_niente_png(tmp_path):
    ensure_fixtures()
    wav = FIXTURES_DIR / "pink_noise.wav"
    runner = CliRunner()
    res = runner.invoke(cli, [
        "analyze", str(wav), "--report", "json", "--no-agent",
        "--no-semantic", "--no-clap", "--narrative", "none",
        "--no-graphics", "--output", str(tmp_path),
    ])
    assert res.exit_code == 0, res.output
    assert not (tmp_path / "graphics").exists()
    assert "Grafici disattivati" in res.output
    summary = json.loads((tmp_path / "pink_noise_summary.json").read_text())
    assert "plots" in summary["timings"]
    assert summary["timings"]["plots"] < 0.5


def test_no_graphics_rifiutato_fuori_da_report_json(tmp_path):
    ensure_fixtures()
    wav = FIXTURES_DIR / "pink_noise.wav"
    runner = CliRunner()
    res = runner.invoke(cli, ["analyze", str(wav), "--no-graphics",
                              "--output", str(tmp_path)])
    assert res.exit_code != 0
    assert "--report json" in res.output
