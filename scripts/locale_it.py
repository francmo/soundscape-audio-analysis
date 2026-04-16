"""Stringhe italiane centralizzate.

Tutte le etichette e i verdetti usati dal toolkit passano da qui.
Le accentate sono sempre nella forma italiana corretta.
Non usare em dash ovunque: solo virgole, punti, trattini brevi.
"""

VERDETTI_HUM = {
    "trascurabile": "trascurabile",
    "presente": "presente",
    "forte": "forte",
}

CATEGORIE_HIFI = {
    "hifi": "Hi-Fi (alta diversità spettrale, buona dinamica)",
    "medio": "Medio (caratteristiche bilanciate)",
    "lofi": "Lo-Fi (bassa dinamica, possibile saturazione di rumore di fondo)",
}

DENSITA_EVENTI = {
    "sparsa": "sparsa (texture continua, pochi eventi)",
    "media": "media (eventi sonori distinguibili)",
    "densa": "densa (molti eventi sovrapposti)",
}

DIAGNOSI_CLIPPING_OK = "assente"
DIAGNOSI_CLIPPING_KO = "presente"
DIAGNOSI_DC_OK = "ok"
DIAGNOSI_DC_KO = "da correggere"

INTESTAZIONI = {
    "metadati": "Metadati tecnici",
    "livelli_dinamica": "Livelli e dinamica",
    "diagnosi_tecnica": "Diagnosi tecnica",
    "spettro": "Distribuzione spettrale per banda",
    "caratt_timbrica": "Caratterizzazione timbrica",
    "picchi_spettrali": "Picchi spettrali principali",
    "densita_attivita": "Densità e attività sonora",
    "stima_qualitativa": "Stima qualitativa (euristica)",
    "ecoacustica": "Indici ecoacustici",
    "classificazione_semantica": "Classificazione semantica",
    "multicanale": "Analisi multicanale",
    "confronto_grm": "Confronto con profili GRM",
    "lettura_compositiva": "Lettura compositiva",
    "clap": "Auto-tagging CLAP (vocabolario italiano)",
    "dialoghi_trascritti": "Dialoghi trascritti",
    "sezioni_strutturali": "Sezioni strutturali",
    "narrativa": "Descrizione segmentata",
}

PARAMETRI = {
    "peak": "Picco",
    "rms": "RMS medio",
    "crest": "Fattore di cresta",
    "dr": "Gamma dinamica",
    "noise_floor": "Rumore di fondo stimato",
    "lufs": "LUFS integrato",
    "lra": "Gamma di loudness (LRA)",
    "true_peak": "Picco reale (true peak)",
    "clipping": "Clipping",
    "dc_offset": "Offset DC",
    "hum_50": "Ronzio 50 Hz",
    "hum_60": "Ronzio 60 Hz",
    "centroide": "Centroide spettrale",
    "rolloff": "Rolloff 85%",
    "flatness": "Piattezza spettrale",
    "zcr": "Tasso di attraversamenti zero",
    "onset_density": "Eventi rilevati",
    "aci": "Indice di complessità acustica (ACI)",
    "ndsi": "Indice differenza normalizzata soundscape (NDSI)",
    "h_entropy": "Entropia acustica (H)",
    "bi": "Indice bioacustico (BI)",
    "adi": "Indice di diversità acustica (ADI)",
    "aei": "Indice di uniformità acustica (AEI)",
}

MESSAGGI_SISTEMA = {
    "ffprobe_mancante": (
        "ffprobe non trovato. Installa ffmpeg prima di procedere: brew install ffmpeg"
    ),
    "claude_cli_mancante": (
        "Il comando claude non è nel PATH. Il CLI della skill procederà senza "
        "invocare l'agente compositivo. Il PDF finale avrà un placeholder nella "
        "sezione Lettura compositiva."
    ),
    "yamnet_precheck_applicato": (
        "Pre-check LUFS: il file è a {lufs:.1f} LUFS, sotto la soglia di "
        "{threshold:.0f} LUFS. Applicata normalizzazione temporanea di +{gain:.1f} dB "
        "in memoria per consentire la classificazione semantica. Il file originale "
        "non è stato modificato."
    ),
    "hum_baseline_nota": (
        "Hum check con baseline locale nelle bande 30-45 e 70-95 Hz, non globale. "
        "Previene falsi positivi su sorgenti tonali."
    ),
    "fonts_fallback": (
        "Font ABTEC40 non trovati in assets/fonts/. Uso fallback di sistema. "
        "Per la coerenza grafica, scarica Libre Baskerville e Source Sans Pro "
        "da Google Fonts in formato TTF."
    ),
}


def verdetto_hum(ratio_db: float) -> str:
    """Mappa ratio_db (picco Hum in dB sopra baseline locale) a verdetto italiano."""
    from .config import HUM_VERDICT_THRESHOLDS
    if ratio_db < HUM_VERDICT_THRESHOLDS["trascurabile"]:
        return VERDETTI_HUM["trascurabile"]
    if ratio_db < HUM_VERDICT_THRESHOLDS["presente"]:
        return VERDETTI_HUM["presente"]
    return VERDETTI_HUM["forte"]


def categoria_hifi(dynamic_range_db: float, flatness: float) -> tuple[str, int]:
    """Ritorna (categoria_testo, score 1-5)."""
    from .config import HIFI_DR_HIGH, HIFI_DR_MID, HIFI_FLATNESS_MAX
    if dynamic_range_db > HIFI_DR_HIGH and flatness < HIFI_FLATNESS_MAX:
        return CATEGORIE_HIFI["hifi"], 4
    if dynamic_range_db > HIFI_DR_MID:
        return CATEGORIE_HIFI["medio"], 3
    return CATEGORIE_HIFI["lofi"], 2


def categoria_densita(eventi_per_sec: float) -> str:
    from .config import ONSET_DENSITY_SPARSE, ONSET_DENSITY_DENSE
    if eventi_per_sec < ONSET_DENSITY_SPARSE:
        return DENSITA_EVENTI["sparsa"]
    if eventi_per_sec < ONSET_DENSITY_DENSE:
        return DENSITA_EVENTI["media"]
    return DENSITA_EVENTI["densa"]


def sanitize_italiano(text: str) -> str:
    """Rimuove em dash e li sostituisce con virgola + spazio.

    Da applicare a tutto il testo che finisce in output per PDF e markdown.
    """
    if not text:
        return text
    return text.replace("\u2014", ", ").replace("\u2013", "-").replace("--", ", ")
