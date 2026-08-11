# -*- coding: utf-8 -*-
"""
ZS Music Maker — phonk_engine_v2.py (GOD MODE)
========================================================================
Второе поколение Phonk-движка. 
Включает:
  - Продвинутый синтез 808-баса с Glide
  - Генерацию паттернов на основе музыкальной теории
  - Интеграцию с Plugin System
"""

import numpy as np
import soundfile as sf
from app.plugins.base import PluginChain
from app.plugins.advanced import PhonkDistortion, AntiAINeuroObfuscator
from modules.phonk_engine import generate_cowbell
from modules.musical_intelligence import MusicalIntelligence

class PhonkEngineV2:
    def __init__(self, sr: int = 44100):
        self.sr = sr
        self.intel = MusicalIntelligence(sr)
        self.chain = PluginChain()
        self.chain.add(PhonkDistortion(drive_db=25.0))
        self.chain.add(AntiAINeuroObfuscator(intensity=0.3))

    def generate_808(self, freq: float, duration: float, glide_to: float = None):
        """Генерирует жирный 808 бас с возможным глайдом."""
        t = np.linspace(0, duration, int(self.sr * duration), endpoint=False)
        
        if glide_to:
            # Линейное изменение частоты
            freqs = np.linspace(freq, glide_to, len(t))
            phase = 2 * np.pi * np.cumsum(freqs) / self.sr
            wave = np.sin(phase)
        else:
            wave = np.sin(2 * np.pi * freq * t)
            
        # Добавляем гармоники для дисторшна
        wave += 0.5 * np.sin(4 * np.pi * freq * t)
        wave += 0.25 * np.sin(6 * np.pi * freq * t)
        
        # Огибающая
        env = np.exp(-t * 5.0)
        return (wave * env).astype(np.float32)

    def create_drift_track(self, project_id: str, bpm: int, key_root: str, mode: str, out_path: str):
        """Создает полноценный Drift Phonk трек."""
        duration_sec = 30 # Для теста 30 секунд
        total_samples = int(self.sr * duration_sec)
        track = np.zeros((total_samples, 2), dtype=np.float32)
        
        step_sec = 60.0 / bpm / 4 # 1/16 ноты
        step_samples = int(self.sr * step_sec)
        
        # Получаем аккорды и ноты
        chords_list = self.intel.suggest_chords(key_root, mode)
        if not chords_list:
            # Fallback progression: i-VI-III-VII
            chords_list = [[key_root], [key_root], [key_root], [key_root]]
        
        # 1. Заполняем 808 и Cowbells по сетке
        for i in range(0, total_samples - self.sr, step_samples * 16):
            # Каждые 4 такта меняем ноту баса
            chord_idx = (i // (step_samples * 16)) % len(chords_list)
            root_note = chords_list[chord_idx][0]
            # Упрощенно: переводим название ноты в частоту (A4=440)
            # В реальном коде нужен маппинг
            freq = 55.0 # Контр-октава А
            
            bass = self.generate_808(freq, step_sec * 8)
            bass_stereo = np.stack([bass, bass], axis=1)
            
            start = i
            end = start + len(bass_stereo)
            track[start:end] += bass_stereo * 0.8
            
            # Добавляем ковбелл на сильные доли
            for j in range(4):
                bell = generate_cowbell(440.0 * (1.2 ** j), duration_sec=0.3)
                bell_stereo = np.stack([bell, bell], axis=1)
                b_start = i + j * step_samples * 4
                b_end = b_start + len(bell_stereo)
                track[b_start:b_end] += bell_stereo * 0.5

        # 2. Применяем цепочку эффектов (GOD MODE)
        track = self.chain.process(track, self.sr)
        
        # 3. Финальная нормализация
        track = track / (np.max(np.abs(track)) + 1e-9) * 0.9
        
        sf.write(out_path, track, self.sr)
        return out_path

if __name__ == "__main__":
    engine = PhonkEngineV2()
    engine.create_drift_track("god_v2_test", 120, "A", "minor", "output/phonk_v2_god.wav")
