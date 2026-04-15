# Template di feedback utente

Compila una copia di questo file per ogni brano analizzato dalla skill su cui
vuoi dare correzioni. Salvalo come `references/user_feedback/<nome_brano>.md`.

Le tue annotazioni saranno tradotte in patch concrete:
- aggiunte/rimozioni di prompt nel vocabolario CLAP italiano
- correzioni del mapping accademico (Schaeffer/Smalley/Krause/Schafer/Chion)
- ricalibrazione delle soglie di hallucination, hum context, suggerimento speech
- nuove regole di filtro contestuale
- glossario terminologico per arricchire il rendering PDF

Non serve compilare tutte le sezioni: lascia vuote quelle che non ti
interessano. Le note libere alla fine sono spesso le piu' utili.

---

## 1. Identificazione

- **File**: `<nome_file.ext>`
- **Versione skill che ha prodotto il report**: `vX.Y.Z`
- **Data feedback**: `2026-MM-DD`
- **Contesto del brano** (autore, anno, strumentazione, contesto compositivo):
  >

## 2. PANNs (classificazione semantica primaria)

### Top-1 globale

- **Skill dice**: `<nome>` (score `<X.YY>`)
- **Reale**:
  - [ ] corretto
  - [ ] errato — la categoria giusta sarebbe: `<...>`
  - [ ] parzialmente corretto, manca: `<...>`

### Top-10 globali

Per ciascun item della top-10 PANNs nel report, marca:

| Posizione | Etichetta PANNs | Score | Valutazione |
|-----------|-----------------|-------|-------------|
| 1 | | | OK / errato / parziale |
| 2 | | | |
| ... | | | |

### Frame dominanti (`top_dominant_frames`)

- **Categoria + percentuale frame** dichiarate dalla skill: `<...>`
- **Coerenti con la tua percezione del brano?**
  >

## 3. CLAP (auto-tagging italiano)

### Top-10 globali

| Posizione | Prompt italiano | Score | Pertinente? | Note |
|-----------|-----------------|-------|-------------|------|
| 1 | | | sì / no / parziale | |
| 2 | | | | |
| ... | | | | |

### Tag flagged come allucinazioni (corsivo nel PDF)

- **Sono stati marcati correttamente?**
  - [ ] sì, sono effettivamente allucinazioni
  - [ ] no, alcuni erano pertinenti: `<lista>`
  - [ ] sì ma ne mancano altri da marcare: `<lista>`

### Prompt CLAP mancanti

Categorie/eventi sonori del brano che la skill non ha colto perche' assenti
dal vocabolario corrente. Per ciascuno, suggerisci un prompt italiano breve:

- `<prompt 1, es. "improvvisazione su tecniche estese di flauto">`
- `<prompt 2, es. "scrittura dialogica strumentale con respiri condivisi">`
- ...

### Prompt CLAP da rimuovere

Prompt che nel vocabolario producono allucinazioni sistematiche e non
contribuiscono a tag credibili:

- `<id o testo prompt>` — motivo: `<...>`
- ...

## 4. Hum check

- **Verdetto complessivo skill**: `<trascurabile / presente / forte>`
- **Reale**:
  - [ ] corretto, c'e' davvero ronzio elettrico
  - [ ] falso positivo: i picchi sono armoniche strumentali / componenti tonali intenzionali
  - [ ] mancato (rumore presente ma non rilevato)
- **Hint contestuale "likely_musical_harmonic"** (v0.5.1): è scattato correttamente?
  - [ ] sì
  - [ ] no, doveva scattare ma non l'ha fatto perche': `<...>`
  - [ ] sì ma il messaggio andava raffinato: `<...>`

## 5. Mapping accademico (academic_hints)

Per ciascuna dimensione, valuta se la distribuzione/dominante riportata
dalla skill ti sembra credibile:

- **Krause (biofonia/antropofonia/geofonia)**: `<...>` → corretto / errato perche' `<...>`
- **Schafer (keynote/signal/soundmark/sound-object)**: `<...>` → ...
- **Schaeffer type (impulsivo/iterativo/tenuto/tenuto-evolutivo/trama/campione)**: `<...>` → ...
- **Smalley motion (flow/turbulence/streaming/...)**: `<...>` → ...
- **Chion modes (causale/semantico/ridotto)**: `<...>` → ...
- **Westerkamp soundwalk relevance**: `<sì/no>` → ...

## 6. Lessico CLAP vs terminologia musicale corretta

Coppie `prompt CLAP nel report → terminologia musicale che useresti`:

- `<prompt skill>` → `<termine corretto>` (tradizione: musica elettroacustica / strumentale / soundscape)
- `<prompt skill>` → `<termine corretto>`
- ...

## 7. Sezioni compositive (timeline manuale)

Stile VB2.pdf: dividi il brano in sezioni con timecode, evento principale,
note descrittive. Servira' a v0.6.0 per validare la segmentazione automatica.

| Sezione | Tempo (mm:ss-mm:ss) | Evento principale | Note frequenziali/gestuali |
|---------|---------------------|-------------------|----------------------------|
| 1 | | | |
| 2 | | | |
| ... | | | |

## 8. Lettura compositiva dell'agente

Se il report contiene la sezione "Lettura compositiva":

- **Pertinente?**
  - [ ] sì, lettura credibile e ben scritta
  - [ ] parzialmente: alcune affermazioni sono giuste, altre forzate. Indica quali: `<...>`
  - [ ] no, lettura incoerente. Motivo principale: `<...>`
  - [ ] non disponibile (output vuoto, fallback)
- **Errori specifici**:
  >

## 9. Note libere

Tutto cio' che non rientra nelle sezioni precedenti: impressioni di ascolto,
contesto storico-poetico, suggerimenti su nuove feature, casi limite
osservati.

>

