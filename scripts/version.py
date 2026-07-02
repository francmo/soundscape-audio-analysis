"""Fonte unica della versione della skill, letta da pyproject.toml.

Il numero di versione compare in più punti (CLI, summary JSON, metadata del
report di corpus, copertina del PDF comparativo). Qui viene letto una volta
sola da pyproject.toml, così un bump di release non può più lasciare indietro
i callsite hardcoded (era già successo con 0.12.5, 0.14.0, 0.16.0 e con il
"v0.6.8" della copertina corpus). Il guard-rail è in tests/test_version.py,
che verifica anche l'allineamento con CHANGELOG.md e con il BibTeX del README.
"""

from __future__ import annotations

import tomllib
from functools import cache
from pathlib import Path

_PYPROJECT_PATH = Path(__file__).resolve().parent.parent / "pyproject.toml"


@cache
def skill_version() -> str:
    """Versione corrente della skill (campo project.version di pyproject.toml)."""
    with _PYPROJECT_PATH.open("rb") as fh:
        data = tomllib.load(fh)
    return str(data["project"]["version"])
