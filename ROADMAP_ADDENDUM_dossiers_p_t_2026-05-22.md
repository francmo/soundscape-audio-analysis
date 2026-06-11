# Roadmap addendum — pattern emersi dai dossier P&T Macerata (22 maggio 2026)

**Workspace skill**: `~/.claude/skills/soundscape-audio-analysis/`
**Workspace dossier sorgente**: `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/`
**Documento precedente collegato**: `ROADMAP_ADDENDUM_caso_a_2026-05-15.md` (interventi già pushati come v0.12.6, qui ne traccio nuovi)

## 0. Contesto

Questo addendum raccoglie i pattern di forzatura, allucinazione e semplificazione della skill emersi dal confronto fra l'output automatico (PDF skill, summary.json, agent_payload.json) e l'ascolto first-hand documentato di quattro studenti del corso "Processi e Tecniche dello Spettacolo Multimediale" all'Accademia di Belle Arti di Macerata, A.A. 2025-2026. I dossier sono in `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/` (sottocartelle `caso_a/`, `caso_b/`, `caso_d/`, `caso_c/`).

I dossier sono in stati diversi del workflow iterativo a 6 tappe:
- **A**: v1 ricevuta 8/05, feedback v1 inviato 15/05, skill v0.12.5 e v0.12.6 generate, in attesa v2 dello studente.
- **B**: v1 ricevuta 22/05, feedback v1 inviato 22/05, v2 ricevuta 22/05, skill v0.12.5 generata 22/05, Nota 3 rilievi inviata 22/05, in attesa self-FC.
- **D**: v1 ricevuta 15/05, feedback v1 inviato 22/05, in attesa v2.
- **C**: v1 ricevuta 8/05 (scheda first-hand su sollecito 22/05), feedback v1 inviato 22/05, in attesa v2.

I file PDF skill di riferimento (per accedere ai dati grezzi):
- `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_a/_skill_outputs/v0.12.5/report.pdf` (e v0.12.6/)
- `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_b/_skill_outputs/v0.12.5/caso_b_file1_audio_report.pdf`
- (D e C: skill non ancora lanciata, in attesa v2)

I documenti diagnostici di docente che hanno guidato l'identificazione dei pattern:
- `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_a/_feedback_docente/FEEDBACK_v1_15_05_2026.{pdf,docx}`
- `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_b/_feedback_docente/NOTA_3_rilievi_self_FC_caso_b.{pdf,html,docx}`
- `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/_internal_rilettura_comparativa_caso_a.md` (rilettura comparativa interna v0.12.5 vs first-hand A)

## 1. Pattern emersi

Sei pattern documentati. Per ciascuno: definizione, casi di studio, file di riferimento, ipotesi sulla causa nel codice skill.

### Pattern 1 — CLAP italiano allucina associazioni storiche/geografiche notevoli su materiali ordinari

**Definizione**: il classificatore CLAP italiano tende ad associare file con presenza vocale densa o ambiente urbano italiano a categorie storiche/geografiche notevoli del vocabolario prompt, anche quando il materiale è di vita ordinaria contemporanea. Pattern di pull verso il "significativo" che catalizza allucinazioni.

**Casi**:
- **B v2** (bar Mamò Macerata, 22/05/2026, ora di pranzo): top CLAP global "Registrazione d'archivio di manifestazione del Sessantotto" (0.355). Compare in `dominant_clap_prompt` di S1 e S2, presente nella narrativa segmentata di 3 blocchi su 4. Anche "porto peschereccio croato con motori a gasolio e gabbiani" (0.312) e "microfoni sul palco con larsen di ritorno" (0.314) in top 5.
- **A v1** (bagno domestico, mattina): pattern documentato nella rilettura comparativa interna (`_internal_rilettura_comparativa_caso_a.md`), con prompt analoghi che attribuiscono associazioni atmosferiche fuori contesto.

**Ipotesi sulla causa**: nel file `references/clap_prompts_italian.json` (o equivalente), alcuni prompt di categoria "soundscape politico urbano", "paesaggi dalmati e adriatici", "performance multimediale" hanno embedding che coprono porzioni dello spazio latente CLAP molto ampie e catalizzano l'attribuzione a materiali con presenza vocale densa. Effetto "calamita" su prompt evocativi/storici.

### Pattern 2 — PANNs confonde transienti umani puntuali con fauna animale per similitudine spettrale

**Definizione**: il classificatore PANNs identifica eventi sonori puntuali umani (tacchi su pavimento duro, oggetti percussivi) come classi animali per similitudine del profilo dei transienti (attacchi netti, banda larga, brevi).

**Casi**:
- **B v2**: tacchi della signora annotati a `00:02-00:23` (marker `schaeffer.profilo.discontinuo`) → PANNs identifica "horse" 0.23 e "clip-clop" 0.38 nella narrativa segmentata del blocco `01:00-01:30`.

**Ipotesi sulla causa**: PANNs è pre-addestrato su AudioSet, dove "clip-clop" è prevalentemente associato a equini (rare istanze di tacchi umani su pavimento duro). Mancanza di post-processing che filtri queste classi animali quando il contesto Krause stimato è "antropofonia" dominante (anti-correlazione semantica).

### Pattern 3 — Etichetta Hi-Fi/Lo-Fi calcolata globalmente sull'intero file, ignora variabilità temporale

**Definizione**: la skill produce una singola etichetta Hi-Fi/Lo-Fi per l'intero file basandosi su parametri dinamici aggregati (LRA, dynamic range, noise floor). Per file con marcata variabilità tra sezioni strutturali, l'etichetta globale maschera l'arco formale interno.

**Casi**:
- **B v2**: etichetta skill `"Lo-Fi (bassa dinamica, possibile saturazione di rumore di fondo)"` score 2/5. Lo studente nella scheda §4 v2 argomenta correttamente "misto" in 3 fasi temporali (hi-fi 00:03-00:30 con canzone e tacchi distinguibili; lo-fi da 01:00 con chiacchiericcio infittito; leggermente hi-fi 01:47-02:00). La lettura first-hand è più fine di quella della skill.

**Ipotesi sulla causa**: il calcolo Hi-Fi/Lo-Fi è in un singolo blocco di `scripts/spectral.py` (o equivalente) che opera sull'intero array audio, non per sezione strutturale. La struttura per sezione esiste già (sezione `structure.sections` in summary.json), basta riusarla.

### Pattern 4 — Concentrazione spettrale anomala nelle basse non interpretata come possibile artefatto di registrazione

**Definizione**: quando la distribuzione spettrale è dominata da contenuto in sub-bass+bass (>60% complessivo), spesso significa handling noise del microfono mobile, vibrazioni del piano d'appoggio, vento sul mic non protetto, o DC offset basso. La skill riporta il dato ma non lo qualifica come potenziale artefatto.

**Casi**:
- **B v2** (iPhone 8 tenuto in mano + appoggiato): `bands_schafer_pct` Sub-bass 41.48 + Bass 40.66 = **82.14%**, centroide 1630 Hz, picco a 48.4 Hz (17.59 dB). Distribuzione anomala per un soundscape urbano dominato da voci. Lo studente non lo nota (correttamente, percettivamente il file suona "vocale"): è artefatto di registrazione, non contenuto significativo del soundscape.

**Ipotesi sulla causa**: in `scripts/spectral.py` la voce `bands_schafer_pct` viene riportata in summary.json senza un campo di interpretazione complementare. Aggiungere un campo `bands_schafer_alert` (oppure un verdetto in `technical`) che si attiva sopra soglia.

### Pattern 5 — Etichette strutturali ripetitive e poco differenzianti

**Definizione**: la skill assegna a sezioni strutturali diverse la stessa etichetta `signature_label` (es. "antropofonia moderata tonale") quando le sezioni in realtà hanno caratteristiche diverse e meriterebbero etichette differenziate.

**Casi**:
- **B v2**: S1 (0-30s) e S2 (30-70s) hanno entrambe `signature_label: "antropofonia moderata tonale"`, varia leggermente in S3 (70-120s) con "soffusa tonale". Lo studente nelle proprie sezioni Struttura JSON distingue "apertura/sviluppo/coda" con tre note diverse ben articolate. La skill è meno fine.

**Ipotesi sulla causa**: la generazione di `signature_label` in `scripts/structure.py` (o `scripts/agent_bridge.py`) usa un template che combina pochi parametri (krause_dominant + intensità RMS + flatness), che producono pochi valori discreti possibili. Aumentare la dimensionalità del vettore di firma (centroide, banda dominante, panns_dominant, presenza/assenza di onset density) per ottenere etichette più variate.

### Pattern 6 — Etichetta "spettro molto tonale" applicata a soundscape urbani larghi

**Definizione**: la skill etichetta come "spettro molto tonale" file con flatness 0.007-0.013, anche se il materiale è un soundscape urbano contenente voci, traffico, oggetti percussivi. "Tonale" è qualifica fuori asse rispetto a un soundscape urbano largo che fisiologicamente ci si aspetterebbe "noisy" o "broadband".

**Casi**:
- **B v2**: tutti e quattro i blocchi della narrativa segmentata (`00:00-00:30`, `00:30-01:00`, `01:00-01:30`, `01:30-02:00`) sono etichettati "spettro molto tonale" con flatness 0.007-0.013.

**Ipotesi sulla causa**: la soglia di flatness sotto la quale si attiva "tonale" è troppo alta (probabilmente 0.02 o 0.03). Per soundscape urbani realistici, la flatness tipica è 0.01-0.05 e questo intervallo è ancora "rumoroso" percettivamente. Rivedere le soglie in `scripts/spectral.py` o nel template narrative.

## 2. Interventi sicuri da fare subito (da 1 a 4)

Questi quattro interventi sono motivati dai pattern documentati sopra, non richiedono training ML né raccolta dati ulteriore, e si possono implementare con logica di post-processing nel codice Python della skill.

### Intervento A — Hi-Fi/Lo-Fi per sezione strutturale

**Cosa fare**: oggi `hi_fi_lo_fi` è calcolato sull'intero array audio in `scripts/spectral.py` (verificare il nome del file esatto). Aggiungere un campo `hi_fi_lo_fi_per_section` in `summary.json` che riporta, per ciascuna sezione di `structure.sections`, un'etichetta e uno score locali. Mantenere il campo globale `hi_fi_lo_fi` per backward compat.

**Implementazione approssimativa**:
```python
# in spectral.py o nuovo file structure_spectral.py
def compute_hi_fi_lo_fi_per_section(audio, sections, sr):
    return [
        {**section, "hi_fi_lo_fi": compute_hi_fi_lo_fi(audio[start:end], sr)}
        for section in sections
        for start, end in [(int(section.t_start_s*sr), int(section.t_end_s*sr))]
    ]
```

**Verifica**: rilanciare su B v2 e confermare che le 3 sezioni S1/S2/S3 ricevano etichette diverse (atteso: S1 più hi-fi, S2 più lo-fi, S3 mid). Confronto con scheda §4 v2 di B.

**Riflesso in agent_payload e PDF**: il template del PDF (in `templates/`) deve includere una tabella aggiuntiva "Hi-Fi/Lo-Fi per sezione". Il prompt all'agente compositivo (`scripts/agent_bridge.py` o `references/composer_prompt.txt`) deve poter usare i dati per sezione per produrre una lettura più sfumata.

### Intervento B — Avviso quando concentrazione spettrale anomala nelle basse

**Cosa fare**: aggiungere in `summary.json` (sezione `technical` o `spectral`) un campo `bands_schafer_alert` che si attiva con messaggio quando la somma di Sub-bass + Bass supera 60%.

**Implementazione approssimativa**:
```python
# in scripts/spectral.py
def compute_bands_schafer_alert(bands_pct):
    low_sum = bands_pct.get("Sub-bass", 0) + bands_pct.get("Bass", 0)
    if low_sum > 60:
        return {
            "level": "warning",
            "message": f"Distribuzione spettrale dominata dal sub-bass+bass ({low_sum:.1f}%): "
                       "plausibile artefatto di handling/microfono mobile/vibrazione del piano "
                       "d'appoggio. Verificare in cuffia se il contenuto basso è percettivamente "
                       "significativo o no.",
            "low_sum_pct": low_sum,
        }
    return None
```

**Verifica**: rilanciare su B v2 (atteso: alert attivo, 82%) e su A v1 (atteso: alert non attivo, distribuzione spettrale più equilibrata).

**Riflesso in PDF**: callout warning nella sezione Spettrale del PDF (in `templates/`), simile ai callout di clipping/hum esistenti.

### Intervento C — Trascrizione speech opzionale auto-attivata sopra soglia

**Cosa fare**: oggi `--speech` è opzionale (default off). Per file dove Speech > 80% nei frame PANNs dominanti (caso B: 83.33%), attivare automaticamente la trascrizione come default, con override `--no-speech` per disabilitare.

**Implementazione approssimativa**:
```python
# in scripts/cli.py o scripts/analyze.py
def should_auto_enable_speech(panns_dominant_frames, threshold=0.8):
    speech_pct = sum(
        f.pct for f in panns_dominant_frames if f.name == "Speech"
    )
    return speech_pct / 100 >= threshold

# nel main flow
if not args.no_speech and should_auto_enable_speech(...):
    args.speech = True
```

**Verifica**: rilanciare B v2 senza flag esplicito (atteso: speech_presence attiva nel summary).

**Costo**: la trascrizione speech è lenta (richiede Whisper o equivalente). Soglia 80% è cauta. Considerare anche `--speech-light` per estrazione delle sole pause/durate vocali, senza testo, come compromesso veloce.

### Intervento D — Etichette strutturali più variate

**Cosa fare**: rivedere la generazione di `signature_label` in `scripts/structure.py` (o `scripts/agent_bridge.py`). Sostituire il template fisso che combina 2 dimensioni (krause + intensità + flatness binarizzata) con un sistema che combini almeno 4 dimensioni con valori discreti più ricchi: krause_dominant (3 valori) × intensità (4 livelli: silenziosa/soffusa/moderata/marcata) × centroide_banda (4 valori: sub-bass/bass/mid/high) × onset_density (3 valori: sparsa/media/densa). Possibili etichette generate: 3 × 4 × 4 × 3 = 144 combinazioni, molto più espressive.

**Verifica**: rilanciare su B v2 e A v1, confermare che sezioni diverse ricevano etichette diverse.

**Bonus**: rivedere anche la soglia di "molto tonale" (pattern 6 sopra). Probabilmente serve etichetta "moderatamente tonale" per flatness 0.005-0.015 e "molto tonale" solo per flatness < 0.005.

## 3. Interventi da rimandare (E, F)

### Intervento E — Patch ai prompt CLAP italiani che catalizzano allucinazioni

**Cosa serve per attaccarlo**: identificare i prompt specifici del vocabolario CLAP italiano (in `references/clap_prompts_italian.json` o simile) che producono allucinazioni su materiali ordinari. Servono almeno 5-6 casi documentati con caratteristiche audio simili (presenza vocale densa, ambiente urbano italiano contemporaneo) per identificare i prompt "calamita" con sicurezza.

**Attualmente**: 2 casi (B + A). Insufficienti per intervenire mirato senza rischio di rimuovere prompt utili.

**Aspettare**: self-FC di B (può documentare altri pattern), v2 di D e C (file diversi: cucina con macchina caffè, finestra con uccelli e taglia erba), eventuali futuri dossier di A v2.

**Quando ho 5+ casi**: estrarre il set di prompt che ricorrono in alta posizione (top 5) su materiali ordinari, classificarli per categoria semantica (storico, geografico, atmosferico), valutare se rimuoverli del tutto oppure assegnar loro un peso negativo basso (`weight: -0.5`) nello scoring.

### Intervento F — Filtro post-processing PANNs su classi fauna in contesto antropico

**Cosa serve per attaccarlo**: capire se il pattern (tacchi → clip-clop/horse) è generale o specifico a tacchi su pavimento di un certo materiale. Servono altri casi simili (oggetti percussivi umani in ambiente antropico) per generalizzare il filtro.

**Attualmente**: 1 caso (B). Insufficiente.

**Aspettare**: self-FC di C (passi di cane reale + altri rumori da finestra), v2 di D (cucina con possibili oggetti percussivi), eventualmente A v2 (bagno con doccia, niente animali, ma possibili impulsi domestici).

**Quando ho 3+ casi**: aggiungere in `scripts/classifier.py` (o equivalente) una logica del tipo "se panns identifica classe animale CON confidenza media/bassa (< 0.5) E krause_dominant stimato == antropofonia, declassare la classe animale di un fattore 0.7". Validare che la logica non sopprima animali reali quando ci sono.

## 4. Casi-test per validazione post-fix

Quando avrai implementato gli interventi A-D, rilancia la skill v0.13 su questi 2 file e confronta con l'output attuale:

### Test 1 — B v2 (bar Mamò, urbano antropico, handling iPhone 8)
- File: `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_b/v2/caso_b_file1_audio.mp3`
- Output v0.12.5 di riferimento: `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_b/_skill_outputs/v0.12.5/`
- Pattern attesi nella v0.13:
  - **A**: 3 sezioni con etichette Hi-Fi/Lo-Fi diverse (atteso S1 hi-fi, S2 lo-fi, S3 mid)
  - **B**: alert spettrale attivo (82% basse, soglia 60%)
  - **C**: speech trascrizione automatica attiva (83.33% > 80%)
  - **D**: 3 etichette strutturali differenziate (non più "antropofonia moderata tonale" ×2)

### Test 2 — A v1 (bagno domestico, gesti + acqua + cane lontano)
- File: `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_a/caso_a_file1_audio.mp3`
- Output v0.12.5 di riferimento: `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_a/_skill_outputs/v0.12.5/report.pdf`
- Output v0.12.6 di riferimento: `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_a/_skill_outputs/v0.12.6/report.pdf`
- Pattern attesi nella v0.13:
  - **A**: 3 sezioni con etichette Hi-Fi/Lo-Fi che riflettano la struttura (atteso: Inizio domestico hi-fi, Sviluppo doccia lo-fi/saturato, Fine quasi hi-fi)
  - **B**: alert spettrale NON attivo (file più equilibrato spettralmente di B, da verificare)
  - **C**: speech trascrizione NON attiva (file dominato da water/material, non Speech)
  - **D**: 3 etichette strutturali differenziate per Inizio/Sviluppo/Fine

## 5. Note per la prossima sessione

**Apertura della sessione**: aprire Claude Code direttamente dalla cartella della skill:
```bash
cd ~/.claude/skills/soundscape-audio-analysis/
claude
```

In questo modo le memorie e le regole specifiche del progetto skill (`.claude/CLAUDE.md` e relativi) sono attive, e il git è già pronto per commit/push. Le memorie del corso Macerata (workspace `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/`) restano accessibili come riferimento esterno ma non interferiscono.

**Primo passo della prossima sessione**: rileggere questo addendum + `CHANGELOG.md` (per allineare l'ultimo stato della skill, v0.12.6) + `ROADMAP_ADDENDUM_caso_a_2026-05-15.md` (per non duplicare interventi già fatti).

**Ordine consigliato degli interventi**:
1. Intervento D (etichette strutturali variate): più semplice, basso rischio, riusabile per migliorare anche A.
2. Intervento A (hi-fi/lo-fi per sezione): media complessità, riusa structure.sections esistente.
3. Intervento B (alert sub-bass+bass): semplice, callout pulito nel PDF.
4. Intervento C (speech auto): più delicato (impatta performance e costo computazionale), va testato con cura.

**Stima orientativa di effort** (sessione Claude Code Opus 4.7): A 1-2h, B 30-45 min, C 1h, D 1-2h. Totale 4-6 ore di sessione attiva per arrivare a v0.13 testata sui 2 casi-test.

**Cosa NON fare in questa fase**: niente interventi E, F (CLAP allucinazioni, PANNs filtri animali) finché non abbiamo 5+ casi documentati (vedi sezione 3). Anche niente refactor architetturale, solo interventi puntuali sui pattern documentati. Mantenere CHANGELOG.md aggiornato per ciascun intervento.

**Update di questo addendum**: dopo aver implementato e validato gli interventi A-D, aggiungere in fondo a questo file una sezione "Stato implementazione" con i commit di riferimento, così resta tracciabile.

## 6. Riferimenti rapidi

- Workspace skill: `~/.claude/skills/soundscape-audio-analysis/`
- Workspace dossier P&T: `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/`
- ROADMAP principale skill: `ROADMAP.md` (radice skill)
- Addendum precedente: `ROADMAP_ADDENDUM_caso_a_2026-05-15.md`
- Rilettura comparativa interna A: `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/_internal_rilettura_comparativa_caso_a.md`
- Nota 3 rilievi B: `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_b/_feedback_docente/NOTA_3_rilievi_self_FC_caso_b.{pdf,html,docx}`
- Feedback v1 B/D/C: nelle rispettive `_feedback_docente/` di ciascuno studente

## 7. Stato implementazione (aggiornato 22/05/2026)

Tutti e quattro gli interventi sicuri (A, B, C, D) sono stati implementati nella release **v0.13.0** e validati su due casi-test:

| Intervento | Stato | File modificati | Test aggiunti |
|---|---|---|---|
| D - signature_label 4D + soglie tonale | Implementato | `scripts/structure.py`, `scripts/locale_it.py`, `scripts/config.py`, `scripts/narrative.py` | 10 nuovi in `test_structure.py` |
| A - hi-fi/lo-fi per sezione | Implementato | `scripts/structure.py`, `scripts/report_pdf.py`, `templates/agent_prompt.md` | 3 nuovi in `test_structure.py` |
| B - alert sub-bass+bass anomalo | Implementato | `scripts/spectral.py`, `scripts/agent_payload.py`, `scripts/report_pdf.py`, `templates/agent_prompt.md` | 4 nuovi in `test_spectral.py` |
| C - speech trascrizione auto | Implementato | `scripts/speech.py`, `scripts/cli.py`, `scripts/config.py` | 7 nuovi in `test_speech.py` |

**Test suite**: 253 passed + 2 skipped (era 229 in v0.12.6, +24 nuovi).

**Validazione su casi-test**:

| Pattern atteso | B v2 | A v1 |
|---|---|---|
| Alert spettrale sub-bass+bass | Attivo, 82.14% (soglia 60%) | NON attivo, 19.71% |
| Speech auto-attivazione | Attesa (83.3% Speech > 80%) | NON attesa (21.05% Speech < 80%) |
| Etichette strutturali differenziate | 3 sezioni con 2 etichette uniche (vs 1 prima): miglioramento netto, ulteriore differenziazione richiederebbe granularita' centroide piu' fine | 5 sezioni con 5 etichette tutte distinte: target raggiunto |
| Hi-Fi/Lo-Fi per sezione | 3 sezioni Lo-Fi 2/5 (coerente con saturazione bar): atteso vista la distribuzione spettrale, S1/S2/S3 hanno tutte dr basso | 5 sezioni differenziate: S1 Medio 3/5, S2-S4 Lo-Fi 2/5, S5 Hi-Fi 4/5 (target raggiunto) |

**Output salvati** in:
- `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_b/_skill_outputs/v0.13.0_fast/`
- `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/v1_dossiers/caso_a/_skill_outputs/v0.13.0_fast/`

**Interventi rimandati**:
- E (CLAP allucinazioni): in attesa 5+ casi documentati (oggi 2). Riprendere dopo self-FC B + v2 D/C.
- F (PANNs filter su fauna in contesto antropico): in attesa 3+ casi (oggi 1). Riprendere dopo self-FC C.

**Follow-up minore identificato in validazione**:
- Quando l'utente passa `--no-speech` esplicitamente, il suggerimento giallo "rilancia con --speech" continua a essere emesso: il messaggio e' contraddittorio rispetto alla scelta esplicita dell'utente. Da risolvere in v0.13.1 distinguendo `do_transcribe_speech=None` (auto) da `do_transcribe_speech=False` (esplicito off) prima di chiamare `check_speech_suggestion`.
- Pattern 5 parzialmente risolto: S1 e S2 di B ricevono ancora la stessa signature_label perche' le 4 dimensioni discrete catturano effettivamente caratteristiche aggregate simili. Una rifinitura delle soglie centroide_banda (es. 250/750/1500/3000 invece di 250/1000/4000) potrebbe separarle, ma rischia overcompensation sui brani gold. Da valutare in v0.13.1 con un test di non regressione sul corpus golden.

**Prossimo passo**: commit + push v0.13.0 sul repo pubblico, verifica che Zenodo bozza non sia bloccata dalla nuova versione.

---

## Addendum 29/05/2026 — consolidamento pattern dai tre dossier (verso v0.14)

Documento sorgente: `~/Documents/_PROGETTI/didattica/aba-macerata-sprint-soundscape/_internal_pattern_allucinazioni_clap.md`. Consolida le evidenze esatte (estratte dai `summary.json`) dei tre dossier con output skill: **C** (finestra/Macerata), **B** (bar/Macerata), **A** (bagno domestico).

**Aggiornamento conteggio casi**: gli interventi E (allucinazioni CLAP) e F (filtro PANNs su fauna in contesto antropico) erano rimandati in attesa di più casi. Oggi i casi documentati con verità first-hand sono **3 dossier**, e due pattern sono **cross-confermati su file indipendenti**, quindi E ed F diventano azionabili. Nota metodologica: i dati duri CLAP/PANNs sono bit-identici fra 0.12.5/0.12.6/0.13.0 (cambiano solo i layer interpretativi).

**Pattern consolidati e punti di calibrazione (target v0.14):**

1. **Prior di ordinarietà / de-pesatura dei prompt "notevoli"**: i prompt geografici-marcati (costa, porto: C 0.31, B 0.31) e storico-sociali (B "Sessantotto" 0.355 rank 1) sono attrattori del vocabolario CLAP. De-pesarli o subordinarli a prove specifiche.
2. **Rifare `likely_hallucination`**: oggi è `false` su tutti i prompt del top_global, incluso il "Sessantotto" → inerte proprio sui casi peggiori. Euristica possibile: alzare il flag quando il top prompt è geo/storico-notevole, le prove PANNs sono generiche e i punteggi assoluti bassi (0.30-0.36).
3. **Plausibility "high" solo su match specifico** non di famiglia (C: "gallo all'alba in villaggio costiero" validato `high` solo perché PANNs Animal/Bird = 0.276).
4. **Falso positivo equino `Horse`/`Clip-clop` su transienti percussivi** (intervento F): cross-confermato su 2 file indipendenti (taglia erba C picco 0.287; tacchi B Clip-clop 0.40). Sopprimere/marcare e **non amplificarlo nella narrativa** (su C è diventato "trazione animale"): aggiungere soglia sul layer narrativo per i tag marginali.
5. **Caveat NDSI su ambienti idrici**: A NDSI 0.711 "biofonia alta" mentre la banda 2-8 kHz è acqua di doccia. Segnalare quando `Water`/geofonia domina 2-8 kHz.
6. **Coerenza fra layer**: risolvere contraddizioni come `schafer_fidelity` CLAP-pesato "hi-fi" vs `structure` per-sezione "Lo-Fi" (A).
7. **`speech_mediation` (introdotta in v0.13.0) fallisce sul caso bersaglio**: A TV telegiornale filtrato classificato `direct`. Usare il file A come test di regressione del parlato mediato.
8. **Layer narrativo**: prosa generalizzata ("la stanza che respira") e pseudo-quantificazione ("Smalley dilation 66%" presentato netto mentre `tentative: true`). Ancorare la narrativa a timestamp/eventi e propagare il flag `tentative`.

Dati duri da spot-verificare alla fonte prima della pubblicazione nel paper. Incongruenze di etichettatura versione da sanare: cartella `caso_b .../v0.13.0_fast/` con `version: 0.12.6`; summary C `v0.12.5` vs report `v0.13.0`.

**Raffinamento 29/05 (dalla relazione critica di C).** I punti 1-2 vanno estesi con la nozione di **auto-rinforzo per accumulo** del CLAP: non solo de-pesare il singolo prompt "notevole", ma penalizzare/segnalare quando i **top-N prompt si addensano su un'unica famiglia tematica notevole** (geografica/storica) mentre le prove PANNs restano generiche (C: 3/5 top prompt costiero-portuali; B: il "Sessantotto" propagato a tutte le sezioni). La **concentrazione tematica del top-N** diventa un input diretto per il rifacimento di `likely_hallucination` (punto 2). Citazione fonte: "una volta formulata la prima ipotesi la rafforza autonomamente, accumulando riferimenti sempre meno attendibili" (relazione `caso_c_file1_relazione_critica.pdf`).
