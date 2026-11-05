# -*- coding: utf-8 -*-
"""
modules/beat/harmony.py — гармонический слой бита: пэд, клавиши, голосоведение.

Барабаны и бас — это ещё не трек. Трек узнаётся по гармонии: аккордовая
последовательность, плавное голосоведение и «воздух» пэда. Модуль даёт:

* диатонические трезвучия/септаккорды от тоники (`chord_freqs`);
* прогрессии по жанрам (`progression_for`) — с честным seed-ом;
* `voice_lead` — инверсии, при которых голоса ходят на минимальные интервалы,
  а не скачут на октаву;
* `synth_pad` — аддитивный пэд с детюном, вибрато и мягким фильтром;
* `synth_keys` — FM-плак для аккордовых «стабов» на офф-битах.

Всё возвращает float32; пэд стерео, стабы моно (панораму задаёт аранжировка).
"""

from __future__ import annotations

import math

import numpy as np

MINOR_SCALE = (0, 2, 3, 5, 7, 8, 10)
MAJOR_SCALE = (0, 2, 4, 5, 7, 9, 11)

# Прогрессии заданы ступенями лада (0 = тоника). Это не «аккорды из головы»:
# i–VI–III–VII, i–iv–VI–v и i–VII–VI–VII — рабочие ходы phonk/trap/pop.
PROGRESSIONS = {
    "phonk": ((0, 5, 2, 6), (0, 5, 6, 4)),
    "trap": ((0, 5, 2, 6), (0, 3, 5, 4)),
    "house": ((0, 4, 5, 3), (0, 5, 3, 4)),
    "pop": ((0, 4, 5, 3), (0, 5, 6, 4)),
    "default": ((0, 5, 2, 6), (0, 4, 5, 3)),
}

PAD_HARMONICS = 8
KEYS_HARMONICS = 4


def _scale_for(minor: bool) -> tuple[int, ...]:
    return MINOR_SCALE if minor else MAJOR_SCALE


def chord_freqs(
    root_hz: float,
    degree: int,
    minor: bool = True,
    seventh: bool = False,
) -> list[float]:
    """Частоты трезвучия (или септаккорда) на ступени лада."""
    scale = _scale_for(minor)
    tones = [0, 2, 4, 6] if seventh else [0, 2, 4]
    freqs = []
    for tone in tones:
        index = degree + tone
        octave = index // 7
        semitones = scale[index % 7] + 12 * octave
        freqs.append(root_hz * (2.0 ** (semitones / 12.0)))
    return freqs


def progression_for(genre: str, seed: int | None = None) -> tuple[int, ...]:
    """Возвращает прогрессию ступеней для жанра; seed выбирает вариант."""
    key = (genre or "").lower()
    family = (
        "phonk"
        if "phonk" in key or "drift" in key
        else "house"
        if "house" in key or "techno" in key or "trance" in key
        else "trap"
        if "trap" in key or "hip" in key or "rap" in key
        else "pop"
        if "pop" in key or "chanson" in key or "ballad" in key
        else "default"
    )
    options = PROGRESSIONS[family]
    index = 0 if seed is None else abs(int(seed)) % len(options)
    return options[index]


def voice_lead(chord: list[float], previous: list[float] | None) -> list[float]:
    """Приводит аккорд к ближайшей инверсии относительно предыдущего.

    Голоса двигаются максимум на кварту: это то, что отличает живую
    аранжировку от «аккорды в примарной позиции на каждом такте».
    Октавный сдвиг считается один раз (`round(log2(цель/голос))`), петель нет.
    """
    if not previous:
        return sorted(chord)
    targets = sorted(previous)
    led: list[float] = []
    for index, freq in enumerate(sorted(chord)):
        target = targets[min(index, len(targets) - 1)]
        shift = int(round(math.log2(max(target, 1e-6) / max(freq, 1e-6))))
        shift = max(-2, min(2, shift))
        value = freq * (2.0 ** shift)
        # Ниже 60 Гц живёт 808-бас: гармония туда не заходит, иначе низ «мылится».
        while value < 60.0:
            value *= 2.0
        led.append(value)
    return sorted(led)


def _detuned_additive(freqs: list[float], t: np.ndarray, sr: int, detune_cents: float) -> np.ndarray:
    out = np.zeros(len(t), dtype=np.float64)
    for freq in freqs:
        for offset in (-detune_cents, detune_cents):
            f = freq * (2.0 ** (offset / 1200.0))
            phase = 2.0 * np.pi * f * t
            voice = np.zeros(len(t), dtype=np.float64)
            for n in range(1, PAD_HARMONICS + 1):
                if f * n > sr / 2 - 500:
                    break
                voice += np.sin(phase * n) / (n ** 1.6)
            out += voice
    return out


def _vibrato(t: np.ndarray, rate: float = 5.2, depth_cents: float = 5.0) -> np.ndarray:
    return 1.0 + (depth_cents / 1200.0) * np.sin(2.0 * np.pi * rate * t)


def synth_pad(
    sr: int,
    freqs: list[float],
    duration: float,
    attack: float = 0.12,
    release: float = 0.18,
    brightness: float = 0.6,
) -> np.ndarray:
    """Мягкий пэд с детюном и вибрато: моно-сигнал, нормированный в 1.0."""
    n = max(16, int(sr * duration))
    t = np.arange(n, dtype=np.float64) / sr
    body = _detuned_additive(freqs, t, sr, detune_cents=4.0)
    body *= _vibrato(t)
    # Фильтр «яркости»: скользящее среднее вместо дорогого БИХ на длинном сигнале.
    window = max(1, int(sr * (0.0004 + 0.0016 * (1.0 - brightness))))
    if window > 1:
        kernel = np.ones(window, dtype=np.float64) / window
        body = np.convolve(body, kernel, mode="same")
    attack_env = np.clip(t / max(attack, 1e-3), 0.0, 1.0) ** 1.4
    release_env = np.clip((duration - t) / max(release, 1e-3), 0.0, 1.0)
    signal = body * attack_env * release_env
    peak = float(np.max(np.abs(signal))) or 1.0
    return (signal * (0.9 / peak)).astype(np.float32)


def synth_keys(
    sr: int,
    freqs: list[float],
    duration: float,
    decay: float = 0.28,
    fm_depth: float = 1.15,
) -> np.ndarray:
    """FM-плак для аккордовых стабов: короткая атака, «стеклянный» хвост."""
    n = max(16, int(sr * duration))
    t = np.arange(n, dtype=np.float64) / sr
    out = np.zeros(n, dtype=np.float64)
    for freq in freqs:
        carrier_phase = 2.0 * np.pi * freq * t
        modulator = fm_depth * np.exp(-t * 7.0) * np.sin(carrier_phase * 2.0)
        voice = np.sin(carrier_phase + modulator) + 0.22 * np.sin(carrier_phase * 3.0)
        for harmonic in range(2, KEYS_HARMONICS + 1):
            voice += 0.12 / harmonic * np.sin(carrier_phase * harmonic)
        out += voice
    env = np.exp(-t / max(decay, 1e-3)) * np.clip(t / 0.004, 0.0, 1.0)
    signal = out * env
    peak = float(np.max(np.abs(signal))) or 1.0
    return (signal * (0.9 / peak)).astype(np.float32)


class HarmonyMixin:
    """Аккордовая сетка и гармонические слои для `BeatConstructor`."""

    def _progression(self) -> tuple[int, ...]:
        if getattr(self, "_progression_cache", None) is None:
            self._progression_cache = progression_for(
                getattr(self, "genre", "default"), getattr(self, "seed", None)
            )
        return self._progression_cache

    def _chord_for_bar(self, bar: int) -> list[float]:
        progression = self._progression()
        degree = progression[bar % len(progression)]
        root = self._root_freq() / 2.0
        return chord_freqs(root, degree, minor=not self._is_major(), seventh=(bar % 4 == 3))

    def _generate_harmony(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
        """Пэд + аккордовые стабы для такта (моно, длина такта)."""
        if section in ("breakdown_silent",):
            return np.zeros(bar_samples, dtype=np.float32)

        bar_sec = bar_samples / self.sr
        chord = self._chord_for_bar(bar)
        previous = getattr(self, "_previous_chord", None)
        chord = voice_lead(chord, previous)
        self._previous_chord = chord

        if section in ("intro", "outro", "breakdown", "intro_pad", "outro_fade"):
            pad_gain, keys_gain = 0.36, 0.0
        elif section in ("hook", "chorus"):
            pad_gain, keys_gain = 0.34, 0.20
        else:
            pad_gain, keys_gain = 0.28, 0.12

        out = np.zeros(bar_samples, dtype=np.float32)
        pad = synth_pad(
            self.sr,
            chord,
            bar_sec,
            attack=0.05 if section in ("hook", "chorus") else 0.16,
            brightness=0.7 if section in ("hook", "chorus") else 0.5,
        )
        out += pad[:bar_samples] * pad_gain

        if keys_gain > 0:
            # Стабы на офф-битах: «2» и «4» с человеческим опозданием.
            for step in (6, 14):
                start = int(step * (bar_samples / 16) + self._hit_offset_sec("melody", step, bar) * self.sr)
                start = max(0, min(bar_samples - 1, start))
                stab = synth_keys(self.sr, chord, min(0.45, bar_sec / 2))
                end = min(start + len(stab), bar_samples)
                out[start:end] += stab[: end - start] * keys_gain * self._velocity("melody", step, bar)

        return out
