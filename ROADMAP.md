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

**Riorientamento di scopo (16/04/2026, sera)**: lo scopo della skill **non e'**
identificare brani noti del repertorio. Brani noti come Presque Rien N°1
vengono usati come **gold standard** per insegnare alla skill a riconoscere
eventi sonori, descriverli con la terminologia compositiva corretta
(Schaeffer/Smalley/Chion/Schafer/Truax/Krause/Westerkamp) e produrre analisi
compositivamente pertinenti, perche' di questi brani esistono analisi
accademiche di riferimento (Pecquet, Caux, Battier, ecc.) contro cui
misurare la qualita' descrittiva. Tre conseguenze sulla pianificazione:

1. Il flag `--known-piece` (v0.5.4) resta utile ma non e' centrale.
2. Il **plausibility check CLAP** torna prioritario: "Acqua del rubinetto"
   su sciabordio onde e' un errore di riconoscimento eventi, non solo
   un'hallucination innocua. Risale da v0.9.0 a v0.7.0.
3. Le **tassonomie estese** (TARTYP completo Schaeffer, Smalley sotto-
   categorie motion/growth, Wishart utterance) sono **funzionali allo scopo**:
   piu' precisione descrittiva = analisi piu' allineata al gold standard.
   Avvicinate da v0.8.0 a v0.6.0.
4. **Nuova v0.7.1**: infrastruttura `golden_analyses/` per benchmark
   sistematico dell'output agente contro analisi accademiche di riferimento.
   Comando `soundscape benchmark <audio> --against <golden.md>`.
5. **Soundscapy/ISO 12913-3** (era v0.7.0) scivola a v0.8.0: dimensione
   perceptive interessante ma meno urgente del riconoscimento eventi.

### v0.6.0 — Narrativa per-finestra + segmentazione strutturale + tassonomie estese (18-26 h, prossima sessione Plan Mode)

Ricomposizione del nucleo descrittivo della skill in chiave compositiva.
Tre blocchi correlati che condividono lo stesso refactor di
`narrative.py`. **Driver**: il bug delle feature globali ripetute identiche
in 40+ blocchi (visibile in `audio5_report.pdf` pp. 14-21, identificato
autonomamente dall'agente in "Criticita' tecniche") rende il PDF illeggibile
nel cuore semantico. Inoltre la terminologia compositiva attuale e'
limitata a poche classi Schaeffer/Smalley quando i due autori hanno
tassonomie molto piu' ricche.

**Blocco 1 - `narrative.py` delta-based** [URGENTE]:
- Audit di `narrative.py` per isolare dove le feature globali del file
  intero vengono passate al formatter come fossero locali.
- Ricomputo per finestra di 30 s con cache (centroide, rolloff, flatness,
  ZCR, RMS, peak, top-3 PANNs locali, top-3 CLAP locali).
- Logica delta-based: prima finestra descrizione completa, finestre
  successive solo se delta significativi (centroide +/- 15%, flatness
  +/- 30%, RMS +/- 6 dB, top-3 cambia). Riduzione attesa del PDF da 10 a
  3-4 pagine di narrativa.

**Blocco 2 - `scripts/structure.py` (nuovo) - segmentazione strutturale**:
- Changepoint detection su RMS envelope + flatness + ZCR + categoria
  PANNs dominante per finestre.
- Output: lista di sezioni con confini temporali e firma caratterizzante
  (es. "00:00-03:00 quasi-silenzio notturno; 03:00-07:00 sezione
  antropofonica diurna; 07:00-10:00 transizione veicolare; 10:00-20:46
  crescendo biofonico crepuscolare").
- Sostituisce il taglio fisso 30 s con sezioni significative.

**Blocco 3 - Tassonomie compositive estese** (assorbite da v0.8.0):
- **TARTYP Schaeffer (28 classi)**: lattice tipologico/morfologico in
  `references/clap_academic_mapping_it.json` con tutte le categorie del
  *Solfege des Objets Sonores* (Schaeffer 1966, trad. UCal Press 2017).
  Sostituisce gli attuali 8 tipi schaeferiani.
- **Sotto-tassonomia Smalley motion + growth processes**: 12 sub-categorie
  (unidirectional/reciprocal/cyclic/centric/convolution + dilation/
  accumulation/dissipation/exogeny/endogeny) da Smalley *Organised Sound*
  1997. Sostituisce gli attuali turbulence/flow.
- **Categoria *utterance* (Wishart 1996)**: nuova in
  `clap_vocabulary_it.json` per gesti vocali umani e non-umani trattati
  come oggetti sonori (urlo, riso, pianto, vocalizzazione animale
  stilizzata, sussurro, lallazione).

**Blocco 4 - Timeline grafica simbolica nel PDF**:
- Rendering matplotlib stile VB2.pdf: barre orizzontali per sezione con
  icone derivate da feature dominanti (cerchio per articolati, onde per
  fruscii, frecce per glissandi/crescendo, triangoli per acuti).
- Ogni sezione ha una "firma visiva" sintetica.

**File da creare**: `scripts/structure.py`, `tests/test_structure.py`.
**File da modificare**: `scripts/narrative.py`,
`references/clap_academic_mapping_it.json` (mapping v1.2),
`references/clap_vocabulary_it.json` (utterance category),
`scripts/clap_mapping.py`, `scripts/report_pdf.py`,
`scripts/agent_payload.py`, `templates/agent_prompt.md`.

**Prerequisito**: Plan Mode con `/plan` per design dettagliato.

### v0.6.1 — Patch indici ecoacustici (3-4 h)

Driver: ricerca web 16/04/2026
(`references/external_feedback/research_2026-04-16_soundscape_texts.md`)
ha individuato il manuale operativo di Bradfer-Lawrence et al., "The Acoustic
Index User's Guide" (*Methods Ecol Evol* 2025) con 91 registrazioni di
riferimento e codice; e il caveat di Kane et al., "Limits to accurate use of
soundscapes for biodiversity" (*Nat Ecol Evol* 2023): gli indici univariati
**non predicono species richness in modo cross-dataset**, ma il *cambiamento*
di soundscape predice il *cambiamento* di community.

- **`scripts/ecoacoustic.py`**: aggiungere `FADI` (frequency-dependent ADI,
  Xu et al. 2024 in *Ecological Indicators*) come terzo indice biodiversity
  aggiuntivo a NDSI/BI. Calcolato per banda di frequenza.
- **`scripts/report_pdf.py`**: nella sezione "Indici ecoacustici"
  aggiungere caveat in corsivo: "Gli indici univariati (ACI, NDSI, H, BI,
  FADI) non predicono in modo affidabile la ricchezza di specie tra
  registrazioni eterogenee (Kane et al. 2023). Sono indicatori di *cambiamento*
  di soundscape, non di valore assoluto."
- Test su fixture corte gia' esistenti.

### v0.6.2 — Hotfix dipendenti dal feedback utente (continuo)

Traduzione di ogni nuovo `references/user_feedback/<brano>.md` in patch
concrete: prompt CLAP aggiunti/rimossi, soglie ricalibrate. Cicli da 2-4 h
ciascuno.

### v0.7.0 — Plausibility check CLAP per riconoscimento eventi (8-12 h)

**Risale di priorita'** (era v0.9.0+): nel chiarimento di scopo del
16/04/2026 sera l'utente ha precisato che la skill serve a riconoscere
**eventi sonori** (non opere) con terminologia compositiva precisa. In
quest'ottica, "Acqua del rubinetto che scorre" su sciabordio onde NON e'
un'hallucination innocua che l'agente puo' segnalare in "Evidenza
contraddittoria": e' un **errore di riconoscimento eventi** che inquina la
descrizione e si propaga al PDF e all'agente. Va filtrato a monte.

**`scripts/clap_plausibility.py` (nuovo) `mark_implausible_tags()`**:
filtro post-hoc che marca `plausibility: "low"|"medium"|"high"` sui tag in
base a consistenza con contesto tecnico:

- Prompt di categoria `musica registrata`, `sacralita sonora`,
  `composizione soundscape`, `trasformazioni elettroacustiche`,
  `performance multimediale` richiedono PANNs `Music`/`Orchestra`/`Choir`/
  `Chant` nei top-5 globali (score > 0.1) per `plausibility: high`.
  Altrimenti `low`.
- Prompt con keyword `preghiera`/`liturgia`/`cerimonia`/`processione` in
  `SACRED_KEYWORDS_IT` (nuovo in `config.py`) richiedono PANNs `Choir`/
  `Chant`/`Religious music` nei top-10 per `plausibility: high`.
  Altrimenti `low`, anche se PANNs Speech generico c'e'.
- Prompt `treno`/`ferrovia`/`stazione` richiedono PANNs `Train`/`Rail` nei
  top-10. Altrimenti degradati.
- Prompt `acqua`/`rubinetto`/`fontanella` richiedono PANNs `Water`/`Liquid`/
  `Stream` nei top-10. Altrimenti degradati (caso "Acqua del rubinetto" su
  sciabordio porto).

**Vocabolario v1.4**: 4-6 prompt per motori marittimi specifici (espansione
`mec_13-14`): "Motore diesel lento di peschereccio con scoppio irregolare",
"Scafo in legno che cigola sul molo", "Sciabordio di onde contro scafo
ormeggiato". Da' a CLAP alternative piu' precise per ridurre confusione
treno/barca e rubinetto/sciabordio alla fonte.

**Rendering PDF**: terzo livello di markup (corsivo grigio) per
`plausibility: low`, separato da `likely_hallucination` (speech-specific) e
`geo_specific` (geografico).

**Payload agente**: propagare `plausibility`, istruire a ignorare i `low`
nelle "Oggetti sonori identificati".

**Test fixture dedicata**: `tests/test_clap_plausibility.py` con casi
reali estratti da `audio5_summary.json` (acqua/preghiera/treno).

### v0.7.1 — Infrastruttura golden analyses + benchmark (6-10 h)

**Driver**: il chiarimento di scopo richiede un meccanismo sistematico per
misurare la qualita' descrittiva dell'output agente contro analisi
accademiche di riferimento di brani noti del repertorio. Senza questo
meccanismo non si puo' valutare oggettivamente se le iterazioni della
skill migliorano davvero.

**Componenti**:

- **`references/golden_analyses/` (nuovo)**: directory con analisi
  accademiche in markdown, strutturate per essere consumate dal
  benchmark. Esempio iniziale: `presque_rien_n1.md` con sintesi delle
  analisi di Pecquet, Caux, Battier (eventi datati, terminologia, modi
  d'ascolto attivati).
- **`templates/golden_analysis_schema.md` (nuovo)**: template standardizzato
  per nuove analisi gold. Sezioni obbligatorie: metadati opera (autore,
  titolo, anno, fonte registrazione), eventi sonori datati con
  timestamp + descrizione + terminologia (Schaefferiana/Smalley/Chion),
  riferimenti bibliografici.
- **`scripts/benchmark.py` (nuovo) `compare_with_golden(agent_output, golden)`**:
  diff strutturato fra eventi descritti dall'agente e quelli nel gold.
  Output: precisione (eventi descritti dall'agente che sono nel gold),
  recall (eventi del gold non descritti dall'agente), terminology overlap
  (Jaccard sui termini compositivi usati). Score aggregato 0-100.
- **Comando CLI nuovo**: `./bin/soundscape benchmark <audio.mp3>
  --against references/golden_analyses/<file.md>`. Genera report markdown
  con i tre score e le differenze concrete.
- **Bootstrap iniziale**: scrivere
  `references/golden_analyses/presque_rien_n1.md` partendo da
  `references/user_feedback/Presque_Rien_N1.md` gia' esistente, integrando
  fonti accademiche (Pecquet, Caux). 2-3 brani gold come baseline iniziale
  (es. anche un Westerkamp con analisi McCartney).

Il benchmark diventa **metrica oggettiva** per accettare/rifiutare patch
future al vocabolario CLAP, al mapping accademico, alle istruzioni
dell'agente. Sostituisce il "sembra meglio" qualitativo.

### v0.8.0 — Soundscapy + ISO 12913-3 (10-14 h, retrocesso da v0.7.0)

**Retrocesso da v0.7.0**: dimensione perceptive interessante ma meno
urgente del riconoscimento eventi (v0.7.0 nuovo) e del benchmark (v0.7.1).

Integrazione del framework ISO 12913-3:2019 con i due assi
*pleasantness/eventfulness* derivati dai PAQ (Perceived Affective Quality,
8 attributi bipolari).

- **Nuova dipendenza `soundscapy>=0.9` (Mitchell et al. 2024,
  github.com/MitchellAcoustics/Soundscapy)**: libreria Python ISO-compliant
  con circumplex pleasantness/eventfulness, modelli predittivi PAQ.
- **`scripts/perception.py` (nuovo)**: metriche psicoacustiche binaurali
  (Zwicker loudness, Aures sharpness) + predizione PAQ + posizione sul
  circumplex.
- **Sezione PDF "Percezione soundscape (ISO 12913-3)"**: scatterplot
  pleasantness/eventfulness con punto del file analizzato, tabella PAQ,
  interpretazione "vibrant/calm/chaotic/monotonous quadrant".
- **Payload agente**: nuovo campo `perception` con i due assi e i PAQ.

### v0.8.1 — Vocabolario CLAP arricchito da WavCaps + repertorio (4-6 h)

Espansione del `clap_vocabulary_it.json` da ~200 a ~280 prompt:

- **WavCaps (Mei et al. 2024, IEEE TASLP)**: 400k clip con caption
  naturali. Estrazione di pattern caption ricorrenti italianizzati.
- **Battier su GRM (Organised Sound 2007)**: prompt `acu_*` per scuola
  acusmatica francese (acousmonium, figures sonores, jeux).
- **Westerkamp scritti**: prompt `wst_*` per soundwalk narrato con
  commento riflessivo.
- **WDR Koln (Stockhausen)**: prompt `elk_*` per elektronische Musik
  (sine tone synthesis, ring modulation, impulse-derived noise band).
- **BirdNET tassonomia call/song/alarm/contact**: precisione biofonica
  oltre nome di specie.

Bump vocabolario v1.4 -> v1.5.

### v0.9.0+ — Idee successive

Da valutare dopo v0.8.x.

- **Confronto strutturale fra brani di un corpus**: analisi del comune e
  del divergente fra sezioni omologhe di brani diversi. Estensione del
  sub-comando `report` corpus.
- **Diarization speech**: separazione speaker quando `--speech` rileva
  voce con probability >= soglia. pyannote-audio o WhisperX.
- **Forced alignment**: timestamp word-level invece che segment-level
  (utile per opere con testo strutturato come Very Beautiful).
- **Flag CLI `--context <file.md>`**: l'utente fornisce biografia autore,
  contesto storico, link video. Il payload agente lo incorpora nella
  lettura compositiva. (Originariamente in v0.6.0, posticipato perche'
  meno centrale dello scopo riconoscimento eventi.)
- **Allineamento testo-musica**: quando `--speech` e' attivo, sovrapporre
  timeline VAD alle sezioni strutturali. Annotazione automatica.
- **YAMNet via tensorflow-metal su Apple Silicon**: alternativa MPS al
  classifier PANNs. Richiede `tensorflow-metal` a `requirements.txt`.
- **Auto-tagging CLAP fine-tuned su soundscape italiano**: training di
  un adapter su corpus annotato dall'utente (~100 brani con etichette
  manuali).
- **Esportazione MIDI/MusicXML** per le sezioni identificate, per
  reimpiego in DAW (Reaper) o sequencer.
- **Indice EARS** (Landy 2007): mappatura categorie skill a ontologia
  formalizzata da `ears.huma-num.fr`.

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
