"""Classificazione semantica con interfaccia astratta.

v0.2.0: refactor con `Classifier` astratto. Due implementazioni:
- `PANNsClassifier` (default): CNN14 addestrato su AudioSet, 527 classi, 32 kHz.
- `YAMNetClassifier` (legacy): wrapper della v0.1 mantenuto per compatibilità.

Lezione critica codificata: pre-check LUFS prima della classificazione. Se il
file è sotto la soglia `LUFS_SEMANTIC_PRECHECK`, applica un gain temporaneo in
memoria (non tocca il file originale) per evitare il fallimento tipo Villa
Ficana (97,9% Silence).
"""
from __future__ import annotations
import csv
import os
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any
import numpy as np

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

from . import config
from .device import resolve_device, log_device, suppress_stdout
from .technical import compute_lufs


@dataclass
class ClassificationResult:
    """Output comune di qualsiasi Classifier, indipendente dal modello.

    La struttura è deliberatamente simile a quella usata dal report v0.1
    per consentire il passaggio fra backend senza ristrutturare il PDF.
    """
    top_global: list[dict] = field(default_factory=list)
    top_dominant_frames: list[dict] = field(default_factory=list)
    timeline: list[dict] = field(default_factory=list)
    frames_total: int = 0
    duration_s: float = 0.0
    n_classes: int = 0
    model_name: str = ""
    model_version: str = ""
    device: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class Classifier(ABC):
    """Interfaccia astratta di un classificatore semantico audio."""

    @property
    @abstractmethod
    def required_sr(self) -> int:
        """Sample rate nativo atteso dal modello."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nome esposto nel report, es. 'PANNs CNN14' o 'YAMNet'."""

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Versione/identificativo del checkpoint."""

    @property
    def device(self) -> str:
        """Device su cui gira il modello (auto/cpu/mps/cuda)."""
        return "cpu"

    @abstractmethod
    def classify(self, waveform: np.ndarray, sr: int,
                 segment_seconds: float = 10.0) -> ClassificationResult:
        """Esegue la classificazione. `sr` deve coincidere con `required_sr`."""


PANNS_CHECKPOINT_DIR = Path.home() / "panns_data"
PANNS_CHECKPOINT_FILE = PANNS_CHECKPOINT_DIR / "Cnn14_mAP=0.431.pth"
PANNS_LABELS_FILE = PANNS_CHECKPOINT_DIR / "class_labels_indices.csv"
PANNS_LABELS_URL = (
    "https://raw.githubusercontent.com/qiuqiangkong/audioset_tagging_cnn/master/"
    "metadata/class_labels_indices.csv"
)


def _ensure_panns_checkpoint() -> None:
    """Scarica checkpoint e labels CSV se assenti. Usa urllib (no wget).

    Evita il bug del package `panns_inference` che invoca wget, assente su macOS.
    """
    import urllib.request
    PANNS_CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    if not PANNS_LABELS_FILE.exists():
        urllib.request.urlretrieve(PANNS_LABELS_URL, str(PANNS_LABELS_FILE))
    if not PANNS_CHECKPOINT_FILE.exists():
        urllib.request.urlretrieve(config.PANNS_CHECKPOINT_URL,
                                    str(PANNS_CHECKPOINT_FILE))


class PANNsClassifier(Classifier):
    """CNN14 addestrato su AudioSet tramite `panns_inference`.

    Checkpoint scaricato automaticamente alla prima invocazione in
    `~/panns_data/` (default del package). 527 classi AudioSet.
    """

    def __init__(self, device: str | None = None):
        self._requested_device = device or config.SEMANTIC_DEVICE
        self._device = resolve_device(self._requested_device)
        self._at = None
        self._labels = None

    @property
    def required_sr(self) -> int:
        return config.PANNS_SR

    @property
    def model_name(self) -> str:
        return "PANNs CNN14"

    @property
    def model_version(self) -> str:
        return "Cnn14_mAP=0.431"

    @property
    def device(self) -> str:
        return self._device

    def _ensure_loaded(self):
        if self._at is not None:
            return
        # Lazy import per non pagare ~1 GB di torch al boot del CLI.
        import torch
        from panns_inference import AudioTagging, labels
        _ensure_panns_checkpoint()

        # panns_inference 0.1.1 accetta solo 'cuda' nel suo costruttore: qualsiasi
        # altro valore viene silenziosamente mappato a 'cpu' con una print su
        # stdout. Costruiamo sempre su CPU (sopprimendo le print), poi spostiamo
        # manualmente il modello su MPS se richiesto. Funziona perché self._at.model
        # è un torch.nn.Module pubblico e self._at.inference() chiama
        # `move_data_to_device(audio, self.device)`: aggiornando self._at.device
        # anche l'input viene spedito al device corretto.
        try:
            with suppress_stdout():
                self._at = AudioTagging(checkpoint_path=None, device="cpu")
        except Exception as e:
            raise RuntimeError(f"Impossibile caricare PANNs: {e}") from e
        self._labels = list(labels)

        if self._device == "mps":
            try:
                self._at.model.to(torch.device("mps"))
                self._at.device = "mps"
                # Sanity forward pass: 1 secondo di silenzio a 32 kHz. Se una
                # op del grafo CNN14 non fosse supportata su MPS nonostante
                # PYTORCH_ENABLE_MPS_FALLBACK=1, cade qui in modo controllato.
                probe = np.zeros((1, config.PANNS_SR), dtype=np.float32)
                self._at.inference(probe)
            except (RuntimeError, NotImplementedError) as e:
                print(
                    f"[PANNs CNN14] MPS forward fallito ({e}), fallback a CPU",
                    file=sys.stderr, flush=True,
                )
                self._at.model.to(torch.device("cpu"))
                self._at.device = "cpu"
                self._device = "cpu"

        log_device("PANNs CNN14", self._device)

    def classify(self, waveform: np.ndarray, sr: int,
                 segment_seconds: float = 10.0) -> ClassificationResult:
        import librosa
        # Resample interno se serve
        if sr != self.required_sr:
            waveform = librosa.resample(waveform, orig_sr=sr, target_sr=self.required_sr)
            sr = self.required_sr

        self._ensure_loaded()

        # Segmentazione in finestre fisse
        chunk_samples = int(segment_seconds * sr)
        n_chunks = max(1, int(np.ceil(len(waveform) / chunk_samples)))
        duration_s = len(waveform) / sr

        all_scores: list[np.ndarray] = []
        segment_bounds: list[tuple[float, float]] = []
        for i in range(n_chunks):
            a = i * chunk_samples
            b = min(a + chunk_samples, len(waveform))
            chunk = waveform[a:b]
            if len(chunk) < sr * 0.5:
                # scarta coda troppo breve, altera poco la distribuzione
                continue
            # PANNs richiede shape (batch, samples) float32
            chunk_batch = chunk[np.newaxis, :].astype(np.float32)
            clipwise, _embed = self._at.inference(chunk_batch)
            all_scores.append(np.asarray(clipwise[0], dtype=np.float32))
            segment_bounds.append((a / sr, b / sr))

        if not all_scores:
            return ClassificationResult(
                duration_s=round(duration_s, 2),
                model_name=self.model_name,
                model_version=self.model_version,
                device=self._device,
            )

        scores_matrix = np.stack(all_scores, axis=0)  # (n_chunks, 527)

        # Top globali (media pesata sui chunk)
        mean_scores = np.mean(scores_matrix, axis=0)
        top_idx = np.argsort(mean_scores)[::-1][:15]
        top_global = [
            {"name": self._labels[int(i)], "score": round(float(mean_scores[i]), 4)}
            for i in top_idx
        ]

        # Dominanza per chunk (top-1)
        top1 = np.argmax(scores_matrix, axis=1)
        counts = defaultdict(int)
        for c in top1:
            counts[int(c)] += 1
        total_frames = int(len(top1))
        sorted_counts = sorted(counts.items(), key=lambda x: -x[1])[:15]
        top_dominant = [
            {"name": self._labels[c], "frames": int(n),
             "pct": round(100.0 * n / total_frames, 2)}
            for c, n in sorted_counts
        ]

        # Timeline top-3 per segmento
        timeline: list[dict] = []
        for (t_start, t_end), chunk_scores in zip(segment_bounds, scores_matrix):
            top3 = np.argsort(chunk_scores)[::-1][:3]
            timeline.append({
                "t_start_s": round(float(t_start), 2),
                "t_end_s": round(float(t_end), 2),
                "top": [
                    {"name": self._labels[int(c)],
                     "score": round(float(chunk_scores[c]), 4)}
                    for c in top3
                ],
            })

        return ClassificationResult(
            top_global=top_global,
            top_dominant_frames=top_dominant,
            timeline=timeline,
            frames_total=total_frames,
            duration_s=round(duration_s, 2),
            n_classes=int(scores_matrix.shape[1]),
            model_name=self.model_name,
            model_version=self.model_version,
            device=self._device,
        )


class YAMNetClassifier(Classifier):
    """YAMNet via TensorFlow Hub, mantenuto per retrocompatibilità v0.1."""

    def __init__(self):
        self._model = None
        self._class_names = None

    @property
    def required_sr(self) -> int:
        return 16000

    @property
    def model_name(self) -> str:
        return "YAMNet"

    @property
    def model_version(self) -> str:
        return "tfhub v1"

    @property
    def device(self) -> str:
        return "cpu"  # TF decide internamente

    def _ensure_loaded(self):
        if self._model is None:
            import tensorflow as tf
            import tensorflow_hub as hub
            self._model = hub.load(config.YAMNET_URL)
            class_map_path = self._model.class_map_path().numpy().decode("utf-8")
            names: list[str] = []
            with tf.io.gfile.GFile(class_map_path) as f:
                for row in csv.DictReader(f):
                    names.append(row["display_name"])
            self._class_names = names

    def classify(self, waveform: np.ndarray, sr: int,
                 segment_seconds: float = 10.0) -> ClassificationResult:
        import librosa
        if sr != self.required_sr:
            waveform = librosa.resample(waveform, orig_sr=sr, target_sr=self.required_sr)
            sr = self.required_sr

        self._ensure_loaded()
        duration_s = len(waveform) / sr

        # YAMNet internalmente processa con hop 0.48s. Spezziamo in chunk
        # da 60s per contenere memoria.
        chunk_samples = int(config.YAMNET_CHUNK_SECONDS * sr)
        n_chunks = int(np.ceil(len(waveform) / chunk_samples)) if len(waveform) else 0

        all_scores: list[np.ndarray] = []
        all_times: list[np.ndarray] = []
        for ci in range(n_chunks):
            a = ci * chunk_samples
            b = min(a + chunk_samples, len(waveform))
            chunk = waveform[a:b]
            if len(chunk) < sr:
                continue
            scores, _emb, _spec = self._model(chunk)
            scores_np = scores.numpy()
            all_scores.append(scores_np)
            times = np.arange(scores_np.shape[0]) * config.YAMNET_FRAME_HOP_S + (a / sr)
            all_times.append(times)

        if not all_scores:
            return ClassificationResult(
                duration_s=round(duration_s, 2),
                model_name=self.model_name,
                model_version=self.model_version,
            )

        scores = np.vstack(all_scores)
        times = np.concatenate(all_times)

        mean_scores = np.mean(scores, axis=0)
        top_idx = np.argsort(mean_scores)[::-1][:15]
        top_global = [
            {"name": self._class_names[int(i)],
             "score": round(float(mean_scores[i]), 4)}
            for i in top_idx
        ]

        top1 = np.argmax(scores, axis=1)
        counts = defaultdict(int)
        for c in top1:
            counts[int(c)] += 1
        total_frames = int(len(top1))
        sorted_counts = sorted(counts.items(), key=lambda x: -x[1])[:15]
        top_dominant = [
            {"name": self._class_names[c], "frames": int(n),
             "pct": round(100.0 * n / total_frames, 2)}
            for c, n in sorted_counts
        ]

        # Timeline per segmenti fissi
        seg_frames = max(int(segment_seconds / config.YAMNET_FRAME_HOP_S), 1)
        n_segments = int(np.ceil(len(scores) / seg_frames))
        timeline: list[dict] = []
        for s in range(n_segments):
            a = s * seg_frames
            b = min(a + seg_frames, len(scores))
            seg = scores[a:b]
            seg_mean = np.mean(seg, axis=0)
            top3 = np.argsort(seg_mean)[::-1][:3]
            t_start = float(times[a]) if a < len(times) else duration_s
            t_end = float(times[b - 1]) if (b - 1) < len(times) else duration_s
            timeline.append({
                "t_start_s": round(t_start, 2),
                "t_end_s": round(t_end, 2),
                "top": [
                    {"name": self._class_names[int(i)],
                     "score": round(float(seg_mean[i]), 4)}
                    for i in top3
                ],
            })

        return ClassificationResult(
            top_global=top_global,
            top_dominant_frames=top_dominant,
            timeline=timeline,
            frames_total=total_frames,
            duration_s=round(duration_s, 2),
            n_classes=int(scores.shape[1]),
            model_name=self.model_name,
            model_version=self.model_version,
        )


def get_classifier(backend: str) -> Classifier:
    """Factory: ritorna l'istanza di classifier richiesta."""
    backend = (backend or "").lower()
    if backend == "panns":
        return PANNsClassifier()
    if backend == "yamnet":
        return YAMNetClassifier()
    raise ValueError(f"Backend semantico sconosciuto: '{backend}'. Usa 'panns' o 'yamnet'.")


def precheck_loudness(
    path: str | Path,
    threshold_lufs: float = config.LUFS_SEMANTIC_PRECHECK,
    target_lufs: float = config.LUFS_SEMANTIC_TARGET,
) -> dict:
    """Pre-check del livello. Se sotto soglia, calcola gain di compensazione."""
    lufs_data = compute_lufs(path)
    lufs = lufs_data.get("integrated_lufs")
    if lufs is None:
        return {"requires_normalization": False, "lufs": None,
                "gain_db": 0.0, "lufs_data": lufs_data}
    requires = bool(lufs < threshold_lufs)
    gain_db = max(0.0, target_lufs - lufs) if requires else 0.0
    return {
        "requires_normalization": requires,
        "lufs": float(lufs),
        "threshold_lufs": threshold_lufs,
        "target_lufs": target_lufs,
        "gain_db": round(gain_db, 2),
        "lufs_data": lufs_data,
    }


def prepare_waveform(path: str | Path, sr: int, gain_db: float = 0.0) -> np.ndarray:
    """Carica il file a `sr` mono. Applica gain in memoria se richiesto."""
    import librosa
    y, _ = librosa.load(str(path), sr=sr, mono=True)
    if gain_db and abs(gain_db) > 0.01:
        factor = 10 ** (gain_db / 20.0)
        y = y * factor
        y = np.clip(y, -1.0, 1.0)
    return y.astype(np.float32)


def save_timeline_csv(timeline: list[dict], out_path: Path) -> None:
    """Salva la timeline in CSV."""
    rows = [[
        "t_start_s", "t_end_s",
        "top1_name", "top1_score",
        "top2_name", "top2_score",
        "top3_name", "top3_score",
    ]]
    for t in timeline:
        row = [t["t_start_s"], t["t_end_s"]]
        for cat in t.get("top", []):
            row += [cat["name"], cat["score"]]
        while len(row) < 8:
            row += ["", ""]
        rows.append(row)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def semantic_summary(
    path: str | Path,
    backend: str | None = None,
    enable: bool = True,
    segment_seconds: float = 10.0,
) -> dict:
    """Orchestrazione completa: precheck + prepare + classify.

    Il backend è preso da `config.SEMANTIC_BACKEND` se non specificato.
    Il summary ritornato ha sempre la stessa struttura indipendentemente
    dal backend.
    """
    if not enable:
        return {"enabled": False, "reason": "disabled"}

    backend = backend or config.SEMANTIC_BACKEND
    classifier = get_classifier(backend)

    pre = precheck_loudness(path)
    waveform = prepare_waveform(
        path, sr=classifier.required_sr, gain_db=pre.get("gain_db", 0.0)
    )
    result = classifier.classify(
        waveform, sr=classifier.required_sr, segment_seconds=segment_seconds
    )
    return {
        "enabled": True,
        "backend": backend,
        "precheck": pre,
        "classifier": result.to_dict(),
    }
