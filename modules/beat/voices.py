# -*- coding: utf-8 -*-
"""
modules/beat/voices.py — синтез отдельных голосов бита.

Kick, snare, hihat, бас-линия, мелодия, FX и панорамирование. Каждый голос
использует детерминированный RNG конструктора, а не глобальный random.
"""

from __future__ import annotations

import math

import numpy as np


class VoicesMixin:
    def _generate_kick(self, step: int, bar: int) -> np.ndarray:
        """Возвращает кик для данного шага с учетом акцентов и вариаций."""
        # Core 16-step pattern is sourced from the selected genre slot.
        kick_pattern = self.slot_patterns["kick"]

        # Вариация каждые 4 такта
        if bar % 4 == 3 and step >= 12:
            # Добавляем сбивку в конце 4-го такта
            if step in [12, 14, 15]:
                kick_pattern = [0] * 12 + [1, 0, 1, 1]

        idx = step % len(kick_pattern)
        if kick_pattern[idx] == 0:
            return np.zeros(1, dtype=np.float32)

        # Акценты: первый удар сильнее, офф-биты слабее
        velocity = 1.0
        if step == 0:
            velocity = 1.05
        elif step % 4 != 0:
            velocity = 0.85

        # Если есть реальный сэмпл кика — используем его
        if self.kick_samples:
            kick_path = self._choice(self.kick_samples)
            return self._load_audio(kick_path) * velocity

        # Иначе синтезируем простой кик
        dur = 0.15  # 150ms
        t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
        env = np.exp(-t * 30)
        freq = 60 * np.exp(-t * 100) + 40  # pitch sweep
        kick = 0.8 * env * np.sin(2 * np.pi * freq * t)
        return kick


    def _generate_snare(self, step: int, bar: int) -> np.ndarray:
        """Возвращает снейр/клэп для данного шага с учетом акцентов."""
        snare_pattern = self.slot_patterns["snare"]

        # Ghost notes (призрачные ноты) для живости
        is_ghost = False
        if snare_pattern[step % 16] == 0:
            if step % 16 in [3, 6, 11, 14] and self._random() < 0.2:
                is_ghost = True
            else:
                return np.zeros(1, dtype=np.float32)

        velocity = 0.3 if is_ghost else (0.9 + self._random() * 0.15)

        if self.snare_samples:
            snare_path = self._choice(self.snare_samples)
            return self._load_audio(snare_path) * velocity

        # Синтез снейра: шум + тон
        dur = 0.12
        t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
        env = np.exp(-t * 25)
        noise = self._noise(len(t)) * 0.5
        tone = 0.3 * np.sin(2 * np.pi * 200 * t)
        snare = 0.6 * env * (noise + tone)
        return snare


    def _generate_hihat(self, step: int, bar: int) -> np.ndarray:
        """Возвращает хэт для данного шага."""
        density = self.groove.get("hihat_density", 0.5)
        swing = self.groove.get("swing", 0.0)

        # Legacy default preserves its historical density-only hat behavior;
        # genre presets use explicit steps plus only a small density variation.
        if self.genre == "legacy":
            play = self._random() < density
        else:
            play = bool(self.slot_patterns["hat"][step % 16])
            if not play:
                play = self._random() < density * 0.12
        if step % 2 == 1 and self._random() < swing * 0.5:
            play = True  # свинг добавляет доп. удары

        if not play:
            return np.zeros(1, dtype=np.float32)

        if self.hihat_samples:
            hh_path = self._choice(self.hihat_samples)
            return self._load_audio(hh_path) * 0.5  # хэт тише

        # Синтез хэта: высокочастотный шум
        dur = 0.05
        t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
        env = np.exp(-t * 80)
        noise = self._noise(len(t))
        # High-pass (простая реализация: вычитаем скользящее среднее)
        if len(noise) > 10:
            noise = noise - np.convolve(noise, np.ones(10) / 10, mode="same")
        hihat = 0.3 * env * noise
        return hihat


    def _generate_bass_line(self, bar: int, bar_samples: int) -> np.ndarray:
        """Генерирует басовую линию для такта."""
        if self.bass_samples:
            bass_path = self._choice(self.bass_samples)
            bass = self._load_audio(bass_path)
            if len(bass) < bar_samples:
                bass = np.pad(bass, (0, bar_samples - len(bass)))
            return bass[:bar_samples] * 0.8

        # Синтез 808 баса
        # Ноты в миноре: I, III, V, VII (для phonk/трэпа)
        root_freqs = {
            "C": 261.63,
            "C#": 277.18,
            "D": 293.66,
            "D#": 311.13,
            "E": 329.63,
            "F": 349.23,
            "F#": 369.99,
            "G": 392.00,
            "G#": 415.30,
            "A": 440.00,
            "A#": 466.16,
            "B": 493.88,
        }
        root = self.key.split()[0] if " " in self.key else "A"
        base_freq = root_freqs.get(root, 440.0) / 2  # на октаву ниже

        # Bass is an independent slot, not an implicit duplicate of the kick.
        bass_pattern = self.slot_patterns["bass"]
        bass = np.zeros(bar_samples, dtype=np.float32)

        step_len = bar_samples // 16
        for i, play in enumerate(bass_pattern):
            if play:
                start = i * step_len
                end = min(start + step_len * 2, bar_samples)
                dur_t = np.linspace(
                    0, (end - start) / self.sr, end - start, endpoint=False
                )
                env = np.exp(-dur_t * 5)
                bass[start:end] += 0.7 * env * np.sin(2 * np.pi * base_freq * dur_t)

        return bass


    def _generate_melody(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
        """Генерирует мелодический слой для такта."""
        # В брейках/интро мелодия плотнее, в дропе — реже
        if section in ("intro", "breakdown", "outro") and self.melody_samples:
            mel_path = self._choice(self.melody_samples)
            mel = self._load_audio(mel_path)
            if len(mel) < bar_samples:
                mel = np.pad(mel, (0, bar_samples - len(mel)))
            return mel[:bar_samples] * 0.4

        if section == "verse" and self.melody_samples and bar % 2 == 0:
            mel_path = self._choice(self.melody_samples)
            mel = self._load_audio(mel_path) * 0.25
            if len(mel) < bar_samples:
                mel = np.pad(mel, (0, bar_samples - len(mel)))
            return mel[:bar_samples]

        return np.zeros(bar_samples, dtype=np.float32)


    def _generate_fx(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
        """Генерирует FX (райзеры, импакты) в переходах."""
        # Райзер перед дропом
        if section == "pre_chorus" and self.fx_samples:
            fx_path = self._choice(self.fx_samples)
            fx = self._load_audio(fx_path)
            if len(fx) < bar_samples:
                fx = np.pad(fx, (0, bar_samples - len(fx)))
            return fx[:bar_samples] * 0.5

        # Стоп-тайм (тишина перед хуком) — 1 шаг тишины в конце такта
        if section == "hook" and bar % 4 == 3:
            stop_samples = bar_samples // 16 * 2
            fx = np.ones(stop_samples, dtype=np.float32) * 0.001
            return np.pad(fx, (bar_samples - stop_samples, 0))

        return np.zeros(bar_samples, dtype=np.float32)


    def _pan_audio(self, audio: np.ndarray, pan: float) -> np.ndarray:
        """Панорамирует моно-сигнал. pan: -1 (L) .. 1 (R)."""
        if audio.ndim > 1:
            return audio  # уже стерео
        # Constant power panning
        angle = (pan + 1.0) * (math.pi / 4.0)
        left = math.cos(angle)
        right = math.sin(angle)
        return np.stack([audio * left, audio * right], axis=1).astype(np.float32)
