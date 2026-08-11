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
from pyAudioAnalysis import audioTrainTest as aT
from pyAudioAnalysis import audioBasicIO
from pyAudioAnalysis import ShortTermFeatures
import mingus.core.chords as chords
import mingus.core.keys as keys

class MusicalIntelligence:
    def __init__(self, sr: int = 44100):
        self.sr = sr

    def analyze_key(self, wav_path: str) -> dict:
        """
        Определяет тональность аудиофайла.
        """
        if not os.path.exists(wav_path):
            return {"ok": False, "error": "File not found"}

        [fs, x] = audioBasicIO.read_audio_file(wav_path)
        if x.ndim > 1:
            x = x.mean(axis=1) # Mono for analysis
            
        # Упрощенный хроматический анализ (здесь можно расширить до полноценного HMM)
        # В данном контексте используем базовый спектральный анализ признаков
        ft, f_names = ShortTermFeatures.feature_extraction(x, fs, 0.050*fs, 0.025*fs)
        
        # Индексы хрома-признаков обычно с 21 по 32
        chroma = ft[21:33, :].mean(axis=1)
        
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        dominant_note_idx = np.argmax(chroma)
        key_root = notes[dominant_note_idx]
        
        # Эвристика мажор/минор по 3-й ступени
        minor_idx = (dominant_note_idx + 3) % 12
        major_idx = (dominant_note_idx + 4) % 12
        
        if chroma[minor_idx] > chroma[major_idx]:
            mode = "minor"
        else:
            mode = "major"
            
        return {
            "ok": True,
            "key": f"{key_root} {mode}",
            "root": key_root,
            "mode": mode,
            "chroma_vector": chroma.tolist()
        }

    def suggest_chords(self, key_root: str, mode: str) -> list:
        """
        Предлагает последовательность аккордов для заданного ключа.
        """
        try:
            if mode == "minor":
                scale = keys.get_notes(key_root + "m")
            else:
                scale = keys.get_notes(key_root)
                
            # Базовая прогрессия i-VI-III-VII для минора или I-V-vi-IV для мажора
            if mode == "minor":
                prog = [scale[0], scale[5], scale[2], scale[6]]
            else:
                prog = [scale[0], scale[4], scale[5], scale[3]]
                
            return [chords.triads(n, key_root + ("m" if mode == "minor" else "")) for n in prog]
        except Exception:
            return []

if __name__ == "__main__":
    # Тест
    intel = MusicalIntelligence()
    print(intel.suggest_chords("A", "minor"))
