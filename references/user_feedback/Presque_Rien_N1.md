# Feedback utente: Luc Ferrari, *Presque Rien N°1 ou Le lever du jour au bord de la mer* (1967-70)

Compilato da Francesco Mariano (assistito da Claude) sulla base del report
`audio3_report.pdf` generato dalla skill v0.5.1 e da fonti accademiche
disponibili in rete. Brano analizzato senza ascolto diretto da parte
dell'estensore di queste note: il confronto e' fra dati della skill e
letteratura accademica del brano, non fra dati e percezione personale.

---

## 1. Identificazione

- **File**: `audio3.mp3` (originale: *Presque Rien N°1*, 21 min, ed. Deutsche Grammophon 1970, ristampato in Bandcamp Luc Ferrari Complete Works 04)
- **Versione skill che ha prodotto il report**: `v0.5.1`
- **Data feedback**: `2026-04-15`
- **Contesto del brano**:
  > *Presque Rien N°1 ou Le lever du jour au bord de la mer* (1967-70) di
  > Luc Ferrari (1929-2005), co-fondatore del GRM con Pierre Schaeffer.
  > Registrato a Vela Luka, isola di Korcula, Croazia (allora Jugoslavia)
  > nell'estate 1967-1968 con microfono posizionato sul davanzale di una
  > finestra; sessioni quotidiane dalle 4 alle 6 del mattino. Composto
  > nello studio Deutsche Grammophon di Hannover (gennaio-febbraio 1970)
  > con interventi minimi: condensazione di un'intera giornata di field
  > recording in 21 minuti, mantenendo il senso documentale e
  > psicogeografico dell'alba in un porto peschereccio. E' opera
  > fondativa della soundscape composition (ante-litteram rispetto a
  > Schafer 1977) e del concetto di "musica aneddotica" formulato da
  > Ferrari stesso. Alla prima presentazione al GRM fu accolto male
  > ("non era musica"); ebbe risonanza forte negli USA e in Scandinavia.

## 2. PANNs (classificazione semantica primaria)

### Top-1 globale

- **Skill dice**: `Speech` (score `0.2938`)
- **Reale**:
  - [x] corretto in valore relativo, sotto-stimato in valore assoluto. Il brano contiene effettivamente molto parlato (pescatori, bambini, voci di mercato della comunita' croata), e Speech 48% nei `top_dominant_frames` lo conferma. Lo score 0.29 e' basso perche' le voci sono in lingua slava, distanti, sovrapposte ad ambiente.

### Top-10 globali

| Posizione | Etichetta PANNs | Score | Valutazione |
|-----------|-----------------|-------|-------------|
| 1 | Speech | 0.2938 | OK (parlato croato di pescatori) |
| 2 | Insect | 0.1405 | OK (cicale, grilli, alba mediterranea) |
| 3 | Vehicle | 0.1389 | OK (motorette, jeep, pescherecci) |
| 4 | Cricket | 0.1279 | OK (sotto-categoria di Insect) |
| 5 | Animal | 0.0750 | OK generico |
| 6 | Frog | 0.0665 | <da verificare: alba marittima, plausibile rane di stagni costieri> |
| 7 | Music | 0.0586 | OK (radio o canti di pescatori, c'e' una sezione musicale verso meta'; Ferrari documenta "fisarmoniche, musica popolare slava") |
| 8 | Outside, rural or natural | 0.0380 | OK (rural village outdoor) |
| 9 | Engine | 0.0372 | OK (motori marini) |
| 10 | Train | 0.0338 | <falso positivo: a Vela Luka non c'erano treni; probabilmente confusione con motore marino o motopesca> |

### Frame dominanti (`top_dominant_frames`)

- **Speech 48% / Vehicle 12% / Cricket 9.6% / Frog 7.2% / Insect 4.8% / Music 3.2% / Animal 2.4% / Train 2.4%**
- **Coerenza con la mia conoscenza del brano**:
  > Speech 48% e' coerente con la presenza pervasiva di voci umane lungo
  > l'arco dei 20 minuti. Vehicle + Cricket + Frog + Insect (33%) sono
  > coerenti con l'ambiente rurale costiero. Music 3% e' verosimile
  > (presenza occasionale di radio o canto). Train 2.4% e' un falso
  > positivo da rumore meccanico generico.
  > **Mancano**: tag espliciti per acqua (mare/onde, stoviglie, sciabordio
  > di barche), galli (importante: Ferrari scrive di "galli che cantano
  > all'alba" come marker temporale), bambini.

## 3. CLAP (auto-tagging italiano)

### Top-10 globali

| Posizione | Prompt italiano | Score | Pertinente? | Note |
|-----------|-----------------|-------|-------------|------|
| 1 | Acqua del rubinetto che scorre | 0.212 | NO, allucinazione | Match probabilmente con sciabordio del mare/onde leggere o con sciacquio di pesce. Brano non ha rubinetti. |
| 2 | Preghiera collettiva sussurrata in chiesa | 0.208 | NO, allucinazione grossa | Le voci in lontananza e i sussurri di pescatori sono confusi con preghiere. Non c'e' chiesa nel brano. |
| 3 | Vento fra alberi | 0.185 | parziale | C'e' brezza marina di alba ma non e' vento fra alberi. |
| 4 | Gufo notturno nel bosco | 0.185 | NO, allucinazione | Non e' bosco e non e' notte (e' alba sul mare). Match probabilmente con qualche grido isolato. |
| 5 | Cicale in campagna estiva del sud Italia | 0.176 | parziale | Cicale presenti, ma non sud Italia: e' Croazia mediterranea. Il prompt e' troppo geo-specifico. |
| 6 | Paesaggio sonoro di borgo rurale italiano | 0.169 | parziale | Borgo rurale si', ma croato non italiano. Stesso problema. |
| 7 | Grilli nella sera estiva | 0.161 | parziale | Insetti ortotteri presenti, ma e' alba non sera. Discrepanza temporale. |
| 8 | Discussione di vicini dalle finestre | 0.148 | OK | Pescatori che si chiamano dalle barche al porto: simile a "vicini dalle finestre" come tipologia (parlato outdoor in lingua locale). |
| 9 | Vicolo di borgo medievale con passi e eco | 0.147 | NO, allucinazione | Vela Luka non e' borgo medievale, e' porto peschereccio settecentesco. Match probabilmente con passi su molo. |
| 10 | Cinguettio di passeri in giardino | 0.146 | parziale | Uccelli presenti (gabbiani, passeriformi), ma non in giardino: in porto. |

### Tag flagged come allucinazioni (corsivo nel PDF v0.5.1)

> Va verificato nel PDF se i tag "Discussione di vicini dalle finestre"
> e "Preghiera collettiva sussurrata in chiesa" sono effettivamente in
> corsivo. PANNs Speech 0.29 e Speech 48% nei frame dominanti
> *dovrebbero* superare le soglie di hallucination (0.10 / 5%) e quindi
> i tag NON dovrebbero essere flagged. Il filtro v0.5.1 in questo caso
> non scatta perche' il parlato c'e' davvero, anche se in lingua slava.
> **Implicazione per la skill**: il filtro hallucination corrente non
> distingue fra "PANNs vede voce ma il prompt CLAP descrive una scena
> diversa" (es. preghiera vs pescatori). Servirebbe un secondo livello
> di check semantico fra prompt CLAP e contesto generale.

### Prompt CLAP mancanti (proposte per v0.5.2)

Eventi sonori del brano non coperti dal vocabolario v1.2:

- `pescatori che chiamano dalle barche in porto`
- `sciabordio di onde leggere su scogli o molo`
- `gallo che canta all'alba in villaggio costiero`
- `motore di peschereccio diesel di piccolo cabotaggio`
- `bambini che giocano in lingua straniera in piazza`
- `voci slave lontane in dialogo informale`
- `mare calmo di prima mattina con leggero rifrangere`
- `passi su molo di legno o pietra`
- `radio popolare a basso volume con musica tradizionale`
- `tintinnio di catene di barca o pesi da pesca`
- `clacson lontano di nave o sirena di porto`
- `uccelli marini (gabbiani) in volo distante`

### Prompt CLAP da rivedere

- `Acqua del rubinetto che scorre` (categoria antropofonia domestica): match
  troppo facile con qualunque liquido in movimento, produce allucinazioni
  su brani con onde/sciabordio. Valutare se restringere il prompt o
  aggiungere prompt distinti per "onde leggere", "sciabordio mare calmo".
- `Preghiera collettiva sussurrata in chiesa` (sacralita sonora): match
  troppo facile con voci sussurrate generiche. Valutare se il prompt deve
  esplicitare elementi acusticamente distintivi (riverbero di navata).
- I prompt geograficamente troppo specifici (`sud Italia`, `borgo
  medievale`, `marchigiano`) producono falsi negativi su materiale
  mediterraneo NON italiano. Valutare versioni piu' geograficamente
  generiche da affiancare.

## 4. Hum check

- **Verdetto complessivo skill (v0.5.1)**: `presente` (50 Hz: +16.82 dB ratio, picco a 48.8 Hz)
- **Reale**:
  - [x] corretto, hum residuo plausibile. Le registrazioni Nagra del 1967 con microfono dinamico sul davanzale catturavano comunemente residui di rete elettrica (specie in zone con cablaggio precario come la Vela Luka di fine anni '60). Il picco a 50 Hz e' coerente con la rete europea. Inoltre il dimensionamento (+16.8 dB sopra baseline) e' significativo ma non disturbante in ascolto.
- **Hint contestuale "likely_musical_harmonic"** (v0.5.1):
  - [x] non scattato — corretto. La flatness 0.0403 e' sopra la soglia 0.05? No, e' SOTTO 0.05, quindi astrattamente il filtro potrebbe scattare. Ma il top-1 PANNs e' "Speech" che NON e' in `MUSICAL_INSTRUMENT_LABELS`, quindi il filtro non scatta. Comportamento corretto: in questo caso il hum *e'* probabilmente ronzio elettrico genuino, non armonica strumentale, e quindi la skill ha fatto bene a NON marcarlo come musicale.
- **Suggerimento operativo**: nei "Gesti compositivi" l'agente skill suggerisce notch filter Q stretto a 50/100/150 Hz prima di mastering. Suggerimento corretto.

## 5. Mapping accademico (academic_hints)

Hint riportati dalla skill:

- **Krause**: `antropofonia 32%, biofonia 26%, mista 26%, geofonia 14%`
- **Schafer roles presenti**: `sound-object, soundmark, keynote, signal`
- **Schafer fidelity**: `hi-fi`
- **Schaeffer type**: `trama 64%, tenuto 35%`
- **Smalley motion**: `turbulence 64%, flow 35%`
- **Chion modes**: `causale, semantico, misto`
- **Westerkamp soundwalk relevance**: `sì (42%, ipotesi)`

Valutazione critica:

- **Krause**: la distribuzione antropofonia 32% / biofonia 26% / geofonia 14% e' **plausibile**. Il brano e' reale soundscape misto: pescatori, animali, mare. Il mare 14% sembra sotto-stimato (geofonia dovrebbe essere piu' alta in un porto), ma e' difetto dei prompt CLAP "geofonia" che includono prevalentemente vento e pioggia, non onde marine.
- **Schafer roles**: presenza di tutti e quattro i ruoli (`sound-object, soundmark, keynote, signal`) e' **corretta** per soundscape ricco. In particolare il *galli che cantano* e *campane di Vela Luka* (se presenti) sono soundmark canonici nel senso di Schafer.
- **Hi-Fi**: corretto. Ferrari registra in luogo silenzioso (Vela Luka anni '60, prima del turismo di massa) con buona separazione delle sorgenti.
- **Schaeffer "trama 64%"**: corretto. Il brano e' dominato da texture continue (cicale, mare, voci diffuse) piu' che da impulsi netti.
- **Smalley turbulence 64%**: corretto. Il fitto delle cicale e l'attivita' biofonica creano turbolenza spettrale costante.
- **Chion misto**: corretto. Il brano richiede ascolto causale (riconoscere fonti) ma anche semantico (capire frammenti di parlato) e ridotto (godere della texture astratta).
- **Westerkamp soundwalk relevance: si' (42%, ipotesi)**: corretto. Il brano e' ESATTAMENTE quello che Westerkamp avrebbe definito "deep listening on a soundwalk", anche se Vela Luka e' stato registrato in posizione fissa, non camminando.

## 6. Lessico CLAP vs terminologia musicale corretta

Coppie da arricchire:

- `Discussione di vicini dalle finestre` → in soundscape composition: `voci anonime in scena urbana/rurale`, `community speech`. In Ferrari: `parlato aneddotico` (terminologia coniata dall'autore).
- `Preghiera collettiva sussurrata in chiesa` → contesto reale: `voci sussurrate in lontananza`, `whispered speech distant`. La distinzione fra preghiera e voci sussurrate qualunque richiede contesto semantico.
- `Acqua del rubinetto che scorre` → distinguere: `acqua corrente domestica` vs `sciacquio di liquidi indistinto` vs `mare calmo/onde leggere`. Al momento il prompt CLAP confonde questi tre.
- `Cicale in campagna estiva del sud Italia` → versione piu' generica: `cicale in ambiente mediterraneo estivo` (non geo-vincolata).
- `Paesaggio sonoro di borgo rurale italiano` → versione generica: `paesaggio sonoro di villaggio rurale mediterraneo`.

Per Presque Rien specificamente, la terminologia accademica corretta:

- **Ferrari**: "musica aneddotica" (anecdotal music), "diapositiva sonora" (sonic photographic slide), "documento sonoro composto"
- **Westerkamp**: "soundscape composition", "deep listening", "phonography"
- **Schafer**: "keynote sound" per il mare di fondo, "sound signals" per i motori, "soundmark" per eventuali campane locali, "Hi-Fi soundscape"
- **Truax**: ascolto in modalita' "listening-in-readiness" (presta attenzione a eventi che emergono dal tappeto sonoro)
- **Chion**: predominantemente *ascolto causale* (riconoscere il porto, i pescatori) con momenti di *ascolto ridotto* (texture astratte di cicale)

## 7. Sezioni compositive (timeline manuale)

L'agente skill identifica **3 fasi acustiche distinte**:

| Sezione | Tempo (mm:ss-mm:ss) | Evento principale | Note (skill + accademia) |
|---------|---------------------|-------------------|--------------------------|
| 1 | 00:00-08:00 | Notturno rarefatto con voci e fauna | Pre-alba, attivita' biofonica notturna (insetti, eventuali rane), prime voci umane sussurrate. PANNs: parlato + insetti. Rispecchia il "lever du jour" dell'inizio. |
| 2 | 08:00-16:00 | Diurno, parlato + biofonia aviaria + attivita' domestica | Sole alto, attivita' del villaggio: voci piu' nitide, motori, cinguettio. PANNs: speech dominante. |
| 3 | 17:00-20:46 | Crepuscolo dominato da ortotteri e anuri | Tornare al biofonico (cicale e rane), spegnimento delle attivita' umane. Climax biofonico finale. |

**Critica accademica**: Ferrari stesso nelle sue note descrive il brano come
*un* arco temporale unico (l'alba estesa), non come 3 sezioni distinte.
La struttura "notturno - diurno - crepuscolo" identificata dalla skill e'
una segmentazione *induttiva* sulla base delle feature (parlato vs
biofonia), interessante ma non documentata da Ferrari come scelta
compositiva. Il brano e' realmente *Le lever du jour au bord de la mer*
(l'alba sul bordo del mare) e finisce intorno alle 6 del mattino, non
include un crepuscolo serale. La skill probabilmente interpreta come
"crepuscolo" il ritorno della fauna biofonica nelle ultime sezioni, ma
in realta' e' lo *scemare delle attivita' iniziali del giorno verso la
mattinata avanzata* (i pescatori sono usciti in mare, il villaggio si
quieta).

**Implicazione per v0.6.0** (segmentazione strutturale): il modulo
`structure.py` deve essere cauto a interpretare i confini come
"sezioni compositive intenzionali" se non vi sono altri marcatori di
struttura. L'agente compositivo dovrebbe etichettare le sezioni come
"fasi di evoluzione del materiale" piuttosto che "scene compositive
distinte" quando il brano e' soundscape continuo.

## 8. Lettura compositiva dell'agente

**Skill output, sezione "Lettura compositiva"** (3 paragrafi):

- **Osservazioni critiche**: identifica correttamente le tre fasi
  acustiche, DR 26.11 dB e LRA 25.9 come Hi-Fi, flatness 0.040 come
  spettro tonale con stridulazioni, NDSI +0.486 come equilibrio
  biofonia/antropofonia. Hint CLAP "borgo rurale italiano" interpretato
  come confluenza di voci, biofonia mediterranea, veicoli sporadici.

- **Oggetti sonori identificati** (7 con timecode): vocalizzazione gufo
  (00:00-02:30), passaggio veicolare pesante (07:00-08:00), tappeto di
  grilli e insetti (08:00-09:30), vocalizzazione felina (12:30-13:00),
  attivita' percussiva meccanica (14:30-15:30), coro di rane e ortotteri
  (18:30-20:46).

- **Collocazione estetica**: "tradizione del paesaggio sonoro rurale
  mediterraneo con forte pertinenza alla soundscape composition di
  ispirazione ecologica. La coesistenza di strati biofonici (ortotteri,
  anuri, rapaci), geofonici (vento) e antropofonici (parlato, veicoli,
  attivita' domestiche) richiama la pratica di ascolto profondo del
  territorio cara a Westerkamp e Truax (ipotesi, hint tentativi)."

**Pertinente?**
- [x] **parzialmente**. La lettura tecnica (livelli, dinamica, distribuzione spettrale, NDSI) e' impeccabile. La collocazione estetica generica e' corretta ma generica. **Il problema fondamentale**: l'agente non sa che e' Presque Rien N°1 di Luc Ferrari. Manca:
  - Identificazione del brano per nome
  - Contesto storico-compositivo (1967-70, Vela Luka, GRM, prima reazione "non e' musica")
  - Riconoscimento di Ferrari come fondatore della "musica aneddotica"
  - Riferimenti alla letteratura specifica sul brano (Eric Drott "The Politics of Presque Rien", Jacqueline Caux libro Les Presses du Reel)
  - Contestualizzazione: questo brano *anticipa* Schafer 1977 di 7-10 anni, *non* deriva da Schafer/Westerkamp.

**Errori specifici**:

- "Vocalizzazione di rapace notturno (gufo)" 00:00-02:30: il PANNs Frog 0.54 e CLAP "gufo notturno 0.19" sono in conflitto. Probabilmente NON e' un gufo, ma una vocalizzazione difficile da classificare (forse rana toro, o un suono umano modulato). Il caso giusto sarebbe stato "evento vocale non identificato con certezza".
- "Vocalizzazione felina" 12:30-13:00 con PANNs gatto 0.57: probabilmente corretto (a Vela Luka c'erano gatti randagi), ma andrebbe riportato come segnale puntuale e non come "evento compositivo".
- "Lavori stradali con martello pneumatico" 14:30-15:30: improbabile per la Vela Luka del 1967 in cui non c'erano lavori stradali importanti. Plausibilmente e' un motore di pescheria/officina, o un battitore di reti. Caso classico di prompt CLAP geo-storicamente fuori contesto.

**Implicazione per v0.6.0** (flag `--context`): un file `--context
presque_rien.md` con biografia Ferrari + storia compositiva avrebbe
permesso all'agente di identificare il brano e produrre lettura
compositiva di livello accademico, citando correttamente la "musica
aneddotica" di Ferrari, Vela Luka, l'anticipazione di Schafer,
l'ostilita' iniziale del GRM. Caso d'uso paradigmatico per la
prossima feature.

## 9. Note libere

**Tre osservazioni di sintesi sull'esito globale del test**:

**1. La skill performa molto bene sui dati grezzi e sul livello
tecnico**. Tutti i numeri sono coerenti, interpretazione spettrale
corretta, hum (in questo caso reale!) identificato giustamente, NDSI
ben interpretato. La "Lettura compositiva" e' ben strutturata sui dati
disponibili.

**2. Il limite e' contestuale: la skill non sa cosa sta analizzando**.
Senza contesto storico-poetico, anche un'analisi tecnicamente perfetta
diventa generica. Il brano viene classificato come "soundscape rurale
mediterraneo generico" invece che "documento storico chiave della
nascita del genere". E' esattamente il gap che il flag `--context`
della v0.6.0 dovrebbe colmare.

**3. CLAP e' fragile su brani non italiani con etichette
geo-specifiche**. Il vocabolario v1.2 e' fortemente italo-centrico
("sud Italia", "borgo medievale italiano", "marchigiano"). Su un
soundscape croato del 1967, questo produce match plausibili ma
geograficamente sbagliati. Per la v0.5.2 (post-feedback) suggerisco di
distinguere prompt geo-specifici da prompt generici, e mantenere
entrambi in vocabolario (i geo-specifici per casi italiani, i generici
per altri Paesi mediterranei). Esempio: tenere "Cicale in campagna
estiva del sud Italia" + aggiungere "Cicale in ambiente mediterraneo
estivo" (versione generica).

**Suggerimenti specifici per la v0.5.2**:

a) Aggiungere ~12 prompt CLAP per coprire la scena di porto peschereccio
mediterraneo (vedi sezione 3): pescatori, onde leggere, gallo, motore
peschereccio, gabbiani, passi su molo.

b) Affiancare ai prompt geo-italiani versioni geo-generiche
mediterranee.

c) Valutare se il filtro hallucination v0.5.1 deve essere esteso anche
a tag con keyword di luoghi specifici (chiesa, conservatorio AFAM,
borgo medievale italiano) quando il contesto generale non li supporta.
Attualmente solo le keyword voce/parlato attivano il filtro.

d) Per la lettura compositiva: aggiungere al prompt template istruzione
esplicita "identifica il brano per autore/anno se riconoscibile da
caratteristiche stilistiche, prima di procedere con la collocazione
estetica generica". Anche senza `--context`, alcuni brani sono
talmente caratteristici (Presque Rien tra questi) che l'agente
potrebbe riconoscerli dai metadata + contenuto.

---

## Riferimenti accademici consultati

- IRCAM Brahms — *Presque rien (N° 1) ou Le lever du jour au bord de la mer, Luc Ferrari*: <https://brahms.ircam.fr/works/work/36417/>
- Luc Ferrari — *Le dit des Presque Riens* (note dell'autore): <http://lucferrari.com/en/analyses-reflexion/le-dit-des-presque-riens/>
- Eric Drott — *The Politics of Presque rien* (2009, PDF accademico): <https://lucferrari.com/wp-content/uploads/2017/04/Eric-Drott__Politics-of-presque-rien__2009.pdf>
- *Luc Ferrari's Listening During Presque Rien No.1* (Project Muse, Johns Hopkins): <https://muse.jhu.edu/pub/6/article/679691/pdf>
- EARS 2 — *Presque rien [Almost Nothing] No.1 (by Luc Ferrari)*: <https://ears2.eu/courses/listen/lessons/presque-rien-almost-nothing-no-1-by-luc-ferrari>
- Frieze — *How Electroacoustic Pioneer Luc Ferrari Captured the Social Life of Sound*: <https://www.frieze.com/article/how-electroacoustic-pioneer-luc-ferrari-captured-social-life-sound>
- Wikipedia — *Luc Ferrari*: <https://en.wikipedia.org/wiki/Luc_Ferrari>
- Bandcamp — *Presque Rien n°1 (1967-70)*: <https://lucferrari.bandcamp.com/track/presque-rien-n-1-1967-70>
- Les Presses du Reel — *Luc Ferrari : Presque Rien n°1* (libro Jacqueline Caux): <https://www.lespressesdureel.com/EN/ouvrage.php?id=10338&menu=0>
