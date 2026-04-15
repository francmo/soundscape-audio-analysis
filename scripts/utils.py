"""Utility generiche."""
import shutil
import subprocess
from pathlib import Path


def check_binary(name: str) -> bool:
    """Ritorna True se il binario `name` è nel PATH."""
    return shutil.which(name) is not None


def require_binaries(names: list[str]) -> list[str]:
    """Ritorna la lista di binari mancanti dal PATH."""
    return [n for n in names if not check_binary(n)]


def format_duration(seconds: float) -> str:
    """Formatta 4010.4 come 1:06:50."""
    import datetime
    return str(datetime.timedelta(seconds=int(seconds)))


def safe_filename(s: str) -> str:
    """Versione sicura per filesystem."""
    keep = [c if (c.isalnum() or c in "_-. ") else "_" for c in s]
    return "".join(keep).strip().replace(" ", "_")


def run_cmd(cmd: list[str], timeout: int | None = None, input_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        input=input_text,
    )


def ensure_dir(path: Path) -> Path:
    Path(path).mkdir(parents=True, exist_ok=True)
    return Path(path)
