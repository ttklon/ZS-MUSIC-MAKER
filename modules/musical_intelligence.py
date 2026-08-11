# -*- coding: utf-8 -*-
"""
ZS Music Maker — musical_intelligence.py (GOD MODE)
========================================================================
Интеллектуальный анализ музыкальной структуры и гармонии.
Использует pyAudioAnalysis и Mingus для определения тональности и аккордов.
"""

import os
import numpy as np
import soundfile as sf

try:
    from pyAudioAnalysis import audioTrainTest as aT
    from pyAudioAnalysis import audioBasicIO
    from pyAudioAnalysis import ShortTermFeatures
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

try:
    import mingus.core.chords as chords
    import mingus.core.keys as keys
    HAS_MINGUS = True
except ImportError:
    HAS_MINGUS = False


class MusicalIntelligence:
    def __init__(self, sr: int = 44100):
        self.sr = sr

    def analyze_key(self, wav_path: str) -> dict:
        """
        Определяет тональность аудиофайла.
        """
        if not os.path.exists(wav_path):
            return {"ok": False, "error": "File not found"}

        if not HAS_PYAUDIO:
            return {"ok": True, "key": "A minor", "root": "A", "mode": "minor", "fallback": True}

        try:
            [fs, x] = audioBasicIO.read_audio_file(wav_path)
            if x.ndim > 1:
                x = x.mean(axis=1)  # Mono for analysis
                
            ft, _ = ShortTermFeatures.feature_extraction(x, fs, 0.050 * fs, 0.025 * fs)
            chroma = ft[21:33, :].mean(axis=1)
            
            notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            dominant_note_idx = np.argmax(chroma)
            key_root = notes[dominant_note_idx]
            
            minor_idx = (dominant_note_idx + 3) % 12
            major_idx = (dominant_note_idx + 4) % 12
            
            mode = "minor" if chroma[minor_idx] > chroma[major_idx] else "major"
                
            return {
                "ok": True,
                "key": f"{key_root} {mode}",
                "root": key_root,
                "mode": mode,
                "chroma_vector": chroma.tolist()
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def suggest_chords(self, key_root: str, mode: str) -> list:
        """
        Предлагает последовательность аккордов для заданного ключа.
        """
        if not HAS_MINGUS:
            return [["Am"], ["F"], ["C"], ["G"]]
        try:
            if mode == "minor":
                scale = keys.get_notes(key_root + "m")
                prog = [scale[0], scale[5], scale[2], scale[6]]
            else:
                scale = keys.get_notes(key_root)
                prog = [scale[0], scale[4], scale[5], scale[3]]
                
            return [chords.triads(n, key_root + ("m" if mode == "minor" else "")) for n in prog]
        except Exception:
            return [["Am"], ["F"], ["C"], ["G"]]


if __name__ == "__main__":
    intel = MusicalIntelligence()
    print(intel.suggest_chords("A", "minor"))
