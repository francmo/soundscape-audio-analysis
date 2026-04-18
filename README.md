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

## Licenza

Questo progetto usa un **dual licensing**:

- **Codice** (`scripts/`, `tests/`, `bin/`, `assets/`, `pyproject.toml`,
  `requirements.txt`): Apache License 2.0. Vedi `LICENSE`.
- **Materiale analitico e documentale** (vocabolari CLAP,
  tassonomie accademiche, template, feedback su brani di riferimento,
  ROADMAP, CHANGELOG, SKILL.md): Creative Commons Attribution 4.0
  International. Vedi `LICENSE-CC-BY-4.0`.

Vedi `NOTICE` per attribuzioni di dipendenze di terze parti (librosa,
PANNs CNN14 di Kong et al. 2020, LAION-CLAP di Wu et al. 2023, font
Libre Baskerville e Source Sans Pro sotto SIL OFL 1.1).

## Come citare

Se utilizzi questa skill in un lavoro accademico, in un report, in
un workshop o in un progetto derivato, cita come segue (formato BibTeX):

```bibtex
@software{mariano2026soundscape,
  author = {Mariano, Francesco},
  title  = {Soundscape Audio Analysis: una skill Claude Code per
            l'analisi tecnica e compositiva di soundscape e musica
            elettroacustica},
  year   = {2026},
  url    = {https://github.com/francmo/soundscape-audio-analysis},
  note   = {Codice Apache 2.0, vocabolari e tassonomie CC BY 4.0}
}
```

In forma discorsiva: "Analisi condotta con Soundscape Audio Analysis
(Mariano, 2026), disponibile su GitHub."
