# Vocabolario tipo-morfologico Schaefferiano

Pierre Schaeffer, nel *Traité des objets musicaux* (1966), introduce un
lessico per descrivere gli oggetti sonori al di là della loro fonte
causale, in termini di qualità percettive. L'agente compositivo della
skill usa questo vocabolario per leggere il materiale audio.

## Oggetto sonoro

Unità sonora percepita come un tutto coerente, definita da inizio, durata
e fine. Non è identificata dalla sorgente ma dalle sue qualità interne.

## Matière et forme

- **Matière** (materia): le qualità timbriche intrinseche dell'oggetto
  (massa, grain, colore).
- **Forme** (forma): l'andamento dinamico ed evolutivo nel tempo
  (profilo di attacco, sostegno, estinzione).

## Masse (tipologia di massa)

- **Tonica**: altezza definita, armonicità.
- **Complessa**: altezza percepita ma con spettro arricchito.
- **Nodo**: altezza ambigua o in transizione.
- **Rumore intonato**: massa con colore ma senza altezza precisa.
- **Rumore bianco/rosa/colorato**: massa distribuita senza centro tonale.
- **Impulsiva**: durata prossima a zero, massa istantanea.
- **Tenuta**: massa stabile nel tempo.
- **Iterativa**: ripetizione di unità brevi.

## Grain

Micro-struttura interna della matière.
- **Grain fine**: liscio, omogeneo (seno puro, voce tenuta).
- **Grain grosso**: granuloso, discontinuo (foglie mosse, pioggia).
- **Grain rugoso**: irregolare, complesso (rumore meccanico, voce soffiata).

## Allure

Andamento dinamico interno dell'oggetto mantenuto.
- **Ferma**: stabile, senza oscillazioni.
- **Ondulante**: movimento lento, regolare.
- **Ciclica**: movimento periodico riconoscibile.
- **Disordinata**: oscillazioni irregolari.

## Critère d'entretien (criterio di mantenimento)

- **Impulsivo**: l'oggetto si esaurisce nell'attacco.
- **Tenuto**: si mantiene omogeneamente.
- **Iterativo**: si mantiene per ripetizione.

## Come l'agente applica il vocabolario

L'agente `soundscape-composer-analyst` riceve il summary JSON e identifica
3-5 oggetti sonori tipo-morfologicamente caratterizzati sulla base di:

- Top-peak spettrali (per altezza/armonicità).
- Spectral flatness (0 = tonale, 1 = rumore) → masse.
- Zero-crossing rate, onset density → grain.
- Timeline YAMNet → categorie semantiche come cornice interpretativa.
- Evoluzione temporale (RMS nel tempo, bande nel tempo) → forme.
