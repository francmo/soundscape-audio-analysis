# Prompt per soundscape-composer-analyst (v0.2.2)

Hai ricevuto due input:

1. **Payload JSON ridotto** al path:
   `{SUMMARY_PATH}`
   Contiene: metadata file, livelli tecnici essenziali, spettro macro, indici ecoacustici,
   top-10 del classificatore semantico (PANNs o YAMNet), top-20 tag CLAP globali (prompt
   italiani con score cosine), e il campo `narrative_markdown` (descrizione segmentata
   già in italiano).

2. **Descrizione segmentata** in italiano fornita inline nel prompt, con finestre di 30 s.

Leggi subito il payload con Read. Usa la descrizione segmentata come spina dorsale
della tua interpretazione, senza ripeterla letteralmente.

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
