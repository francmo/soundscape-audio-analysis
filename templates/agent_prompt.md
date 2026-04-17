# Prompt per soundscape-composer-analyst (v0.6.3)

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
- "Soundscape composition canadese (Truax, Westerkamp): la prevalenza del field
  recording come documento ecosonoro."

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
