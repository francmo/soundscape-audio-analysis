# Lezioni apprese

Questo documento riassume le lezioni critiche derivate dall'esperienza di analisi
del corpus Villa Ficana (14 aprile 2026). Ogni lezione è codificata nell'implementazione
della skill.

## 1. Hum check con baseline locale, non globale

**Problema iniziale.** Nel toolkit originale `~/audio-analyzer/analyze.py`, il confronto
tra i picchi a 50/60 Hz e lo spettro avveniva rispetto alla **media globale** dello
spettro intero. Questo produceva falsi positivi su sorgenti tonali (es. drone di
frequenza bassa reale nel contenuto), perché il rapporto picco/media risultava alto
anche in assenza di ronzio elettrico.

**Soluzione canonica.** Baseline calcolata come mediana dei bin FFT nelle bande
**30-45 Hz** e **70-95 Hz**, deliberatamente lontane da 50/60/100/120/150/180 Hz.
FFT ad alta risoluzione (n_fft = 16384 a 8 kHz, cioè 0.5 Hz/bin). Il picco viene
cercato entro ±2 Hz del target.

**Dove è implementato.** `scripts/hum.py::hum_check`. La versione con baseline globale
è esplicitamente scartata e non viene riportata altrove nel codice.

**Come verificarlo.** Il test `tests/test_hum.py::test_pink_noise_no_false_positive`
esegue il check su rumore rosa (nessun hum) e verifica che tutti i verdetti siano
`trascurabile`.

## 2. Pre-check LUFS prima della classificazione semantica YAMNet

**Problema iniziale.** Il file Villa Ficana MP3 da 67 minuti, renderizzato a -60.4 LUFS,
è stato classificato da YAMNet come `Silence` al **97,9%**. I pochi frame non-Silence
ritornavano categorie sparse e poco significative (`Mechanical fan`, `Microwave`,
`Vehicle`). Il toolkit originale inviava la waveform grezza al modello senza alcun
controllo di livello.

**Causa.** YAMNet è addestrato su AudioSet, un corpus dove i clip sono normalizzati
a livelli tipici broadcast. Quando il segnale è 35-40 dB sotto il livello atteso, la
rete produce attivazioni molto basse e la classe `Silence` (la più rappresentata
nell'assenza di segnale) vince statisticamente.

**Soluzione canonica.** Prima di invocare YAMNet:

1. Calcola l'integrated LUFS del file (via `ffmpeg ebur128`).
2. Se il LUFS è sotto la soglia `LUFS_SEMANTIC_PRECHECK = -45.0`:
   a. Calcola `gain_db = -23.0 - lufs` (porta il materiale verso lo standard broadcast).
   b. Applica il gain **in memoria**, sulla waveform 16 kHz mono passata al modello.
   c. Non modificare il file su disco.
3. Annota `precheck.requires_normalization=True` e `precheck.gain_db=...` nel summary.
4. Il report PDF riporta l'avvenuta normalizzazione con un box di avviso in italiano.

**Dove è implementato.** `scripts/semantic.py::precheck_loudness` + `prepare_waveform`.

**Come verificarlo.** `tests/test_semantic_precheck.py` costruisce un file a -60 LUFS
e verifica che:
- `precheck.requires_normalization` sia `True`.
- `precheck.gain_db` sia vicino a +37 dB.
- La classificazione top-1 dopo il pre-check non sia `Silence`.

## 3. Il pre-check non sostituisce il problema di sorgente

Se il pre-check si attiva, la skill lo dichiara chiaramente nel report ma non risolve
il problema **a monte**. Un file registrato con livello d'ingresso troppo basso ha
catturato il self-noise del preamp con piena energia, e questo non si recupera in post.
Il report contiene questa avvertenza nella sezione "Criticità tecniche" (l'agente
compositivo ne è istruito), così il committente è informato della necessità di rifare
la registrazione alla sorgente, non di ritoccare il file.

## 4. Multicanale: analisi per canale, non solo downmix

Il toolkit originale ha analizzato i due render 7.1.4 dell'Ecomuseo come downmix stereo,
perdendo l'informazione spaziale. La nuova skill esegue l'analisi su ogni canale
separatamente (`scripts/multichannel.py::analyze_channels`) e il confronto di gruppo
(front/center/LFE/surround/height) per identificare squilibri e differenze rilevanti.

## 5. Font ABTEC40 con fallback robusto

I PDF del corpus didattico Villa Ficana usano Libre Baskerville (titoli) e Source Sans
Pro (corpo). La skill scarica le TTF OFL e le registra in ReportLab al boot. Se
mancano, cade su Helvetica core (latin-1 completo, accentate italiane preservate)
con un warning in italiano per l'utente.

## 6. Nessun em dash, ovunque

Convenzione stilistica del docente. La skill ha una funzione `sanitize_italiano` in
`scripts/locale_it.py` che ripulisce em dash (—) ed en dash (–) dai testi generati,
sostituendoli con virgole o trattini brevi. Applicata anche al testo prodotto
dall'agente compositivo prima dell'inserimento nel PDF.
