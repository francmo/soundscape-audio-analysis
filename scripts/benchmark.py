"""Benchmark dell'output dell'agente compositivo contro analisi accademiche
di riferimento (`references/golden_analyses/<id>.md`).

Metriche:
- **Precision terminologica**: % di termini citati dall'agente che sono nel gold.
- **Recall terminologico**: % di termini del gold citati dall'agente.
- **Jaccard**: |intersezione| / |unione| sui lemmi normalizzati.
- **Precision parentele** / **Recall parentele**: stesso calcolo sui
  compositori/scuole elencati in "Parentele stilistiche attese".
- **Score aggregato 0-100**: media pesata
  (0.30 precision_term + 0.30 recall_term + 0.20 precision_par + 0.20 recall_par).

Il gold è parsabile grazie allo schema `templates/golden_analysis_schema.md`:
sezioni markdown dedicate e obbligatorie.
"""
from __future__ import annotations
import json
import math
import re
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path


# --------------------------------------------------------------------------- #
# Parsing del gold
# --------------------------------------------------------------------------- #

HEADING = re.compile(r"^##\s+(.+?)\s*$")
BULLET = re.compile(r"^[-*]\s+(.+?)\s*$")
KV = re.compile(r"^([a-zà-ù][\w_ ]*?)\s*:\s*(.+?)\s*$")


@dataclass
class Golden:
    metadata: dict
    tracklist_verified: bool
    verification_source: str
    contesto: str
    struttura: str
    terminologia: list[str]
    parentele: list[str]
    bibliografia: list[str]
    note_benchmark: str
    raw_sections: dict


def parse_golden(md_path: Path) -> Golden:
    text = md_path.read_text(encoding="utf-8")
    sections: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            current = m.group(1).strip().lower()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)

    def get(name: str) -> list[str]:
        for key in sections:
            if key.startswith(name):
                return sections[key]
        return []

    metadata_lines = get("metadati")
    metadata: dict[str, str] = {}
    for ln in metadata_lines:
        m = KV.match(ln.strip())
        if m:
            metadata[m.group(1).strip().lower()] = m.group(2).strip()

    tracklist_lines = get("tracklist verificata")
    verified = False
    source = ""
    for ln in tracklist_lines:
        m = KV.match(ln.strip())
        if not m:
            continue
        k, v = m.group(1).lower(), m.group(2)
        if k == "verificato":
            verified = v.strip().lower() in ("true", "sì", "si", "yes")
        elif k == "fonte":
            source = v.strip()

    def _bullets(lines: list[str]) -> list[str]:
        out = []
        for ln in lines:
            m = BULLET.match(ln.strip())
            if m:
                out.append(m.group(1).strip())
        return out

    terminologia = _bullets(get("terminologia attesa"))
    parentele = _bullets(get("parentele stilistiche attese"))
    bibliografia = _bullets(get("fonti bibliografiche"))

    def _text(lines: list[str]) -> str:
        return "\n".join(l for l in lines if l.strip())

    return Golden(
        metadata=metadata,
        tracklist_verified=verified,
        verification_source=source,
        contesto=_text(get("contesto critico")),
        struttura=_text(get("struttura attesa")),
        terminologia=terminologia,
        parentele=parentele,
        bibliografia=bibliografia,
        note_benchmark=_text(get("note per il benchmark")),
        raw_sections={k: "\n".join(v) for k, v in sections.items()},
    )


# --------------------------------------------------------------------------- #
# Normalizzazione lemmi per confronto fuzzy
# --------------------------------------------------------------------------- #

_WORD = re.compile(r"[a-z0-9]+")


def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.lower().strip()


def _lemmas(s: str) -> set[str]:
    return set(_WORD.findall(_normalize(s)))


_ACRONYM_IN_PAREN = re.compile(r"\(([A-Z][A-Z0-9\/]+)\)")
_STOPWORDS = {
    # italiano
    "di", "del", "della", "dei", "delle", "il", "la", "lo", "gli", "le", "un", "una",
    "con", "per", "su", "in", "a", "e", "o", "che", "come",
    # francese
    "de", "du", "des", "le", "la", "les", "et", "ou", "au", "aux", "dans", "sur",
    # inglese
    "the", "of", "in", "on", "to", "and", "or", "as", "by",
    # anglosassone per "paesaggi anglosassoni"
}


def _content_lemmas(s: str) -> set[str]:
    """Lemmi di contenuto: rimuove stopwords comuni (it/fr/en)."""
    return {w for w in _lemmas(s) if w not in _STOPWORDS}


def _extract_acronym_aliases(text: str) -> list[str]:
    """Estrae alias equivalenti da una parentela gold.

    Es. 'Groupe de Recherches Musicales (GRM)' genera alias 'GRM'.
    Permette match 'cognome-soltanto' e acronimi senza penalizzare.
    """
    aliases = []
    for m in _ACRONYM_IN_PAREN.finditer(text):
        aliases.append(m.group(1))
    return aliases


def _core_phrases(items: list[str]) -> list[tuple[set[str], list[set[str]]]]:
    """Da ogni bullet, estrae (core_lemmas, aliases).

    core_lemmas: lemmi di contenuto del testo prima del primo `—` o `-` lungo,
    stopwords rimosse.
    aliases: lista di set di lemmi alternativi (es. acronimi in parentesi).

    v0.8.0: il match phrase contro gold accetta sia il core (con soglia
    multi-parola) sia uno qualunque degli aliases (match esatto).
    """
    out = []
    for it in items:
        head = re.split(r"\s[—–-]\s", it, maxsplit=1)[0]
        core = _content_lemmas(head)
        aliases = []
        for ac in _extract_acronym_aliases(head):
            ac_lem = _lemmas(ac)
            if ac_lem:
                aliases.append(ac_lem)
        if core or aliases:
            out.append((core, aliases))
    return out


def match_phrase(agent_lemmas: set[str], gold_phrase: set[str],
                 aliases: list[set[str]] | None = None) -> bool:
    """Un gold è considerato coperto se:
    - tutti i lemmi del core sono presenti (1-parola: match esatto), OPPURE
    - almeno N//2 dei lemmi del core sono presenti (multi-parola), OPPURE
    - uno qualunque degli aliases è interamente contenuto nell'agent (match
      esatto di acronimi come "GRM" per "Groupe de Recherches Musicales (GRM)").

    Questo permette sia cognome-soltanto sia acronimo-soltanto di matchare
    un'entry gold formulata per esteso.
    """
    if gold_phrase:
        if len(gold_phrase) == 1:
            if gold_phrase.issubset(agent_lemmas):
                return True
        else:
            needed = max(1, len(gold_phrase) // 2)
            if len(gold_phrase & agent_lemmas) >= needed:
                return True
    for ac in (aliases or []):
        if ac and ac.issubset(agent_lemmas):
            return True
    return False


# --------------------------------------------------------------------------- #
# Confronto agente-vs-gold
# --------------------------------------------------------------------------- #

@dataclass
class BenchmarkResult:
    precision_term: float
    recall_term: float
    jaccard_term: float
    precision_parent: float
    recall_parent: float
    jaccard_parent: float
    score_aggregate: float
    terms_covered: list[str]
    terms_missing: list[str]
    parents_covered: list[str]
    parents_missing: list[str]
    gold_verified: bool
    warnings: list[str]


CANON_TERMS = [
    # Schaeffer / TARTYP
    "tenuto", "iterativo", "impulsivo", "accumulativo", "cross-sintesi",
    "morphing", "granulare", "oggetto sonoro", "ascolto ridotto",
    # Smalley
    "flow", "oscillation", "rotation", "push", "drag", "dilation",
    "endogeny", "multiplication", "divergence", "convergence", "spectromorphology",
    # Chion
    "causale", "semantico", "ridotto", "acousmetre", "indessicalita",
    # Schafer
    "keynote", "signal", "soundmark", "hi-fi", "lo-fi", "soundscape",
    # Truax
    "readiness", "search", "listening mode",
    # Krause
    "biofonia", "antropofonia", "geofonia", "niche", "nicchia",
    # Westerkamp
    "soundwalk",
    # generale
    "field recording", "drone", "plateau", "ad arco", "atlante",
]


def _scan_canon_terms(text: str) -> set[str]:
    norm = _normalize(text)
    found = set()
    for term in CANON_TERMS:
        if term in norm:
            found.add(term)
    return found


def compare(agent_text: str, golden: Golden) -> BenchmarkResult:
    agent_lem = _lemmas(agent_text)
    warnings: list[str] = []

    if not golden.tracklist_verified:
        warnings.append(
            "Gold non verificato contro tracklist ufficiale: score da interpretare con cautela."
        )

    gold_terms = _core_phrases(golden.terminologia)
    gold_parents = _core_phrases(golden.parentele)

    if not gold_terms:
        warnings.append("Sezione 'Terminologia attesa' vuota nel gold.")
    if not gold_parents:
        warnings.append("Sezione 'Parentele stilistiche attese' vuota nel gold.")

    terms_covered_raw = []
    terms_missing_raw = []
    for i, (gt, aliases) in enumerate(gold_terms):
        if match_phrase(agent_lem, gt, aliases):
            terms_covered_raw.append(golden.terminologia[i])
        else:
            terms_missing_raw.append(golden.terminologia[i])

    parents_covered_raw = []
    parents_missing_raw = []
    for i, (gp, aliases) in enumerate(gold_parents):
        if match_phrase(agent_lem, gp, aliases):
            parents_covered_raw.append(golden.parentele[i])
        else:
            parents_missing_raw.append(golden.parentele[i])

    agent_canon = _scan_canon_terms(agent_text)
    gold_canon = _scan_canon_terms("\n".join(golden.terminologia + [golden.struttura, golden.contesto]))

    recall_term = (len(terms_covered_raw) / len(gold_terms)) if gold_terms else 0.0
    precision_term = 0.0
    if agent_canon:
        hits = len(agent_canon & gold_canon)
        precision_term = hits / len(agent_canon)
    jaccard_term = 0.0
    if agent_canon or gold_canon:
        jaccard_term = len(agent_canon & gold_canon) / len(agent_canon | gold_canon)

    recall_par = (len(parents_covered_raw) / len(gold_parents)) if gold_parents else 0.0
    precision_par = 0.0
    if gold_parents:
        if parents_covered_raw:
            precision_par = len(parents_covered_raw) / max(1, len(gold_parents))
    union = len(gold_parents) + max(0, len(_lemmas(agent_text)) // 200)
    jaccard_par = len(parents_covered_raw) / max(1, union) if union else 0.0

    score = (
        0.30 * precision_term
        + 0.30 * recall_term
        + 0.20 * precision_par
        + 0.20 * recall_par
    ) * 100.0

    return BenchmarkResult(
        precision_term=round(precision_term, 4),
        recall_term=round(recall_term, 4),
        jaccard_term=round(jaccard_term, 4),
        precision_parent=round(precision_par, 4),
        recall_parent=round(recall_par, 4),
        jaccard_parent=round(jaccard_par, 4),
        score_aggregate=round(score, 1),
        terms_covered=terms_covered_raw,
        terms_missing=terms_missing_raw,
        parents_covered=parents_covered_raw,
        parents_missing=parents_missing_raw,
        gold_verified=golden.tracklist_verified,
        warnings=warnings,
    )


def format_report(
    audio_path: Path,
    gold_path: Path,
    agent_text: str,
    golden: Golden,
    result: BenchmarkResult,
) -> str:
    lines: list[str] = []
    lines.append(f"# Benchmark report")
    lines.append("")
    lines.append(f"- Audio: `{audio_path.name}`")
    lines.append(f"- Gold: `{gold_path.name}`")
    lines.append(f"- Autore gold: {golden.metadata.get('autore', '?')}")
    lines.append(f"- Titolo gold: {golden.metadata.get('titolo', '?')}")
    lines.append(f"- Gold verificato: {'sì' if result.gold_verified else 'NO'}")
    if golden.verification_source:
        lines.append(f"- Fonte verifica: {golden.verification_source}")
    lines.append("")
    lines.append("## Score")
    lines.append(f"- **Aggregato: {result.score_aggregate:.1f}/100**")
    lines.append(f"- Precision terminologica: {result.precision_term:.3f}")
    lines.append(f"- Recall terminologico: {result.recall_term:.3f}")
    lines.append(f"- Jaccard terminologia: {result.jaccard_term:.3f}")
    lines.append(f"- Precision parentele: {result.precision_parent:.3f}")
    lines.append(f"- Recall parentele: {result.recall_parent:.3f}")
    lines.append(f"- Jaccard parentele: {result.jaccard_parent:.3f}")
    lines.append("")
    if result.warnings:
        lines.append("## Avvertenze")
        for w in result.warnings:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("## Terminologia coperta dall'agente")
    for t in result.terms_covered:
        lines.append(f"- {t}")
    if not result.terms_covered:
        lines.append("_(nessuna)_")
    lines.append("")
    lines.append("## Terminologia mancante")
    for t in result.terms_missing:
        lines.append(f"- {t}")
    if not result.terms_missing:
        lines.append("_(nessuna)_")
    lines.append("")
    lines.append("## Parentele colte")
    for p in result.parents_covered:
        lines.append(f"- {p}")
    if not result.parents_covered:
        lines.append("_(nessuna)_")
    lines.append("")
    lines.append("## Parentele mancanti")
    for p in result.parents_missing:
        lines.append(f"- {p}")
    if not result.parents_missing:
        lines.append("_(nessuna)_")
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Lettura dell'output agente da PDF (o fallback da file testo)
# --------------------------------------------------------------------------- #

def extract_agent_reading(pdf_or_txt_path: Path) -> str:
    if pdf_or_txt_path.suffix.lower() == ".md" or pdf_or_txt_path.suffix.lower() == ".txt":
        return pdf_or_txt_path.read_text(encoding="utf-8")
    if pdf_or_txt_path.suffix.lower() != ".pdf":
        raise ValueError(f"Formato non supportato: {pdf_or_txt_path.suffix}")
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError(
            "pypdf non installato. Installa con `pip install pypdf`."
        ) from e
    reader = PdfReader(str(pdf_or_txt_path))
    pages = [page.extract_text() for page in reader.pages]
    full = "\n".join(pages)
    start = full.find("Lettura compositiva")
    end = full.find("Documento prodotto dalla skill", start if start >= 0 else 0)
    if start >= 0 and end > start:
        return full[start:end]
    if start >= 0:
        return full[start:]
    return full


# --------------------------------------------------------------------------- #
# Entry point per uso da cli
# --------------------------------------------------------------------------- #

def run_benchmark(
    audio_path: Path,
    gold_path: Path,
    agent_source: Path | None = None,
) -> tuple[str, BenchmarkResult]:
    """Esegue il confronto e restituisce (markdown_report, BenchmarkResult).

    `agent_source`: percorso a PDF report esistente, agent_reading.md, o summary
    JSON. Se None, cerca file accanto all'audio con pattern <stem>_report.pdf.
    """
    golden = parse_golden(gold_path)
    if agent_source is None:
        candidates = [
            audio_path.with_name(audio_path.stem + "_report.pdf"),
            audio_path.with_name(audio_path.stem + "_agent_reading.md"),
        ]
        agent_source = next((c for c in candidates if c.exists()), None)
        if agent_source is None:
            raise FileNotFoundError(
                f"Nessun output agente trovato accanto a {audio_path}. "
                f"Lancia prima `soundscape analyze` oppure passa --agent-source."
            )
    agent_text = extract_agent_reading(agent_source)
    result = compare(agent_text, golden)
    report_md = format_report(audio_path, gold_path, agent_text, golden, result)
    return report_md, result


def result_to_dict(result: BenchmarkResult) -> dict:
    return asdict(result)
