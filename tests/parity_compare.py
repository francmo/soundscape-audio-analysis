"""Confronto di parità fra due summary JSON della skill (non è un test pytest).

Uso:
    venv/bin/python -m tests.parity_compare <baseline.json> <nuovo.json> [tolleranza]

Confronta ricorsivamente i due summary ignorando i campi volatili
(version, generated_at, path assoluti) e riporta ogni differenza numerica
sopra la tolleranza (default 1e-4) o strutturale. Exit code 0 = parità.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

IGNORE_KEYS = {"version", "generated_at", "path", "timings"}
# campi testuali che contengono path assoluti o timestamp
IGNORE_SUBSTR_KEYS = {"_path", "_paths"}


def _ignored(key: str) -> bool:
    if key in IGNORE_KEYS:
        return True
    return any(s in key for s in IGNORE_SUBSTR_KEYS)


def compare(a, b, tol: float, path: str = "") -> list[str]:
    diffs: list[str] = []
    if isinstance(a, dict) and isinstance(b, dict):
        keys = set(a) | set(b)
        for k in sorted(keys):
            if _ignored(str(k)):
                continue
            p = f"{path}.{k}" if path else str(k)
            if k not in a:
                diffs.append(f"{p}: solo nel nuovo")
            elif k not in b:
                diffs.append(f"{p}: solo nel baseline")
            else:
                diffs.extend(compare(a[k], b[k], tol, p))
        return diffs
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f"{path}: lunghezza {len(a)} vs {len(b)}")
            return diffs
        for i, (xa, xb) in enumerate(zip(a, b)):
            diffs.extend(compare(xa, xb, tol, f"{path}[{i}]"))
        return diffs
    if isinstance(a, bool) or isinstance(b, bool):
        if a != b:
            diffs.append(f"{path}: {a!r} vs {b!r}")
        return diffs
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if abs(float(a) - float(b)) > tol:
            diffs.append(f"{path}: {a} vs {b} (delta {abs(float(a)-float(b)):.6g})")
        return diffs
    if a != b:
        sa, sb = str(a), str(b)
        if len(sa) > 60:
            sa = sa[:57] + "..."
        if len(sb) > 60:
            sb = sb[:57] + "..."
        diffs.append(f"{path}: {sa!r} vs {sb!r}")
    return diffs


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    baseline = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    nuovo = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 1e-4
    diffs = compare(baseline, nuovo, tol)
    if not diffs:
        print(f"PARITA' OK (tolleranza {tol})")
        return 0
    print(f"{len(diffs)} differenze (tolleranza {tol}):")
    for d in diffs[:80]:
        print(f"  {d}")
    if len(diffs) > 80:
        print(f"  ... e altre {len(diffs) - 80}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
