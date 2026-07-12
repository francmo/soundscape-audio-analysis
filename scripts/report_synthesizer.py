"""Sintesi corpus via `claude -p` non interattivo.

Riusa il pattern di `agent_bridge.py` estendendolo per:
- prompt grande (passato via stdin invece che argomento)
- timeout più lungo (default 300s per corpus di medie dimensioni)
- modello selezionabile
- fallback pulito se `claude` non è nel PATH
- sanitizzazione italiano (rimozione em dash residui) sull'output
"""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path

from . import config
from .locale_it import sanitize_italiano, MESSAGGI_SISTEMA


def _strip_preamble(text: str) -> str:
    """Rimuove qualsiasi riga prima del primo H1 Markdown (riga che inizia con '# ').

    Fix v0.3.1: la v0.3.0 aveva osservato casi in cui l'agente, nonostante il
    vincolo del template, apriva con preamboli del tipo "Ho tutti i dati
    necessari. Ecco il report comparativo." Questa funzione li rimuove in
    modo deterministico post-generazione.

    Se il testo non contiene alcun '# ', ritorna il testo originale con le
    sole righe vuote iniziali strippate (nessuna rimozione di contenuto).
    """
    if not text:
        return text
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("# "):
            return "\n".join(lines[i:]).strip()
    return text.lstrip()


def invoke_corpus_synthesizer(
    prompt_text: str,
    model: str = "opus",
    timeout_s: int = 300,
    retries: int = 1,
    fallback_model: str | None = None,
) -> dict:
    """Invoca `claude -p` non interattivo via stdin.

    v0.19.3 (C1+C3 addendum performance): retry adattivo. Se un tentativo
    scade per timeout, il successivo raddoppia il timeout e (se
    `fallback_model` è indicato) passa al modello di riserva, più veloce.
    Stessa lezione della v0.6.2 sull'agente (300 s erano strutturalmente
    stretti per leggere 11 file e scrivere 2000-4000 parole).

    Ritorna dict con chiavi:
        text          markdown dell'agente (sanitizzato) o placeholder
        fallback_used True se `claude` manca o è fallito
        error         stringa di errore se fallback_used
        model         modello EFFETTIVO dell'ultimo tentativo
        model_requested  modello richiesto in origine
        attempts      numero di tentativi eseguiti
        elapsed_s     tempo di esecuzione
    """
    import time

    if shutil.which("claude") is None:
        return {
            "text": MESSAGGI_SISTEMA["claude_cli_mancante"],
            "fallback_used": True,
            "error": "claude non nel PATH",
            "model": model,
            "model_requested": model,
            "attempts": 0,
            "elapsed_s": 0.0,
        }

    last_error: str | None = None
    t0 = time.time()
    current_model = model
    current_timeout = timeout_s
    attempts = 0
    for attempt in range(retries + 1):
        attempts += 1
        cmd = ["claude", "-p", "--model", current_model]
        try:
            result = subprocess.run(
                cmd,
                input=prompt_text,
                capture_output=True,
                text=True,
                timeout=current_timeout,
                encoding="utf-8",
            )
            if result.returncode == 0 and result.stdout.strip():
                raw = result.stdout.strip()
                clean = sanitize_italiano(raw)
                clean = _strip_preamble(clean)
                return {
                    "text": clean,
                    "fallback_used": False,
                    "error": None,
                    "model": current_model,
                    "model_requested": model,
                    "attempts": attempts,
                    "elapsed_s": round(time.time() - t0, 1),
                }
            last_error = result.stderr.strip() or "output vuoto"
        except subprocess.TimeoutExpired:
            last_error = f"timeout dopo {current_timeout}s (model {current_model})"
            # Retry adattivo: timeout raddoppiato, modello di riserva se dato.
            current_timeout = current_timeout * 2
            if fallback_model and current_model != fallback_model:
                current_model = fallback_model
        except Exception as e:
            last_error = str(e)

    return {
        "text": (
            "La sintesi automatica del corpus non è stata generata. "
            f"Errore: {last_error}. "
            f"Il prompt completo è stato salvato; puoi rilanciare solo la "
            f"sintesi con: soundscape report-resynth <cartella del report>"
        ),
        "fallback_used": True,
        "error": last_error,
        "model": current_model,
        "model_requested": model,
        "attempts": attempts,
        "elapsed_s": round(time.time() - t0, 1),
    }


def build_synth_prompt(
    template_path: Path,
    golden_path: Path,
    corpus_title: str,
    n_files: int,
    total_duration_s: float,
    payloads_dir: Path,
    plots_dir: Path,
    file_payload_paths: list[Path],
    plot_paths: dict[str, Path],
) -> str:
    """Compone il prompt completo a partire dal template e dai placeholder."""
    template = template_path.read_text(encoding="utf-8")

    def _fmt_duration(s: float) -> str:
        m = int(s) // 60
        h = m // 60
        if h:
            return f"{h}h {m % 60}min"
        return f"{m} min"

    payload_list = "\n".join(
        f"  {i + 1}. {p}" for i, p in enumerate(file_payload_paths)
    )
    plots_list = "\n".join(
        f"  - {name}: {path}" for name, path in plot_paths.items()
    )

    text = template
    text = text.replace("{GOLDEN_PATH}", str(golden_path))
    text = text.replace("{CORPUS_TITLE}", corpus_title)
    text = text.replace("{N_FILES}", str(n_files))
    text = text.replace("{TOTAL_DURATION}", _fmt_duration(total_duration_s))
    text = text.replace("{PAYLOADS_DIR}", str(payloads_dir))
    text = text.replace("{PLOTS_DIR}", str(plots_dir))
    text = text.replace("{PAYLOAD_LIST}", payload_list)
    text = text.replace("{PLOT_LIST}", plots_list)
    return text
