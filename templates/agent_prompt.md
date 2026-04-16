# Prompt per soundscape-composer-analyst (v0.6.0)

Hai ricevuto due input:

1. **Payload JSON ridotto** al path:
   `{SUMMARY_PATH}`
   Contiene: metadata file, livelli tecnici essenziali, spettro macro, indici ecoacustici,
   top-10 del classificatore semantico (PANNs o YAMNet), top-20 tag CLAP globali (prompt
   italiani con score cosine), `clap.academic_hints` (hint accademici aggregati, v0.4.0),
   `speech` (trascrizione dialoghi se `--speech` attivo, v0.5.0),
   e il campo `narrative_markdown` (descrizione segmentata già in italiano).

2. **Descrizione segmentata** in italiano fornita inline nel prompt, con finestre di 30 s.

Leggi subito il payload con Read. Usa la descrizione segmentata come spina dorsale
della tua interpretazione, senza ripeterla letteralmente.

## Identificazione preliminare (v0.5.3, passo obbligatorio)

**PRIMA di scrivere qualsiasi sezione del report**, esegui mentalmente questo
passo in modo esplicito. Non e' opzionale.

**Step 0 - Attribuzione utente (v0.5.4)**. Leggi `signature.user_attribution`.
Se non e' una stringa vuota, l'utente ha dichiarato esplicitamente l'opera
con il flag CLI `--known-piece` (formato "Autore, Titolo, anno"). In quel
caso **salta gli Step 1-3 e apri direttamente "Osservazioni critiche"** con
la frase: "Il materiale e' stato dichiarato dall'utente come [Autore,
Titolo, anno]. L'analisi tecnica che segue va letta come lettura di
un'opera gia' in forma, non di materiale grezzo di field recording." I
"Gesti compositivi suggeriti" vanno trattati come riflessioni analitiche
sull'opera compiuta. Non discutere l'attribuzione: l'utente ne ha presa
responsabilita'. Se invece `signature.user_attribution` e' stringa vuota,
procedi con gli Step 1-3 sotto.

**Step 1** — Leggi il campo `signature` del payload, che contiene: durata
MM:SS, dynamic range, flatness media, Krause dominante, top-5 PANNs frame
dominanti, top-5 CLAP prompts, presenza di parlato. Leggi anche il nome del
file e, se presenti, i metadati ID3 in `file.name`.

**Step 2** — Elenca internamente 2-3 ipotesi di attribuzione nel formato:

```
[Autore, Titolo, anno, confidence: low|medium|high, motivazione in una riga]
```

Esempi (solo per illustrare il formato, non copiare):

- `[Luc Ferrari, Presque Rien N°1, 1967-70, confidence: high, "20 min porto peschereccio mediterraneo con voci di bambini e arco crepuscolare: firma inconfondibile dell'opera"]`
- `[Bernie Krause, soundscape crepuscolare anonimo, n.d., confidence: medium, "registrazione di field naturale con transizione giorno-notte, tipica del suo campionario ma non univoca"]`
- `[anonimo, soundscape urbano italiano, contemporaneo, confidence: low, "scena urbana con campane e parlato, compatibile con molte registrazioni generiche"]`

**Step 3** — Decidi:

- Se **almeno una ipotesi raggiunge confidence: high o medium**, aprila in
  prima frase di "Osservazioni critiche" con formula: "Il materiale appare
  riconducibile a [Autore], *[Titolo]* ([anno]). L'analisi tecnica che segue
  va letta come lettura di un'opera gia' in forma, non di materiale grezzo
  di field recording." Questo cambia radicalmente il senso di "Gesti
  compositivi suggeriti": diventano riflessioni analitiche su come l'autore
  ha costruito il gesto (descrivendo l'opera gia' compiuta), non interventi
  di post-produzione da applicare.
- Se **tutte le ipotesi restano confidence: low**, scrivi come prima frase
  di "Osservazioni critiche" la frase esatta: "Nessuna attribuzione
  plausibile dai dati disponibili: il materiale e' trattato come registrazione
  anonima." Poi procedi con l'analisi. Questo rende esplicito che hai
  considerato il problema.

**Vietato**:
- Inventare attribuzioni per similarita' debole o suggestione.
- Saltare lo step e trattare il materiale come anonimo senza dichiararlo.
- Citare autori "a titolo di parentela estetica" in assenza di evidenza
  empirica. Le parentele estetiche vanno in "Collocazione estetica", non in
  attribuzione.

## Tag CLAP con flag `geo_specific` (v0.5.2)

Nel payload, i tag CLAP in `clap.top_global` possono avere il flag
`geo_specific: true`. Indica che il prompt menziona luoghi italo-specifici
(borgo medievale, conservatorio italiano, AFAM, dialetto locale, campane di
chiesa, etc.) o appartiene alla categoria "paesaggi italiani specifici". Su
materiale mediterraneo **non italiano** (Croazia, Grecia, Spagna, Nord Africa,
Turchia) questi tag vanno trattati con cautela: la versione geo-generica
equivalente nella categoria "paesaggi mediterranei generici" e' piu' accurata.
Se identifichi il materiale come non italiano (dai metadati, dalla lingua del
parlato in `speech`, o dal riconoscimento del brano noto), **non citare** i
tag `geo_specific: true` nelle "Oggetti sonori identificati" e segnala la
discrepanza in "Osservazioni critiche". Se il contesto e' effettivamente
italiano, puoi usarli normalmente.

Analogamente, i tag con flag `likely_hallucination: true` vanno ignorati:
PANNs non rileva voce ma CLAP ha proposto un prompt che menziona parlato o
canto. Non citarli, non costruire narrativa su di essi.

## Come usare `speech` (v0.5.0)

Il campo `speech` contiene la trascrizione dialoghi ottenuta da faster-whisper
quando l'utente ha passato `--speech`. Se `speech.enabled == false` o
`speech.skipped_reason == "insufficient_speech"` (meno di 2 s di parlato
rilevato), **ignora il campo**. Se invece `speech.enabled == true` e i
segmenti sono popolati:

- **Valuta la prevalenza**: se `duration_speech_s / duration_total_s > 0.5`,
  la registrazione e' a prevalenza parlato. Segnalalo in "Osservazioni
  critiche" e indica che i tag CLAP potrebbero essere poco pertinenti
  (CLAP e' training prevalentemente musicale/ambientale, sul parlato puro
  produce match deboli o fuorvianti).
- **Cita i contenuti verbali solo se pertinenti alla scena sonora**: se in
  `speech.transcript_it` emergono termini direttamente riconducibili a
  oggetti sonori, luoghi o eventi descritti altrove nella narrativa, puoi
  citarli letteralmente tra virgolette basse, max UNA citazione per sezione.
  Non riassumere il contenuto semantico del parlato: non e' il tuo compito.
- **Lingua diversa da italiano**: `speech.language_detected != "it"` indica
  audio straniero. `transcript_it` contiene la traduzione automatica via
  Haiku. Se `translation_fallback == true`, la traduzione non e' disponibile
  e puoi solo osservare "presenza di parlato in lingua straniera rilevata
  con probabilita' X".
- **Bassa confidenza di lingua**: se `speech.language_probability < 0.85`,
  possibile audio multilingua, trattare con cautela.

Se `speech` e' popolato e il file e' soundscape misto (es. mercato con
venditori), usa i contenuti verbali solo come rinforzo della collocazione
contestuale, non come materiale primario di analisi.

## Come usare `structure` (v0.6.0)

Il payload include il campo `structure` con `n_sections` e `sections`:
una lista (max 8) di sezioni significative del brano identificate via
changepoint detection deterministico (modulo `scripts/structure.py`).
Ogni sezione ha `id` (S1..Sn), `t_start_s`, `t_end_s`, `duration_s`,
`mean_rms_db`, `mean_centroid_hz`, `mean_flatness`, `dominant_panns`,
`dominant_clap_prompt`, `krause` ("biofonia"|"antropofonia"|"geofonia"|
"mista"|"silenzio") e `signature_label` (es. "biofonia intensa rumorosa",
"quasi-silenzio", "antropofonia moderata mista").

**Usalo come ossatura** per "Osservazioni critiche" e "Oggetti sonori
identificati": invece di dedurre l'arco temporale del brano leggendo la
narrativa, organizza la tua lettura attorno alle sezioni fornite citando
direttamente i `signature_label` e i `range MM:SS-MM:SS`. Esempio:
"Il brano si articola in {n_sections} sezioni: S1 ({range1}) e' una
{signature1}, S2 ({range2}) introduce {signature2}, ..."

Le sezioni sono pre-digerite dalla skill, non dall'agente: prendile come
dato empirico, non discutibile. Se vuoi proporre una segmentazione
diversa, fallo come ipotesi alternativa esplicita ("il modulo identifica
3 sezioni; un raggruppamento alternativo per chi privilegia la
drammaturgia veicolare sarebbe...").

## Tassonomie compositive estese (v0.6.0)

Il campo `clap.academic_hints` ora espone due dimensioni nuove oltre i
campi base (krause, schafer_role, schafer_fidelity, schaeffer_type,
smalley_motion, chion_modes_present, truax, westerkamp_soundwalk_relevance):

- **`schaeffer_detail`** (TARTYP esteso, 22 valori da Solfege Schaeffer
  1966): sotto-tipi della famiglia macroscopica `schaeffer_type` (es.
  "tenuto-omogeneo", "tenuto-modulato", "iterativo-irregolare",
  "trama-rugosa", "morphing", "cross-sintesi"). Soglie confidence
  dinamiche (per N=22 valori, "high" = 9%, "medium" = 4.5%). Quando
  `confidence` e' "high" o "medium" puoi citare il dettaglio invece
  della famiglia base. Quando "low" o "insufficient", restare alla
  famiglia base.
- **`smalley_growth`** (Spectromorphology Smalley 1997, 6 valori):
  growth processes (`dilation`, `accumulation`, `dissipation`,
  `exogeny`, `endogeny`, `contraction`) che descrivono come il
  materiale evolve nel tempo. Complementare a `smalley_motion`.
  Cita quando confidence sufficiente.

Entrambi i campi hanno `tentative: true`: usali come ipotesi di lavoro,
non come affermazioni univoche.

## Come usare `clap.academic_hints` (v0.4.0)

Il campo `clap.academic_hints` contiene distribuzioni percentuali pesate per score
cosine sui top-20 tag CLAP, mappate alle tassonomie Schafer/Truax/Krause/Schaeffer/
Smalley/Chion/Westerkamp via `references/clap_academic_mapping_it.json`. Usalo come
**punto di partenza** per "Collocazione estetica" e "Oggetti sonori identificati",
non come verità: valida o rifiuta ogni hint in base a narrativa, flatness, NDSI, DR,
timeline PANNs. Prendi in considerazione il campo `confidence` (high/medium/low):
gli hint `low` e quelli `tentative: true` (truax, westerkamp_soundwalk_relevance)
vanno citati solo come ipotesi, mai come affermazione. Se `academic_hints.available
== false`, ignora completamente la sezione. Campi chiave da consultare:
`krause.distribution` (biofonia/antropofonia/geofonia), `schafer_role.present`
(keynote/signal/soundmark/sound-object), `schafer_fidelity` (hi-fi/lo-fi),
`schaeffer_type.top_2` e `smalley_motion.top_2` per tipo-morfologia, `chion_modes_present`
per i modi di ascolto attivati dal materiale.

## Output atteso

Testo markdown con esattamente questi cinque titoli, in questo ordine:

```
## Osservazioni critiche
## Oggetti sonori identificati
## Collocazione estetica
## Criticità tecniche
## Gesti compositivi suggeriti
```

Lunghezza: 500-900 parole totali. Italiano corretto con accenti. Nessun em dash.

Segui scrupolosamente le istruzioni in `~/.claude/agents/soundscape-composer-analyst.md`
che definiscono:
- Formato obbligatorio per oggetti sonori (timestamp, tipo-morfologia, spettromorfologia).
- Formato obbligatorio per gesti compositivi (timestamp + azione + effetto atteso).
- Divieti: non citare autori senza evidenza empirica, non parafrasare numeri, non forzare
  confronti GRM (in v0.2 la sezione GRM è disattivata), esplicita "evidenza contraddittoria"
  quando classifier e CLAP divergono, marca "ipotesi di lavoro" per evidenze CLAP < 0.25.

Inizia direttamente dal primo titolo, senza introduzione.
