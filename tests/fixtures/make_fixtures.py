"""Genera fixture WAV sintetici deterministici per i test.

Eseguire una sola volta, poi committare i WAV.
"""
from pathlib import Path
import numpy as np
import soundfile as sf


HERE = Path(__file__).resolve().parent
SR = 22050


def _pink_noise_signal(n: int, sr: int, seed: int = 1) -> np.ndarray:
    """Genera pink noise senza DC via divisione 1/sqrt(freq) con freqs[0]=0 (no boost DC)."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(n)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, d=1/sr)
    scale = np.zeros_like(freqs)
    scale[1:] = 1.0 / np.sqrt(freqs[1:])
    fft = fft * scale  # bin 0 (DC) a zero
    pink = np.fft.irfft(fft, n=n).astype(np.float32)
    pink = pink - float(np.mean(pink))  # rimuovi eventuale offset residuo
    pink = pink / (np.max(np.abs(pink)) + 1e-9)
    return pink


def sine_with_noise(duration=2.0, sine_hz=50.0, sine_level_dbfs=-20.0,
                    noise_level_dbfs=-40.0, sr=SR):
    """Seno puro + pink noise basso, per test hum positivo."""
    n = int(duration * sr)
    t = np.linspace(0, duration, n, endpoint=False)
    sine = np.sin(2 * np.pi * sine_hz * t) * (10 ** (sine_level_dbfs / 20.0))
    pink = _pink_noise_signal(n, sr, seed=42) * (10 ** (noise_level_dbfs / 20.0))
    y = (sine + pink).astype(np.float32)
    return y


def pink_noise(duration=3.0, level_dbfs=-10.0, sr=SR, seed=1):
    """Pink noise puro, senza DC, nessun hum."""
    n = int(duration * sr)
    pink = _pink_noise_signal(n, sr, seed=seed) * (10 ** (level_dbfs / 20.0))
    return pink.astype(np.float32)


def silence_low(duration=4.0, level_dbfs=-60.0, sr=SR):
    """Pink noise a livello molto basso, per test pre-check YAMNet."""
    return pink_noise(duration=duration, level_dbfs=level_dbfs, sr=sr, seed=7)


def transient_dense(duration=4.0, n_events=150, sr=SR):
    """Serie di click-transienti, onset density alta."""
    n = int(duration * sr)
    y = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(13)
    positions = rng.integers(0, n - 100, size=n_events)
    for pos in positions:
        env = np.exp(-np.linspace(0, 10, 100))
        phase = rng.random() * 2 * np.pi
        freq = rng.uniform(500, 3000)
        t = np.linspace(0, 100/sr, 100)
        click = np.sin(2 * np.pi * freq * t + phase) * env * 0.3
        y[pos:pos+100] += click
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.7
    return y.astype(np.float32)


def multichannel_714(duration=2.0, sr=SR):
    """File 12 canali 7.1.4 con contenuto differenziato per canale."""
    n = int(duration * sr)
    t = np.linspace(0, duration, n, endpoint=False)
    data = np.zeros((n, 12), dtype=np.float32)
    # L, R: 440 Hz + 880 Hz
    data[:, 0] = np.sin(2 * np.pi * 440 * t) * 0.3
    data[:, 1] = np.sin(2 * np.pi * 880 * t) * 0.3
    # C: 220 Hz
    data[:, 2] = np.sin(2 * np.pi * 220 * t) * 0.3
    # LFE: 40 Hz
    data[:, 3] = np.sin(2 * np.pi * 40 * t) * 0.5
    # Ls, Rs: 1320 Hz, 1760 Hz
    data[:, 4] = np.sin(2 * np.pi * 1320 * t) * 0.2
    data[:, 5] = np.sin(2 * np.pi * 1760 * t) * 0.2
    # Lb, Rb: 2200 Hz, 2640 Hz
    data[:, 6] = np.sin(2 * np.pi * 2200 * t) * 0.2
    data[:, 7] = np.sin(2 * np.pi * 2640 * t) * 0.2
    # Tfl, Tfr: 3300 Hz, 3960 Hz (air, height)
    data[:, 8] = np.sin(2 * np.pi * 3300 * t) * 0.15
    data[:, 9] = np.sin(2 * np.pi * 3960 * t) * 0.15
    # Trl, Trr: 4400 Hz, 5280 Hz
    data[:, 10] = np.sin(2 * np.pi * 4400 * t) * 0.15
    data[:, 11] = np.sin(2 * np.pi * 5280 * t) * 0.15
    return data


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    print("Genero fixtures in:", HERE)

    sf.write(HERE / "sine_50hz.wav", sine_with_noise(), SR, subtype="PCM_16")
    sf.write(HERE / "pink_noise.wav", pink_noise(), SR, subtype="PCM_16")
    sf.write(HERE / "silence_low.wav", silence_low(), SR, subtype="PCM_16")
    sf.write(HERE / "transient_dense.wav", transient_dense(), SR, subtype="PCM_16")
    sf.write(HERE / "multichannel_714.wav", multichannel_714(), SR, subtype="PCM_16")
    print("Fatto")


if __name__ == "__main__":
    main()
