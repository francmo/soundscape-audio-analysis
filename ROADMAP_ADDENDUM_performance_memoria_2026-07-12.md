# Addendum roadmap - Performance, memoria e robustezza del run di corpus

**Data**: 12 luglio 2026
**Versione analizzata**: 0.19.0
**Driver**: run di corpus reale del 12/07/2026 (10 file, 196,7 minuti totali, 2 file oltre i 60 minuti, 2 file quad) che ha saturato la macchina di sviluppo (M4, 24 GB RAM). Osservati durante il run - processo Python a 800% CPU, picco RSS 27 GB, swap thrashing (6,1 M swapout), load average 30,8, sistema al collasso (fseventsd 67%, WindowServer 42%), sintesi Claude del corpus fallita per doppio timeout a 300 s. Il PDF finale è stato prodotto ma senza la sezione di sintesi.

Questo addendum copre un'area che la roadmap non tratta - il costo computazionale della pipeline. Non propone alcun cambiamento ai valori numerici prodotti (livelli, indici, classificazioni, soglie); i gruppi A e B sono per costruzione a parità di output, verificabile con snapshot test. Le proposte di qualità semantica (gruppo E) sono subordinate al protocollo statistico del piano v0.20-v0.23 (N>=5 run, CI 95%, paired t-test).

---

## 1. Diagnosi - dove vanno tempo e memoria

Analisi statica di `cli.py::_analyze_single` e dei moduli chiamati, incrociata con il log del run (`report_run.log`) e i metadati (`corpus_run_metadata.json`).

### 1.1 Il file audio viene decodificato da disco 6-7 volte per analisi

Per un singolo file stereo la pipeline attuale esegue queste decodifiche complete indipendenti.

| # | Punto | Cosa fa | SR |
|---|-------|---------|-----|
| 1 | `io_loader.load_audio_multichannel` | sf.read completo + resample per canale | nativo -> 22050 |
| 2 | `technical.compute_lufs` (stadio 2) | subprocess ffmpeg ebur128 sull'intero file | nativo |
| 3 | `hum.hum_check` (stadio 3) | librosa.load completo | nativo -> 8000 |
| 4 | `semantic.precheck_loudness` (stadio 6) | **secondo** ffmpeg ebur128 identico al #2 | nativo |
| 5 | `semantic.prepare_waveform` (stadio 6) | librosa.load completo per PANNs | nativo -> 32000 |
| 6 | `cli.py` riga 119 (stadio 7) | librosa.load completo per CLAP | nativo -> 48000 |
| 7 | `speech` (se attivo) | resample in memoria di y | 22050 -> 16000 |

Il doppio LUFS (#2 e #4) è una duplicazione secca - stesso comando ffmpeg, stesso file, due processi. I resample soxr_hq da SR nativo su file da 60 minuti sono operazioni da decine di secondi ciascuna.

### 1.2 La stessa STFT viene ricalcolata circa 20 volte per file

librosa accetta una magnitudine `S` precomputata in quasi tutte le feature, ma la pipeline non la riusa mai.

- `spectral_summary` - 1 STFT n_fft=4096 (bande, picchi), scartata al ritorno.
- `compute_timbre` globale - 5 STFT n_fft=2048 separate e identiche (centroid, bandwidth, rolloff, flatness, flux), più ZCR.
- `onset_analysis` - 1 mel-spettrogramma (STFT interna).
- `cli.py` stadio 10 - **seconda** STFT n_fft=4096 identica alla prima (`compute_stft_mean` richiamata per i grafici); la matrice `S_stft` ritornata non viene mai usata (i plot usano solo `spectrum` e `freqs`).
- `plot_spectrogram` - 1 STFT n_fft=2048 completa.
- `multichannel.analyze_channels` - per OGNI canale 1 STFT 4096 + 5 STFT 2048 (per un file quad sono 24 STFT aggiuntive).
- `structure._extract_features_per_window` - `compute_timbre` per ogni finestra da 10 s. Su un file da 64 minuti sono 385 finestre x 5 STFT = ~1900 mini-STFT, di cui la structure usa solo 2 feature su 6 (centroid e flatness); bandwidth, rolloff, flux e ZCR per finestra vengono calcolate e buttate.
- `aural_form.build_dynamic_form` - una passata RMS aggiuntiva (la terza, dopo compute_levels e structure).

### 1.3 I grafici sono la causa principale del picco RAM (27 GB)

- `plot_waveform` passa a matplotlib **tutti i campioni**. Per il file da 64,3 minuti a 22050 Hz sono 85 milioni di punti; la costruzione dei vertici del Path (float64 x2) più le trasformate supera da sola i 3-4 GB di picco, per un PNG largo ~1500 px.
- `plot_spectrogram` fa pcolormesh (via specshow) su una matrice non decimata 1025 x ~166.000 colonne; fra coordinate QuadMesh e array colori sono altri 5-6 GB di picco.
- `load_audio_multichannel` tiene in vita per l'intera pipeline tre copie dell'audio (matrice `data`, lista `channels`, `downmix`), usate solo allo stadio 9. Per il file da 64 minuti stereo sono ~1,4 GB permanenti; per i quad il doppio.

La sovrapposizione di questi picchi con i modelli residenti (PANNs ~0,4 GB + CLAP ~2 GB su MPS + torch) spiega l'RSS osservato e lo swap. Su una macchina da 24 GB il costo termico dello swap thrashing supera quello del calcolo stesso.

### 1.4 Modelli - PANNs ricaricato per ogni file, prompt CLAP ri-embeddati per ogni file

- `semantic_summary` crea un nuovo `PANNsClassifier()` a ogni chiamata; il checkpoint CNN14 (~330 MB) viene riletto da disco e ricaricato su MPS **per ogni file del corpus** (confermato dal log - 11 occorrenze di `[PANNs CNN14] Using device: mps`). CLAP invece ha già il singleton corretto (`_CLAP_MODEL_SINGLETON`).
- `clap_summary` richiama `embed_prompts(prompt_texts)` a ogni file - il forward del text encoder sui 251 prompt del vocabolario, sempre identico, viene rifatto 10 volte in un corpus da 10 file.
- L'inferenza PANNs e CLAP procede un chunk da 10 s alla volta (`batch=1`). Su MPS il costo di dispatch per chiamata domina; per il file da 64 minuti sono 385 forward PANNs + 385 forward CLAP sequenziali.

### 1.5 Robustezza del run di corpus

- **Sintesi in timeout by design**. `CORPUS_REPORT_TIMEOUT_S = 300` con modello opus e un compito che richiede la lettura di 11 file (golden + 10 payload) e la scrittura di 2000-4000 parole. La stessa lezione era già stata codificata per l'agente compositivo (v0.6.2 - `AGENT_TIMEOUT_S` 300 -> 600 dopo "timeout x2 senza output"), ma non applicata al percorso corpus. Nel run di oggi entrambi i tentativi (300 s x2) sono scaduti e il PDF è uscito senza sintesi.
- **Recupero manuale macchinoso**. Esiste `report-merge`, ma il recupero richiede due comandi manuali distinti (claude -p + report-merge) documentati solo nel messaggio di errore.
- **Nessuna telemetria dei tempi**. Il log non riporta la durata di alcuno stadio; ogni ottimizzazione (inclusa questa diagnosi) va fatta a occhio. Anche la stima mostrata all'utente prima della conferma (`durata_audio x 1,2 + 2 min`) risulta sovrastimata di ~10 volte rispetto al comportamento reale osservato (~0,08-0,10x la durata dell'audio con questa pipeline su M4).
- **Cache dei summary senza controllo di versione**. `_summary_cache_valid` confronta solo gli mtime; un summary prodotto da una versione precedente della skill viene riusato in silenzio dentro un report nuovo.
- **Warning HF Hub a ogni load CLAP** (richieste non autenticate) anche quando il checkpoint è già in cache locale.

---

## 2. Gruppo A - Performance CPU (a parità di output numerico)

Ordinati per rapporto beneficio/effort.

### A1. Singleton PANNs module-level (come CLAP)

Cache module-level dell'istanza `PANNsClassifier` (chiave su backend+device), speculare a `_CLAP_MODEL_SINGLETON`. Elimina 9 ricariche del checkpoint da disco nel corpus di oggi.
**Effort** ~15 min. **Rischio** nullo (stessa istanza, stessi pesi).

### A2. Cache degli embedding dei prompt CLAP

Gli embedding testuali dei 251 prompt dipendono solo da (vocabolario, versione vocabolario, checkpoint). Cache in memoria module-level più cache su disco (`references/clap_prompt_embeddings_<vocabver>.npz`, invalidata su hash del JSON del vocabolario). Il forward testuale si paga una volta per release del vocabolario, non 10 volte per corpus.
**Effort** ~30-45 min. **Rischio** nullo (embedding bit-identici, arrotondamento float16 già nel summary).

### A3. Batching dell'inferenza PANNs e CLAP

I chunk da 10 s hanno tutti la stessa lunghezza (l'ultimo, più corto, resta fuori dal batch come oggi). Impilare i chunk in batch da 8-16 e fare un forward per batch. `AudioTagging.inference` e `get_audio_embedding_from_data` accettano già shape (batch, samples).
**Effort** ~1 ora con test. **Rischio** basso; i punteggi per chunk restano identici (verifica con snapshot a tolleranza 1e-5). Beneficio atteso 2-4x sulla fase di inferenza per file lunghi.

### A4. Compute once, share everywhere (decodifiche, LUFS, STFT)

Il cuore dell'intervento, in quattro mosse dentro `_analyze_single`.

- **a) Un solo LUFS**. `technical_summary` già calcola il LUFS; passarlo a `semantic_summary` (parametro `lufs_data` opzionale in `precheck_loudness`) ed eliminare il secondo ffmpeg.
- **b) Una sola decodifica**. Decodificare una volta a 48 kHz mono float32 (ffmpeg pipe o librosa) e derivare in memoria 32k (PANNs), 22.05k (analisi), 16k (speech), 8k (hum) con resample a cascata. Le derivazioni costano meno di una nuova decodifica+resample da SR nativo, e il file si legge da disco una volta sola. In prima battuta basta eliminare i load #5 e #6 (PANNs e CLAP) derivandoli dal decode multicanale già esistente.
- **c) STFT condivise**. Calcolare una volta |STFT| n_fft=4096 (bande, picchi, spettro medio, plot spettro) e una volta |STFT| n_fft=2048 (timbre, flux, spettrogramma plot), e passarle alle feature librosa via parametro `S=`. `compute_timbre(y, sr)` diventa `compute_timbre(y, sr, S=None)` con retrocompatibilita'.
- **d) Structure senza mini-STFT**. `_extract_features_per_window` oggi rifa' 5 STFT per finestra usando solo centroid e flatness. Derivare le feature per finestra aggregando le colonne della STFT 2048 globale per intervalli temporali (media dei frame che cadono nella finestra). Elimina ~1900 mini-STFT sul file da 64 minuti e rende le feature per finestra coerenti con quelle globali (stessi parametri).

**Effort** ~3-5 ore complessive con test di parità. **Rischio** moderato solo per (d) - il centroide per finestra calcolato da STFT globale differisce marginalmente da quello su chunk isolato (effetti di bordo del framing); va verificato che i confini structure non si spostino sul corpus di parity (tolleranza già prevista dal test con soglia MAD). (a), (b), (c) sono a parità bit o quasi-bit.

### A5. Governo dei thread e modalità a basso impatto termico

Oggi nessun cap - BLAS/Accelerate e torch prendono tutti i core (800% osservato) e il sistema collassa.

- `config.CPU_THREADS` (default 0 = auto) applicato a inizio pipeline con `torch.set_num_threads` e env `OMP_NUM_THREADS`/`VECLIB_MAXIMUM_THREADS` se non già impostati. Default proposto - `max(4, performance_cores - 2)`.
- Flag CLI `--low-impact` per `analyze` e `report` - imposta CPU_THREADS=4 e abbassa la priorità del processo (`os.setpriority`), così un run di corpus lungo convive con il lavoro interattivo invece di monopolizzare la macchina. Documentare nel SKILL.md che il run "di cortesia" è più lento ma non scalda né blocca.

**Effort** ~45 min. **Rischio** nullo sul piano numerico.

### A6. Thread espliciti per faster-whisper

`WhisperModel(..., cpu_threads=N)` allineato a CPU_THREADS invece del default CTranslate2.
**Effort** ~10 min.

---

## 3. Gruppo B - Memoria (fix del picco da 27 GB)

### B1. Waveform plot con inviluppo min/max decimato

`plot_waveform` deve disegnare al massimo ~4000 colonne (inviluppo min/max per pixel), non 85 milioni di punti. Risultato visivamente identico o migliore (l'inviluppo è più leggibile del plot lineare fitto), picco RAM da GB a KB, tempo da decine di secondi a frazioni.
**Effort** ~30 min. **Rischio** nullo (solo resa grafica).

### B2. Spettrogramma decimato nel tempo

Prima di specshow, ridurre la matrice a ~4000 colonne aggregando i frame (max per bin di colonne, che preserva i transienti meglio della media). Il PNG a dpi 130 largo 12 pollici ha ~1560 px, oltre 4000 colonne sono invisibili per costruzione.
**Effort** ~30 min. **Rischio** nullo (solo resa grafica).

### B3. Ciclo di vita dell'audio multicanale

Spostare `multichannel_summary` subito dopo il load (stadio 2) oppure liberare esplicitamente `mc["channels"]` e `mc["data"]` appena consumati. Obiettivo - una sola copia dell'audio (il downmix di lavoro) viva durante gli stadi pesanti.
**Effort** ~30 min. **Rischio** nullo.

### B4. Non ritornare matrici inutilizzate

`compute_stft_mean` ritorna `S` completa anche dove serve solo lo spettro medio (stadio 10). Variante `compute_spectrum_mean` senza ritorno di `S` (o riuso della STFT condivisa di A4c che rende il punto superfluo).
**Effort** incluso in A4.

**Obiettivo misurabile dei gruppi A+B** - picco RSS sotto i 10 GB e wall time ridotto del 40-60% sul corpus di riferimento del 12/07 (rispetto a 27 GB e ~5 min/file lungo osservati), senza alcuna variazione dei valori nei summary JSON (snapshot test).

---

## 4. Gruppo C - Robustezza del run di corpus

### C1. Timeout sintesi adeguato e configurabile

`CORPUS_REPORT_TIMEOUT_S` 300 -> 900 e flag CLI `--synth-timeout`. Retry con timeout raddoppiato al secondo tentativo (300+300 oggi, 900+1800 proposto solo se il primo fallisce per timeout). Stessa lezione della v0.6.2 sull'agente.

### C2. Sotto-comando `report-resynth`

Oggi il recupero di una sintesi fallita richiede due comandi manuali. Nuovo comando che, data la cartella del report (o il `corpus_run_metadata.json`), rilancia SOLO la sintesi dal `corpus_synth_prompt.md` salvato e fa il merge nel PDF (riusa `invoke_corpus_synthesizer` + `merge_markdown_into_pdf`). Un comando, idempotente, senza rifare l'analisi.

### C3. Fallback di modello per la sintesi

Primo tentativo col modello richiesto (default opus), secondo tentativo automatico con sonnet se il primo scade per timeout. Il PDF riporta quale modello ha prodotto la sintesi. In alternativa (più conservativo) solo log esplicito che suggerisce `--model sonnet`.

### C4. Telemetria dei tempi per stadio

Dict `timings` nel summary JSON (`{"levels": 2.1, "hum": 8.4, "spectral": 31.0, "panns": 95.2, ...}`) e riga di log per stadio con durata. Nel run metadata del corpus - tempo totale per file e per stadio aggregato. È il prerequisito per qualsiasi ottimizzazione futura misurata e fornisce i costi computazionali citabili nel paper.

### C5. Stima di durata calibrata

Sostituire la formula `durata x 1,2 + 2` con una stima basata sui timings reali (C4) - in prima battuta `durata_audio x 0,12 + 1 min per file + 8 min di sintesi`, poi auto-calibrante sulla mediana dei run precedenti (persistita in `references/` o in `~/.cache`).

### C6. Cache dei summary con controllo di versione

`_summary_cache_valid` deve controllare anche `summary["version"]` contro `skill_version()` (major.minor) oltre agli mtime. Flag `--rerun` invariato per forzare.

### C7. Silenziare la rete quando i checkpoint sono in cache

Se il checkpoint CLAP esiste già in `~/.cache/clap`, impostare `HF_HUB_OFFLINE=1` per il load (elimina warning e round-trip di rete). Documentare `HF_TOKEN` nel README per chi scarica la prima volta.

**Effort gruppo C** ~2-3 ore complessive.

---

## 5. Gruppo D - Qualità dei dati (piccoli, additivi)

### D1. Caveat metodologico sugli indici univariati (riprende v0.6.5 in backlog)

Il caveat Kane et al. 2023 e il FADI proposti nella v0.6.5 del backlog restano validi e a costo basso; questo addendum non li ridefinisce, li richiama come naturale complemento della sezione ecoacustica. La divergenza ACI legacy/maad (parity rho 0,117, flip respinto) merita una riga nel PDF - dichiarare quale definizione di ACI usa la skill (implementazione legacy, riferimento Pieretti et al. 2011) così il numero è interpretabile e confrontabile.

### D2. Finestre narrative allineate ai confini strutturali (esperimento)

La narrativa segmenta a finestre fisse da 30 s; la structure produce confini semanticamente motivati. Allineare le finestre narrative ai confini delle sezioni (con suddivisione interna a ~30 s dentro le sezioni lunghe) eviterebbe descrizioni che tagliano un evento a meta'. È un cambio di prodotto testuale - va misurato col benchmark (N>=5, CI 95%) prima di diventare default; flag sperimentale `--narrative-align structure|fixed`.

### D3. Coerenza feature globali/per-finestra

Effetto collaterale positivo di A4d già descritto - centroid e flatness per finestra derivati dalla stessa STFT delle feature globali, stessi parametri, stessa definizione. Oggi differiscono (n_fft 2048 default librosa su chunk isolati vs feature globali sullo stesso n_fft ma framing diverso).

---

## 6. Gruppo E - Qualità semantica (esperimenti sotto protocollo statistico)

Tutte le proposte di questo gruppo producono claim di miglioramento solo attraverso il protocollo del piano statistico (N>=5 run, CI 95%, paired t-test, tabella nel CHANGELOG). Nessun flip di default senza numeri.

### E1. Calibrazione delle soglie CLAP sui dati del comando `compare`

Le soglie di plausibility e hallucination (0,02-0,40 in `config.py`) derivano da casi singoli documentati. Con `compare` (v0.19) la skill accumula confronti uomo/macchina strutturati (Krause per bin, kappa). Proposta - quando i confronti disponibili superano una decina di file, usare le annotazioni umane come ground truth per una taratura sistematica delle soglie (grid search su precision/recall dei flag), con report riproducibile in `references/`. Collega v0.19 al piano v0.22 (inter-rater) e sostituisce la taratura aneddotica.

### E2. A/B del checkpoint CLAP generalista

Il checkpoint attuale (`music_audioset_epoch_15_esc_90.14`) è orientato alla musica; il corpus d'uso è prevalentemente soundscape/field recording. Esperimento - stesso benchmark, checkpoint `630k-audioset-best` (generalista), confronto punteggi e falsi positivi delle categorie marcate. Attenzione - le soglie e i pattern anti-allucinazione sono calibrati sulla distribuzione di score del checkpoint attuale; l'A/B va letto insieme a E1. Solo esperimento, nessun flip.

### E3. Spike su classificatori post-CNN14 (orizzonte v0.23+)

CNN14 (2020, mAP 0,431) ha successori con mAP nettamente superiore su AudioSet (HTS-AT, BEATs, EfficientAT). Un backend aggiuntivo `--semantic-backend beats` dietro l'interfaccia `Classifier` già astratta sarebbe a costo architetturale basso, ma sposta la distribuzione degli score e quindi TUTTE le soglie calibrate (narrative, structure, plausibility). Da valutare solo dopo E1 (che rende la ricalibrazione un processo, non un artigianato). Registrato qui come direzione, con la stessa cautela del "conflict resolver" v0.23+.

### E4. Ensemble di template per i prompt CLAP

Pratica standard CLIP/CLAP - per ogni prompt, 2-3 varianti di template ("registrazione di X", "suono di X", "X in campo aperto") ed embedding medio. Riduce la varianza del text encoder senza toccare il vocabolario semantico. Con la cache A2 il costo runtime è zero (si paga solo alla generazione della cache). Esperimento con benchmark, poi eventualmente default.

### E5. Aggregazione max-pooling accanto alla media (CLAP globale)

`global_top_tags` usa solo la media sui segmenti - un evento saliente di 10 s in un file di 60 minuti scompare per costruzione. Aggiungere accanto (non al posto) un ranking per max score con conteggio segmenti sopra soglia, reso nel PDF come "presenze puntuali salienti". Additivo, già coerente con la filosofia della timeline PANNs citabile (v0.19).

---

## 7. Cosa NON si propone

- **Flip del backend ecoacustico a maad** - già valutato e respinto (parity ACI rho 0,117, v0.9.0); resta opt-in.
- **Parallelismo multi-file (process pool) nel report di corpus** - su una macchina da 24 GB il collo è la RAM, non la coda dei file; con A+B il singolo processo torna sotto controllo, il pool moltiplicherebbe i picchi. Da rivalutare solo dopo, eventualmente con 2 worker e cap thread per worker.
- **Spostare Whisper su GPU** - CTranslate2 non supporta MPS (già documentato in config); int8+NEON resta la scelta giusta.
- **Cambi al contratto interchange o ai campi dei summary** - fuori scopo; A/B/C sono trasparenti per l'Atelier e per `compare`.

---

## 8. Piano di release proposto

| Release | Contenuto | Effort stimato (sessione attiva) | Gate |
|---------|-----------|----------------------------------|------|
| v0.19.1 | A1, A2, A5, A6, B1, B2, B3, B4, C7 | 3-4 ore | snapshot test summary invariati + suite leggera |
| v0.19.2 | A3, A4 (compute once) | 3-5 ore | parity test dedicato su corpus fixture + structure invariata |
| v0.19.3 | C1-C6 (robustezza corpus + telemetria) | 2-3 ore | run di corpus reale end-to-end |
| sperimentali | D2, E1, E2, E4, E5 | 1-3 ore ciascuno | protocollo statistico v0.20+ |

La sequenza mette prima i fix a rischio zero e beneficio massimo (v0.19.1 da sola dovrebbe eliminare lo swap e la saturazione termica), poi il refactor compute-once che richiede il parity test più attento, poi la robustezza. Gli esperimenti semantici seguono il binario statistico già pianificato e non interferiscono con la numerazione v0.20-v0.23.

### Criterio di accettazione complessivo (v0.19.1-v0.19.3)

Sul corpus di riferimento del 12/07 (10 file, 196,7 min) rianalizzato da zero con `--rerun` -

- picco RSS del processo < 10 GB (era ~27 GB);
- nessuno swap thrashing con le app quotidiane aperte;
- wall time ridotto di almeno il 40%;
- summary JSON identici ai baseline (tolleranza float 1e-4, structure/narrative invariate);
- sintesi corpus completata al primo o secondo tentativo, PDF con sezione di sintesi presente;
- log con telemetria per stadio.
