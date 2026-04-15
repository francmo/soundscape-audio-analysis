# Soundscape Audio Analysis

Infrastruttura Claude Code per l'analisi tecnica e compositiva di file audio.
Progettata per soundscape composition, field recording, musica elettroacustica, didattica AFAM.

## Installazione

Il pacchetto vive dentro `~/.claude/skills/soundscape-audio-analysis/`. Per ricreare la venv da zero:

```bash
cd ~/.claude/skills/soundscape-audio-analysis
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Sistema:
- macOS o Linux
- Python 3.12
- ffmpeg + ffprobe (`brew install ffmpeg`)

## Uso rapido

```bash
# Analisi singolo file
bash ~/.claude/skills/soundscape-audio-analysis/bin/soundscape analyze mio_file.wav

# Analisi batch di una cartella
bash ~/.claude/skills/soundscape-audio-analysis/bin/soundscape analyze ~/recordings/ --output ~/reports/

# Senza classificazione semantica (più veloce)
bash ~/.claude/skills/soundscape-audio-analysis/bin/soundscape analyze file.wav --no-semantic

# Confronto con un profilo GRM specifico
bash ~/.claude/skills/soundscape-audio-analysis/bin/soundscape analyze file.wav --compare presque_rien
```

## Struttura

- `scripts/` tutti i moduli Python della pipeline
- `templates/` template ReportLab e prompt agente
- `assets/fonts/` Libre Baskerville + Source Sans Pro (licenza OFL)
- `references/` tassonomie, profili GRM, lezioni apprese
- `tests/` pytest suite, fixture sintetici, acceptance Villa Ficana
- `bin/soundscape` wrapper shell che attiva venv ed esegue il CLI

## Agente collegato

`~/.claude/agents/soundscape-composer-analyst.md`: riceve il summary JSON e produce una
lettura compositiva in italiano usando il vocabolario Schaefferiano.

## Versione

Vedi `CHANGELOG.md`.
