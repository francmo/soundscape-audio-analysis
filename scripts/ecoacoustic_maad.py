"""Thin wrapper sopra scikit-maad 1.4.3 per indici ecoacustici (v0.9.0 Step A).

Wrapper minimale che mappa i 5 indici canonici (ACI, NDSI, H, BI, ADI/AEI) alle
funzioni peer-reviewed di scikit-maad (Ulloa et al. 2021, SoftwareX, DOI
10.1016/j.softx.2021.100720). L'output API pubblica (dict ritornato da
`ecoacoustic_summary_maad`) e' identico a quello della versione legacy;
differisce solo l'engine numerico.

API v1.4.3 usata (ispezionata e verificata, NON assumere nomi):
- `maad.sound.spectrogram(x, fs, nperseg, noverlap, mode='psd')` → (Sxx, tn, fn, ext)
- `maad.features.acoustic_complexity_index(Sxx)` → (ACI_xx, ACI_per_bin, ACI_total)
- `maad.features.soundscape_index(Sxx_power, fn, flim_bioPh, flim_antroPh)` → (NDSI, rBA, AnthroPh, BioPh)
- `maad.features.temporal_entropy(s, compatibility='QUT')` → float
- `maad.features.spectral_entropy(Sxx, fn, display=False)` → (EAS, ECU, ECV, EPS, EPS_KURT, EPS_SKEW)
- `maad.features.bioacoustics_index(Sxx, fn, flim)` → float
- `maad.features.acoustic_diversity_index(Sxx, fn, fmax, bin_step, dB_threshold, index)` → float
- `maad.features.acoustic_eveness_index(Sxx, fn, fmax, bin_step, dB_threshold)` → float

Note metodologiche:
- ACI totale = terzo elemento della tupla (scalare, Pieretti 2011).
- NDSI = primo elemento della tupla (Kasten 2012).
- H = Ht * Hf dove Ht = `temporal_entropy` e Hf = EAS (primo elemento di
  `spectral_entropy`, "Entropy of Average Spectrum", corrispondente al H
  spettrale classico Sueur 2008).
- `acoustic_entropy` come funzione unica NON ESISTE in maad 1.4.3: va composta.
- Default parametri (banda, finestra, soglia) allineati a quelli del legacy
  per massimizzare parity.
"""
from __future__ import annotations

import numpy as np

from . import config


def _compute_spectrogram(y: np.ndarray, sr: int, n_fft: int = 2048):
    """Spettrogramma PSD + array frequenze via maad.sound.spectrogram.

    Garantisce formato coerente (Sxx, fn) per tutte le funzioni maad.features
    che seguono. Modalita' 'psd' (power spectral density).
    """
    from maad.sound import spectrogram
    hop = n_fft // 2
    Sxx, tn, fn, _ = spectrogram(y, fs=sr, nperseg=n_fft, noverlap=hop, mode="psd")
    return Sxx, fn


_ENERGY_FLOOR = 1e-12


def _is_silent(Sxx: np.ndarray) -> bool:
    """True se lo spettrogramma e' piatto/nullo (silenzio digitale o near-floor).

    Guard contro divisioni per zero in maad.features.* (ACI, NDSI, BI).
    Le funzioni maad 1.4.3 non gestiscono internamente il caso `sum(Sxx)==0`
    e producono NaN / RuntimeWarning: restituire 0.0 sintatticamente corretto
    preserva l'API legacy (che ritorna 0 su silenzio digitale)."""
    return bool(np.sum(Sxx) < _ENERGY_FLOOR)


def compute_aci(y: np.ndarray, sr: int,
                j_seconds: float = 5.0,  # ignorato in maad 1.4.3 (non esposto)
                min_freq: float = 2000,
                max_freq: float = 8000,
                n_fft: int = 2048) -> float:
    """ACI (Pieretti, Farina, Morri 2011) via scikit-maad.

    Restringe lo spettrogramma alla banda biofonica prima del calcolo per
    coerenza col legacy (che applica la stessa maschera). Il parametro
    `j_seconds` del legacy non e' esposto in maad 1.4.3 (ACI si calcola
    sull'intera durata); il parametro e' accettato per compatibilita' di
    firma ma ignorato.
    """
    from maad.features import acoustic_complexity_index
    Sxx, fn = _compute_spectrogram(y, sr, n_fft=n_fft)
    band = (fn >= min_freq) & (fn <= max_freq)
    if not band.any():
        return 0.0
    Sxx_band = Sxx[band, :]
    if _is_silent(Sxx_band):
        return 0.0
    _, _, aci_total = acoustic_complexity_index(Sxx_band)
    if np.isnan(aci_total) or np.isinf(aci_total):
        return 0.0
    return round(float(aci_total), 2)


def compute_ndsi(y: np.ndarray, sr: int,
                 antro_band: tuple[float, float] = config.ECO_ANTHROPOPHONY_BAND,
                 bio_band: tuple[float, float] = config.ECO_BIOPHONY_BAND,
                 n_fft: int = 2048) -> dict:
    """NDSI (Kasten et al. 2012) via scikit-maad.

    Dict identico al legacy. Nota: `soundscape_index` di maad ritorna
    (NDSI, rBA, AnthroPh, BioPh) in quest'ordine.
    """
    from maad.features import soundscape_index
    Sxx, fn = _compute_spectrogram(y, sr, n_fft=n_fft)
    if _is_silent(Sxx):
        return {
            "ndsi": 0.0,
            "biophony_energy": 0.0,
            "anthropophony_energy": 0.0,
            "biophony_band_hz": list(bio_band),
            "anthropophony_band_hz": list(antro_band),
        }
    ndsi, _rBA, anthph, bioph = soundscape_index(
        Sxx, fn,
        flim_bioPh=tuple(bio_band),
        flim_antroPh=tuple(antro_band),
    )
    def _safe(v):
        return 0.0 if (np.isnan(v) or np.isinf(v)) else float(v)
    return {
        "ndsi": round(_safe(ndsi), 3),
        "biophony_energy": round(_safe(bioph), 3),
        "anthropophony_energy": round(_safe(anthph), 3),
        "biophony_band_hz": list(bio_band),
        "anthropophony_band_hz": list(antro_band),
    }


def compute_entropy_h(y: np.ndarray, sr: int, n_fft: int = 2048) -> dict:
    """H = Ht * Hf (Sueur et al. 2008) composto da temporal_entropy +
    (1 - EAS) di scikit-maad.

    **Nota di mapping critica** (v0.9.0 Step A):
    maad `spectral_entropy` segue Towsey 2017 e ritorna 6 grandezze fra cui
    EAS (Entropy of Average Spectrum). EAS di Towsey misura la **deviazione
    dell'entropia dalla distribuzione uniforme**: valore ALTO su spettro
    concentrato (sinusoide), BASSO su spettro uniforme (rumore bianco).

    H_spectral classico Sueur 2008 misura invece direttamente la
    **uniformita' della distribuzione spettrale**: ALTO su rumore, BASSO
    su sinusoide. Sono complementari: verificato algebricamente su
    sine/noise che `H_Sueur = 1 - EAS` (delta < 1e-3).

    Il wrapper applica la trasformazione `1 - EAS` per mantenere la
    convenzione Sueur usata dalla skill (e citata nel report PDF).

    `acoustic_entropy` come funzione unica non esiste in maad 1.4.3:
    H_total = Ht * Hf va composto manualmente.
    """
    from maad.features import temporal_entropy, spectral_entropy
    Sxx, fn = _compute_spectrogram(y, sr, n_fft=n_fft)
    if _is_silent(Sxx):
        return {"h_total": 0.0, "h_temporal": 0.0, "h_spectral": 0.0}
    H_t = float(temporal_entropy(y, compatibility="QUT"))
    if not np.isfinite(H_t):
        # Fallback: maad 1.4.3 temporal_entropy puo' andare in NaN su audio
        # lungo (overflow precisione numerica nella somma envelope). Ripiego
        # sul calcolo manuale Sueur identico a quello legacy, preservando la
        # stessa scala [0, 1]. Osservato su Cusack SFDP Vol.1 (55 min),
        # Lockwood Danube (2h29), Lopez Untitled #104 (43 min), ecc.
        env = np.abs(y.astype(np.float64))
        env_sum = env.sum() + 1e-12
        p_t = env / env_sum
        H_t = float(-np.sum(p_t * np.log2(p_t + 1e-12)) / np.log2(max(len(env), 2)))
    se_tuple = spectral_entropy(Sxx, fn, display=False)
    # (EAS, ECU, ECV, EPS, EPS_KURT, EPS_SKEW). EAS convertito a Sueur: 1-EAS.
    eas = float(se_tuple[0]) if isinstance(se_tuple, tuple) else float(se_tuple)
    if not np.isfinite(eas):
        eas = 1.0  # worst case: H_f = 0
    H_f = 1.0 - eas
    H = H_t * H_f
    return {
        "h_total": round(H, 4),
        "h_temporal": round(H_t, 4),
        "h_spectral": round(H_f, 4),
    }


def compute_bioacoustic_index(y: np.ndarray, sr: int,
                              lo: float = 2000, hi: float = 8000,
                              n_fft: int = 2048) -> float:
    """BI (Boelman et al. 2007) via scikit-maad, compatibilita' soundecology R."""
    from maad.features import bioacoustics_index
    Sxx, fn = _compute_spectrogram(y, sr, n_fft=n_fft)
    if _is_silent(Sxx):
        return 0.0
    bi = bioacoustics_index(Sxx, fn, flim=(lo, hi), R_compatible="soundecology")
    if np.isnan(bi) or np.isinf(bi):
        return 0.0
    return round(float(bi), 2)


def compute_adi_aei(y: np.ndarray, sr: int,
                    max_freq: float = 10000,
                    db_threshold: float = -50.0,
                    freq_step: float = 1000.0,
                    n_fft: int = 2048) -> dict:
    """ADI/AEI (Villanueva-Rivera et al. 2011) via scikit-maad.

    `bin_step` parametro di maad corrisponde a `freq_step` del legacy.
    Default AEI in maad e' bin_step=500; lo forziamo a `freq_step` per
    coerenza col legacy.
    """
    from maad.features import acoustic_diversity_index, acoustic_eveness_index
    Sxx, fn = _compute_spectrogram(y, sr, n_fft=n_fft)
    max_f = float(min(max_freq, sr / 2))
    adi = acoustic_diversity_index(
        Sxx, fn,
        fmax=max_f,
        bin_step=freq_step,
        dB_threshold=db_threshold,
        index="shannon",
    )
    aei = acoustic_eveness_index(
        Sxx, fn,
        fmax=max_f,
        bin_step=freq_step,
        dB_threshold=db_threshold,
    )
    n_bands = int(max_f // freq_step)
    return {
        "adi": round(float(adi), 4),
        "aei": round(float(aei), 4),
        "bands_count": n_bands,
        "freq_step_hz": freq_step,
        "db_threshold": db_threshold,
    }


def ecoacoustic_summary_maad(y: np.ndarray, sr: int, extended: bool = False) -> dict:
    """Dispatcher wrapper: produce il dict standard di indici ecoacustici
    sfruttando scikit-maad 1.4.3.

    Output API identico a `_ecoacoustic_summary_legacy` di `ecoacoustic.py`.
    """
    out = {
        "aci": compute_aci(y, sr),
        "ndsi": compute_ndsi(y, sr),
        "h_entropy": compute_entropy_h(y, sr),
        "bi": compute_bioacoustic_index(y, sr),
    }
    if extended:
        out["adi_aei"] = compute_adi_aei(y, sr)
    return out
