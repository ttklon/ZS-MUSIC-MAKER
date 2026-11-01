# -*- coding: utf-8 -*-
"""
modules/beat/arrangement.py — сборка секции трека из тактов.

Секция собирает голоса по 16-шаговой сетке с humanize, акцентами и
переходами; результат всегда стерео.
"""

from __future__ import annotations


import numpy as np

from modules.beat import humanize


class ArrangementMixin:
    def _build_section(
        self, section: str, n_bars: int, aggression: float = 0.7, plan=None
    ) -> np.ndarray:
        """Строит секцию трека из нескольких тактов (СТЕРЕО)."""
        beat_sec = 60.0 / self.bpm
        bar_sec = beat_sec * 4
        bar_samples = int(self.sr * bar_sec)
        step_samples = bar_samples // 16

        section_audio = np.zeros((bar_samples * n_bars, 2), dtype=np.float32)
        # Потолок плотности из драматургии: в куплете не должно звучать всё сразу.
        layers = set(plan.layers) if plan is not None else {
            "drums", "bass", "pad", "keys", "melody", "fx"
        }

        for bar in range(n_bars):
            bar_start = bar * bar_samples
            bar_audio = np.zeros((bar_samples, 2), dtype=np.float32)

            # Басовая линия (центр)
            if section not in ("intro_pad", "breakdown_silent", "outro_fade") and "bass" in layers:
                bass = self._generate_bass_line(bar, bar_samples)
                bar_audio += self._pan_audio(bass, 0.0)

            # Драм-паттерн. Каждый удар ставится со своим микротаймингом:
            # ровно по сетке играет только метроном.
            if section not in ("intro_pad", "breakdown_silent") and "drums" in layers:
                for step in range(16):
                    step_start = step * step_samples

                    # Кик всегда в центре
                    kick = self._generate_kick(step, bar)
                    kick_at = max(0, step_start + int(self._hit_offset_sec("kick", step, bar) * self.sr))
                    kick_end = min(kick_at + len(kick), bar_samples)
                    bar_audio[kick_at:kick_end] += self._pan_audio(
                        kick[: kick_end - kick_at], 0.0
                    )

                    # Снейр/клэп почти в центре
                    snare = self._generate_snare(step, bar)
                    snare_at = max(
                        0, step_start + int(self._hit_offset_sec("snare", step, bar) * self.sr)
                    )
                    snare_end = min(snare_at + len(snare), bar_samples)
                    bar_audio[snare_at:snare_end] += self._pan_audio(
                        snare[: snare_end - snare_at], self._uniform(-0.05, 0.05)
                    )

                    # Хэты панорамируем (шире для стерео-поля)
                    hh = self._generate_hihat(step, bar)
                    hh_at = max(0, step_start + int(self._hit_offset_sec("hat", step, bar) * self.sr))
                    hh_end = min(hh_at + len(hh), bar_samples)
                    hh_pan = 0.45 if step % 2 == 0 else -0.45
                    bar_audio[hh_at:hh_end] += self._pan_audio(
                        hh[: hh_end - hh_at], hh_pan
                    )

                # Сбивка в конце фразы: 32-е на малом, тише и с нарастанием.
                fill_steps = humanize.ghost_roll_steps(humanize.is_fill_bar(bar))
                if fill_steps and section in ("verse", "pre_chorus", "hook", "chorus"):
                    for index, roll_step in enumerate(fill_steps):
                        roll_at = roll_step * step_samples
                        roll = self._generate_snare(14, bar)
                        crescendo = 0.35 + 0.2 * index
                        roll_end = min(roll_at + len(roll), bar_samples)
                        bar_audio[roll_at:roll_end] += self._pan_audio(
                            roll[: roll_end - roll_at] * crescendo, self._uniform(-0.08, 0.08)
                        )

            # Гармония: пэд + аккордовые стабы (основа «трека», не только ритм)
            if section not in ("breakdown_silent",) and layers & {"pad", "keys"}:
                bar_audio += self._pan_audio(
                    self._generate_harmony(bar, section, bar_samples), 0.0
                )

            # Мелодия (шире). В «бедной» секции её нет — это анти-«каша».
            if "melody" in layers:
                mel = self._generate_melody(bar, section, bar_samples)
                bar_audio += self._pan_audio(mel, self._uniform(-0.6, 0.6))

            # FX (очень широко)
            if "fx" in layers:
                fx = self._generate_fx(bar, section, bar_samples)
                bar_audio += self._pan_audio(fx, self._uniform(-0.85, 0.85))

            # Микро-мутации: во второй половине секции меняем хэт
            if bar >= n_bars // 2 and section in ("verse", "hook"):
                # Добавляем доп. хэты на офф-битах
                for off_step in [7, 15]:
                    os_start = off_step * step_samples
                    extra_hh = self._generate_hihat(off_step, bar) * 0.3 * aggression
                    os_end = min(os_start + len(extra_hh), bar_samples)
                    bar_audio[os_start:os_end] += self._pan_audio(
                        extra_hh[: os_end - os_start], 0.2
                    )

            # Аварийная защита такта, а не нормализация.
            # Раньше такт делился на пик при peak > 1.0 — это давало слышимую
            # « pump»-качку уровня от такта к такту. Теперь гейн меняется только
            # при реальном перегрузе, а общий уровень выставляет финальная
            # нормализация трека.
            peak = np.max(np.abs(bar_audio)) + 1e-9
            if peak > 1.25:
                bar_audio = bar_audio / peak * 1.1

            section_audio[bar_start : bar_start + bar_samples] = bar_audio

        # v26 FIX (P0): секционный gain-envelope (ранее hit_scorer._hook_energy
        # видел peak/median ≈ 1.05 → score 11/100). Теперь verse -4 dB,
        # hook +0 dB, intro/outro -8 dB → честный громкостной контраст.
        _sec_gain_db = {
            "intro": -8.0,
            "intro_pad": -10.0,
            "verse": -4.0,
            "pre_chorus": -2.0,
            "hook": 0.0,
            "chorus": 0.0,
            "breakdown": -8.0,
            "breakdown_silent": -60.0,
            "outro": -8.0,
            "outro_fade": -10.0,
        }.get(section, -2.0)
        section_audio = section_audio * (10.0 ** (_sec_gain_db / 20.0))

        return section_audio
