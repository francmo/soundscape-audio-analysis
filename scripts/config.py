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

# Narrativa (v0.2.2)
NARRATIVE_WINDOW_S = 30.0
NARRATIVE_MODE_DEFAULT = "full"  # "full" | "summary" | "none"

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
AGENT_TIMEOUT_S = 120
AGENT_RETRIES = 1

# Testo output
LANG_DEFAULT = "it"
