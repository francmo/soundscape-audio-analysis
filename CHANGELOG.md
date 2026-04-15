# Changelog

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
