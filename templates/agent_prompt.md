# Prompt per soundscape-composer-analyst (v0.2.2)

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
