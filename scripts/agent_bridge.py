"""Bridge verso l'agente soundscape-composer-analyst.

Invoca `claude -p "..."` in modalità non interattiva, con timeout e retry.
Fallback pulito se `claude` non è nel PATH.

v0.5.1: diagnostica arricchita su stderr per visibilita' dei failure mode
(returncode, stderr completo, dimensione prompt, durata, n. tentativi).
Il dict ritornato include anche prompt_size_bytes e last_returncode per
ispezione successiva nel summary JSON.

v0.12.5: sanificazione payload per l'agent (Patch 1 anti-filename/path
leakage). Prima dell'invocazione una copia temporanea del summary viene
scritta con `metadata.path` e `metadata.filename` mascherati. L'agent
non puo' piu' dedurre toponimi, itinerari o scene dal nome del file o
dal path della cartella parent. Il summary originale su disco resta
invariato ed e' ancora quello usato dal PDF e dalla catena di analisi.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from . import config
from . import contextual_hints
from .locale_it import MESSAGGI_SISTEMA


AGENT_NAME = "soundscape-composer-analyst"
PROMPT_TEMPLATE_PATH = config.TEMPLATES_DIR / "agent_prompt.md"
AGENT_PAYLOAD_MASK = "<mascherato per agent>"


def _load_summary_safe(summary_path: Path) -> dict | None:
    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 — robustezza: se il summary non si legge, skip hints
        print(
            f"[agent_bridge] impossibile leggere summary per hints contestuali: {e}",
            file=sys.stderr, flush=True,
        )
        return None


def _sanitize_summary_for_agent(summary_path: Path) -> Path:
    """v0.12.5: crea una copia sanificata del summary per l'invocazione agent.

    Maschera `metadata.path` e `metadata.filename` con il placeholder
    `AGENT_PAYLOAD_MASK`. Evita che il nome del file o della cartella parent
    inneschino inferenze di scena, luogo, itinerario non supportate dal
    contenuto audio (Patch 1 anti-filename/path leakage, v0.12.5).

    Il summary originale su disco resta invariato. Il file temporaneo
    ritornato va rimosso a cura del chiamante.

    Se la sanificazione fallisce, ritorna il path originale (comportamento
    di degradazione: meglio correre il rischio di leakage che bloccare la
    lettura compositiva).
    """
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 — degrada al path originale
        print(
            f"[agent_bridge] sanitize fallito, uso path originale: {e}",
            file=sys.stderr, flush=True,
        )
        return summary_path

    meta = summary.get("metadata") or {}
    if isinstance(meta, dict):
        if "path" in meta:
            meta["path"] = AGENT_PAYLOAD_MASK
        if "filename" in meta:
            meta["filename"] = AGENT_PAYLOAD_MASK
        summary["metadata"] = meta

    fd, tmp = tempfile.mkstemp(prefix="soundscape_agent_payload_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)
    except Exception as e:  # noqa: BLE001
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            Path(tmp).unlink(missing_ok=True)
        except OSError:
            pass
        print(
            f"[agent_bridge] scrittura payload sanificato fallita, uso path "
            f"originale: {e}",
            file=sys.stderr, flush=True,
        )
        return summary_path

    return Path(tmp)


def _build_prompt(summary_path: Path, narrative_md: str | None = None) -> str:
    """Costruisce il prompt da inviare a claude -p.

    v0.2.2: se `narrative_md` è presente viene iniettato direttamente nel
    prompt come materiale empirico già tradotto in italiano, evitando
    all'agente di leggere la timeline completa.

    v0.7.3: inietta un blocco di "Suggerimenti contestuali di parentela"
    selezionati condizionalmente dal payload (vedi `contextual_hints.py`).
    Attivi solo le regole i cui marker acustici sono realmente presenti,
    evitando di caricare il prompt con tutte le scuole possibili (pattern
    di regressione documentato in v0.7.2 e v0.6.9). Se il summary non è
    leggibile, il blocco viene omesso e il comportamento è identico a v0.7.1.
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
    summary_dict = _load_summary_safe(summary_path)
    hints_block = ""
    if summary_dict is not None:
        hints_block = contextual_hints.build_hints(summary_dict)
    body = f"""Sei l'agente {AGENT_NAME}. Segui esattamente le istruzioni seguenti.

{instructions}
{hints_block}{narrative_block}
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
        print(
            "[agent_bridge] claude non trovato nel PATH: lettura compositiva saltata",
            file=sys.stderr, flush=True,
        )
        return {
            "text": MESSAGGI_SISTEMA["claude_cli_mancante"],
            "fallback_used": True,
            "error": "claude_not_in_path",
            "prompt_size_bytes": 0,
            "attempts": 0,
            "last_returncode": None,
            "last_stderr_excerpt": "",
        }

    # v0.12.5: payload sanificato per evitare filename/path leakage.
    sanitized_path = _sanitize_summary_for_agent(summary_path)
    sanitized_is_temp = sanitized_path != summary_path

    try:
        prompt = _build_prompt(sanitized_path, narrative_md=narrative_md)
        prompt_size = len(prompt.encode("utf-8"))
        print(
            f"[agent_bridge] invoco claude -p --agents {AGENT_NAME}, prompt "
            f"{prompt_size} byte, timeout {timeout_s} s, retries={retries}",
            file=sys.stderr, flush=True,
        )

        last_error: str | None = None
        last_returncode: int | None = None
        last_stderr: str = ""
        attempts = 0
        for attempt in range(retries + 1):
            attempts = attempt + 1
            t0 = time.perf_counter()
            try:
                result = subprocess.run(
                    ["claude", "-p", prompt, "--agents", AGENT_NAME],
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                )
                elapsed = time.perf_counter() - t0
                last_returncode = result.returncode
                last_stderr = (result.stderr or "").strip()
                stdout_clean = (result.stdout or "").strip()
                if result.returncode == 0 and stdout_clean:
                    print(
                        f"[agent_bridge] OK tentativo {attempts}/{retries + 1} "
                        f"in {elapsed:.1f} s, output {len(stdout_clean)} char",
                        file=sys.stderr, flush=True,
                    )
                    return {
                        "text": stdout_clean,
                        "fallback_used": False,
                        "error": None,
                        "prompt_size_bytes": prompt_size,
                        "attempts": attempts,
                        "last_returncode": result.returncode,
                        "last_stderr_excerpt": last_stderr[:500],
                        "elapsed_s": round(elapsed, 1),
                    }
                # returncode 0 ma stdout vuoto, oppure returncode != 0
                if result.returncode == 0:
                    last_error = "output vuoto (returncode 0 ma stdout vuoto)"
                else:
                    last_error = f"returncode {result.returncode}"
                print(
                    f"[agent_bridge] tentativo {attempts}/{retries + 1} fallito "
                    f"in {elapsed:.1f} s: {last_error}. stderr "
                    f"({len(last_stderr)} char): {last_stderr[:300]}",
                    file=sys.stderr, flush=True,
                )
            except subprocess.TimeoutExpired as te:
                elapsed = time.perf_counter() - t0
                last_error = f"timeout dopo {timeout_s} s"
                last_returncode = None
                # v0.6.2: subprocess.TimeoutExpired espone stdout/stderr catturati
                # fino al kill quando capture_output=True. Senza leggerli perdiamo
                # ogni diagnostica sul failure (PDF audio7 mostrava "Stderr: .").
                def _decode(x):
                    if x is None:
                        return ""
                    if isinstance(x, bytes):
                        return x.decode("utf-8", errors="replace")
                    return x
                last_stderr = _decode(te.stderr).strip()
                partial_stdout = _decode(te.stdout).strip()
                print(
                    f"[agent_bridge] tentativo {attempts}/{retries + 1} TIMEOUT "
                    f"a {elapsed:.1f} s. stderr ({len(last_stderr)} char): "
                    f"{last_stderr[:300] or '<vuoto>'}. stdout parziale: "
                    f"{len(partial_stdout)} char",
                    file=sys.stderr, flush=True,
                )
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                last_returncode = None
                print(
                    f"[agent_bridge] tentativo {attempts}/{retries + 1} "
                    f"eccezione: {last_error}",
                    file=sys.stderr, flush=True,
                )

        return {
            "text": (
                "La lettura compositiva automatica non è stata generata. "
                f"Errore: {last_error}. "
                f"Tentativi: {attempts}. Stderr: {last_stderr[:200]}. "
                "Puoi invocare manualmente l'agente con: "
                f"claude -p '...' --agents {AGENT_NAME}"
            ),
            "fallback_used": True,
            "error": last_error,
            "prompt_size_bytes": prompt_size,
            "attempts": attempts,
            "last_returncode": last_returncode,
            "last_stderr_excerpt": last_stderr[:500],
        }
    finally:
        # v0.12.5: pulizia payload temporaneo sanificato.
        if sanitized_is_temp:
            try:
                sanitized_path.unlink(missing_ok=True)
            except OSError:
                pass
