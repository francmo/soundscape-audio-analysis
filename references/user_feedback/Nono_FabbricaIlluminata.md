# Feedback - Luigi Nono, *La fabbrica illuminata* (1964)

## 1. Identificazione

- **File**: `track_03.mp3` (copia anonimizzata, soundscape-training/audio_blind/)
- **Versione skill che ha prodotto il report**: v0.6.5, senza `--speech` (anche se il gold lo raccomandava)
- **Data feedback**: 2026-04-17
- **Contesto del brano**: Luigi Nono, *La fabbrica illuminata* (1964), 17 minuti, per soprano e nastro magnetico a quattro tracce. Prima: Venezia, La Fenice, 15 settembre 1964. Dedicata agli operai dell'Italsider di Genova-Cornigliano. Materiale: registrazioni industriali (laminatoi a caldo e a freddo, altoforno) + voci operai autentiche + soprano Carla Henius + coro RAI di Milano (direttore Giulio Bertola) + elettronica originale prodotta allo Studio di Fonologia RAI Milano (tecnico Marino Zuccheri). Testi: Giuliano Scabia (gergo di fabbrica, contratto sindacale, immagini oniriche) + Cesare Pavese (finale, "Due poesie a T"). Struttura in quattro movimenti: Coro di apertura, Solo nastro, Bed Circuit, City Total + Finale. Sezione finale con tecnica seriale del "quadrato magico". Opera **censurata prima della prima** per testi politicizzati.
- **Gold analitico**: `Nottoli-03-Nono-FabbricaIlluminata/analisi-luiginono.md` (luiginono.it).

## 2. PANNs

### Top-1 globale

- **Skill dice**: `Music` (score 0.30, frame dominante solo 31.7%)
- **Reale**: parzialmente corretto. A differenza di *Basilica* e *Song of Songs I*, qui Music **non domina**: frame dominanti sono Music 31.7%, Speech 29.7%, Humming 13.9%, Vehicle 5%, Opera 4%, Sonar 4%, Silence 3%, Choir 1%. Distribuzione più onesta, riflette la reale eterogeneità del brano.

### Top-10 globali

| Posizione | Etichetta PANNs | Score | Valutazione |
|-----------|-----------------|-------|-------------|
| 1 | Music | 0.2987 | OK |
| 2 | Speech | 0.2328 | **corretto** (voci operai + soprano) |
| 3 | Humming | 0.1185 | parziale (forse voci su registro mediano processate) |
| 4 | Opera | 0.0810 | **corretto** (soprano Henius) |
| 5 | Singing | 0.0698 | **corretto** (canto soprano/coro) |
| 6 | Vehicle | 0.0579 | parziale (potrebbero essere rumori industriali assimilati a veicolo) |
| 7 | Inside, small room | 0.0488 | OK (registrazioni ambientate) |
| 8 | **Theremin** | 0.0477 | interessante: **sinusoidi Studio di Fonologia** assimilate a theremin |
| 9 | Sonar | 0.0424 | potrebbe essere **generatori elettronici** |
| 10 | Animal | 0.0388 | errato (no animali) |

**Gap notevole**:
- **Mancano etichette industriali**: Machinery, Engine, Motor, Factory, Industrial processing, Steam. PANNs vede "Vehicle" come genericizzazione ma non riconosce il *contesto-fabbrica*. Eppure il gold dichiara laminatoi + altoforno come sorgenti primarie.
- **Choir al 1% nei frame dominanti ma non nei top-10 globali**: il coro RAI di Milano è presente.
- **Theremin e Sonar** sono **interessanti segnali indiretti**: l'elettronica della Fonologia RAI (generatori sinusoidali, oscillatori) viene assimilata a theremin/sonar dalla rete AudioSet-trained, che non ha categorie per "elektronische Musik / Studio di Fonologia".

### Frame dominanti

- **Speech al 29.7%** è il dato più significativo: la skill riconosce che il brano è largamente vocale, molto più di *Basilica* (Speech 0% frame dominanti).
- **Humming 13.9%**: probabilmente coro e voci sovrapposte in registri mediani.

## 3. CLAP

### Top-10 globali

| Posizione | Prompt italiano | Score | Pertinente? | Note |
|-----------|-----------------|-------|-------------|------|
| 1 | Voce amplificata con effetti elettronici | 0.269 | **sì, perfetto** (descrive esattamente la soprano Henius amplificata) |
| 2 | Voce umana manipolata acusmatica | 0.266 | sì |
| 3 | Time-stretch estremo di oggetto concreto | 0.254 | sì |
| 4 | **Grilli nella sera estiva** | 0.233 | **no, allucinazione biofonica** (sinusoidi/oscillatori → grilli) |
| 5 | Accumulo granulare stocastico | 0.233 | sì |
| 6 | **Insetti in texture densa su corteccia** | 0.231 | **no, allucinazione biofonica** ricorrente |
| 7 | Grandine che cade su superficie dura | 0.227 | no (transitori industriali letti come grandine) |
| 8 | Sussurro intimo non intelligibile | 0.223 | sì (voci sussurrate operai) |
| 9 | Preghiera collettiva sussurrata in chiesa | 0.223 | allucinazione (no preghiera qui, ma voci sussurrate collettive sì) |
| 10 | Aspirapolvere in uso domestico | 0.218 | **no, allucinazione** (rumori industriali letti come elettrodomestico) |

### Tag segmentali notevoli

- Positivi / indicativi:
  - `Coro in prova a cappella` (00:30-00:40, 01:10-01:20, 01:30-01:40): **corretto**, coglie il coro RAI.
  - `Processione religiosa con canto` (00:40-00:50, 02:10-02:20, 02:40-02:50): parziale (non è processione ma materiale corale liturgico-like).
  - `Feedback di microfono controllato` (04:20-04:30, 07:00-07:10, 08:30-08:40): **corretto**, tipica elettronica di Fonologia RAI (larsen controllati).
  - `Trapano elettrico in foratura` (04:30-04:40): parziale, potrebbe essere davvero un'industria trapanata su nastro.
  - `Risonanza metallica prolungata` (04:40-04:50): **corretto**, laminatoi o strutture di fabbrica.
  - `Rintocchi funebri lenti e profondi` (07:00-07:10, 10:30-11:00): interessante, basso metallico lento (caratteristico).
  - `Massa tonica con micro-oscillazioni interne` (03:30-03:40, 04:40-04:50): **corretto**, descrive l'elettronica Fonologia.
  - `Delay ritmico a ciclo lungo con feedback` (08:30-08:40, 10:30-11:00): **corretto**, tecnica classica Fonologia.
  - `Scrittura su tastiera di computer` (05:10-05:20, 06:50-07:00): allucinazione (impulsi rapidi letti come digitazione).
  - `Tastiera elettrica o sintetizzatore` (03:40-03:50): parziale.
  - `Quartetto d'archi in esecuzione` (05:50-06:00, 06:20-06:30): allucinazione (voce/coro processato letto come archi).
  - `Urlo umano isolato in primo piano` (10:00-10:30): **corretto**, sezioni di Sprechgesang o urlo operistico.
  - `Performance live elettronica in sala` (10:00-10:30): parziale, è registrazione ma stilisticamente sì.
  - `Improvvisazione strumentale libera` (10:30-11:00): allucinazione.
  - `Lallazione infantile spontanea` (12:30-13:00): allucinazione.
  - `Porto peschereccio mediterraneo all'alba con voci` (06:10-06:20): allucinazione italo-specifica.
  - `Treno regionale in arrivo a stazione di provincia` (06:10-06:20): allucinazione (forse rumori di fabbrica interpretati come treno).

- Negativi sistemici:
  - `Acqua del rubinetto che scorre` (07:50-08:00, 05:20-05:30): **terza occorrenza** del falso positivo ricorrente.
  - `Neve che cade in ambiente silenzioso` (05:20-05:30, 07:50-08:00): altra allucinazione.
  - `Preghiera collettiva sussurrata in chiesa`: molto presente sulle voci corali.
  - `Gatto`, `Whale vocalization`, `Horse`, `Gong`: allucinazioni animali/oggetti su materiali elettronici.

### Prompt CLAP mancanti

**Categoria "ambienti industriali" / "musica concreta di fabbrica"** completamente assente dal vocabolario corrente. Candidati:

- `Laminatoio in acciaieria a caldo`.
- `Altoforno con ventilazione e colata`.
- `Officina meccanica con martelli pneumatici`.
- `Fabbrica con macchinari pesanti`.
- `Acciaio tagliato con fiamma ossidrica`.
- `Catena di montaggio con pressa idraulica`.
- `Nastro magnetico storico con rumore di fondo`.

Senza questi prompt, il materiale industriale di Nono rimane invisibile al classificatore italiano, oppure viene ricondotto a prompt semanticamente lontani (aspirapolvere domestico, trapano, grandine).

Categoria **"elektronische Musik / Studio di Fonologia / sinusoidi generative"**:

- `Generatore di sinusoidi a frequenza pura`.
- `Oscillatore elettronico con sweep di frequenza`.
- `Rumore bianco filtrato a banda stretta`.
- `Modulazione ad anello di due sinusoidi` (ring modulation).
- `Nastro magnetico con voce processata`.

Attualmente l'elettronica Fonologia RAI viene riconosciuta come "theremin" / "sonar" da PANNs (AudioSet) o come "tastiera elettrica / sintetizzatore" da CLAP: utili ma non precisi storicamente.

### Prompt CLAP da rivedere

Oltre ai già noti (`Acqua del rubinetto`, `Treno`, `Trattore`, ecc.), emergono nuovi falsi positivi ricorrenti:

- **`Grilli nella sera estiva` e `Insetti in texture densa su corteccia`** (biofonia): matchano largo su materiali elettronici sinusoidali stretti. **Grave**. Da plausibility-filtrare quando PANNs Insect/Cricket/Animal < 0.05 (qui Animal 0.039 al limite).
- **`Aspirapolvere in uso domestico`** (antropofonia meccanica): matcha su rumori industriali stazionari.
- **`Canticchio`** (biofonia): presente in classificazione frame-level (PANNs?). Da verificare se è "cricket" in inglese tradotto o altro. Se è "canticchiare" (humming) allora è umano, non biofonia.
- **`Quartetto d'archi in esecuzione`**: matcha su voci sostenute tonali.

## 4. Hum check

- **Verdetto complessivo skill**: presente (+19.3 dB a 50 Hz vs baseline).
- **Reale**: qui è **plausibilmente corretto**. Registrazione analogica su nastro magnetico del 1964 dello Studio RAI, ronzio 50 Hz europeo è realistico. L'agente dice appropriatamente: "verificare la baseline 50 Hz e valutare se rimuoverlo alla sorgente o se è una componente intenzionale (potrebbe essere ronzio elettrico di scena)". **Lettura contestualizzata corretta**: il ronzio elettrico di una fabbrica illuminata può essere *voluto* drammaturgicamente, non un artefatto da rimuovere. Notare: il hint `likely_musical_harmonic` v0.5.1 **non è scattato** (correttamente: flatness 0.0078 tonale ma classificatore Music solo 0.30, non dominante → contesto non "materiale tonale + classificatore dominante Music").

## 5. Mapping accademico

- **Krause**: antropofonia 60%, mista 19%, biofonia 15%, geofonia 5% → distribuzione realistica. La biofonia 15% è **artefatto** delle allucinazioni CLAP su grilli/insetti. Nella realtà il brano è 100% antropofonia.
- **Schafer**: signal + sound-object → OK ma manca **keynote industriale** come categoria dominante. Il "signal" industriale qui è dominante (soundscape di fabbrica politico).
- **Schaeffer type**: tenuto 39%, trama 31% → **ottimo**, "trama" è categoria centrale per la Fonologia RAI (masse granulate, texture continue).
- **Smalley motion**: turbulence 39%, oscillation 30% → **corretto** (rumori industriali = turbolenza, oscillatori = oscillation).
- **Schaeffer detail**: morphing 28% (high) → OK (cross-sintesi voce/rumore).
- **Smalley growth**: endogeny 54% (high) → **eccellente**: "endogeny" (crescita endogena, interna al materiale) è la categoria Smalley più pertinente per il brano, e l'agente la cita esplicitamente nella lettura ("endogenous growth alla Smalley, una crescita tutta interna al materiale").
- **Chion**: semantico + ridotto + causale → OK, coerente con il testo politico + dimensione acusmatica.
- **Westerkamp soundwalk relevance**: non menzionato (appropriato: qui non c'è soundwalk).

## 6. Lessico CLAP vs terminologia musicale

- `Voce amplificata con effetti elettronici` → OK, preciso per la soprano Henius sovraesposta al microfono.
- `Coro in prova a cappella` → impreciso: è il Coro RAI diretto da Bertola, non "in prova a cappella". Ma cattura la natura corale polifonica.
- `Massa tonica con micro-oscillazioni interne` → OK, è descrizione Smalley-compatibile di "mass" con "internal motion".
- `Feedback di microfono controllato` → OK, tecnica classica di Nono (anche nelle opere successive come *Contrappunto dialettico alla mente*).
- `Time-stretch estremo di oggetto concreto` → parziale: Nono usava più nastro manipolato (tape splicing, reversal, pitch shifting) che time-stretching moderno. Il vocabolario non distingue le epoche.

## 7. Sezioni compositive (timeline manuale)

La skill ha rilevato 8 sezioni (S1 00:00-03:30, S2 03:30-04:00, S3 04:00-04:50, S4 04:50-05:20, S5 05:20-06:20, S6 06:20-13:20, S7 13:20-16:40, S8 16:40-16:47). Struttura ricca, coerente con la complessità del brano. Proposta manuale (4 movimenti + coda secondo il gold):

| Sezione | Tempo | Evento | Note |
|---------|-------|--------|------|
| I. Coro di apertura | 00:00-03:30 | coro + soprano dal vivo, materiale operistico trattato | skill: "Coro amplificato, apertura corale" |
| II. Solo nastro (inizio) | 03:30-06:20 | rumori industriali + voci operai | skill: "Turbolenza granulare" + "Preghiera sommersa" |
| III. Bed Circuit | 06:20-13:20 | voce dal vivo + materiale elettronico processato + soprano registrato | skill: "Deriva acusmatica lunga" (la sezione più estesa, 7 minuti) |
| IV. City Total + Finale | 13:20-16:40 | voce dal vivo contro voci registrate + coro, testo Pavese finale, quadrato magico | skill: "Notturno biofonico" (interpretato come notturno naturale, che è **lettura metaforica** non letterale) |
| Dissolvenza | 16:40-16:47 | quasi-silenzio | skill: "Dissolvenza, 8 secondi" |

Osservazione: la skill ha colto la struttura come "arco di dissoluzione" ma ha mancato la **struttura in quattro movimenti** dichiarata da Nono. In parte perché l'agente non conosce il gold, in parte perché le transizioni fra movimenti sono nascoste dalla continuità del materiale.

## 8. Lettura compositiva

**Eccellente qualità interpretativa.** Passaggi forti:

- "Un lento atto di dissoluzione della voce umana nel paesaggio." (incipit)
- "Ciò che era parola diventa grana."
- "Un endogenous growth alla Smalley, una crescita tutta interna al materiale: nessuna figura esterna irrompe, è la massa iniziale che si apre, si dilata e si svuota fino al quasi silenzio."
- Binomi concettuali: voce-oggetto, comunità-solitudine, sacro-tecnologico, figura-notturno. **Tutti centrati**.

**Parentele stilistiche: attribuzione corretta**:

- **Studio di Fonologia RAI di Milano, nella direzione Berio e Maderna** → **gold**: l'agente ha identificato la scuola giusta!
- Trevor Wishart Vox cycle (Vox 5, Tongues of Fire) per la cross-sintesi voce-oggetto → ottima parentela secondaria.
- Truax/Westerkamp "solo come citazione conclusiva, per il gesto di resa all'ambiente nel finale" → formulazione corretta: pariteticità senza forzatura (la lezione v0.6.5 ha funzionato).

**Nota importante**: l'agente **non nomina esplicitamente Nono** (appropriato: non è suo compito identificare il brano), ma la scuola Fonologia RAI con direzione Berio/Maderna è precisamente il contesto dove Nono lavorava. Cartello stilistico perfetto.

**Nota interpretativa**: il "notturno biofonico" finale (13:20-16:40) è basato sulla falsa biofonia CLAP ("grilli nella sera estiva", "canticchio"), ma l'agente lo integra in una lettura metaforica coerente ("la voce ha finito di parlare e il mondo ambientale la riprende"). Come in *Song of Songs I* col "New York" di whisper, un errore di riconoscimento viene riassorbito in una narrativa plausibile: **buona per la lettura artistica ma problematica per la correttezza analitica**. Da discutere nel paper come caso di "confabulazione coerente" dell'agente LLM.

**Suggerimenti compositivi**: ottimi, drammaturgici e pedagogici:
- Diffusione acousmonium con spazializzazione della traiettoria globale.
- Remix del notturno finale come pezzo breve autonomo.
- Performance con soprano dal vivo che esegue cellule operistiche sovrapposte.
- Laboratorio AFAM sul passaggio 03:00-04:30 come caso di studio sul morphing vocale.
- Serata monografica "voce-elettronica nella tradizione italiana" accostando brano strumentale della scuola Fonologia RAI.
- Documentazione video con aule vuote o spazi liturgici abbandonati.

## 9. Note libere

### Positivi per il paper

1. **Riconoscimento scuola Fonologia RAI** senza metadata: l'agente ha identificato "Studio di Fonologia RAI di Milano, direzione Berio e Maderna" come parentela più forte, il che è il **contesto esatto** di Nono. Questo dimostra che i segnali combinati (CLAP "voce amplificata con effetti elettronici" + PANNs "Opera+Singing+Theremin+Sonar" + Schaeffer "trama 31%" + Smalley "endogeny 54%" + durata 17 min) sono sufficienti a triangolare correttamente l'area stilistica. **Caso positivo** contro l'errore di *Song of Songs I* (dove Truax non è stato riconosciuto).
2. **Endogeny Smalley 54% high**: la categoria più precisa per questo brano è emersa quantitativamente e l'agente l'ha usata nella lettura. Prova che le tassonomie v0.6.0 funzionano.
3. **Hum 50 Hz trattato con cautela contestuale**: l'agente non lo dà per scontato artefatto, propone due ipotesi ("componente intenzionale o ronzio di scena"). Atteggiamento epistemologicamente corretto.
4. **Sezioni strutturali 8**: changepoint detection funziona bene su brani lunghi complessi.
5. **Distribuzione PANNs onesta** (Music solo 31.7%, Speech 29.7%): a differenza di *Basilica* dove Music al 97% saturava tutto, qui i classificatori rispecchiano la reale stratificazione.

### Gap strutturali per il paper

1. **Ambienti industriali invisibili al vocabolario**: *La fabbrica illuminata* è letteralmente "soundscape industriale + voce", ma il vocabolario CLAP non ha prompt per laminatoi, altoforno, macchinari pesanti. Il materiale industriale viene ricondotto a "aspirapolvere", "trapano", "grandine", "treno" (allucinazioni). **Urgente**: aggiungere categoria `ambienti industriali / suoni di fabbrica / musica concreta industriale` al vocabolario v1.7.
2. **Elettronica storica (Fonologia RAI)**: sinusoidi, ring modulation, larsen controllati, nastro magnetico con rumore → letti come "theremin", "sonar", "tastiera elettrica". Manca specificità storica. Aggiungere prompt per `elektronische Musik 1950-1970` / `Studio di Fonologia RAI Milano`.
3. **Allucinazione biofonica sistemica su elettronica stretta**: `Grilli nella sera estiva`, `Insetti in texture densa`, `Canticchio` matchano su sinusoidi, oscillatori, texture elettroniche stretti. Falso positivo grave perché inquina la distribuzione Krause (15% biofonia su brano 100% antropofonia).
4. **Trascrizione speech assente**: il brano ha testi Scabia (italiano politico) + Pavese (italiano poetico) + gergo di fabbrica + contratto sindacale. `--speech` non è stato attivato. Con --speech, whisper avrebbe probabilmente riconosciuto l'italiano (a differenza di Song of Songs in inglese) e recuperato il testo politico, portando un layer semantico cruciale per questo brano.
5. **Confabulazione coerente** dell'agente sul "notturno biofonico" finale: integra allucinazioni CLAP (grilli) in una lettura drammaturgica plausibile. Il paper deve discutere questa proprietà come **rischio duale**: migliora la narrativa ma compromette la correttezza analitica.

### Patch candidate

**v0.6.6 (hotfix feedback)**:
- Aggiungere categoria **"ambienti industriali"** al vocabolario CLAP v1.7 con 6-8 prompt (laminatoio, altoforno, officina, catena di montaggio, fabbrica macchinari, acciaio tagliato, fiamma ossidrica).
- Aggiungere categoria **"elektronische Musik storica"** con 4-5 prompt (generatore sinusoidi, oscillatore sweep, rumore bianco filtrato, ring modulation, nastro magnetico vintage).
- Correggere categorie biofonia dove i prompt sono semanticamente troppo generici (`insetti in texture densa su corteccia`, `grilli nella sera estiva`).

**v0.7.0 (plausibility check)**:
- Regola aggiuntiva: tag biofonici (categoria `biofonia`) con PANNs `Animal/Insect/Cricket/Bird` < 0.05 → plausibility `low`.
- Tag antropofonia-meccanica (`aspirapolvere`, `trattore`, `treno`) con PANNs `Vehicle/Engine/Machinery` < 0.05 → plausibility `low`.

**Prompt agente**:
- Regola: se compaiono simultaneamente PANNs `Opera + Singing + Choir + Speech` (anche a score moderati) + CLAP `voce amplificata con effetti elettronici + coro a cappella + feedback di microfono controllato`, considerare la parentela con `Studio di Fonologia RAI Milano (Berio/Maderna/Nono)` come alternativa paritetica al GRM francese.

### Lezioni per il paper

- **Distribuzione PANNs più onesta** su brani multi-sorgente non saturati dal processing: *La fabbrica illuminata* con Music 30% / Speech 30% / Humming 14% / Vehicle 5% / Opera 4% / Theremin+Sonar riflette meglio la stratificazione di *Basilica* con Music 97%.
- **Gap vocabolario industriale**: il field di Nono (soundscape politico della classe operaia, fabbrica illuminata) richiede categorie semantiche oggi assenti nel vocabolario CLAP italiano. Domanda aperta: il vocabolario deve coprire *anche* soundscape politici/urbani/industriali (Luc Ferrari *Presque Rien*, Stockhausen *Hymnen*, Nono *Fabbrica*, Lachenmann ecc.), o deve restare focalizzato su natural soundscape + acusmatica classica?
- **Hum contestualizzato correttamente**: a differenza di *Basilica* (falso positivo risolto dal hint), qui il 50 Hz potrebbe essere reale (nastro 1964). L'agente lo ha dichiarato come dato da verificare, non come fatto. Esempio virtuoso di gestione dell'incertezza.
- **Endogeny Smalley come categoria descrittiva cruciale**: la dilazione interna senza intervento esterno è la qualità saliente di questo brano. Il v0.6.0 l'ha resa visibile.
