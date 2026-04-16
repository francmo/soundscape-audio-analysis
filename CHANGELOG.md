# Changelog

## [0.5.3] - 2026-04-16

Hotfix agente: riconoscimento di brani noti del repertorio come passo
obbligatorio prima dell'analisi compositiva. Driver: rilettura completa di
`audio5_report.pdf` (Presque Rien N°1 di Luc Ferrari rilanciato con v0.5.2)
ha mostrato che l'agente produce una lettura compositiva di qualita' alta
ma tratta il materiale come "registrazione anonima", nonostante 20 minuti
di porto peschereccio mediterraneo e arco crepuscolare siano firma
riconoscibilissima dell'opera. L'istruzione v0.5.2 "Identificazione
preliminare" era formulata come suggerimento opzionale e l'agente la
saltava. Due interventi non breaking.

### Added

- **`signature` nel payload agente**: campo di alto livello in
  `scripts/agent_payload.py::_build_signature()` che aggrega durata MM:SS,
  dynamic range, flatness media, Krause dominante, top-5 PANNs frame
  dominanti, top-5 CLAP prompts, presenza di parlato. Non inventa
  etichette: fornisce all'agente i dati grezzi aggregati per facilitare
  il ragionamento di attribuzione. Il riconoscimento del brano resta
  responsabilita' del ragionamento LLM.

### Changed

- **Identificazione preliminare da suggerimento a passo obbligatorio**:
  in `templates/agent_prompt.md` e
  `~/.claude/agents/soundscape-composer-analyst.md` il paragrafo e' stato
  riscritto in tre step espliciti: (1) leggi `signature`, (2) formula 2-3
  ipotesi in formato `[Autore, Titolo, anno, confidence, motivazione]`,
  (3) decidi: se almeno una ipotesi raggiunge confidence medium o high,
  apri "Osservazioni critiche" con attribuzione esplicita che cambia il
  senso di "Gesti compositivi suggeriti" (da intervento post-produzione a
  lettura analitica dell'opera compiuta); se tutte low, scrivi frase
  esatta "Nessuna attribuzione plausibile dai dati disponibili: il
  materiale e' trattato come registrazione anonima" prima di procedere.
  Cosi' l'agente non puo' piu' saltare il passo: o attribuisce o
  dichiara esplicitamente di non poter attribuire.

### Fixed

- **Refuso label "Hint accademici aggregati"** in `scripts/report_pdf.py`:
  rimosso versioning "(v0.5.1)" fuori aggiornamento. Versioning ora solo
  nel footer/colofone.

### Internal

- Bump 0.5.2 → 0.5.3 in `scripts/__init__.py`, `scripts/cli.py`
  (3 callsite), `scripts/report_cmd.py`, `scripts/report_pdf.py`
  (3 stringhe user-facing), `pyproject.toml`.

### Feedback sources

- `references/user_feedback/Presque_Rien_N1.md`: la seconda osservazione
  dell'utente sul report audio5 ha mostrato l'efficacia parziale della
  v0.5.2 (flag `geo_specific` e prompt mediterranei generici funzionano,
  agente li applica correttamente) e il gap residuo del riconoscimento
  brani noti. L'agente GIA' identifica autonomamente le hallucination CLAP
  in "Evidenza contraddittoria": il plausibility check CLAP automatico
  pianificato per v0.5.3 e' quindi stato rinviato a v0.7.0 come
  nice-to-have (documentato in `ROADMAP.md`).

## [0.5.2] - 2026-04-15

Hotfix mirato al feedback raccolto analizzando *Presque Rien N°1* di Luc
Ferrari (1967-70, Vela Luka, Croazia). La skill ha prodotto falsi positivi
geografici ("borgo medievale italiano", "cicale del sud Italia",
"conservatorio italiano", "preghiera collettiva sussurrata in chiesa") perche'
il vocabolario CLAP era italo-centrico e mancava di prompt mediterranei
generici. Inoltre l'agente compositivo non aveva istruzioni per riconoscere
brani noti del repertorio prima di interpretare, producendo analisi "da
materiale grezzo" su un'opera canonica. Tre interventi non breaking.

### Added

- **Vocabolario CLAP v1.3**: aggiunta categoria nuova `paesaggi mediterranei
  generici` (10 prompt da `pmd_01` a `pmd_10`: porto peschereccio, mercato
  pesce mediterraneo, voci di bambini che giocano in piazza, sciabordio
  barche, gabbiani costieri, cicale mediterranee, brezza marina, rane
  marine, ecc.) piu' 11 prompt aggiuntivi in altre categorie
  (`bio_16-18`, `urb_11-13`, `mec_13-14`, `geox_11-13`). Totale 193 prompt
  in 18 categorie (+21 rispetto alla v1.2).
- **Mapping accademico v1.1**: `clap_academic_mapping_it.json` con
  `vocabulary_ref.min_version` allineato a "1.3", `category_defaults` per
  "paesaggi mediterranei generici" (`krause: mista`,
  `schafer_role: soundmark`, `schafer_fidelity: misto`, `chion: misto`,
  `truax: readiness`, `westerkamp_soundwalk_relevance: true`) e 11
  override prompt specifici.
- **Flag `geo_specific` sui tag CLAP**:
  `scripts/clap_mapping.py::mark_geo_specific_tags(top_global)` marca con
  `geo_specific=True` i tag che appartengono alla categoria "paesaggi
  italiani specifici" o contengono keyword italo-specifiche (borgo
  medievale, conservatorio italiano, AFAM, campane di chiesa, dialetto
  locale, osteria pomeridiana, ecc.) nel set `LOCATION_SPECIFIC_KEYWORDS_IT`
  di `config.py`. Separato da `likely_hallucination`: non hallucination
  certa ma "potenziale fuori contesto geografico". Il PDF renderizza
  questi tag in corsivo con caption dedicata.

### Changed

- **Prompt agente `soundscape-composer-analyst`**: aggiunte istruzioni
  esplicite per (a) identificare eventuale brano noto del repertorio prima
  di scrivere l'analisi (cambia il senso di "Gesti compositivi suggeriti"
  da interventi post-produzione a riflessioni analitiche sull'opera);
  (b) trattare con cautela i tag `geo_specific=True` su materiale non
  italiano (riconosciuto da metadati, lingua speech, identificazione del
  brano). Aggiornato sia `templates/agent_prompt.md` sia
  `~/.claude/agents/soundscape-composer-analyst.md`.
- **Rendering PDF sezione CLAP**: i tag con `geo_specific=True` e quelli
  con `likely_hallucination=True` sono entrambi renderizzati in corsivo,
  con caption separate che spiegano il flag specifico.

### Fixed

- Falso positivo CLAP "Vicolo di borgo medievale al tramonto" su porto
  peschereccio croato: ora flaggato `geo_specific=True` e reso in corsivo
  con hint per l'agente di preferire la versione geo-generica quando il
  materiale e' identificato come non italiano.
- Manca di riconoscimento brano noto nell'output agente: ora un paragrafo
  dedicato istruisce a valutare file name, metadati, durata, scena
  coerente con opera canonica prima di scrivere l'analisi. Cambia il
  senso stesso di "Gesti compositivi" (da intervento compositivo a lettura
  analitica dell'opera gia' in forma).

### Internal

- Test nuovi in `tests/test_clap_academic_mapping.py`
  (`test_paesaggi_mediterranei_generici_category_exists`,
  `test_mark_geo_specific_flags_italian_category`,
  `test_mark_geo_specific_flags_keyword_in_prompt`,
  `test_mark_geo_specific_no_flag_on_generic`) piu' aggiornamenti in
  `tests/test_clap_tagging.py` per la nuova versione vocabolario.
- Bump versione 0.5.1 → 0.5.2 in `scripts/__init__.py`, `scripts/cli.py`
  (3 callsite), `scripts/report_cmd.py`, `scripts/report_pdf.py`
  (3 stringhe user-facing), `pyproject.toml`.

### Feedback sources

- `references/user_feedback/Presque_Rien_N1.md`: analisi di 20m46 di
  field recording mediterraneo (porto peschereccio a Vela Luka, Korcula)
  comparata con letteratura accademica su Luc Ferrari. Ha identificato 12
  prompt mancanti, 3 hallucination concrete (tra cui "preghiera collettiva
  sussurrata in chiesa" flaggata correttamente dalla v0.5.1) e il gap
  strutturale del riconoscimento brani.

## [0.5.1] - 2026-04-15

Hotfix interpretativi su tre fronti emersi dal confronto fra l'output della
skill su VB_Flauto.mp3 (brano del catalogo) e le analisi manuali fatte
dall'utente (VB2.pdf, Air Piece.pdf), e dalla critica di Gemini sui report
SheLiesDown / Washing Machine. Tre interventi mirati senza nuove dipendenze
ne breaking change. Il modulo `narrative.py` (descrizione delta-based) e
gli altri miglioramenti strutturali sono rimandati alla v0.6.0.

### Fix

- **Hum check contestualizzato su materiale musicale tonale**:
  `scripts/hum.py::interpret_in_context(hum_res, spectral, classifier)`
  arricchisce il dict hum con `interpretation_hint`. Quando flatness < 0.05
  e il top-1 PANNs e' uno strumento musicale (set
  `MUSICAL_INSTRUMENT_LABELS` in config con ~50 label AudioSet) con score >
  0.5, marca i picchi come "probabile componente armonica strumentale, non
  rumore di rete". Il verdict numerico resta invariato (dato grezzo
  sempre disponibile), il PDF mostra il caveat in corsivo. Caso colto: il
  picco a 150 Hz con verdict "presente" sul flauto solista di Very
  Beautiful era un falso positivo, ora correttamente contestualizzato.

- **Filtro allucinazioni CLAP speech-related**:
  `scripts/clap_mapping.py::mark_speech_hallucinations(top_global,
  classifier)` marca con `likely_hallucination=True` i tag CLAP che
  contengono keyword di voce/parlato/canto (~30 termini in
  `SPEECH_KEYWORDS_IT`) quando PANNs Speech score <= 0.10 e i frame
  dominanti Speech <= 5%. I tag NON vengono rimossi (l'utente vede
  comunque il match) ma resi in corsivo nel PDF con nota "basso supporto
  empirico". Caso colto da Gemini: "Discussione di vicini dalle finestre"
  su drone ambient privo di parlato.

- **Diagnostica arricchita di `agent_bridge.py`**: telemetria su stderr
  dei tentativi di invocazione `claude -p --agents
  soundscape-composer-analyst` con dimensione prompt in byte, returncode,
  stderr completo (primi 300 char), durata, n. tentativi. Il dict
  ritornato include `prompt_size_bytes`, `attempts`, `last_returncode`,
  `last_stderr_excerpt`, `elapsed_s`. Distinzione esplicita fra "output
  vuoto con returncode 0" e "returncode != 0". Il bug "lettura
  compositiva non generata" osservato da Gemini sui report
  SheLiesDown/Washing Machine ora produce informazione utile per
  diagnosi successiva (causa esatta visibile sia in stderr sia nel
  summary JSON).

### Aggiunto

- `scripts/config.py`: nuove costanti `HUM_CONTEXT_FLATNESS_MAX`,
  `HUM_CONTEXT_CLASSIFIER_SCORE_MIN`, `MUSICAL_INSTRUMENT_LABELS`,
  `HALLUCINATION_SPEECH_SCORE_MAX`, `HALLUCINATION_SPEECH_DOMINANT_PCT_MAX`,
  `SPEECH_KEYWORDS_IT`.

- `tests/test_hum.py`: 5 test su `interpret_in_context` (caso flauto,
  caso ambientale, all-trascurabile, score basso, dati mancanti).

- `tests/test_clap_academic_mapping.py`: 3 test su
  `mark_speech_hallucinations` (drone con CLAP voce, intervista con
  Speech alto, classifier mancante).

### Modificato

- `scripts/cli.py::_analyze_single`: chiama
  `hum.interpret_in_context()` dopo PANNs e
  `clap_mapping.mark_speech_hallucinations()` dopo CLAP per arricchire i
  dict prima della scrittura del summary.

- `scripts/report_pdf.py::_build_hum_block`: paragrafo in corsivo con
  l'`interpretation_hint` quando `likely_musical_harmonic=True`.
- `scripts/report_pdf.py::_build_clap_block`: tag flagged in corsivo +
  caption finale con il conteggio degli N tag a basso supporto empirico.

- Bump versione 0.5.0 → 0.5.1 in `scripts/__init__.py`, `scripts/cli.py`
  (tre callsite), `scripts/report_cmd.py`, `scripts/report_pdf.py` (tre
  stringhe user-facing), `pyproject.toml`.

### Test suite

- 113 passed + 2 skipped (10 nuovi: 5 hum context, 3 hallucinations CLAP,
  +2 da test esistenti aggiornati). Zero regressioni.

### Rimandato a v0.6.0

- Modulo `structure.py` per segmentazione strutturale automatica
  (changepoint detection su RMS/flatness/ZCR/PANNs dominante).
- Timeline grafica simbolica nel PDF in stile VB2.
- `narrative.py` delta-based.
- Flag `--context <file.md>` per contesto utente.
- Allineamento testo-musica via Speech timeline.


## [0.5.0] - 2026-04-15

Trascrizione automatica dei dialoghi opt-in via flag `--speech`. Pipeline
nuova: Silero VAD standalone come pre-filtro (salta Whisper se meno di 2 s
di parlato totale, risparmia ~1.2 GB RAM su file non vocali),
faster-whisper large-v3 con compute_type int8 su CPU (CTranslate2 non
supporta MPS; le ottimizzazioni NEON SIMD di Apple Silicon producono ~15x
realtime), traduzione italiana automatica via subprocess `claude -p
--model claude-haiku-4-5` quando la lingua rilevata non e' italiana.
Suggerimento automatico a stderr in giallo quando PANNs rileva Speech
dominante nei frame ma l'utente non ha passato `--speech`: metrica
`top_dominant_frames.pct > 25%` (semanticamente piu' onesta di una
confidence media). Sezione PDF "Dialoghi trascritti" con top-10 segmenti,
trascritto inline se corto o riferimento a `.txt` companion se lungo.
Payload agente arricchito con campo speech (transcript_it capped 3000
char, segments top-15) per permettere all'agente di valutare la
prevalenza parlato e citare contenuti verbali pertinenti.

### Aggiunto
- `scripts/speech.py`: modulo autonomo con `SpeechResult` dataclass,
  `SpeechTranscriber` singleton lazy-loaded di faster-whisper,
  `speech_summary` entry point con pre-filtro Silero VAD e fallback
  skipped_reason='insufficient_speech' quando non vale la pena caricare
  Whisper, `translate_transcript` con chunking sopra 8000 char (size
  6000, overlap 500) via subprocess claude -p --model Haiku,
  `check_speech_suggestion` helper per la logica stderr.
- `scripts/config.py`: costanti `WHISPER_*`, `SILERO_VAD_*`,
  `SPEECH_SUGGEST_DOMINANT_PCT`, `TRANSLATION_*`, `TRANSCRIPT_PDF_MAX_CHARS`.
- `tests/test_speech.py`: 15 test (disabled, empty waveform, VAD-skip,
  translation noop/fallback/chunking/short/timeout, 5 sul helper
  suggestion, 2 sul payload agente, 1 whisper reale skipped).
- `tests/test_report_pdf.py`: 3 test nuovi per `_build_speech_block`
  (empty, accenti italiani, long transcript usa companion).
- Sezione PDF "Dialoghi trascritti" via `_build_speech_block` in
  `scripts/report_pdf.py`: header con modello/device/compute_type,
  lingua rilevata con probability, durata parlato/totale con pct,
  warning multilingua se probability < 0.85, tabella top-10 segmenti,
  trascritto inline se < `TRANSCRIPT_PDF_MAX_CHARS` (2000 char) o
  riferimento ai file `.txt` companion altrimenti. Traduzione italiana
  integrale se lingua != it. Note su translation_fallback se claude
  non in PATH.
- Flag CLI `--speech` in `scripts/cli.py::analyze_cmd` (opt-in,
  default False). Step pipeline rinumerato da [N/9] a [N/10] per
  includere [8/10] Trascrizione dialoghi.
- Export `.txt` companion accanto al PDF: `<base>_transcript.txt` con
  il testo originale, `<base>_transcript_it.txt` con la traduzione
  italiana quando lingua != it.
- Suggerimento stderr giallo a fine `analyze_cmd` per file con Speech
  dominante ma senza `--speech`: "[soundscape] <file>: PANNs rileva
  Speech dominante nel X% dei frame. Per trascrizione: rilancia con
  --speech".
- Campo `speech` nel payload agente con `transcript_it` capped a 3000
  char e `segments[:15]`.
- Paragrafo "Come usare speech (v0.5.0)" in `templates/agent_prompt.md`
  con istruzioni operative: valuta prevalenza parlato
  (`duration_speech_s / duration_total_s > 0.5` → segnala in
  Osservazioni critiche), cita contenuti verbali solo se pertinenti e
  max una citazione per sezione, gestione lingua straniera e traduzione
  fallback.
- `~/.claude/agents/soundscape-composer-analyst.md` (agent definition
  globale fuori dal repo) aggiornato con menzione del campo speech.

### Modificato
- `requirements.txt`: nuove dipendenze `faster-whisper>=1.0,<2` e
  `silero-vad>=5.0,<6`. Transitive: ctranslate2, onnxruntime, av.
- `scripts/locale_it.py::INTESTAZIONI`: nuova chiave
  `dialoghi_trascritti: "Dialoghi trascritti"` per il titolo sezione PDF.
- Bump versione 0.4.1 → 0.5.0 in `scripts/__init__.py`, `scripts/cli.py`
  (tre callsite), `scripts/report_cmd.py`, `scripts/report_pdf.py` (tre
  stringhe user-facing), `pyproject.toml`.

### Note tecniche
- **CTranslate2 non supporta MPS**: faster-whisper gira su CPU con
  compute_type int8. Le ottimizzazioni NEON di Apple Silicon compensano
  l'assenza di accelerazione Metal: ~15x realtime su large-v3.
- **Silero VAD come pre-filtro**: evita di caricare Whisper (~1.2 GB
  RAM + ~3 GB download al primo run) per audio con meno di
  `SILERO_VAD_MIN_TOTAL_SPEECH_S = 2.0` secondi di parlato. Su file
  soundscape tipici (Villa Ficana et al.) Whisper non viene mai
  caricato.
- **Traduzione via claude -p Haiku**: modello leggero per velocita',
  pattern mutuato da `report_synthesizer::invoke_corpus_synthesizer`
  (stdin + `--model`). Chunking automatico sopra 8000 char con overlap
  500 per continuita' stilistica.
- **Singleton Whisper/VAD**: module-level, condivisi fra file in loop
  corpus per evitare reload ~3 GB per ogni file.

### Test suite
- 105 passed + 2 skipped (benchmark PANNs gated da
  `SOUNDSCAPE_BENCHMARK=1`, whisper_real gated da fixture
  `speech_italian.wav` non committata).


## [0.4.1] - 2026-04-15

Hotfix: risolto off-by-one nella pre-allocazione del resample multicanale
in `scripts/io_loader.py::load_audio_multichannel` che scatenava
`ValueError: could not broadcast input array from shape (N,) into shape
(N-1,)` su file stereo lunghi (es. WAV 44100 Hz risampleato a 48000 Hz
con durata ~88 s). Bug originale della v0.3.3, rilevato in produzione
dopo il bump a v0.4.0.

### Fix
- `scripts/io_loader.py::load_audio_multichannel` (riga 109 v0.3.3):
  la formula `int(data.shape[0] * sr / sr_orig)` usata per pre-allocare
  l'array `resampled` puo' differire di +/-1 sample rispetto all'output
  effettivo di `librosa.resample` (algoritmo default `soxr_hq`). Ora
  risampliamo ciascun canale separatamente in una lista, misuriamo la
  lunghezza minima effettiva e allineiamo tutti i canali con trim
  difensivo via `np.column_stack`. Il check `if sr_orig != sr` esistente
  gia' salta il resample nel caso sr_orig == target_sr.

### Aggiunto
- `tests/test_multichannel.py`:
  - `test_load_multichannel_resample_44100_to_48000_no_off_by_one`:
    regressione del crash con file stereo 44100 Hz a 88 s risampleato a
    48000 Hz. Verifica coerenza lunghezza +/- 2 e allineamento canali.
  - `test_load_multichannel_no_resample_when_sr_matches`: verifica che
    quando `sr_orig == target_sr` i campioni restino invariati bit-wise
    e non venga fatta alcuna operazione di resample.

### Modificato
- Bump versione 0.4.0 → 0.4.1 in `scripts/__init__.py`, `scripts/cli.py`
  (tre callsite), `scripts/report_cmd.py`, `scripts/report_pdf.py` (tre
  stringhe user-facing), `pyproject.toml`.


## [0.4.0] - 2026-04-15

Espansione del vocabolario CLAP italiano da 102 a 172 prompt in 17 categorie
(nuova categoria "sacralita sonora", "paesaggi italiani specifici" cresciuta
da 8 a 22 prompt). Introduzione di un layer di mapping accademico post-hoc
(`references/clap_academic_mapping_it.json`) che associa ogni prompt alle
tassonomie di riferimento (Schafer 1977, Truax 1984, Krause 2012, Schaeffer
1966, Smalley 1997, Chion, Westerkamp) con ereditarieta category_defaults
→ prompt override. Il payload che l'agente `soundscape-composer-analyst`
riceve ora contiene `clap.academic_hints` con distribuzioni pesate per
score cosine (krause, schafer_role, schafer_fidelity, schaeffer_type,
smalley_motion, chion, truax, westerkamp_soundwalk_relevance), da usare
come punto di partenza per la lettura critica, sempre da validare contro
narrativa e dati tecnici. Il PDF nella sezione CLAP riporta 2-3 righe di
sommario degli hint.

### Aggiunto
- `references/clap_vocabulary_it.json` v1.2: 172 prompt (+70 rispetto a
  v1.1). Nuova categoria `sacralita sonora` (10 prompt: campane maggiori,
  organo liturgico, canto gregoriano, processioni, rintocchi funebri,
  carillon, preghiere sussurrate). Espansione `paesaggi italiani specifici`
  da 8 a 22 prompt (mercato cittadino, borgo medievale, conservatorio,
  aula AFAM, motorino in centro storico, treno regionale, dialetto, piazza
  con fontana, ecomuseo, osteria, bar italiano, venditore ambulante, fiera
  paesana, traffico centro storico). Altri incrementi: biofonia (+10),
  antropofonia meccanica (+8), antropofonia urbana (+5), geofonia estesa
  (+4), trasformazioni elettroacustiche (+5), oggetto sonoro astratto (+3),
  geofonia (+3), ambiente didattico AFAM (+3), antropofonia domestica (+2),
  musica registrata (+2), performance multimediale (+1).
- `references/clap_academic_mapping_it.json` v1.0: schema con `enums`
  (liste valide per schafer_role/fidelity/krause/schaeffer_type/
  smalley_motion/chion/truax/confidence), `category_defaults` per le 17
  categorie del vocabolario v1.2, `prompts` override per 80+ prompt con
  specificita tipologica (schaeffer_type, smalley_motion) o promozione a
  soundmark (campane, soundscape italiani).
- `scripts/clap_mapping.py`: tre funzioni pubbliche:
  - `load_academic_mapping(path)`: carica e valida enum.
  - `get_prompt_mapping(prompt_id, vocab, mapping)`: merge superficiale
    category_defaults + prompts override, a query-time.
  - `aggregate_academic_hints(top_global, vocab, mapping, min_score=0.15)`:
    filtra tag rumorosi, pesa per score cosine, produce `distribution` +
    `dominant` con label `confidence` (high >= 0.5, medium >= 0.33,
    low < 0.33). Campi `truax` e `westerkamp_soundwalk_relevance` marcati
    `tentative: true`.
- Integrazione in `scripts/semantic_clap.py::clap_summary()`: calcola
  gli hint accademici dopo il top_global e li include nel `ClapResult`
  (nuovi campi `academic_hints` e `academic_mapping_version`). Wrapping
  try/except: se il mapping non carica, campo ritorna
  `{"available": False, "reason": "..."}` senza rompere la pipeline.
- `tests/test_clap_academic_mapping.py`: 9 test (load + enum, coverage
  categorie, risoluzione prompt con ereditarieta, enum validity, override,
  aggregate struttura, aggregate segnale debole, espansione paesaggi,
  categoria sacra).

### Modificato
- `scripts/agent_payload.py::build_agent_payload`: legge `academic_hints`
  direttamente da `summary["clap"]` (invece di calcolarli dentro il
  payload). Aggiunto campo `vocabulary_version` e `academic_mapping_version`
  al payload per tracciare la provenienza.
- `templates/agent_prompt.md`: aggiunto paragrafo esplicito "Come usare
  `clap.academic_hints` (v0.4.0)" che spiega i campi principali
  (`krause.distribution`, `schafer_role.present`, `schafer_fidelity`,
  `schaeffer_type.top_2`, `smalley_motion.top_2`, `chion_modes_present`) e
  il principio "punto di partenza, non verita". Istruzioni su come
  trattare `confidence: low` e `tentative: true`.
- `~/.claude/agents/soundscape-composer-analyst.md` (agent definition
  globale fuori dal repo): aggiornata sezione "Come ricevi i dati" con
  menzione del nuovo campo e istruzione di validazione. Fallback al
  comportamento v0.3.x se `available: false`.
- `scripts/report_pdf.py::_build_clap_block`: aggiunto sommario prosaico
  di 2-3 righe degli academic_hints (distribuzione Krause, ruoli Schafer,
  fidelity, Schaeffer top-2, Smalley top-2, modi Chion, rilevanza
  soundwalk) fra la tabella top-10 e la timeline. Solo se
  `available: true`.
- `scripts/semantic_clap.py::ClapResult`: aggiunti campi opzionali
  `academic_mapping_version: str` e `academic_hints: dict`.
- `tests/test_clap_tagging.py::test_vocabulary_load`: soglia `>= 40` →
  `>= 150`, aggiunto `assert vocab["version"] == "1.2"`, verifica id
  univoci.
- Bump versione 0.3.3 → 0.4.0 in `scripts/__init__.py`, `scripts/cli.py`
  (tre callsite), `scripts/report_cmd.py`, `scripts/report_pdf.py` (tre
  stringhe user-facing), `pyproject.toml`.

### Test suite
- 85 test passati + 1 skipped (76 pre-esistenti + 9 nuovi test
  `test_clap_academic_mapping.py`). Zero regressioni.

### Fuori scope v0.4.0, pianificato v0.5 o oltre
- Trascrizione dialoghi via Whisper large-v3 + VAD + traduzione italiana
  (flag CLI `--transcribe-speech`). Richiede aggiunta dipendenze
  (`openai-whisper`, `silero-vad`) e test dedicati su audio misto.


## [0.3.3] - 2026-04-15

Uniformazione in italiano del PDF e dei grafici. La v0.3.2 aveva ancora label
miste (italiano nei titoli sezione, inglese in alcune etichette di grafico,
dizionario `locale_it.PARAMETRI` per metà in inglese). Gli acronimi tecnici
internazionali (LUFS, RMS, STFT, ACI, NDSI, H, BI, ADI, AEI, dB, Hz, true
peak, clipping, rolloff) restano invariati come convenzione DSP, ma le
descrizioni discorsive e le intestazioni tabellari sono ora tutte in italiano.

### Modificato
- `scripts/locale_it.py::PARAMETRI`: tradotte le voci residue inglesi.
  `Peak` → `Picco`, `Crest factor` → `Fattore di cresta`, `Dynamic range` →
  `Gamma dinamica`, `Noise floor stimato` → `Rumore di fondo stimato`,
  `Integrated LUFS` → `LUFS integrato`, `Loudness Range (LRA)` → `Gamma di
  loudness (LRA)`, `True Peak` → `Picco reale (true peak)`, `DC offset` →
  `Offset DC`, `Hum 50/60 Hz` → `Ronzio 50/60 Hz`, `Spectral flatness` →
  `Piattezza spettrale`, `Zero-crossing rate` → `Tasso di attraversamenti
  zero`. Gli indici ecoacustici (`Acoustic Complexity Index (ACI)`, `Normalized
  Difference Soundscape Index (NDSI)`, `Acoustic Entropy (H)`, `Bioacoustic
  Index (BI)`, `Acoustic Diversity Index (ADI)`, `Acoustic Evenness Index
  (AEI)`) ora hanno descrizione italiana con sigla internazionale tra
  parentesi.
- `scripts/locale_it.py::INTESTAZIONI`: rimosso il riferimento obsoleto
  `(YAMNet)` dalla sezione `classificazione_semantica` (dalla v0.2.0 il
  backend di default è PANNs, non YAMNet).
- `scripts/plotting.py`: `"Waveform"` → `"Forma d'onda"`, `"Magnitude (dB)"`
  → `"Modulo (dB)"` negli spettri e nell'hum zoom.
- `scripts/comparison_plots.py`: `"Integrated LUFS"` → `"LUFS integrato"`,
  `"Dynamic Range (dB)"` → `"Gamma dinamica (dB)"`.
- `scripts/report_pdf.py`: header tabelle: `"Rank"` → `"Posizione"`,
  `"Score medio"` → `"Punteggio medio"`, `"Range (Hz)"` → `"Intervallo (Hz)"`
  nella tabella bande Schafer.
- Bump versione 0.3.2 → 0.3.3 in `scripts/__init__.py`, `scripts/cli.py`
  (tre callsite), `scripts/report_cmd.py`, `scripts/report_pdf.py` (tre
  stringhe user-facing), `pyproject.toml`.


## [0.3.2] - 2026-04-15

Abilitazione MPS (Metal Performance Shaders) per PANNs CNN14 su Apple Silicon.
La v0.3.1 forzava CPU anche quando MPS era disponibile, citando il fatto che
`panns_inference 0.1.1` non supporta nativamente device diversi da CUDA. La
v0.3.2 aggira il limite costruendo `AudioTagging` su CPU (con stdout soppresso)
e spostando manualmente il modello su MPS tramite monkey-patch. Speedup atteso
circa 5x su file lunghi (da ~28 min a ~5-6 min per un file di 67 min). CLAP
usava già MPS e continua a funzionare invariato, con in più un log esplicito
del device.

### Aggiunto
- `scripts/device.py`: helper condiviso con `resolve_device`, `log_device`,
  `suppress_stdout`. Sostituisce le due funzioni `_resolve_device` duplicate
  che vivevano in `semantic.py` e `semantic_clap.py` con priorità leggermente
  divergenti. Il log "Using device: <device>" su stderr rende trasparente
  quale backend hardware è in uso.
- Sanity forward pass in `PANNsClassifier._ensure_loaded`: dopo lo spostamento
  del modello su MPS esegue un forward di prova con 1 secondo di silenzio a
  32 kHz. Se fallisce, fa fallback trasparente a CPU con warning su stderr.
- `PYTORCH_ENABLE_MPS_FALLBACK=1` impostato sia in `scripts/__init__.py` (prima
  di qualunque import di torch) sia nel wrapper `bin/soundscape` (export dopo
  il venv activate). Doppia cintura per evitare edge case di import order
  durante i test.
- `tests/test_device_resolve.py`: 8 test sul nuovo helper device.
- `tests/test_panns_benchmark.py`: benchmark interno MPS vs CPU, eseguito
  solo con `SOUNDSCAPE_BENCHMARK=1`. Asserisce speedup minimo 1.43x
  (t_mps < t_cpu * 0.7).
- In `tests/test_semantic_classifier.py`: `test_panns_uses_mps_when_available`
  verifica che il modello sia effettivamente caricato su MPS;
  `test_panns_result_consistent_mps_vs_cpu` verifica che il drift numerico
  MPS vs CPU sia contenuto (overlap top-5 >= 4, max_abs_diff < 0.02).

### Modificato
- `scripts/semantic.py::PANNsClassifier`: rimosso il forzamento a CPU quando
  device risolto è MPS (righe 128-130 della v0.3.1). Ora costruisce
  `AudioTagging` sempre su CPU dentro `suppress_stdout()` (per sopprimere le
  print informative di panns_inference) e poi sposta esplicitamente il
  modello su MPS con `self._at.model.to(torch.device("mps"))` e
  `self._at.device = "mps"`. Questo funziona perché `AudioTagging.inference()`
  internamente chiama `move_data_to_device(audio, self.device)`, quindi
  aggiornando i due attributi tutto il forward pass avviene su MPS.
- `scripts/semantic_clap.py`: usa `scripts.device.resolve_device` al posto
  della funzione locale. Aggiunto `log_device("LAION-CLAP", _CLAP_DEVICE)`
  dopo il caricamento. Comportamento invariato.
- `scripts/__init__.py`: aggiunto `os.environ.setdefault(
  "PYTORCH_ENABLE_MPS_FALLBACK", "1")` prima dell'assegnamento di
  `__version__`.
- `bin/soundscape`: export `PYTORCH_ENABLE_MPS_FALLBACK=1` dopo `source venv`.
- Bump versione 0.3.1 → 0.3.2 in `scripts/__init__.py`, `scripts/cli.py`
  (tre callsite: summary dict, version_option, version_cmd),
  `scripts/report_cmd.py`, `scripts/report_pdf.py` (tre stringhe user-facing).

### Fix
- `pyproject.toml`: `version` stale a `0.1.0` da v0.2.0. Allineato a `0.3.2`.

### Test suite
- 77 test totali (66 v0.3.1 esistenti + 8 test_device_resolve + 2 nuovi
  semantic MPS + 1 benchmark saltato di default). 76 passed + 1 skipped su
  Mac M4 con MPS attivo. Benchmark misurato: speedup MPS/CPU 1.87x su 60 sec
  di audio (la soglia minima del test è 1.43x).

### Fuori scope v0.3.2, pianificato v0.4
- Accelerazione YAMNet via `tensorflow-metal`. Richiede l'aggiunta di
  `tensorflow-metal` a `requirements.txt` e test dedicati. YAMNet è backend
  legacy (default è PANNs), priorità bassa.


## [0.3.1] - 2026-04-15

Adeguamento tipografico completo alla nuova regola CLAUDE.md "Regola sulla tipografia
dei documenti generati". Sfondo bianco su pagine interne, testo nero su bianco, tabelle
markdown renderizzate come Table ReportLab vere, palette Tab10 sui grafici comparativi.
Fix collaterale: preambolo dell'agente rimosso automaticamente.

### Aggiunto
- `scripts/md_renderer.py`: parser markdown robusto basato su mistune 3.x. Converte AST
  in flowable ReportLab (Paragraph, Table, Preformatted, HRFlowable) gestendo titoli,
  paragrafi, liste ordinate e puntate, tabelle GFM con allineamento, blockquote, code
  fence, thematic break, inline bold/italic/code/link/strikethrough.
- `scripts/report_synthesizer._strip_preamble(text)`: rimuove qualsiasi riga prima del
  primo H1 nell'output dell'agente, correggendo il caso v0.3.0 in cui il modello apriva
  con "Ho tutti i dati necessari. Ecco il report.". Integrato nella pipeline dopo
  `sanitize_italiano`.
- `tests/test_md_renderer.py` (12 test).
- `tests/test_report_synthesizer.py` (6 test).

### Modificato
- `scripts/report_pdf.py::_on_body_page`: sfondo bianco puro (#FFFFFF), footer nero
  (#000000). La copertina resta come era (sfondo blu scuro con testo bianco, ammessa
  dalla regola al punto 2 come eccezione per copertine).
- `scripts/report_pdf.py::_markdown_to_story`: delegato a `md_renderer.render_markdown`.
  Firma invariata.
- `scripts/report_pdf.py::build_report` e `build_corpus_report`: aggiunto
  `NextPageTemplate("body")` dopo la copertina per switchare al template con sfondo
  bianco dalla seconda pagina in poi (bug v0.3.0 che lasciava le pagine interne con
  sfondo scuro della copertina).
- `scripts/report_styles.py::build_styles`: `body`, `body_it`, `quote_text`,
  `table_cell` textColor → `#000000`. `caption`, `quote_attr` → `#1A1A1A`. Titoli h1/h2
  mantengono `PAL["dark"]` come eccezione motivata per titoli di sezione.
- `scripts/report_styles.py::box_quote`: fondo cambiato da `bg_muted` (#e8e0d8) a
  `#FFFFFF` con barra sinistra terracotta come accento motivato.
- `scripts/comparison_plots.py`: `BG_AXES` e `BG_FIGURE` entrambi `#FFFFFF`.
  `FG_ON_LIGHT` a nero puro `#000000`. Palette serie dati sostituita con Tab10 di
  matplotlib (8 colori saturi print-friendly): bar chart LUFS in tab:blue, dynamic
  range in tab:green, radar ecoacustico ciclico su 8 colori Tab10 (escluso grigio e
  olive). Linee target LUFS in tab:red e tab:purple.
- `templates/report_synth_prompt.md`: nuova sezione "Regola critica: tabelle" che vieta
  tabelle markdown. Rafforzato il vincolo H1 iniziale con divieto esplicito di
  preamboli ("Ho tutti i dati necessari", "Ecco il report", "Procedo con...").
- `requirements.txt`: `mistune>=3.0,<4`.
- Bump versione a 0.3.1 in `scripts/__init__.py`, `scripts/cli.py::version_cmd`,
  `version_option` del CLI, `summary["version"]`, `report_pdf.build_corpus_report`.

### Fix
- Bug di rendering tabelle markdown: prima della v0.3.1 le righe con pipe `|`
  comparivano come testo letterale nel PDF. Ora sono rese come tabelle ReportLab con
  header, zebra e allineamento colonne secondo la sintassi markdown.
- Bug preambolo agente: l'output della sessione claude-p conteneva spesso una riga
  introduttiva ("Ho tutti i dati necessari, ecco il report") nonostante il template
  lo vietasse. `_strip_preamble` rimuove deterministicamente qualsiasi cosa prima
  del primo H1.
- Bug pagine interne con sfondo scuro: la mancanza di `NextPageTemplate("body")`
  nella story di ReportLab causava l'applicazione del template cover a tutte le
  pagine, con testo nero invisibile su sfondo blu scuro.

### Test suite
- 64 test passati (46 esistenti + 12 md_renderer + 6 report_synthesizer).



## [0.3.0] - 2026-04-14

Sotto-comando `soundscape report` per analisi comparativa di un corpus di file audio.
Lancia `analyze` su tutti i file della cartella, raccoglie i summary, produce grafici
comparativi e invoca una sessione Claude Code non interattiva per la sintesi testuale,
componendo un PDF comparativo in stile ABTEC40.

### Aggiunto
- `scripts/report_cmd.py`: orchestrazione completa del nuovo comando.
- `scripts/comparison_plots.py`: 5 grafici comparativi standard (LUFS bar, Dynamic
  Range bar, heatmap bande Schafer, radar indici ecoacustici, heatmap similarità
  CLAP). Helper `wcag_contrast_ratio` con verifica programmatica del contrasto
  WCAG AA 4.5:1 su tutti i testi.
- `scripts/report_synthesizer.py`: invocazione `claude -p` non interattiva via stdin.
  Pattern simile a `agent_bridge.py` ma con timeout esteso (300s default) e modello
  configurabile. Sanitizzazione italiano (rimozione em dash) sull'output.
- `templates/report_synth_prompt.md`: template del prompt per la sessione Claude
  con placeholder per corpus title, file payload, grafici. Vincoli di stile espliciti
  (italiano, no em dash, no GitHub).
- `references/golden_reports/REPORT_ANALISI_villa_ficana.md`: copia del REPORT_ANALISI
  manuale del 14/04/2026 su Villa Ficana, usato come riferimento di stile nella
  generazione dei report di corpus.
- `scripts/report_pdf.py::build_corpus_report()`: nuova funzione dedicata al PDF
  comparativo (copertina corpus, sommario esecutivo, tabella panoramica, grafici,
  sintesi markdown dell'agente, colofone). Supporta fallback se la sintesi non è
  disponibile.
- Sub-comandi CLI `report` e `report-merge` in `cli.py`.
- `tests/test_comparison_plots.py` (9 test, inclusi test su contrasto WCAG).
- `tests/test_report_cmd.py` (6 test, scansione, cache, smoke end-to-end, merge).

### Modificato
- `scripts/config.py`: nuove costanti `GOLDEN_REPORTS_DIR`, `GOLDEN_VILLA_FICANA`,
  `CORPUS_REPORT_MODEL`, `CORPUS_REPORT_TIMEOUT_S`, `CORPUS_CONFIRM_THRESHOLD_FILES`
  e `CORPUS_CONFIRM_THRESHOLD_MINUTES`.
- `scripts/report_styles.py`: colori degli stili `caption` e `quote_attr` da
  `muted_gray` (contrasto 4.13 su sfondo beige) a `dark_mid` (contrasto 7.92),
  in linea con il nuovo vincolo WCAG AA della CLAUDE.md.
- `scripts/report_pdf.py::_on_body_page`: footer con pagina e nome skill passati
  da `muted_gray` a `dark_mid` per contrasto adeguato.
- Versione bumped a 0.3.0 nel comando `soundscape version`.
- `requirements.txt`: nessuna nuova dipendenza (tutto risolto con lo stack v0.2).

### Politiche di esecuzione
- **Cache di freschezza**: il comando `report` riusa i summary JSON esistenti se
  sono più recenti del file audio. Flag `--rerun` forza l'analisi completa.
- **Conferma interattiva**: scatta sopra soglia (più di 10 file o durata totale
  oltre 30 minuti). Sotto soglia parte diretto. Flag `--yes` per skippare sempre.
- **Fallback pulito se `claude` non disponibile**: il prompt completo viene salvato
  in `<out>/corpus_synth_prompt.md`, il PDF viene prodotto con box "sintesi non
  disponibile", il sub-comando `soundscape report-merge <pdf> <md>` integra
  successivamente la sintesi prodotta a parte.

### Test suite
- 46 test passati in v0.3.0 (aggiunti 15 rispetto a v0.2).

## [0.2.4] - 2026-04-14

## [0.2.4] - 2026-04-14

### Modificato
- Vocabolario CLAP italiano ampliato da 70 a **102 prompt** (`references/clap_vocabulary_it.json` v1.1). Cinque nuovi blocchi tematici:
  - Geofonia estesa (+6): scogliera, pioggia su lamiera, fontana, fiume in forra, schiuma, grotta umida.
  - Trasporti e mobilità (+6): treno alta velocità, metropolitana, bicicletta su ciottolato, moto sportiva, nave mercantile, auto che frena.
  - Paesaggi italiani specifici (+8): campanile marchigiano, aia rurale, discussione di vicini, mercato rionale, osteria, trattore, processione, cicale del sud.
  - Trasformazioni elettroacustiche (+8): reverse, granulazione vocale, time-stretch estremo, convoluzione iperreale, pitch down, filtro stretto, feedback controllato, ring modulation.
  - Silenzi compositivi (+4): cadenza di silenzio, pausa con micro-rumori di sala, respiro fra eventi, stacco brusco.
- Nessuna modifica al codice. Il vocabolario viene riletto automaticamente al prossimo `soundscape analyze`.



## [0.2.3] - 2026-04-14

Riscrittura dell'agente compositivo, disattivazione confronto GRM fasullo, validazione qualitativa finale.

### Riscritto
- `~/.claude/agents/soundscape-composer-analyst.md`: nuovo focus operativo in cinque sezioni fisse (Osservazioni critiche, Oggetti sonori identificati, Collocazione estetica, Criticità tecniche, Gesti compositivi suggeriti). Obbligo di timestamp per ogni oggetto sonoro, gesti compositivi concreti con motivazione ancorata ai dati, divieto di citare autori senza evidenza empirica, marcatura "ipotesi di lavoro" per CLAP < 0.25.
- `templates/agent_prompt.md`: nuovo formato con narrativa inline nel prompt.

### Rimosso dal PDF di default
- Sezione "Confronto con profili GRM" disattivata. Riattivabile con `--compare=grm-experimental` o `<profile_id>`. Codice e profili letteratura-based mantenuti come stand-by per v0.3. Il PDF ora include un box di avviso sperimentale quando la sezione è riattivata.

### Fix
- Bug formatting hum `+-3.0 dB` corretto in `report_pdf.py::_hum_row()`.

## [0.2.2] - 2026-04-14

Introduzione dello strato intermedio narrativo fra dati tecnici e agente compositivo.

### Aggiunto
- `scripts/narrative.py`: generatore di prosa italiana segmentata (default 30 s per finestra). Integra livelli RMS/peak per segmento, spettro macro, densità onset, top-3 classifier e top-3 CLAP nel segmento in un paragrafo coerente. Modalità `full` (tutto), `summary` (12 finestre su file lunghi), `none`.
- `scripts/agent_payload.py`: riduce il summary a un payload essenziale per l'agente (metadata, technical, spettro macro, ecoacoustic, top-10 classifier, top-20 CLAP, narrative markdown). Evita timeout su file lunghi come Air piece RnR (13 min) e Villa Ficana MP3 (67 min).
- `references/panns_taxonomy_it.json`: 120 categorie AudioSet tradotte in italiano idiomatico per la narrativa.
- Nuova sezione PDF "Descrizione segmentata" subito prima di "Lettura compositiva".
- Flag CLI `--narrative=full|summary|none`.
- Refactor `agent_bridge.py`: accetta `narrative_md` inline e passa il payload ridotto all'agente.

## [0.2.1] - 2026-04-14

Auto-tagging semantico con LAION-CLAP su vocabolario italiano.

### Aggiunto
- `scripts/semantic_clap.py`: auto-tagging con modello LAION-CLAP `music_audioset_epoch_15_esc_90.14` (multilingual, accetta prompt italiani). Top-3 tag per ogni segmento di 10 s più top-15 globali.
- `references/clap_vocabulary_it.json`: 70 prompt italiani approvati dall'utente. 7 categorie (geofonia, biofonia, antropofonia domestica/urbana/meccanica, qualità schaefferiane, composizione soundscape) più 4 blocchi opzionali (musica registrata +10, performance multimediale +8, ambienti didattici AFAM +6, oggetti sonori astratti +6). File JSON editabile per personalizzazioni di progetto.
- Embedding audio e prompt serializzati in base64 float16 nel summary JSON per ricerca semantica futura (dimensione tipica ~80 KB per 13 min).
- Flag CLI `--clap/--no-clap`.
- Nuova sezione PDF "Auto-tagging CLAP (vocabolario italiano)" con top-globali e timeline top-3.
- `tests/test_clap_tagging.py` con 4 test smoke.

### Dipendenze aggiunte
- `laion_clap>=1.1.6`, `transformers>=4.40`, `torchvision` (dipendenza implicita di laion_clap).
- Checkpoint ~2.2 GB scaricato una volta in `~/.cache/clap/`.

### Note
- LAION-CLAP su MPS funziona (HTSAT transformer supportato), device `mps` usato automaticamente.
- Primo run CLAP sulla macchina richiede il download del checkpoint.

## [0.2.0] - 2026-04-14

Refactor del modulo `semantic.py` con interfaccia astratta `Classifier` per sostituire YAMNet con classificatori più recenti. Primo passo della roadmap v0.2 verso l'arricchimento semantico interpretativo.

### Aggiunto
- `scripts/semantic.py` refattorizzato: dataclass `ClassificationResult`, classe astratta `Classifier`, factory `get_classifier(backend)`.
- `PANNsClassifier` (CNN14 AudioSet, 527 classi, 32 kHz) come backend di default.
- `YAMNetClassifier` mantenuto come backend legacy (`--semantic-backend=yamnet`).
- Download automatico checkpoint PANNs via `urllib` (evita dipendenza da wget).
- Flag CLI `--semantic-backend=panns|yamnet`.
- `tests/test_semantic_classifier.py` con 6 test specifici per PANNs.

### Modificato
- `scripts/cli.py` usa chiave `classifier` unificata nel summary.
- `scripts/report_pdf.py` legge `semantic.classifier` (fallback `semantic.yamnet` per retrocompat), etichette generiche basate su `model_name`.
- `scripts/config.py` con nuove costanti: `SEMANTIC_BACKEND`, `SEMANTIC_DEVICE`, `PANNS_SR`, `CLAP_*`, `NARRATIVE_*`.
- **`--compare` default da `all` a `none`**: il confronto con i profili GRM letteratura-based è stato disattivato (non pertinente su file fuori tradizione GRM). Riattivazione esplicita con `--compare=grm-experimental` o `--compare=<profile_id>`.
- Fix bug formatting hum: `+-3.0 dB` ora correttamente `-3.0 dB`.
- `requirements.txt` con `torch`, `torchaudio`, `panns_inference`, `laion_clap`, `transformers`.

### Note
- `panns_inference 0.1.1` non supporta device MPS: viene automaticamente forzato a CPU. Tempo inferenza accettabile su Apple Silicon M4.
- MPS resta disponibile per CLAP e altri classificatori in v0.2.1+.
- Test suite: 27 test passati (6 nuovi su PANNs).


Tutte le modifiche significative a questa skill sono documentate qui.
Versionamento semver interno: MAJOR.MINOR.PATCH.

## [0.1.0] - 2026-04-14

Primo rilascio. Trasforma il toolkit frammentato in ~/audio-analyzer/ in
un'infrastruttura stabile e riutilizzabile su più progetti (Villa Ficana,
Terra Viva ESA, ABTEC40 Macerata, Ear Training Bologna, ricerca ITSERR).

### Aggiunto
- Struttura skill completa in `~/.claude/skills/soundscape-audio-analysis/`.
- Virtualenv Python 3.12 dedicata con tutte le dipendenze pinate.
- Font ABTEC40 Libre Baskerville + Source Sans Pro (OFL) committati in
  `assets/fonts/` per generazione PDF offline.
- Moduli di analisi tecnica:
  - `technical.py` livelli, LUFS EBU R128, crest, dynamic range, noise floor, clipping, DC offset.
  - `hum.py` hum check con baseline locale (bande 30-45 e 70-95 Hz), FFT 0.5 Hz/bin.
  - `spectral.py` bande Schafer, feature timbriche, onset density, Hi-Fi/Lo-Fi.
  - `ecoacoustic.py` ACI, NDSI, H entropy, BI, ADI/AEI (implementazione diretta).
  - `semantic.py` YAMNet con pre-check LUFS e normalizzazione temporanea in memoria.
  - `multichannel.py` analisi canale per canale, downmix equal-weight, confronto gruppi (front/center/LFE/surround/height).
- Gestione profili GRM di riferimento:
  - 4 profili letteratura-based: Parmegiani De Natura Sonorum (1975), Westerkamp Kits Beach Soundwalk (1989), Ferrari Presque Rien N.1 (1970), Krause Great Animal Orchestra (2012).
  - Schema JSON di validazione.
  - Comando `soundscape profile build` per rifinire profili da audio reale.
- `comparison.py` cosine similarity file ↔ profili GRM con narrativa italiana.
- `plotting.py` waveform, spettrogramma log, spettro medio, bar chart bande, zoom hum.
- Generatore PDF `report_pdf.py` + `report_styles.py`:
  - Stile ABTEC40 con palette 13 colori.
  - 5 famiglie di box (info, quote, accent, highlight, neutral).
  - Copertina gradient blu con elementi decorativi.
  - Sezioni: metadati, livelli, diagnosi tecnica, hum, spettro, bande, ecoacustica, semantica, multicanale, confronto GRM, lettura compositiva, colofone.
- Agente `~/.claude/agents/soundscape-composer-analyst.md`:
  - Vocabolario Schaefferiano, Schaferiano, Krause, Chion.
  - Output strutturato in 5 sezioni fisse.
  - Invocato automaticamente dal CLI con prompt template.
- Bridge `agent_bridge.py` con subprocess `claude -p` e fallback pulito.
- CLI `soundscape` con sub-comandi `analyze`, `profile list/show/build`, `init-profiles`, `version`.
- Wrapper shell `bin/soundscape` eseguibile.
- Fixture sintetici deterministici e pytest suite (21 test).
- Test di acceptance Villa Ficana che verifica:
  - Regressione anti falso-positivo hum su MP3 (baseline locale).
  - Regressione anti 97,9% Silence su file a -60 LUFS (pre-check LUFS attivato).
- Documentazione:
  - `SKILL.md` con frontmatter auto-invocation.
  - `README.md` quick start.
  - `references/lessons_learned.md`.
  - `references/taxonomies/*.md` (bande Schafer, indici ecoacustici, vocabolario Schaefferiano, tassonomia YAMNet).

### Lezioni applicate dall'esperienza Villa Ficana (14 aprile 2026)
- Hum check con baseline locale (bande 30-45 e 70-95 Hz), non globale. La
  versione globale produceva falsi positivi su sorgenti tonali.
- Pre-check LUFS prima di YAMNet. Se il file è sotto -45 LUFS, applica
  normalizzazione temporanea in memoria per evitare classificazione
  97% "Silence".
- Fallback robusto font ABTEC40 con tre livelli (OFL TTF, sistema, Helvetica core).
- Nessun em dash nei testi generati; funzione `sanitize_italiano` applica la regola.
- Multichannel analizzato canale per canale, non solo downmix.

### Criterio di successo verificato
Pipeline end-to-end eseguita su file Villa Ficana reali:
- `Camera da letto Ecomuseo Ficana ...wav` (stereo, 2 min): PDF 483 KB + JSON 20 KB + 5 PNG, YAMNet riconosce "Inside, small room" e "Knock", confronto GRM produce ranking, somma bande Schafer 98,44%.
- Test di acceptance pytest: 2 test passati (hum trascurabile su MP3, pre-check attivato a -60 LUFS).
- Suite completa: 21/21 test passati.

### Post-1.0 (roadmap)
- `birdnet_adapter.py` completo con birdnetlib per avifauna.
- Comando `profile build` applicato a file reali delle 4 opere GRM.
- Supporto Ambisonics B-format con spaudiopy.
- Database SQLite per storicizzare analisi cross-progetto.
- Interfaccia web locale con drag&drop.
