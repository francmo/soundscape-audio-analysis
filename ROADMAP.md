# Roadmap soundscape-audio-analysis

Documento unico per orientarsi: cosa fa la skill oggi, cosa e' pianificato,
chi fa cosa. Aggiornato a ogni release.

**Versione corrente**: 0.19.1 (12 luglio 2026)
**Test suite**: suite leggera 290 passed + 1 skipped (32 deselezionati, i test con modelli PANNs/CLAP reali)
**Branch**: `main`
**Aggiornamento ROADMAP**: 12 luglio 2026 (nuovo addendum performance/memoria
con piano v0.19.1-v0.19.3, prima tranche shippata come v0.19.1; per commit e
release fa fede CHANGELOG.md, qui niente hash che invecchiano)

---

## Stato corrente

> Nota 02/07/2026. L'elenco capabilities qui sotto fotografa la v0.11 ed è
> storicamente valido ma incompleto. Dopo di allora sono arrivate, in sintesi,
> le calibrazioni didattiche anti-forzatura (v0.12.6-v0.14), spread e flux
> timbrici (v0.15), gli assi Aural Sonology con contratto interchange v1.2 e
> comando `enrich` (v0.16-v0.17), il benchmark con similarità semantica e
> rigore statistico (v0.18), la release di igiene post-audit (v0.18.1), il
> confronto annotazioni umane vs skill (`compare`) e la timeline PANNs
> citabile nel PDF (v0.19). Dettagli release per release in CHANGELOG.md.

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
- **Auto-tagging CLAP italiano**: 251 prompt v1.9 (conteggio verificato il
  02/07/2026) in categorie tematiche
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
| Tassonomie di riferimento | `references/taxonomies/` (note narrative .md), `references/taxonomies.json` (vocabolario canonico v1.0, 128 termini in 8 tassonomie, fonte per la PWA `soundscape-annotation-atelier`) |
| Profili GRM | `references/grm_profiles/` |
| Feedback utente | `references/user_feedback/` |

---

## Pianificato (priorita' decrescente)

### Addendum 12/07/2026 - performance, memoria e robustezza del corpus

Diagnosi e piano in `ROADMAP_ADDENDUM_performance_memoria_2026-07-12.md`,
nato dal run di corpus del 12/07 che ha saturato la macchina (RSS 27 GB,
swap, 800% CPU, sintesi in doppio timeout). Tre tranche: **v0.19.1 SHIPPATA**
(grafici decimati, cache classifier e prompt CLAP, cap thread, `--low-impact`,
HF offline); **v0.19.2** compute-once (LUFS singolo, decodifica unica, STFT
condivise, batching inferenza, structure senza mini-STFT) con parity test;
**v0.19.3** robustezza corpus (timeout sintesi 900 s, `report-resynth`,
fallback modello, telemetria tempi per stadio, stima calibrata, cache con
version check). Gli esperimenti semantici dell'addendum (calibrazione soglie
dai dati `compare`, A/B checkpoint CLAP, ensemble template, max-pooling)
seguono il protocollo statistico v0.20+.

### Addendum 02/07/2026 - esiti audit, v0.18.1/v0.19.0 e rinumerazione

- **v0.18.1 SHIPPATA** (igiene post-audit): versione unica da pyproject.toml
  con guard-rail nei test, escaping XML nei Paragraph del PDF, chiavi reali
  nella sintesi iniziale, accenti nelle stringhe renderizzate, caveat sui
  profili GRM literature_based, SKILL.md/README allineati (251 prompt, PANNs
  default).
- **v0.19.0 SHIPPATA**: `soundscape compare` (annotazioni umane dell'Atelier
  vs analisi della skill, tre assi: confini strutturali, famiglia Krause per
  bin con Cohen's kappa, copertura per annotazione) + tabella timeline PANNs
  citabile nel PDF (addendum 19/06 chiuso). Era la "v0.5" residua della
  roadmap della PWA Annotation Atelier.
- **Aperti dall'audit, da verificare con casi reali prima di toccare le
  soglie**: filtro anti-allucinazione che marca biofonia legittima; misure
  placeholder nella narrativa su file sotto i 20 s; ricostruzione
  `audio_derived` dei profili GRM (`build_profile_from_audio` esiste, servono
  gli audio sorgente).
- **Follow-on v0.18 dichiarato in CHANGELOG**: ricalcolo retroattivo del
  benchmark v0.9 -> v0.12.3 con metodo hybrid e CI 95% (N=5 x 14 tracce, run
  costoso da pianificare in una finestra dedicata).
- **Rinumerazione**: le tappe pianificate sotto ("v0.14-v0.17" del piano
  originale) diventano v0.20-v0.23; i vecchi numeri collidono con release
  reali già uscite con altri contenuti (il piano "v0.13" è shippato come
  0.18.0).

### Addendum 19/06/2026 - timeline PANNs citabile nel report PDF

> **STATO: IMPLEMENTATO nella release 0.19.0 (02/07/2026)**: tabella "Timeline
> per segmento" in `_build_semantic_block`, compattata sul tag dominante
> (`_merge_panns_timeline`), cap a 40 righe con nota di omissione.

Problema emerso nell'uso didattico. Quando un rilievo si riferisce a un singolo segmento temporale (per esempio un transito Vehicle/Train forte solo nei primi dieci secondi, che sulla media dell'intero file scende molto), il valore per-segmento non è citabile dal solo report PDF. Oggi la pagina di classificazione semantica stampa come testo solo gli aggregati globali: `top_global` (etichettato "punteggio medio") e `top_dominant_frames` (percentuali di dominanza). L'andamento per-segmento esiste in `summary.json` (`semantic.classifier.timeline`) ma nel PDF è reso solo dal grafico dei tag nel tempo, quindi chi fonda le osservazioni su citazioni testuali del PDF non trova il numero e lo legge come una discrepanza fra i tre valori (per-segmento, media globale, dominanza per-frame), che invece sono coerenti.

Proposta additiva, basso rischio: aggiungere al report PDF una tabella compatta della timeline PANNs per-segmento (t_start, t_end, primi 2-3 tag con score), accanto al grafico esistente. Rende ogni rilievo "nel tempo" verificabile e citabile dal solo PDF e allinea report e `summary.json`. Nessuna modifica ai dati, solo alla resa; verificare non regressione su corpus iteration.

### Addendum 15/05/2026 - caso A (Soundscape Annotation ABA Macerata)

Nove interventi (6 sulla skill, 3 sui template) emersi dal primo dossier
didattico del corso PTSM. Schede di valutazione, ordine, decisioni di
design aperte: `ROADMAP_ADDENDUM_caso_a_2026-05-15.md`. Non sostituisce
la sequenza statistica v0.13-v0.17, la affianca: i 3 interventi a impatto
quantitativo (speech mediation, onset citation, confidenza narrative
numerica) entrano sotto regime paired t-test, i 6 qualitativi/strutturali
possono essere shippati con sola verifica di non regressione su corpus
iteration v0.10. Aggregazione proposta: **v0.12.5 - integrazione caso
A** (una sola release con i 3 interventi quantitativi). Decisioni
di design aperte in §4 dell'addendum, da risolvere prima di iniziare.

### Piano statistico pre-paper (20/04/2026; tappe rinumerate v0.20-v0.23 il 02/07/2026)

Driver: review critica esterna dopo v0.12.3 ha identificato che il noise
floor stocastico ±15-20 punti sub-agent rende non-falsificabili i delta
delle release v0.9 -> v0.12.3 (+2.1 sull'all mean, dentro il rumore).
Nessuna claim di miglioramento e' metodologicamente difendibile in un
paper SMC/NIME/Organised Sound senza intervalli di confidenza e altre
misure di governance statistica del benchmark.

La review proponeva 10 interventi tutti in v0.13. Scelta operativa:
distribuire su 4-5 minor release ordinate per costo/beneficio, applicando
ad ogni step le nuove metriche statistiche.

#### v0.13 - Rigore statistico + similarita' semantica (~8 ore)

> **STATO: IMPLEMENTATO nella release 0.18.0 (28/06/2026)**, branch `feat/benchmark-v0.13`.
> Embedding similarity (`scripts/embedding_match.py`, modello `paraphrase-multilingual-mpnet-base-v2`,
> metodo `hybrid` = lessicale OR embedding) e rigore statistico (`scripts/benchmark_stats.py`:
> intervallo di confidenza 95% + paired t-test con Cohen d_z; harness `--runs N`). Correzione
> empirica alla stima qui sotto - la soglia cosine reale e **0.45**, non 0.7 (su mpnet i sinonimi
> stanno a ~0.50, non ~0.85); con 0.7 non matcherebbe nulla. Il ricalcolo retroattivo
> v0.9 -> v0.12.3 resta da eseguire come run completo (N=5 x 14 tracce, follow-on costoso).

Blocker per ogni claim futuro di miglioramento.

- **Paired t-test, N=5-7 run per versione**. `blind_benchmark_cycle.py`
  deve girare piu' volte per versione, calcolare intervallo di confidenza
  al 95% via paired t-test (stessa traccia vs stessa traccia), non
  confronto medie di campioni indipendenti. Il paired test e' piu'
  potente del t-test unpaired e permette N piu' basso.
- **Embedding similarity per matching termini**: sostituire Jaccard con
  cosine similarity su sentence-transformers
  (paraphrase-multilingual-mpnet-base-v2), soglia 0.7. "Sviluppo timbrico"
  vs "evoluzione spettrale" oggi score Jaccard=0, con embedding ~0.85.
  Jaccard resta come metrica secondaria legacy per tracciabilita'.
- **Ricalcolo retroattivo** v0.9 -> v0.12.3 con nuove metriche. Dichiarare
  onestamente nel CHANGELOG quali release erano miglioramenti reali e
  quali rumore.

Criterio di accettazione: tabella versioni con media, deviazione
standard, CI 95% pre/post embedding, colonna "significativo vs versione
precedente" (paired t-test p<0.05).

#### v0.20 - Governance corpus (~12 ore; era "v0.14" nel piano originale)

- **Normalizzazione gold fatti vs cornice**: ogni gold suddiviso in
  `fatti_analitici` (tassonomia, tecniche, parentele dichiarate) e
  `cornice_interpretativa` (lettura poetica, programma). Il benchmark
  confronta agent output solo con `fatti_analitici`. Risolve il bias:
  attualmente confrontiamo programme notes Cusack (poetico) con Moore
  eContact WSP (tassonomico) come se fossero lo stesso genere letterario.
- **Preregistration template held-out**: `heldout_preregistration_v{X}.md`
  con hash git committato prima di qualsiasi run OOD. Documenta prompt
  version + pipeline version usati. Evita leak implicito da iterazione
  sotto osservazione.

#### v0.21 - Payload agent + routing epistemologico (~10 ore; era "v0.15")

- **Payload agent rinforzato (non sostituito)**: aggiungere blocco
  `top_panns_scored` e `top_clap_families_scored` al payload in formato
  numerico esplicito, accanto alla narrativa 30s esistente. NON rimuovere
  la narrativa (contiene struttura temporale che l'agent usa per Scene
  sonore). L'agent vede entrambi: qualificatori linguistici per la grana
  temporale, numeri per il ranking.
- **Mode routing esplicito via CLI**: flag `--mode
  acousmatic|soundscape|hybrid|auto` (default auto con euristica
  trasparente + soglia esposta). Il prompt agent carica condizionalmente
  le tassonomie:
  - acousmatic: Schaeffer/Smalley/Chion
  - soundscape: Schafer/Krause/Westerkamp
  - hybrid: tutte + istruzione esplicita di dichiarare quale paradigma
    si applica a ogni scena
  Nel PDF: indici ecoacustici mostrati con banner di avviso quando
  mode=acousmatic (l'applicare Krause a Parmegiani e' error categoriale).
- **Pydantic parziale su parentele_stilistiche**: enum di compositori/
  scuole canoniche, output come `list[ComposerEnum]` anziche' testo
  libero. Abbatte varianza per la sezione piu' critica del benchmark.

#### v0.22 - Inter-rater reliability (~20 ore, umane; era "v0.16")

- **Cohen's kappa su 3-4 brani** con un secondo annotatore (candidato:
  musicologo/compositore di Bologna o Macerata) indipendentemente sullo
  stesso schema gold. Il kappa fissa il tetto legittimo del benchmark:
  se due umani concordano al 80%, nessun LLM puo' superare quella
  soglia eticamente. Step fondamentale per paper.

#### v0.23+ - Architettura speculativa (solo dopo v0.22; era "v0.17+")

Solo se dopo v0.22 il sistema e' statisticamente stabile e i gap
residui lo giustificano. Nessun impegno di timeline.

- Conflict resolver CLAP/PANNs con tabella priorita' + flag `conflict=true`
  quando divergenza > soglia.
- Multi-agent split (analista_tecnico + analista_semantico +
  drammaturgo_sintetizzatore) con validazione A/B vs single-agent N=10.
- RAG few-shot: iteration set come database vettoriale embedding CLAP
  audio. Inject i 2-3 gold piu' simili come stylistic template nel
  prompt drammaturgo.

#### Regola operativa per tutte le tappe del piano statistico

Ogni release: N=5+ run per misurare, CI al 95%, tabella paired delta
nel CHANGELOG. Nessun commit dichiara "miglioramento" se gli intervalli
si sovrappongono.

### Backlog pre-paper (ereditato, ora subordinato alla sequenza sopra)

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

### v0.6.5 — Patch indici ecoacustici (3-4 h)

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

### v0.6.6 — Hotfix dipendenti dal feedback utente (continuo)

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

- **v0.11.0** (20/04/2026): leggibilita' PDF + precisione narrative.
  Aggiunta `_build_narrative_legenda()` (tabella 8x5 soglie
  PANNs/CLAP/flatness/centroide/onset/LRA/LUFS) prima della Descrizione
  segmentata. `narrative._describe_panns/clap`: qualificatori
  linguistici (`tenue/plausibile/marcato`, `affinita' debole/moderata/
  forte`) integrati con valori in parentesi. Blind cycle completo su 14
  brani: mediana +0.95 vs v0.10, media -0.87, 5 regressioni e 6
  migliorie bilanciate. **Lezione**: noise floor stocastico sub-agent
  misurato a ~±15-20 punti (non ±10 come stimato), da N14 variato di 23
  punti tra due run identici. Bug italian_context stale (CLAP pre-v0.8.2)
  risolto via re-analyze con CLAP v1.9 fresh: N12 Fabbrica 13.8 -> 19.5.
- **v0.10.0** (19/04/2026): regola fondatori + 5 gold Nottoli.
  Nuova sezione "Regola dei fondatori" in `agent_prompt.md` e
  `agents/soundscape-composer-analyst.md` che mappa 9 scuole/tecniche
  con autori canonici da nominare (Schafer+WSP, Truax+Roads,
  Zuccheri+Fonologia, Risset+GRM+Bayle, Cusack+CRiSAP, Lopez+Vainio+
  Nilsen+Koner, Watson+Winderen+Krause, Lockwood+Westerkamp, Smalley).
  Terminologia canonica obbligatoria (spectromorphology, keynote,
  soundmark, musique concrete, granular synthesis, quadrato magico,
  sonic journalism, PODX/Syter/MUSIC V). Corpus benchmark da 9 a 14
  tracce: aggiunti 5 gold Nottoli (Truax Basilica + Song of Songs I,
  Nono Fabbrica + Non Consumiamo Marx, Risset Sud). Blind cycle:
  **mediana +5.6 vs v0.9, media +2.9**, 7 migliorie >5 pt. Infrastruttura
  `blind_benchmark_cycle.py` introdotta in `~/soundscape-training/tools/`.
  Split iteration/held-out formalizzato: 14 iteration visibili, 6
  Research Catalogue (Chester/Brito Dias/Pisano/Chattopadhyay/Wright)
  held-out sigillati per v1.0.
- **v0.9.0** (20/04/2026): Step A refactor ecoacoustic. Wrapper
  `ecoacoustic_maad.py` contro scikit-maad 1.4.3 (Ulloa 2021). Dispatcher
  `ecoacoustic_summary(backend=...)`. Flag CLI `--ecoacoustic-backend`,
  default `legacy`. 10 test parity nuovi, fixture sintetiche
  `silence_digital.wav` + `biofonia_sintetica.wav`. Pin requirements
  stringenti (`scikit-maad==1.4.3`, `scikit-image<0.23`, `tifffile<2024`,
  `numpy<2.0`). Bug fix wrapper: NaN su silenzio + NaN su temporal_entropy
  con audio lungo, mapping EAS->Sueur verificato algebricamente.
  **Parity corpus v1** (9 brani): ρ NDSI=1.000, BI=1.000, H_total=0.983,
  ACI=0.117. Flip default NON approvato in v0.10.0 per ACI. Wrapper maad
  resta opt-in permanente. 192 test passed.
- **v0.8.2** (19/04/2026 sera): categoria CLAP 'paesaggi dalmati e
  adriatici' (6 prompt) per recuperare il fit mediterraneo su Ferrari
  *Presque Rien* senza bias italo-generico. Ferrari: 49.1 -> 59.9/100
  (+10.8, precision/recall parentele 0.80).
- **v0.8.1** (19/04/2026 sera): flag deterministico `italian_context.
  is_italian_context` in agent_payload + regola agente "hum != Fonologia
  RAI se contesto non italiano". Test blind esterni (Westerkamp *Kits
  Beach*, López *Buildings [New York]*): attribuzione autore + titolo
  + anno corrette al primo passo, flag citato esplicitamente
  dall'agente come indicatore anti-Fonologia.
- **v0.8.0** (19/04/2026): patch vocabolario CLAP per rimuovere bias
  italo-centrico. v1.7 -> v1.8: 18 prompt neutralizzati (rimossa parola
  "italiano"/"mediterraneo" quando semanticamente non essenziale),
  1 rimosso (ita_12 duplicato), 10 aggiunti (5 nuove categorie
  non-italiane: nordici, artici, anglosassoni, europei orientali,
  urbani internazionali). Totale prompt 236 -> 245. `category_defaults`
  aggiornato in clap_academic_mapping_it.json. Benchmark esteso con
  acronym alias (`(GRM)` matcha "GRM") e stopwords filter (di/the/de/of)
  per metrica piu' equa. Zero tag italo-specifici nei top-10 CLAP dei
  9 brani del corpus golden v1 (era 15-20 su v1.7). Media v0.8.0:
  41.3/100 (Δ +0.4 vs baseline v0.7.1 ricalcolato). Trade-off: Ferrari
  -10 (unico brano davvero mediterraneo, perde fit specifico), Nilsen
  +11.8, Lockwood +19.6, Cusack London +5.8 (guadagni massicci su
  brani non italiani che erano il target primario).
- **v0.7.3** (19/04/2026): rule engine contestuale condizionato
  (`scripts/contextual_hints.py`) che ispeziona il payload agente e
  inietta dinamicamente blocchi "Suggerimenti contestuali di parentela"
  solo quando i marker acustici sono realmente presenti. 7 regole
  (underwater/contact_mic_ice/urban_drone/sonic_journalism/drone_metal/
  river_long/hum_no_fonologia). 16 test unitari. Modifica
  `agent_bridge.py::_build_prompt` per l'iniezione. Fix `benchmark.py`
  soglia match da 60% a 50% (permette match su cognome-soltanto per
  frasi di 2 parole: "Westerkamp" matcha "Hildegard Westerkamp"). Media
  v0.7.3: 39.5/100, Δ -0.2 vs baseline v0.7.1 ricalcolato (39.7).
  Risultato "neutrale metrico" con redistribuzione: guadagno forte su
  Nilsen (+13.5), Lockwood (+24.9), Cusack Chernobyl (+7.1); Ferrari
  stabile a 62.1 (gold verificato); regressione su Watson (-27.5
  artefatto gold incompleto: skill cita Watson+Köner ma gold non ha
  Köner nelle parentele attese). **Skip v0.7.2**: tentativo prompt-patch
  monolitico rollbackato lo stesso giorno (regressione -13 Ferrari,
  -10 Winderen, -9 Lopez), pattern di non-monotonicità LLM documentato
  come lezione metodologica per il paper.
- **v0.7.1** (19/04/2026): infrastruttura benchmark. `scripts/benchmark.py`
  con parsing deterministico gold, match fuzzy, metriche precision/recall/
  Jaccard su terminologia e parentele, score aggregato 0-100.
  `templates/golden_analysis_schema.md` schema standardizzato per
  scrivere gold parsabili. Sub-comando `soundscape benchmark` CLI.
  Primo gold calibrato Ferrari *Presque Rien N°1* (41.1/100 baseline).
  11 nuovi test. **Skip v0.7.0**: plausibility sistematica rimandata a
  v0.7.2+ con driver empirico dal benchmark. Driver: corpus golden v1
  validato 2026-04-19 con 48% aggregato (test-set held-out, vs 80%
  corpus Nottoli training-set); **5 gold su 9 contenevano allucinazioni
  LLM sui titoli**, lezione metodologica codificata nel validator gold.
- **v0.6.8** (18/04/2026): estensione pre-filtro plausibility da 5 a 11
  pattern (aspirapolvere, scrittura tastiera, pianto infantile, grandine,
  porta di legno, veicoli specifici). 154 test passati. Embrione
  ulteriore della v0.7.0 completa.
- **v0.6.7** (18/04/2026): rendering PDF del flag plausibility v0.6.6
  (corsivo + suffisso testuale "[plausibilita bassa/media]" + caption
  automatica sotto la tabella top-10 CLAP). Chiude il punto rimasto
  aperto in v0.6.6. Zero regressioni, 147 test passati.
- **v0.6.6** (18/04/2026): hotfix dalle 5 analisi blind del corpus
  Nottoli (Truax Basilica, Truax Song of Songs I, Nono Fabbrica
  illuminata, Risset Sud part 1, Nono Non consumiamo Marx). Quattro
  patch atomiche: (a) vocabolario CLAP v1.7 con 5 categorie nuove e
  33 prompt (ambienti industriali, soundscape politico urbano,
  elektronische Musik storica, sintesi digitale storica, canto
  liturgico e cantillazione) per coprire domini semantici
  sistematicamente invisibili (Nono industriale, Nono politico,
  Fonologia RAI, MUSIC V, canto monastico); (b) plausibility
  pre-filter deterministico su 5 pattern di falso positivo
  ricorrenti (rubinetto, preghiera, spiaggia mediterranea, biofonia
  su elettronico, treno su bande basse stretched), embrione della
  v0.7.0 completa; (c) prompt agente "lingua != scuola compositore"
  con 4 casi documentati + indicatori tecnici per 4 scuole
  (Fonologia RAI, GRM, WSP/SFU, WDR) per correggere il bias di
  attribuzione emerso su Song of Songs I (EN ma canadese) e Non
  consumiamo Marx (FR ma italiano Fonologia); (d) Krause cross-check
  da PANNs frame dominanti tramite `config.PANNS_LABEL_TO_KRAUSE`
  per rilevare inconsistenze col Krause CLAP-based (caso Sud: NDSI
  +0.516 vs Krause CLAP 4% biofonia). 147 test passati. Driver:
  5 file feedback in `references/user_feedback/` + research log in
  `~/.claude/projects/.../memory/project_soundscape_research_log.md`.
- **v0.6.5** (17/04/2026): correzione chirurgica della regressione
  v0.6.4. Il confronto blind di 4 brani (Truax Song of Songs I, Nono
  Fabbrica, Risset Sud, Nono Non consumiamo Marx) ha mostrato bias
  sistematico verso Truax Basilica: due brani su quattro (Fabbrica,
  Sud) attribuiti erroneamente perche' i prompt CLAP elx_14..17
  matchavano largo su risonanze metalliche tonali (laminatoi
  industriali, sintesi additiva MUSIC V) e la regola WSP-vs-GRM
  forzava Truax come alternativa. Rimossi elx_14..17 (vocabolario
  1.5 -> 1.6, 207 -> 203 prompt). Rimossa la regola di discriminazione
  WSP-vs-GRM dal prompt (WSP resta voce paritetica, non alternativa
  preferita). Mantenuta patch #1 "tag PANNs marginali" che aveva
  funzionato. Lezione: prompt CLAP troppo specifici matchano casi
  analoghi e producono bias.
- **v0.6.4** (17/04/2026): patch dal primo test blind del corpus
  Nottoli (Truax Basilica). Tre interventi: (a) regola PANNs marginali
  contraddittori (score < 0.40 su eventi concreti in contesto
  astratto vanno trattati come ipotesi, non fatti); (b) vocabolario
  CLAP v1.4 -> v1.5 con 4 prompt elx_14..elx_17 per campane
  trasformate/risonanze metalliche dilatate/oggetti tonali campanari;
  (c) tassonomia parentele stilistiche estesa con GRM/WSP-SFU/Fonologia
  RAI/WDR/ambient/granular/broadcast + regola di discriminazione
  WSP-vs-GRM per materiali granulari dilatati non-acusmatici-francesi.
  Driver: confronto track_01 Basilica in blind (prompt v0.6.3 aveva
  accettato PANNs "Train" come dato, perso attribuzione a Truax,
  ricaduto su parentele GRM).
- **v0.6.3** (17/04/2026): cambio di paradigma della lettura compositiva
  dell'agente. Riscrittura di `templates/agent_prompt.md` e
  `~/.claude/agents/soundscape-composer-analyst.md` con nuova struttura a 6
  sezioni: "Lettura drammaturgica" (apertura narrativa obbligatoria con
  metafora globale), "Scene sonore" (3-7 scene con titoli evocativi, non
  signature_label automatiche), "Binomi concettuali" (2-4 coppie che
  organizzano il senso), "Parentele stilistiche" (1-3 riferimenti motivati
  empiricamente, sostituisce Collocazione estetica), "Criticità tecniche"
  (invariata), "Suggerimenti compositivi" (drammaturgici e performativi,
  niente gesti DSP). Nuove regole: numeri solo a conferma interpretativa
  (max 1-2 per paragrafo), niente percentuali distributive nude, niente
  "Nessuna attribuzione plausibile" come frase esplicita, niente Q/dB/ms/
  plugin nei suggerimenti. Driver: confronto con analisi manuale di Air
  Piece di John Heineman (1970), salvata come
  `references/user_feedback/Air_Piece.md` come gold interpretativo.
  Feedback utente: lettura precedente troppo frammentata e tecnica,
  mancava interpretazione concettuale.
- **v0.6.2** (16/04/2026): hotfix PDF/agente emerso dalla validazione
  visuale di `audio7_report.pdf`. Tre regressori fixati in blocco: (a)
  celle timeline CLAP troncate a 35 char in `report_pdf.py::_build_clap_block`
  sostituite con word-wrap ReportLab nativo (via `styled_table._wrap`);
  (b) `schaeffer_detail` e `smalley_growth` v0.6.0 presenti in
  `clap_mapping.aggregate_academic_hints` ma non renderizzati da
  `report_pdf.py::_format_academic_hints`, aggiunti i due branch con
  rendering solo se confidence high/medium; (c) `agent_bridge.py::except
  subprocess.TimeoutExpired` non leggeva `e.stdout`/`e.stderr`, quindi
  su timeout perdevamo ogni diagnostica (audio7 mostrava "Stderr: ." dopo
  2 tentativi). Ora stdout/stderr parziali vengono decodificati e loggati
  a stderr. Bump `AGENT_TIMEOUT_S` 300→600 s per sostenere payload
  structure + narrative esteso. Driver: rilettura audio7_report.pdf
  16/04 sera.
- **v0.6.1** (16/04/2026): sub-comando `soundscape agent
  <summary.json>` per invocare solo l'agente compositivo su summary
  esistente (modalita' stdout + modalita' --pdf), evitando di rifare
  l'intera pipeline. Utile per iterare sul prompt agente.
- **v0.6.0** (16/04/2026): strumento compositivo step 1. Refactor
  narrative.py per-finestra delta-based (fix bug feature globali
  ripetute identiche, riduzione PDF da 10 a 3-5 pagine). Nuovo modulo
  scripts/structure.py per segmentazione strutturale via changepoint
  detection deterministico. Tassonomie compositive estese: Schaeffer
  TARTYP 22 sotto-tipi, Smalley 6 growth processes, Wishart utterance
  10 prompt nuovi. Timeline grafica matplotlib nel PDF. 14 test nuovi.
  Driver: chiarimento di scopo 16/04/2026 sera (riconoscimento eventi
  con terminologia accademica). Ricerca testi 16/04/2026 sui canoni
  Schaeffer/Smalley/Wishart/Landy.
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
