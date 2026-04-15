# Roadmap soundscape-audio-analysis

Documento unico per orientarsi: cosa fa la skill oggi, cosa e' pianificato,
chi fa cosa. Aggiornato a ogni release.

**Versione corrente**: 0.5.1 (15 aprile 2026)
**Test suite**: 113 passed + 2 skipped (benchmark e whisper reale gated)
**Branch**: `main`

---

## Stato corrente (v0.5.1)

### Capabilities attive

- **Analisi tecnica**: livelli (peak, RMS, crest, DR, noise floor), LUFS EBU
  R128, true peak, clipping, DC offset.
- **Hum check con baseline locale**: bande 30-45 e 70-95 Hz, evita falsi
  positivi su sorgenti tonali. **v0.5.1**: arricchito con `interpretation_hint`
  che marca i picchi come "probabile componente armonica strumentale" quando
  flatness < 0.05 e top-1 PANNs e' uno strumento musicale (50 label
  AudioSet).
- **Analisi spettrale**: bande Schafer (7), centroide, rolloff, flatness,
  ZCR, onset density, hi-fi/lo-fi score.
- **Indici ecoacustici**: ACI, NDSI, H, BI (default basic). ADI/AEI in
  modalita' extended.
- **Classificazione semantica PANNs CNN14** (default): 527 classi AudioSet,
  pre-check LUFS per evitare bug "97% Silence" su file molto bassi.
- **Auto-tagging CLAP italiano**: 172 prompt v1.2 in 17 categorie
  (geofonia, biofonia, antropofonia *, musica, sacralita sonora, paesaggi
  italiani specifici, ecc.). **v0.5.1**: filtro allucinazioni speech-related
  che marca con `likely_hallucination=True` i tag con keyword voce/parlato
  quando PANNs Speech score <= 0.10.
- **Mapping accademico** (v0.4.0): hint aggregati su Schafer (keynote/signal/
  soundmark), Truax (listening modes), Krause (biofonia/antropofonia/
  geofonia), Schaeffer (tipologia), Smalley (motion processes), Chion
  (causale/semantico/ridotto), Westerkamp (soundwalk relevance).
- **Trascrizione dialoghi opt-in** (v0.5.0): flag `--speech` attiva
  faster-whisper large-v3 + Silero VAD pre-filtro + traduzione italiana via
  `claude -p --model claude-haiku-4-5`. Suggerimento stderr giallo se PANNs
  rileva Speech dominante > 25% dei frame senza il flag.
- **Multicanale**: rilevamento layout (mono/stereo/quad/5.1/7.1/5.1.4/
  7.1.4), per-channel levels, downmix.
- **Narrativa segmentata**: prosa italiana finestrata 30s.
- **Lettura compositiva agente**: subprocess `claude -p --agents
  soundscape-composer-analyst`. **v0.5.1**: telemetria stderr per diagnosi
  failure mode (returncode, stderr completo, n. tentativi, durata).
- **Report PDF**: copertina, metadati, livelli, diagnosi (con hum hint),
  spettrale, ecoacustica, semantica, CLAP (con tag flagged in corsivo +
  academic_hints), dialoghi trascritti (se `--speech`), multicanale,
  narrativa, lettura compositiva, colofone.
- **Report corpus**: sub-comando `soundscape report` per analisi
  comparativa multi-file con grafici (loudness bar, dynamic range, bande
  Schafer, indici ecoacustici, similarita' CLAP).

### File chiave per orientarsi

| Cosa | Dove |
|------|------|
| Pipeline CLI | `scripts/cli.py::_analyze_single` (10 step numerati) |
| Costanti centrali | `scripts/config.py` |
| Stringhe italiane | `scripts/locale_it.py` |
| Hum check | `scripts/hum.py` |
| Spettrale | `scripts/spectral.py` |
| Tecnico (LUFS) | `scripts/technical.py` |
| Ecoacustico | `scripts/ecoacoustic.py` |
| PANNs | `scripts/semantic.py` |
| CLAP | `scripts/semantic_clap.py` |
| Mapping accademico CLAP | `scripts/clap_mapping.py` + `references/clap_academic_mapping_it.json` |
| Vocabolario CLAP | `references/clap_vocabulary_it.json` |
| Speech | `scripts/speech.py` |
| Narrativa segmentata | `scripts/narrative.py` |
| Agente compositivo | `scripts/agent_bridge.py`, `templates/agent_prompt.md`, `~/.claude/agents/soundscape-composer-analyst.md` |
| PDF | `scripts/report_pdf.py` |
| Tassonomie di riferimento | `references/taxonomies/` |
| Profili GRM | `references/grm_profiles/` |
| Feedback utente | `references/user_feedback/` |

---

## Pianificato (priorita' decrescente)

### v0.6.0 — Strumento compositivo (16-22 h, prossima sessione Plan Mode)

Trasforma la skill da "report statistico" a "strumento di analisi
compositiva" allineato al modo in cui Francesco scrive le analisi
(rif. VB2.pdf, Air Piece.pdf).

**Cinque feature nuove correlate**:

1. **`scripts/structure.py` (nuovo) - segmentazione strutturale**.
   Changepoint detection su RMS envelope + flatness + ZCR + categoria PANNs
   dominante per finestre. Output: lista di sezioni con confini temporali
   e firma caratterizzante. Risolve il gap "skill statistica vs analisi
   per sezioni" osservato comparando con le tabelle manuali in VB2.pdf.

2. **Timeline grafica simbolica nel PDF**. Rendering matplotlib in stile
   VB2.pdf: barre orizzontali per sezione con icone derivate da feature
   dominanti (cerchio per articolati, onde per fruscii, frecce per
   glissandi/crescendo, triangoli per acuti). Ogni sezione ha una "firma
   visiva" sintetica.

3. **`narrative.py` delta-based**. Prima finestra descrizione completa,
   finestre successive solo delta significativi (centroide cambia di +/-
   15%, flatness cambia di +/- 30%, etc.). Risolve la verbosita'
   identificata da Gemini ("Spettralmente il centroide si colloca a 1485
   Hz" ripetuto in ogni segmento).

4. **Flag CLI `--context <file.md>`**. L'utente fornisce biografia autore,
   contesto storico, link video, frasi chiave. Il payload agente lo
   incorpora nella lettura compositiva. Colma il gap "nessun contesto
   extra-audio" rispetto alle analisi manuali.

5. **Allineamento testo-musica**. Quando `--speech` e' attivo, sovrapporre
   timeline VAD alle sezioni strutturali. Annotazione automatica "sezione
   X coincide con parlato in lingua Y", "frase 'I remember everything'
   coincide con momento di massima intensita' a 5:40-6:32".

**File da creare**: `scripts/structure.py`, `tests/test_structure.py`,
estensione di `report_pdf.py` per timeline grafica.
**File da modificare**: `scripts/narrative.py`, `scripts/cli.py`,
`scripts/agent_payload.py`, `templates/agent_prompt.md`,
`references/external_context_schema.md` (nuovo).

**Prerequisito**: aprire Plan Mode con `/plan` per design dettagliato.

### v0.5.2 — Hotfix dipendenti dal feedback utente

Una volta che `references/user_feedback/VB_Flauto.md` (e altri brani) e'
compilato, traduzione delle correzioni in:

- Prompt CLAP rimossi/aggiunti in `clap_vocabulary_it.json` v1.3.
- Override del mapping accademico per casi specifici corretti dall'utente.
- Ricalibrazione soglie `HUM_CONTEXT_*`, `HALLUCINATION_*`,
  `SPEECH_SUGGEST_*`.
- Nuove parole chiave nel filtro hallucination.
- Glossario lessico CLAP -> terminologia musicale corretta (per
  arricchimento PDF e prompt agente).

Tempo: 2-4 h dopo ogni ciclo di feedback.

### v0.7.0+ — Idee successive

Da valutare quando v0.6.0 e' rilasciata e stabile.

- **Confronto strutturale fra brani di un corpus**: analisi del comune
  e del divergente fra sezioni omologhe di brani diversi. Estensione del
  sub-comando `report` corpus.
- **Diarization speech**: separazione speaker quando `--speech` rileva
  voce con probability >= soglia. pyannote-audio o WhisperX.
- **Forced alignment**: timestamp word-level invece che segment-level
  (utile per opere con testo strutturato come Very Beautiful).
- **YAMNet via tensorflow-metal su Apple Silicon**: alternativa MPS al
  classifier PANNs. Richiede aggiungere `tensorflow-metal` a
  `requirements.txt` e test dedicati.
- **Auto-tagging CLAP fine-tuned su soundscape italiano**: training di
  un adapter su corpus annotato dall'utente (servirebbero ~100 brani con
  etichette manuali).
- **Esportazione MIDI/MusicXML** per le sezioni identificate, per
  reimpiego in DAW (Reaper) o sequencer.

---

## Loop di feedback utente

Sistema di miglioramento iterativo basato sulle annotazioni del compositore
(documentato in `references/user_feedback/README.md`):

1. Skill produce report PDF su un brano.
2. Utente apre `references/user_feedback/TEMPLATE.md`, copia in
   `<nome_brano>.md`, compila almeno la sezione 9 (Note libere).
3. Le correzioni vengono tradotte in patch concrete (vocabolario CLAP,
   mapping accademico, soglie filtri).
4. Release v0.X.Y patch dipendente dal feedback.
5. Si ripete su brani diversi per coprire casi limite.

Stato attuale: `VB_Flauto.md` istanza pre-popolata in attesa di
completamento.

---

## Storia release (rimanda a `CHANGELOG.md` per dettagli)

- **v0.5.1** (15/04/2026): hotfix interpretativi (hum contestuale,
  allucinazioni CLAP, diagnostica agent).
- **v0.5.0** (15/04/2026): trascrizione dialoghi opt-in via
  faster-whisper + Silero VAD + traduzione `claude -p`.
- **v0.4.1** (15/04/2026): hotfix off-by-one resample multicanale.
- **v0.4.0** (15/04/2026): espansione vocabolario CLAP (102 -> 172) +
  mapping accademico Schafer/Truax/Krause/Schaeffer/Smalley/Chion/
  Westerkamp.
- **v0.3.3** (15/04/2026): uniformazione italiano nel PDF e nei grafici.
- **v0.3.2** (15/04/2026): abilitazione MPS per PANNs CNN14 su Apple
  Silicon.
- **v0.3.1** e precedenti: vedi CHANGELOG.

---

## Convenzioni

- Italiano corretto in PDF, log utente, commenti d'uso, CHANGELOG.
- Niente em dash, accenti italiani sempre (è, à, ò, ù, ì, é, perché,
  poiché, etc.).
- Acronimi tecnici internazionali (LUFS, RMS, STFT, PANNs, CLAP, MPS,
  VAD) restano in inglese.
- Versioning: minor per nuove feature pubbliche, patch per fix.
  Pre-bump verifica con grep `vX.Y.Z` per catturare tutti i callsite.
- Test prima del commit (suite completa zero regressioni).
