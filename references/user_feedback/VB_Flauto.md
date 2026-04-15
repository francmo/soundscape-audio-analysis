# Feedback utente: VB_Flauto.mp3

Istanza pre-compilata in parte sulla base del report `VB_Flauto_report.pdf`
generato dalla skill v0.5.0 (prima dei fix v0.5.1 su hum contestuale e
allucinazioni CLAP). Aggiorna i campi rimasti vuoti.

---

## 1. Identificazione

- **File**: `VB_Flauto.mp3`
- **Versione skill che ha prodotto il report**: `v0.5.0`
- **Data feedback**: `2026-04-15`
- **Contesto del brano**: `Very Beautiful per flauto solista` di / a partire da
  John Heineman (1973). Esecuzione live con flauto improvvisato sul brano
  originale di Heineman. Tecniche estese (multiphonics, key clicks, air noise),
  scrittura dialogica con accenti melodici, glissandi, momenti di massima
  intensità ("I remember everything", 5:40-6:32). Vedi tabella eventi del
  flauto in `VB2.pdf`.

## 2. PANNs (classificazione semantica primaria)

### Top-1 globale

- **Skill dice**: `Flute` (score `0.6564`)
- **Reale**:
  - [x] corretto

### Top-10 globali

| Posizione | Etichetta PANNs | Score | Valutazione |
|-----------|-----------------|-------|-------------|
| 1 | Flute | 0.6564 | OK |
| 2 | Music | 0.6324 | OK (categoria genitore) |
| 3 | Speech | 0.5832 | <da valutare: c'e' parlato di sottofondo della voce di Heineman?> |
| 4 | Wind instrument, woodwind instrument | 0.4390 | OK |
| 5 | Musical instrument | 0.4201 | OK (genitore) |
| 6 | Inside, small room | 0.1309 | <ambiente acustico: corretto?> |
| 7 | Clarinet | 0.0294 | <falso positivo o tecnica estesa che evoca clarinetto?> |
| 8 | Guitar | 0.0251 | <verosimilmente falso positivo da key clicks> |
| 9 | Classical music | 0.0232 | <musica colta: si ma non esattamente classical> |
| 10 | Animal | 0.0230 | <falso positivo da air noise/multiphonics?> |

### Frame dominanti

- **Categoria + percentuale frame**: `Flute 61.8%`
- **Coerenti con la tua percezione del brano?**
  >

## 3. CLAP (auto-tagging italiano)

### Top-10 globali

> Compila dalla pagina CLAP del report PDF. Indica tag per tag se il prompt
> italiano e' pertinente o un'allucinazione.

| Posizione | Prompt italiano | Score | Pertinente? | Note |
|-----------|-----------------|-------|-------------|------|
| 1 | | | | |
| 2 | | | | |
| ... | | | | |

### Tag flagged come allucinazioni (corsivo nel PDF)

> Nella v0.5.0 il flag non esisteva. Dopo aver rilanciato con v0.5.1, segnala
> qui se i tag in corsivo erano effettivamente allucinazioni o erano
> pertinenti.

### Prompt CLAP mancanti

Categorie/eventi del brano non coperti:

- `improvvisazione su tecniche estese di flauto (multiphonics, key clicks, air noise alternati)`
- `scrittura dialogica strumentale con accenti narrativi`
- `<altri da aggiungere>`

### Prompt CLAP da rimuovere

>

## 4. Hum check

- **Verdetto complessivo skill (v0.5.0)**: `presente` (picco 150 Hz +5.61 dB ratio +11.57 dB)
- **Reale**:
  - [x] falso positivo: 150 Hz e' un'armonica di nota di flauto, non ronzio elettrico
- **Hint contestuale "likely_musical_harmonic"** (v0.5.1): è scattato?
  > Da verificare ri-eseguendo l'analisi con v0.5.1.

## 5. Mapping accademico (academic_hints)

> Compila guardando la sezione CLAP del report (campo academic_hints).

- **Krause**: `<...>`
- **Schafer**:
- **Schaeffer type**:
- **Smalley motion**:
- **Chion modes present**:
- **Westerkamp soundwalk relevance**:

## 6. Lessico CLAP vs terminologia musicale corretta

Coppie da popolare:

- `<prompt skill>` → `<termine corretto>`
- ...

## 7. Sezioni compositive

Riferimento gia' presente in `VB2.pdf` (tabella "Eventi del flauto"). Riporta
qui in forma sintetica per integrazione nella skill (v0.6.0 segmentazione
strutturale).

| Sezione | Tempo (mm:ss-mm:ss) | Evento principale | Note |
|---------|---------------------|-------------------|------|
| 1 | 0:00-1:53 | Suoni di tasti, fruscii | Attacchi leggeri, attivita' nelle medie 2-4 kHz |
| 2 | 1:53-3:46 | Ingressi flauto, attacchi leggeri | Brevi melodie, scale ascendenti, crescendo |
| 3 | 3:46-5:39 | Glissandi, note alte | Curve diagonali, alternating air/key noise. "I speak English" |
| 4 | 5:39-7:32 | Massima intensita', tecniche estese | Spettro fino 12-14 kHz, multiphonics. "I remember everything" |
| 5 | 7:32-9:25 | Dinamiche variate, fruscii | Scale ascendenti, arpeggi. "Very very beautiful" |
| 6 | 9:25-11:20 | Decrescita, gesti conclusivi | Suoni residuali, fruscii, chiusura |

## 8. Lettura compositiva dell'agente

> Compila sulla base di quello che il PDF riporta nella sezione "Lettura
> compositiva". Se ne segnali errori, posso istruire l'agente a evitarli.

## 9. Note libere

>
