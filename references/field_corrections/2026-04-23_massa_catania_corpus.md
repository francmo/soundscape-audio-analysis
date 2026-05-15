# Field corrections - Corpus viaggio Massa-Catania (20-21 aprile 2026)

## 1. Identificazione

- **Corpus**: 18 file `.m4a` iPhone 14 Plus, viaggio Francesco Mariano Massa > Catania, 20-21 aprile 2026
- **Cartella sorgente**: `~/Downloads/registrazioni audio viaggio massa catania 20 aprile 2026 iphone 14 plus/`
- **Versione skill che ha prodotto i report**: v0.12.4 (fallback ffmpeg per AAC)
- **Data feedback**: 2026-04-23
- **Modalita' di feedback**: iniziata come Modalita' A (testo libero in chat); promossa a Modalita' B (log strutturato) al sesto file per pattern consolidati
- **File ascoltati e annotati**: 11 su 18 (Reg 19, 20, 21, 22, 23, 24, 25, 26, 27, Massa Centro, Via della Fontanella, Via dei Rutuli, Roma Termini)

Timeline cronologica ricostruita dai metadati `creation_time` in `_timeline.md` nella cartella sorgente.

## 2. Scena reale vs scena letta dalla skill (per file annotato)

Elenco minimo: realta' percepita dall'utente, frase chiave che l'agent usa per inquadrare il brano, pattern attivati.

### Reg 19 (20/04 19:30, auto ferma davanti stazione Massa, 58 s)
- **Realta'**: conversazione in auto ferma con amico che ha accompagnato l'utente, sottofondo misto auto e stazione FS, dialoghi chiari
- **Agent**: "cinquantotto secondi di viaggio trattenuti dentro un abitacolo"; "Traversata (00:10-00:40)... il veicolo si fa piu' presente"
- **Pattern**: P2 movimento inventato; P3 CLAP off-target (nastro magnetico + sussurro intimo + ventilatore); P4 whisper hallucination su parlato chiaro; P5 Ferrari Presque Rien su 58 s di parlato in auto ferma

### Reg 20 (20/04 19:32, stessa scena del 19, 1:44)
- **Realta'**: continua conversazione in auto ferma davanti stazione
- **Agent**: "sospesi fra Massa e Catania"; partizione inventata "Partenza / Plateau del tragitto / Conversazione / Coda rumble"
- **Pattern**: P1 path leakage (filename generico, ma il toponimo Massa-Catania arriva dalla cartella parent); P2; P7 "preghiera collettiva sussurrata in chiesa"; P8 partitura formale inventata oltre i changepoint reali

### Massa Centro (20/04 20:51, treno AV appena partito da Massa, 2:31)
- **Realta'**: treno AV in corsa, dialogo col controllore e con addetta al carrello bar
- **Agent**: "Registrazione iPhone nel centro di Massa"; "traffico di una citta' di provincia"; "passaggio del veicolo... un'auto vicina al microfono"; CLAP "treno ad alta velocita'" scartato come "metafora, non referente"
- **Pattern**: P1 filename leakage (caso didattico); P6 override di CLAP-treno corretto; P2 frame piazza urbana; P15 controllore non riconosciuto

### Via della Fontanella (20/04 21:50, treno in corsa con galleria e dialogo barista, 2:26)
- **Realta'**: treno in corsa; ~43 s ingresso in galleria (cambio scena netto); 1:06-1:20 dialogo col barista di bordo; poi rientro al posto attraversando piu' vagoni (passi)
- **Agent**: riconosce che il filename "non trova riscontro empirico" (piccolo progresso), ma sceglie "monolite di rumore motoristico colto da dentro il proprio perimetro"; "Plateau del veicolo... il tag CLAP 'Treno ad alta velocita'' sale, ma resta interpretazione ferroviaria di un motore di cabotaggio"; "vento sul diaframma" (probabile galleria o passi fra vagoni); "Coda sulla risacca... PANNs Boat 0.37"
- **Pattern**: P6 (secondo override consecutivo di CLAP-treno); P10 PANNs Boat allucinato su treno; P9 dialogo barista mascherato in "plateau"; P11 galleria non rilevata come changepoint; P8 partitura inventata

### Reg 21 (20/04 23:04, treno in fermata Roma Termini con annunci PA e manipolazione bagagli, 5:32)
- **Realta'**: a Roma Termini. Annuncio PA "treno in transito, allontanarsi dalla linea gialla", voci folla stazione, treni, da 1:45 cerniere dei propri bagagli che si chiudono
- **Agent**: "tratta ferroviaria e uno sbarco in ambiente urbano"; "Viaggio a finestrino aperto (01:00-03:00)... brevi firme di aeromobile"; "Piazza all'arrivo"; CLAP "Piazza urbana centroeuropea", "Granulazione densa di voce umana"
- **Pattern**: P1; P2 "finestrino aperto", "aeromobile" (inesistenti); P12 cerniere bagagli lette come "accartocciare 0.43" (CLAP coglie la natura di gesto ravvicinato ma manca prompt specifico); P13 voce PA non riconosciuta, "Voce umana manipolata acusmatica 0.23"; P14 annuncio PA non isolato come soundmark

### Roma Termini (20/04 23:24, treno Intercity Notte fermo al binario, con controllore, 4:54)
- **Realta'**: dentro carrozza IC Notte fermo a Termini. Controllore che chiede dove scendono i passeggeri e se vogliono la sveglia. Treno in preparazione, non in movimento
- **Agent**: "field recording... registrato nell'atrio della stazione Termini di Roma, documento di passaggio dentro una delle cattedrali laiche del viaggio italiano contemporaneo"; "Piccioni dentro la cattedrale laica (02:30-03:30)... PANNs Pigeon 0.71"; "Partenza del veicolo (04:30-04:53)"
- **Pattern**: P1 caso estremo (filename scrive tutta la lettura); P10 PANNs Pigeon hallucination grave (nessun piccione in carrozza); P3 CLAP "Bar con macchina del caffe' e chiacchiere", "Discussione di vicini dalle finestre", "Acqua del rubinetto che scorre"; P7 "preghiera sussurrata in chiesa"; P13 "larsen da PA" inventato; P15 controllore non riconosciuto

### Reg 22 (20/04 23:57, treno IC Notte in corsa con dialogo controllore-signora, 1:10)
- **Realta'**: treno in movimento, dialogo controllore con signora decifrabile
- **Agent**: "Settantuno secondi di viaggio colti dall'interno di un abitacolo in movimento" (movimento corretto); "i marker italo-specifici proposti da CLAP ('Treno regionale', 'Discussione di vicini') vanno trattati come proiezioni"; finale "cambio di marcia, passaggio, strappo di velocita'"; "l'interlocuzione interna al mezzo prende corpo"
- **Pattern**: P6 downgrade raffinato (treno CLAP accettato come "mezzo su ruote" generico); P2 lessico automobilistico ("cambio di marcia") su treno; P15 dialogo controllore-signora come "interlocuzione"; P1 path ("Massa-Catania come arco narrativo" nei suggerimenti)

### Via dei Rutuli (21/04 00:00, treno IC Notte in corsa con dialogo controllore per biglietto/documento/colazione, 1:44)
- **Realta'**: treno in corsa, voci ben definite, controllore chiede biglietto, documento, colazione
- **Agent**: "Un microritratto di strada: registrati in Via dei Rutuli, dove il respiro di un motore in folle e le voci dei passanti"; "Il tag CLAP 'Treno regionale' e' fuorviante... si legga come rumble urbano continuo"; "Schafer: soundmark stradale in registro Lo-Fi"; dialogo controllore-viaggiatore > "frammenti di conversazione non processati"
- **Pattern**: P1 didattico (filename stradale romano > scena stradale inventata); **P6 in forma esplicita: l'agent rigetta il CLAP-treno chiamandolo "fuorviante"**; P2; P15
- **Caso piu' chiaro del combinato P1 + P6 dell'intero corpus**

### Reg 23 (21/04 00:23, treno in corsa con pattern ritmico in sottofondo, 1:22)
- **Realta'**: treno in movimento, niente di particolarmente rilevante, pattern ritmico (presumibilmente giunti rotaia)
- **Agent**: "dentro il ventre di un veicolo in movimento"; CLAP "Neve che cade in ambiente silenzioso" 0.29 top-1; "Motore di peschereccio diesel"; "CLAP 'Treno regionale' raggiunge 0.40 (plausibility medium, qualche supporto PANNs 'Train' 0.08). Possibile passaggio su tratto ferrato"; parentele Cusack + Chris Watson (panel appropriato)
- **Pattern**: **P6 al massimo grado: CLAP 0.40 + PANNs Train confermato > "possibile tratto ferrato"** (non "e' un treno"); P10 nuovo falso positivo "Neve che cade"; P17 PANNs Vehicle generico sovrascrive Train specifico; P18 pattern ritmico periodico non riconosciuto; P5 assente su drone puro (panel adattato correttamente)

### Reg 24 (21/04 00:52, simile al 23 piu' presente, forse galleria, 0:41)
- **Realta'**: come 23 ma piu' presente (galleria o maggiore velocita')
- **Agent**: "fragment di documento di trasferimento... viaggio da Massa a Catania il 20 aprile 2026"; "tratta autostradale italiana"; "motore d'automobile come tonica inconsapevole"; suggerisce "voce narrante che legge in tempo reale i toponimi attraversati (Massa, Lucca, Firenze, Roma, Napoli, Salerno, Villa San Giovanni, Messina, Catania)"
- **Pattern**: **P1 al massimo: l'agent inventa l'intero itinerario geografico** (toponimi dedotti dal folder name + durata); P2 "automobile" invece di treno; P10 "Motore di peschereccio diesel" 0.33 top-1

### Reg 25 (21/04 08:37, mattina, treno fermo sul traghetto, 0:52)
- **Realta'**: **treno fermo sul traghetto**. Rumori interno cabina
- **Agent**: "dentro un mezzo in movimento"; "Attraversamenti (00:30-00:51)... qualcosa che PANNs confonde con 'Boat, Water vehicle' e 'Train'"
- **Pattern**: **P19 nuovo e critico: nave/traghetto/porto categoria assente**; P6 invertito pericoloso: PANNs Boat e Water vehicle **erano corretti** (traghetto reale), l'agent li scarta come "confusione" perche' incoerenti col frame "treno"; P10 "Generatore di sinusoidi a frequenza pura" 0.25 (hum motore > sinusoide pura)

### Reg 26 (21/04 08:43, traghetto + dialogo controllore + PA "la nave sta lasciando il porto", 7:29)
- **Realta'**: ancora sul traghetto. Da 4:45 dialogo chiaro col controllore. A 6:23 altoparlante annuncia "la nave sta lasciando il porto"
- **Agent**: "viaggio in presa diretta che attraversa l'Italia... il brano si apre con l'ingresso di un treno"; "Strada in citta', veicoli in primo piano (03:00-04:00)... come un finestrino aperto su una tangenziale"; "Falsa biofonia (04:00-04:30) PANNs segnala Sheep a 0.52... annuncio megafonico che AudioSet assimila al belato"; sezione 04:30-06:00 (dialogo controllore su traghetto) > CLAP "Voci di mercato in dialetto locale" e "Occupazione di spazio pubblico con voci militanti"; finale "Stazione terminale, brusio della folla... ingresso in treno, uscita in stazione"
- **Pattern**: P1 completo (Toscana > Sicilia, stazione terminale); P19 traghetto mai nominato; P10 PANNs Sheep (probabilmente voce PA "la nave sta lasciando il porto"); P13 dialogo controllore > "mercato dialettale" + "voci militanti" (falso positivo grave); P14 annuncio PA non isolato; P2 "finestrino aperto su tangenziale"

### Reg 27 (21/04 09:11, entrata in porto con annuncio PA bilingue italiano/inglese, 3:40)
- **Realta'**: ingresso in porto, altoparlante chiaro e pulito bilingue italiano/inglese
- **Agent**: "treno... presumibilmente un treno della tratta tirrenico-ionica"; "cio' che sembra un annuncio diffuso dall'impianto interno" (piccolo progresso: categoria PA riconosciuta come astratta); "coda dell'abbandono S3... singhiozzo umano (PANNs Hiccup 0.66)"
- **Pattern**: P19 porto mai nominato; P14 mitigato (PA riconosciuto come categoria ma contesto sbagliato: "impianto vagone" invece di PA nave); **P20 nuovo: bilinguismo IT/EN non riconosciuto, inglese mai menzionato**; P10 PANNs Hiccup 0.66 (probabile inglese parlato classificato come singhiozzo)

## 3. Indice pattern consolidati

Numerazione progressiva assegnata durante l'ascolto. Frequenza riferita agli 11 file annotati.

### P1 - Filename / path leakage
- **Descrizione**: il nome del file e/o della cartella parent (`registrazioni audio viaggio massa catania 20 aprile 2026 iphone 14 plus`) entra nel contesto dell'agent e genera inferenze di scena, luogo, itinerario non supportate dal contenuto audio
- **Frequenza**: 8/11 file (escluso Reg 19 dove il file name era generico e non c'era ancora abbastanza segnale path)
- **Gravita'**: alta
- **Casi esemplari**:
  - Massa Centro: filename "Massa Centro" > "registrazione nel centro di Massa" con piazza e traffico stradale
  - Roma Termini: filename "Roma Termini" > "atrio della stazione Termini, cattedrale laica"
  - Via dei Rutuli: filename toponimo stradale romano > "microritratto di strada... motore in folle... passanti"
  - Reg 24: folder name "viaggio massa catania" > itinerario completo Toscana-Sicilia inventato con toponimi
  - Reg 20: filename generico, ma "sospesi fra Massa e Catania" viene dal folder
- **Varianti**: (a) basename con toponimo > scena urbana stradale; (b) path parent con arco narrativo > itinerario geografico inventato; (c) filename con stazione > spazio architettonico monumentale

### P2 - Frame "movimento / motore stradale" applicato indebitamente
- **Descrizione**: hum di rete o di impianto, bande basse sature, parlato + rumore continuo, vengono letti come "veicolo stradale in movimento" anche quando: la scena e' statica (auto ferma, treno fermo), oppure il veicolo e' di tipo diverso (treno AV, traghetto)
- **Frequenza**: 7/11
- **Gravita'**: alta
- **Casi esemplari**: Reg 19-20 (auto ferma > "abitacolo in movimento"); Massa Centro (treno AV > "passaggio di un'auto"); Via dei Rutuli (treno IC Notte > "motore in folle stradale"); Reg 26 (traghetto > "finestrino aperto su tangenziale"); Reg 22 (treno > "cambio di marcia" lessico automobilistico)

### P3 - CLAP top dominato da tag "qualita' registrazione" o off-target
- **Descrizione**: la top-3 CLAP di quasi tutti i file contiene uno o piu' prompt che descrivono la qualita' della registrazione invece del contenuto, oppure prompt vistosamente falsi positivi su broadband low o parlato riverberato
- **Frequenza**: 11/11
- **Gravita'**: alta
- **Prompt ricorrenti problematici**:
  - "Nastro magnetico storico con rumore di fondo" (quasi sempre in top-3, su qualsiasi registrazione Lo-Fi)
  - "Ventilatore che gira" (scatta su qualsiasi basso continuo)
  - "Sussurro intimo non intelligibile" (scatta su parlato a basso volume in ambiente rumoroso > P4)
  - "Preghiera collettiva sussurrata in chiesa" (scatta su parlato + basso continuo o riverbero > P7)
  - "Acqua del rubinetto che scorre" (scatta su broadband low)
  - "Bar con macchina del caffe' e chiacchiere" (scatta su voci + rumore continuo)
  - "Discussione di vicini dalle finestre" (scatta su voci in ambiente chiuso)
  - "Neve che cade in ambiente silenzioso" (scatta su drone veicolare, nuovo in Reg 23)
  - "Motore di peschereccio diesel di piccolo cabotaggio" (scatta su motori terrestri)
  - "Generatore di sinusoidi a frequenza pura" (scatta su hum motore)
- **Il flag `italian_context.is_italian_context` esiste gia'** (v0.5.2) e degrada correttamente alcuni prompt italo-specifici (es. "acqua del rubinetto" con plausibility low in Reg 23). Non e' pero' sufficiente: molti prompt qui sopra non sono italo-specifici e continuano a dominare la top-3

### P4 - Whisper / sussurro hallucination su parlato chiaro
- **Descrizione**: parlato chiaro e decifrabile in ambiente rumoroso viene classificato come "sussurro intimo non intelligibile"
- **Frequenza**: 2/11 (Reg 19, Reg 20)
- **Gravita'**: media

### P5 - Tris canonico Ferrari + Cusack + Schafer + Westerkamp (condizionale)
- **Descrizione**: nelle Parentele stilistiche compaiono quasi sempre gli stessi 3-4 compositori/scuole
- **Frequenza**: 8/11
- **Gravita'**: media
- **Osservazione importante**: il pattern e' **condizionale**. Scatta quando il materiale contiene **voce + drone**. Nei file drone-puro (Reg 23, Via della Fontanella) il panel cambia correttamente (Koner, Nilsen, Lopez, Chris Watson, Smalley). Quindi il problema non e' il panel in se', e' la sua **attivazione automatica su scene miste**

### P6 - Override o downgrade di tag CLAP / PANNs corretti
- **Descrizione**: l'agent, una volta scelto un frame interpretativo, rigetta o svuota di specificita' le etichette dei classificatori anche quando sono corrette. Include due varianti: (a) override (dice "il tag e' sbagliato, nonostante il classificatore"), (b) downgrade (accetta il tag ma lo generalizza, es. "treno" > "mezzo su ruote", "treno AV" > "motore di cabotaggio")
- **Frequenza**: 7/11
- **Gravita'**: alta
- **Casi chiave**:
  - Massa Centro: CLAP "treno ad alta velocita'" > "metafora, non referente: qui e' un'auto vicina al microfono"
  - Via della Fontanella: CLAP "Treno AV" > "interpretazione ferroviaria di un motore di cabotaggio"
  - Via dei Rutuli: CLAP "Treno regionale" > "fuorviante, si legga come rumble urbano continuo"
  - **Reg 23**: CLAP "Treno regionale" 0.40 + PANNs Train 0.08 > "possibile passaggio su tratto ferrato" (il treno c'e' ma resta sempre ipotesi)
  - **Reg 25 invertito**: PANNs Boat + Water vehicle **corretti** (su traghetto reale) > scartati come "confusione"
- **Nota**: P6 e' probabilmente il pattern piu' pericoloso per la qualita' dell'analisi perche' vanifica il lavoro dei classificatori

### P7 - Falso positivo "preghiera collettiva sussurrata in chiesa"
- **Descrizione**: prompt CLAP della categoria "sacralita' sonora" che si attiva sistematicamente su parlato a basso volume con basso continuo o riverbero, in contesti evidentemente profani
- **Frequenza**: 2/11 (Reg 20, Roma Termini)
- **Gravita'**: media
- **Raccomandazione**: rivedere o deprioritizzare

### P8 - Partitura formale inventata oltre i changepoint detection
- **Descrizione**: l'agent dichiara 4-5 sezioni formali nella Lettura compositiva quando la changepoint detection ne ha identificate 2. Le sezioni inventate sono costruzioni narrative coerenti col frame scelto, non con il materiale
- **Frequenza**: 3/11 (Reg 20, Via della Fontanella, in parte Reg 21)
- **Gravita'**: media
- **Caso opposto**: Reg 21 (Roma Termini stazione) e Reg 26 seguono piu' fedelmente i 4-6 changepoint reali, quando la changepoint detection e' ricca

### P9 - Dialoghi brevi in ambiente rumoroso mascherati dal frame dominante
- **Descrizione**: dialoghi decifrabili ma di breve durata dentro un ambiente sonoro continuo vengono dissolti dall'agent in "plateau", "tenuto", "brusio" invece che identificati come eventi discreti
- **Frequenza**: 1/11 esplicito (Via della Fontanella: dialogo barista 1:06-1:20 mascherato come "Plateau del veicolo")
- **Gravita'**: media

### P10 - PANNs hallucination di classi specifiche
- **Descrizione**: PANNs CNN14 produce score alti su classi AudioSet specifiche su materiale fuori distribuzione (OOD). L'agent le recepisce e costruisce sezioni drammaturgiche su di esse
- **Frequenza**: 4/11
- **Casi documentati**:
  - Via della Fontanella: **Boat 0.37** su treno AV (broadband low > diesel marino)
  - Roma Termini: **Pigeon 0.71** su interno carrozza IC Notte
  - Reg 26: **Sheep 0.52** su (probabile) voce PA "la nave sta lasciando il porto"
  - Reg 27: **Hiccup 0.66** su (probabile) inglese dell'annuncio bilingue
- **Osservazione critica**: Reg 25 mostra il caso opposto, PANNs Boat e Water vehicle **corretti** su traghetto reale ma scartati dall'agent. Quindi il problema non e' "PANNs sbaglia sempre" ma "l'agent non sa distinguere PANNs corretto da PANNs sbagliato senza evidenza contestuale"

### P11 - Cambio scena (galleria) non registrato come changepoint
- **Descrizione**: cambio acustico netto udibile all'ascolto (ingresso in galleria, cambio di ambiente) non viene identificato dalla changepoint detection
- **Frequenza**: 1/11 (Via della Fontanella ~43 s)
- **Gravita'**: bassa-media
- **Osservazione**: la changepoint detection lavora su gradiente RMS + centroide + flatness + categorie dominanti. Potrebbe non pesare abbastanza i transitori di pressione acustica (compressione/rarefazione in galleria)

### P12 - Foley bagagli / gesti ravvicinati non nel vocabolario
- **Descrizione**: cerniere di zaino/valigia, manipolazione bagagli, gesti foley ravvicinati al microfono vengono etichettati con prompt adiacenti ma imprecisi
- **Frequenza**: 1/11 (Reg 21: cerniere > CLAP "accartocciare 0.43")
- **Gravita'**: bassa
- **Osservazione positiva**: il CLAP coglie la natura di "gesto ravvicinato", sbaglia solo l'oggetto. Aggiungendo prompt specifici si puo' correggere

### P13 - Voce da altoparlante / PA pubblica > "voce manipolata acusmatica" o "voci militanti / mercato"
- **Descrizione**: voce amplificata da sistema PA (stazione, nave, annuncio pubblico) viene classificata come manipolazione acusmatica intenzionale, o come contesto politico/mercato
- **Frequenza**: 3/11 (Reg 21 Roma Termini "Voce umana manipolata acusmatica" + "microfoni con larsen"; Reg 26 "Voci di mercato in dialetto locale" e "Occupazione di spazio pubblico con voci militanti" su dialogo controllore su traghetto)
- **Gravita'**: media
- **Causa**: il CLAP confonde la distorsione del canale PA con gesto compositivo di manipolazione elettronica. Categoria categoriale opposta

### P14 - Annuncio PA non isolato come soundmark
- **Descrizione**: un annuncio PA chiaro e comprensibile ("treno in transito, allontanarsi dalla linea gialla", "la nave sta lasciando il porto") non viene isolato come evento significativo. Viene dissolto in "signal vocale degli annunci" o non menzionato
- **Frequenza**: 1/11 esplicito (Reg 21)
- **Mitigato**: Reg 27 lo riconosce come categoria ma nel contesto sbagliato ("impianto vagone" invece di nave)

### P15 - Ruoli vocali funzionali non riconosciuti
- **Descrizione**: figure con ruolo funzionale nel contesto (controllore del treno, barista di bordo, addetto al carrello bar, personale di terra) e con atti linguistici tipici (chiedere biglietto, chiedere dove scendere, offrire sveglia o colazione) vengono appiattite a "voci", "parlato", "interlocuzione"
- **Frequenza**: 6/11 (Massa Centro, Reg 21, Roma Termini, Reg 22, Via dei Rutuli, Reg 26)
- **Gravita'**: alta
- **Causa**: vocabolario CLAP privo di prompt relativi a ruoli ferroviari o marittimi italiani (controllore, capotreno, personale di bordo, annuncio di servizio)

### P16 - "Neve che cade in ambiente silenzioso" falso positivo su drone veicolare
- **Descrizione**: prompt CLAP che si attiva sul combinato di basso continuo + ventilazione alta
- **Frequenza**: 1/11 (Reg 23 top-1)
- **Gravita'**: media
- **Raccomandazione**: deprioritizzare o rivedere

### P17 - PANNs Vehicle generico sovrascrive Train specifico
- **Descrizione**: la gerarchia AudioSet ha Vehicle come padre di Rail transport / Train. CNN14 tende a scoring alto sul padre, l'agent ignora il figlio
- **Frequenza**: 1/11 esplicito (Reg 23: Vehicle 0.58 + Train 0.08 > "documento resta un'antropofonia meccanica senza ambiguita'")
- **Gravita'**: media

### P18 - Pattern ritmico periodico non riconosciuto come ritmo
- **Descrizione**: regolarita' ritmica udibile (giunti rotaia, pattern metrico) non viene qualificata come "ritmo" dalla narrativa. Onset density restituisce un numero, non la periodicita'
- **Frequenza**: 1/11 (Reg 23)
- **Gravita'**: bassa
- **Capacita' mancante**: detection di periodicita' nella onset train

### P19 - Nave, traghetto, porto: categoria assente dal vocabolario
- **Descrizione**: l'intero contesto marittimo (traghetto FS ferroviario, navigazione, ingresso in porto, imbarco e sbarco) non ha rappresentanza nel vocabolario CLAP italiano. Anche quando PANNs dice Boat correttamente, l'agent non dispone di prompt CLAP che confermino, e rigetta
- **Frequenza**: 3/11 (Reg 25, 26, 27)
- **Gravita'**: alta
- **Raccomandazione**: aggiungere famiglia "contesto marittimo" con prompt dedicati

### P20 - Bilinguismo IT/EN negli annunci non riconosciuto
- **Descrizione**: annuncio PA in italiano + inglese > l'inglese non viene menzionato ne' riconosciuto come lingua. Puo' generare hallucination PANNs (Hiccup 0.66 in Reg 27)
- **Frequenza**: 1/11 (Reg 27)
- **Gravita'**: media

## 4. Proposte di patch

Ordinate per rapporto impatto/costo.

### Patch 1 - Anti-filename/path leakage (alta priorita')

**Target**: P1, componente P6 legata al filename-driven frame

**Interventi**:
1. Modifica `scripts/agent_bridge.py` o del punto dove si costruisce il payload dell'agent: rimuovere filename e folder name dal contesto narrativo passato all'agent. Tenerli in un campo metadato separato `file_label` con caveat esplicito
2. Modifica a `templates/agent_prompt.md`: aggiungere sezione "Regole interpretative" con istruzione non negoziabile

   > Il nome del file e della cartella parent possono contenere etichette arbitrarie, toponimi, o informazioni contestuali su un corpus piu' ampio. Tratta filename e folder name come metadati amministrativi, non come evidenze di scena. Non dedurre luogo, itinerario, evento, tipo di spazio, o situazione dal filename. Costruisci l'interpretazione esclusivamente a partire da: tag CLAP, top PANNs, profilo spettrale, indici ecoacustici, narrativa segmentata 30 s. Se un toponimo compare nel filename, non menzionarlo nella lettura drammaturgica, nelle scene sonore, nei binomi o nei suggerimenti, salvo sia esplicitamente confermato dai classificatori.

3. Test di regressione: rilanciare l'analyze su Via dei Rutuli e Roma Termini e verificare che la Lettura compositiva non contenga piu' "Via dei Rutuli", "atrio della stazione Termini", toponimi inventati

### Patch 2 - Anti-override classificatori (alta priorita')

**Target**: P6

**Interventi**:
1. Prompt agent, nuova sezione "Come trattare i tag CLAP e PANNs":
   > Quando CLAP restituisce un tag con score >= 0.30 e PANNs restituisce una classe coerente con score >= 0.05, considera la categoria come ipotesi di lavoro forte. Se intendi rigettarla, devi motivare con evidenza spettrale o ecoacustica (centroide, flatness, bande Schafer, hum, onset density), non con ipotesi di scena costruite a priori. In particolare: non sostituire un tag di categoria specifica (es. "treno regionale", "treno ad alta velocita'", "traghetto") con una formulazione piu' generica (es. "veicolo", "mezzo su ruote", "rumble urbano"). La specificita' di un tag CLAP e' informazione, non rumore.
2. Regola speciale per trasporti: lista bianca di categorie CLAP che l'agent non deve downgradare: treno AV, treno regionale, metropolitana, tram, traghetto, stazione ferroviaria, porto, aereo, automobile
3. Test di regressione: Via dei Rutuli, Reg 23, Reg 25 (casi P6 puri documentati)

### Patch 3 - Vocabolario CLAP: aggiunte e revisioni (alta priorita')

**Target**: P3, P13, P14, P15, P19, P20, P12

**Aggiunte proposte** (`references/clap_vocabulary_it.json`):

Famiglia "trasporto pubblico - figure professionali":
- "controllore del treno che chiede biglietto"
- "controllore che chiede documento di identita'"
- "capotreno che annuncia stazione"
- "addetto al carrello bar che offre prodotti"
- "barista di bordo treno"
- "personale di servizio ferroviario"

Famiglia "annunci pubblici":
- "annuncio da altoparlante di stazione ferroviaria"
- "annuncio di sicurezza in stazione (linea gialla)"
- "annuncio in italiano da altoparlante di nave"
- "annuncio bilingue italiano inglese da altoparlante"
- "voce amplificata da sistema PA in ambiente pubblico"

Famiglia "contesto marittimo - nuova":
- "treno a bordo di traghetto ferroviario"
- "interno di nave in navigazione"
- "nave che manovra in porto"
- "ingresso di traghetto in porto"
- "sbarco passeggeri da traghetto"
- "motore diesel di nave in porto"

Famiglia "foley bagagli":
- "cerniera di zaino che si chiude"
- "cerniera di valigia"
- "manipolazione di bagaglio al microfono"

Famiglia "ferrovia - eventi":
- "transito su scambio ferroviario"
- "ingresso di treno in galleria"
- "passaggio di treno in galleria"

**Revisioni/deprioritizzazioni proposte**:

- "Nastro magnetico storico con rumore di fondo": confinare alla categoria "qualita' di registrazione" con flag che la escluda dalle top-3 della Sintesi (o rendere esplicito nel PDF che e' qualita', non contenuto)
- "Preghiera collettiva sussurrata in chiesa" (P7): abbassare il peso, o aggiungere plausibility check basato su riverbero effettivo stimato
- "Discussione di vicini dalle finestre", "Bar con macchina del caffe' e chiacchiere": richiedono verifica che l'`italian_context.is_italian_context` sia True oltre a una soglia minima
- "Neve che cade in ambiente silenzioso" (P16): aggiungere plausibility check su banda alta (se Presence e Brilliance totali < 0.5% dell'energia, non puo' essere neve)
- "Motore di peschereccio diesel", "Barca in porto": richiedono plausibility geografica (coerenza con tag marittimi di contesto, altrimenti penalizzazione)

### Patch 4 - Meta-regole di frame (media priorita')

**Target**: P2, P8, P11, P18

**Interventi**:
1. Prompt agent, regola anti-frame-fissato:
   > Non applicare un frame ambientale ("auto in movimento", "citta' in transito", "atrio monumentale") a scene che hanno durata inferiore a 30 s: limitati a descrivere cio' che e' effettivamente presente senza ricostruire un contesto di spazio/tempo piu' ampio.
2. Regola anti-partitura-inventata:
   > Il numero di sezioni della Lettura compositiva deve coincidere con il numero di changepoint identificati +/- 1. Non inventare sezioni intermedie chiamandole "Plateau", "Coda", "Apertura" se non corrispondono a una transizione misurata.
3. Miglioramento changepoint detection (codice, non prompt): aggiungere feature "reverb proxy" o "pressione acustica" per catturare cambi di ambiente (galleria, indoor/outdoor) non sempre visibili in RMS+centroide

### Patch 5 - Tris canonico condizionale (bassa priorita')

**Target**: P5

**Intervento**: non necessario intervenire aggressivamente. Il panel stilistico funziona gia' dinamicamente (drone puro > Koner/Lopez/Watson; voce+drone > Ferrari/Cusack/Schafer/Westerkamp). Raccomandazione minore:
- nel prompt, istruire l'agent a scegliere 2 parentele massimo (non 4) e a motivarle ognuna con un elemento specifico del materiale, non solo con il tipo di scena

## 5. Criteri di validazione delle patch

Per non ricadere nel noise floor stocastico gia' documentato in ROADMAP.md (Piano v0.13):
- Ogni patch proposta qui va validata sulle stesse 11 registrazioni annotate, con N >= 3 run per file
- Metrica: conteggio manuale delle occorrenze di ciascun pattern P1-P20 nei report v0.12.4 vs report post-patch
- Significativita': accettare la patch solo se la riduzione di occorrenze di almeno un pattern target e' statisticamente significativa (paired test, p < 0.05)
- Candidato a test della Patch 1 (filename leakage): Via dei Rutuli, Roma Termini, Reg 24. Aspettativa: toponimi inventati > 0 nel post-patch

## 6. Note di governance

- Questo file e' il primo field_corrections del corpus. Istituisce la cartella `references/field_corrections/` come parallelo a `references/user_feedback/` (che resta riservata ai gold di repertorio accademico).
- Non modificare retroattivamente: se un pattern viene risolto o si rivela spurio, creare una nota in coda con data.
- Questo documento non sostituisce i singoli report PDF: e' la loro lettura trasversale. I summary.json e agent_payload.json originali restano l'evidenza primaria.
