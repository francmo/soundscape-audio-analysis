from __future__ import annotations

import pytest

from scripts import embedding_match as em

pytestmark = pytest.mark.skipif(
    not em.is_available(),
    reason="sentence-transformers non installato (feature opzionale)",
)


def test_split_units_clauses():
    units = em.split_units("Il gesto granulare frammenta il materiale, mentre un drone resta sotto.")
    # almeno la frase intera + qualche proposizione
    assert any("granulare" in u for u in units)
    assert len(units) >= 2


def test_phrase_head_strips_gloss():
    assert em.phrase_head("musique anecdotique — registrazione di scene quotidiane") == "musique anecdotique"


def test_coverage_synonym_vs_unrelated():
    gold = ["sviluppo timbrico", "tariffa della lezione"]
    agent = "Il brano mostra una marcata evoluzione spettrale che trasforma il timbro nel tempo."
    cov = {c.phrase: c for c in em.coverage(gold, agent, threshold=0.45)}
    # sinonimia descrittiva colta
    assert cov["sviluppo timbrico"].covered is True
    assert cov["sviluppo timbrico"].best_cos >= 0.45
    # concetto estraneo non coperto
    assert cov["tariffa della lezione"].covered is False


def test_coverage_empty_inputs():
    assert em.coverage([], "qualcosa") == []
    res = em.coverage(["x"], "")
    assert res and res[0].covered is False


def test_compare_hybrid_recall_ge_lexical():
    """Il metodo hybrid non puo coprire meno termini del solo lessicale."""
    from scripts import benchmark as bench

    golden = bench.Golden(
        metadata={"autore": "Test", "titolo": "T"},
        tracklist_verified=True,
        verification_source="diretta",
        contesto="",
        struttura="",
        terminologia=["sviluppo timbrico", "field recording"],
        parentele=[],
        bibliografia=[],
        note_benchmark="",
        raw_sections={},
    )
    # l'agente usa una parafrasi ("evoluzione spettrale") e un termine esatto
    agent = "Si percepisce una netta evoluzione spettrale. La tecnica e quella del field recording."
    lex = bench.compare(agent, golden, method="lexical")
    hyb = bench.compare(agent, golden, method="hybrid")
    assert hyb.recall_term >= lex.recall_term
    # la parafrasi viene colta solo in hybrid
    assert hyb.recall_term > lex.recall_term
