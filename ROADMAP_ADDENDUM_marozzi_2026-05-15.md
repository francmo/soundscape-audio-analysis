# Addendum ROADMAP - Caso Marozzi (ABA Macerata, 15/05/2026)

Documento di pianificazione che integra nove interventi emersi dal primo dossier dello Soundscape Annotation con gli studenti del corso PTSM (Macerata). Non sostituisce `ROADMAP.md`, lo affianca. Le proposte sono in fase di valutazione: nessun codice viene scritto in questo step.

Driver: confronto fra dossier studente (JSON 28 marker, scheda first-hand, audio 180.7 s ambiente bagno) e output skill (PDF tecnico + summary.json + agent_payload.json). Analisi cronologica completa in `~/Documents/aba-macerata-sprint-soundscape/_internal_rilettura_comparativa_marozzi.md`.

Versione di riferimento della skill: la ROADMAP segna v0.11.0, il file `summary.json` del caso riporta `version: 0.6.1` (probabile drift della stringa nel `_analyze_single` di `scripts/cli.py:185`). Verificare prima di iniziare se la stringa di versione è da aggiornare.

---

## Sommario

1. [Panoramica e cosa è già parzialmente coperto](#1-panoramica-e-cosa-è-già-parzialmente-coperto)
2. [Schede di valutazione dei nove interventi](#2-schede-di-valutazione-dei-nove-interventi)
   - 2.1 [Distinzione parlato diretto vs mediato](#21-distinzione-parlato-diretto-vs-mediato)
   - 2.2 [Trasparenza dei numerali nella narrative](#22-trasparenza-dei-numerali-nella-narrative)
   - 2.3 [Caveat PANNs per sezioni brevi](#23-caveat-panns-per-sezioni-brevi)
   - 2.4 [Citazione di onset puntuali nella narrative](#24-citazione-di-onset-puntuali-nella-narrative)
   - 2.5 [Sub-segmentazione PANNs sub-class](#25-sub-segmentazione-panns-sub-class-per-famiglie-geofoniche)
   - 2.6 [Marcatura di incertezza epistemica](#26-marcatura-di-incertezza-epistemica-nelle-inferenze-di-ambientazione)
   - 2.7 [Scheda §1 - split primo/secondo ascolto](#27-scheda-1-split-primo-e-secondo-ascolto)
   - 2.8 [Scheda §3 - mini-glossario operativo](#28-scheda-3-mini-glossario-operativo-keynote-signal-soundmark)
   - 2.9 [Scheda §6 - stencil di sintassi per ambiguità](#29-scheda-6-stencil-di-sintassi-per-le-ambiguità)
3. [Ordine consigliato di esecuzione e motivazione](#3-ordine-consigliato-di-esecuzione-e-motivazione)
4. [Decisioni di design su cui serve un parere prima di iniziare](#4-decisioni-di-design-su-cui-serve-un-parere-prima-di-iniziare)
5. [Rischi trasversali](#5-rischi-trasversali)
6. [Aggancio alla ROADMAP statistica v0.13-v0.17](#6-aggancio-alla-roadmap-statistica-v013-v017)

---

## 1. Panoramica e cosa è già parzialmente coperto

| Intervento | Già parzialmente implementato | Dove |
|---|---|---|
| 1. speech direct/mediated | No. Esiste solo `hum.interpret_in_context` che marca picchi hum come "armonica strumentale" se flatness < 0.05 e top-1 PANNs musicale. Non c'è nulla sul parlato. | `scripts/hum.py`, pattern da estendere |
| 2. trasparenza numerali | No nel PDF. Esiste in payload `clap.academic_hints.smalley_growth.pct` come float, ma `aggregate_academic_hints` non è documentato nel report. | `scripts/clap_mapping.py::aggregate_academic_hints`, `scripts/report_pdf.py` |
| 3. caveat PANNs su sezioni brevi | No. `structure._build_sections` non valuta `duration_s` per modulare la fiducia del `dominant_panns`. | `scripts/structure.py:326-377` |
| 4. citazione onset puntuali | Parziale a rovescio: filtro `<0.03` taglia silenzio, `<0.15` taglia "tenue". Già esiste qualificatore "tenue presenza di X". Manca la citazione per timestamp. | `scripts/narrative.py::_describe_panns:124-150` |
| 5. sub-segmentazione famiglie | No. `_extract_features_per_window` salva solo top-1 PANNs per finestra. La sub-class `Water tap` vs `Bathtub` esiste nei top globali ma non viene usata per segmentare. | `scripts/structure.py:171-198` |
| 6. marcatore incertezza epistemica | No esplicito. Esiste un sistema di confidence (`confidence: low/medium/high`) sui campi `academic_hints` ma non si traduce in marcatori linguistici nella narrative o nel prompt agente. | `scripts/narrative.py`, `templates/agent_prompt.md` |
| 7. scheda §1 split primo/secondo ascolto | No. Sezione attuale lascia 4-6 righe libere con suggerimento implicito. | `~/Documents/aba-macerata-sprint-soundscape/09_scheda_first_hand_template.md:23-25` |
| 8. scheda §3 mini-glossario | No. Distinzione keynote/signal/soundmark è solo testuale, senza esempi. | stesso file, §3 |
| 9. scheda §6 stencil | No. Esempio attuale è citazione illustrativa, non stencil. | stesso file, §6 |

`scripts/contextual_hints.py` è il **framework architetturalmente più adatto** per ospitare gli interventi 1 e 6: estende già il prompt agente con blocchi condizionati ai marker acustici. Non serve introdurre un nuovo modulo per quei due punti.

---

## 2. Schede di valutazione dei nove interventi

### 2.1 Distinzione parlato diretto vs mediato

**Sintesi del problema**: PANNs marca tutto come `Speech` senza distinguere voce in scena (microfono in presa diretta) da voce mediata da una parete, da uno speaker TV o radio, da una cornetta telefonica. La differenza è cruciale per l'inferenza di ambientazione: parlato diretto significa "persona in scena", parlato mediato significa "apparecchio in stanza adiacente o in scena". Nel caso Marozzi questa distinzione manca e l'agente legge il telegiornale TV come "qualcuno arriva sulla soglia".

| Aspetto | Dettaglio |
|---|---|
| **File / funzioni** | Nuovo modulo `scripts/speech_mediation.py` con funzione `classify_speech_mediation(waveform, sr, panns_segments)`. Hook in `scripts/cli.py::_analyze_single` step [6/10] subito dopo `semantic.semantic_summary` quando classifier ha frame Speech > 5% dominant_frames. Output esposto come campo `semantic.speech_mediation` in summary e propagato in `agent_payload.signature.speech_mediation` |
| **Approccio tecnico (proposta)** | Per ogni segmento PANNs con top-1 = Speech, calcolare: (a) rolloff 85% (parlato TV/radio filtrato perde sopra 3-4 kHz); (b) low-pass shoulder slope fra 2.5 e 5 kHz (decadimento monotonico marcato è firma di filtro acustico passivo, parete); (c) HNR locale (parlato in presa diretta ha rapporto armonica/rumore più alto); (d) stazionarietà nel tempo (telegiornale = presenza continua per blocchi lunghi, persona = pause respiratorie). Soglia composita produce label `direct / mediated / uncertain` + confidence |
| **Complessità** | 4-6 ore. La parte spettrale e di stazionarietà è meccanica (numpy/librosa). La parte di calibrazione delle soglie richiede 4-6 file di confronto (parlato diretto in stanza piccola, parlato TV filtrato dalla parete, parlato telefonico, parlato all'aperto). Mezz'ora di test sui file Marozzi e su altri due o tre file domestici già disponibili |
| **Dipendenze** | Nessuna verso altri 8 interventi. Beneficia il punto 6 (marcatura incertezza): se Speech è marcato mediated, l'agente può evitare di costruire scena "persona in scena" |
| **Decisioni di design aperte** | Vedere [§4.1](#41-euristica-deterministica-vs-classificatore-dedicato-per-speech-mediation) |
| **Rischi** | Falsi positivi su parlato in stanza grande (riverbero lo allontana dall'asciutto e può somigliare a parlato filtrato). Su materiale acusmatico con voce trasformata, classificazione `direct/mediated` non ha senso semantico: serve fallback a `uncertain` su flatness > 0.3 |

---

### 2.2 Trasparenza dei numerali nella narrative

**Sintesi del problema**: numerali come "dilation domina al 66%" appaiono nella narrative compositiva dell'agente senza riferimento a metodo, finestra, score. Il lettore non può verificare. È pseudo-precisione. Il numero **esiste** nel payload (`clap.academic_hints.smalley_growth.pct`), ma il suo metodo di calcolo (somma pesata di score CLAP cosine su top-20 tag mappati alla categoria growth) non è scritto da nessuna parte nel report.

| Aspetto | Dettaglio |
|---|---|
| **File / funzioni** | (a) `scripts/clap_mapping.py::aggregate_academic_hints`: aggiungere campi `methodology: str` e `window_seconds: float|None` (None se globale) accanto a `pct` per ogni categoria; (b) `scripts/report_pdf.py`: nuova sezione "Appendice metodologica" alla fine del PDF prima del colofone, tabella `categoria | metodo | parametri | finestra`; (c) `templates/agent_prompt.md`: aggiunta regola "ogni numerale citato deve essere accompagnato da `[App. A]` se proviene da `clap.academic_hints`, oppure tradotto in qualificatore qualitativo (`prevale`, `tendenza`, `predominante`) se non vuoi cit. l'appendice". (d) `scripts/agent_payload.py::build_agent_payload`: passare la stringa `methodology` direttamente nei campi `academic_hints` perché l'agente possa decidere quando trasformare |
| **Approccio alternativo (più conservativo)** | Eliminare i numerali dalla narrative agente per default. Regola di prompt: "non scrivere percentuali nude, trasforma in qualificatori (`tendenza`, `prevale`, `domina chiaramente`, `oscilla fra X e Y`)". Niente appendice, niente metodo. Pro: zero rischio di rumore tipografico. Contro: perde l'informazione quantitativa per il lettore esperto |
| **Complessità** | (a) appendice metodologica nel PDF: 3-4 ore (struttura tabella + sezione PDF ReportLab + agganciamento referenze `[App. A.X]`). (b) variante conservativa: 1-2 ore (solo modifica `agent_prompt.md`) |
| **Dipendenze** | Nessuna stretta. Sinergico col punto 6 (marcatore incertezza): un numerale con metodologia documentata è già più trasparente di uno nudo, ma resta asserzione; combinato con marker di confidenza diventa "ipotesi quantitativa con metodo e grado di certezza" |
| **Decisioni di design aperte** | Vedere [§4.2](#42-numerali-narrative-appendice-metodologica-o-soppressione) |
| **Rischi** | Se si sceglie l'appendice, il PDF cresce di 1-2 pagine e il lettore non specialista può non capire la tabella. Se si sceglie la soppressione, si perde l'aggancio empirico delle frasi compositive |

---

### 2.3 Caveat PANNs per sezioni brevi

**Sintesi del problema**: la sezione S5 del caso Marozzi (0.74 s, impulso meccanico finale) è stata classificata `Music` come dominante perché il grafo CNN14 confonde impulsi percussivi armonici con strumenti musicali. Sotto i 2 s di durata, il dominant PANNs è statisticamente inaffidabile (1 frame da 1s con un singolo top-1).

| Aspetto | Dettaglio |
|---|---|
| **File / funzioni** | `scripts/structure.py::_build_sections:326-377`: aggiungere campo `dominant_panns_confidence: str` (`high`/`medium`/`low`) calcolato sulla base di `duration_s` e numero di frame PANNs intersecati. Sotto 2s: forzare confidence=low, mostrare top-3 PANNs invece del solo top-1. Se la sezione coincide con un onset isolato seguito da decadimento (vedere `spectral.onset_analysis`), aggiungere flag `signature_label = "impulso + decadimento"` indipendentemente dal PANNs (regola di overrid eura) |
| **Hook PDF** | `scripts/report_pdf.py` rendering tabella structure: quando confidence=low marcare in corsivo grigio il valore `dominant_panns` con asterisco e nota a piè di tabella "sezione troppo breve per classificazione robusta" |
| **Hook agente** | `templates/agent_prompt.md` sezione "Come usare `structure` (v0.6.0)": aggiungere "se `dominant_panns_confidence == low`, non citare il dominant come fatto; tratta la sezione come *impulso* o *coda* senza assegnarle Krause antropofonia/biofonia/geofonia". Il prompt agente già contempla in modo generale "tag PANNs marginali contraddittori" (v0.6.4), questo è una sua estensione su asse temporale |
| **Complessità** | 2-3 ore. La logica di confidence è una tabella su durata. Il rendering corsivo è già supportato da `report_pdf._build_clap_block` (precedente v0.6.2). Test su due fixture: file Marozzi (S5 = 0.74s) + uno qualunque con sezione > 30s come controllo (confidence=high) |
| **Dipendenze** | Sinergia con punto 5 (sub-segmentazione): se 5 è implementato, le sezioni risultanti saranno più granulari e qualcuna potrebbe scendere sotto 2s. Quindi 3 va dopo 5 oppure considerati insieme |
| **Decisioni di design aperte** | Vedere [§4.3](#43-confidence-panns-su-durata-soglia-fissa-2s-o-statistica) |
| **Rischi** | Bassissimo. Cambia un valore strutturale che viene già consumato dal PDF. Test minimale su `tests/test_structure.py` (probabile estensione di una fixture esistente) |

---

### 2.4 Citazione di onset puntuali nella narrative

**Sintesi del problema**: la narrative cita PANNs aggregati per finestra di 30s, scartando i tag con score < 0.15 (filtro in `narrative._describe_panns`). Su file domestici molti onset rilevanti hanno score 0.03-0.15 (Animal 0.045 per cane abbaiante a 00:38, Door 0.058 per chiusura porta, ecc.). Vengono saltati. Marozzi li annota a mano. Il filtro 0.15 va bene per opere d'arte acusmatiche, è troppo aggressivo per registrazioni didattiche domestiche.

| Aspetto | Dettaglio |
|---|---|
| **File / funzioni** | `scripts/narrative.py::_describe_panns:124-150`: già contempla `0.03-0.15` come "tenue presenza" con qualificatore, ma di default filtra a 0.15 con `if score > 0.15`. Modificare per emettere tutti i tag con score > 0.03 come "tenue presenza", non solo i top-3. Aggiungere un secondo blocco descrittivo nella narrative per finestra che cita gli onset puntuali della finestra con timestamp e label se score > 0.03 |
| **Approccio alternativo (timestamp puntuali)** | Estendere `spectral.onset_analysis` per ritornare anche la lista di timestamp degli onset (oggi ritorna solo `events_count`, `events_per_sec`, `density_label`). Poi in `narrative.build_full_narrative` correlare i timestamp degli onset con il top-K PANNs della finestra temporale che li contiene per dare frasi tipo "a 00:38 emerge una tenue presenza di animale (Animal 0.045)". Più costoso ma compositivamente più ricco |
| **Complessità** | (a) variante abbassamento soglia: 1-2 ore (1 funzione modificata + test di non regressione sui blind benchmark per misurare se la verbosità aumenta troppo). (b) variante onset+timestamp: 4-6 ore (estensione `onset_analysis` + nuova funzione `correlate_onset_with_panns` + integrazione narrative) |
| **Dipendenze** | Sinergia col punto 3 (caveat sezioni brevi): se la soglia scende a 0.03 e un onset isolato emerge in una sezione di 0.74s come S5, l'integrazione fra punto 3 e punto 4 deve dichiarare onset come "impulso isolato a 03:00, possibile decadimento metallico", non come "tenue presenza di Music a 03:00" |
| **Decisioni di design aperte** | Vedere [§4.4](#44-onset-soglia-statica-o-modalita-didattica-vs-acusmatica) |
| **Rischi** | Verbosità della narrative aumenta su file domestici (molti onset tenui). Potrebbe regredire i blind benchmark dei brani gold acusmatici (dove il filtro 0.15 protegge dal rumore di classificazione). Mitigazione: flag `--narrative-mode` con valori `acousmatic` (filtro 0.15 attuale) / `didactic` (filtro 0.03 + onset puntuali) / `full` (entrambi se durata < 5 min) |

---

### 2.5 Sub-segmentazione PANNs sub-class per famiglie geofoniche

**Sintesi del problema**: il changepoint detection lavora sul top-1 PANNs per finestra. Su S3 del caso Marozzi (70-150s, 80s), il top-1 resta `Water` per tutta la durata, anche se i top-3 cambiano fra doccia (`Water` + `Water tap, faucet` + `Bathtub`) e lavandino (`Water` + `Sink (filling)` + `Water tap, faucet`). Risultato: una sola sezione "Acqua continua 80s" dove ce ne sono due semanticamente distinte.

| Aspetto | Dettaglio |
|---|---|
| **File / funzioni** | `scripts/structure.py::_extract_features_per_window:171-198`: aggiungere `panns_top3` (lista di 3 nomi) accanto a `panns_top1`. `_detect_changepoints:201-286`: includere un termine di gradiente categoriale anche su `panns_top3` (Jaccard distance fra finestre adiacenti su top-3). Soglia adattiva. `_build_sections`: dopo la segmentazione globale, applicare un secondo passo di sub-segmentazione interna per sezioni con `krause in ("geofonia", "biofonia")` e durata > 30s, usando solo PANNs sub-class come segnale (escludere RMS e centroide che oscillano poco entro famiglie acquatiche o vocali). Nuove sezioni con `id = "S3a", "S3b"` |
| **Approccio alternativo** | Lasciare invariato `structure.py` e demandare la sub-segmentazione alla narrative: in `narrative.build_full_narrative`, se due finestre adiacenti hanno top-1 PANNs uguale ma top-2 diverso (e top-2 sale di score sopra soglia 0.10), emettere segnalazione "transizione interna a X" senza modificare il record `structure.sections`. Meno invasivo, meno coerente |
| **Complessità** | (a) variante structure: 6-8 ore (modifica changepoint + nuovi test + verifica timeline PNG + propagazione a `agent_payload.structure.sections`). (b) variante narrative: 2-3 ore. Mio consiglio: variante structure, perché il punto 5 è strutturale e va al cuore dell'API `structure` |
| **Dipendenze** | Sinergia con punto 3 (caveat brevi): sub-segmentazione può produrre sezioni < 2s che andranno marcate confidence=low. Il punto 3 deve essere implementato prima o contestualmente |
| **Decisioni di design aperte** | Vedere [§4.5](#45-sub-segmentazione-su-quale-jaccard-e-su-quale-soglia-di-score-panns) |
| **Rischi** | Possibile esplosione del numero di sezioni su file lunghi naturalisti (5h di registrazione dawn chorus). Per evitare: cap a max 12 sub-sezioni totali. Vincolo `STRUCTURE_MAX_SECTIONS=8` attuale va innalzato o duplicato in `STRUCTURE_MAX_SUB_SECTIONS_PER_PARENT=3` |

---

### 2.6 Marcatura di incertezza epistemica nelle inferenze di ambientazione

**Sintesi del problema**: l'agente scrive "soglia domestica" come asserzione. La frase è inferenza probabilistica da indizi acustici (porte, parlato), non dato. Manca un marcatore esplicito di confidenza ("l'ambientazione si configura plausibilmente come...", "gli indizi suggeriscono..."). La forma dichiarativa è appropriata su attribuzione forte (high confidence), la forma ipotetica su attribuzione debole (low confidence).

| Aspetto | Dettaglio |
|---|---|
| **File / funzioni** | (a) `scripts/agent_payload.py::_build_signature`: aggiungere campo `inference_confidence: dict` con due indici: `panns_concentration` (varianza top-5 dei `top_dominant_frames.pct`) e `clap_concentration` (varianza score dei top-5 CLAP). Concentrazione alta = pochi tag dominanti = high confidence. Concentrazione bassa = tag dispersi = low confidence. (b) `templates/agent_prompt.md`: nuova sezione "Tono epistemico delle inferenze di ambientazione": tabella con range di concentrazione e marcatori linguistici corrispondenti ("la scena è X" vs "l'ambientazione si configura plausibilmente come X" vs "alcuni indizi suggerirebbero X"). (c) `scripts/contextual_hints.py`: nuova regola `_check_low_confidence_scene` che attiva un blocco di prompt aggiuntivo se entrambe le concentrazioni sono basse |
| **Approccio alternativo (più semplice)** | Solo modifica `templates/agent_prompt.md` con regola generale "le inferenze di ambientazione (scena, luogo, contesto) devono usare marcatori di ipotesi (`plausibilmente`, `indizi suggeriscono`, `compatibile con`), non dichiarazioni assertive". Niente meccanismo numerico. Pro: zero codice, regola di prompt. Contro: regola di prompt difficile da rendere robusta senza ancoraggio quantitativo |
| **Complessità** | (a) approccio completo: 4-6 ore (calcolo concentrazione + regola prompt + regola contextual_hints + test). (b) approccio solo prompt: 1 ora |
| **Dipendenze** | Beneficia 2 (trasparenza numerali), come spiegato sopra. Posiziona il framework di confidence che il punto 2 può sfruttare per scegliere fra "App. A.X" vs qualificatore qualitativo |
| **Decisioni di design aperte** | Vedere [§4.6](#46-confidenza-narrative-formula-aritmetica-o-soglie-discrete) |
| **Rischi** | Su file molto buoni con alta concentrazione PANNs (es. dawn chorus puro), forzare marcatori di ipotesi suona artificioso. Mitigare con scala continua, non binaria |

---

### 2.7 Scheda §1 split primo e secondo ascolto

**Sintesi del problema**: gli studenti tendono a scrivere un paragrafo unico mescolando impressioni di primo e secondo ascolto. Lo splitting in due sotto-campi forza il doppio passaggio.

| Aspetto | Dettaglio |
|---|---|
| **File / funzioni** | `~/Documents/aba-macerata-sprint-soundscape/09_scheda_first_hand_template.md:23-25` (fuori dal repo skill). Modifica markdown + rigenerazione DOCX/PDF/HTML con pipeline esistente (`Pandoc` o equivalente già usato per `09_scheda_first_hand_template.docx`, .html, .pdf). Verificare quale pipeline produce i tre formati. Probabile script in `~/Documents/aba-macerata-sprint-soundscape/` |
| **Approccio** | Cambiare §1 in §1.a "Primo ascolto (5 min, senza prendere appunti)" + §1.b "Secondo ascolto (10 min, in cuffia, con appunti)". Tre righe ciascuno, prompt esplicito |
| **Complessità** | 30 min. Edit template MD + comando di rigenerazione DOCX/PDF/HTML |
| **Dipendenze** | Nessuna verso gli altri otto |
| **Decisioni di design aperte** | Nessuna grave. Eventualmente accordarsi sulle durate consigliate (5+10 vs 3+7 vs lasciare libero) |
| **Rischi** | Nessuno, modifica reversibile |

---

### 2.8 Scheda §3 mini-glossario operativo keynote signal soundmark

**Sintesi del problema**: due studenti su due hanno applicato male la triade Schafer. La distinzione teorica non basta, serve esempio operativo inline.

| Aspetto | Dettaglio |
|---|---|
| **File / funzioni** | Stesso file `09_scheda_first_hand_template.md:40-58` (sezione §3). Aggiungere riquadro a inizio §3 con esempio canonico |
| **Approccio** | Inserire prima del prompt operativo un blockquote markdown di tre righe con un esempio costruito su soundscape urbano: «Keynote: ronzio continuo del traffico veicolare in lontananza. Signal event: clacson che emerge sul traffico. Soundmark: campane di una chiesa del centro storico, riconoscibili come identità del quartiere» |
| **Complessità** | 20 min. Edit + rigenerazione formati |
| **Dipendenze** | Nessuna |
| **Decisioni di design aperte** | Vedere [§4.7](#47-mini-glossario-uno-o-due-esempi-rurale-urbano) |
| **Rischi** | Nessuno |

---

### 2.9 Scheda §6 stencil di sintassi per le ambiguità

**Sintesi del problema**: gli studenti scrivono auto-valutazioni del processo invece di casi specifici di oscillazione fra termini del vocabolario. L'esempio attuale è citato come illustrazione, non come stencil. Diventa uno stencil esplicito da copiare e completare.

| Aspetto | Dettaglio |
|---|---|
| **File / funzioni** | `09_scheda_first_hand_template.md:89-98` (sezione §6) |
| **Approccio** | Sostituire l'esempio attuale con un blocco markdown codificato come stencil: ```«Fra [mm:ss] e [mm:ss] ho oscillato fra [tassonomia.termineA] e [tassonomia.termineB]. Ho scelto [A] perché [motivo]. Dubbio resta perché [motivo].»```. Aggiungere due esempi di output atteso (uno domestico, uno urbano) per ancorare l'astrazione |
| **Complessità** | 30 min |
| **Dipendenze** | Nessuna |
| **Decisioni di design aperte** | Vedere [§4.7](#47-mini-glossario-uno-o-due-esempi-rurale-urbano) |
| **Rischi** | Nessuno |

---

## 3. Ordine consigliato di esecuzione e motivazione

### Fase 0 - Setup template (sblocco didattica)

| # | Intervento | Ore | Perché qui |
|---|---|---|---|
| 7 | Split §1 primo/secondo ascolto | 0.5 | Modifica template, sblocca il prossimo studente in pipeline |
| 8 | Mini-glossario §3 | 0.3 | Stessa pipeline, stessa rigenerazione |
| 9 | Stencil §6 | 0.5 | Stessa pipeline |

**Totale Fase 0**: 1-2 ore. Si chiude in una mattinata. I tre interventi sui template sono **non-bloccanti** rispetto agli altri sei, ma sono i più formativamente urgenti perché impattano sulla qualità degli artefatti che i prossimi studenti consegneranno. Cominciare da qui.

### Fase 1 - Framework di confidenza (sostrato per il resto)

| # | Intervento | Ore | Perché qui |
|---|---|---|---|
| 6 | Marcatura di incertezza epistemica | 4-6 | Introduce campo `inference_confidence` in payload signature e i marcatori linguistici nel prompt agente. È il **sostrato** che gli interventi 2 e 3 useranno per modulare il loro output |
| 3 | Caveat PANNs su sezioni brevi | 2-3 | Una volta che esiste il framework `confidence: high/medium/low`, applicarlo alla durata sezione è un'estensione lineare. Modifica `structure._build_sections` |

**Totale Fase 1**: 6-9 ore. Lascia in piedi una skill che, anche senza altri interventi, già marca incertezza nei punti critici.

### Fase 2 - Riconoscimento eventi più fine (sostrato per la narrative ricca)

| # | Intervento | Ore | Perché qui |
|---|---|---|---|
| 5 | Sub-segmentazione PANNs sub-class | 6-8 | Cambia struttura delle sezioni: più granulare. Va prima di 4 perché modifica `structure.sections` che la narrative legge |
| 1 | Speech direct/mediated | 4-6 | Si appoggia all'infrastruttura PANNs già in pipeline. Va prima di 4 perché classifica il parlato in modo che la narrative possa qualificarlo correttamente quando lo cita |

**Totale Fase 2**: 10-14 ore. Dopo questa fase la struttura dell'analisi è più ricca di indizi che la narrative può citare.

### Fase 3 - Narrative ricca e trasparente (consuma tutto il sostrato)

| # | Intervento | Ore | Perché qui |
|---|---|---|---|
| 4 | Citazione onset puntuali | 1-6 (a seconda della variante) | Beneficia di 5 (sub-segmentazione: gli onset sono ora attribuiti a sub-sezioni più precise) e 1 (Speech mediated: gli onset Speech sono qualificati correttamente). Va dopo |
| 2 | Trasparenza numerali nella narrative | 1-4 (a seconda della variante) | Ultimo perché beneficia di 6 (può scegliere App. A.X vs qualificatore in base a confidence) e di tutto quello che è stato fatto prima (i numerali stessi possono essere più ricchi se 5 e 1 hanno popolato campi nuovi nel payload) |

**Totale Fase 3**: 2-10 ore a seconda delle scelte di design.

### Totale stimato

| Variante | Ore di sessione |
|---|---|
| Minimale (varianti conservative) | 18-25 |
| Massima (varianti complete) | 30-40 |

In termini calendariali con un ritmo di 2-3 ore di sessione attiva al giorno, la roadmap completa è 8-15 giorni di lavoro distribuito.

### Perché questo ordine

- **Template prima di codice**: pipeline didattica già attiva, costo marginale zero, beneficio formativo immediato sui prossimi due studenti.
- **Framework di confidenza prima dei consumatori**: il punto 6 introduce un linguaggio (`high/medium/low`) e una metrica (`inference_confidence`); i punti 3, 2 li usano. Se si invertisse, si avrebbero due meccanismi di confidence inconsistenti.
- **Sub-segmentazione e mediation prima della narrative**: 5 e 1 producono dati che 4 e 2 citano. Se si invertisse, la narrative ricca dovrebbe essere riscritta una seconda volta.
- **Onset prima dei numerali**: 4 è più semplice da modulare in base a confidence (è già scrittura prosaica), 2 richiede decisioni più profonde su PDF e prompt; meglio chiudere prima quello più tattile.

---

## 4. Decisioni di design su cui serve un parere prima di iniziare

### 4.1 Euristica deterministica vs classificatore dedicato per speech mediation

Tre opzioni:

| Opzione | Pro | Contro |
|---|---|---|
| A. Euristica numpy/librosa pura su 4 feature (rolloff, shoulder slope, HNR, stazionarietà) con soglie calibrate | Deterministico, leggibile, integrabile in 4-6 ore, nessuna nuova dipendenza, nessun checkpoint | Soglie vanno calibrate su corpus eterogeneo, rischio overfit al caso Marozzi |
| B. Classifier piccolo dedicato (CNN poco profonda o gradient boosting su MFCC) addestrato su corpus annotato | Più robusto teoricamente | Richiede corpus annotato (oggi non c'è), addestramento, checkpoint, fragile su domini OOD; allunga il tempo a 20-40 ore; non giustificato per un singolo caso |
| C. PANNs frame-level già esistente con regola: se top-2 contiene `Television` o `Radio` o `Telephone` o `Loudspeaker`, marca come mediated; altrimenti direct | Zero codice nuovo, riusa output esistente | AudioSet ha label `Television` e `Radio` ma vengono raramente top in materiale domestico misto. Probabile recall basso. Vale la pena testarlo come baseline |

**Mio consiglio**: opzione A (euristica) come baseline + opzione C come override quando PANNs ha top-1 fra le label mediatiche. Combinazione robusta in 4-6 ore. Vale il tuo parere.

### 4.2 Numerali narrative appendice metodologica o soppressione

Tre opzioni:

| Opzione | Pro | Contro |
|---|---|---|
| A. Appendice metodologica nel PDF, ogni numerale citato dall'agente ha `[App. A.X]` | Trasparenza massima, supporta lettori esperti | PDF cresce, regola di prompt complicata da rendere robusta |
| B. Soppressione dei numerali nudi, qualificatori obbligatori | Pulizia massima, regola di prompt semplice | Perde informazione quantitativa |
| C. Compromesso: numerali permessi solo se nella forma "X (categoria di metodo)" tipo "dilation prevale chiaramente (CLAP cosine top-20)", senza appendice ma con suffisso metodo inline | Compromesso ragionevole | Frase più lunga del normale |

**Mio consiglio**: opzione C. Aggiunge ancora metodologica senza esplodere il PDF. Una decisione editoriale è meno costosa di una sezione PDF nuova. Vale il tuo parere.

### 4.3 Confidence PANNs su durata soglia fissa 2s o statistica

Due opzioni:

| Opzione | Pro | Contro |
|---|---|---|
| A. Soglia fissa: < 2s → confidence=low, < 5s → confidence=medium, ≥ 5s → confidence=high | Semplice, deterministico, replicabile | 2s è euristica empirica, non statistica |
| B. Statistico: confidence = numero di frame PANNs dominanti / numero atteso per durata | Più solido teoricamente | Richiede prior empirico, soglie da calibrare |

**Mio consiglio**: opzione A nella prima implementazione, opzione B candidata a v0.13+ con paired t-test. Vale il tuo parere.

### 4.4 Onset soglia statica o modalita didattica vs acusmatica

Tre opzioni:

| Opzione | Pro | Contro |
|---|---|---|
| A. Abbassare la soglia globale da 0.15 a 0.03 | Una sola regola, semplice | Regressione probabile sui blind benchmark del corpus golden acusmatico |
| B. Flag CLI `--narrative-mode acousmatic / didactic / auto` con soglie diverse | Flessibile, esplicito | Una scelta in più che l'utente deve fare |
| C. Auto-rilevamento: se duration < 5 min e flatness > 0.1 e PANNs top-1 contiene categorie domestic (Inside small room, Domestic sounds), modalità didactic; altrimenti acousmatic | Automatico, intelligente | Euristica può sbagliare, richiede test |

**Mio consiglio**: opzione B (flag esplicito con default `auto` che usa la logica di C). Salva la backward compatibility, rende il flag opt-in. Vale il tuo parere.

### 4.5 Sub-segmentazione su quale jaccard e su quale soglia di score PANNs

Decisione tecnica: il gradiente categoriale interno (Jaccard distance fra top-3 PANNs adiacenti) richiede una soglia. Proposta iniziale 0.5 (50% di sovrapposizione fra top-3 adiacenti → no cut, sotto 50% → cut potenziale). Anche soglia di score per inclusione nel top-3: 0.05 (sotto è rumore). Sono numeri da calibrare empiricamente su S3 Marozzi e su altri 2-3 file domestici. Vuoi che li proponga come default modificabili in `config.py` o decidiamo prima sul caso Marozzi?

### 4.6 Confidenza narrative formula aritmetica o soglie discrete

Per `panns_concentration` proposta: `concentrazione = top1_pct / (top1_pct + top2_pct + top3_pct)`. Range 0.33 (dispersione massima) - 1.0 (top1 unico). Soglie discrete: < 0.5 = low confidence, 0.5-0.75 = medium, > 0.75 = high. Analogo per CLAP ma con score cosine. Va bene così o preferisci una formula informazionale (entropia di Shannon normalizzata)? L'entropia è più solida teoricamente ma meno leggibile. Vale il tuo parere.

### 4.7 Mini-glossario uno o due esempi rurale urbano

Per la scheda §3, opzione di un solo esempio (urbano canonico) o di due esempi (urbano + rurale) per coprire i due domini più ricorrenti negli sprint. Due esempi sono più ricchi ma rendono il riquadro più lungo. Personalmente preferirei uno solo (urbano) ben costruito + nota inline che invita lo studente a costruirne uno per il proprio file. Vale il tuo parere.

---

## 5. Rischi trasversali

- **Backward compatibility del payload agente**: aggiungere campi `inference_confidence`, `speech_mediation`, `dominant_panns_confidence`, sub-sezioni `S3a/S3b`, metadata `methodology` cambia il payload JSON. Gli agenti subagent che leggono il payload (`soundscape-composer-analyst`) vanno aggiornati. Verificare `~/.claude/agents/soundscape-composer-analyst.md` e allineare al prompt versione nuova.
- **Tabelle nel PDF**: ReportLab non gestisce nativamente tabelle che si spezzano fra pagine. Le tabelle nuove dell'appendice metodologica vanno dimensionate per una pagina A4 oppure suddivise.
- **Test suite**: la skill ha test su ogni modulo (`tests/`). Modifiche a `structure.py`, `narrative.py`, `agent_payload.py` richiedono aggiornamento dei test e probabilmente nuove fixture (file Marozzi è un buon candidato di fixture didattica, ma è un file privato dello studente: serve permesso o file sintetico equivalente).
- **Stocastica del sub-agent**: ogni modifica al prompt agente o al payload va validata su corpus di 4-5 brani con N ≥ 3 run per misurare se il delta è dentro il noise floor stocastico (±15-20 punti documentato). Se non è dentro, il delta è significativo. Questa procedura è già in `~/soundscape-training/tools/blind_benchmark_cycle.py` (dalla ROADMAP).

---

## 6. Aggancio alla ROADMAP statistica v0.13-v0.17

La ROADMAP principale prescrive che da v0.13 in poi ogni release dichiari un "miglioramento" solo se l'intervallo di confidenza al 95% via paired t-test non si sovrappone con la release precedente. I nove interventi di questo addendum vanno classificati su due assi:

| Asse | Qualifica del cambiamento | Necessità di paired t-test |
|---|---|---|
| Qualitativo (cambia il *tipo* di output, non il *quanto*) | 7, 8, 9 (template); 2 variante C (numerali con metodo inline); 6 variante semplice (regola di prompt) | No: il cambiamento non è confrontabile per score, è cambio di natura |
| Strutturale (cambia dati nel payload o nel report, non la qualità della lettura) | 3 (confidence sezioni brevi), 5 (sub-segmentazione) | No, ma serve verifica di non regressione su 4-5 brani |
| Quantitativo (può migliorare o peggiorare score benchmark sub-agent) | 1 (speech mediation), 4 (onset citation), 6 variante completa (confidence numerica) | Sì: paired t-test N=5 minimo, regola della ROADMAP statistica |

Quindi solo gli interventi quantitativi 1, 4 e 6 (variante completa) vanno sotto il regime statistico. Gli altri sei sono modifiche qualitative o strutturali, non producono delta su benchmark Jaccard e possono essere shippati senza paired test, purché i blind cycle confermino assenza di regressione su brani gold (corpus iteration v0.10).

Per questi tre, suggerisco di aggregare il loro impatto in un'unica release statisticamente validata: **v0.12.5 - integrazione caso Marozzi** invece di tre release separate. Una sola misura paired t-test, un solo CI 95% da pubblicare nel CHANGELOG.

Questa scelta lascia comunque libera la decisione finale: se preferisci versioning più granulare con release indipendenti, ogni release a impatto quantitativo paga il suo paired t-test e il proprio noise floor.
