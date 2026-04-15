"""Trascrizione dialoghi (v0.5.0).

Pipeline:
1. `speech_summary(waveform, sr, enable, duration_total_s)`:
   - Resample a 16 kHz (config.WHISPER_SR).
   - Pre-filtro Silero VAD standalone: se meno di
     `SILERO_VAD_MIN_TOTAL_SPEECH_S` secondi di parlato, ritorna
     skipped_reason='insufficient_speech' senza caricare Whisper.
   - Altrimenti: invoca SpeechTranscriber (faster-whisper large-v3,
     device cpu, compute_type int8, vad_filter=True per rimappatura
     timestamp assoluti automatica).
2. `translate_transcript(speech_dict)`:
   - No-op se language_detected == 'it'.
   - Altrimenti: chunking sopra config.TRANSLATION_CHUNK_THRESHOLD_CHARS,
     subprocess `claude -p --model <TRANSLATION_MODEL>` con prompt via
     stdin. Fallback a transcript originale se claude non in PATH o
     timeout, con translation_fallback=True e warning stderr.

CTranslate2 non supporta MPS: il device Whisper e' forzato a 'cpu' con
compute_type 'int8'. Su Apple Silicon M4 le ottimizzazioni NEON SIMD
danno ~15x realtime sul large-v3, adeguato per file fino a 60 min.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from . import config
from .device import log_device


_TRANSCRIBER_SINGLETON: "SpeechTranscriber | None" = None
_VAD_SINGLETON = None


@dataclass
class SpeechResult:
    """Output di `speech_summary`."""
    enabled: bool
    model_name: str = ""
    device: str = ""
    compute_type: str = ""
    language_detected: str = ""
    language_probability: float = 0.0
    duration_speech_s: float = 0.0
    duration_total_s: float = 0.0
    n_vad_segments: int = 0
    segments: list[dict] = field(default_factory=list)
    transcript: str = ""
    transcript_it: str = ""
    translation_model: str = ""
    translation_fallback: bool = False
    skipped_reason: str = ""
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _load_silero_vad():
    """Singleton module-level per Silero VAD."""
    global _VAD_SINGLETON
    if _VAD_SINGLETON is None:
        from silero_vad import load_silero_vad
        _VAD_SINGLETON = load_silero_vad(onnx=False)
    return _VAD_SINGLETON


def _vad_speech_segments(
    waveform_16k: np.ndarray,
) -> tuple[list[dict], float]:
    """Silero VAD standalone. Ritorna (list di {start_s, end_s}, durata_totale_s)."""
    import torch
    from silero_vad import get_speech_timestamps

    vad = _load_silero_vad()
    audio_tensor = torch.from_numpy(waveform_16k.astype(np.float32))
    ts = get_speech_timestamps(
        audio_tensor,
        vad,
        threshold=config.SILERO_VAD_THRESHOLD,
        sampling_rate=config.WHISPER_SR,
        min_speech_duration_ms=config.SILERO_VAD_MIN_SPEECH_MS,
        min_silence_duration_ms=config.SILERO_VAD_MIN_SILENCE_MS,
        return_seconds=True,
    )
    duration_speech_s = sum(float(t["end"]) - float(t["start"]) for t in ts)
    segments = [{"start_s": float(t["start"]), "end_s": float(t["end"])} for t in ts]
    return segments, duration_speech_s


class SpeechTranscriber:
    """Wrapper faster-whisper large-v3 con lazy load singleton."""

    def __init__(
        self,
        model_name: str = None,
        device: str = None,
        compute_type: str = None,
    ):
        self._model_name = model_name or config.WHISPER_MODEL
        self._device = device or config.WHISPER_DEVICE
        self._compute_type = compute_type or config.WHISPER_COMPUTE_TYPE
        self._model = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def device(self) -> str:
        return self._device

    @property
    def compute_type(self) -> str:
        return self._compute_type

    def _ensure_loaded(self):
        if self._model is not None:
            return
        from faster_whisper import WhisperModel
        self._model = WhisperModel(
            self._model_name,
            device=self._device,
            compute_type=self._compute_type,
        )
        log_device(
            f"Whisper {self._model_name}",
            f"{self._device} (compute_type={self._compute_type})",
        )

    def transcribe(self, waveform_16k: np.ndarray) -> dict:
        """Trascrive waveform mono 16 kHz. Ritorna dict serializzabile JSON."""
        self._ensure_loaded()
        segments_iter, info = self._model.transcribe(
            waveform_16k.astype(np.float32),
            beam_size=config.WHISPER_BEAM_SIZE,
            vad_filter=True,
            vad_parameters={
                "threshold": config.SILERO_VAD_THRESHOLD,
                "min_speech_duration_ms": config.SILERO_VAD_MIN_SPEECH_MS,
                "min_silence_duration_ms": config.SILERO_VAD_MIN_SILENCE_MS,
            },
            language_detection_segments=config.WHISPER_LANG_DETECT_SEGMENTS,
        )
        segments: list[dict] = []
        transcript_parts: list[str] = []
        for seg in segments_iter:
            text = seg.text.strip()
            if not text:
                continue
            segments.append(
                {
                    "t_start_s": round(float(seg.start), 3),
                    "t_end_s": round(float(seg.end), 3),
                    "text": text,
                }
            )
            transcript_parts.append(text)
        language = info.language or ""
        probability = float(info.language_probability or 0.0)
        if probability < config.WHISPER_LANG_CONF_WARN:
            print(
                f"[Whisper] Lingua '{language}' rilevata con probabilita' "
                f"bassa ({probability:.2f}): possibile audio multilingua",
                file=sys.stderr,
                flush=True,
            )
        return {
            "segments": segments,
            "transcript": "\n".join(transcript_parts),
            "language_detected": language,
            "language_probability": probability,
        }


def _get_transcriber() -> SpeechTranscriber:
    global _TRANSCRIBER_SINGLETON
    if _TRANSCRIBER_SINGLETON is None:
        _TRANSCRIBER_SINGLETON = SpeechTranscriber()
    return _TRANSCRIBER_SINGLETON


def speech_summary(
    waveform: np.ndarray | None,
    sr: int,
    enable: bool = False,
    duration_total_s: float = 0.0,
) -> dict:
    """Entry point. Ritorna dict serializzabile JSON (SpeechResult.to_dict())."""
    if not enable:
        return SpeechResult(enabled=False, reason="disabled").to_dict()

    if waveform is None or len(waveform) == 0:
        return SpeechResult(
            enabled=True, reason="empty_waveform", duration_total_s=duration_total_s
        ).to_dict()

    # Resample a 16 kHz per Silero VAD e Whisper
    target_sr = config.WHISPER_SR
    if sr != target_sr:
        import librosa
        waveform_16k = librosa.resample(
            waveform.astype(np.float32), orig_sr=sr, target_sr=target_sr
        )
    else:
        waveform_16k = waveform.astype(np.float32)

    # Pre-filtro Silero VAD standalone: saltiamo Whisper se parlato insufficiente
    vad_segments, duration_speech_s = _vad_speech_segments(waveform_16k)
    if duration_speech_s < config.SILERO_VAD_MIN_TOTAL_SPEECH_S:
        return SpeechResult(
            enabled=True,
            model_name=config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
            duration_speech_s=round(duration_speech_s, 2),
            duration_total_s=round(duration_total_s, 2),
            n_vad_segments=len(vad_segments),
            skipped_reason="insufficient_speech",
        ).to_dict()

    # Whisper con VAD interno per timestamp assoluti corretti
    transcriber = _get_transcriber()
    result = transcriber.transcribe(waveform_16k)

    return SpeechResult(
        enabled=True,
        model_name=transcriber.model_name,
        device=transcriber.device,
        compute_type=transcriber.compute_type,
        language_detected=result["language_detected"],
        language_probability=result["language_probability"],
        duration_speech_s=round(duration_speech_s, 2),
        duration_total_s=round(duration_total_s, 2),
        n_vad_segments=len(vad_segments),
        segments=result["segments"],
        transcript=result["transcript"],
    ).to_dict()


def _translate_chunk(
    text: str, model: str, timeout_s: int = None
) -> str:
    """Subprocess `claude -p --model <model>` con prompt via stdin.

    Il pattern e' quello di report_synthesizer::invoke_corpus_synthesizer.
    Non gestisce fallback: il chiamante deve avere gia' verificato
    `shutil.which('claude')`.
    """
    prompt = (
        "Traduci in italiano il seguente testo, preservando la struttura "
        "in paragrafi. Mantieni invariati i termini tecnici e i nomi propri. "
        "Output: solo la traduzione, senza introduzioni ne' commenti.\n\n"
        + text
    )
    timeout_s = timeout_s or config.TRANSLATION_TIMEOUT_S
    result = subprocess.run(
        ["claude", "-p", "--model", model],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout_s,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"claude -p returncode {result.returncode}: {result.stderr[:200]}"
        )
    return result.stdout.strip()


def _translate_long(text: str, model: str) -> str:
    """Chunking sopra soglia con overlap per continuita' stilistica."""
    threshold = config.TRANSLATION_CHUNK_THRESHOLD_CHARS
    if len(text) <= threshold:
        return _translate_chunk(text, model)
    size = config.TRANSLATION_CHUNK_SIZE_CHARS
    overlap = config.TRANSLATION_CHUNK_OVERLAP_CHARS
    chunks: list[str] = []
    translated_parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap if end < len(text) else end
    # Primo chunk: traduzione integrale. Chunk successivi: traduzione
    # completa, poi scartiamo la parte sovrapposta dalla seconda traduzione
    # in poi (l'overlap e' ~500 char in lingua origine, che corrisponde
    # approssimativamente a ~500 char in italiano).
    for i, chunk in enumerate(chunks):
        translated = _translate_chunk(chunk, model)
        if i == 0:
            translated_parts.append(translated)
        else:
            # Rimozione difensiva di un eventuale overlap duplicato:
            # tagliamo i primi overlap caratteri della traduzione
            # (approssimazione, l'allineamento esatto non e' garantito).
            if len(translated) > overlap:
                translated = translated[overlap:]
            translated_parts.append(translated)
    return "\n".join(translated_parts)


def check_speech_suggestion(
    semantic_res: dict,
    flag_active: bool,
    threshold_pct: float = None,
) -> float | None:
    """Scansiona semantic_res['classifier']['top_dominant_frames'] per un item
    con name='Speech' e pct > threshold_pct. Ritorna il pct (float) se match
    e flag NON attivo, altrimenti None.

    Permette di suggerire via stderr all'utente di rilanciare con --speech
    quando PANNs rileva parlato dominante nei frame.
    """
    if flag_active:
        return None
    threshold = (
        threshold_pct if threshold_pct is not None
        else config.SPEECH_SUGGEST_DOMINANT_PCT
    )
    top_dom = (semantic_res.get("classifier", {}) or {}).get(
        "top_dominant_frames", []
    )
    for item in top_dom:
        if item.get("name") == "Speech" and float(item.get("pct", 0)) > threshold:
            return float(item["pct"])
    return None


def translate_transcript(
    speech_dict: dict,
    target_lang: str = "it",
    model: str = None,
) -> dict:
    """Arricchisce speech_dict con transcript_it e flag traduzione.

    Ritorna il dict modificato (in-place safe: lavora su copia).
    """
    out = dict(speech_dict)
    if not out.get("enabled"):
        return out
    if out.get("skipped_reason"):
        return out
    transcript = out.get("transcript", "")
    if not transcript:
        return out

    model = model or config.TRANSLATION_MODEL
    language = out.get("language_detected", "")

    if language == target_lang:
        out["transcript_it"] = transcript
        out["translation_model"] = ""
        out["translation_fallback"] = False
        return out

    if shutil.which("claude") is None:
        print(
            "[speech] claude non in PATH: traduzione italiana saltata, "
            "trascritto originale usato",
            file=sys.stderr,
            flush=True,
        )
        out["transcript_it"] = transcript
        out["translation_model"] = ""
        out["translation_fallback"] = True
        return out

    try:
        out["transcript_it"] = _translate_long(transcript, model)
        out["translation_model"] = model
        out["translation_fallback"] = False
    except (subprocess.TimeoutExpired, RuntimeError) as e:
        print(
            f"[speech] Traduzione fallita ({type(e).__name__}: {e}), "
            "trascritto originale usato",
            file=sys.stderr,
            flush=True,
        )
        out["transcript_it"] = transcript
        out["translation_model"] = model
        out["translation_fallback"] = True

    return out
