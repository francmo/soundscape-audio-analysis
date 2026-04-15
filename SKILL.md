---
name: soundscape-audio-analysis
description: >
  Analisi audio completa per soundscape, field recording e composizione elettroacustica.
  Dalla v0.3 supporta sia singolo file che **report comparativo di corpus**. Calcola
  livelli (peak, RMS, crest, LUFS, true peak), diagnosi tecnica (clipping, DC offset,
  hum 50/60 Hz con baseline locale), spettro (bande Schafer, centroide, rolloff, flatness,
  picchi, onset density), indici ecoacustici (ACI, NDSI, entropia H, BI, ADI/AEI),
  classificazione semantica PANNs CNN14 (default v0.2) o YAMNet legacy con pre-check LUFS,
  auto-tagging CLAP italiano (70 prompt), narrativa italiana segmentata 30 s, confronto
  con profili GRM (Parmegiani, Westerkamp, Ferrari, Krause) e genera report PDF ReportLab
  in stile ABTEC40. Il sotto-comando `report` analizza una cartella di file audio e
  produce un PDF comparativo con grafici comparativi (LUFS, dynamic range, heatmap bande,
  radar ecoacustico, similarità CLAP) e sintesi testuale generata da sessione Claude non
  interattiva che usa il REPORT_ANALISI di Villa Ficana come riferimento di stile.
  Gestisce file multicanale fino a 7.1.4. Attiva quando l'utente parla di field
  recording, soundscape, analisi spettrale, spettrogramma, LUFS, clipping, hum, YAMNet,
  PANNs, CLAP, bande Schafer, biofonia, antropofonia, geofonia, composizione
  elettroacustica, musique concrète, GRM, Parmegiani, Westerkamp, Ferrari, Krause, report
  comparativo, corpus audio, confronto fra registrazioni, batch di analisi, relazione di
  corpus.
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Soundscape Audio Analysis

Infrastruttura stabile per l'analisi tecnica e compositiva di file audio.
Usa questa skill ogni volta che l'utente chiede di analizzare file audio per scopi
soundscape, field recording, composizione elettroacustica, didattica AFAM, oppure chiede
hum check, LUFS, bande spettrali, classificazione semantica, indici ecoacustici, confronto
con profili di riferimento GRM, generazione di report PDF o schede di field recording.

## Comandi principali

Il comando unificato è un wrapper shell che attiva il virtualenv dedicato ed esegue la
pipeline. Due modalità:

```bash
# Analisi di singolo file (o cartella, ogni file produce un PDF separato)
bash ~/.claude/skills/soundscape-audio-analysis/bin/soundscape analyze <path> [flags]

# Report comparativo di un corpus (v0.3): un solo PDF con sintesi
bash ~/.claude/skills/soundscape-audio-analysis/bin/soundscape report <cartella> [flags]

# Integra manualmente una sintesi markdown in un PDF di corpus parziale
bash ~/.claude/skills/soundscape-audio-analysis/bin/soundscape report-merge <pdf> <md>
```

Dove `<path>` può essere:
- un singolo file audio (WAV, MP3, FLAC, AIFF, OGG)
- una cartella contenente più file audio

Flag principali:

- `--semantic/--no-semantic`  classificazione YAMNet (default attivo)
- `--birdnet`                 riconoscimento avifauna con BirdNET (opzionale, richiede birdnetlib)
- `--ecoacoustic=basic|extended`  indici ecoacustici (default basic: ACI, NDSI, H, BI)
- `--compare=all|<profile_id>|none`  confronto con profili GRM (default all)
- `--report=pdf|md|json|all`   formato output (default pdf+json)
- `--output=<dir>`              cartella di output (default: dir del file audio)
- `--multichannel=auto|split|downmix-only`  gestione file multicanale (default auto)
- `--agent/--no-agent`          invocazione agente compositivo (default attivo)
- `--lang=it|en`                lingua output (default it)

Sub-comandi per gestione profili GRM:

```bash
soundscape profile list
soundscape profile show <nome>
soundscape profile build <nome> <audio1> [<audio2> ...] --title "..." --author "..." --year <anno>
```

## Report comparativo di corpus (v0.3)

```bash
soundscape report <cartella> [--output <dir>] [--corpus-title "..."]
                              [--rerun] [--yes] [--model opus]
                              [--no-synth] [--golden <path>]

soundscape report-merge <pdf_parziale> <sintesi.md>
```

`soundscape report` scansiona la cartella indicata, lancia la pipeline `analyze`
su ogni file (con cache di freschezza), raccoglie i summary JSON, genera cinque
grafici comparativi (LUFS, dynamic range, heatmap bande Schafer, radar
ecoacustico, similarità CLAP) e invoca una sessione Claude Code non interattiva
che usa il REPORT_ANALISI di Villa Ficana (`references/golden_reports/`) come
riferimento di stile. Il PDF finale unisce panoramica, grafici e sintesi.

Se `claude` non è nel PATH o la sintesi fallisce, il comando salva comunque il
prompt completo in `<out>/corpus_synth_prompt.md` e produce un PDF parziale. Il
sub-comando `report-merge` permette di integrare successivamente una sintesi
markdown esterna nel PDF esistente.

## Workflow tipico

1. **Utente fornisce uno o più file audio** (link Drive, path locale, batch in cartella).
2. **Invoca la skill**: lancia il comando `soundscape analyze` sul path.
3. **Pipeline automatica**:
   - Metadati e caricamento audio (mono/multicanale)
   - Analisi tecnica (livelli, LUFS, clipping, DC, hum con baseline locale)
   - Analisi spettrale (bande Schafer, feature timbriche, onset)
   - Indici ecoacustici
   - Classificazione semantica con pre-check LUFS (se il file è sotto -45 LUFS, applica gain in memoria per evitare il fallimento tipo Villa Ficana 97% Silence)
   - Analisi multicanale se il file ha più di un canale
   - Confronto con profili GRM
   - Generazione grafici (spettrogramma, waveform, timeline, radar)
   - Invocazione dell'agente `soundscape-composer-analyst` per la lettura critica
   - Generazione PDF ReportLab stile ABTEC40
4. **Output**: PDF + JSON summary + PNG + scheda field recording nella cartella indicata.

## Quando NON usare questa skill

- Ascolto casuale di un file (usa player standard)
- Conversione di formato senza analisi (usa ffmpeg direttamente)
- Editing audio (usa Reaper, Audacity, Max/MSP)

## Dipendenze

- Python 3.12 (venv dedicata in `venv/`)
- ffmpeg, ffprobe (installati con brew)
- TensorFlow 2.x + tensorflow-hub (per YAMNet)
- ReportLab per PDF
- librosa, soundfile, numpy, scipy, matplotlib

Tutte gestite dentro il virtualenv della skill. Il primo uso di YAMNet scarica il modello
(~40 MB) nella cache locale `~/.cache/tfhub_modules/`.

## Lezioni critiche applicate

1. **Hum check con baseline locale** (non globale). Vedi `references/lessons_learned.md`.
   La versione con baseline globale che produceva falsi positivi è esplicitamente scartata.
2. **Pre-check LUFS prima di YAMNet**. Se il file è sotto -45 LUFS, applica normalizzazione
   temporanea in memoria per evitare che il modello restituisca "Silence" al 97% (fallimento
   documentato sul file Villa Ficana da 67 minuti a -60 LUFS).

## Riferimenti

- `references/lessons_learned.md`  bug e correzioni derivate dall'esperienza Villa Ficana
- `references/taxonomies/`          bande Schafer, indici ecoacustici, vocabolario Schaefferiano
- `references/grm_profiles/`        profili di riferimento Parmegiani, Westerkamp, Ferrari, Krause
- `CHANGELOG.md`                    storico versioni

## Aggancio con l'agente compositivo

Al termine della pipeline tecnica, il CLI invoca automaticamente l'agente
`soundscape-composer-analyst` (definito in `~/.claude/agents/soundscape-composer-analyst.md`)
passandogli il summary JSON completo. L'agente produce una lettura compositiva in italiano
(osservazioni critiche, oggetti sonori Schaefferiani, potenziale drammaturgico, criticità
tecniche, gesti suggeriti) che viene integrata come sezione dedicata del PDF finale.
