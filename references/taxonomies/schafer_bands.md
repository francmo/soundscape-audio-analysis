# Bande di frequenza Schafer

La suddivisione in 7 bande usata dalla skill segue la convenzione diffusa
nella letteratura di sound studies e broadcast, coerente con il vocabolario
introdotto da R. Murray Schafer in *The Soundscape*.

| Banda | Range Hz | Caratteristiche | Suoni tipici |
|-------|---------:|-----------------|--------------|
| Sub-bass | 20-60 | Vibrazione fisica, percepita più col corpo che con l'orecchio | Terremoti, tuoni lontani, LFE cinema, drone bassi |
| Bass | 60-250 | Corpo, calore, fondamentali di voci maschili e motori | Traffico, motori, passi, contrabbasso, grancassa |
| Low-mid | 250-500 | Pienezza, corpo delle voci medie | Voce parlata maschile, vento costante, riverbero ambiente |
| Mid | 500-2000 | Presenza, chiarezza, fascia della parola | Voci, strumenti melodici, presenza umana |
| High-mid | 2000-4000 | Intelligibilità del parlato, sibilanti | Consonanti dure, uccelli, richiami |
| Presence | 4000-6000 | Brillantezza, dettagli ambientali | Dettagli di field recording, scampanellii |
| Brilliance | 6000-20000 | Aria, spazialità, alte formanti | Grilli, fruscii, cigolii, transienti sibilanti |

## Uso nella skill

Ogni file analizzato produce in `spectral.bands_schafer` la distribuzione
percentuale dell'energia nelle 7 bande. Questo permette di:

- Caratterizzare timbricamente il materiale (bass-heavy, balanced, bright).
- Identificare impronte acustiche di ambienti (es. indoor ha meno Brilliance
  rispetto a outdoor aperti).
- Confrontare diversi field recording in modo quantitativo.
- Popolare i profili GRM con `bands_pct` medi per opera di riferimento.
