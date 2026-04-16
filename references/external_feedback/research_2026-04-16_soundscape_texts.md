# Ricerca testi soundscape composition (16/04/2026)

Sintesi prodotta da agente di ricerca su web (general-purpose) su richiesta
dell'utente: identificare testi accademici, libri, articoli e risorse
online che potrebbero arricchire la skill `soundscape-audio-analysis` in
tre direzioni: tassonomie aggiuntive, vocabolari CLAP piu' ricchi,
strumenti analitici quantitativi 2021-2026.

Materiale di riferimento per pianificazione versioni v0.6.x → v0.8.0+
(vedi `ROADMAP.md` aggiornata 16/04/2026).

---

## 1. Tassonomie aggiuntive

### Priorita' ALTA

- **Schaeffer P., *Treatise on Musical Objects: An Essay across Disciplines***,
  University of California Press, 2017 (trad. North/Dack del *Traite'* 1966).
  Il *Solfege des Objets Sonores* completo (TARTYP) introduce 28 classi
  tipologiche con criteri di massa/fattura/sostegno. La skill copre solo
  parzialmente (8 tipi schaeferiani in mapping accademico). Estensione: refactor
  del mapping per supportare TARTYP completo.

- **Smalley D., "Spectromorphology: explaining sound-shapes",
  *Organised Sound* 2(2), 1997**. PDF aperto su York University. Tassonomia
  completa Note/Node/Noise + 4 assi (Typology, Morphology, Motion, Structuring
  Processes). Sottocategorie motion (*unidirectional, reciprocal, cyclic/
  centric, convolution*) e growth processes (*dilation, accumulation,
  dissipation*) parzialmente coperte (la skill ha solo turbulence/flow).

- **Wishart T., *On Sonic Art* (Emmerson ed.), Routledge/Harwood, 1996**.
  Lattice tridimensionale pitch/duration/timbre, teoria del *sound-object*
  come "morphology with internal motion", capitoli su utterance umana e
  non-umana e su "representational sounds". Categoria nuova: gesti vocali
  e utterance.

- **Landy L., *Understanding the Art of Sound Organization***,
  MIT Press, 2007. Definisce *sound-based music* con framework olistico
  (intent/receptivity), categorie di accesso al pubblico ("something to
  hold on to factor"), mappa al catalogo EARS (ears.huma-num.fr). Ontologia
  formalizzata gia' strutturata, importabile direttamente.

### Priorita' MEDIA

- **Roads C., *Microsound***, MIT Press, 2001. Nove time scales
  (infinite, supra, macro, meso, sound object, micro, sample, subsample,
  infinitesimal) e tassonomia particles (grains, glissons, grainlets, pulsars,
  trainlets). Utile per analisi a scala micro nei soundscape granulari/drone.

- **Kane B., *Sound Unseen: Acousmatic Sound in Theory and Practice***,
  Oxford UP, 2014. Teoria della "sonic trinity" (source/cause/effect) e
  "spacing" (*technê*) per descrivere il grado di separazione causale.
  Categoria nuova di "acousmaticity" da affiancare ai listening modes di
  Chion.

- **Emmerson S., *Living Electronic Music***, Ashgate 2007 / Routledge 2017.
  Tassonomia performance/diffusion (*local/field functions, arena/landscape*)
  e i "Five Spaces" come categoria analitica.

### Priorita' BASSA

- **Voegelin S., *Listening to Noise and Silence***, Bloomsbury, 2010.
  Fenomenologia dell'ascolto come pratica socio-politica. Utile per il
  commento estetico dell'agente, non per tassonomie computabili.

---

## 2. Vocabolari di prompt CLAP piu' ricchi

### Priorita' ALTA

- **Battier M., "What the GRM brought to music", *Organised Sound* 12(3),
  2007**. Lessico GRM (acousmonium, *figures sonores*, *jeux*) e categorie
  Schaefferian *ecoute reduite/causale/semantique*. Da qui derivare prompt
  come "acousmatic diffusion in concert hall", "GRM-style spectral
  processing", "phonographic field recording with reduced listening intent".

- **Westerkamp H., scritti raccolti su hildegardwesterkamp.ca** (sezione
  "writings"). Categorie di soundwalk e *Kits Beach Soundwalk* analizzato in
  scalar.usc.edu. Prompt: "high-frequency barnacle ecosystem", "harbor
  industrial drone with seagulls", "narrated soundwalk with reflexive
  commentary". Rafforza categoria soundwalk gia' presente.

- **Kahl S. et al., BirdNET technical documentation, Cornell K. Lisa Yang
  Center for Conservation Bioacoustics, 2021-2025**. Tassonomia di
  vocalizzazioni (call/song/alarm/contact) per rendere la categoria
  *biofonia* italiana piu' precisa.

### Priorita' MEDIA

- **McFarlane W. M., "The Development of Acousmatics in Montreal",
  *eContact!* 6.2** (CEC). Per scuola canadese: prompt su "Dhomont-style
  narrative acousmatics", "Empreintes DIGITALes spatial diffusion",
  "Truax granular soundscape composition".

- **WDR Studio Koln (Stockhausen) - articoli su *Studie I*, *Studie II*,
  *Gesang der Junglinge*, *Kontakte*** (Stockhausen-Verlag). Prompt
  elektronische Musik: "pure sine tone synthesis", "tone mixture clusters",
  "ring modulation cathedral", "impulse-derived noise band".

- **Tamm E., *Brian Eno: His Music and the Vertical Color of Sound***,
  Da Capo Press, 1995 (PDF Monoskop). Per ambient/drone: "as ignorable as
  it is interesting", *furniture music*, *vertical color*, generative
  ambient. Prompt: "Eno-style generative ambient", "slowly evolving drone
  cluster", "non-teleological texture".

---

## 3. Strumenti analitici quantitativi (2021-2026)

### Priorita' ALTA

- **Bradfer-Lawrence T. et al., "The Acoustic Index User's Guide",
  *Methods in Ecology and Evolution* 16, 2025**. Manuale operativo con 91
  registrazioni di riferimento (aria/acqua/suolo) e codice. Indici aggiornati
  oltre ACI/NDSI/H/BI: ADI, AEI, **FADI** (frequency-dependent ADI, Xu et al.
  2024 in *Ecological Indicators*). Sostituisce/estende il modulo indici
  ecoacustici esistente.

- **Mitchell A. et al., "Soundscapy: A python package for soundscape
  assessment and analysis", *INTER-NOISE 2024 Proceedings*, Nantes**.
  Libreria Python ISO 12913-3 con circumplex pleasantness/eventfulness,
  analisi psicoacustica binaurale, modelli predittivi PAQ. GitHub:
  `MitchellAcoustics/Soundscapy`. Introduce dimensione perceptive ISO
  totalmente assente nella skill.

- **ISO/TS 12913-2:2018 e 12913-3:2019**. Standard con 8 PAQ bipolari
  (pleasant/unpleasant, vibrant/monotonous, eventful/uneventful, chaotic/
  calm, annoying/not annoying) trasformabili in due assi
  pleasantness/eventfulness. Nuova categoria tassonomica.

- **Mei X. et al., "WavCaps", *IEEE TASLP* 32, 2024** (arxiv 2303.17395).
  Dataset di 400k clip con caption naturali (AudioSet, BBC SFX, FreeSound,
  SoundBible) usabile come fonte di prompt vocabulary piu' ricco e
  idiomatico per CLAP zero-shot. Estende direttamente il vocabolario di
  193 prompt.

- **Stowell D., "Computational bioacoustics with deep learning: a review
  and roadmap", *PeerJ* 10, 2022, e_13152**. Review canonica su deep learning
  per bioacustica ecologica. Riferimento metodologico per scelte di
  architettura.

- **Kane J. et al., "Limits to the accurate and generalizable use of
  soundscapes to monitor biodiversity", *Nature Ecology & Evolution* 7,
  2023**. Indici univariati e ML non predicono species richness in modo
  cross-dataset; soundscape change indica community change. **Caveat
  metodologico critico** da integrare nei report.

### Priorita' MEDIA

- **Wu Y. et al., *LAION-CLAP* - github.com/LAION-AI/CLAP** e
  **Microsoft CLAP - github.com/microsoft/CLAP**. La skill gia' usa CLAP;
  T-CLAP (Wu et al. 2024) aggiunge sensibilita' all'ordine temporale degli
  eventi (+30pp retrieval), GLAP (Pellegrini et al. 2025, arxiv 2506.11350)
  estende a multilingue. Upgrade del modello gia' in uso.

- **Kahl S. et al., "Overview of BirdCLEF 2024", CLEF Working Notes,
  2024** (HAL inria.hal-04719578). Dataset Western Ghats e tecniche
  pseudo-labeling. **BirdCLEF+ 2025** estende a mammiferi/anfibi/insetti.
  Utile se la skill espande la biofonia oltre uccelli.

- **Ghani B. et al., "Global birdsong embeddings enable superior transfer
  learning for bioacoustic classification", *Scientific Reports* 13, 2023;
  estensioni Perch 2.0 (Hamer et al. 2024)**. Embeddings da affiancare/
  sostituire a PANNs per analisi biofonica.

---

## Mapping ricerca → versioni della skill

| Risorsa | Versione skill | Stima ore |
|---------|----------------|-----------|
| FADI + caveat Kane et al. | v0.6.1 | 3-4 |
| Soundscapy + ISO 12913-3 | v0.7.0 | 10-14 |
| WavCaps + Battier + Westerkamp + WDR + BirdNET | v0.7.1 | 4-6 |
| TARTYP completo + Smalley esteso + Wishart utterance + EARS | v0.8.0 | 12-18 |
| Plausibility check CLAP (rinviato) | v0.9.0+ | 6-10 |

---

## Sources principali

- [On Sonic Art (Wishart) - Routledge](https://www.routledge.com/On-Sonic-Art/Emmerson-Wishart/p/book/9783718658473)
- [Spectromorphology (Smalley 1997) - Organised Sound PDF](http://www.yorku.ca/vannort/smalley-spectromorphology.pdf)
- [Understanding the Art of Sound Organization (Landy) - MIT Press](https://mitpress.mit.edu/9780262529259/understanding-the-art-of-sound-organization/)
- [Microsound (Roads) - MIT Press](https://mitpress.mit.edu/9780262681544/microsound/)
- [Treatise on Musical Objects (Schaeffer) - JSTOR](https://www.jstor.org/stable/10.1525/j.ctt1qv5pqb)
- [What the GRM brought to music (Battier) - Organised Sound](https://www.cambridge.org/core/journals/organised-sound/article/abs/what-the-grm-brought-to-music-from-musique-concrete-to-acousmatic-music/A7918A18328E4DF62512DAD515BD2752)
- [Sound Unseen (Kane) - Oxford UP](https://global.oup.com/academic/product/sound-unseen-9780199347841)
- [Hildegard Westerkamp writings](https://www.hildegardwesterkamp.ca/writings/writings-by/?post_id=11)
- [The Acoustic Index User's Guide (Bradfer-Lawrence 2025) - MEE](https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210X.14357)
- [Frequency-dependent acoustic diversity index (FADI) - Ecol Ind 2024](https://www.sciencedirect.com/science/article/pii/S1470160X23010828)
- [Soundscapy (Mitchell 2024) - INTER-NOISE Proceedings](https://ince.publisher.ingentaconnect.com/contentone/ince/incecp/2024/00000270/00000007/art00005)
- [Soundscapy GitHub repository](https://github.com/MitchellAcoustics/Soundscapy)
- [ISO 12913-1 Soundscape Definition](https://www.iso.org/obp/ui/#iso:std:iso:12913:-1:ed-1:v1:en)
- [ISO/TS 12913-3:2019 Data Analysis PDF](https://cdn.standards.iteh.ai/samples/69864/27add82ea1724f9599bf0ae2208472f2/ISO-TS-12913-3-2019.pdf)
- [LAION CLAP - GitHub](https://github.com/LAION-AI/CLAP)
- [WavCaps paper (arxiv)](https://arxiv.org/html/2303.17395v2)
- [BirdNET publications - Cornell](https://birdnet.cornell.edu/publications/)
- [Limits to accurate use of soundscapes for biodiversity - Nat Ecol Evol](https://www.nature.com/articles/s41559-023-02148-z)
- [Computational bioacoustics review (Stowell 2022) - PeerJ](https://peerj.com/articles/13152/)
