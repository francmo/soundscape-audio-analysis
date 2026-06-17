"""Riduzione del summary per il payload dell'agente compositivo (v0.2.2).

Invece di passare tutto il summary JSON all'agente (che includeva la
timeline completa di PANNs/YAMNet e poteva far scattare timeout), si
costruisce un payload ridotto focalizzato su quello che serve per la
lettura critica: metadata essenziali, livelli, hum overall, spectral
macro, top-10 PANNs globali, top-20 CLAP globali, narrativa markdown.

v0.4.0: aggiunto `clap.academic_hints` con distribuzioni pesate per score
cosine su tassonomie Schafer/Truax/Krause/Schaeffer/Smalley/Chion/Westerkamp,
calcolate da `scripts.clap_mapping.aggregate_academic_hints`. Se il mapping
non e caricabile (file mancante o malformato), il campo ritorna
`{"available": False, "reason": "..."}` senza rompere la pipeline.

v0.5.0: aggiunto campo `speech` quando la trascrizione e' attiva.
Contiene lingua rilevata, durate, trascritto italiano capped a 3000 char
e top-15 segmenti VAD. Se speech non abilitato o skipped, il campo resta
compatto con solo enabled=False + skipped_reason.

v0.5.3: aggiunto campo `signature` (feature di alto livello sintetizzate
per facilitare il riconoscimento di brani noti del repertorio): durata
MM:SS, dynamic range, flatness, Krause dominante, top-5 PANNs frame
dominanti, top-5 CLAP prompts, presenza di parlato. L'agente usa la
signature nel primo passo "Identificazione preliminare" (v0.5.3
obbligatorio).
"""
from __future__ import annotations
from pathlib import Path

from . import config
from .serialization import dump as dump_json


def _compute_inference_confidence(
    classifier: dict,
    clap: dict,
) -> dict:
    """Concentrazione delle distribuzioni top-K PANNs/CLAP (v0.12.6, P6 A).

    Misura quanto i classificatori convergono su pochi tag dominanti vs si
    disperdono su molti. Concentrazione alta -> high confidence sulle
    inferenze di ambientazione costruite dall'agente. Concentrazione bassa
    -> tag dispersi, agente deve usare marcatori di ipotesi.

    Formula (PANNs): concentration = top1_pct / sum(top1, top2, top3).
    Range teorico: 0.33 (perfettamente dispersi) -> 1.0 (top1 unico).

    Formula (CLAP): concentration = top1_score / sum(top1, top2, top3).
    Stesso range teorico.

    Soglie discrete: < 0.5 = low, 0.5-0.75 = medium, > 0.75 = high.
    Confidence aggregata = peggiore (min) fra PANNs e CLAP, perche' inferenze
    di scena richiedono accordo fra le due fonti.
    """
    def _conc(values: list[float]) -> float:
        vs = [float(v or 0) for v in values[:3] if (v or 0) > 0]
        if not vs:
            return 0.0
        total = sum(vs)
        if total < 1e-9:
            return 0.0
        return float(vs[0] / total)

    def _bucket(conc: float) -> str:
        if conc >= 0.75:
            return "high"
        if conc >= 0.5:
            return "medium"
        return "low"

    panns_top = (classifier.get("top_dominant_frames", []) or [])[:3]
    panns_pcts = [t.get("pct", 0) for t in panns_top]
    panns_conc = _conc(panns_pcts)

    clap_top = (clap.get("top_global", []) or [])[:3]
    clap_scores = [t.get("score", 0) for t in clap_top]
    clap_conc = _conc(clap_scores)

    panns_bucket = _bucket(panns_conc)
    clap_bucket = _bucket(clap_conc)

    rank = {"high": 3, "medium": 2, "low": 1}
    aggregate = min(panns_bucket, clap_bucket, key=lambda b: rank[b])

    return {
        "panns_concentration": round(panns_conc, 3),
        "panns_bucket": panns_bucket,
        "clap_concentration": round(clap_conc, 3),
        "clap_bucket": clap_bucket,
        "aggregate": aggregate,
        "method": "top1 / (top1 + top2 + top3); PANNs su pct dei dominant_frames, CLAP su score dei top_global",
    }


def _build_signature(
    meta: dict,
    tech: dict,
    spec: dict,
    classifier: dict,
    clap: dict,
    speech: dict,
) -> dict:
    """Feature di alto livello sintetizzate per il riconoscimento brani (v0.5.3).

    Non inventa etichette (es. "porto peschereccio"): fornisce all'agente
    dati grezzi ordinati in modo leggibile. Il riconoscimento del brano e'
    responsabilita' del ragionamento LLM, non della skill.

    v0.12.6 (P6 caso A): aggiunto `inference_confidence` che misura
    la concentrazione delle distribuzioni top-K. L'agente usa il valore
    aggregato per scegliere il registro epistemico delle inferenze di
    ambientazione (dichiarativo vs ipotetico).
    """
    duration_s = float(meta.get("duration_s", 0) or 0)
    mins = int(duration_s // 60)
    secs = int(round(duration_s % 60))
    duration_mmss = f"{mins}:{secs:02d}"

    levels = (tech or {}).get("levels", {}) or {}
    timbre = (spec or {}).get("timbre", {}) or {}

    top_frames = (classifier.get("top_dominant_frames", []) or [])[:5]
    top_clap = (clap.get("top_global", []) or [])[:5]

    academic = clap.get("academic_hints") or {}
    krause_dom = None
    if isinstance(academic, dict) and academic.get("available"):
        krause_dom = ((academic.get("krause") or {}).get("dominant") or {}).get("value")

    return {
        "duration_mmss": duration_mmss,
        "duration_s": duration_s,
        "dynamic_range_db": levels.get("dynamic_range_db"),
        "integrated_lufs": (tech or {}).get("lufs", {}).get("integrated_lufs"),
        "flatness_mean": timbre.get("spectral_flatness"),
        "krause_dominant": krause_dom,
        "top_panns_dominant_frames": [
            {"name": f.get("name"), "pct": f.get("pct")} for f in top_frames
        ],
        "top_clap_prompts": [
            {
                "prompt": t.get("prompt", ""),
                "category": t.get("category", ""),
                "score": round(float(t.get("score", 0) or 0), 3),
            }
            for t in top_clap
        ],
        "speech_presence": {
            "enabled": bool(speech.get("enabled", False)),
            "duration_speech_s": float(speech.get("duration_speech_s", 0) or 0),
            "language_detected": speech.get("language_detected", ""),
        },
        "user_attribution": meta.get("user_known_piece", ""),
        "inference_confidence": _compute_inference_confidence(classifier, clap),
    }


def _compute_italian_context(speech: dict, hum: dict, clap: dict) -> dict:
    """v0.8.1: flag deterministico di "contesto italiano" per regolare le
    attribuzioni stilistiche dell'agente.

    Ritorna `{is_italian_context: bool, reasons: [str]}` con motivazione
    ispezionabile. Il flag e' True solo se CO-occorrono almeno 2 dei 4
    indicatori, evitando che l'hum 50 Hz da solo forzi l'agente verso
    la Fonologia RAI.

    Indicatori:
    1. `speech_italian`: speech.language_detected == 'it' con probabilita'
       >= 0.80.
    2. `hum_50hz_dominant`: hum 50 Hz "presente" nel verdict overall (hum
       60 Hz da solo esclude: rete americana).
    3. `italian_clap_markers`: almeno 1 tag CLAP nei top-20 con
       geo_specific=True e categoria 'paesaggi italiani specifici'.
    4. `italian_speech_content`: trascrizione speech (se presente) contiene
       parole italiane frequenti (la, il, che, non, è, un).

    L'agente usa questo flag per la regola "hum analogico != Fonologia RAI
    senza corroborazione italiana" documentata nel prompt v0.8.1.
    """
    reasons: list[str] = []
    lang = str(speech.get("language_detected", "") or "").lower()
    lang_prob = float(speech.get("language_probability", 0) or 0)
    speech_italian = (lang == "it" and lang_prob >= 0.80)
    if speech_italian:
        reasons.append("speech_italian")

    hum_overall = str(hum.get("overall_verdict", "") or "").lower()
    hum_50 = False
    peaks = hum.get("peaks") or []
    for p in peaks:
        if p.get("target_hz") == 50 and p.get("verdict") == "presente":
            hum_50 = True
            break
    if hum_50 and "presente" in hum_overall:
        reasons.append("hum_50hz_dominant")

    clap_italian = False
    for t in (clap.get("top_global") or [])[:20]:
        if t.get("geo_specific") is True and "italian" in str(t.get("category", "")).lower():
            clap_italian = True
            break
    if clap_italian:
        reasons.append("italian_clap_markers")

    transcript = str(speech.get("transcript_it", "") or "").lower()
    italian_stopwords = {" la ", " il ", " che ", " non ", " un ", " una ", " del ", " della ", "è "}
    if transcript and sum(1 for sw in italian_stopwords if sw in transcript) >= 3:
        reasons.append("italian_speech_content")

    is_italian = len(reasons) >= 2
    return {"is_italian_context": is_italian, "reasons": reasons}


def build_agent_payload(summary: dict, narrative_md: str) -> dict:
    """Estrae il payload minimo ma sufficiente per l'agente."""
    meta = summary.get("metadata", {})
    tech = summary.get("technical", {})
    hum = summary.get("hum", {})
    spec = summary.get("spectral", {})
    eco = summary.get("ecoacoustic", {})
    classifier = (summary.get("semantic", {}) or {}).get("classifier", {}) or {}
    clap = summary.get("clap", {}) or {}
    speech = summary.get("speech", {}) or {}
    speech_mediation = summary.get("speech_mediation", {}) or {}
    mc = summary.get("multichannel", {}) or {}
    structure = summary.get("structure", {}) or {}

    italian_ctx = _compute_italian_context(speech, hum, clap)

    payload = {
        "file": {
            "name": meta.get("filename", ""),
            "duration_s": meta.get("duration_s", 0),
            "sample_rate": meta.get("sr", 0),
            "channels": meta.get("channels", 0),
            "layout": (mc or {}).get("layout") or "stereo",
        },
        "italian_context": italian_ctx,
        "signature": _build_signature(meta, tech, spec, classifier, clap, speech),
        "technical": {
            "peak_dbfs": tech.get("levels", {}).get("peak_dbfs"),
            "rms_dbfs": tech.get("levels", {}).get("rms_dbfs"),
            "crest_db": tech.get("levels", {}).get("crest_db"),
            "dynamic_range_db": tech.get("levels", {}).get("dynamic_range_db"),
            "noise_floor_db": tech.get("levels", {}).get("noise_floor_db"),
            "integrated_lufs": tech.get("lufs", {}).get("integrated_lufs"),
            "true_peak_db": tech.get("lufs", {}).get("true_peak_db"),
            "lra": tech.get("lufs", {}).get("lra"),
            "clipping_verdict": tech.get("clipping", {}).get("verdict"),
            "dc_offset_verdict": tech.get("dc_offset", {}).get("verdict"),
            "hum_overall": hum.get("overall_verdict", "n.d."),
        },
        "spectral": {
            "bands_schafer_pct": {
                k: v.get("energy_pct") for k, v in (spec.get("bands_schafer") or {}).items()
            },
            "bands_schafer_alert": spec.get("bands_schafer_alert"),
            "centroid_hz": (spec.get("timbre") or {}).get("spectral_centroid_hz"),
            "spread_hz": (spec.get("timbre") or {}).get("spectral_spread_hz"),
            "rolloff_hz": (spec.get("timbre") or {}).get("spectral_rolloff_hz"),
            "flatness": (spec.get("timbre") or {}).get("spectral_flatness"),
            "flux": (spec.get("timbre") or {}).get("spectral_flux"),
            "hi_fi_lo_fi": spec.get("hifi_lofi", {}),
            "top_peaks_hz": spec.get("top_peaks_hz", []),
            "onsets": spec.get("onsets", {}),
        },
        "ecoacoustic": {
            "aci": eco.get("aci"),
            "ndsi": (eco.get("ndsi") or {}).get("ndsi"),
            "h_total": (eco.get("h_entropy") or {}).get("h_total"),
            "bi": eco.get("bi"),
        },
        "classifier": {
            "model_name": classifier.get("model_name"),
            "top_global": classifier.get("top_global", [])[:10],
            "top_dominant_frames": classifier.get("top_dominant_frames", [])[:8],
        },
        "clap": {
            "enabled": clap.get("enabled", False),
            "model_name": clap.get("model_name"),
            "vocabulary_size": clap.get("vocabulary_size"),
            "vocabulary_version": clap.get("vocabulary_version"),
            "academic_mapping_version": clap.get("academic_mapping_version", ""),
            "top_global": clap.get("top_global", [])[:20],
            "academic_hints": clap.get("academic_hints", {"available": False}),
        },
        "speech": {
            "enabled": speech.get("enabled", False),
            "model_name": speech.get("model_name", ""),
            "language_detected": speech.get("language_detected", ""),
            "language_probability": speech.get("language_probability", 0),
            "duration_speech_s": speech.get("duration_speech_s", 0),
            "duration_total_s": speech.get("duration_total_s", 0),
            "n_vad_segments": speech.get("n_vad_segments", 0),
            "transcript_it": (speech.get("transcript_it") or "")[:3000],
            "segments": speech.get("segments", [])[:15],
            "skipped_reason": speech.get("skipped_reason", ""),
            "translation_fallback": speech.get("translation_fallback", False),
        },
        "structure": {
            "enabled": structure.get("enabled", False),
            "n_sections": structure.get("n_sections", 0),
            "n_sub_sections": structure.get("n_sub_sections", 0),
            "sections": structure.get("sections", [])[:8],
        },
        "aural_form": {
            "time_fields": (summary.get("time_fields") or [])[:24],
            "dynamic_form": _compact_dynamic_form(summary.get("dynamic_form")),
            "suggested_layers": (summary.get("suggested_layers") or [])[:8],
        },
        "speech_mediation": {
            "enabled": speech_mediation.get("enabled", False),
            "speech_dominant_pct": speech_mediation.get("speech_dominant_pct"),
            "global": speech_mediation.get("global"),
            "reason": speech_mediation.get("reason", ""),
        },
        "narrative_markdown": narrative_md,
    }
    return payload


def _compact_dynamic_form(df: dict | None, max_points: int = 12) -> dict | None:
    """Forma dinamica ridotta per l'agente: peak + contorno grossolano.

    L'energia piena (fino a 500 punti) e' eccessiva per il payload: si tiene
    peakSec, la risoluzione e un contorno sotto-campionato a max_points punti.
    """
    if not df:
        return None
    energy = df.get("energy") or []
    if len(energy) > max_points:
        step = len(energy) / max_points
        idxs = sorted({int(i * step) for i in range(max_points)})
        contour = [energy[i] for i in idxs if i < len(energy)]
    else:
        contour = energy
    return {
        "resolution_hz": df.get("resolutionHz"),
        "unit": df.get("unit"),
        "peak_sec": df.get("peakSec"),
        "n_points_full": len(energy),
        "contour": contour,
    }


def write_agent_payload(summary: dict, narrative_md: str, out_path: Path) -> Path:
    payload = build_agent_payload(summary, narrative_md)
    dump_json(payload, out_path)
    return out_path
