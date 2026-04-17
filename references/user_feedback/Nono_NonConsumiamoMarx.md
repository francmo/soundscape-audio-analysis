# Feedback - Luigi Nono, *Non consumiamo Marx* (1969)

## 1. Identificazione

- **File**: `track_05.mp3` (copia anonimizzata, soundscape-training/audio_blind/)
- **Versione skill che ha prodotto il report**: v0.6.5 con `--speech`
- **Data feedback**: 2026-04-17
- **Contesto del brano**: Luigi Nono, *Non consumiamo Marx* (1969), seconda parte di *Musica-Manifesto n. 1* (la prima è *Un volto, del mare*). 17:36 di durata, prima esecuzione Châtillon-sous-Bagneux 17 maggio 1969. Dedica a Carlos Franqui, poeta rivoluzionario cubano. Voce: Edmonda Aldini. Realizzazione tecnica: Marino Zuccheri, Studio di Fonologia Musicale della RAI, Milano. Materiale:
  - Parigi, maggio 1968: venti scritte murali e slogan (coscienza rivoluzionaria).
  - Venezia, giugno 1968: registrazioni dei boicottaggi studenti-operai-intellettuali contro la Biennale (contestazione Montedison-CIGA).
  - Materiali di strada: manifestazioni, cori, grida.
  - Voci elaborate elettronicamente + campi sonori elettronici originali.
  - "Musica di strada" per agitare la coscienza degli ascoltatori negli spazi pubblici.
- **Gold analitico**: `Nottoli-05-Nono-NonConsumiamoMarx/analisi-luiginono.md` (luiginono.it).

## 2. PANNs

### Top-1 globale

- **Skill dice**: `Speech` (score 0.7573, frame dominanti 90.8%)
- **Reale**: **corretto**. Primo brano del corpus Nottoli dove Speech domina PANNs. Coerente col gold: "musica di strada" con slogan/voci/scritte murali registrate dal vivo + voce Aldini elaborata.

### Top-10 globali

| Posizione | Etichetta PANNs | Score | Valutazione |
|-----------|-----------------|-------|-------------|
| 1 | Speech | 0.7573 | **corretto** (dominante) |
| 2 | Vehicle | 0.2311 | **corretto** (ambiente urbano manifestazione, traffico Parigi/Venezia) |
| 3 | Music | 0.1737 | OK (elaborazione elettronica) |
| 4 | Car | 0.1100 | **corretto** (ambiente urbano) |
| 5 | Male speech, man speaking | 0.1033 | **corretto** (voci operai/studenti) |
| 6 | **Outside, urban or manmade** | 0.0937 | **corretto**, riconosce il contesto urbano di manifestazione |
| 7 | **Narration, monologue** | 0.0672 | **corretto** (slogan recitati, declamazione politica) |
| 8 | Race car, auto racing | 0.0616 | parziale (probabilmente rumore urbano letto come auto veloci) |
| 9 | **Run** | 0.0615 | **suggestivo** (passi di corsa? manifestazione in movimento?) |
| 10 | **Crowd** | 0.0529 | **corretto**, folla di manifestazione |

### Frame dominanti

- Speech 90.8%, Music 3.7%, Vehicle 2.8%, Gong 1.8%, Silence 0.9%.
- **Speech al 90.8%**: dato più nettamente "parlato" di tutto il corpus. Giustamente.

**Nota per il paper**: PANNs qui funziona notevolmente bene nel riconoscere il **contesto urbano di manifestazione** (Speech + Crowd + Run + Outside urban + Narration + Vehicle + Car). La rete AudioSet è stata probabilmente addestrata su registrazioni di news/manifestazioni urbane, quindi **riconosce bene materiali documentali di strada**, molto meglio che su *Basilica* (campane processate) o *Song of Songs I* (cicale processate).

## 3. CLAP

### Top-10 globali

| Posizione | Prompt italiano | Score | Pertinente? | Note |
|-----------|-----------------|-------|-------------|------|
| 1 | Texture granulare densa | 0.304 | sì |
| 2 | Time-stretch estremo di oggetto concreto | 0.301 | sì |
| 3 | Voce umana manipolata acusmatica | 0.299 | **sì, perfetto** (voce Aldini elaborata) |
| 4 | Accumulo granulare stocastico | 0.265 | sì |
| 5 | Trasformazione spettrale progressiva | 0.248 | sì |
| 6 | Voce amplificata con effetti elettronici | 0.232 | sì |
| 7 | Preghiera collettiva sussurrata in chiesa | 0.220 | **no, allucinazione** (non c'è preghiera) |
| 8 | **Spiaggia mediterranea con onde leggere e voci distanti** | 0.217 | **no, grave allucinazione** (brano urbano politico, non spiaggia) |
| 9 | Cross-sintesi fra due suoni concreti | 0.209 | sì |
| 10 | Risonanza metallica prolungata | 0.208 | parziale (forse gong iniziale) |

**Problema CLAP grave**: i tag top-10 globali **non contengono prompt per "manifestazione politica", "slogan urbano", "corteo", "contestazione", "voci di strada militanti"**. Il brano più politicamente connotato del corpus (Parigi '68 + Venezia Biennale '68) è descritto da CLAP come "texture granulare densa + voce manipolata + preghiera + spiaggia mediterranea". **Gap catastrofico del vocabolario**: il lessico politico-urbano è assente.

### Tag CLAP segmentali notevoli

- `Motocicletta sportiva che accelera` (10:00-10:30), `Automobile che frena bruscamente` (10:00-10:30): **plausibile** (rumori di strada urbani).
- `Transizione dal silenzio notturno all'attività umana` (00:30-01:00, 11:00-11:30): irrilevante (non c'è silenzio notturno).
- `Voce amplificata con effetti elettronici`, `Feedback di microfono controllato`, `Accumulo granulare stocastico` presenti diffusamente: **corretti**, coprono la natura acusmatica del materiale.
- `Processione religiosa con canto` (06:50-07:00): allucinazione.
- `Synthetic singing` (07:30-08:00): potrebbe essere Aldini processata elettronicamente.

### Prompt CLAP mancanti

**Categoria "manifestazione urbana / soundscape politico"** completamente assente. Candidati da aggiungere:

- `Slogan di manifestazione politica in corteo`.
- `Cortina di voci da contestazione studentesca`.
- `Scritte murali di protesta declamate`.
- `Sciopero generale con cori di piazza`.
- `Megafono di manifestazione in ambiente urbano`.
- `Occupazione di spazio pubblico con voci militanti`.
- `Voce femminile elaborata su materiale politico` (specificità Nono/Aldini).
- `Rivoluzione sonora `68: slogan, grida, passi di corteo`.

Senza questi prompt, il brano più "politico" del corpus acusmatico è descritto genericamente come "voce manipolata + granulare + preghiera + spiaggia". Categoria **"contestazione/politica/strada/manifestazione"** è cieca del vocabolario attuale.

**Categoria "voci storiche di manifestazioni"**:

- `Registrazione d'archivio di manifestazione parigina anni '60`.
- `Piazza d'Italia con cori di contestazione`.
- `Manifestazione del Maggio francese `68`.

### Prompt CLAP da rivedere

- `Spiaggia mediterranea con onde leggere e voci distanti` (0.217): grave falso positivo. Su voci umane sovrapposte + rumore urbano continuo, matcha "voci distanti + onde leggere". Da plausibility-filtrare quando PANNs Speech > 0.50 E PANNs Ocean/Water < 0.03.
- `Preghiera collettiva sussurrata in chiesa`: **quinta occorrenza** nel corpus di questo falso positivo. Matcha su voci sovrapposte intime. Da plausibility-filtrare quando PANNs Choir/Chant < 0.02.

## 4. Hum check

- **Verdetto complessivo skill**: presente (+15 dB a 50 Hz vs baseline).
- **Reale**: **corretto**. Registrazione d'archivio 1969 su nastro magnetico RAI, il ronzio 50 Hz europeo è realistico e **parte della firma storica**. L'agente esplicitamente dice: "Hum 50/60 Hz presente su tutto il brano: testimonia sorgente analogica non filtrata, va valutato se conservarlo come patina storica o attenuarlo in mastering" + "Conservare il hum come elemento drammaturgico, non rimuoverlo: è firma di sorgente e parte della memoria sonora del brano." **Lettura esemplare** (in accordo con *La fabbrica illuminata*).
- Hint `likely_musical_harmonic` non è scattato (correttamente: PANNs Speech 0.76 dominante, non Music).

## 5. Mapping accademico

- **Krause**: antropofonia 54%, mista 36%, biofonia 4%, geofonia 3% → **corretto** per un brano di strada politico (antropofonia urbana).
- **Schafer**: sound-object + signal + soundmark → OK.
- **Schaeffer type**: tenuto 34%, trama 32% → coerente con materiale continuo (slogan + ambiente urbano + elettronica).
- **Smalley motion**: turbulence 32%, flow 29% → OK (flow delle voci + turbolenza urbana).
- **Schaeffer detail**: **cross-sintesi 70%** (high) → **valore massimo del corpus finora**. Ed è corretto: il brano è letteralmente cross-sintesi fra voci di strada + voci Aldini elaborate + campi elettronici. L'agente lo cita nella lettura: "gesto dominante è il time-stretch estremo del materiale concreto, con cross-sintesi (ipotesi Schaeffer TARTYP: cross-sintesi 70%) fra voce e fondo ambientale".
- **Smalley growth**: endogeny 41% (high) → coerente con crescita interna al materiale.
- **Chion**: ridotto + semantico → OK, tensione permanente fra decifrare i frammenti politici e abbandonarsi al grano.
- **Westerkamp soundwalk relevance**: non esplicitato, appropriato.

## 6. Lessico CLAP vs terminologia musicale

- `Voce umana manipolata acusmatica` → descrive l'elaborazione di Aldini. Riferimento teorico: Wishart (voci come oggetto plastico), Chion (acousmatic), Nono stesso (voci elaborate elettronicamente dal Nono *Scritti e colloqui*).
- `Time-stretch estremo di oggetto concreto` → tecnica documentata del brano. Termine preciso.
- `Cross-sintesi fra due suoni concreti` → categoria Schaefferiana pertinente.
- `Voce amplificata con effetti elettronici` → OK.
- Mancano termini per **discorso politico**, **slogan**, **militanza sonora** che sarebbero terminologicamente centrali (Nono stesso parla di "musica di strada").

## 7. Sezioni compositive

La skill ha rilevato 8 sezioni, tutte con signature "antropofonia moderata tonale" a parte S1 "sezione mista" iniziale. Struttura piatta e onesta: il brano è effettivamente **antropofonicamente omogeneo** per quasi la totalità (90%+ Speech frame). Manuale proposto:

| Sezione | Tempo | Evento | Note |
|---------|-------|--------|------|
| Soglia del gong | 00:00-00:40 | apertura sottovoce, oggetto risonante metallico | skill: colta ("Soglia del gong") |
| Prima emersione della voce | 00:40-02:00 | voce entra sfigurata, "Votre cœur cesse d'être" | skill: colta |
| Il grano del parlato | 02:00-06:30 | regime stabile, cross-sintesi 70% | skill: colta |
| Il fuoco della rivoluzione | 06:30-12:00 | slogan più espliciti "Plus je fais la révolution" | skill: **ottimamente colta** con nome evocativo |
| Picco antropico | 12:00-16:00 | dinamica si apre, onsets sopra 6/s, "Les uns sur les autres" | skill: colta |
| Dissolvenza | 16:00-18:03 | ritorno alla quiete | skill: colta |

Segmentazione automatica e narrativa agente convergono. Struttura "arco chiuso crepuscolare" (come dichiara l'agente).

## 8. Lettura compositiva

**Eccellente qualità narrativa**, con attribuzione stilistica **parzialmente errata**.

Passaggi forti:
- "Un lungo viaggio attraverso la materia vocale trasfigurata, diciotto minuti in cui la parola non viene mai pronunciata intera: affiora, si stira, si sgretola dentro una trama granulare che la tiene in ostaggio."
- "La lingua rilevata è il francese (probabilità 0.58, bassa), e i frammenti testuali affiorano come slogan semi-riconoscibili: 'Votre cœur cesse d'être, d'exister', 'Plus je fais la révolution', 'Enlâchez ton fils'. Sono detriti linguistici con un'aura politica che rimanda al **Sessantotto francese**, ma incastonati dentro una drammaturgia acusmatica che li dissolve in grana."
- "L'opera vive in questo attrito fra senso e materia: la parola vorrebbe parlare, il gesto compositivo la trattiene nello stato di oggetto."
- Scene evocative: "Soglia del gong", "Prima emersione della voce", "Il grano del parlato", "Il fuoco della rivoluzione" (bellissimo), "Picco antropico", "Dissolvenza".
- Binomi concettuali: parola/materia, rivoluzione/dissoluzione, soglia/plateau, modo semantico/modo ridotto.

**Riconoscimento politico corretto**: l'agente identifica il registro Maggio '68 dai frammenti whisper e lo incorpora nella lettura drammaturgica.

**Attribuzione stilistica errata**: l'agente propone:
- **"Territorio acusmatico francese, GRM come riferimento naturale"** → **errato**: il brano è italiano (Studio Fonologia RAI).
- **"Bernard Parmegiani e ... Luc Ferrari negli anni del post-Sessantotto"** → Parmegiani ok come parentela estetica generica; Ferrari invece è **vicino** (politica sonora esplicita nel suo lavoro), ma non identifica Nono.
- **"Poésie sonore di Henri Chopin e François Dufrêne"** → parentela corretta per il trattamento della parola come fonema, ma secondaria.

**Causa probabile dell'errore**: l'agente ha usato la lingua del parlato (francese) come proxy di scuola nazionale. Stesso errore inverso al suo: *Song of Songs I* (inglese) → non-Truax, *Non consumiamo Marx* (francese) → non-Fonologia RAI.

**Gold corretto**: **Studio di Fonologia RAI Milano** come scuola (come per *La fabbrica illuminata*), con influenze GRM/Ferrari per la politica sonora ma matrice tecnica e culturale italiana. Nono stesso partecipò attivamente al dibattito post-68 italiano (PCI, Althusser, '68 italiano).

**Criticità tecniche ben formulate**:
- LUFS integrato -21.1: coerente con target ridotto tipico materiali d'archivio.
- Hum 50 Hz come firma storica (raccomandazione di preservarlo, non rimuoverlo).
- Lo-Fi 2/5: dinamica compressa e rumore percepibile, coerente con materiale d'archivio.
- Lingua rilevata con bassa confidenza (0.58): segnalato come "possibile materiale multilingua o fortemente processato".

**Suggerimenti compositivi**: eccellenti:
- Acousmonium con spazializzazione separata di slogan (frontali) vs grano (perimetrale).
- Dittico con filmati situazionisti 1968 (Debord, Resnais, ORTF archivio).
- Remix che isola i 53 secondi di parlato identificato in un pezzo breve per radio.
- Laboratorio AFAM sul trattamento acusmatico del discorso politico (confronto Parmegiani/Chopin).
- Performance live con declamazione dal vivo in francese contemporaneo, doppio temporale rivoluzione dichiarata vs archiviata.
- Conservare il hum come elemento drammaturgico (raccomandazione **esatta**).

## 9. Note libere

### Positivi rilevanti per il paper

1. **Whisper su francese '68**: 9 frammenti trascritti e tradotti. Testo politico riconoscibile ("Plus je fais la révolution", "la haute s'étouffe"). Pipeline speech v0.5.0 funziona efficacemente su materiale multilingua d'archivio.
2. **PANNs urbano**: Speech 91% frame + Crowd + Outside urban + Narration + Vehicle + Run = contesto di manifestazione riconosciuto al 100%. Qui AudioSet training ha coperto bene il dominio.
3. **Hum come firma storica**: l'agente e la skill **non** trattano il hum come difetto ma come patina temporale. Contesto interpretativo corretto.
4. **Hi-Fi/Lo-Fi 2/5**: riconoscimento del materiale d'archivio.
5. **Schaeffer cross-sintesi 70%** massimo del corpus: categoria descrittiva perfetta per un brano basato sulla cross-sintesi voce-ambiente-elettronica.
6. **Lettura drammaturgica "Il fuoco della rivoluzione"** come nome evocativo di una sezione: esempio di trasformazione empirica (slogan "Plus je fais la révolution" + crescita dinamica) in titolo interpretativo.
7. **Suggerimento "conservare il hum"**: pedagogicamente forte, epistemologicamente corretto.

### Gap strutturali per il paper

1. **Bias lingua → geografia compositore**: caso scuola più grave del corpus. L'agente ha letto francese → GRM, sbagliando la scuola. Inversamente, in *Song of Songs I* (inglese) aveva letto non-Truax. Regola mancante: **la lingua del parlato non implica la nazionalità del compositore**.
2. **Fonologia RAI non identificata** nonostante le firme tecniche (hum analogico + Lo-Fi + voce manipolata anni '60-'70 + registrazioni di strada) che in *La fabbrica illuminata* avevano fatto convergere correttamente. Serve euristica: quando compaiono simultaneamente (a) nastro analogico (hum + Lo-Fi) + (b) voce manipolata + (c) registrazioni di strada/rumore urbano + (d) ambiente politico → considerare **Fonologia RAI** come ipotesi paritetica a GRM anche se lingua del parlato è francese.
3. **Vocabolario CLAP privo di dimensione politica/urbana/militante**: manifestazione, corteo, slogan, contestazione, Maggio '68, piazza politica sono assenti. Caso studio perfetto per il paper: un brano canonico della musica acusmatica politica (Nono) non è esprimibile dal vocabolario. **Urgente**: aggiungere categoria `soundscape politico/militante/urbano` al vocabolario v1.7.
4. **Allucinazione "Spiaggia mediterranea"** su manifestazione urbana: caso di voci sovrapposte + rumore di fondo letti come "spiaggia con onde + voci distanti". Da filtrare con plausibility quando PANNs Ocean/Water < 0.03.
5. **Trascrizione parziale**: 53s su 1082s = 4.9% del brano. Il resto del parlato non è riconoscibile per whisper perché troppo processato. **Ma i 53s riconoscibili sono sufficienti** a dare una traccia semantica decisiva all'agente. Esempio positivo di **"quantità minima di segnale semantico"**.
6. **Connessione multi-brano non possibile nella pipeline attuale**: *La fabbrica illuminata* e *Non consumiamo Marx* sono dello stesso autore (Nono), condividono scuola (Fonologia RAI) e tecnica (voci + materiali di strada + elettronica), ma la skill analizza ogni brano in isolamento. Feature futura (ROADMAP v0.9.0+): comparazione strutturale fra brani di un corpus.

### Patch candidate

**v0.6.6 (immediate)**:
- **Vocabolario CLAP v1.7**: categoria `manifestazione urbana / soundscape politico` (6-8 prompt) + categoria `registrazioni d'archivio di protesta politica`.
- Plausibility-filtrare `Spiaggia mediterranea con onde leggere e voci distanti` quando PANNs Water/Ocean < 0.03 E PANNs Speech > 0.50.
- Plausibility-filtrare `Preghiera collettiva sussurrata in chiesa` quando PANNs Choir/Chant < 0.02.

**Prompt agente v0.6.6**:
- Regola: **la lingua del parlato non implica la nazionalità del compositore**. Esempi documentati: *Song of Songs I* (inglese, Truax canadese), *Non consumiamo Marx* (francese, Nono italiano), *Thema (Omaggio a Joyce)* di Berio (inglese, italiano Fonologia RAI).
- Regola: se compaiono simultaneamente (a) hum analogico + Lo-Fi (firma nastro storico), (b) voce manipolata elettronicamente, (c) registrazioni di strada/rumore urbano, (d) materiale politico (slogan, cori di manifestazione, contestazioni), considerare **Studio di Fonologia RAI Milano** come scuola paritetica a GRM, anche se la lingua del parlato non è italiana.
- Regola: quando whisper rileva lingua con probability bassa (< 0.70), l'agente deve **marcare la localizzazione geografica come ipotesi**, non come fatto. Evitare frasi tipo "territorio acusmatico francese" se non corroborato da altri indicatori.

**v0.7.0 (plausibility check)**:
- Tag `soundscape marittimi/costieri` con PANNs Ocean/Water/Stream < 0.03 → plausibility `low`.
- Tag `religiosi/liturgici` con PANNs Choir/Chant/Religious music < 0.02 → plausibility `low`.

### Lezioni per il paper

- **Brano con trascrizione speech decisiva**: qui 53 secondi di parlato whisper hanno determinato la lettura drammaturgica. La pipeline speech trasforma una traccia ambientale opaca in documento politico decifrabile. **Effetto di amplificazione semantica**: piccole quantità di segnale parlato riconoscibile pesano molto nell'output agente.
- **Bias di attribuzione stilistica da lingua**: caso emblematico. Il paper deve discutere come l'agente LLM mediatore usi la lingua del parlato come proxy di scuola nazionale, con conseguenze errate sistematiche. Contromisure proposte nella sezione Patch.
- **Vocabolario CLAP bias culturale**: il vocabolario v1.6 copre bene paesaggi naturali + acusmatica classica + musica sacra + alcuni luoghi italiani. **Non copre** soundscape politici/urbani/militanti, che sono invece centrali per una porzione rilevante del repertorio acusmatico (Nono, Lachenmann, Ferrari politico, Stockhausen Hymnen, Reich Come Out). Gap sistemico da documentare.
- **Hum come firma temporale** (e non come artefatto): questa interpretazione emerge coerentemente su *Fabbrica illuminata* e *Non consumiamo Marx*. Il hint `likely_musical_harmonic` (per armoniche strumentali) v0.5.1 va esteso a `likely_archival_signature` quando contesto + Lo-Fi + parlato + hum 50 Hz → materiale d'archivio.
- **Endogeny + cross-sintesi**: le due categorie Smalley+Schaeffer (growth + TARTYP detail) emergono come **più descrittive** del brano rispetto a Krause/Schafer. Per il paper: discutere **rilevanza differenziale** delle tassonomie sul corpus (quale tassonomia è più discriminante su quale tipo di brano).
