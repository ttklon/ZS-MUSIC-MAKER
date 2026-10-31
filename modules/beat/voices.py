# -*- coding: utf-8 -*-
"""
modules/beat/voices.py — синтез отдельных голосов бита.

Kick, snare, hihat, бас-линия, мелодия, FX и панорамирование. Каждый голос
использует детерминированный RNG конструктора, а не глобальный random.

Сэмпл из банка всегда приоритетнее синтеза; синтез помечен `FALLBACK`
(см. `modules/beat/drums.py`). Velocity, микротайминг и round-robin берутся
из `modules/beat/humanize.py`, поэтому бит не звучит «по линеечке».
"""

from __future__ import annotations

import math

import numpy as np

from modules.beat import drums, humanize

ROOT_FREQS = {
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

KICK_VARIANTS = 3
SNARE_VARIANTS = 3
HAT_VARIANTS = 4


class VoicesMixin:
    def _rng_noise(self):
        """Генератор шума для синтеза: детерминирован seed'ом конструктора."""
        return self._np_rng if self._np_rng is not None else np.random.default_rng(0)

    def _step_ms(self) -> float:
        return (60_000.0 / float(self.bpm)) / 4.0

    def _hit_offset_sec(self, part: str, step: int, bar: int) -> float:
        offset_ms = humanize.timing_offset_ms(
            self._uniform,
            part,
            step,
            bar,
            swing=self.groove.get("swing", 0.0) or 0.0,
            step_ms=self._step_ms(),
        )
        # Ограничение ±9 мс: дальше это уже не грув, а рассинхрон.
        return float(np.clip(offset_ms, -9.0, 9.0)) / 1000.0

    def _velocity(self, part: str, step: int, bar: int, ghost: bool = False) -> float:
        return humanize.velocity_gain(
            self._random, self._uniform, part, step, bar, ghost=ghost
        )

    def _generate_kick(self, step: int, bar: int) -> np.ndarray:
        """Кик: сэмпл банка или синтез с питч-конвертом и кликом."""
        kick_pattern = list(self.slot_patterns["kick"])
        # Сбивка в конце 4-тактовой фразы: три удара вместо ровной доли.
        if bar % 4 == 3 and step >= 12:
            kick_pattern = [0] * 12 + [1, 0, 1, 1]

        if kick_pattern[step % len(kick_pattern)] == 0:
            return np.zeros(1, dtype=np.float32)

        velocity = self._velocity("kick", step, bar)

        if self.kick_samples:
            kick_path = self.kick_samples[
                humanize.variant_index(self._random, len(self.kick_samples))
            ]
            return self._load_audio(kick_path) * velocity * drums.INSTRUMENT_GAIN["kick"]

        variant = humanize.variant_index(self._random, KICK_VARIANTS)
        tune = 1.0 + (variant - 1) * 0.035
        decay = 0.23 + 0.03 * variant
        return (
            drums.synth_kick(self.sr, self._rng_noise(), tune=tune, decay=decay)
            * velocity
            * drums.INSTRUMENT_GAIN["kick"]
        )

    def _generate_snare(self, step: int, bar: int) -> np.ndarray:
        """Снейр/клэп: сэмпл, синтез корпуса+шума или ghost-нота."""
        snare_pattern = self.slot_patterns["snare"]
        is_ghost = humanize.ghost_note(self._random, "snare", step)
        if snare_pattern[step % 16] == 0 and not is_ghost:
            return np.zeros(1, dtype=np.float32)

        position = step % 16
        # На 2 и 4 доле бита — клэп поверх снейра (типично для phonk/trap).
        wants_clap = bool(self.clap_samples) and position in (4, 12) and bar % 2 == 1
        velocity = self._velocity("snare", step, bar, ghost=is_ghost)

        if self.snare_samples:
            snare_path = self.snare_samples[
                humanize.variant_index(self._random, len(self.snare_samples))
            ]
            hit = self._load_audio(snare_path)
        else:
            variant = humanize.variant_index(self._random, SNARE_VARIANTS)
            hit = drums.synth_snare(
                self.sr,
                self._rng_noise(),
                tune=1.0 + (variant - 1) * 0.03,
                decay=0.155 + 0.012 * variant,
                bright=1.0 + 0.08 * variant,
            )

        if wants_clap:
            hit = hit * 0.75 + drums.synth_clap(self.sr, self._rng_noise()) * 0.55
        return hit * velocity * drums.INSTRUMENT_GAIN["snare"]

    def _generate_hihat(self, step: int, bar: int) -> np.ndarray:
        """Хэт: закрытый/открытый, round-robin тембров, свинг по нечётным."""
        density = self.groove.get("hihat_density", 0.5)
        swing = self.groove.get("swing", 0.0) or 0.0

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

        velocity = self._velocity("hat", step, bar)
        # Открытый хэт — на последней шестнадцатой такта, как в живом груве.
        open_hat = (step % 16 == 15) and bar % 2 == 1

        if self.hihat_samples:
            if open_hat and self.open_hat_samples:
                hat_path = self.open_hat_samples[
                    humanize.variant_index(self._random, len(self.open_hat_samples))
                ]
            else:
                hat_path = self.hihat_samples[
                    humanize.variant_index(self._random, len(self.hihat_samples))
                ]
            return self._load_audio(hat_path) * velocity * drums.INSTRUMENT_GAIN["hat"]

        variant = humanize.variant_index(self._random, HAT_VARIANTS)
        tone = 1.0 + (variant - 1) * 0.045
        return (
            drums.synth_hat(
                self.sr,
                self._rng_noise(),
                open_hat=open_hat,
                tune=tone,
                metallic=0.66 + 0.06 * variant,
            )
            * velocity
            * drums.INSTRUMENT_GAIN["hat"]
        )

    def _root_freq(self) -> float:
        root = self.key.split()[0] if " " in self.key else "A"
        return ROOT_FREQS.get(root, 440.0)

    def _is_major(self) -> bool:
        return self.key.split()[-1].lower().startswith("maj") if " " in self.key else False

    def _bass_note_freq(self, index: int) -> float:
        """Ноты баса по ступеням лада, на октаву ниже тоники."""
        major = (0, 2, 4, 7)
        minor = (0, -2, -5, -7)
        steps = major if self._is_major() else minor
        semitones = steps[index % len(steps)]
        return (self._root_freq() / 2.0) * (2.0 ** (semitones / 12.0))

    def _generate_bass_line(self, bar: int, bar_samples: int) -> np.ndarray:
        """Генерирует басовую линию для такта."""
        if self.bass_samples:
            bass_path = self.bass_samples[
                humanize.variant_index(self._random, len(self.bass_samples))
            ]
            bass = self._load_audio(bass_path)
            if len(bass) < bar_samples:
                bass = np.pad(bass, (0, bar_samples - len(bass)))
            return bass[:bar_samples] * 0.8

        bass_pattern = self.slot_patterns["bass"]
        bass = np.zeros(bar_samples, dtype=np.float32)

        step_len = bar_samples // 16
        note_index = 0
        for i, play in enumerate(bass_pattern):
            if not play:
                continue
            offset = int(self._hit_offset_sec("bass", i, bar) * self.sr)
            start = max(0, min(bar_samples - 1, i * step_len + offset))
            end = min(start + step_len * 2, bar_samples)
            note = drums.synth_808(
                self.sr,
                self._bass_note_freq(note_index),
                (end - start) / self.sr,
                self._rng_noise(),
                glide=0.028,
                drive=1.7 + 0.2 * (bar % 2),
            )
            bass[start:end] += (
                note[: end - start]
                * drums.INSTRUMENT_GAIN["bass808"]
                * self._velocity("bass", i, bar)
            )
            note_index += 1

        return bass

    def _generate_melody(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
        """Генерирует мелодический слой для такта."""
        # В брейках/интро мелодия плотнее, в дропе — реже
        if section in ("intro", "breakdown", "outro") and self.melody_samples:
            mel_path = self.melody_samples[
                humanize.variant_index(self._random, len(self.melody_samples))
            ]
            mel = self._load_audio(mel_path)
            if len(mel) < bar_samples:
                mel = np.pad(mel, (0, bar_samples - len(mel)))
            return mel[:bar_samples] * 0.4

        if section == "verse" and self.melody_samples and bar % 2 == 0:
            mel_path = self.melody_samples[
                humanize.variant_index(self._random, len(self.melody_samples))
            ]
            mel = self._load_audio(mel_path) * 0.25
            if len(mel) < bar_samples:
                mel = np.pad(mel, (0, bar_samples - len(mel)))
            return mel[:bar_samples]

        return np.zeros(bar_samples, dtype=np.float32)

    def _generate_fx(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
        """Генерирует FX (райзеры, импакты) в переходах."""
        # Райзер перед дропом
        if section == "pre_chorus" and self.fx_samples:
            fx_path = self.fx_samples[
                humanize.variant_index(self._random, len(self.fx_samples))
            ]
            fx = self._load_audio(fx_path)
            if len(fx) < bar_samples:
                fx = np.pad(fx, (0, bar_samples - len(fx)))
            return fx[:bar_samples] * 0.5

        # Импакт на первом такте хука: низа становится заметно больше.
        if section in ("hook", "chorus") and bar == 0:
            impact = drums.synth_sub_impact(self.sr, self._rng_noise())
            out = np.zeros(bar_samples, dtype=np.float32)
            length = min(len(impact), bar_samples)
            out[:length] = impact[:length] * drums.INSTRUMENT_GAIN["impact"]
            return out

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
