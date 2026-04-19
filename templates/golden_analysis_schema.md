# Schema per `references/golden_analyses/<id>.md`

Template standardizzato per analisi accademiche di riferimento contro cui
misurare l'output dell'agente compositivo. Ogni gold va scritto rispettando
questa struttura perché `scripts/benchmark.py` possa estrarre in modo
deterministico i termini attesi e calcolare precision/recall/Jaccard.

La sezione **`## Metadati`** è YAML-like e **parsabile automaticamente**:
valori dopo i due punti, uno per riga, senza virgole nei valori.

La sezione **`## Tracklist verificata`** dichiara se i titoli/durate sono
stati confrontati contro una fonte affidabile (Discogs, Bandcamp ufficiale,
label). È obbligatoria per accettare il gold come oracolo del benchmark.

Le sezioni **`## Terminologia attesa`** e **`## Parentele stilistiche attese`**
sono elenchi puntati di termini canonici (frase breve, possibilmente
lemma + eventuale qualificatore). Non includere esempi negativi.

---

# <Autore>, <Titolo opera>

## Metadati
autore: <nome cognome>
titolo: <titolo canonico dell'opera>
anno: <YYYY o YYYY-YYYY>
label: <etichetta e catalogo, se applicabile>
luogo: <luogo di registrazione principale>
durata: <mm:ss o hh:mm:ss>
genere: <soundscape | acusmatico | drone | elettroacustico | field recording | ...>

## Tracklist verificata
verificato: <true | false>
fonte: <discogs/bandcamp/label/altro, con URL se possibile>
note: <eventuale disclaimer (es. file scaricato è estratto, album diverso da traccia titolo, ecc.)>

## Contesto critico
<1-3 paragrafi discorsivi. Riferimenti bibliografici inline.>

## Struttura attesa
<Lista puntata di sezioni temporali (timeline) o descrizione della forma globale (ad arco, atlante, plateau...).>

## Terminologia attesa
Ogni voce sulla propria riga, formato: `<termine>` — <breve spiegazione o riferimento accademico>.

Categorie di terminologia da coprire quando pertinenti:
- Schaeffer/TARTYP: tipologia (tenuto, iterativo, impulsivo, accumulativo, ecc.)
- Smalley: motion (flow, oscillation, rotation, push/drag...), growth (dilation, endogeny, multiplication...)
- Chion: modo causale / semantico / ridotto
- Schafer: keynote / signal / soundmark, Hi-Fi / Lo-Fi
- Truax: listening modes, readiness, search
- Krause: biofonia / antropofonia / geofonia, Acoustic Niche Hypothesis
- Westerkamp: soundwalk, indexical listening
- Wishart: utterance (10 categorie)

## Parentele stilistiche attese
Lista di compositori/scuole canonicamente citati in letteratura accademica come parentele pertinenti (max 5). Ogni riga: `<compositore o scuola>` — <motivazione breve>.

## Fonti bibliografiche
Lista puntata di riferimenti bibliografici (autore, titolo, anno). Almeno 2 fonti accademiche revisionate.

## Note per il benchmark
<Eventuali avvertenze: caso anomalo nel catalogo dell'autore, opera atipica rispetto alla poetica generale, gold scritto su estratto/album diverso dalla traccia titolo, ecc.>
