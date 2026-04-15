"""Serializzazione JSON dei risultati con supporto numpy.

Porting del pattern `_conv` usato in analyze.py del toolkit originale.
"""
import json
from pathlib import Path
from typing import Any
import numpy as np


def _default(o: Any):
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    if isinstance(o, bytes):
        return o.decode("utf-8", errors="replace")
    raise TypeError(f"Oggetto di tipo {type(o).__name__} non serializzabile in JSON")


def dumps(obj: Any, indent: int = 2) -> str:
    return json.dumps(obj, indent=indent, default=_default, ensure_ascii=False)


def dump(obj: Any, path: Path, indent: int = 2) -> None:
    Path(path).write_text(dumps(obj, indent=indent), encoding="utf-8")


def load(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
