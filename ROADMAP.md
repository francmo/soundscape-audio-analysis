# Roadmap soundscape-audio-analysis

Documento unico per orientarsi: cosa fa la skill oggi, cosa e' pianificato,
chi fa cosa. Aggiornato a ogni release.

**Versione corrente**: 0.5.2 (15 aprile 2026)
**Test suite**: 117 passed + 2 skipped (benchmark e whisper reale gated)
**Branch**: `main`

---

## Stato corrente (v0.5.2)

### Capabilities attive

- **Analisi tecnica**: livelli (peak, RMS, crest, DR, noise floor), LUFS EBU
  R128, true peak, clipping, DC offset.
- **Hum check con baseline locale**: bande 30-45 e 70-95 Hz, evita falsi
  positivi su sorgenti tonali. **v0.5.1**: arricchito con `interpretation_hint`
  che marca i picchi come "probabile componente armonica strumentale" quando
  flatness < 0.05 e top-1 PANNs e' uno strumento musicale (50 label
  AudioSet).
- **Analisi spettrale**: bande Schafer (7), centroide, rolloff, flatness,
  ZCR, onset density, hi-fi/lo-fi score.
- **Indici ecoacustici**: ACI, NDSI, H, BI (default basic). ADI/AEI in
  modalita' extended.
- **Classificazione semantica PANNs CNN14** (default): 527 classi AudioSet,
  pre-check LUFS per evitare bug "97% Silence" su file molto bassi.
- **Auto-tagging CLAP italiano**: 193 prompt v1.3 in 18 categorie
  (geofonia, biofonia, antropofonia *, musica, sacralita sonora, paesaggi
  italiani specifici, **paesaggi mediterranei generici** nuova in v0.5.2,
  ecc.). **v0.5.1**: filtro allucinazioni speech-related che marca con
  `likely_hallucination=True` i tag con keyword voce/parlato quando PANNs
  Speech score <= 0.10. **v0.5.2**: flag `geo_specific=True` sui tag
  italo-specifici (categoria "paesaggi italiani specifici" o keyword
  italiane nel prompt), resi in corsivo nel PDF con caption dedicata per
  evitare falsi positivi su materiale mediterraneo non italiano.
- **Mapping accademico** (v0.4.0): hint aggregati su Schafer (keynote/signal/
  soundmark), Truax (listening modes), Krause (biofonia/antropofonia/
  geofonia), Schaeffer (tipologia), Smalley (motion processes), Chion
  (causale/semantico/ridotto), Westerkamp (soundwalk relevance).
- **Trascrizione dialoghi opt-in** (v0.5.0): flag `--speech` attiva
  faster-whisper large-v3 + Silero VAD pre-filtro + traduzione italiana via
  `claude -p --model claude-haiku-4-5`. Suggerimento stderr giallo se PANNs
  rileva Speech dominante > 25% dei frame senza il flag.
- **Multicanale**: rilevamento layout (mono/stereo/quad/5.1/7.1/5.1.4/
  7.1.4), per-channel levels, downmix.
- **Narrativa segmentata**: prosa italiana finestrata 30s.
- **Lettura compositiva agente**: subprocess `claude -p --agents
  soundscape-composer-analyst`. **v0.5.1**: telemetria stderr per diagnosi
  failure mode (returncode, stderr completo, n. tentativi, durata).
- **Report PDF**: copertina, metadati, livelli, diagnosi (con hum hint),
  spettrale, ecoacustica, semantica, CLAP (con tag flagged in corsivo +
  academic_hints), dialoghi trascritti (se `--speech`), multicanale,
  narrativa, lettura compositiva, colofone.
- **Report corpus**: sub-comando `soundscape report` per analisi
  comparativa multi-file con grafici (loudness bar, dynamic range, bande
  Schafer, indici ecoacustici, similarita' CLAP).

### File chiave per orientarsi

| Cosa | Dove |
|------|------|
| Pipeline CLI | `scripts/cli.py::_analyze_single` (10 step numerati) |
| Costanti centrali | `scripts/config.py` |
| Stringhe italiane | `scripts/locale_it.py` |
| Hum check | `scripts/hum.py` |
| Spettrale | `scripts/spectral.py` |
| Tecnico (LUFS) | `scripts/technical.py` |
| Ecoacustico | `scripts/ecoacoustic.py` |
| PANNs | `scripts/semantic.py` |
| CLAP | `scripts/semantic_clap.py` |
| Mapping accademico CLAP | `scripts/clap_mapping.py` + `references/clap_academic_mapping_it.json` |
| Vocabolario CLAP | `references/clap_vocabulary_it.json` |
| Speech | `scripts/speech.py` |
| Narrativa segmentata | `scripts/narrative.py` |
| Agente compositivo | `scripts/agent_bridge.py`, `templates/agent_prompt.md`, `~/.claude/agents/soundscape-composer-analyst.md` |
| PDF | `scripts/report_pdf.py` |
| Tassonomie di riferimento | `references/taxonomies/` |
| Profili GRM | `references/grm_profiles/` |
| Feedback utente | `references/user_feedback/` |

---

## Pianificato (priorita' decrescente)

### v0.6.0 — Strumento compositivo (16-22 h, prossima sessione Plan Mode)

Trasforma la skill da "report statistico" a "strumento di analisi
compositiva" allineato al modo in cui Francesco scrive le analisi
(rif. VB2.pdf, Air Piece.pdf).

**Cinque feature nuove correlate**:

1. **`scripts/structure.py` (nuovo) - segmentazione strutturale**.
   Changepoint detection su RMS envelope + flatness + ZCR + categoria PANNs
   dominante per finestre. Output: lista di sezioni con confini temporali
   e firma caratterizzante. Risolve il gap "skill statistica vs analisi
   per sezioni" osservato comparando con le tabelle manuali in VB2.pdf.

2. **Timeline grafica simbolica nel PDF**. Rendering matplotlib in stile
   VB2.pdf: barre orizzontali per sezione con icone derivate da feature
   dominanti (cerchio per articolati, onde per fruscii, frecce per
   glissandi/crescendo, triangoli per acuti). Ogni sezione ha una "firma
   visiva" sintetica.

3. **`narrative.py` delta-based**. Prima finestra descrizione completa,
   finestre successive solo delta significativi (centroide cambia di +/-
   15%, flatness cambia di +/- 30%, etc.). Risolve la verbosita'
   identificata da Gemini ("Spettralmente il centroide si colloca a 1485
   Hz" ripetuto in ogni segmento).

4. **Flag CLI `--context <file.md>`**. L'utente fornisce biografia autore,
   contesto storico, link video, frasi chiave. Il payload agente lo
   incorpora nella lettura compositiva. Colma il gap "nessun contesto
   extra-audio" rispetto alle analisi manuali.

5. **Allineamento testo-musica**. Quando `--speech` e' attivo, sovrapporre
   timeline VAD alle sezioni strutturali. Annotazione automatica "sezione
   X coincide con parlato in lingua Y", "frase 'I remember everything'
   coincide con momento di massima intensita' a 5:40-6:32".

**File da creare**: `scripts/structure.py`, `tests/test_structure.py`,
estensione di `report_pdf.py` per timeline grafica.
**File da modificare**: `scripts/narrative.py`, `scripts/cli.py`,
`scripts/agent_payload.py`, `templates/agent_prompt.md`,
`references/external_context_schema.md` (nuovo).

**Prerequisito**: aprire Plan Mode con `/plan` per design dettagliato.

### v0.5.3 — Plausibility check CLAP (feedback audio5/Presque Rien N°1)

Hotfix mirato ai gap residui emersi rilanciando Presque Rien N°1 con la v0.5.2
(`references/user_feedback/Presque_Rien_N1.md` sezione "Note libere audio5"):
il flag `geo_specific` ha funzionato e i prompt mediterranei generici sono
entrati in top-10, ma restano 4 classi di hallucination CLAP non coperte dai
filtri attuali. Tempo stimato: 6-10 h.

**Hallucinations residue documentate**:

1. **"Acqua del rubinetto che scorre" (top-1, 0.212)** su sciabordio di onde
   contro scafo in porto peschereccio. CLAP confonde acqua domestica con acqua
   mediterranea. Nessun filtro attuale lo cattura.
2. **"Preghiera collettiva sussurrata in chiesa" (top-2, 0.208)** su voci di
   pescatori e bambini in banchina. Il filtro `likely_hallucination` v0.5.1
   non scatta perche' PANNs vede Speech al 48% dei frame: c'e' voce, ma non
   di preghiera. Serve un livello semantico piu' fine (tipo di voce, non
   solo presenza).
3. **Prompt musicali strumentali**: "Quartetto d'archi in esecuzione",
   "Tastiera elettrica o sintetizzatore", "Musica elettronica ambient",
   "Processione con coro e tamburi", "Campane di chiesa che suonano" compaiono
   ripetutamente nella timeline su field recording di porto. CLAP li propone
   su suoni meccanici o ambientali tonali.
4. **Prompt di composizione soundscape**: "Profilo dinamico in morphing
   continuo", "Transizione dal silenzio notturno a [alba]", "Cross-sintesi fra
   due suoni concreti" entrano come top-1/top-2 in molti segmenti su field
   recording grezzo. CLAP li associa a qualsiasi transizione dinamica.
5. **Confusione motore terrestre/marittimo**: "Treno regionale in arrivo a
   stazione", "Treno ad alta velocita'" vs motore diesel di peschereccio.
   Vocabolario non distingue bene.

**Azioni proposte**:

- **`scripts/clap_plausibility.py` (nuovo) `mark_implausible_tags()`**. Filtro
  post-hoc che marca `plausibility: "low"|"medium"|"high"` sui tag in base
  a consistenza con contesto tecnico. Regole:
  - Prompt di categoria "musica registrata", "sacralita sonora",
    "composizione soundscape", "trasformazioni elettroacustiche", "performance
    multimediale" richiedono PANNs "Music"/"Orchestra"/"Choir"/"Chant" nei
    top-5 globali (score > 0.1) per avere `plausibility: high`. Altrimenti
    `low`.
  - Prompt di categoria "paesaggi italiani specifici" o con keyword
    italo-specifiche richiedono conferma esterna dall'utente (flag
    `geo_specific` gia' in v0.5.2) + `plausibility: medium` di default su
    materiale non identificato.
  - Prompt con keyword "preghiera/liturgia/cerimonia/processione" richiedono
    PANNs "Choir"/"Chant"/"Religious music" nei top-10 per `plausibility:
    high`. Altrimenti `low`, anche se PANNs Speech c'e' genericamente.
  - Prompt "treno/ferrovia/stazione" richiedono PANNs "Train"/"Rail" nei
    top-10 per plausibility alta. Altrimenti degradati.
- **Vocabolario v1.4**: aggiungere 4-6 prompt per motori marittimi specifici
  (gia' abbiamo `mec_13-14`, espandere con "Motore diesel lento di peschereccio
  con scoppio irregolare", "Scafo in legno che cigola sul molo", "Sciabordio
  di onde contro scafo ormeggiato") per dare a CLAP alternative piu' precise
  agli erronei "Treno" e "Acqua del rubinetto".
- **Rendering PDF**: tag con `plausibility: "low"` resi in corsivo grigio (gia'
  usato per allucinazioni) con caption distinta "tag con bassa plausibilita'
  tecnica", separata da `likely_hallucination` (speech-specific) e
  `geo_specific` (geografico). Terza categoria di markup.
- **Test fixture dedicata**: `tests/test_clap_plausibility.py` con 4-5
  casi reali estratti da `audio5_summary.json` per regression coverage sui
  filtri.
- **Payload agente**: propagare `plausibility` nei campi top_global. Istruire
  l'agente a ignorare tag con `plausibility: "low"` come fa gia' con
  `likely_hallucination`.

**Fuori scope v0.5.3** (rinviati a v0.6.0+): post-hoc reranking via embedding
text-audio con modello secondario, fine-tuning CLAP su soundscape annotato.

### v0.5.4 — Hotfix dipendenti dal feedback utente (continuo)

Traduzione di ogni nuovo `references/user_feedback/<brano>.md` in patch
concrete: prompt CLAP aggiunti/rimossi, soglie ricalibrate, regole di
plausibility estese. Cicli da 2-4 h ciascuno.

### v0.7.0+ — Idee successive

Da valutare quando v0.6.0 e' rilasciata e stabile.

- **Confronto strutturale fra brani di un corpus**: analisi del comune
  e del divergente fra sezioni omologhe di brani diversi. Estensione del
  sub-comando `report` corpus.
- **Diarization speech**: separazione speaker quando `--speech` rileva
  voce con probability >= soglia. pyannote-audio o WhisperX.
- **Forced alignment**: timestamp word-level invece che segment-level
  (utile per opere con testo strutturato come Very Beautiful).
- **YAMNet via tensorflow-metal su Apple Silicon**: alternativa MPS al
  classifier PANNs. Richiede aggiungere `tensorflow-metal` a
  `requirements.txt` e test dedicati.
- **Auto-tagging CLAP fine-tuned su soundscape italiano**: training di
  un adapter su corpus annotato dall'utente (servirebbero ~100 brani con
  etichette manuali).
- **Esportazione MIDI/MusicXML** per le sezioni identificate, per
  reimpiego in DAW (Reaper) o sequencer.

---

## Loop di feedback utente

Sistema di miglioramento iterativo basato sulle annotazioni del compositore
(documentato in `references/user_feedback/README.md`):

1. Skill produce report PDF su un brano.
2. Utente apre `references/user_feedback/TEMPLATE.md`, copia in
   `<nome_brano>.md`, compila almeno la sezione 9 (Note libere).
3. Le correzioni vengono tradotte in patch concrete (vocabolario CLAP,
   mapping accademico, soglie filtri).
4. Release v0.X.Y patch dipendente dal feedback.
5. Si ripete su brani diversi per coprire casi limite.

Stato attuale: `VB_Flauto.md` istanza pre-popolata in attesa di
completamento.

---

## Storia release (rimanda a `CHANGELOG.md` per dettagli)

- **v0.5.2** (15/04/2026): hotfix mediterraneo (vocabolario CLAP v1.3 con
  categoria "paesaggi mediterranei generici", flag `geo_specific` sui tag
  italo-specifici, istruzioni agente per riconoscimento brani noti).
  Feedback source: Presque Rien N°1 di Luc Ferrari.
- **v0.5.1** (15/04/2026): hotfix interpretativi (hum contestuale,
  allucinazioni CLAP, diagnostica agent).
- **v0.5.0** (15/04/2026): trascrizione dialoghi opt-in via
  faster-whisper + Silero VAD + traduzione `claude -p`.
- **v0.4.1** (15/04/2026): hotfix off-by-one resample multicanale.
- **v0.4.0** (15/04/2026): espansione vocabolario CLAP (102 -> 172) +
  mapping accademico Schafer/Truax/Krause/Schaeffer/Smalley/Chion/
  Westerkamp.
- **v0.3.3** (15/04/2026): uniformazione italiano nel PDF e nei grafici.
- **v0.3.2** (15/04/2026): abilitazione MPS per PANNs CNN14 su Apple
  Silicon.
- **v0.3.1** e precedenti: vedi CHANGELOG.

---

## Convenzioni

- Italiano corretto in PDF, log utente, commenti d'uso, CHANGELOG.
- Niente em dash, accenti italiani sempre (è, à, ò, ù, ì, é, perché,
  poiché, etc.).
- Acronimi tecnici internazionali (LUFS, RMS, STFT, PANNs, CLAP, MPS,
  VAD) restano in inglese.
- Versioning: minor per nuove feature pubbliche, patch per fix.
  Pre-bump verifica con grep `vX.Y.Z` per catturare tutti i callsite.
- Test prima del commit (suite completa zero regressioni).
