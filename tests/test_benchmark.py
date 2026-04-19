"""Test per scripts/benchmark.py (v0.7.1)."""
from __future__ import annotations
import json
from pathlib import Path

import pytest

from scripts import benchmark as bench


GOLD_VALID = """# Test Author, Test Work

## Metadati
autore: Test Author
titolo: Test Work
anno: 2020
label: Test Label
luogo: Studio X
durata: 10:00
genere: test

## Tracklist verificata
verificato: true
fonte: fonte diretta

## Contesto critico

Contesto critico di prova con riferimenti a Schaeffer e alla musique anecdotique.

## Struttura attesa

- 00:00 - 05:00: prima sezione biofonica
- 05:00 - 10:00: seconda sezione antropofonica

## Terminologia attesa

- `field recording` — tecnica centrale
- `biofonia` — prima sezione
- `antropofonia` — seconda sezione
- `soundscape` — definizione complessiva

## Parentele stilistiche attese

- `Luc Ferrari` — filiazione musique anecdotique
- `Hildegard Westerkamp` — soundscape composition

## Fonti bibliografiche

- Pincelli 2020
- Moretti 2021

## Note per il benchmark

Fixture di test.
"""

GOLD_UNVERIFIED = GOLD_VALID.replace("verificato: true", "verificato: false")

AGENT_HIT = """
Lettura compositiva
Lettura drammaturgica

Il brano è un field recording che alterna biofonia a antropofonia,
ricordando la tradizione del soundscape. Parentele con Luc Ferrari
e con la soundscape composition di Hildegard Westerkamp.
"""

AGENT_MISS = """
Lettura compositiva
Il brano è un drone elettronico con heavy metal dominante. Parentele
con Earth e Sunn O))). Nessuna connessione alla tradizione anecdotica.
"""


@pytest.fixture
def tmp_gold(tmp_path):
    p = tmp_path / "gold.md"
    p.write_text(GOLD_VALID)
    return p


@pytest.fixture
def tmp_gold_unverified(tmp_path):
    p = tmp_path / "gold.md"
    p.write_text(GOLD_UNVERIFIED)
    return p


def test_parse_golden_basic(tmp_gold):
    g = bench.parse_golden(tmp_gold)
    assert g.metadata["autore"] == "Test Author"
    assert g.metadata["titolo"] == "Test Work"
    assert g.tracklist_verified is True
    assert g.verification_source == "fonte diretta"
    assert len(g.terminologia) == 4
    assert len(g.parentele) == 2
    assert "Luc Ferrari" in g.parentele[0]


def test_parse_golden_unverified(tmp_gold_unverified):
    g = bench.parse_golden(tmp_gold_unverified)
    assert g.tracklist_verified is False


def test_match_phrase_exact():
    agent = {"field", "recording", "biofonia"}
    gold = bench._lemmas("field recording")
    assert bench.match_phrase(agent, gold) is True


def test_match_phrase_partial():
    agent = {"field", "biofonia"}
    gold = bench._lemmas("field recording")
    # 1/2 = 50% < 60% threshold → no match
    assert bench.match_phrase(agent, gold) is False


def test_match_phrase_single_word():
    agent = {"biofonia"}
    assert bench.match_phrase(agent, bench._lemmas("biofonia")) is True
    assert bench.match_phrase(agent, bench._lemmas("antropofonia")) is False


def test_compare_perfect(tmp_gold):
    g = bench.parse_golden(tmp_gold)
    r = bench.compare(AGENT_HIT, g)
    assert r.recall_term == 1.0  # tutti i 4 termini core coperti
    assert r.recall_parent == 1.0  # Ferrari + Westerkamp colti
    assert r.score_aggregate > 70.0
    assert r.gold_verified is True
    assert not any("non verificato" in w for w in r.warnings)


def test_compare_zero_overlap(tmp_gold):
    g = bench.parse_golden(tmp_gold)
    r = bench.compare(AGENT_MISS, g)
    assert r.recall_term < 0.5  # pochissimo copertura
    assert r.score_aggregate < 40.0


def test_compare_unverified_warns(tmp_gold_unverified):
    g = bench.parse_golden(tmp_gold_unverified)
    r = bench.compare(AGENT_HIT, g)
    assert any("non verificato" in w for w in r.warnings)


def test_run_benchmark_with_agent_source(tmp_gold, tmp_path):
    audio = tmp_path / "audio.mp3"
    audio.touch()
    agent_md = tmp_path / "agent.md"
    agent_md.write_text(AGENT_HIT)
    report_md, result = bench.run_benchmark(audio, tmp_gold, agent_md)
    assert "Score" in report_md
    assert "Aggregato" in report_md
    assert result.score_aggregate > 70.0


def test_result_to_dict_roundtrip(tmp_gold, tmp_path):
    audio = tmp_path / "audio.mp3"
    audio.touch()
    agent_md = tmp_path / "agent.md"
    agent_md.write_text(AGENT_HIT)
    _, result = bench.run_benchmark(audio, tmp_gold, agent_md)
    d = bench.result_to_dict(result)
    # round-trip JSON
    roundtrip = json.loads(json.dumps(d))
    assert roundtrip["score_aggregate"] == result.score_aggregate
    assert roundtrip["gold_verified"] == result.gold_verified


def test_run_benchmark_no_agent_source_raises(tmp_gold, tmp_path):
    audio = tmp_path / "audio.mp3"
    audio.touch()
    with pytest.raises(FileNotFoundError):
        bench.run_benchmark(audio, tmp_gold, None)
