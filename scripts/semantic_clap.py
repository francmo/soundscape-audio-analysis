"""Auto-tagging semantico con LAION-CLAP su vocabolario italiano.

v0.2.1: introduce tagging empirico per segmento di 10s. Per ogni finestra
calcola la similarità coseno fra embedding audio e embedding di 70 prompt
italiani (editabili in `references/clap_vocabulary_it.json`) e restituisce
top-K tag. Embedding audio e prompt salvati nel summary (base64 float16)
per ricerca semantica futura.

Import lazy di torch, laion_clap, transformers per non pagare ~1 GB al
boot del CLI.
"""
from __future__ import annotations
import base64
import os
import warnings
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import numpy as np

os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
warnings.filterwarnings("ignore", category=FutureWarning)

from . import config
from .device import resolve_device, log_device
from .serialization import load as load_json


CLAP_CHECKPOINT_DIR = Path.home() / ".cache" / "clap"
CLAP_CHECKPOINT_FILE = CLAP_CHECKPOINT_DIR / "music_audioset_epoch_15_esc_90.14.pt"
VOCAB_PATH = config.REFERENCES_DIR / "clap_vocabulary_it.json"

_CLAP_MODEL_SINGLETON = None
_CLAP_DEVICE = None


@dataclass
class ClapResult:
    """Output di `clap_summary`."""
    enabled: bool
    model_name: str = ""
    device: str = ""
    vocabulary_size: int = 0
    vocabulary_version: str = ""
    academic_mapping_version: str = ""
    segment_seconds: float = 0.0
    timeline: list[dict] = field(default_factory=list)
    top_global: list[dict] = field(default_factory=list)
    academic_hints: dict = field(default_factory=dict)
    embeddings_audio_b64: str = ""
    embeddings_prompts_b64: str = ""
    embeddings_shape: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _ensure_checkpoint() -> Path:
    """Scarica il checkpoint CLAP la prima volta (~400 MB)."""
    import urllib.request
    CLAP_CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    if not CLAP_CHECKPOINT_FILE.exists():
        url = config.CLAP_CHECKPOINT_URL
        urllib.request.urlretrieve(url, str(CLAP_CHECKPOINT_FILE))
    return CLAP_CHECKPOINT_FILE


def load_clap_model(device: str | None = None):
    """Carica il modello CLAP in singleton. Idempotente."""
    global _CLAP_MODEL_SINGLETON, _CLAP_DEVICE
    if _CLAP_MODEL_SINGLETON is not None:
        return _CLAP_MODEL_SINGLETON, _CLAP_DEVICE

    import torch
    import laion_clap

    resolved = resolve_device(device or config.SEMANTIC_DEVICE)
    ckpt = str(_ensure_checkpoint())

    # amodel 'HTSAT-base' matcha il checkpoint music_audioset_epoch_15_esc_90
    model = laion_clap.CLAP_Module(enable_fusion=False, amodel="HTSAT-base")
    try:
        model.load_ckpt(ckpt)
    except Exception as e:
        raise RuntimeError(f"Impossibile caricare checkpoint CLAP da {ckpt}: {e}") from e

    # Sposta su device se possibile. laion_clap non espone API pulita per
    # il move, quindi usiamo l'attributo .model interno.
    try:
        if resolved != "cpu":
            torch_device = torch.device(resolved)
            model.model.to(torch_device)
            _CLAP_DEVICE = resolved
        else:
            _CLAP_DEVICE = "cpu"
    except Exception:
        _CLAP_DEVICE = "cpu"

    _CLAP_MODEL_SINGLETON = model
    log_device("LAION-CLAP", _CLAP_DEVICE)
    return model, _CLAP_DEVICE


def load_vocabulary(path: Path | None = None) -> dict:
    """Carica il vocabolario italiano dei prompt."""
    return load_json(path or VOCAB_PATH)


def embed_prompts(prompts: list[str], device: str | None = None) -> np.ndarray:
    """Forward testuale di CLAP su una lista di prompt."""
    model, dev = load_clap_model(device=device)
    # L'API laion_clap: get_text_embedding(list_of_strings)
    embeddings = model.get_text_embedding(prompts, use_tensor=False)
    return np.asarray(embeddings, dtype=np.float32)


def embed_audio_segments(
    waveform: np.ndarray,
    sr: int,
    segment_seconds: float = config.CLAP_SEGMENT_S,
    target_sr: int = 48000,
) -> tuple[np.ndarray, list[tuple[float, float]]]:
    """Spezza l'audio in segmenti e calcola embedding CLAP per ognuno.

    CLAP richiede 48 kHz mono float32. Resample interno.
    """
    import librosa
    model, _dev = load_clap_model()

    if sr != target_sr:
        waveform = librosa.resample(waveform, orig_sr=sr, target_sr=target_sr)
        sr = target_sr

    chunk_samples = int(segment_seconds * sr)
    n_chunks = max(1, int(np.ceil(len(waveform) / chunk_samples)))

    bounds: list[tuple[float, float]] = []
    embeddings: list[np.ndarray] = []
    for i in range(n_chunks):
        a = i * chunk_samples
        b = min(a + chunk_samples, len(waveform))
        chunk = waveform[a:b]
        if len(chunk) < sr * 0.5:
            continue
        # CLAP vuole shape (1, samples) float32
        chunk_batch = chunk[np.newaxis, :].astype(np.float32)
        emb = model.get_audio_embedding_from_data(x=chunk_batch, use_tensor=False)
        embeddings.append(np.asarray(emb[0], dtype=np.float32))
        bounds.append((a / sr, b / sr))

    if not embeddings:
        return np.zeros((0, 512), dtype=np.float32), []
    return np.stack(embeddings, axis=0), bounds


def tag_segments(
    audio_emb: np.ndarray,
    prompt_emb: np.ndarray,
    prompts: list[dict],
    bounds: list[tuple[float, float]],
    top_k: int = config.CLAP_TOP_K,
) -> list[dict]:
    """Cosine similarity audio-prompt, top-K per segmento."""
    if audio_emb.size == 0 or prompt_emb.size == 0:
        return []
    a = audio_emb / (np.linalg.norm(audio_emb, axis=1, keepdims=True) + 1e-9)
    p = prompt_emb / (np.linalg.norm(prompt_emb, axis=1, keepdims=True) + 1e-9)
    sim = a @ p.T  # (n_segments, n_prompts)

    segments: list[dict] = []
    for seg_idx, (t_start, t_end) in enumerate(bounds):
        scores = sim[seg_idx]
        top_idx = np.argsort(scores)[::-1][:top_k]
        segments.append({
            "t_start_s": round(float(t_start), 2),
            "t_end_s": round(float(t_end), 2),
            "tags": [
                {
                    "id": prompts[int(i)]["id"],
                    "prompt": prompts[int(i)]["text"],
                    "category": prompts[int(i)].get("category", ""),
                    "score": round(float(scores[int(i)]), 4),
                }
                for i in top_idx
            ],
        })
    return segments


def global_top_tags(
    audio_emb: np.ndarray, prompt_emb: np.ndarray, prompts: list[dict], top_k: int = 15
) -> list[dict]:
    """Top tag aggregati su tutto il file (media similarità)."""
    if audio_emb.size == 0 or prompt_emb.size == 0:
        return []
    a = audio_emb / (np.linalg.norm(audio_emb, axis=1, keepdims=True) + 1e-9)
    p = prompt_emb / (np.linalg.norm(prompt_emb, axis=1, keepdims=True) + 1e-9)
    sim = a @ p.T  # (n_segments, n_prompts)
    mean_sim = np.mean(sim, axis=0)
    top_idx = np.argsort(mean_sim)[::-1][:top_k]
    return [
        {
            "id": prompts[int(i)]["id"],
            "prompt": prompts[int(i)]["text"],
            "category": prompts[int(i)].get("category", ""),
            "score": round(float(mean_sim[int(i)]), 4),
        }
        for i in top_idx
    ]


def _encode_float16(a: np.ndarray) -> str:
    """Comprime a float16 e ritorna base64 per serializzazione JSON."""
    return base64.b64encode(a.astype(np.float16).tobytes()).decode("ascii")


def clap_summary(
    waveform: np.ndarray,
    sr: int,
    enable: bool = True,
    segment_seconds: float = config.CLAP_SEGMENT_S,
    top_k: int = config.CLAP_TOP_K,
    include_embeddings: bool = True,
    classifier: dict | None = None,
) -> dict:
    """Pipeline CLAP completa: carica vocabolario, embed audio + prompts,
    tag per segmento + globale. Ritorna dict serializzabile."""
    if not enable:
        return {"enabled": False, "reason": "disabled"}

    vocab = load_vocabulary()
    prompts = vocab["prompts"]
    prompt_texts = [p["text"] for p in prompts]

    audio_emb, bounds = embed_audio_segments(waveform, sr, segment_seconds=segment_seconds)
    prompt_emb = embed_prompts(prompt_texts)

    timeline = tag_segments(audio_emb, prompt_emb, prompts, bounds, top_k=top_k)
    top_global = global_top_tags(audio_emb, prompt_emb, prompts)

    _model, dev = load_clap_model()

    # v0.4.0: calcola hint accademici aggregati sui top-20. Wrapping
    # difensivo: se il mapping non carica (file mancante o malformato)
    # la pipeline non si interrompe e il campo resta {"available": False}.
    academic_hints: dict = {}
    academic_mapping_version = ""
    try:
        import sys as _sys
        from .clap_mapping import aggregate_academic_hints, load_academic_mapping
        mapping = load_academic_mapping()
        academic_mapping_version = mapping.get("version", "")
        top20 = global_top_tags(audio_emb, prompt_emb, prompts, top_k=20)
        # v0.6.6: passa classifier per cross-check Krause da PANNs frame
        academic_hints = aggregate_academic_hints(
            top20, vocab, mapping, classifier=classifier
        )
    except Exception as e:
        import sys as _sys
        print(
            f"[semantic_clap] Errore calcolo academic_hints: {e}",
            file=_sys.stderr, flush=True,
        )
        academic_hints = {"available": False, "reason": f"hints error: {e}"}

    result = ClapResult(
        enabled=True,
        model_name=vocab.get("model", "LAION-CLAP"),
        device=dev,
        vocabulary_size=len(prompts),
        vocabulary_version=vocab.get("version", "1.0"),
        academic_mapping_version=academic_mapping_version,
        segment_seconds=segment_seconds,
        timeline=timeline,
        top_global=top_global,
        academic_hints=academic_hints,
    )
    if include_embeddings:
        result.embeddings_audio_b64 = _encode_float16(audio_emb)
        result.embeddings_prompts_b64 = _encode_float16(prompt_emb)
        result.embeddings_shape = [list(audio_emb.shape), list(prompt_emb.shape)]

    return result.to_dict()
