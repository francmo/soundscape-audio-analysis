# Report di analisi audio - Villa Ficana

**Data analisi:** 2026-04-14
**File analizzati:** 3 (1 MP3 + 2 WAV multicanale)

---

## 1. Panoramica dei file

| File | Formato | Durata | Sample rate | Canali | Peak | LUFS |
|------|---------|--------|-------------|--------|------|------|
| Villa Ficana Soundscape.mp3 | MP3 320 kbps | 1h 06' | 22050 Hz | stereo | -22.3 dBFS | **-60.4 LUFS** |
| Cucina Ecomuseo (7.1.4) | PCM float32 | 1' 59" | 22050 Hz | stereo (downmix) | 0.0 dBFS | -25.0 LUFS |
| Camera da letto Ecomuseo (7.1.4) | PCM float32 | 1' 59" | 22050 Hz | stereo (downmix) | -0.3 dBFS | -34.7 LUFS |

> **Nota:** i due WAV erano renderer 7.1.4 ma sono stati caricati come stereo (downmix automatico). Per analisi multicanale completa serve un trattamento separato.

---

## 2. Pulizia tecnica per archivio

### 2.1 Villa Ficana Soundscape.mp3

| Indicatore | Valore | Diagnosi |
|---|---|---|
| Peak | -22.3 dBFS | OK (con headroom abbondante) |
| LUFS integrato | **-60.4 LUFS** | **Molto basso, da normalizzare** |
| Dynamic range | 10.5 dB | Ridotto |
| Clipping | 0 campioni | OK |
| DC offset | -0.0007 | OK |
| Hum 50/60 Hz (FFT alta risoluzione) | +6.5 dB sopra baseline | Trascurabile |

**Azione consigliata:** applicare un gain di +35 dB per portare il file a un livello broadcast standard (-23 LUFS), oppure normalizzare a peak -1 dBFS. Il sospetto hum della prima analisi era un falso positivo: una FFT a risoluzione 0.5 Hz/bin con baseline locale conferma che a 50 e 60 Hz non c'è ronzio significativo.

### 2.2 Cucina Ecomuseo (WAV)

| Indicatore | Valore | Diagnosi |
|---|---|---|
| Peak | 0.0 dBFS | **Al limite, 2 campioni clippati e True Peak +0.4 dBTP** |
| LUFS integrato | -25.0 LUFS | Vicino allo standard broadcast |
| Dynamic range | 49.7 dB | Molto ampio |
| LRA | 14.8 LU | Buono |
| Hum | trascurabile | OK |

**Azione consigliata:** abbassare il livello di -1 dB per portare il True Peak sotto 0 dBTP ed evitare distorsioni in conversione lossy. Il file è in ottime condizioni.

### 2.3 Camera da letto Ecomuseo (WAV)

| Indicatore | Valore | Diagnosi |
|---|---|---|
| Peak | -0.3 dBFS | OK |
| LUFS integrato | -34.7 LUFS | Basso (registrazione di ambiente molto silenzioso) |
| Dynamic range | 41.4 dB | Ampio |
| LRA | 19.2 LU | Molto ampio |

**Azione consigliata:** se serve uniformare con la Cucina, alzare di +9 dB. Altrimenti il livello attuale è coerente con un ambiente notturno.

---

## 3. Analisi spettrale per composizione

### Distribuzione energetica per banda (% del totale)

| Banda (Hz) | Villa Ficana | Cucina | Camera |
|---|---:|---:|---:|
| Sub-bass (20-60) | 2.8% | 1.0% | **24.6%** |
| Bass (60-250) | 4.2% | 14.2% | **33.0%** |
| Low-mid (250-500) | 1.3% | 17.1% | 17.5% |
| Mid (500-2k) | 1.9% | **27.2%** | 16.5% |
| High-mid (2-4k) | 0.2% | **26.1%** | 4.1% |
| Presence (4-6k) | 0.07% | 11.4% | 1.9% |
| Brilliance (6k+) | 0.1% | 3.1% | 0.8% |

### Caratterizzazione timbrica

| Parametro | Villa Ficana | Cucina | Camera |
|---|---:|---:|---:|
| Centroide spettrale | 1850 Hz | 2805 Hz | 2674 Hz |
| Rolloff 85% | 4540 Hz | 5258 Hz | 5538 Hz |
| Spectral flatness | 0.004 (tonale) | 0.121 (misto) | 0.102 (misto) |
| Densità eventi | 0.19 ev/sec (sparsa) | 1.88 ev/sec (media) | 1.70 ev/sec (media) |
| Hi-Fi/Lo-Fi | Lo-Fi | **Hi-Fi** | **Hi-Fi** |

**Per la composizione:**

- La **Cucina** ha lo spettro più ricco e bilanciato (energia distribuita su mid e high-mid). Materiale ideale come *texture principale*, già pronto per l'uso senza grandi elaborazioni.
- La **Camera** è dominata da basse frequenze (57.6% sotto 250 Hz). Materiale interessante per *layer di sfondo*, drone, sostegno bassi. Il pitch up potrebbe rivelare dettagli nascosti.
- **Villa Ficana** richiede prima un boost di gain. Lo spettro è bass-dominant e tonale, contenuto poco diversificato: utile come *materia prima da trasformare* (granulazione, time stretch).

---

## 4. Classificazione contenuti (YAMNet su 521 categorie)

### 4.1 Villa Ficana Soundscape.mp3 (67 minuti)

Top categorie globali:

1. **Silence** - 97.9%
2. Inside, small room - 0.21%
3. White noise - 0.16%
4. Mechanisms - 0.16%
5. Mechanical fan - 0.12%
6. Microwave oven, Noise, Tick, Vehicle, Camera, Music, Rustle, Wind...

**Lettura:** YAMNet considera il file praticamente *silenzio* perché il livello è troppo basso per attivare significativamente i classificatori. Le tracce di "Mechanical fan", "Microwave", "Vehicle", "Music" emergono quando il segnale sale leggermente. Per una classificazione semantica utile bisogna **prima alzare il gain** del file e poi rilanciare YAMNet.

### 4.2 Cucina Ecomuseo

Top categorie globali (alta confidenza):

1. **Inside, small room** - 0.32
2. **Tap (rubinetto)** - 0.07
3. **Water** - 0.06
4. **Water tap, faucet** - 0.05
5. **Dishes, pots, and pans** - 0.05
6. Cutlery, silverware - 0.04
7. Glass, Percussion - 0.04
8. Sink (filling or washing) - 0.04
9. Music - 0.04
10. Liquid, Chink/clink, Drum, Typing

Categorie dominanti per frame:
- Inside small room **28.6%**
- Silence 18.5%
- Music 4.4%, Water tap 3.6%, Percussion 3.6%, Dishes 3.2%, Water 3.2%, Typing 2.8%, Cutlery 2.4%, Frying (food) 2.4%

**Timeline (segmenti 10s):** Inside small room → Typing → Water tap → Silence → Inside → Inside → Silence → Inside.

**Lettura:** scena di cucina perfettamente identificata. Si sente: ambiente chiuso piccolo, rubinetto/lavandino, stoviglie e posate, musica di sottofondo, dattilografia, frittura, vetro. Soundscape **antropofonico domestico** ricco e plausibile per un ecomuseo.

### 4.3 Camera da letto Ecomuseo

Top categorie globali:

1. **Silence** - 0.55
2. **Inside, small room** - 0.21
3. **Knock (busso)** - 0.06
4. **Door (porta)** - 0.05
5. Tap, Writing, Dishes, Wood, Bouncing
6. Inside, large room or hall, Percussion
7. Speech (debole)

Categorie dominanti per frame:
- Silence **46.4%**
- Inside small room **35.5%**
- Knock 8.9%, Door 4.0%, Dishes 1.2%, Animal 0.8%

**Lettura:** ambiente molto più calmo e raccolto. Predomina il silenzio (Schafer: ambiente *Hi-Fi*), interrotto da bussi su porta/legno, qualche scrittura, eventi minimi. Coerente con una camera da letto in ecomuseo, dove il visitatore percepisce la quiete dell'ambiente storico interrotta da pochi gesti.

---

## 5. Confronto fra registrazioni

### Sintesi qualitativa dei tre soundscape

| Caratteristica | Villa Ficana 67' | Cucina | Camera |
|---|---|---|---|
| Tipo di scena (YAMNet) | Indeterminato (silence) | **Cucina attiva** | **Stanza in quiete** |
| Carattere drammaturgico | Texture continua, monotona | Eventi domestici densi | Ambiente sospeso, eventi rari |
| Ricchezza spettrale | Bassa | **Alta** | Media (bias bassi) |
| Hi-Fi / Lo-Fi (Schafer) | Lo-Fi (livello sotto soglia) | **Hi-Fi** | **Hi-Fi** |
| Densità eventi | 0.19 ev/sec | 1.88 ev/sec | 1.70 ev/sec |
| Suono identitario (soundmark candidato) | n.d. | Acqua del rubinetto | Bussi alla porta |

### Per il progetto Soundmapping Borgo Santa Croce

I due rendering 7.1.4 (Cucina e Camera) sono **materiale finito di alta qualità**, già adatto a un'installazione audio: rappresentano due *stanze sonore* coerenti con la funzione (cucina attiva vs camera in quiete) e sfruttano bene il contrasto Hi-Fi.

Il file lungo MP3 va invece **ri-bouncato a un livello più alto** prima di essere usato come materiale compositivo o per una classificazione semantica utile. Allo stato attuale è inservibile come fonte (non si distingue niente).

---

## 6. File generati nella cartella

Per ogni file audio:
- `*_analisi.png` - waveform, spettrogramma, spettro medio
- `*_scheda.txt` - scheda di field recording precompilata
- `*_summary.json` - dati strutturati (per confronti automatici futuri)
- `*_yamnet_summary.txt` - top categorie YAMNet
- `*_yamnet_timeline.csv` - timeline classificazioni segmento per segmento

Solo per Villa Ficana (file lungo):
- `*_hum.png` - analisi mirata 0-200 Hz (50/60 Hz)
- `*_timeline.png` - spettrogramma con energia per banda nel tempo + RMS

---

## 7. Note metodologiche

- **Sample rate di analisi:** tutto è stato downcampionato a 22050 Hz (mono per analisi spettrale, 16 kHz per YAMNet) per ragioni di memoria. Le bande Schafer fino a Brilliance (6 kHz+) sono comunque coperte. Per analisi di dettaglio sopra gli 11 kHz si può rilanciare con sr originale su segmenti più brevi.
- **YAMNet:** modello addestrato su AudioSet di Google (521 classi). Affidabile per categorie generali (ambiente, eventi domestici), meno per dettagli specifici (es. distinguere specie di uccelli serve BirdNET).
- **Hum analysis:** la prima passata (FFT a bassa risoluzione) ha dato un falso positivo. La seconda passata con FFT a 0.5 Hz/bin e baseline locale è la lettura corretta.
