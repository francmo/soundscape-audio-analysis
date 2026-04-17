# Feedback - Jean-Claude Risset, *Sud* part 1 (1985)

## 1. Identificazione

- **File**: `track_04.mp3` (copia anonimizzata, soundscape-training/audio_blind/)
- **Versione skill che ha prodotto il report**: v0.6.5, senza `--speech`
- **Data feedback**: 2026-04-17
- **Contesto del brano**: Jean-Claude Risset (1938-2016), *Sud* (1985), prima parte di un'opera in 3 parti per nastro stereo (durata totale 23:40). Commissione del Ministero della Cultura francese tramite GRM/INA. Materiale: field recording del Massiccio delle Calanques presso Marsiglia (mare, vento, insetti, uccelli) + sintesi MUSIC V (Faculté des Sciences di Luminy + Laboratoire de Mécanique et d'Acoustique CNRS) + suoni strumentali trattati. Processing: Studio 123 del GRM con sistema Syter. Principio strutturale: presentazione separata di naturale e sintetico, poi fusione progressiva. Parte 1 = **presentazione dei materiali naturali**, con le sintesi che si affacciano verso la fine. Risset co-fondatore con Chowning della ricerca sulla sintesi digitale del suono.
- **Gold analitico**: `Nottoli-04-Risset-Sud-part1/analisi-sfu-grm.md` + `analisi-Mitsialis.pdf`.

## 2. PANNs

### Top-1 globale

- **Skill dice**: `Music` (score 0.25, frame dominanti 36.7%)
- **Reale**: parzialmente corretto. A differenza dei tre brani precedenti, qui PANNs riconosce **esplicitamente la biofonia**: la distribuzione mostra Cricket (0.116), Insect (0.099), Water (0.047), Bird (0.042), Bird vocalization (0.040), Chirp/tweet (0.037), Boat/Water vehicle (3.3% frame). **Tutte corrispondenze col gold** (Calanques → cicale, uccelli, mare). **Primo brano del corpus dove PANNs fa il lavoro giusto sui materiali naturali**.

### Top-10 globali

| Posizione | Etichetta PANNs | Score | Valutazione |
|-----------|-----------------|-------|-------------|
| 1 | Music | 0.2549 | OK |
| 2 | **Cricket** | 0.1155 | **corretto**, cicale delle Calanques |
| 3 | **Insect** | 0.0995 | **corretto** |
| 4 | Speech | 0.0513 | debole/falso (no parlato nella parte 1) |
| 5 | **Water** | 0.0470 | **corretto**, mare e ruscelli |
| 6 | Chime | 0.0456 | **corretto**, sintesi MUSIC V idiofoniche |
| 7 | **Bird** | 0.0421 | **corretto**, uccelli delle Calanques |
| 8 | Musical instrument | 0.0410 | OK |
| 9 | **Bird vocalization/call/song** | 0.0398 | **corretto** |
| 10 | **Chirp/tweet** | 0.0367 | **corretto** |

### Frame dominanti

- Music 36.7%, **Cricket 13.3%**, **Water 6.7%**, Environmental noise 5%, **Bird vocalization 5%**, **Boat/Water vehicle 3.3%**, Speech 3.3%, **Insect 3.3%**. Distribuzione ecologicamente coerente col gold.

## 3. CLAP

### Top-10 globali

| Posizione | Prompt italiano | Score | Pertinente? | Note |
|-----------|-----------------|-------|-------------|------|
| 1 | **Acqua del rubinetto che scorre** | 0.245 | **parzialmente** | c'è acqua (mare/ruscelli) ma non da rubinetto |
| 2 | Profilo dinamico in morphing continuo | 0.245 | sì |
| 3 | Time-stretch estremo di oggetto concreto | 0.227 | sì |
| 4 | Texture granulare densa | 0.225 | sì |
| 5 | Preghiera collettiva sussurrata in chiesa | 0.222 | **no, allucinazione** (no voce coranica) |
| 6 | Accumulo granulare stocastico | 0.220 | sì |
| 7 | Grandine che cade su superficie dura | 0.220 | **no, allucinazione** (onsets letti come grandine) |
| 8 | Trasformazione spettrale progressiva | 0.211 | sì |
| 9 | Porta di legno che si apre e si chiude | 0.208 | possibile (porte dell'apertura?) |
| 10 | Percussioni leggere e ritmiche | 0.204 | sì (sintesi idiofoniche) |

### Tag segmentali rilevanti

Positivi (corretti o pertinenti):
- `Acqua che sgorga da fontana pubblica` (00:10-00:20), `Acqua che scorre in un ruscello` (00:20-00:30): **corretti** per l'apertura del brano.
- `Cicale in campagna estiva del sud Italia` (01:20-01:30 e molte altre): **pertinente** come materiale biofonico, ma **errato geograficamente** (Marsiglia, non Italia). Tag italo-specifico flaggato.
- `Grilli nella sera estiva` (01:30-01:40): OK biofonica.
- `Gallo che canta all'alba in villaggio costiero` (01:40-01:50): plausibile ma non sicuro.
- `Wind chime` e `Tubular bells`, `Chime`, `Glockenspiel`, `Mallet percussion`, `Tonalità bassa continua come drone` (03:00-05:30): **catturano le sintesi MUSIC V** di Risset che simulano idiofoni (caratteristica centrale del suo lavoro sulla sintesi spettrale).
- `Campane piccole di chiesa di paese` (08:10-08:20, 08:30-08:50, 08:50-09:10): potrebbe essere risonanza metallica, dubbio.
- `Goccia d'acqua che cade in ambiente chiuso` (08:30-09:00): coerente con acqua delle Calanques.

Negativi (allucinazioni italo-specifiche):
- `Osteria pomeridiana con stoviglie e voci` (00:40-01:10, 02:00-02:10, 07:30-07:50): italo-specifico, matcha su voci/stoviglie/ambiente chiuso non presenti.
- `Aula di conservatorio italiano con esercizi simultanei` (00:40-00:50, 09:20-09:30): italo-specifico.
- `Pianoforte solista in studio` (03:10-03:20, 04:50-05:00), `Scale ripetute al pianoforte da studente` (05:10-05:20): **interessante**: CLAP legge le sintesi MUSIC V di Risset come piano da studio. Non del tutto errato (le sintesi additive ricordano piani ed è il tratto storico del lavoro di Risset sulla sintesi strumentale), ma fuori contesto.
- `Vicolo di borgo medievale con passi e eco` (09:10-09:20), `Vicolo bianco di villaggio mediterraneo con passi e eco` (09:10-09:20): allucinazioni italo-specifiche su riverbero.
- `Pianto infantile prolungato` (09:40-09:50): allucinazione finale.
- `Paesaggio sonoro di borgo rurale italiano` (09:20-09:30): italo-specifico.

### Prompt CLAP mancanti

**Sintesi MUSIC V / sintesi additiva storica** (lavoro di Risset al CNRS-Luminy):

- `Sintesi additiva di suoni percussivi`.
- `Sintesi strumentale spettrale con partials decrescenti`.
- `Campana sintetica di Risset con spettro modulato`.
- `Cross-sintesi timbrica fra field recording e strumento sintetico`.

**Syter processing GRM**:

- `Filtraggio spettrale in tempo reale su field recording`.
- `Iterazione granulare con controllo parametrico` (caratteristica Syter).

**Paesaggio mediterraneo francese**:

- `Calanques mediterranee con mare e vento` (per bilanciare i tag italo-specifici).
- `Paesaggio costiero provenzale con cicale`.
- `Insetti mediterranei francesi in macchia` (distinto da "Sud Italia").

Il gold dichiara che la copertina del CD rappresenta "analisi della fine di un suono fischiato" (sonogramma): questa dimensione analitica-spettrografica meriterebbe prompt come `spettrografia sonora di materiale fischiato`, `analisi spettrale visualizzata`.

### Prompt CLAP da rivedere

Già noti dai brani precedenti:
- `Acqua del rubinetto che scorre` top-1 globale: **quarta occorrenza**. Qui è parzialmente pertinente (c'è acqua) ma il prompt specifico "rubinetto" è sempre falso. Da convertire in `Acqua corrente in ambiente naturale o domestico` per coprire più casi senza ambiguità, o mantenere specifico ma con plausibility-check rigoroso.
- `Aula di conservatorio italiano con esercizi simultanei`, `Osteria pomeridiana con stoviglie e voci`, `Vicolo di borgo medievale`, `Paesaggio sonoro di borgo rurale italiano`: catena italo-specifica che **compromette la lettura geografica**. Pericoloso: la geografia è cruciale per capire il corpus acusmatico francese (GRM) vs italiano (Fonologia RAI).

## 4. Hum check

- **Verdetto complessivo skill**: trascurabile.
- **Reale**: corretto. Registrazione pulita, nessun ronzio reale.

## 5. Mapping accademico

- **Krause**: antropofonia 62%, mista 27%, geofonia 5%, biofonia 4% → **inconsistenza interna** rispetto a NDSI +0.516 (biofonia > antropofonia) e frame PANNs (Cricket 13.3%, Water 6.7%, Bird 5%, Insect 3.3% = 28% frame biofonici dominanti). Il calcolo Krause dai tag CLAP top-10 è dominato da prompt antropofonici (acqua rubinetto, preghiera, osteria, porta legno) che non riflettono la realtà del brano. **Bug di coerenza fra hint accademici e indici ecoacustici**: da investigare come patch per v0.6.6.
- **Schafer**: sound-object + soundmark + signal → OK, le Calanques sono soundmark provenzale (anche se l'agente non lo localizza).
- **Schaeffer type**: tenuto 29%, trama 24% → coerente con materiale elettroacustico + ambiente continuo.
- **Smalley motion**: turbulence 32%, flow 25% → OK (vento, mare, cicale).
- **Schaeffer detail**: cross-sintesi 38% (high) → **categoria centrale per questo brano**, e l'agente la cita "dettaglio schaefferiano dominante". Combacia con la tecnica di Risset (cross-sintesi fra naturale e sintetico).
- **Smalley growth**: endogeny 53% (high) → coerente con crescita interna al materiale.
- **Chion modes**: causale + ridotto + semantico → OK.
- **Truax listening mode**: search → l'agente cita "Truax classifica il materiale come 'search'", che è coerente con un brano che esplora soundscape.
- **Westerkamp soundwalk relevance**: l'agente dice "non un soundwalk descrittivo, ma un viaggio timbrico che usa il field recording come punto di partenza e lo spinge verso la cross-sintesi". **Formulazione precisa e corretta**.

## 6. Lessico CLAP vs terminologia musicale

- `Profilo dinamico in morphing continuo`, `Cross-sintesi fra due suoni concreti`, `Trasformazione spettrale progressiva` → descrivono bene il **morphing** di Risset fra naturale e sintetico. Terminologia allineata a Smalley (spectromorphology).
- `Wind chime`, `Tubular bells`, `Glockenspiel`, `Mallet percussion` → corrispondono alle **sintesi additive di Risset** che simulano idiofoni metallici. Concetto estetico: sintesi strumentale spettrale (Risset fu pioniere).
- `Tonalità bassa continua come drone` → coglie il **drone armonico di fondo** del passaggio 04:00-05:30 (cuore lirico del brano).

## 7. Sezioni compositive

La skill ha rilevato 5 sezioni con **firme Krause coerenti** (prima volta nel corpus Nottoli):

| Sezione skill | Tempo | Krause | Note |
|---------------|-------|--------|------|
| S1 "sezione mista soffusa" | 00:00-01:20 | mista | apertura con acqua/porte/voci |
| S2 "antropofonia moderata tonale" | 01:20-04:30 | antropofonia | materiali umani + cicale + gallo |
| S3 "antropofonia moderata tonale" | 04:30-06:10 | antropofonia | carillon/tubular bells synth (sintesi MUSIC V) |
| S4 "biofonia soffusa mista" | 06:10-09:40 | **biofonia** | notturno biofonico finale (cicale dominanti) |
| S5 "quasi-silenzio" | 09:40-09:52 | silenzio | chiusura |

**Primo caso del corpus** dove la segmentazione Krause riflette un passaggio biofonico esplicito. Ottimo risultato.

Il gold dichiara come principio strutturale: "i suoni naturali e sintetici sono prima presentati separatamente". Per la parte 1, la skill ha colto: apertura domestica/acqua → ambiente naturale → introduzione sintesi → ritorno biofonica. Coerente.

## 8. Lettura compositiva

**Eccellente**. L'agente ha fatto la migliore attribuzione stilistica del corpus fin qui:

- **"Scuola acusmatica GRM con inflessione soundscape"**: **esattamente corretto** (GRM è la scuola di Risset).
- **"Luc Ferrari per l'aggancio concreto iniziale (porta, acqua, osteria) e per l'arco narrativo"**: parentela **perfetta** (Presque Rien + GRM).
- **"Barry Truax e la soundscape composition canadese per l'uso del granulare come processo di trasformazione del documento ecosonoro (l'hint Truax 'search' lo corrobora)"**: parentela secondaria pertinente, con **giustificazione empirica esplicita** (hint Truax listening mode). Nuovo standard qualitativo.
- **"In filigrana, una memoria di Parmegiani (De Natura Sonorum) per il passaggio morfologico fra materiale concreto e oggetto musicale"**: parentela tertiaria GRM-coerente (Parmegiani è GRM contemporaneo di Risset).
- **"Il tag CLAP 'Aula di conservatorio italiano' è geo-specifico con bassa corroboranza e va trattato con prudenza, ma il materiale resta compatibile con la produzione elettroacustica italiana di studio"**: qui l'agente **sbaglia la localizzazione geografica** (Sud è francese, non italiano). L'apertura tagliata come "lavandino domestico italiano" è basata sui tag italo-specifici scartati ma reincorporati come "compatibilità italiana". Regola geo_specific necessita rinforzo: se gli altri indizi (GRM ref, Ferrari ref, Syter timing) puntano a scuola francese, la compatibilità italiana va negata, non tollerata.

**Binomi concettuali eccellenti**: domestico/paesaggio, concreto/trasformato, strumento/ambiente, accumulo/silenzio. **Tutti centrati**.

**Scene sonore in 6 blocchi**:
- Soglia domestica (00:00-01:30): apertura con acqua, stoviglie, porta.
- Alba e insetti (01:30-02:30): uccelli, gallo, cicale.
- Morphing verso il suono musicale (02:30-04:00): introduzione sintesi (piano Music 0.71, Keyboard, glockenspiel).
- Carillon crepuscolare (04:00-05:30): wind chime, tubular bells, mallet percussion, drone tonale.
- Accumulo granulare e cicale reali (05:30-08:00): ritorno della biofonia su texture granulare + time-stretch.
- Crepuscolo biofonico e dissolvenza (08:00-09:53): cicale dominanti, dissolvenza finale.

Struttura drammaturgica coerente con la sezione 1 del gold (materiali separati, con le sintesi che entrano verso il centro).

**Suggerimenti compositivi**: eccellenti e pedagogici:
- Acousmonium con tre fasce (soglia domestica frontale, carillon interno, biofonia finale in cupola alta).
- Versione installativa in loop per spazio museale o sito naturalistico mediterraneo.
- Laboratorio AFAM sulla zona centrale 02:30-05:30 come caso di cross-sintesi e morphing.
- **Dittico di programmazione con Presque Rien N°2 di Ferrari o Riverrun di Truax** → suggerimento programmatico-curatoriale preciso.
- Proiezione video curata separatamente, non illustrativa.

## 9. Note libere

### Positivi rilevanti per il paper

1. **PANNs funziona benissimo su biofonia mediterranea non processata**: Cricket, Insect, Water, Bird, Chirp sono nei top-10 con score moderati ma coerenti. A differenza di *Basilica* dove tutto era "Music 97%", qui c'è **granularità ecologica**.
2. **NDSI positivo +0.516** — unico del corpus — riflette correttamente la biofonia dominante nelle sezioni 06:10-09:40. Indice ecoacustico usato come proxy estetico funziona.
3. **Sezioni strutturali con Krause differenziato** (S4 biofonia soffusa mista): prima volta nel corpus dove il changepoint detection intercetta un passaggio Krause significativo.
4. **Attribuzione stilistica GRM corretta** e con giustificazione empirica (hint Truax "search" a corroborazione della parentela soundscape). Nuovo livello qualitativo.
5. **Ferrari + Parmegiani + Truax** in filigrana: parentele accurate e articolate. L'agente ha fatto **triangolazione corretta** senza forzare su una sola scuola.
6. **CLAP coglie sintesi MUSIC V come idiofoni**: wind chime, tubular bells, glockenspiel, pianoforte solista, mallet percussion, scale ripetute. È la **firma timbrica storica di Risset** (sintesi additiva di suoni percussivi). La rete non sa che è MUSIC V ma ne cattura il risultato timbrico.
7. **Schaeffer detail cross-sintesi 38% high**: categoria descrittiva perfetta per il brano. L'agente la usa esplicitamente.

### Gap strutturali per il paper

1. **Localizzazione geografica sbagliata**: il vocabolario CLAP italo-specifico ha fatto pendere la lettura verso "produzione elettroacustica italiana di studio" quando il brano è **francese GRM**. La regola `geo_specific=True` di v0.5.2 ha flaggato i tag in corsivo ma l'agente li ha parzialmente riassorbiti. Serve una regola di **esclusione attiva**: se parentele forti e indipendenti puntano a scuola non italiana (GRM, WSP, WDR), negare la compatibilità italiana esplicitamente.

2. **Inconsistenza interna Krause**:
   - NDSI (calcolato su spettro) = +0.516 (biofonia > antropofonia).
   - Krause hint accademico (calcolato da top tag CLAP) = antropofonia 62%, biofonia 4%.
   - PANNs frame dominanti biofonici = ~28%.
   
   I tre segnali sono discordanti perché calcolati da fonti diverse. Per il paper: **documentare come limitazione metodologica**. Per la skill: **riallineare** il calcolo Krause hint dai tag CLAP con pesi che tengano conto anche di PANNs biofonici dominanti.

3. **Vocabolario CLAP per sintesi storica assente**: MUSIC V, Syter, Csound, sintesi additiva di Risset/Chowning non sono rappresentati direttamente. La rete sostituisce con "pianoforte solista in studio" o "wind chime", soluzioni parziali. Aggiungere categoria `sintesi digitale storica` al vocabolario v1.7.

4. **L'apertura "soglia domestica" è un'interpretazione errata** costruita sui tag italo-specifici ("lavandino", "osteria"): il materiale sono le **Calanques mediterranee all'alba**, non una cucina. Qui il bias italo-specifico del vocabolario ha deformato la lettura in modo semanticamente grave (interno domestico vs esterno naturalistico). Da documentare come errore di tipo categoriale.

### Patch candidate

**v0.6.6 (immediate)**:
- Aggiungere categoria `paesaggi mediterranei francesi` e/o `paesaggi mediterranei generici` (v0.5.2 l'aveva introdotta ma serve rinforzarla con prompt nuovi: `Macchia mediterranea con cicale`, `Costa rocciosa con vento e mare`, `Calanques provenzali all'alba`).
- Rimuovere o plausibility-filtrare `Osteria pomeridiana con stoviglie e voci` quando PANNs Speech < 0.10 (qui Speech 0.051).
- Plausibility-filtrare `Aula di conservatorio italiano con esercizi simultanei` quando PANNs Music < 0.40 (qui Music 0.25 al limite).

**v0.7.0 (plausibility check)**:
- `Acqua del rubinetto che scorre` su Sud: qui è **parzialmente** pertinente (c'è acqua ambientale reale). Regola: se PANNs Water > 0.04 AND PANNs Stream/Liquid > 0.02 → plausibility `medium` (c'è acqua ma il prompt specifico rubinetto resta inappropriato). Altrimenti `low`. Su *Basilica*/*Song of Songs*/*Fabbrica* era `low`; qui `medium`.

**v0.6.6 (consistenza Krause)**:
- Investigare calcolo `distribuzione_krause` in `clap_mapping.aggregate_academic_hints`. Probabilmente somma i prompt top con categoria biofonia/antropofonia/geofonia pesata su score. Aggiungere peso da **PANNs frame dominanti biofonici** (Insect, Cricket, Bird, Water) in modo da allineare con NDSI.

**Prompt agente**:
- Regola: se `geo_specific=True` su più di 3 tag consecutivi e altre evidenze (parentele stilistiche, NDSI biofonica, cicale/uccelli in PANNs) puntano a paesaggio mediterraneo senza localizzazione italiana specifica, **dichiarare esplicitamente** "paesaggio mediterraneo non univocamente italiano, compatibile con contesto francese/greco/maghrebino" invece di "compatibile con produzione italiana".

### Lezioni per il paper

- **Brano di riferimento positivo**: Sud mostra che la skill **funziona bene** quando il materiale è field recording naturale + sintesi leggera. PANNs cattura la biofonia, CLAP cattura i sonorities strumentali delle sintesi, gli academic hints (cross-sintesi, endogeny, Truax search) si allineano, l'agente triangola la scuola corretta (GRM + Ferrari + Parmegiani + Truax).
- **Brano di riferimento negativo sulla geografia**: il vocabolario italo-specifico deforma la lettura di un brano mediterraneo francese. Caso scuola per discutere i bias linguistico-geografici del vocabolario CLAP in italiano.
- **Caso scuola per il paper sulla triangolazione multi-layer**: PANNs (cricket/insect/water/bird), CLAP (acqua, cicale, wind chime, tubular bells), academic hints (cross-sintesi 38%, endogeny 53%, Truax search), agente (scuola GRM + Ferrari + Truax + Parmegiani). Tutti i layer contribuiscono alla lettura finale corretta. Dimostrazione di **sinergia architetturale**.
- **Il vocabolario deve distinguere geograficamente**: paesaggi mediterranei italiani vs francesi vs greci vs maghrebini. Senza questa dimensione, brani canonici (Sud, Kontakte di Stockhausen, Presque Rien) rischiano di essere mal-attribuiti.
