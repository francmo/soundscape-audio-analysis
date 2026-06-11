# Soundscape Interchange v1.1: contratto di interoperabilità

Versione 1.1 del 11/06/2026. Sede canonica: questo repo (`soundscape-audio-analysis/templates/`), accanto a `annotation_schema.json` (v1.0) e `taxonomies` di riferimento. Copie operative: `demo-soundscapestudio/docs/INTEROP.md`, nota in `soundscape-critic-web/docs/`.

## Scopo

Un solo formato di scambio per i quattro strumenti dell'ecosistema:

| Strumento | Ruolo | Scrive | Legge |
|---|---|---|---|
| Soundscape Studio (PWA) | allenamento + raccolta sul campo | `recording` | `analysis`, `annotations` |
| Annotation Atelier (PWA) | annotazione scientifica | `annotations`, `structure` | `recording` (contesto), `analysis` (read-only, futuro) |
| soundscape-critic-web (PWA) | analisi rapida nel browser | `analysis` | `recording` (contesto) |
| skill soundscape-audio-analysis (CLI) | analisi profonda locale | `analysis` (estratto del `*_summary.json`) | `recording` via `--context` |

## Schema

`templates/interchange_schema_v1.1.json`. È l'annotation schema v1.0 esteso in modo **additivo** con due blocchi opzionali top-level:

- **`recording`**: contesto di registrazione (recordingId, recordedAt, gps, exercise, equipment con micPattern/windProtection/dspProfile, environment, performerNotes, userSelections).
- **`analysis`**: risultati di analisi automatica (engine{name,version}, analyzedAt, levels LUFS/peak/crest, spectral con bandsSchafer, tags CLAP/PANNs globali o a segmenti, summaryRef).

Nessun campo v1.0 cambia nome, tipo o semantica.

## Regole di compatibilità (non negoziabili)

1. **I writer conformi scrivono `schemaVersion: "1.1"`.**
2. **I reader accettano `^1\.`** (1.0, 1.1, futuri 1.x) e **ignorano i blocchi opzionali che non conoscono**. Niente rifiuto su campi sconosciuti di livello root.
3. **Round-trip senza perdita**: chi legge e riscrive il file (es. Atelier che riesporta) DEVE preservare i blocchi che non gestisce.
4. **`audio.sha256` fortemente raccomandato**: è la chiave di riconciliazione quando lo stesso audio passa tra strumenti.
5. I file v1.0 esistenti restano validi: un reader 1.1 li legge senza modifiche.

### Adeguamenti reader richiesti (one-line, da fare con il primo rilascio utile)

- Atelier: `src/lib/importer.ts:28`, da `version !== ANNOTATION_SCHEMA_VERSION` a check `^1\.` + preservazione blocchi sconosciuti nell'export.
- Skill: FATTO l'11/06/2026: `scripts/load_annotation.py` accetta `^1\.` e preserva i blocchi sconosciuti in `AnnotationProject.extra_blocks` (test in `tests/test_load_annotation.py`).
- critic-web: nasce già 1.1 (nessun legacy).

## Canali di scambio

1. **File download/upload: canale base universale.** Funziona ovunque, iOS Safari standalone incluso. Ogni strumento DEVE supportarlo. Il file viaggia come `<base>.interchange.json` accanto all'audio.
2. **postMessage bridge: progressive enhancement.** Solo quando lo strumento di destinazione è aperto via `window.open` dallo strumento sorgente. Envelope:

```json
{ "protocol": "soundscape-interchange", "version": "1.1",
  "type": "clip-offer" | "clip-request" | "analysis-result" | "ack",
  "payload": { "interchange": { }, "audioBlob": "(transferable o ArrayBuffer)" } }
```

   Handshake: sorgente apre destinazione con `?bridge=1`; destinazione pronta invia `{type:"clip-request"}` all'opener; sorgente risponde `clip-offer`; destinazione conferma `ack`. **Timeout 3 s senza `ack` → fallback automatico al canale file con istruzioni UI.** Allowlist origin esplicita in entrambe le direzioni; feature-detect su `window.opener` (su iOS standalone è spesso null: in quel caso non proporre il bridge).
3. **NIENTE same-origin path-based per ora** (conflitti di scope service worker; rivalutare dopo la Fase 4 di Studio).

## Naming convention

- Base name: `<slug-luogo-o-esercizio>_<YYYYMMDD-HHmmss>` (es. `mercato-albinelli_20260611-073000`).
- Audio: `<base>.wav` | `<base>.m4a` | `<base>.webm` (Studio registra Opus/AAC di default, WAV opzionale).
- Interchange: `<base>.interchange.json`.
- Pacchetto per la skill: `<base>.analysis-pack.zip` = audio + `context.json` (estratto: blocchi `audio` + `recording`). La skill lo consuma con `--context context.json` (INT-11).
- Output skill: invariati (`*_summary.json`, `*_report.pdf`); il blocco `analysis` scritto nell'interchange è un ESTRATTO del summary, con `summaryRef` che punta al file completo.

## Requisiti minimi per critic-web v0.1 (INT-02)

1. Il bottone "Esporta risultati" scrive un interchange 1.1 con `audio` (+sha256), `metadata` minimale, `analysis` completo dei dati calcolati (levels, spectral.bandsSchafer, tags CLAP top-5).
2. Se l'utente ha caricato anche un `.interchange.json` accanto all'audio (o ricevuto via bridge), critic-web PRESERVA i blocchi esistenti e aggiunge/sostituisce solo `analysis`.
3. Parametri URL riservati per il futuro bridge (v0.1.1): `?bridge=1` ignorato in v0.1 senza errori.
4. Nessun listener postMessage richiesto in v0.1 (va in v0.1.1, INT-08), per non erodere il budget della scadenza del 19/06.

## Versionamento del contratto

Modifiche additive (nuovi blocchi/campi opzionali) = bump minor (1.2, 1.3...) con reader già pronti via regola `^1\.`. Modifiche incompatibili = bump major (2.0) + migrazione esplicita. Questo file e lo schema si aggiornano insieme, nella sede canonica, e le copie nei progetti si sincronizzano a mano nel primo rilascio utile.
