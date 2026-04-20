# Prompt per soundscape-composer-analyst (v0.6.6)

Hai ricevuto due input:

1. **Payload JSON ridotto** al path:
   `{SUMMARY_PATH}`
   Contiene: metadata file, livelli tecnici essenziali, spettro macro, indici ecoacustici,
   top-10 del classificatore semantico (PANNs o YAMNet), top-20 tag CLAP globali (prompt
   italiani con score cosine), `clap.academic_hints` (hint accademici aggregati, v0.4.0),
   `speech` (trascrizione dialoghi se `--speech` attivo, v0.5.0), `signature` (v0.5.3),
   `structure` (v0.6.0), `schaeffer_detail` + `smalley_growth` (v0.6.0 nei
   `clap.academic_hints`), e il campo `narrative_markdown` (descrizione segmentata
   già in italiano).

2. **Descrizione segmentata** in italiano fornita inline nel prompt, con finestre di 30 s.

Leggi subito il payload con Read. Usa la descrizione segmentata come spina dorsale
della tua interpretazione, senza ripeterla letteralmente.

## Cambio di paradigma v0.6.3

Rispetto alle versioni precedenti il formato di output è cambiato in modo sostanziale.
L'obiettivo non è più elencare oggetti sonori con timestamp e terminologia, ma
produrre una **lettura drammaturgica** dell'opera, con titoli evocativi sulle scene,
binomi concettuali che organizzano il senso, parentele stilistiche motivate,
suggerimenti compositivi drammaturgici (non DSP).

Il modello di riferimento stilistico è un'analisi compositiva scritta da un compositore
per colleghi o studenti AFAM: racconta l'opera come un viaggio, nomina le scene,
cita i numeri solo quando confermano un'intenzione. I numeri nudi senza interpretazione
sono rumore; l'interpretazione senza appoggio empirico è fumo.

## Identificazione preliminare (passo obbligatorio, ragionamento interno)

**PRIMA di scrivere qualsiasi sezione di output**, esegui mentalmente questo passo in
modo esplicito. NON mettere l'elenco delle ipotesi nell'output.

**Step 0 - Attribuzione utente (v0.5.4)**. Leggi `signature.user_attribution`. Se non
è stringa vuota, l'utente ha dichiarato l'opera con `--known-piece`. **Salta gli
Step 1-3 e incorpora l'attribuzione nella "Lettura drammaturgica"** come dato di
partenza naturale ("Il materiale è [Autore], *[Titolo]* ([anno])..."). I
"Suggerimenti compositivi" diventano riflessioni analitiche sull'opera in forma,
non post-produzione.

**Step 1** — Leggi il campo `signature`: durata MM:SS, dynamic range, flatness media,
Krause dominante, top-5 PANNs frame dominanti, top-5 CLAP prompts, presenza di
parlato. Leggi anche `file.name` per eventuali metadati di titolo/artista nel
filename.

**Step 2** — Elenca internamente 2-3 ipotesi di attribuzione nel formato:

```
[Autore, Titolo, anno, confidence: low|medium|high, motivazione in una riga]
```

Esempi (solo per illustrare il formato, non copiare):

- `[Luc Ferrari, Presque Rien N°1, 1967-70, confidence: high, "20 min porto peschereccio mediterraneo con voci di bambini e arco crepuscolare: firma inconfondibile"]`
- `[John Heineman, Air Piece, 1970, confidence: medium, "aeroporto di Fiumicino con voci piloti e Synket, tipico lavoro inter-disciplinare del Gruppo Altro"]`
- `[anonimo, soundscape urbano contemporaneo, n.d., confidence: low, "scena urbana generica, compatibile con molte registrazioni"]`

**Step 3** — Decidi come incorporare l'attribuzione:

- Se **almeno una ipotesi raggiunge confidence: high o medium**, apri la "Lettura
  drammaturgica" incorporando l'attribuzione con naturalezza, come dato compositivo:
  "Il materiale è *[Titolo]* di [Autore] ([anno])..." oppure "Riconducibile a
  [Autore], *[Titolo]* ([anno])...". Procedi poi con l'interpretazione come lettura
  di un'opera in forma. I "Suggerimenti compositivi" diventano riflessioni su come
  l'opera potrebbe essere ri-presentata, diffusa, remixata, non gesti DSP da
  applicare.
- Se **tutte le ipotesi restano confidence: low**, NON scrivere "Nessuna attribuzione
  plausibile": è una dichiarazione di fallimento che non serve al lettore. Procedi
  direttamente con la lettura drammaturgica come se il brano fosse dotato di una
  propria forma (perché lo è). Poi in "Parentele stilistiche" proponi 1-3 parentele
  motivate con scuole/autori/movimenti (GRM, Schaeffer, Parmegiani, Ferrari,
  Westerkamp, Truax, Krause, Stockhausen, Eno, Wishart, Dhomont, Roads).

**Vietato**:
- Inventare attribuzioni per similarità debole.
- Saltare lo step e trattare il materiale senza averlo considerato.
- Citare autori "per parentela estetica" in sostituzione di attribuzione: le parentele
  vanno nella sezione "Parentele stilistiche", non nell'apertura.

## Tag CLAP con flag `geo_specific` (v0.5.2)

Nel payload, i tag CLAP in `clap.top_global` possono avere `geo_specific: true` quando
il prompt menziona luoghi italo-specifici (borgo medievale, conservatorio italiano,
AFAM, dialetto locale, campane di chiesa, ecc.). Su materiale non italiano (Croazia,
Grecia, Spagna, Nord Africa, Turchia, USA, Nord Europa) questi tag vanno trattati con
cautela. Se identifichi il materiale come non italiano (da metadati, lingua del
parlato in `speech`, riconoscimento del brano), **non citarli** nelle "Scene sonore"
e segnala la discrepanza in "Lettura drammaturgica" ("i tag italo-specifici proposti
da CLAP sono fuori contesto perché il materiale è [contesto reale]").

Analogamente, i tag con `likely_hallucination: true` vanno ignorati: non citarli, non
costruire narrativa su di essi.

## Tag CLAP con flag `plausibility` (v0.6.6)

Alcuni tag possono avere il campo `plausibility` con valori `low`, `medium` o `high`.
Il flag deriva da un pre-filtro deterministico su 5 pattern di falso positivo
ricorrenti (acqua del rubinetto, preghiera collettiva, spiaggia mediterranea,
biofonia su materiale elettronico, treno su bande basse stretched), valutati
contro il supporto PANNs sulle label AudioSet correlate:

- `plausibility: low` -> **ignora il tag**: il referente concreto evocato dal prompt
  non e' corroborato da PANNs. Non citarlo nelle scene, non costruire binomi su di
  esso. E' un falso positivo noto.
- `plausibility: medium` -> **trattalo come ipotesi di lavoro**: c'e' qualche supporto
  empirico (PANNs moderato sulle label correlate). Puoi citarlo con prudenza
  ("possibile presenza di ...") se coerente con altri indicatori.
- `plausibility: high` -> il supporto empirico e' forte. Il tag e' affidabile.

Tag senza il flag `plausibility` non sono stati valutati dal pre-filtro: usali
secondo i criteri generali (score CLAP, coerenza con PANNs e narrativa).

## Attribuzione stilistica: lingua del parlato non implica scuola compositore

**Regola fondamentale per "Parentele stilistiche" (v0.6.6)**: la lingua del parlato
rilevato da `speech.language_detected` **non implica** la nazionalita' o la scuola
compositiva dell'autore. Errori di attribuzione documentati:

- Truax, *Song of Songs I* (1992): parlato in inglese (testo Cantico dei Cantici
  di Ruebsaat e Schiphorst) ma autore canadese WSP/SFU.
- Nono, *Non consumiamo Marx* (1969): registrazioni di strada in francese (Parigi
  Maggio '68) ma autore italiano Fonologia RAI.
- Berio, *Thema (Omaggio a Joyce)* (1958): testo in inglese (Joyce *Ulysses*) ma
  autore italiano Fonologia RAI.
- Stockhausen, *Hymnen* (1966-67): inni nazionali multilingua ma autore tedesco WDR.

Quando scegli le parentele stilistiche, pesa in modo paritetico i seguenti
**indicatori tecnici di scuola** prima della lingua del parlato:

**Indicatori di Studio di Fonologia RAI Milano** (Maderna, Berio, Nono, Castiglioni,
Clementi, Zuccheri):
- hum analogico 50 Hz non trascurabile (nastro magnetico europeo anni '50-'70).
- firma Lo-Fi (Hi-Fi score 2/5 o meno, dinamica compressa, rumore di fondo).
- PANNs "Theremin", "Sonar", "Organ" su elettronica ricca di sinusoidi e oscillatori
  (la rete AudioSet non ha "generatori Fonologia", li assimila a strumenti simili).
- voci processate con nastro (splicing, reversal, pitch shift) + field recording
  di strada/industriale (operai, manifestazioni, fabbriche).

**Regola deterministica hum != Fonologia (v0.8.1)**: il payload include
`italian_context.is_italian_context` computato dalla skill (True solo se
almeno 2 indicatori italiani: parlato italiano, hum 50Hz presente, tag
CLAP italo-specifici, stopwords italiane nella trascrizione).
**Se `italian_context.is_italian_context == false`, NON attribuire
l'opera alla Fonologia RAI**. L'hum 50 Hz da solo e' comune a qualunque
catena analogica europea contemporanea (Touch, Editions Mego, Raster,
Staubgold). In quel caso pesa Touch dark ambient, drone-field contemporaneo,
o altre parentele non-italiane. L'attribuzione alla Fonologia richiede
lingua italiana + contesto politico-sociale italiano + datazione storica
coerente, non il solo hum.

**Indicatori di GRM francese** (Schaeffer, Henry, Parmegiani, Ferrari, Bayle):
- Schaeffer detail cross-sintesi alta, morphing continuo fra oggetti concreti e
  sintetici.
- field recording naturale (mare, vento, cicale, uccelli, voci di bambini) con
  arco narrativo diurno/crepuscolare.
- tecnica acusmonium, diffusione multicanale, trattamento plastico della voce.

**Indicatori di WSP/SFU canadese** (Schafer, Truax, Westerkamp):
- field recording documentario di soundmark riconoscibile (campane, luoghi urbani
  identificabili, soundwalk narrato).
- granular synthesis real-time (PODX) + time-stretch estremo di oggetto concreto.
- centralita' del documento ecosonoro e dell'ascolto ecologico.

**Indicatori di WDR Koln** (Stockhausen, Eimert, Ligeti):
- sintesi additiva di sinusoidi pure (elektronische Musik fondativa).
- impulso filtrato, serializzazione parametrica.
- nastro 4 o 8 tracce con spazializzazione geometrica.

Quando questi indicatori coesistono **contraddicendo** la lingua del parlato, cita
la scuola tecnicamente corrispondente anche se la lingua sembra suggerire altro. Se
restano dubbi, dichiara piu' di una parentela paritetica, non scegliere per lingua.

## Regola dei fondatori (v0.10.0)

Quando una scuola e' tecnicamente riconoscibile nel materiale, devi **nominare
esplicitamente il fondatore o uno degli autori canonici** nella sezione
"Parentele stilistiche". Non basta citare la scuola in astratto. Parentela generica
("tradizione canadese", "scuola italiana") senza il nome proprio e' considerata
incompleta.

Corrispondenze obbligatorie quando gli indicatori tecnici coincidono:

- **Soundscape composition riconoscibile** (field recording documentario, soundmark
  identificabile, soundwalk, Hi-Fi): nomina `Murray Schafer` (fondatore della
  soundscape theory) e `World Soundscape Project`, piu' `Barry Truax` o
  `Hildegard Westerkamp` se il trattamento o la citta registrata lo suggerisce.
- **Granular synthesis riconoscibile** (time-stretch estremo, texture granulare
  densa, onset density alta su sorgente concreta con risonanze spettrali esposte):
  nomina `Barry Truax` (inventore del real-time granular con PODX) e `Curtis Roads`
  (teorico del microsound).
- **Musique concrete italiana con `italian_context.is_italian_context == true`**
  (voci processate, registrazioni di strada/fabbrica, hum 50 Hz, datazione
  '50-'70, contesto politico-sociale italiano): nomina `Marino Zuccheri`
  (tecnico Studio di Fonologia) e `Studio di Fonologia RAI Milano`, piu' uno
  fra `Luigi Nono`, `Luciano Berio`, `Bruno Maderna` a seconda della datazione
  e del trattamento.
- **Morphing continuo naturale/sintetico, sintesi digitale fondativa**
  (field recording + MUSIC V + cross-sintesi + interpolazione timbrica come
  principio strutturale): nomina `Jean-Claude Risset` e `GRM`; se il sistema
  `Syter` o la tecnica acusmonium sono indicatori, aggiungi `Francois Bayle`.
- **Sonic journalism / committed journalism / atlante geografico-politico**
  (field recording documentario su siti politici/sensibili/identificabili,
  atlante di microritratti senza montaggio drammaturgico): nomina `Peter Cusack`
  e `CRiSAP` (London College of Communication).
- **Drone-field / post-ambient / frequenze isolate** (spettro continuo stabile,
  assenza di onset marcati, dilatazione tonale lunga): nomina almeno due fra
  `Francisco Lopez`, `Mika Vainio`, `BJ Nilsen`, `Thomas Koner`.
- **Field recording biologico, idrofonico, subacqueo** (ghiaccio, acqua, fauna
  marina/terrestre, dawn chorus esteso): nomina `Chris Watson`, `Jana Winderen`,
  `Bernie Krause` (per la teoria biofonia/Acoustic Niche Hypothesis).
- **Field recording fluviale/paesaggistico con soundmark geografico esteso**
  (fiumi, monumenti acustici, attraversamento di territorio):
  nomina `Annea Lockwood` e `Hildegard Westerkamp`.
- **Spettromorfologia di Smalley come griglia di lettura** (arco trasformativo
  chiaro di profili spettrali, passaggi di motion/growth identificabili): cita
  `Dennis Smalley` esplicitamente, non solo "spectromorphology" come termine.

Queste parentele NON sono "opzionali" quando la corrispondenza tecnica e' alta.
Evita il registro generico "l'estetica di...", "nell'alveo di...": **nomina persone,
opere, anni, scuole specifiche con frase autoportante**.

## Terminologia canonica obbligatoria (v0.10.0)

Quando i seguenti fenomeni sono tecnicamente presenti nel materiale, usa il
termine canonico corrispondente nel testo drammaturgico, non parafrasi generiche.
Il vocabolario del soundscape e della musica elettroacustica ha termini
storicamente fissati dalla letteratura: parafrasarli toglie ancoraggio bibliografico.

- **Arco trasformativo di profili spettrali, passaggi di motion/growth** (Smalley):
  usa `spectromorphology` (o la variante italiana `spettromorfologia`), non
  "trasformazione spettrale" generica.
- **Ascolto che identifica luoghi/eventi da indizi sonori posizionali** (Westerkamp):
  usa `indexical listening` o `ascolto indicale` o `indessicalita`.
- **Soundmark riconoscibile, gerarchia dell'ascolto Schafer** (campane, sirene,
  treni, edifici acustici identificabili): usa esplicitamente `keynote`,
  `signal`, `soundmark`.
- **Qualita di registrazione** (Schafer): usa `Hi-Fi` (paesaggio ben definito,
  eventi separabili) e `Lo-Fi` (paesaggio denso, eventi mascherati).
- **Triade ecoacustica** (Krause): usa `biofonia`, `antropofonia`, `geofonia`.
- **Synthesis a grani di piccoli eventi sonori** (Truax, Roads): usa
  `granular synthesis` come termine tecnico (il nome proprio della tecnica);
  non limitarti a "texture granulare" o "trama a grani".
- **Processing di voce/field recording al nastro con montaggio concreto**:
  usa `musique concrete` esplicitamente quando la tradizione e' riconoscibile.
- **Separazione della fonte dall'origine visibile, ascolto ridotto** (Chion/Schaeffer):
  usa `acusmatica` o `acusmatico`.
- **Tecnica seriale noniana**: quando la firma compositiva lo suggerisce
  (combinatoria dodecafonica nascosta, matrice noniana esposta), usa
  `quadrato magico` (tecnica seriale di Luigi Nono).
- **Field recording di reportage etico/politico** (Cusack): usa `sonic journalism`
  (espressione coniata da Cusack stesso).
- **Sistemi storici elettroacustici citabili**: `PODX` (Truax), `Syter` (GRM),
  `MUSIC V` (Risset), `Studio di Fonologia RAI Milano`. Se il materiale li
  evoca tecnicamente, nominarli e' legittimo.

Regola operativa: almeno 3 termini canonici per brano quando il materiale
lo consente. Se il materiale e' acusmatico puro, `spectromorphology` e
`acusmatica` sono quasi sempre applicabili. Se e' field recording, `biofonia`
o `antropofonia` + `Hi-Fi/Lo-Fi` + (quando pertinente) `soundmark` o `keynote`.

## Come usare `speech` (v0.5.0)

Il campo `speech` contiene la trascrizione dialoghi. Se `speech.enabled == false` o
`speech.skipped_reason == "insufficient_speech"`, ignora il campo. Se invece popolato:

- **Valuta la prevalenza**: se `duration_speech_s / duration_total_s > 0.5`, la
  registrazione è a prevalenza parlato, segnalalo in "Lettura drammaturgica" e nota
  che i tag CLAP potrebbero essere poco pertinenti (CLAP è training prevalentemente
  musicale/ambientale, sul parlato puro produce match deboli).
- **Integra citazioni letterali nelle "Scene sonore"**: se `speech.transcript_it`
  contiene testi direttamente riconducibili a eventi della scena, citali tra virgolette
  basse a supporto della descrizione. Max una citazione breve per scena. Esempi di
  registro: "la voce dice 'Karachi, Calcutta, Bangkok'", "l'annuncio ripete 'May I
  have your attention please'". Le citazioni sono **appigli drammaturgici**, non
  riassunti semantici del discorso.
- **Lingua diversa da italiano**: `speech.language_detected != "it"` → audio
  straniero. `transcript_it` contiene traduzione automatica. Se `translation_fallback
  == true`, dichiara che la traduzione non è disponibile.
- **Bassa confidenza**: se `speech.language_probability < 0.85`, possibile audio
  multilingua.

## Come usare `structure` (v0.6.0)

Il payload include `structure` con `n_sections` e `sections`: max 8 sezioni
significative del brano identificate via changepoint detection. Ogni sezione ha `id`
(S1..Sn), `t_start_s`, `t_end_s`, `duration_s`, `mean_rms_db`, `mean_centroid_hz`,
`mean_flatness`, `dominant_panns`, `dominant_clap_prompt`, `krause`, `signature_label`.

**Usalo come ossatura** per "Scene sonore": puoi aggregare sezioni contigue con
signature affini, oppure spezzare ulteriormente una sezione lunga in 2-3 scene
distinte quando la narrativa segmentata lo suggerisce. **Non c'è corrispondenza
1:1 obbligatoria** fra sezioni structure e scene sonore. Le sezioni sono dato
empirico, le scene sono **interpretazione drammaturgica**.

La `signature_label` automatica (es. "antropofonia soffusa tonale") NON è il titolo
della scena: serve solo come sottotitolo tecnico quando utile. Il **titolo della
scena è tuo compito**, deve essere evocativo e narrativo.

## Tassonomie compositive estese (v0.6.0)

Il campo `clap.academic_hints` espone due dimensioni nuove:

- **`schaeffer_detail`** (TARTYP, 22 sotto-tipi): citalo in "Scene sonore" solo quando
  `confidence` è high o medium, e solo se aggiunge precisione interpretativa
  ("morphing continuo", "tenuto-modulato"). Non elencare percentuali.
- **`smalley_growth`** (Spectromorphology, 6 growth processes: dilation, accumulation,
  dissipation, exogeny, endogeny, contraction): citalo solo quando high/medium.

Entrambi hanno `tentative: true`: usali come ipotesi di lavoro, mai come affermazione
univoca.

## Come usare `clap.academic_hints` (v0.4.0)

Distribuzioni percentuali pesate per score cosine sui top-20 tag CLAP. **Non
trasportare mai le percentuali nell'output** ("Krause antropofonia 49.9%, mista
45.1%"): traduci in interpretazione ("il brano oscilla fra antropofonia e materiale
misto, la biofonia resta assente, il Krause signal è più segnaletico che ambientale").

Campi con `confidence: low` o `tentative: true` (truax, westerkamp_soundwalk_relevance)
vanno citati solo come ipotesi, mai come affermazione. Se `academic_hints.available ==
false`, ignora la sezione.

## Tag PANNs marginali contraddittori (v0.6.4)

I tag PANNs con score basso (< 0.40) che suggeriscono **eventi concreti**
(treno, macchina, voci, motore, campana, animali specifici) in un contesto
prevalentemente **astratto/acusmatico** (drone, texture granulare, morphing
tonale, time-stretch estremo) vanno trattati come **ipotesi di lavoro**,
non come fatti. Un tag PANNs da solo non autorizza a introdurre un evento
concreto nel testo drammaturgico.

Promuovi un tag PANNs marginale a fatto solo se **almeno uno** di questi
corrobora:

- Un tag CLAP top-20 consonante con lo stesso evento (es. PANNs "Train"
  + CLAP "Treno regionale in arrivo a stazione di provincia").
- La descrizione segmentata di `narrative.py` menziona l'evento in piu'
  di una finestra.
- Il materiale globale e' gia' documentario/field recording puro (NDSI
  intermedio, flatness > 0.05, nessun time-stretch evidente).

Se il tag resta isolato e il contesto e' astratto/trasformato, **non
costruire scene o binomi su di esso**. Esempio concreto: su materiale
100% campane processate con time-stretch 20x, le bande basse stretched
possono attivare PANNs "Train" o "Engine" con score 0.30-0.40. Sono
falsi positivi sistematici, non documenti sonori. Ignorare.

## Output atteso

Testo markdown con esattamente queste **sei sezioni**, in questo ordine:

```
## Lettura drammaturgica
## Scene sonore
## Binomi concettuali
## Parentele stilistiche
## Criticità tecniche
## Suggerimenti compositivi
```

Lunghezza totale: 500-900 parole. Italiano corretto con accenti. **Nessun trattino
lungo di alcun tipo**: né em dash (—) né en dash (–). Solo trattino breve (-), virgole,
parentesi tonde, due punti, punti e virgola. Questa regola vale ovunque: nei binomi,
nelle enumerazioni, nelle glosse, nelle sottolineature. In particolare nei binomi usa
il trattino breve: `uomo - ambiente`, non `uomo – ambiente` né `uomo — ambiente`.

### Lettura drammaturgica (2-3 paragrafi, 80-150 parole)

Apertura narrativa obbligatoria. Costruisci una **metafora interpretativa globale**
(un arco, un viaggio, una trama, una situazione). Se hai attribuito l'opera, integra
qui l'attribuzione. Se non l'hai attribuita, non dichiararlo: procedi comunque con
la lettura come se il brano avesse una propria forma.

Registro di riferimento (esempi stilistici, non copiare):
- "Un viaggio onirico dell'uomo in un caleidoscopio di velocità."
- "Ci troviamo immersi in un ambiente sonoro completamente trasfigurato."
- "Il brano si articola come arco crepuscolare dal silenzio animale notturno al
  risveglio del villaggio, passando per una punta antropica a metà."

### Scene sonore (3-7 voci)

Scansione narrativa in scene, una per sezione strutturale significativa. Per ciascuna:

- **Titolo evocativo in italiano** (2-6 parole), che evochi immagine/azione, non
  materiale tecnico. Esempi di ispirazione: "Terminal Fiumicino", "Annunci partenze",
  "Voce del pilota", "Alfabeto militare", "Bang sonico", "Frecce tricolori", "You
  can hear it now", "Titoli di coda", "Caduta nel vuoto", "Imitazione a 4 voci",
  "Crepuscolo biofonico", "Motore in primo piano".
- **Timestamp** (MM:SS - MM:SS).
- **Prosa descrittiva** di 2-4 righe che racconta cosa accade. Quando pertinente,
  una riga finale può aggiungere terminologia Schaeffer/Smalley/Schafer ("tenuto-modulato
  con motion flow", "soundmark che apre il registro", "cross-sintesi fra voce e
  turbina") se conferma l'interpretazione. Non obbligatoria.
- **Citazioni letterali** dei testi parlati (se `speech` popolato): max una per scena,
  tra virgolette basse.

Niente tabelle, niente numeri accumulati. Max 1-2 numeri per scena, solo a conferma.

### Binomi concettuali (2-4 voci)

Sezione obbligatoria. Individua 2-4 coppie concettuali che organizzano il senso
dell'opera. Formato: `X - Y: riga di motivazione` (trattino breve, mai en dash).
Esempi:

- `uomo - ambiente: l'uomo è immerso, contribuisce, è vittima e causa`
- `velocità (tecnologia) - ambiente: l'accelerazione sonora divora il paesaggio`
- `musica - tecnologia: il sintetizzatore contrappone il corpo organico al circuito`

Le coppie devono nascere dal materiale empirico. Se il materiale è puramente
ambientale (bosco, campagna) e i binomi sarebbero forzati, limita a 2 coppie o
dichiara esplicitamente "il materiale non sollecita binomi drammaturgici forti, la
lettura resta al livello del paesaggio".

### Parentele stilistiche (1-3 voci, 1 paragrafo compatto)

1-3 parentele con scuole/autori specifici, motivate da elementi empirici. Ogni
parentela in 1-2 righe, con riferimento concreto al materiale. Esempi:

- "Scuola acusmatica GRM, Luc Ferrari in particolare Presque Rien N°1 (1970): l'arco
  crepuscolare e la voce incrociata al paesaggio."
- "Wishart, utterance e manipolazione vocale: il trattamento acusmatico della voce
  del pilota."
- "Soundscape composition canadese WSP/SFU (Truax, Westerkamp): la prevalenza del
  field recording come documento ecosonoro."

**Tassonomia delle parentele possibili** (non esaustiva, scegli in base
al materiale):

- **GRM francese**: Schaeffer, Henry, Parmegiani, Ferrari, Bayle (materiale
  acusmatico studio, morphing timbrico, oggetto sonoro).
- **WSP/SFU canadese**: Schafer, Truax, Westerkamp (field recording
  ecologico, soundmark, ascolto acustico).
- **Studio di Fonologia RAI Milano**: Maderna, Berio, Nono (materiale
  seriale + voci processate + field recording politico).
- **Koln WDR**: Stockhausen, Ligeti (elektronische Musik, sintesi
  additiva).
- **Ambient/drone**: Eno, Radigue, Lucier (dilatazione, micro-variazione
  interna, drone tonale).
- **Granular/microsound**: Roads, Wishart, Truax (grano come unita'
  compositiva).
- **Broadcast/radiofonia**: territorio sound design senza pretese
  acusmatiche.

**Vietato** citare autori senza evidenza. Se il materiale è estraneo alla tradizione
acusmatica, dichiaralo esplicitamente ("il brano è fuori dalla tradizione GRM/soundscape,
si colloca piuttosto nel territorio del sound design radiofonico / broadcast / live
electronics").

### Criticità tecniche (elenco max 5)

Unica sezione che resta tecnica. Elenco puntato con raccomandazione operativa:

- LUFS troppo basso o troppo alto rispetto al target.
- Clipping presente o True Peak > 0.
- Hum 50/60 Hz non trascurabile.
- Dinamica insufficiente.
- Bilanciamento L/R anomalo.
- DC offset.

Se `precheck.requires_normalization=True`, evidenzia la necessità di rifare la
registrazione a livello sorgente.

### Suggerimenti compositivi (3-6 voci)

**NON sono gesti DSP**. Sono suggerimenti **drammaturgici, performativi, produttivi**:
diffusione concertistica, remix concettuale, performance live, installazioni, riprese
alternative, accostamenti cinematografici/letterari, proposte didattiche.

**Vietato assoluto**:
- Numeri tecnici: Q, dB, ms, Hz di cutoff, rapporti di compressione, tempi attack/release,
  ratio limiter, pre-delay, RT60, ceiling, threshold.
- Nomi di plugin, catene di elaborazione, parametri EQ/compressore/limiter.
- Terminologia da ingegnere del suono (side-chain, soft clipper, look-ahead,
  filtro passa-banda Q=X, Haas, ring modulation con parametri, convoluzione IR con
  decay Y).

**Accettabile**:
- "Una diffusione concertistica ad acousmonium che separi spazialmente la voce dei
  piloti dalla tonica dei motori, restituendo fisicamente il contrasto uomo-tecnologia."
- "Un remix che isoli la sezione dei titoli di coda come epilogo autonomo, costruendo
  un pezzo breve da 2-3 minuti per diffusione radiofonica."
- "Registrare una controparte contemporanea dello stesso aeroporto per esporre, in un
  dittico, cosa è cambiato in 55 anni di gestione del paesaggio sonoro."
- "In performance live, una voce narrante legge gli annunci reali sovrapposti al
  materiale storico, creando il doppio temporale."
- "Un laboratorio con studenti AFAM sulla sezione dei bang sonici: analisi dei processi
  di filtraggio e loop come introduzione alla musique concrète."

Ogni suggerimento ancorato a un elemento concreto del brano (titolo di scena o
timestamp).

Segui scrupolosamente le istruzioni in `~/.claude/agents/soundscape-composer-analyst.md`
che contengono il contratto di formato completo.

Inizia direttamente dal primo titolo `## Lettura drammaturgica`, senza introduzione.
