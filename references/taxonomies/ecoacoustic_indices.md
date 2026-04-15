# Indici ecoacustici

Gli indici ecoacustici implementati misurano quantitativamente la complessità,
la diversità e la struttura del paesaggio sonoro. Sono strumenti standard
della bioacustica e ecoacustica per comparare habitat, monitorare biodiversità
e analizzare composizioni soundscape.

Implementazione diretta da formule (nessuna dipendenza da scikit-maad).

## ACI - Acoustic Complexity Index

Pieretti, Farina, Morri (2011). Misura la variazione spettrale nel tempo.
Per ogni bin di frequenza si calcola la somma delle differenze assolute
tra frame successivi, normalizzata sull'energia del bin.

Valori più alti indicano complessità spettro-temporale (canti di uccelli,
eventi discreti). Valori bassi: rumore uniforme o silenzio.

## NDSI - Normalized Difference Soundscape Index

Kasten, Gage, Fox, Joo (2012). Formula:
```
NDSI = (B - A) / (B + A)
```
Dove B è l'energia nella banda biofonica (2-8 kHz) e A nella banda
antropofonica (1-2 kHz). Intervallo [-1, +1].
- NDSI = +1: solo biofonia (habitat intatto).
- NDSI = -1: solo antropofonia (ambiente urbano).
- NDSI = 0: bilanciato.

## H - Acoustic Entropy (Sueur, Aide, Pavoine 2008)

Entropia di Shannon del segnale, calcolata come prodotto di entropia
temporale (sulla envelope) ed entropia spettrale (sulla PSD). Normalizzata
a [0, 1].
- H alto: segnale complesso, distribuito uniformemente.
- H basso: segnale concentrato (tonale, silenzio, picco unico).

## BI - Bioacoustic Index

Boelman, Asner, Hart, Martin (2007). Area sotto la curva spettrale (in dB)
nella banda biofonica (2-8 kHz), normalizzata rispetto al minimo della
banda stessa. Correla con la ricchezza di specie vocalizzanti.

## ADI / AEI - Acoustic Diversity / Evenness

Villanueva-Rivera et al. (2011). Divide lo spettro 0-10 kHz in bande da
1 kHz. Per ognuna calcola la frazione di bin sopra una soglia dB.
- ADI: entropia di Shannon su queste frazioni (diversità spettrale).
- AEI: coefficiente di Gini (equipartizione).

## Lettura integrata per soundscape composition

Per il compositore elettroacustico questi indici permettono di:

- Verificare che un paesaggio sonoro registrato sia sufficientemente
  ricco (ACI, H alti) prima di usarlo come materia prima.
- Mappare la tensione antropica di un territorio (NDSI).
- Confrontare il proprio lavoro con profili di riferimento della
  tradizione GRM e soundscape composition.
