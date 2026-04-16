# Roadmap soundscape-audio-analysis

Documento unico per orientarsi: cosa fa la skill oggi, cosa e' pianificato,
chi fa cosa. Aggiornato a ogni release.

**Versione corrente**: 0.5.4 (16 aprile 2026)
**Test suite**: 117 passed + 2 skipped (benchmark e whisper reale gated)
**Branch**: `main`

---

## Stato corrente (v0.5.4)

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
- **Auto-tagging CLAP italiano**: 193 prompt v1.3 in 18 categorie
  (geofonia, biofonia, antropofonia *, musica, sacralita sonora, paesaggi
  italiani specifici, **paesaggi mediterranei generici** nuova in v0.5.2,
  ecc.). **v0.5.1**: filtro allucinazioni speech-related che marca con
  `likely_hallucination=True` i tag con keyword voce/parlato quando PANNs
  Speech score <= 0.10. **v0.5.2**: flag `geo_specific=True` sui tag
  italo-specifici (categoria "paesaggi italiani specifici" o keyword
  italiane nel prompt), resi in corsivo nel PDF con caption dedicata per
  evitare falsi positivi su materiale mediterraneo non italiano.
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

Priorita' riordinate dopo la rilettura completa di `audio5_report.pdf`
(16/04/2026): l'agente applica correttamente il flag `geo_specific` ed
identifica autonomamente le hallucination CLAP in "Evidenza contraddittoria"
(esempio: "CLAP propone 'acqua del rubinetto' 0.21 e 'preghiera collettiva
sussurrata' 0.21 come tag dominanti, ma il classificatore non rileva ne'
Water ne' Religious music. Queste associazioni riflettono probabilmente la
texture continua a grana fine degli insetti che CLAP confonde con flussi
d'acqua o mormorii vocali"). Questo sposta il plausibility check CLAP da
priorita' alta a nice-to-have (rinviato a v0.7.0). Emergono invece due gap
piu' urgenti: agente non riconosce Presque Rien nonostante indizi forti, e
`narrative.py` produce 10 pagine di testo ridondante (stessa frase con
centroide 3029 Hz / flatness 0.040 / onset 86 ripetuta in 40+ blocchi).

### v0.6.0 — Strumento compositivo (16-22 h, prossima sessione Plan Mode)

Trasforma la skill da "report statistico" a "strumento di analisi
compositiva" allineato al modo in cui Francesco scrive le analisi
(rif. VB2.pdf, Air Piece.pdf). **Priorita' interna**: il punto 3
(`narrative.py` delta-based) e' il piu' urgente e visibile: in
`audio5_report.pdf` occupa 10 pagine con lo stesso paragrafo ripetuto 40+
volte (centroide 3029 Hz, flatness 0.040, onset 86 identici perche'
feature globali erroneamente presentate come locali). Potrebbe valere la
pena estrarlo in una v0.5.4 intermedia se il resto di v0.6.0 richiede
troppo tempo.

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

3. **`narrative.py` delta-based** [**URGENTE**]. Prima finestra descrizione
   completa, finestre successive solo delta significativi (centroide cambia
   di +/- 15%, flatness cambia di +/- 30%, RMS cambia di +/- 6 dB, top-3
   CLAP cambia, top-3 PANNs cambia). Bug confermato in `audio5_report.pdf`:
   centroide 3029 Hz, flatness 0.040, onset 86 (2.9/s) ripetuti identici in
   40+ blocchi perche' la funzione usa feature globali del file intero
   invece che feature per finestra. Fix: audit `narrative.py` per isolare
   dove passa le globali al formatter, ricomputare su finestre locali con
   cache, poi applicare logica delta-based.

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

### v0.6.1 — Patch indici ecoacustici (3-4 h)

Driver: ricerca web 16/04/2026 (`references/external_feedback/research_2026-04-16_soundscape_texts.md`)
ha individuato il manuale operativo di Bradfer-Lawrence et al., "The Acoustic
Index User's Guide" (Methods Ecol Evol 2025) con 91 registrazioni di
riferimento e codice; e il caveat di Kane et al., "Limits to accurate use of
soundscapes for biodiversity" (Nat Ecol Evol 2023): gli indici univariati
**non predicono species richness in modo cross-dataset**, ma il *cambiamento*
di soundscape predice il *cambiamento* di community. Da integrare:

- **`scripts/ecoacoustic.py`**: aggiungere `FADI` (frequency-dependent ADI,
  Xu et al. 2024 in *Ecological Indicators*) come terzo indice biodiversity
  aggiuntivo a NDSI/BI. Calcolato per banda di frequenza, espone hot-spot
  spettrali della complessita' biofonica.
- **`scripts/report_pdf.py`**: nella sezione "Indici ecoacustici" aggiungere
  caveat in corsivo: "Gli indici ecoacustici univariati (ACI, NDSI, H, BI,
  FADI) non predicono in modo affidabile la ricchezza di specie tra
  registrazioni eterogenee (Kane et al. 2023). Sono indicatori di *cambiamento*
  di soundscape, non di valore assoluto. Confronti longitudinali sullo stesso
  sito sono piu' affidabili dei valori isolati."
- Test su fixture corte gia' esistenti.

### v0.6.2 — Hotfix dipendenti dal feedback utente (continuo)

Traduzione di ogni nuovo `references/user_feedback/<brano>.md` in patch
concrete: prompt CLAP aggiunti/rimossi, soglie ricalibrate. Cicli da 2-4 h
ciascuno.

### v0.7.0 — Soundscapy + ISO 12913-3 (10-14 h, sostituisce plausibility check)

**Rivisto rispetto alla roadmap precedente**: il plausibility check CLAP
(era v0.7.0) e' stato retrocesso a v0.9.0+ perche' l'agente gia' lo svolge
autonomamente in "Evidenza contraddittoria" (validato in
`audio5_report.pdf`). Al suo posto, integrazione di una dimensione perceptive
totalmente assente nella skill: il framework ISO 12913-3:2019 con i due
assi *pleasantness/eventfulness* derivati dai PAQ (Perceived Affective
Quality, 8 attributi bipolari).

**Componenti**:

- **Nuova dipendenza `soundscapy>=0.9` (Mitchell et al. 2024,
  github.com/MitchellAcoustics/Soundscapy)**: libreria Python ISO-compliant
  con circumplex pleasantness/eventfulness, modelli predittivi PAQ da feature
  psicoacustiche (loudness, sharpness, roughness, fluctuation strength).
- **`scripts/perception.py` (nuovo) `iso12913_summary(waveform, sr)`**:
  calcolo metriche psicoacustiche binaurali (Zwicker loudness, Aures
  sharpness) + predizione PAQ + posizione sul circumplex.
- **Sezione PDF "Percezione soundscape (ISO 12913-3)"**: scatterplot
  pleasantness/eventfulness con punto del file analizzato, tabella PAQ
  values, interpretazione "vibrant/calm/chaotic/monotonous quadrant".
- **Payload agente**: nuovo campo `perception` con i due assi e i PAQ. L'agente
  puo' citare "il file e' percepito come *eventful* (0.7) e *moderatamente
  pleasant* (0.4): tipico di soundscape urbano vibrante".
- **Mapping a tassonomie esistenti**: pleasant=hi-fi, chaotic=lo-fi correlazioni
  da validare empiricamente sul corpus utente.

**Riferimenti**:
- ISO/TS 12913-2:2018 (Method for data collection)
- ISO/TS 12913-3:2019 (Method for data analysis)
- Mitchell A. et al., "Soundscapy", *INTER-NOISE 2024 Proceedings*

### v0.7.1 — Vocabolario CLAP arricchito da WavCaps + repertorio (4-6 h)

Espansione del `clap_vocabulary_it.json` da 193 a ~250 prompt usando come
fonti:

- **WavCaps (Mei et al. 2024, IEEE TASLP)**: 400k clip audio con caption
  naturali da AudioSet/BBC SFX/FreeSound/SoundBible. Estrazione di pattern
  caption ricorrenti italianizzati, focus su scene non ancora coperte
  (industriale, marittimo, montano, deserto).
- **Battier su GRM (Organised Sound 2007)**: prompt `acu_*` per scuola
  acusmatica francese (acousmonium, figures sonores, jeux, ecoute reduite).
- **Westerkamp scritti (hildegardwesterkamp.ca)**: prompt `wst_*` per
  soundwalk narrato con commento riflessivo.
- **WDR Köln archivi (Stockhausen-Verlag)**: prompt `elk_*` per elektronische
  Musik (sine tone synthesis, ring modulation cathedral, impulse-derived
  noise band).
- **BirdNET tassonomia call/song/alarm/contact (Cornell)**: precisione
  biofonica oltre nome di specie (es. "Allocco di richiamo territoriale"
  vs "Allocco di canto crepuscolare").

Bump vocabolario v1.3 → v1.4. Mapping accademico esteso di conseguenza.

### v0.8.0 — Strumento compositivo step 2: TARTYP completo + Smalley esteso (12-18 h)

Refactor del mapping accademico per supportare le tassonomie complete:

- **TARTYP Schaeffer (28 classi)**: lattice tipologico/morfologico in
  `clap_academic_mapping_it.json` con tutte le categorie del
  *Solfège des Objets Sonores* (Schaeffer 1966, trad. UCal Press 2017).
- **Sotto-tassonomia Smalley motion + growth processes**: 12 sub-categorie
  (unidirectional/reciprocal/cyclic/centric/convolution + dilation/
  accumulation/dissipation, etc.) da Organised Sound 1997.
- **Categoria *utterance* (Wishart)**: nuova in `clap_vocabulary_it.json`
  per gesti vocali umani e non-umani trattati come oggetti sonori (urlo,
  riso, pianto, vocalizzazione animale stilizzata).
- **Indice EARS** (Landy 2007): mappatura categorie skill a ontologia
  formalizzata da `ears.huma-num.fr`.

### v0.9.0+ — Idee successive

Da valutare dopo v0.8.0.

- **Plausibility check CLAP** (rinviato da v0.7.0): vedi razionale sopra,
  l'agente gia' lo fa. Implementare solo se emergono casi in cui l'agente
  fallisce sistematicamente.
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

- **v0.5.4** (16/04/2026): flag CLI `--known-piece` per attribuzione
  utente esplicita (bypassa l'auto-attribuzione del modello quando
  l'utente conosce gia' l'opera). Plus aumento AGENT_TIMEOUT_S 120 -> 300
  s per sostenere il prompt v0.5.3 esteso. Feedback source: audio6
  rilanciato con v0.5.3 (opus propone Ferrari N°2 invece di N°1 per
  knowledge gap).
- **v0.5.3** (16/04/2026): hotfix agente (riconoscimento brani noti da
  suggerimento a passo obbligatorio, nuovo campo `signature` nel payload).
  Feedback source: rilettura di audio5_report.pdf (Presque Rien N°1
  rilanciato con v0.5.2).
- **v0.5.2** (15/04/2026): hotfix mediterraneo (vocabolario CLAP v1.3 con
  categoria "paesaggi mediterranei generici", flag `geo_specific` sui tag
  italo-specifici, istruzioni agente per riconoscimento brani noti).
  Feedback source: Presque Rien N°1 di Luc Ferrari.
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
