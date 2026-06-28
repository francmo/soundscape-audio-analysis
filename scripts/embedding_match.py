"""Copertura semantica gold-vs-agente via embedding (benchmark v0.13).

Il benchmark lessicale (`benchmark.py`) marca coperto un termine gold solo se i
suoi lemmi compaiono nel testo dell'agente. Questo manca la sinonimia: "sviluppo
timbrico" vs "evoluzione spettrale" danno Jaccard 0 pur essendo lo stesso concetto.

Qui calcoliamo la copertura per similarita di embedding. Per ogni gold phrase si
prende la cosine massima contro le unita (frasi e proposizioni) del testo agente;
la phrase e coperta se supera una soglia calibrata.

Calibrazione (verificata su MPS, M4, modello di default):
- modello `paraphrase-multilingual-mpnet-base-v2` (IT/FR/EN).
- term-vs-term: sinonimi ~0.52-0.55, non correlati ~0.20-0.22.
- gold-term-vs-frase: vero accordo ~0.37-0.50, non correlato ~0.14-0.15.
- soglia di default 0.45 nel regime phrase-vs-unita, con split a livello di
  proposizione per ridurre la diluizione delle frasi lunghe.
Il modello `MiniLM-L12` dava separazione troppo debole (sinonimi ~0.31), scartato.

Il modulo e OPZIONALE - se `sentence-transformers` non e installato, l'import di
`coverage`/`get_model` solleva `EmbeddingUnavailable`, che il chiamante intercetta
per ricadere sul percorso lessicale con un avviso.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from functools import lru_cache

DEFAULT_MODEL = "paraphrase-multilingual-mpnet-base-v2"
DEFAULT_THRESHOLD = 0.45


class EmbeddingUnavailable(RuntimeError):
    """sentence-transformers assente o modello non caricabile."""


# --------------------------------------------------------------------------- #
# Caricamento modello (pigro, una sola volta, su MPS con fallback CPU)
# --------------------------------------------------------------------------- #

_DEVICE_LOGGED = False


def _select_device() -> str:
    try:
        import torch
    except ImportError as e:  # pragma: no cover
        raise EmbeddingUnavailable("torch non disponibile") from e
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


@lru_cache(maxsize=4)
def get_model(name: str = DEFAULT_MODEL):
    """Carica (e memoizza) il modello sentence-transformers sul device migliore.

    Solleva EmbeddingUnavailable se la libreria manca o il modello non si carica.
    """
    global _DEVICE_LOGGED
    # Fallback MPS per operazioni non supportate, evita crash su Apple Silicon.
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise EmbeddingUnavailable(
            "sentence-transformers non installato. "
            "Installa con `pip install sentence-transformers` (vedi requirements-embedding.txt)."
        ) from e
    device = _select_device()
    if not _DEVICE_LOGGED:
        print(f"[embedding_match] Using device: {device}", file=sys.stderr)
        _DEVICE_LOGGED = True
    try:
        return SentenceTransformer(name, device=device)
    except Exception as e:  # pragma: no cover - rete/modello
        raise EmbeddingUnavailable(f"caricamento modello '{name}' fallito: {e}") from e


def is_available() -> bool:
    """True se sentence-transformers e importabile (non carica il modello)."""
    try:
        import sentence_transformers  # noqa: F401
        import torch  # noqa: F401
    except ImportError:
        return False
    return True


# --------------------------------------------------------------------------- #
# Segmentazione del testo agente in unita confrontabili
# --------------------------------------------------------------------------- #

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
# proposizioni dentro la frase: punteggiatura debole e congiunzioni frequenti
_CLAUSE_SPLIT = re.compile(r"\s*[;:,]\s*|\s+(?:e|che|ma|oppure|mentre|dove|con)\s+")
_MIN_UNIT_CHARS = 8


def split_units(text: str) -> list[str]:
    """Spezza il testo in unita a livello di proposizione.

    Tiene sia le frasi intere sia le proposizioni, deduplicate, per dare alla
    cosine massima la migliore chance di agganciare un concetto espresso in
    modo diverso senza diluirlo in una frase troppo lunga.
    """
    units: list[str] = []
    seen: set[str] = set()
    for sent in _SENT_SPLIT.split(text):
        sent = sent.strip()
        if len(sent) >= _MIN_UNIT_CHARS and sent.lower() not in seen:
            seen.add(sent.lower())
            units.append(sent)
        for clause in _CLAUSE_SPLIT.split(sent):
            clause = clause.strip()
            if len(clause) >= _MIN_UNIT_CHARS and clause.lower() not in seen:
                seen.add(clause.lower())
                units.append(clause)
    return units


_HEAD_SPLIT = re.compile(r"\s[—–-]\s")


def phrase_head(phrase: str) -> str:
    """Parte significativa di un bullet gold (prima del trattino esplicativo)."""
    return _HEAD_SPLIT.split(phrase, maxsplit=1)[0].strip()


# --------------------------------------------------------------------------- #
# Copertura semantica
# --------------------------------------------------------------------------- #

@dataclass
class PhraseCoverage:
    phrase: str
    covered: bool
    best_cos: float
    best_unit: str


def coverage(
    gold_phrases: list[str],
    agent_text: str,
    threshold: float = DEFAULT_THRESHOLD,
    model_name: str = DEFAULT_MODEL,
) -> list[PhraseCoverage]:
    """Per ogni gold phrase, copertura = cosine massima contro le unita agente.

    Confronta la testa della phrase (termine, senza glossa) con le proposizioni
    del testo dell'agente. Coperta se la cosine massima >= soglia.
    """
    if not gold_phrases:
        return []
    units = split_units(agent_text)
    if not units:
        return [PhraseCoverage(p, False, 0.0, "") for p in gold_phrases]

    model = get_model(model_name)
    from sentence_transformers import util

    heads = [phrase_head(p) for p in gold_phrases]
    gold_emb = model.encode(heads, convert_to_tensor=True, normalize_embeddings=True)
    unit_emb = model.encode(units, convert_to_tensor=True, normalize_embeddings=True)
    sims = util.cos_sim(gold_emb, unit_emb)  # [n_gold, n_units]

    out: list[PhraseCoverage] = []
    for i, phrase in enumerate(gold_phrases):
        row = sims[i]
        best_idx = int(row.argmax())
        best = float(row[best_idx])
        out.append(
            PhraseCoverage(
                phrase=phrase,
                covered=best >= threshold,
                best_cos=round(best, 4),
                best_unit=units[best_idx],
            )
        )
    return out
