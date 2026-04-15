# Feedback utente sui report della skill

Cartella per raccogliere annotazioni umane sui report generati dalla skill,
con l'obiettivo di migliorare iterativamente il vocabolario CLAP, il mapping
accademico, le soglie di filtro contestuale e le regole di hallucination.

## Come usare

1. Esegui la skill su un brano: `bin/soundscape analyze <file.wav>`.
2. Apri il PDF generato e leggilo.
3. Copia `TEMPLATE.md` in questa cartella con nome `<nome_brano>.md`.
4. Compila almeno la sezione 9 (Note libere); le altre se hai tempo.
5. Fai sapere quando il file e' pronto: viene tradotto in patch concrete al
   codice (vocabolario, mapping, soglie).

Le sezioni compilate vengono riprocessate per:

- aggiungere/rimuovere prompt al vocabolario CLAP
- correggere `clap_academic_mapping_it.json`
- calibrare soglie (`HUM_CONTEXT_*`, `HALLUCINATION_*`, `SPEECH_SUGGEST_*`)
- aggiungere parole chiave al filtro hallucination
- documentare casi limite per regressione futura

## File presenti

- `TEMPLATE.md`: schema vuoto da copiare per ogni nuovo brano.
- `VB_Flauto.md`: istanza pre-compilata per Very Beautiful flauto solista
  (v0.5.0 report, da completare e ri-eseguire con v0.5.1).
