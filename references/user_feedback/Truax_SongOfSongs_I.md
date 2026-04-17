# Feedback - Barry Truax, *Song of Songs I "Morning"* (1992)

## 1. Identificazione

- **File**: `track_02.mp3` (copia anonimizzata, soundscape-training/audio_blind/)
- **Versione skill che ha prodotto il report**: v0.6.5 con `--speech`
- **Data feedback**: 2026-04-17
- **Contesto del brano**: Barry Truax, *Song of Songs I "Morning"* (1992), primo movimento di un ciclo di 4 per oboe d'amore, corno inglese, due nastri digitali e immagini al computer. Materiale multi-sorgente di field recording elaborato con sistema PODX:
  - Registrazioni vocali del *Cantico dei Cantici* biblico (Norbert Ruebsaat, Thecla Schiphorst).
  - Monaco che canta con campane del monastero SS. Annunziata di Amelia (Italia).
  - Cicale e grilli del sito del monastero italiano.
  - Dawn Chorus bretone (registrazioni WSP/SFU).
  - Ruscello e fuoco scoppiettante (Robert MacNevin).
  - Cantillazione ebraica tradizionale come refrain.
  - Tecnica: time-stretching + harmonizing con granular synthesis real-time, ~250 eventi/sec per coppia stereo.
- **Gold analitico**: `Nottoli-02-Truax-SongOfSongs-I/analisi-sfu.md` (sfu.ca/~truax/songs.html).

## 2. PANNs

### Top-1 globale

- **Skill dice**: `Music` (score 0.60)
- **Reale**: parzialmente corretto. Come in *Basilica*, il classificatore cattura il risultato post-processing ("musica") ma la genealogia multi-sorgente (voce umana + cicale + uccelli + campane + ruscello + fuoco) è in gran parte persa. È notevolmente meglio che su *Basilica*: qui PANNs **coglie** Speech (0.24, frame dominante 16%), Wind instrument/Flute/Violin (0.15/0.11/0.06), Shofar (0.045, 10° posto!). La traccia del materiale sorgente emerge più chiaramente perché il processing è meno aggressivo del time-stretch 20x di *Basilica*.

### Top-10 globali

| Posizione | Etichetta PANNs | Score | Valutazione |
|-----------|-----------------|-------|-------------|
| 1 | Music | 0.5977 | parziale (risultato, non genealogia) |
| 2 | Speech | 0.2443 | **corretto**, c'è effettivamente parlato inglese |
| 3 | Musical instrument | 0.2017 | corretto (flauto, oboe d'amore, corno inglese) |
| 4 | Vehicle | 0.1557 | **errato, falso positivo** (sistemico) |
| 5 | Wind instrument, woodwind | 0.1525 | **corretto** (flauto/oboe/corno inglese come orchestrazione dichiarata) |
| 6 | Flute | 0.1067 | **corretto** (strumento presente nella scrittura del brano) |
| 7 | Violin, fiddle | 0.0637 | parziale (potrebbe essere residuo di armonici) |
| 8 | **Shofar** | 0.0451 | **sorprendentemente corretto**: il gold dichiara "cantillazione ebraica tradizionale come refrain", e lo shofar è strumento rituale ebraico |
| 9 | Inside, small room | 0.0441 | OK (contesto chiesa/monastero) |
| 10 | Environmental noise | 0.0417 | OK |

### Frame dominanti

- **Skill**: Music 68%, Speech 16%, Environmental noise 8%, Wind instrument 4%, Silence 4%.
- **Reale**: coerente con il brano. La presenza di Speech al 16% è giustamente alta (testo biblico cantato). Wind instrument 4% coerente con l'orchestrazione (oboe d'amore, corno inglese, flauto).
- **Gap**: mancano Chant/Choir/Singing (canto monacale), Bell (campane monastero), Cricket/Insect (cicale), Bird/Dawn chorus (uccelli bretoni), Stream/Water (ruscello). Una parte di queste sorgenti è forse nascosta dal processing denso (250 eventi/sec), un'altra parte è un gap reale della rete per materiali compositi.

## 3. CLAP

### Top-10 globali

| Posizione | Prompt italiano | Score | Pertinente? | Note |
|-----------|-----------------|-------|-------------|------|
| 1 | Voce umana manipolata acusmatica | 0.277 | **sì**, coglie il trattamento granulare della voce |
| 2 | Accumulo granulare stocastico | 0.238 | **sì**, tecnica di Truax (granular PODX) |
| 3 | **Acqua del rubinetto che scorre** | 0.235 | **no, allucinazione ricorrente** (caso scuola v0.7.0) |
| 4 | Preghiera collettiva sussurrata in chiesa | 0.232 | **sì parzialmente**, c'è voce orante ma non sussurrata (cantata) |
| 5 | Musica elettronica ambient | 0.222 | parziale |
| 6 | Voci umane lontane senza parole distinte | 0.219 | sì |
| 7 | Paesaggio sonoro di borgo rurale italiano | 0.213 | sì, **corretto geograficamente** (Amelia, Italia) - italo-specifico flaggato correttamente in corsivo |
| 8 | Profilo dinamico in morphing continuo | 0.208 | sì |
| 9 | Time-stretch estremo di oggetto concreto | 0.201 | sì |
| 10 | Spazializzazione sonora multicanale | 0.200 | OK (il brano è stereo ma il gold menziona versione 8 canali) |

### Tag flagged come allucinazioni

- Nessun tag speech-related flaggato in corsivo (correttamente: lo Speech PANNs è 0.244, sopra soglia 0.10, quindi "Voce umana manipolata acusmatica" e "Preghiera collettiva sussurrata" sono legittimi).
- Tag italo-specifici flaggati in corsivo come `geo_specific=True` ("Paesaggio sonoro di borgo rurale italiano", "Aula di conservatorio italiano", "Festa di paese mediterranea") e l'agente li **scarta correttamente** dalla lettura finale perché "i tag CLAP italo-specifici del vocabolario sono fuori contesto e vanno letti come rumore semantico del classificatore". **In realtà qui la registrazione di ambiente è italiana** (monastero di Amelia): il flag `geo_specific` si è rivelato un falso positivo inverso: i tag erano pertinenti ma sono stati scartati perché il parlato era in inglese. Nota critica per il paper.

### Tag CLAP segmentali allucinatori ricorrenti

Dalla timeline segmentata si leggono anche:

- "Porto peschereccio mediterraneo all'alba con voci" (00:10-00:20): allucinazione.
- "Aula di conservatorio italiano con esercizi simultanei" (01:50-02:00): allucinazione per sovrapposizioni dense.
- "Treno ad alta velocità che sfreccia" (02:20-02:30): **secondo falso positivo "treno"** dopo *Basilica*. Sistemico.
- "Trattore che lavora in campagna" (03:30-03:40): allucinazione (probabilmente il tessuto granulare denso + bande basse).
- "Grandine che cade su superficie dura" (00:20-00:30): allucinazione (transitori granulari rapidi).
- "Lallazione infantile spontanea" (02:30-02:40): allucinazione su voce manipolata.

### Prompt CLAP mancanti

- **Canto monastico / gregoriano**: `Canto monastico maschile in risonanza di chiesa`, `Salmodia liturgica in latino`, `Gregoriano in abbazia`. Attualmente il brano viene tradotto come "preghiera collettiva sussurrata" che non è accurato.
- **Cantillazione ebraica / refrain semitico**: `Cantillazione ebraica tradizionale`, `Canto sefardita in sinagoga`. Coerente con Shofar 0.045 PANNs e col gold.
- **Field recording di cicale/insetti mediterranei processato**: `Insetti estivi stratificati in processing granulare`. Darebbe un'alternativa più plausibile di "Acqua del rubinetto" quando la sorgente è coreale-insetto ma il processing la deforma.
- **Dawn chorus di uccelli**: `Dawn chorus di uccelli all'alba in bosco`. Manca completamente.
- **Ruscello e fuoco scoppiettante**: `Ruscello d'acqua corrente in bosco`, `Fuoco di legna scoppiettante`. Per la parte di MacNevin.

### Prompt CLAP da rivedere

- `Acqua del rubinetto che scorre`: **seconda occorrenza** del falso positivo sistematico dopo *Basilica*. Questo è il caso scuola più grave per v0.7.0: il prompt matcha a larga gittata qualunque texture con grana continua in medio-acuti. Urgente.
- `Treno ad alta velocità che sfreccia`: seconda occorrenza del falso "treno" (dopo *Basilica*). Pattern di bande basse stretched che attivano questo prompt.
- `Aula di conservatorio italiano con esercizi simultanei`: specifico italo-AFAM, crea falso positivo su qualunque sovrapposizione strumentale densa. Da valutare rimozione o plausibility `low` quando Speech/Music PANNs < soglia.

## 4. Hum check

- **Verdetto complessivo skill**: trascurabile.
- **Reale**: corretto. Registrazione pulita. Picchi tonali a 121, 151, 181 Hz presenti (armoniche del materiale) ma ratio bassi vs baseline, verdetto "trascurabile" appropriato.
- **Hint contestuale**: non è scattato (non serviva: qui i ratio restano sotto soglia, a differenza di *Basilica*).

## 5. Mapping accademico

- **Krause**: antropofonia 56%, mista 33%, geofonia 9% → parzialmente corretto. Il **gap** è la biofonia a 0% quando il brano contiene cicale e dawn chorus processati. Il classificatore non vede quella dimensione.
- **Schafer**: sound-object + soundmark → OK (monastero italiano è soundmark locale).
- **Schaeffer type**: tenuto 50%, tenuto-evolutivo 24% → corretto.
- **Smalley motion**: flow 33%, oscillation 18% → corretto (tessitura continua con oscillazioni del parlato manipolato).
- **Schaeffer detail**: morphing 62% (high) → corretto (cross-sintesi voce/ambiente è il tratto saliente).
- **Smalley growth**: dilation 39% (high) → corretto (time-stretch + harmonizing).
- **Chion**: ridotto + causale + semantico + misto → OK.
- **Westerkamp soundwalk relevance**: non menzionato. Il gold dichiara esplicitamente che il materiale è field recording + processing acusmatico (tradizione soundscape composition). L'agente commenta "qui non c'è field recording documentario" → **errato**: c'è eccome, è solo molto processato.

## 6. Lessico CLAP vs terminologia musicale

- `Voce umana manipolata acusmatica` → OK, allineato a **text-sound composition** (Wishart, *On Sonic Art*) e al "trattamento plastico della voce" (Smalley).
- `Accumulo granulare stocastico` → OK, *stochastic granular synthesis* (Xenakis/Truax). Potrebbe essere più preciso: *real-time granular synthesis PODX* ma per un'analisi automatica è accurato.
- `Preghiera collettiva sussurrata in chiesa` → impreciso per questo brano: il materiale è canto monacale (cantato, non sussurrato). Sostituibile con `canto liturgico monastico in chiesa`.
- `Time-stretch estremo di oggetto concreto` → OK ma qui lo stretch è meno estremo di *Basilica*.

## 7. Sezioni compositive

La skill ha rilevato 3 sezioni (S1 00:00-01:40, S2 01:40-04:00, S3 04:00-04:05). Manuale proposto, più articolato:

| Sezione | Tempo | Evento principale | Note |
|---------|-------|-------------------|------|
| Soglia | 00:00-00:30 | emersione a livelli bassi, figura tonale che si raccoglie | skill: colta ("Soglia") |
| Appello | 00:30-01:00 | entra la voce "Return, my friend, return, return, I'm in New York" | skill: colta ("L'appello") |
| Tessitura densa | 01:00-02:00 | 6 onset/s, flauto si affaccia, cross-sintesi voce/strumento | skill: colta ("Tessitura densa") |
| Preghiera laica | 02:00-03:30 | morphing continuo, centroide scende verso 2100 Hz, zona sussurrata | skill: colta ("Preghiera laica") |
| Soffio conclusivo | 03:30-04:00 | wind instrument / shofar prendono il centro | skill: colta ("Soffio conclusivo") |
| Quasi-silenzio | 04:00-04:05 | crollo a RMS -85 | skill: colta ("Quasi-silenzio") |

La lettura segmentata dell'agente è **più fine** della segmentazione automatica a 3 zone. Qui l'agente ha fatto lavoro interpretativo che la changepoint detection non cattura. Nota positiva: la struttura a 6 scene emerge dai dati + narrativa + classificatori aggregati, non da metadati.

## 8. Lettura compositiva dell'agente

- **Pertinente?**: sì, lettura di ottima qualità. Passaggi forti:
  - "Al minuto 0:36 entra una voce in inglese ... che apre una ferita semantica dentro il tessuto: l'appello al ritorno e la dichiarazione di distanza convivono nello stesso gesto."
  - "La parola è già oggetto sonoro, il senso è già eco" (*molto Schaefferiano*, centrato).
  - "Un campo rituale costruito senza riti, per sola tessitura timbrica" (sulla *Preghiera laica*).
  - "Il materiale non è italiano (speech in inglese): i tag CLAP italo-specifici sono fuori contesto" → filtro geografico esplicito, ma **errato** qui perché gli ambienti registrati *sono* italiani, solo la voce-testo è inglese.
- **Binomi concettuali eccellenti**: voce/processo, lontananza/presenza, rituale/laicità. Perfetti per il brano.
- **Parentele stilistiche**: Wishart, Charles Dodge, Paul Lansky, Robert Ashley (text-sound composition americana), Parmegiani (De Natura Sonorum). Buonissima pista: **il trattamento plastico della voce** è effettivamente la parentela teorica più forte. Menziona Truax/Westerkamp solo en-passant ("gesto condiviso con la scuola ... del soundscape ecologico, ma qui non c'è field recording documentario"): qui c'è un **doppio errore**: (a) il brano **è di Truax**, e (b) **c'è field recording** (cicale italiane, dawn chorus bretone, fuoco, ruscello), solo molto processato. Gap di riconoscimento sistematico della scuola WSP/SFU.
- **Errore di trascrizione whisper**: "I'm in New York" è probabilmente un'allucinazione o confabulazione di whisper. Il testo originale del Cantico dei Cantici 6:13 recita "Return, return, O Shulamite, return, return". "New York" non è plausibile. L'agente ha costruito una lettura sopra questo errore ("sono a New York dichiara un altrove"). Segnale: la bassa confidence di whisper (0.73) avrebbe dovuto pesare di più sull'interpretazione testuale.
- **Suggerimenti compositivi**: ottimi drammaturgicamente: diffusione della voce in orbita periferica, performance con attore che recita dal vivo, dittico con registrazione documentaria contemporanea da New York (purtroppo costruito sull'allucinazione whisper), laboratorio AFAM sulla sezione cross-sintesi 00:30-02:00.

## 9. Note libere

### Positivi rilevanti per il paper

1. **Whisper riconosce la frase chiave del Cantico dei Cantici ("Return, my friend, return")** nonostante sia cantata e manipolata. La pipeline speech opt-in v0.5.0 è efficace.
2. **Shofar (PANNs 0.045)** sorprendente: il gold dichiara "cantillazione ebraica tradizionale come refrain" e la rete associa effettivamente uno strumento rituale ebraico. La confidence è bassa ma il segnale c'è.
3. **L'agente costruisce un arco drammaturgico coerente in 6 scene** da una segmentazione automatica a 3 sezioni. La combinazione changepoint detection + narrativa segmentata + classificatori aggregati produce una risoluzione interpretativa maggiore dei singoli layer. Dato importante per la discussione del paper.
4. **Filtro `geo_specific` attivato**: l'agente scarta i tag italo-specifici. La logica funziona.
5. **Parentele Wishart/Dodge/Lansky/Ashley**: precise. Il trattamento plastico della voce è la genealogia teorica corretta.
6. **Binomi concettuali voce/processo, lontananza/presenza, rituale/laicità**: sintesi interpretativa forte.

### Gap strutturali per il paper

1. **Multi-sorgente field recording invisibile**: il brano combina 4+ tracce ambientali (cicale, dawn chorus, ruscello, fuoco) + 2+ voci + strumenti, ma PANNs e CLAP catturano solo una frazione. Le biofonie sono completamente perse. La decomposizione del multi-layer **non è possibile** con classificatori a singolo output: servirebbe source separation (es. Demucs, HTDemucs) o iterative unmixing.
2. **Allucinazione whisper propagata nell'interpretazione**: "I'm in New York" (probabile confabulazione) è entrata come dato nella lettura drammaturgica. Serve una regola: quando `language_probability < 0.80` E la trascrizione contiene toponimi specifici (New York, Paris, ecc.), marcare la trascrizione come "parzialmente ipotetica" e istruire l'agente a **non costruire narrativa sui dati testuali**.
3. **Filtro `geo_specific` invertito**: qui gli ambienti *sono* italiani (monastero di Amelia), quindi i tag "Paesaggio sonoro di borgo rurale italiano" sarebbero pertinenti. Il flag ha scartato informazione corretta perché basato sulla lingua del parlato. Regola da raffinare: il `geo_specific` non è da applicare automaticamente se la traccia è multi-layer (voce in una lingua + ambiente in altra geografia).
4. **Scuola WSP/SFU di nuovo non riconosciuta** come parentela: l'agente ha ragione nel vedere text-sound composition (Wishart/Dodge) come pista forte, ma sbaglia a escludere Truax dicendo "qui non c'è field recording documentario". **C'è, è il brano di Truax**. Regola: se compaiono simultaneamente (a) tag CLAP di **luoghi naturali** (anche score moderati 0.15-0.22), (b) tag di **voce manipolata**, (c) morphing/dilation alti, considerare la tradizione soundscape (Truax, Westerkamp) come parentela **paritetica** alla text-sound composition (Wishart, Dodge, Ashley).

### Casi scuola per v0.7.0 plausibility check

- `Acqua del rubinetto che scorre` (score 0.235): **secondo caso ricorrente** dopo *Basilica*. Qui PANNs Water/Liquid/Stream molto bassi → plausibility `low`.
- `Treno ad alta velocità che sfreccia` (02:20-02:30): **secondo falso treno**, diverso dal *Basilica*.
- `Aula di conservatorio italiano con esercizi simultanei` (01:50-02:00), `Trattore che lavora in campagna` (03:30-03:40), `Grandine che cade su superficie dura`, `Lallazione infantile spontanea`: falsi positivi semanticamente gravi.

### Lezioni per il paper

- Su brani multi-sorgente con processing denso (Truax 250 eventi/sec), il **rapporto signal/noise semantico** diminuisce: la skill vede "musica + parlato + wind instrument" ma perde cicale, uccelli, ruscello, fuoco, campane monastero. Questo è un **limite dell'analisi a classificatore unico** che va dichiarato nelle limitazioni.
- La **catena speech -> trascrizione -> interpretazione agente** è sensibile alle allucinazioni di whisper. Il confidence score va propagato come "marker di incertezza" fino all'agente.
- La **qualità drammaturgica dell'output agente v0.6.3** resta alta anche su brani brevi e densi. La struttura a 6 sezioni (Soglia / Appello / Tessitura densa / Preghiera laica / Soffio conclusivo / Quasi-silenzio) è eccellente e dimostra la potenza del paradigma "lettura drammaturgica > elenco tecnico".
