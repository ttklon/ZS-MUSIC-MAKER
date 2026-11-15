# -*- coding: utf-8 -*-
"""
modules/beat/constructor.py — конструктор бита: состояние, RNG и сборка трека.

`BeatConstructor` наследует три миксина (банк сэмплов, голоса, аранжировка) и
держит только состояние: детерминированный RNG, слоты и сборку секций в WAV.
"""

from __future__ import annotations

import random

import numpy as np

from modules.beat import track_assembly, variation
from modules.beat.arrangement import ArrangementMixin
from modules.beat.dramaturgy import plan_sections, sections_from_arrangement, structure_report
from modules.beat.drums import CAPABILITIES as DRUM_ENGINE
from modules.beat.harmony import HarmonyMixin
from modules.beat.paths import output_dir
from modules.beat.patterns import (
    LEGACY_SLOT_PRESET,
    family_for_genre,
    slot_preset_for_genre,
    velocity_map_for_genre,
)
from modules.beat.samples import SampleBankMixin
from modules.beat.voices import VoicesMixin


class BeatConstructor(SampleBankMixin, VoicesMixin, ArrangementMixin, HarmonyMixin):
    """Конструктор оригинального бита из сэмплов + groove template."""

    def __init__(
        self,
        bpm: int = 128,
        key: str = "A minor",
        groove: dict = None,
        samples: list = None,
        genre: str = "legacy",
        seed: int | None = None,
    ):
        self.bpm = bpm
        self.key = key
        self.genre = genre
        self.seed = None if seed is None else int(seed)
        self._py_rng = random if self.seed is None else random.Random(self.seed)
        self._np_rng = None if self.seed is None else np.random.default_rng(self.seed)
        self.groove = groove or {}
        self.slot_patterns = (
            {slot: list(values) for slot, values in LEGACY_SLOT_PRESET.items()}
            if genre == "legacy"
            else slot_preset_for_genre(genre)
        )
        self.velocity_map = (
            {slot: [1.0] * 16 for slot in self.slot_patterns}
            if genre == "legacy"
            else velocity_map_for_genre(genre)
        )
        for slot, groove_key in (("kick", "kick_pattern"), ("snare", "snare_pattern"), ("hat", "hat_pattern"), ("bass", "bass_pattern"), ("melody", "melody_pattern")):
            if isinstance(self.groove.get(groove_key), list) and len(self.groove[groove_key]) == 16:
                self.slot_patterns[slot] = [int(bool(value)) for value in self.groove[groove_key]]
        self.samples = samples or []  # список путей к wav-файлам сэмплов
        self.sr = 44100
        # Отказы загрузки сэмплов: пустой список означает «все прочитались».
        # Раньше неудача молча возвращала секунду тишины и нигде не отмечалась.
        self.sample_load_errors: list[dict] = []

        # Классифицируем сэмплы по типу
        self.kick_samples = []
        self.snare_samples = []
        self.clap_samples = []
        self.hihat_samples = []
        self.open_hat_samples = []
        self.bass_samples = []
        self.melody_samples = []
        self.fx_samples = []
        # Сколько сэмплов реально прозвучало: раньше отчёт отдавал длину
        # списков путей (обычно 0), то есть «0 сэмплов» рядом с честным
        # `REAL_PASS` «drums come from the sample bank».
        self.samples_used: dict[str, int] = {}
        self.sample_source_used: dict[str, int] = {}
        self._classify_samples()

    def _samples_used_report(self) -> dict:
        """Фактически прозвучавшие сэмплы: по инструментам и по источникам.

        `available` — что было предложено (пути из `samples=`), `by_instrument`
        — что реально попало в трек. Раньше отчёт отдавал длину списков путей
        рядом с `REAL_PASS` «drums come from the sample bank», то есть
        утверждение без факта и противоречие самому себе.
        """
        return {
            "by_instrument": dict(self.samples_used),
            "by_source": dict(self.sample_source_used),
            "total": sum(self.samples_used.values()),
            "available": {
                "kick": len(self.kick_samples),
                "snare": len(self.snare_samples),
                "clap": len(self.clap_samples),
                "hat": len(self.hihat_samples),
                "open_hat": len(self.open_hat_samples),
                "bass": len(self.bass_samples),
                "melody": len(self.melody_samples),
                "fx": len(self.fx_samples),
            },
        }

    def note_sample(self, instrument: str, source_is_bank: bool) -> None:
        """Учесть прозвучавший сэмпл: инструмент и источник (банк/файл)."""
        self.samples_used[instrument] = self.samples_used.get(instrument, 0) + 1
        key = "bank" if source_is_bank else "file"
        self.sample_source_used[key] = self.sample_source_used.get(key, 0) + 1


    def _drum_engine_report(self) -> dict:
        """REAL_PASS, если инструменты берутся из банка, иначе FALLBACK с деталями."""
        report = dict(DRUM_ENGINE)
        # Отказы загрузки пользовательских сэмплов видны в отчёте: иначе
        # трек звучит синтезом, хотя сэмплы были переданы и «приняты».
        if getattr(self, "sample_load_errors", None):
            report["sample_load_errors"] = list(self.sample_load_errors)
        try:
            from app.audio.samples import capability

            bank = capability(self._bank())
        except Exception:
            return report
        covered = [name for name in bank.get("instruments_with_samples", []) if name in
                   ("kick", "snare", "clap", "hat", "open_hat", "808")]
        report["sample_bank"] = {
            "instruments_with_samples": covered,
            "total_samples": bank.get("total_samples", 0),
        }
        if len(covered) >= 4:
            report["status"] = "REAL_PASS"
            # Имя движка не врёт: барабаны действительно из банка, синтез
            # остаётся только для перкуссии/импактов, которых в банке нет.
            report["engine"] = "sample_bank+procedural"
            report["reason"] = "удары взяты из лицензионного банка сэмплов"
        else:
            report["reason"] = (
                f"банк покрывает {len(covered)} из 6 барабанных инструментов, "
                "остальное синтезировано"
            )
        return report

    def _random(self) -> float:
        return self._py_rng.random()


    def _choice(self, values):
        return self._py_rng.choice(values)


    def _uniform(self, low: float, high: float) -> float:
        return self._py_rng.uniform(low, high)


    def _noise(self, size: int) -> np.ndarray:
        return np.random.randn(size) if self._np_rng is None else self._np_rng.standard_normal(size)


    def build_slot_plan(self, bars: int = 8) -> dict[str, list[int]]:
        """Expose the exact five 16-step slots used for a fixed number of bars."""
        if bars < 1:
            raise ValueError("bars must be positive")
        return {slot: pattern * bars for slot, pattern in self.slot_patterns.items()}


    def build_track(
        self,
        duration_sec: int = 120,
        n_verses: int = 2,
        n_choruses: int = 2,
        aggression: float = 0.7,
        include_intro: bool = True,
        include_outro: bool = True,
        out_name: str = "constructed_beat.wav",
        sections: list | None = None,
    ) -> dict:
        """
        Полная сборка трека.
        Структура: intro → verse1 → pre_chorus → chorus1 → verse2 → pre_chorus → chorus2 → outro

        `sections` — готовый план секций (из планировщика аранжировки). Если он
        передан, бит следует ему, а не строит собственную сетку; `None`
        сохраняет прежнее поведение бит-в-бит.

        Тело — сборка: пост-обработка вынесена в `modules/beat/track_assembly.py`
        (дроп, лид-мотив, ширина, «человечность», запись), чтобы шаги читались
        и проверялись по отдельности.
        """
        beat_sec = 60.0 / self.bpm
        bar_sec = beat_sec * 4

        # Структуру задаёт драматургия: энергия секций, потолок плотности и
        # правило «хук в первые 15 секунд» вместо жёстких 8/4/8 тактов.
        plans = (
            sections_from_arrangement(sections, self.bpm)
            if sections
            else plan_sections(
                bpm=self.bpm,
                duration_sec=duration_sec,
                include_intro=include_intro,
                include_outro=include_outro,
                n_verses=n_verses,
                n_choruses=n_choruses,
            )
        )
        self.dramaturgy = structure_report(plans, self.bpm)

        all_audio = [
            self._build_section(plan.name, plan.bars, aggression, plan=plan) for plan in plans
        ]
        section_info = track_assembly.section_table(plans, bar_sec)
        full_track = np.concatenate(all_audio, axis=0)

        full_track = track_assembly.apply_drop(full_track, section_info, self.sr)
        full_track = track_assembly.apply_hook_motif(
            full_track, section_info, self.sr, self.bpm, self.key, self._pan_audio
        )
        full_track = track_assembly.fit_length(full_track, int(duration_sec * self.sr))
        stereo = track_assembly.finalize_stereo(full_track, self.sr)
        # «Человеческие шероховатости» (план 4.7.2): дрейф темпа ±0.2 % и шум
        # комнаты — к уже сведённому стерео, политика ширины не меняется.
        stereo, humanity = track_assembly.apply_humanity(stereo, self.sr, self.seed)
        out_path = track_assembly.write_track(output_dir(), out_name, stereo, self.sr)

        return {
            "ok": True,
            "beat_path": out_path,
            "duration_sec": round(len(full_track) / self.sr, 2),
            "bpm": self.bpm,
            "key": self.key,
            "seed": self.seed,
            "deterministic": self.seed is not None,
            "sections": section_info,
            "drum_engine": self._drum_engine_report(),
            "groove_family": family_for_genre(self.genre),
            "dramaturgy": getattr(self, "dramaturgy", None),
            "humanity": humanity,
            "repetition": variation.repetition_report(stereo, self.sr, self.bpm),
            "slot_plan": self.build_slot_plan(max(1, sum(s["bars"] for s in section_info))),
            "total_bars": sum(s["bars"] for s in section_info),
            "samples_used": self._samples_used_report(),
        }
