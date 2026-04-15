"""Bridge verso l'agente soundscape-composer-analyst.

Invoca `claude -p "..."` in modalità non interattiva, con timeout e retry.
Fallback pulito se `claude` non è nel PATH.
"""
import shutil
import subprocess
from pathlib import Path
from typing import Any

from . import config
from .locale_it import MESSAGGI_SISTEMA


AGENT_NAME = "soundscape-composer-analyst"
PROMPT_TEMPLATE_PATH = config.TEMPLATES_DIR / "agent_prompt.md"


def _build_prompt(summary_path: Path, narrative_md: str | None = None) -> str:
    """Costruisce il prompt da inviare a claude -p.

    v0.2.2: se `narrative_md` è presente viene iniettato direttamente nel
    prompt come materiale empirico già tradotto in italiano, evitando
    all'agente di leggere la timeline completa (che su file lunghi
    provocava timeout).
    """
    template = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    instructions = template.replace("{SUMMARY_PATH}", str(summary_path))
    narrative_block = ""
    if narrative_md:
        narrative_block = (
            "\n## Descrizione segmentata (da usare come spina dorsale dell'interpretazione)\n\n"
            + narrative_md
            + "\n"
        )
    body = f"""Sei l'agente {AGENT_NAME}. Segui esattamente le istruzioni seguenti.

{instructions}
{narrative_block}
Leggi il file JSON payload (summary ridotto) all'inizio del tuo ragionamento,
poi integra la descrizione segmentata soprastante come materiale empirico
già tradotto. Non ripeterla letteralmente: usala come evidenza. Produci il
testo markdown richiesto senza commenti extra, senza introduzioni.
"""
    return body


def invoke_composer_analyst(summary_path: Path,
                             narrative_md: str | None = None,
                             timeout_s: int = config.AGENT_TIMEOUT_S,
                             retries: int = config.AGENT_RETRIES) -> dict:
    """Invoca l'agente in modalità non interattiva e ritorna {text, error, fallback_used}.

    v0.2.2: accetta `narrative_md` opzionale (descrizione segmentata italiana)
    che viene iniettato direttamente nel prompt come materiale empirico.

    Se `claude` non è disponibile, ritorna un messaggio italiano come placeholder.
    """
    if shutil.which("claude") is None:
        return {
            "text": MESSAGGI_SISTEMA["claude_cli_mancante"],
            "fallback_used": True,
            "error": None,
        }

    prompt = _build_prompt(summary_path, narrative_md=narrative_md)
    last_error: str | None = None
    for attempt in range(retries + 1):
        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--agents", AGENT_NAME],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            if result.returncode == 0 and result.stdout.strip():
                return {
                    "text": result.stdout.strip(),
                    "fallback_used": False,
                    "error": None,
                }
            last_error = result.stderr.strip() or "output vuoto"
        except subprocess.TimeoutExpired:
            last_error = f"timeout dopo {timeout_s}s"
        except Exception as e:
            last_error = str(e)

    return {
        "text": (
            "La lettura compositiva automatica non è stata generata. "
            f"Errore: {last_error}. "
            "Puoi invocare manualmente l'agente con: "
            f"claude -p '...' --agents {AGENT_NAME}"
        ),
        "fallback_used": True,
        "error": last_error,
    }
