"""
Legacy phonk_engine compatibility shim for phonk_engine_v2.py
"""
import numpy as np

def generate_cowbell(notes: list, bpm: int, out_path: str) -> str:
    """Generates a simple cowbell sample."""
    sr = 44100
    t = np.linspace(0, 0.2, int(sr * 0.2))
    audio = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 15)
    import soundfile as sf
    sf.write(out_path, audio, sr)
    return out_path
