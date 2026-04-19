"""Costanti centralizzate. Cambiare qui una volta per avere l'effetto su tutti i moduli."""
from pathlib import Path

# Path di base
SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_ROOT / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
REFERENCES_DIR = SKILL_ROOT / "references"
PROFILES_DIR = REFERENCES_DIR / "grm_profiles"
TEMPLATES_DIR = SKILL_ROOT / "templates"
TESTS_DIR = SKILL_ROOT / "tests"

# Audio defaults
SR_ANALYSIS = 22050
SR_SEMANTIC = 16000
SR_HUM = 8000
N_FFT_ANALYSIS = 4096
N_FFT_HUM = 16384
HOP_LENGTH = 1024

# Hum check
HUM_TARGET_HZ = [50, 60, 100, 120, 150, 180]
HUM_PEAK_BW = 2.0
HUM_BASELINE_BANDS = [(30, 45), (70, 95)]
HUM_VERDICT_THRESHOLDS = {"trascurabile": 10.0, "presente": 20.0}

# Hum context (v0.5.1): evita falsi positivi su materiale musicale tonale.
# Quando flatness e' sotto soglia E top-1 PANNs e' uno strumento musicale con
# score alto, marchiamo i picchi hum come "probabile componente armonica
# strumentale" senza cambiare il verdict numerico (che resta il dato grezzo).
HUM_CONTEXT_FLATNESS_MAX = 0.05
HUM_CONTEXT_CLASSIFIER_SCORE_MIN = 0.5
MUSICAL_INSTRUMENT_LABELS = {
    # Strumenti con spettro armonico puro o prevalentemente tonale (AudioSet)
    "Music", "Musical instrument", "Orchestra", "Classical music",
    "Flute", "Clarinet", "Saxophone", "Oboe", "Bassoon",
    "Wind instrument, woodwind instrument", "Brass instrument",
    "Trumpet", "Trombone", "French horn", "Tuba",
    "Violin, fiddle", "Cello", "Double bass", "Viola",
    "String (musical instrument)", "Bowed string instrument",
    "Plucked string instrument", "Harp",
    "Guitar", "Acoustic guitar", "Electric guitar", "Bass guitar",
    "Mandolin", "Banjo", "Ukulele",
    "Piano", "Electric piano", "Keyboard (musical)",
    "Organ", "Electronic organ", "Hammond organ", "Pipe organ",
    "Synthesizer", "Sampler", "Theremin",
    "Harpsichord", "Accordion", "Harmonica",
    "Bell", "Church bell", "Chime", "Tubular bells",
    "Singing", "Choir", "Chant", "Mantra",
    "Vocal music", "A capella",
    "Drum kit", "Snare drum", "Bass drum", "Timpani",
    "Xylophone", "Marimba, xylophone", "Vibraphone", "Glockenspiel",
}

# Livelli
CLIPPING_THRESHOLD = 0.999
DC_OFFSET_THRESHOLD = 0.005
LUFS_SEMANTIC_PRECHECK = -45.0
LUFS_SEMANTIC_TARGET = -23.0
LUFS_PODCAST_TARGET = -16.0

# Bande Schafer
SCHAFER_BANDS = [
    ("Sub-bass", 20, 60),
    ("Bass", 60, 250),
    ("Low-mid", 250, 500),
    ("Mid", 500, 2000),
    ("High-mid", 2000, 4000),
    ("Presence", 4000, 6000),
    ("Brilliance", 6000, 20000),
]

# Semantica (classificatore)
SEMANTIC_BACKEND = "panns"  # "panns" (default v0.2) | "yamnet" (legacy)
SEMANTIC_DEVICE = "auto"    # "auto" | "mps" | "cpu" | "cuda"

# YAMNet (legacy)
YAMNET_URL = "https://tfhub.dev/google/yamnet/1"
YAMNET_CHUNK_SECONDS = 60
YAMNET_FRAME_HOP_S = 0.48

# PANNs
PANNS_CHECKPOINT_URL = "https://zenodo.org/records/3987831/files/Cnn14_mAP%3D0.431.pth?download=1"
PANNS_SR = 32000

# CLAP auto-tagging (v0.2.1)
CLAP_MODEL_NAME = "music_audioset_epoch_15_esc_90.14"
CLAP_CHECKPOINT_URL = "https://huggingface.co/lukewys/laion_clap/resolve/main/music_audioset_epoch_15_esc_90.14.pt"
CLAP_SEGMENT_S = 10.0
CLAP_TOP_K = 3

# Speech transcription (v0.5.0)
WHISPER_MODEL = "large-v3"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_DEVICE = "cpu"  # CTranslate2 non supporta MPS; NEON SIMD su Apple Silicon da' ~15x realtime
WHISPER_BEAM_SIZE = 5
WHISPER_LANG_DETECT_SEGMENTS = 3  # 90 s per mitigare audio multilingua
WHISPER_LANG_CONF_WARN = 0.85  # warning se language_probability sotto soglia
WHISPER_SR = 16000  # sample rate richiesto da Whisper e Silero VAD

# Silero VAD (v0.5.0)
SILERO_VAD_THRESHOLD = 0.5
SILERO_VAD_MIN_SPEECH_MS = 250
SILERO_VAD_MIN_SILENCE_MS = 250
SILERO_VAD_MIN_TOTAL_SPEECH_S = 2.0  # soglia per saltare Whisper (risparmia ~1.2 GB RAM)

# Speech suggerimento automatico stderr (v0.5.0)
SPEECH_SUGGEST_DOMINANT_PCT = 25.0  # soglia PANNs top_dominant_frames per suggerire --speech

# Traduzione via claude -p (v0.5.0)
TRANSLATION_MODEL = "claude-haiku-4-5"
TRANSLATION_TIMEOUT_S = 120
TRANSLATION_CHUNK_THRESHOLD_CHARS = 8000
TRANSLATION_CHUNK_SIZE_CHARS = 6000
TRANSLATION_CHUNK_OVERLAP_CHARS = 500

# PDF Dialoghi trascritti (v0.5.0)
TRANSCRIPT_PDF_MAX_CHARS = 2000  # soglia inline nel PDF, oltre esporta .txt companion

# CLAP allucinazioni speech-related (v0.5.1): marca i tag con keyword di voce
# come likely_hallucination quando PANNs non rileva voce. Evita "Discussione di
# vicini" su drone ambient privo di parlato.
HALLUCINATION_SPEECH_SCORE_MAX = 0.10
HALLUCINATION_SPEECH_DOMINANT_PCT_MAX = 5.0
SPEECH_KEYWORDS_IT = {
    "voce", "voci", "vociare", "discussione", "dialogo", "dialogare",
    "parla", "parlato", "parlante", "interlocutore", "interlocutori",
    "canto", "cantata", "cantato", "canta", "coro", "corale",
    "preghiera", "preghiere", "sussurrata", "spiega", "spiegare",
    "venditore", "venditori", "grida", "gridano", "voci di",
    "discussione di vicini", "vociare di",
}

# Filtro geo-specificita' (v0.5.2): tag CLAP che contengono keyword di luoghi
# italo-specifici vengono marcati con flag `geo_specific=True` su materiale
# non identificato come italiano. Il flag e' separato da `likely_hallucination`:
# segnala "tag potenzialmente fuori contesto geografico", non hallucination
# certa. Emerso dal feedback su Presque Rien N°1 (Croazia) classificato come
# "borgo medievale italiano" e "cicale del sud Italia".
LOCATION_SPECIFIC_KEYWORDS_IT = {
    "italian", "italia", "italiana", "italiano", "italiani",
    "marchigian", "toscan", "siciliana", "siciliano", "napolet",
    "veneto", "veneta", "lombard", "romana", "romano", "fiorentin",
    "AFAM", "conservatorio italiano", "borgo medievale", "italianita",
    "campanile di paese", "barocca", "gregoriano", "afam",
    "dialetto locale", "in dialetto", "parlato italiano",
    "centro storico italiano", "ecomuseo rurale",
    "fiera paesana", "osteria pomeridiana",
    "bar italiano", "moka", "trituratore per pasta", "caffettiera",
    "campane di chiesa", "piazza italiana", "via",
}

# CLAP plausibility check deterministico (v0.6.6): pre-filtro sui tag CLAP
# sistematicamente allucinati emersi dal confronto blind corpus Nottoli.
# Per ciascun pattern, se i PANNs "supporto" sono sotto le soglie, il tag
# viene marcato `plausibility: "low"`; se sono moderati, `medium`; altrimenti
# `high` (o nessun flag, che equivale a high). Differisce da
# `likely_hallucination` (binario, specifico su voce) perche' usa una scala
# a tre livelli. Embrione della v0.7.0 plausibility check completa, limitato
# a 5 pattern ad alto tasso di falso positivo documentati.
#
# Ogni pattern e' una tupla: (keyword_any, panns_any, threshold_low,
# threshold_medium, reason_template).
# - keyword_any: sottostringhe case-insensitive da cercare nel prompt CLAP.
#   Se almeno una matcha, il pattern si applica.
# - panns_any: label AudioSet che fungono da "supporto empirico" per il
#   pattern. Si prende il max score fra queste label in PANNs top_global
#   e si confronta con le soglie.
# - threshold_low: sotto questo score il tag e' plausibility=low.
# - threshold_medium: fra low e medium. Sopra medium, plausibility=high.
# - reason_template: stringa con placeholder {score} e {labels}.
PLAUSIBILITY_PATTERNS = (
    {
        "name": "acqua",
        "keywords": ("acqua del rubinetto", "rubinetto", "fontana pubblica",
                     "sgorga da fontana", "goccia d'acqua che cade"),
        "panns_any": ("Water", "Stream", "Liquid", "Gurgling",
                      "Drip", "Pour", "Waterfall", "Ocean"),
        "threshold_low": 0.03,
        "threshold_medium": 0.08,
        "reason": "prompt idrico specifico",
    },
    {
        "name": "preghiera",
        "keywords": ("preghiera collettiva", "processione religiosa",
                     "liturgia", "preghiera sussurrata"),
        "panns_any": ("Choir", "Chant", "Religious music",
                      "Mantra", "Hymn", "Speech"),
        "threshold_low": 0.02,
        "threshold_medium": 0.08,
        "reason": "prompt liturgico sacro",
    },
    {
        "name": "spiaggia_mediterranea",
        "keywords": ("spiaggia mediterranea", "onde leggere",
                     "mare calmo con onde", "sciabordio"),
        "panns_any": ("Ocean", "Water", "Wind", "Waves, surf"),
        "threshold_low": 0.03,
        "threshold_medium": 0.07,
        "reason": "prompt costiero marino",
    },
    {
        "name": "biofonia_insetti",
        "keywords": ("insetti in texture densa", "grilli nella sera",
                     "cicale in campagna", "canto di uccelli",
                     "cinguettio", "cinghiale", "gallo che canta",
                     "gufo notturno", "dawn chorus"),
        "panns_any": ("Cricket", "Insect", "Animal", "Bird",
                      "Bird vocalization, bird call, bird song",
                      "Chirp, tweet", "Wild animals", "Owl", "Crow"),
        "threshold_low": 0.03,
        "threshold_medium": 0.08,
        "reason": "prompt biofonico animale",
    },
    {
        "name": "treno",
        "keywords": ("treno regionale", "treno ad alta velocita",
                     "stazione ferroviaria", "treno in arrivo"),
        "panns_any": ("Train", "Rail transport", "Railroad car, train wagon",
                      "Train horn", "Train whistle", "Train wheels squealing"),
        "threshold_low": 0.04,
        "threshold_medium": 0.10,
        "reason": "prompt ferroviario",
    },
    {
        "name": "aspirapolvere_domestico",
        "keywords": ("aspirapolvere", "phon per capelli",
                     "rasoio elettrico", "trituratore", "frullatore"),
        "panns_any": ("Vacuum cleaner", "Mechanisms", "Engine",
                      "Machinery", "Domestic sounds, home sounds"),
        "threshold_low": 0.02,
        "threshold_medium": 0.06,
        "reason": "prompt elettrodomestico",
    },
    {
        "name": "scrittura_tastiera",
        "keywords": ("scrittura su tastiera", "tastiera di computer",
                     "digitazione su computer", "tastiera digitale"),
        "panns_any": ("Typing", "Computer keyboard",
                      "Keyboard (musical)", "Click"),
        "threshold_low": 0.02,
        "threshold_medium": 0.06,
        "reason": "prompt digitazione",
    },
    {
        "name": "pianto_infantile",
        "keywords": ("pianto infantile", "lallazione infantile",
                     "bambino che piange", "neonato"),
        "panns_any": ("Baby cry, infant cry", "Crying, sobbing",
                      "Child speech, kid speaking", "Whimper", "Wail, moan"),
        "threshold_low": 0.02,
        "threshold_medium": 0.06,
        "reason": "prompt infantile",
    },
    {
        "name": "grandine_impulsi",
        "keywords": ("grandine che cade", "grandinata",
                     "grandine su superficie"),
        "panns_any": ("Hail", "Ice", "Rain on surface", "Patter", "Pour"),
        "threshold_low": 0.02,
        "threshold_medium": 0.06,
        "reason": "prompt grandine impulsivo",
    },
    {
        "name": "porta_legno",
        "keywords": ("porta di legno che si apre", "porta che si chiude",
                     "porta cigolante", "uscio di legno"),
        "panns_any": ("Door", "Creak", "Squeak", "Slam", "Wood"),
        "threshold_low": 0.02,
        "threshold_medium": 0.06,
        "reason": "prompt porta legno",
    },
    {
        "name": "veicoli_specifici",
        "keywords": ("motocicletta sportiva", "automobile che frena",
                     "auto da corsa", "clacson di auto",
                     "motorino che passa"),
        "panns_any": ("Motorcycle", "Car", "Race car, auto racing",
                      "Motor vehicle (road)", "Vehicle horn",
                      "Skidding", "Tire squeal"),
        "threshold_low": 0.03,
        "threshold_medium": 0.08,
        "reason": "prompt veicolo specifico",
    },
)

# Mapping delle label AudioSet (PANNs) verso categorie Krause (v0.6.6).
# Usato da `aggregate_academic_hints` per produrre `krause_cross_check`, stima
# indipendente della distribuzione Krause derivata dai frame dominanti PANNs,
# separata dal calcolo CLAP-based. Serve a rilevare inconsistenze fra le due
# stime (es. Sud di Risset: NDSI +0.516 biofonico, ma Krause hint CLAP-based
# 4% biofonia per dominanza di prompt antropofonici nella top-10). Le
# categorie coprono solo label ad alto segnale: molte label AudioSet
# ("Music", "Speech") sono genericamente antropofoniche ma vengono classificate
# con cautela. Label sconosciute cadono in "mista" di default.
PANNS_LABEL_TO_KRAUSE = {
    # Biofonia (animali, insetti, uccelli, fauna)
    "Animal": "biofonia",
    "Bird": "biofonia",
    "Bird vocalization, bird call, bird song": "biofonia",
    "Chirp, tweet": "biofonia",
    "Cricket": "biofonia",
    "Insect": "biofonia",
    "Owl": "biofonia",
    "Crow": "biofonia",
    "Wild animals": "biofonia",
    "Dog": "biofonia",
    "Cat": "biofonia",
    "Horse": "biofonia",
    "Cow": "biofonia",
    "Chicken, rooster": "biofonia",
    "Wolf": "biofonia",
    "Pigeon, dove": "biofonia",
    "Duck": "biofonia",
    "Cattle, bovinae": "biofonia",
    "Pig": "biofonia",
    "Sheep": "biofonia",
    "Frog": "biofonia",
    "Bee, wasp, etc.": "biofonia",
    "Mosquito": "biofonia",
    "Fly, housefly": "biofonia",
    "Whale vocalization": "biofonia",
    "Goat": "biofonia",
    # Geofonia (elementi naturali non biologici)
    "Water": "geofonia",
    "Stream": "geofonia",
    "Ocean": "geofonia",
    "Wind": "geofonia",
    "Thunder": "geofonia",
    "Thunderstorm": "geofonia",
    "Rain": "geofonia",
    "Rain on surface": "geofonia",
    "Fire": "geofonia",
    "Crackle": "geofonia",  # spesso fuoco
    "Waves, surf": "geofonia",
    "Waterfall": "geofonia",
    "Gurgling": "geofonia",
    "Drip": "geofonia",
    # Antropofonia (voce umana + musica + macchine + urbano)
    "Speech": "antropofonia",
    "Male speech, man speaking": "antropofonia",
    "Female speech, woman speaking": "antropofonia",
    "Child speech, kid speaking": "antropofonia",
    "Singing": "antropofonia",
    "Choir": "antropofonia",
    "Chant": "antropofonia",
    "Humming": "antropofonia",
    "Narration, monologue": "antropofonia",
    "Shout": "antropofonia",
    "Crowd": "antropofonia",
    "Laughter": "antropofonia",
    "Cheering": "antropofonia",
    "Applause": "antropofonia",
    "Music": "antropofonia",
    "Musical instrument": "antropofonia",
    "Vehicle": "antropofonia",
    "Car": "antropofonia",
    "Train": "antropofonia",
    "Rail transport": "antropofonia",
    "Boat, Water vehicle": "antropofonia",
    "Aircraft": "antropofonia",
    "Motor vehicle (road)": "antropofonia",
    "Engine": "antropofonia",
    "Traffic noise, roadway noise": "antropofonia",
    "Machinery": "antropofonia",
    "Inside, small room": "antropofonia",
    "Inside, large room or hall": "antropofonia",
    "Environmental noise": "antropofonia",
    "Outside, urban or manmade": "antropofonia",
    "Race car, auto racing": "antropofonia",
    "Run": "antropofonia",
}

# Narrativa (v0.2.2)
NARRATIVE_WINDOW_S = 30.0
NARRATIVE_MODE_DEFAULT = "full"  # "full" | "summary" | "none"

# Narrativa delta-based (v0.6.0): la prima finestra ha descrizione completa,
# le successive vengono descritte solo se almeno una di queste feature
# cambia significativamente rispetto alla finestra precedente. Le finestre
# senza delta vengono accumulate come "plateau" con una sola riga finale.
# Driver: bug del v0.5.x in cui le feature timbriche globali erano ripetute
# identiche in 40+ blocchi (audio6_report.pdf pp. 14-21).
NARRATIVE_DELTA_CENTROID_PCT = 0.15  # +/- 15% sul centroide
NARRATIVE_DELTA_FLATNESS_PCT = 0.30  # +/- 30% sulla flatness
NARRATIVE_DELTA_RMS_DB = 6.0  # +/- 6 dB sul RMS

# Segmentazione strutturale (v0.6.0): identifica sezioni significative del
# brano via changepoint detection deterministico su gradiente di feature
# multidimensionali per finestra (RMS, centroide, flatness, top-1 PANNs/CLAP).
STRUCTURE_WINDOW_S = 10.0  # finestra di analisi (allineata a CLAP)
STRUCTURE_MIN_SECTIONS = 2  # almeno 2 sezioni anche su file omogenei
STRUCTURE_MAX_SECTIONS = 8  # massimo 8 sezioni anche su file frammentati
STRUCTURE_MIN_SECTION_DURATION_S = 30.0  # min distance fra confini consecutivi
STRUCTURE_GRADIENT_THRESHOLD_MAD_K = 2.0  # soglia adattiva: mediana + K*MAD
# Mappa colori per la timeline grafica (per categoria Krause dominante)
STRUCTURE_TIMELINE_COLORS = {
    "biofonia": "#2e7d32",  # verde scuro
    "antropofonia": "#ef6c00",  # arancio
    "geofonia": "#1565c0",  # blu
    "mista": "#6a1b9a",  # viola
    "silenzio": "#757575",  # grigio
}

# Corpus report (v0.3.0)
GOLDEN_REPORTS_DIR = REFERENCES_DIR / "golden_reports"
GOLDEN_VILLA_FICANA = GOLDEN_REPORTS_DIR / "REPORT_ANALISI_villa_ficana.md"
CORPUS_REPORT_MODEL = "opus"
CORPUS_REPORT_TIMEOUT_S = 300
CORPUS_CONFIRM_THRESHOLD_FILES = 10
CORPUS_CONFIRM_THRESHOLD_MINUTES = 30

# Onset density
ONSET_DENSITY_SPARSE = 0.5
ONSET_DENSITY_DENSE = 2.0

# Hi-Fi / Lo-Fi
HIFI_DR_HIGH = 25.0
HIFI_DR_MID = 15.0
HIFI_FLATNESS_MAX = 0.3

# Ecoacoustic
ECO_BIOPHONY_BAND = (2000, 8000)
ECO_ANTHROPOPHONY_BAND = (1000, 2000)

# v0.9.0 Step A: backend indici ecoacustici.
# - "legacy": implementazione custom storica (scripts/ecoacoustic.py, v0.2+).
# - "maad": thin wrapper sopra scikit-maad (scripts/ecoacoustic_maad.py),
#   libreria peer-reviewed (Ulloa et al. 2021, SoftwareX). Output API identico.
# Il flip del default a "maad" avverra' in v0.10.0 solo se il parity test
# (tests/test_ecoacoustic_parity.py + corpus golden v1) conferma delta
# accettabili documentati nel research log.
ECO_BACKEND = "legacy"

# Palette ABTEC40 (hex)
PALETTE = {
    "dark": "#1a2a3a",
    "dark_mid": "#2d4a5e",
    "teal": "#3d6a7a",
    "teal_light": "#7eb8c9",
    "beige_warm": "#c9a87c",
    "terracotta": "#c17f59",
    "terracotta_dk": "#8b4513",
    "bg": "#f5f0eb",
    "bg_light": "#f8f5f0",
    "bg_muted": "#e8e0d8",
    "gold": "#ffd700",
    "white": "#ffffff",
    "muted_gray": "#6b7280",
}

# Report PDF
PDF_PAGE_SIZE_MM = (210, 297)  # A4
PDF_MARGINS_MM = {"top": 22, "right": 20, "bottom": 20, "left": 22}

# Timeouts
# v0.5.3: prompt agente esteso con identificazione preliminare obbligatoria
# (3 step: leggi signature, formula 2-3 ipotesi attribuzione, decidi).
# Il ragionamento iniziale + lettura del file JSON puo' richiedere oltre 120 s
# su file lunghi (~20 min audio con timeline densa). Aumentato a 300 s per
# evitare timeout su Presque Rien e simili.
# v0.6.2: con payload esteso da structure + schaeffer_detail + smalley_growth
# e narrative delta-based espansa su file ~20 min, 300 s restano stretti.
# audio7_report.pdf ha mostrato timeout x2 senza output. Portato a 600 s.
AGENT_TIMEOUT_S = 600
AGENT_RETRIES = 1

# Testo output
LANG_DEFAULT = "it"
