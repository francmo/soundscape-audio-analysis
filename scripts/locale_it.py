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
    "executive_summary": "Sintesi",
    "partitura_grafica": "Partitura grafica",
    "overview_tecnica": "Overview tecnica",
    "appendice": "Appendice analitica",
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
    "spread": "Ampiezza spettrale",
    "rolloff": "Rolloff 85%",
    "flatness": "Piattezza spettrale",
    "flux": "Flusso spettrale",
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


# v0.13.0 (Intervento D addendum dossier P&T): etichette brevi italiane per
# signature_label a 4 dimensioni. Le forme estese restano in DENSITA_EVENTI
# (usate nella partitura grafica e nel PDF dettagliato); qui servono varianti
# compatte da incastrare in un'etichetta sotto i 50 caratteri.

SIGNATURE_CENTROID_BANDS = {
    "scura": "scura",          # centroide < 250 Hz, dominio sub-bass + bass
    "media": "media",          # centroide 250-1000 Hz, dominio low-mid
    "chiara": "chiara",        # centroide 1000-4000 Hz, dominio mid + high-mid
    "brillante": "brillante",  # centroide >= 4000 Hz, dominio presence + brilliance
}

SIGNATURE_DENSITY_SHORT = {
    "sparsa": "sparsa",
    "media": "media",
    "densa": "densa",
}

SIGNATURE_TONALITY_SHORT = {
    "molto_tonale": "molto tonale",
    "moderatamente_tonale": "moderatamente tonale",
    "tonale": "tonale",
    "tendenzialmente_tonale": "tendenzialmente tonale",
    "misto": "misto",
    "molto_rumoroso": "molto rumoroso",
}


def signature_centroid_band(centroid_hz: float) -> str:
    """Mappa il centroide spettrale in una delle 4 bande qualitative per
    signature_label: scura/media/chiara/brillante. Soglie in config.
    """
    from .config import (
        SIGNATURE_CENTROID_BAND_SCURO_MAX_HZ,
        SIGNATURE_CENTROID_BAND_MEDIO_MAX_HZ,
        SIGNATURE_CENTROID_BAND_CHIARO_MAX_HZ,
    )
    if centroid_hz < SIGNATURE_CENTROID_BAND_SCURO_MAX_HZ:
        return SIGNATURE_CENTROID_BANDS["scura"]
    if centroid_hz < SIGNATURE_CENTROID_BAND_MEDIO_MAX_HZ:
        return SIGNATURE_CENTROID_BANDS["media"]
    if centroid_hz < SIGNATURE_CENTROID_BAND_CHIARO_MAX_HZ:
        return SIGNATURE_CENTROID_BANDS["chiara"]
    return SIGNATURE_CENTROID_BANDS["brillante"]


def signature_density(eventi_per_sec: float) -> str:
    """Variante breve di categoria_densita per signature_label (sparsa/media/
    densa, senza descrittore espanso). Stesse soglie di ONSET_DENSITY_*.
    """
    from .config import ONSET_DENSITY_SPARSE, ONSET_DENSITY_DENSE
    if eventi_per_sec < ONSET_DENSITY_SPARSE:
        return SIGNATURE_DENSITY_SHORT["sparsa"]
    if eventi_per_sec < ONSET_DENSITY_DENSE:
        return SIGNATURE_DENSITY_SHORT["media"]
    return SIGNATURE_DENSITY_SHORT["densa"]


def signature_tonality(flatness: float) -> str:
    """Mappa flatness in una delle 6 categorie tonale. Soglie raffinate
    v0.13.0 (pattern 6 caso B): la soglia storica 0.05 era troppo alta
    e classificava come "tonale" file urbani con flatness 0.007-0.013 che
    sono percettivamente noisy. Ora "molto tonale" e' riservato a flatness
    sub-0.005 (sinusoidi pure, droni armonici stretti).
    """
    from .config import (
        FLATNESS_MOLTO_TONALE_MAX,
        FLATNESS_MODERATAMENTE_TONALE_MAX,
        FLATNESS_TONALE_MAX,
        FLATNESS_TENDENZIALMENTE_TONALE_MAX,
        FLATNESS_MISTO_MAX,
    )
    if flatness < FLATNESS_MOLTO_TONALE_MAX:
        return SIGNATURE_TONALITY_SHORT["molto_tonale"]
    if flatness < FLATNESS_MODERATAMENTE_TONALE_MAX:
        return SIGNATURE_TONALITY_SHORT["moderatamente_tonale"]
    if flatness < FLATNESS_TONALE_MAX:
        return SIGNATURE_TONALITY_SHORT["tonale"]
    if flatness < FLATNESS_TENDENZIALMENTE_TONALE_MAX:
        return SIGNATURE_TONALITY_SHORT["tendenzialmente_tonale"]
    if flatness < FLATNESS_MISTO_MAX:
        return SIGNATURE_TONALITY_SHORT["misto"]
    return SIGNATURE_TONALITY_SHORT["molto_rumoroso"]


def sanitize_italiano(text: str) -> str:
    """Rimuove em dash e li sostituisce con virgola + spazio.

    Da applicare a tutto il testo che finisce in output per PDF e markdown.
    """
    if not text:
        return text
    return text.replace("\u2014", ", ").replace("\u2013", "-").replace("--", ", ")
