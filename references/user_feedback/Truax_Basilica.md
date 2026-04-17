# Feedback - Barry Truax, *Basilica* (1992)

## 1. Identificazione

- **File**: `track_01.mp3` (copia anonimizzata, soundscape-training/audio_blind/)
- **Versione skill che ha prodotto il report**: v0.6.5
- **Data feedback**: 2026-04-17
- **Contesto del brano**: Barry Truax, *Basilica* (1992), CD *Song of Songs* (Cambridge Street Records). Materiale integralmente derivato da tre campane della Basilica di Notre-Dame de Québec, catturate dal World Soundscape Project (Simon Fraser University) nel 1973. Tecniche dichiarate dall'autore: trasposizione di frequenza (ottava sotto + dodicesima sopra), time-stretch oltre venti volte, granular synthesis in real-time con sistema PODX (DSP DMX-1000 + PDP Micro-11). Deriva da *Dominion* (1991). Versione originale stereo, esiste anche diffusione 8 canali (sistema DM-8).
- **Gold analitico**: `references/user_feedback/../soundscape-training/Nottoli-01-Truax-Basilica/analisi-sfu.md` (scheda ufficiale dall'autore, sfu.ca/~truax/basilica.html).

## 2. PANNs (classificazione semantica primaria)

### Top-1 globale

- **Skill dice**: `Music` (score 0.68)
- **Reale**: parzialmente corretto, manca la sorgente concreta: il brano è 100% derivato da **campane di chiesa** (Bell / Church bell in AudioSet). La classificazione come "Music" cattura solo il risultato post-trasformazione, non la sorgente riconoscibile all'inizio e alla fine del brano.

### Top-10 globali

| Posizione | Etichetta PANNs | Score | Valutazione |
|-----------|-----------------|-------|-------------|
| 1 | Music | 0.6815 | parziale (cattura il risultato, non la sorgente) |
| 2 | Scary music | 0.3183 | OK interpretativo (il tenuto dilatato è inquietante) |
| 3 | Ambient music | 0.0598 | OK interpretativo |
| 4 | Musical instrument | 0.0505 | OK debole |
| 5 | Soundtrack music | 0.0494 | irrilevante |
| 6 | **Train** | 0.0470 | **errato, falso positivo** |
| 7 | Theme music | 0.0389 | irrilevante |
| 8 | Speech | 0.0368 | errato (non c'è parlato) |
| 9 | **Rail transport** | 0.0341 | **errato, falso positivo** |
| 10 | Vehicle | 0.0292 | errato |

**Gap grave**: `Bell`, `Church bell`, `Chime`, `Bell tower`, `Bell ringing` NON compaiono nei top-10 globali (e probabilmente nemmeno nei top-20). Il classificatore è stato fuorviato dal time-stretch estremo che trasforma i transitori impulsivi delle campane in textures sostenute, facendo scattare "Music" come categoria generica. È esattamente il caso studio previsto nel README del brano: la skill non sa distinguere "campane naturali" da "campane trasformate 20x".

### Frame dominanti

- **Skill**: Music 97.2%, Train 1.4%, Silence 1.4%.
- **Reale**: la percezione di Music al 97% è coerente con l'output *finale* percepito, ma è un'astrazione: sotto c'è sempre materia campanaria. "Train" 1.4% è un artefatto sistematico dalle bande basse delle campane stretched (la regola patch #1 v0.6.4 per tag marginali < 0.40 ha funzionato: l'agente ha correttamente scartato il treno nella lettura compositiva).

## 3. CLAP (auto-tagging italiano)

### Top-10 globali

| Posizione | Prompt italiano | Score | Pertinente? | Note |
|-----------|-----------------|-------|-------------|------|
| 1 | Texture granulare densa | 0.349 | sì | descrive il risultato post-granular, centrale |
| 2 | Musica elettronica ambient | 0.263 | parziale | genere approssimativo |
| 3 | Time-stretch estremo di oggetto concreto | 0.258 | **sì, ottimo** | coglie la tecnica principale dichiarata da Truax |
| 4 | **Insetti in texture densa su corteccia** | 0.232 | **no, allucinazione biofonica** | materiale non è biofonia, è bronzo dilatato |
| 5 | Trasformazione spettrale progressiva | 0.231 | sì | corretto |
| 6 | Profilo dinamico in morphing continuo | 0.219 | sì | corretto, coglie il morphing |
| 7 | Voce umana manipolata acusmatica | 0.195 | no, allucinazione | correttamente flaggata (corsivo PDF) come ipotesi di lavoro |
| 8 | Percussioni leggere e ritmiche | 0.186 | parziale | le campane originali hanno attacco percussivo; dopo stretch non più |
| 9 | **Acqua del rubinetto che scorre** | 0.182 | **no, allucinazione forte** | tipico falso positivo del vocabolario |
| 10 | **Accordatura di strumenti orchestrali** | 0.176 | **no, allucinazione** | spettro tonale ricco ≠ tuning di orchestra |

### Tag flagged come allucinazioni

- `Voce umana manipolata acusmatica` correttamente marcato in corsivo (PANNs Speech 0.037, sotto soglia 0.10): la regola `likely_hallucination` v0.5.1 funziona.
- **Ma non sono flaggati**: `Insetti in texture densa su corteccia`, `Acqua del rubinetto che scorre`, `Accordatura di strumenti orchestrali`. Sono tutti e tre falsi positivi semanticamente gravi. Il filtro attuale marca solo voice-related, non biofonia/idrofonia/orchestra-tuning quando PANNs Music domina al 97%.

### Prompt CLAP mancanti

La sorgente sonora del brano (campana di chiesa registrata) è **assente** dal vocabolario corrente (v1.6, 203 prompt). Candidati da aggiungere con estrema cautela (lezione v0.6.4 → v0.6.5: prompt CLAP troppo specifici causano bias):

- `Campana di chiesa in risonanza armonica dilatata` (categoria: trasformazioni elettroacustiche, non "bronzo campanario" generico).
- `Bronzo metallico con parziali inarmonici dilatati` (più neutro, riferimento timbrico, non iconografico).
- `Registrazione di campanile trasformata acusmaticamente`.

**Vincolo**: NON aggiungere prompt che matchino largo qualunque risonanza tonale metallica (come elx_14..elx_17 rimossi in v0.6.5). Riservarli a materiali dove la sorgente campanaria sia effettivamente documentabile. Meglio che l'agente componga "campane trasformate" dalla combinazione di tag base (time-stretch + morphing + tonalità armonica sostenuta) che dalla presenza di un prompt-sorgente diretto.

### Prompt CLAP da rivedere

- `Insetti in texture densa su corteccia` (biofonia): testo troppo semanticamente generico, matcha qualunque micro-rumorosità iterativa. Da **non rimuovere ma plausibility-filter** quando PANNs biofonico (Insect, Bird, Cricket) < 0.05.
- `Acqua del rubinetto che scorre` (antropofonia domestica): è l'esempio scolastico della falsa attribuzione già citato nel ROADMAP (v0.7.0 plausibility check). Qui ricompare su tutt'altro materiale. Da filtrare con plausibility `low` quando PANNs Water/Liquid/Stream < 0.05.
- `Accordatura di strumenti orchestrali`: matcha materiali tonali armonici densi. Da filtrare quando PANNs Orchestra/Musical instrument < 0.05 (qui Musical instrument 0.05 al limite).

## 4. Hum check

- **Verdetto complessivo skill**: presente (picchi a 120, 150, 180 Hz con ratio +11-14 dB vs baseline).
- **Reale**: falso positivo. I picchi a 120/150/180 Hz non sono ronzio di rete ma **armoniche strumentali** del drone tonale del brano (fondamentale intorno a 306 Hz con armoniche 613, 360, 818 Hz identificate dall'agente).
- **Hint contestuale "likely_musical_harmonic"** v0.5.1: è scattato correttamente. Il PDF mostra la frase: "Contesto: materiale tonale (flatness 0.005) con classificatore dominante Music (0.68): picchi a 120 Hz, 150 Hz, 180 Hz probabilmente armoniche strumentali, non rumore di rete." **Funziona**.

## 5. Mapping accademico (academic_hints)

- **Krause**: antropofonia 51% / mista 36% / biofonia 7% / geofonia 5% → **corretto in senso compositivo** (il brano è musica elettroacustica quindi antropofonia di massima). La presenza biofonia 7% è residuo delle allucinazioni CLAP ("insetti"), non reale.
- **Schafer (keynote/signal/soundmark)**: sound-object + signal + soundmark → OK, le campane registrate sono un soundmark canadese (Notre-Dame de Québec).
- **Schaeffer type**: tenuto 38%, tenuto-evolutivo 32% → **corretto**, è esattamente la morfologia del brano (tenuto dilatato con evoluzione lenta interna).
- **Smalley motion**: flow 37%, turbulence 28% → **corretto**, il flow è la categoria dominante per un drone che si accumula e si sottrae.
- **Schaeffer detail (TARTYP)**: morphing 67% (high confidence) → **molto corretto**, la tecnica centrale di Truax è proprio il cross-morphing granulare.
- **Smalley growth**: dilation 42% (high confidence) → **perfetto**, il time-stretch 20x è la definizione di dilation.
- **Chion modes**: ridotto + semantico + causale + misto → OK, il brano invita all'ascolto ridotto (Schaeffer) sulla materia tonale.
- **Westerkamp soundwalk relevance**: non menzionato. Qui sarebbe pertinente richiamare la scuola WSP (Vancouver) come contesto di provenienza delle registrazioni originali.

## 6. Lessico CLAP vs terminologia musicale corretta

- `Texture granulare densa` → OK, corrisponde a *granular synthesis* (Roads 2004) ma manca riferimento al **PODX system** e al **real-time granular synthesis** come tecnica specifica di Truax.
- `Time-stretch estremo di oggetto concreto` → OK, coglie. Forse più preciso: *time-stretching dello spettro* o *phase-vocoder time-stretching* (Truax usava il PODX, non il phase vocoder standard, ma per un analizzatore non-specialistico va bene così).
- `Profilo dinamico in morphing continuo` → OK, *cross-synthesis* / *granular morphing* sarebbe più preciso.
- `Trasformazione spettrale progressiva` → OK, è *spectral morphology* in senso Smalley.
- `Voce umana manipolata acusmatica` → falso positivo, da rimuovere.
- `Insetti in texture densa su corteccia` → falso positivo, da rimuovere.

## 7. Sezioni compositive (timeline manuale)

La skill ha rilevato 5 sezioni via changepoint detection (S1 00:00-07:40, S2 07:40-10:00, S3 10:00-10:30, S4 10:30-11:50, S5 11:50-11:53). Manuale proposto:

| Sezione | Tempo | Evento principale | Note |
|---------|-------|-------------------|------|
| Apertura | 00:00-00:30 | entrata del drone tonale su fondamentale 306 Hz, texture granulare già presente ma rada | skill: correttamente segnalata nella lettura drammaturgica come "respiro iniziale" |
| Accumulazione | 00:30-02:30 | densificazione progressiva (onset da 1.4/s a 6.6/s), salita del centroide fino a 2025 Hz | skill segnala "accumulazione" nella lettura drammaturgica |
| Plateau tonale | 02:30-07:30 | cinque minuti di tenuto-evolutivo, morphing continuo, flow Smalley dominante, cross-sintesi fra strati tonali e granulari | skill: coglie bene |
| Scurimento | 07:30-10:00 | centroide crolla da 2000+ Hz a 869 Hz, ingresso camera più profonda | skill segnala bene "Scurirsi" |
| Decadimento | 10:00-11:30 | caduta dinamica di 15 dB, falso-positivo "Train" su bande basse stretched | skill coglie l'artefatto e lo scarta correttamente (patch #1 v0.6.4) |
| Sottrazione finale | 11:30-11:54 | quasi-silenzio con ultimo lembo a -83 dB | skill: OK |

La segmentazione automatica combacia ragionevolmente con l'articolazione percepita. Suggerimento: la "Accumulazione" 00:30-02:30 meriterebbe essere una sezione distinta (non fusa nella S1 00:00-07:40 di 460s).

## 8. Lettura compositiva dell'agente

- **Pertinente?**: sì, lettura credibile e ben scritta. Alcuni passaggi sono di ottima qualità:
  - "Un drone di quasi dodici minuti che respira. L'opera non racconta eventi, racconta una dilatazione."
  - "Il drone tonale ha trovato la sua maschera granulare." (plateau 02:30-07:30)
  - "Decadimento e falso treno (10:00-11:30) ... È con ogni probabilità un artefatto di classificazione sulle bande basse stretched, non un documento ferroviario. Si ignora."
- **Parentele stilistiche: gap**: l'agente propone "Area acusmatica post-GRM con orientamento microsound", Curtis Roads (*Point Line Cloud*, *Clang Tint*), Éliane Radigue (*Trilogie de la Mort*, *Naldjorlak*), Francisco López, Robert Henke. **Manca completamente la scuola di appartenenza reale**: Vancouver Soundscape Project (WSP) / Simon Fraser University (SFU) canadese, di cui Truax è figura centrale insieme a Westerkamp e Schafer. Questo gap è sistematico (già emerso in v0.6.3/v0.6.4) e la regola WSP-vs-GRM v0.6.4 era stata rimossa in v0.6.5 perché causava bias opposto. Serve una formulazione più fine: riconoscere la **tradizione soundscape canadese** come parentela valida per materiali che combinano (a) field recording di soundmark + (b) granular synthesis + (c) tenuti dilatati, senza però forzarla su altro granular non-canadese.
- **Suggerimenti compositivi**: ottimi, drammaturgici e performativi. "Diffusione in acousmonium con la coda spazializzata in cupola alta", "Estratto autonomo della fascia 02:30-07:30 come pezzo installativo di cinque minuti in loop", "Dittico con un field recording biofonico non processato come contrappunto drammaturgico", "Laboratorio AFAM di composizione elettroacustica sulla fascia 07:30-10:00 come studio del morphing come principio formale", "Performance live con strumentista acustico (contrabbasso con archetto, violoncello, singing bowl) che raddoppia dal vivo la tonica a 306 Hz". Niente gesti DSP (Q/dB/ms/plugin). Regola v0.6.3 rispettata.

## 9. Note libere

### Risultati positivi (da consolidare)

1. **Regola v0.6.4 patch #1 (tag PANNs marginali contraddittori)**: funziona. Il falso positivo "Train" 0.047 non ha inquinato la lettura drammaturgica.
2. **Hint v0.5.1 `likely_musical_harmonic` sul hum**: funziona. I picchi 120/150/180 Hz sono stati contestualizzati come armoniche, non come ronzio.
3. **Filtro v0.5.1 allucinazioni speech-related**: funziona. "Voce umana manipolata acusmatica" (CLAP 0.195) correttamente marcato.
4. **Schaeffer detail (morphing 67% high) + Smalley growth (dilation 42% high)**: coppia descrittiva perfetta per questo brano. La tassonomia v0.6.0 è al livello giusto.
5. **Lettura drammaturgica v0.6.3**: ottima qualità interpretativa. L'agente costruisce un arco narrativo ("lunga espirazione", "accumulazione - sottrazione", "cerniera intorno a 7:30") coerente.

### Gap strutturali (patch candidate)

1. **Sorgente "campana" persa dal riconoscimento**. PANNs non vede Bell/Church bell. CLAP non ha prompt specifici per campane. Possibili azioni:
   - **Non aggiungere** prompt troppo specifici al vocabolario CLAP (lezione v0.6.4→v0.6.5).
   - Piuttosto, **istruire l'agente nel prompt template** che quando PANNs Music domina > 0.60 con materiale tonale (flatness < 0.01) e morphing (TARTYP) > 0.60, considerare come ipotesi di lavoro la presenza di sorgente concreta trasformata (campane, metalli, vetri) anche se non riconosciuta da PANNs. L'agente può segnalarlo come "ipotesi di materia sonora sorgente" senza trattarlo come fatto.

2. **Allucinazioni CLAP non biofoniche/non speech**. Tre tag falsi positivi sistematici nel top-10: "Insetti in texture densa", "Acqua del rubinetto che scorre", "Accordatura di strumenti orchestrali". Sono casi scolastici per **v0.7.0 plausibility check**:
   - `Insetti...` → plausibility `low` quando PANNs Insect/Cricket/Bird < 0.05.
   - `Acqua del rubinetto...` → plausibility `low` quando PANNs Water/Liquid/Stream < 0.05.
   - `Accordatura di strumenti orchestrali` → plausibility `low` quando PANNs Orchestra < 0.05.

3. **Parentele stilistiche: mancata tradizione WSP/SFU/Vancouver**. L'agente propone GRM/microsound/ambient ma non la scuola canadese. Questo è l'errore di attribuzione sistematico. Possibili formulazioni da inserire nel prompt dell'agente **senza creare bias**:
   - Regola contestuale: "Se il materiale combina (a) indizi di field recording non processato o soundmark riconoscibile + (b) granular synthesis estesa + (c) tenuti dilatati, considera la **tradizione soundscape canadese (WSP/SFU, Truax, Westerkamp, Schafer)** come parentela co-paritetica al GRM francese, non come alternativa".
   - Se non ci sono indizi di field recording → tradizione canadese NON prioritaria (evita regressione v0.6.4).

4. **Sezione "Accumulazione" 00:30-02:30 non emergente dalla segmentazione automatica**. La fusione in S1 00:00-07:40 (460s) perde un'articolazione drammaturgicamente rilevante. Forse da rivedere la soglia di changepoint detection su brani con transizioni graduali.

### Lezioni per il paper

- Caso emblematico del **gap PANNs su materiali elettroacustici trasformati**: una sorgente concreta riconoscibile (campana di chiesa) diventa invisibile al classificatore AudioSet dopo time-stretch estremo. Il classificatore percepisce solo il risultato ("Music"), non la genealogia.
- Caso emblematico del **bias di attribuzione stilistica** per LLM mediatori: senza metadati, l'agente tende al GRM francese come categoria default per materiali granulari dilatati, sovra-pesando la tradizione più rappresentata nella letteratura disponibile.
- La **triangolazione** fra PANNs (dato empirico percettivo), CLAP (etichette concettuali), academic_hints (tassonomia Schaeffer/Smalley) e agente compositivo (interpretazione drammaturgica) **funziona** come architettura: la lettura finale è più ricca della somma delle parti. Ma ogni layer ha i suoi errori sistemici, da documentare come limitazioni.
- La coppia **Schaeffer detail + Smalley growth** (morphing + dilation) si è dimostrata la descrizione analitica più precisa. Da verificare su altri brani stretched/granulari.
