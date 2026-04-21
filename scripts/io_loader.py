"""Caricamento audio e metadati.

Combinazione di ffprobe (metadati), librosa (analisi generale mono/stereo)
e soundfile (lettura multicanale diretta).
"""
import json
from pathlib import Path
import numpy as np
import subprocess

from . import config
from .utils import run_cmd, check_binary


def load_metadata(path: str | Path) -> dict:
    """Porting da analyze.py del toolkit originale.

    Usa ffprobe per leggere metadati di stream e container.
    """
    if not check_binary("ffprobe"):
        raise RuntimeError("ffprobe non trovato. Installa ffmpeg: brew install ffmpeg")

    r = run_cmd([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ])
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe fallito: {r.stderr}")

    data = json.loads(r.stdout)
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    duration = float(fmt.get("duration", 0) or 0)
    bitrate = int(fmt.get("bit_rate", 0) or 0)
    sr = int(audio_stream.get("sample_rate", 0) or 0)
    channels = int(audio_stream.get("channels", 0) or 0)
    codec = audio_stream.get("codec_name", "?")
    bit_depth = audio_stream.get("bits_per_sample") or audio_stream.get("bits_per_raw_sample")
    try:
        bit_depth = int(bit_depth) if bit_depth else None
    except (TypeError, ValueError):
        bit_depth = None

    size_bytes = int(fmt.get("size", 0) or 0)
    if not size_bytes:
        try:
            size_bytes = Path(path).stat().st_size
        except OSError:
            size_bytes = 0

    return {
        "path": str(path),
        "filename": Path(path).name,
        "codec": codec,
        "sr": sr,
        "bit_depth": bit_depth,
        "channels": channels,
        "duration_s": duration,
        "bitrate_kbps": bitrate // 1000 if bitrate else None,
        "size_mb": round(size_bytes / 1024 / 1024, 3),
        "format_name": fmt.get("format_name"),
        "tags": fmt.get("tags") or {},
    }


def detect_layout(channels: int) -> str:
    """Mappa numero canali a layout canonico."""
    mapping = {
        1: "mono",
        2: "stereo",
        4: "quad",
        6: "5.1",
        8: "7.1",
        10: "5.1.4",
        12: "7.1.4",
    }
    return mapping.get(channels, f"custom_{channels}ch")


def load_audio_mono(path: str | Path, sr: int = config.SR_ANALYSIS) -> tuple[np.ndarray, int]:
    """Caricamento mono a sample rate configurabile, per analisi generali.

    Con sr ridotto (default 22050) contiene il consumo di memoria su file lunghi.
    """
    import librosa
    y, sr_out = librosa.load(str(path), sr=sr, mono=True)
    return y.astype(np.float32), sr_out


def load_audio_multichannel(path: str | Path, sr: int = config.SR_ANALYSIS) -> dict:
    """Carica file preservando i canali.

    Ritorna:
      {
        "channels": [np.ndarray, ...] (ciascuno mono),
        "downmix_mono": np.ndarray,
        "n_channels": int,
        "sr": int,
        "layout": str,
      }
    """
    import soundfile as sf
    import librosa

    try:
        data, sr_orig = sf.read(str(path), always_2d=True, dtype="float32")
    except sf.LibsndfileError:
        # v0.12.4: fallback ffmpeg per formati non supportati da libsndfile
        # (es. AAC in container MP4/m4a di iPhone Voice Memos). ffmpeg
        # decodifica virtualmente qualsiasi formato, output pipe WAV PCM.
        import subprocess
        import io as _io
        proc = subprocess.run(
            ["ffmpeg", "-i", str(path), "-f", "wav", "-acodec", "pcm_s16le",
             "-ar", str(sr), "-hide_banner", "-loglevel", "error", "pipe:1"],
            capture_output=True, check=True,
        )
        data, sr_orig = sf.read(_io.BytesIO(proc.stdout), always_2d=True,
                                dtype="float32")
    if sr_orig != sr:
        # v0.4.1: fix off-by-one della pre-allocazione. librosa.resample puo'
        # restituire una lunghezza che differisce di +/-1 sample rispetto alla
        # formula int(n * target/orig), a seconda dell'algoritmo interno
        # (default soxr_hq). Risampliamo ciascun canale separatamente e
        # allineiamo tutti alla lunghezza minima con trim difensivo.
        resampled_list = [
            librosa.resample(data[:, ch], orig_sr=sr_orig, target_sr=sr)
            for ch in range(data.shape[1])
        ]
        min_len = min(len(c) for c in resampled_list)
        data = np.column_stack(
            [c[:min_len] for c in resampled_list]
        ).astype(np.float32)

    channels = [data[:, i].astype(np.float32) for i in range(data.shape[1])]
    n_ch = len(channels)
    downmix = np.mean(data, axis=1).astype(np.float32)
    layout = detect_layout(n_ch)

    return {
        "channels": channels,
        "downmix_mono": downmix,
        "n_channels": n_ch,
        "sr": sr,
        "layout": layout,
    }


def channel_label(idx: int, layout: str) -> str:
    """Etichetta canale secondo layout canonico."""
    layouts = {
        "mono": ["Mono"],
        "stereo": ["L", "R"],
        "quad": ["L", "R", "Ls", "Rs"],
        "5.1": ["L", "R", "C", "LFE", "Ls", "Rs"],
        "7.1": ["L", "R", "C", "LFE", "Ls", "Rs", "Lb", "Rb"],
        "5.1.4": ["L", "R", "C", "LFE", "Ls", "Rs", "Tfl", "Tfr", "Trl", "Trr"],
        "7.1.4": ["L", "R", "C", "LFE", "Ls", "Rs", "Lb", "Rb", "Tfl", "Tfr", "Trl", "Trr"],
    }
    names = layouts.get(layout)
    if names and idx < len(names):
        return names[idx]
    return f"Ch{idx+1}"
