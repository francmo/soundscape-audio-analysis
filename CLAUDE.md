# CLAUDE.md - soundscape-audio-analysis

Toolkit Python per l'analisi tecnica e compositiva di soundscape, field
recording e musica elettroacustica. Skill Claude Code con CLI unificata
`soundscape` (wrapper `bin/soundscape`, venv dedicata in `venv/`).

## Orientarsi

- A ogni sessione leggere prima `CHANGELOG.md` (release correnti) e
  `ROADMAP.md` (piano, addenda, mappa dei moduli in "File chiave per
  orientarsi").
- La versione vive SOLO in `pyproject.toml` ed è letta da
  `scripts/version.py::skill_version`. Mai hardcodare numeri di versione
  nei sorgenti; il guard-rail è `tests/test_version.py` (pyproject, voce in
  testa al CHANGELOG e BibTeX del README devono coincidere).
- Lo stato di sessione locale sta in `.claude/SESSION_HANDOFF.md`
  (gitignored, assente dal repo pubblico).

## Comandi

```bash
bash bin/soundscape analyze <audio.wav>                  # pipeline completa
bash bin/soundscape report <cartella>                    # report comparativo corpus
bash bin/soundscape compare <ann.json> <summary.json>    # annotazione umana vs analisi
bash bin/soundscape benchmark <audio> --against <gold.md>
bash bin/soundscape enrich <ann.json> <summary.json>     # blocco analysis v1.2 nell'Atelier
bash bin/soundscape version

# Suite leggera (~1 min), esclude i test con modelli reali PANNs/CLAP
venv/bin/python -m pytest tests/ -q -k "not panns and not clap_tagging and not semantic_classifier"
```

## Convenzioni non negoziabili

- Italiano corretto con accenti veri (è, più, città, plausibilità) in
  stringhe renderizzate, commenti e CHANGELOG; niente em dash.
- Ogni stringa dinamica destinata a un Paragraph ReportLab passa da
  `report_pdf._esc` (escaping XML) PRIMA dell'interpolazione nel markup
  intenzionale.
- Contratto interchange additivo con reader rule `^1\.`; mai cambiare la
  semantica dei campi 1.x esistenti.
- Test prima del commit, suite leggera a zero regressioni.
- Versioning: minor per nuove feature, patch per fix. Bump = pyproject +
  voce CHANGELOG + BibTeX README (il test di versione li vuole allineati).
- Privacy: i casi studio didattici compaiono SOLO con pseudonimi (caso A,
  caso B, ...), mai nomi reali nei file tracciati.
- Tipografia PDF: sfondo bianco, testo nero, font Unicode OFL già registrati
  in `report_styles.py`.

## Interoperabilità con la PWA Annotation Atelier

- Vocabolario canonico in `references/taxonomies.json` (128 termini, 8
  tassonomie); la PWA si sincronizza da qui col proprio bridge.
- Schema annotazione `templates/annotation_schema.json` (v1.0), contratto
  esteso `templates/interchange_schema_v1.2.json` (blocco `analysis`).
- Flusso: la PWA esporta il JSON di annotazione; `enrich` vi inietta
  l'analisi della skill; `compare` misura l'accordo umano vs macchina
  (confini strutturali, famiglia Krause con Cohen's kappa, copertura).
