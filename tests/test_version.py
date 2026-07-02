"""Guard-rail di versionamento.

pyproject.toml è l'unica fonte di verità della versione (scripts/version.py).
Questi test verificano che la voce in testa al CHANGELOG e il BibTeX del
README restino allineati e che nessun modulo reintroduca versioni hardcoded.
Il bump dimenticato è già successo quattro volte (0.12.5 nel comando version,
0.14.0 in __init__ e report_cmd, 0.16.0 nel summary, v0.6.8 nel corpus PDF).
"""
import re
from pathlib import Path

from scripts.version import skill_version

ROOT = Path(__file__).resolve().parent.parent


def test_changelog_top_entry_matches_pyproject():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, flags=re.MULTILINE)
    assert m, "CHANGELOG.md senza voce di release in testa"
    assert m.group(1) == skill_version(), (
        f"CHANGELOG in testa dichiara {m.group(1)} ma pyproject dice "
        f"{skill_version()}: allineare prima della release"
    )


def test_readme_bibtex_version_matches_pyproject():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(r"version\s*=\s*\{v(\d+\.\d+\.\d+)\}", readme)
    assert m, "README.md senza campo version nel BibTeX @software"
    assert m.group(1) == skill_version(), (
        f"BibTeX del README dichiara v{m.group(1)} ma pyproject dice "
        f"v{skill_version()}: la versione citabile va bumpata a ogni release"
    )


def test_no_hardcoded_skill_version_in_scripts():
    """Nessun sorgente deve dichiarare la versione della skill come literal.

    Il pattern copre i tre modi in cui il bug si è presentato in passato,
    la chiave "version" nei dict, l'assegnazione version=..., e la stringa
    "soundscape-audio-analysis vX.Y.Z" nei testi renderizzati.
    """
    pattern = re.compile(
        r'"version"\s*:\s*"0\.\d+\.\d+"'
        r'|version\s*=\s*"0\.\d+\.\d+"'
        r"|soundscape-audio-analysis v?0\.\d+\.\d+"
    )
    offenders: list[str] = []
    for py in sorted((ROOT / "scripts").glob("*.py")):
        text = py.read_text(encoding="utf-8")
        for m in pattern.finditer(text):
            offenders.append(f"{py.name}: {m.group(0)!r}")
    assert not offenders, (
        "Versione della skill hardcoded nei sorgenti (usare "
        f"scripts.version.skill_version): {offenders}"
    )
