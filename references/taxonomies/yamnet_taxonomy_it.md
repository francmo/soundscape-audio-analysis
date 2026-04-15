# YAMNet e tassonomia AudioSet (note per l'uso in italiano)

YAMNet è un modello convoluzionale di Google addestrato su AudioSet.
Classifica in 521 categorie organizzate gerarchicamente, con label in
inglese. La skill riporta le label originali in inglese nei summary JSON
(per non introdurre traduzioni approssimative), e le usa come input
dell'agente compositivo che le contestualizza in italiano.

## Macro-categorie AudioSet (mappatura orientativa in italiano)

| Famiglia | Descrizione | Esempi tipici |
|----------|-------------|---------------|
| Human sounds | Suoni umani | Speech, Singing, Laughter, Cough, Crowd |
| Animal sounds | Animali | Bird vocalization, Dog, Cat, Insects |
| Sounds of things | Oggetti/artefatti | Door, Knock, Water tap, Dishes, Paper |
| Natural sounds | Natura | Wind, Thunderstorm, Rain, Stream |
| Music | Musica | Piano, Guitar, Drum, Choral |
| Source ambiguous | Indeterminati | Silence, White noise, Tick, Mechanisms |
| Channel/Environment | Acustica | Inside small room, Outside rural, Reverberation |

## Nota critica: pre-check LUFS

Il modello è sensibile al livello del segnale. File molto silenziosi
attivano in modo sproporzionato la classe "Silence" (vedi fallimento
Villa Ficana 14/04/2026: 97,9% Silence su file a -60 LUFS). La skill
applica un pre-check LUFS: se il file è sotto -45 LUFS, applica un gain
temporaneo in memoria prima dell'inferenza. Il file originale non viene
modificato. L'avvenuta normalizzazione è registrata nel summary.

## Categorie più frequenti in soundscape

Per orientare l'interpretazione dei risultati YAMNet applicati a field
recording e soundscape composition, queste sono le categorie tipicamente
dominanti:

- **Inside, small room** / **Inside, large room**: firma acustica di
  spazi chiusi (riverbero corto vs lungo).
- **Outside, rural or natural**: ambienti aperti naturali.
- **Outside, urban or manmade**: ambienti urbani antropici.
- **Wind, Rain, Thunder**: geofonia.
- **Bird vocalization, Insect, Frog**: biofonia.
- **Speech, Conversation, Whispering**: presenza umana.
- **Traffic noise, Vehicle, Motorcycle**: antropofonia mobile.
- **Music, Musical instrument**: elementi musicali di passaggio.
- **Mechanical fan, Air conditioning, Microwave**: antropofonia domestica.

Queste categorie, incrociate con le bande Schafer e gli indici ecoacustici,
permettono al report di triangolare la natura del paesaggio sonoro in
modo quantitativo.
