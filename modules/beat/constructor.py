# -*- coding: utf-8 -*-
"""
modules/beat/constructor.py — конструктор бита: состояние, RNG и сборка трека.

`BeatConstructor` наследует три миксина (банк сэмплов, голоса, аранжировка) и
держит только состояние: детерминированный RNG, слоты и сборку секций в WAV.
"""

from __future__ import annotations

import logging

import os
import random

import numpy as np

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

        # Классифицируем сэмплы по типу
        self.kick_samples = []
        self.snare_samples = []
        self.clap_samples = []
        self.hihat_samples = []
        self.open_hat_samples = []
        self.bass_samples = []
        self.melody_samples = []
        self.fx_samples = []
        self._classify_samples()


    def _drum_engine_report(self) -> dict:
        """REAL_PASS, если инструменты берутся из банка, иначе FALLBACK с деталями."""
        report = dict(DRUM_ENGINE)
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
            report["reason"] = "drums come from the licensed sample bank"
        else:
            report["reason"] = (
                "sample bank covers "
                f"{len(covered)} of 6 drum instruments; the rest is synthesised"
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

        all_audio = []
        section_info = []
        for plan in plans:
            audio = self._build_section(plan.name, plan.bars, aggression, plan=plan)
            all_audio.append(audio)
            section_info.append(
                {
                    "name": plan.name,
                    "arrangement_name": plan.source_name or plan.name,
                    "bars": plan.bars,
                    "start_sec": round(sum(item.bars for item in plans[: len(section_info)]) * bar_sec, 2),
                    "duration_sec": round(plan.bars * bar_sec, 2),
                    "energy": plan.energy,
                    "gain_db": plan.gain_db,
                    "bass_gain": plan.bass_gain,
                    "layers": list(plan.layers),
                }
            )

        full_track = np.concatenate(all_audio, axis=0)

        # 300 мс глубокий провал перед первым hook = drop
        try:
            _first_hook_sec = None
            for _info in section_info:
                if _info["name"] in ("hook", "chorus"):
                    _first_hook_sec = _info["start_sec"]
                    break
            if _first_hook_sec is not None:
                _idx = int(_first_hook_sec * self.sr)
                _fade = int(0.30 * self.sr)
                if _idx - _fade > 0:
                    # Степень 4, а не линейный спад: перед дропом должен быть
                    # реальный провал тишины (~120 мс), иначе «drop» не читается.
                    _env = ((1.0 - np.linspace(0.0, 1.0, _fade)) ** 4).astype(
                        np.float32
                    )[:, np.newaxis]
                    full_track[_idx - _fade : _idx] *= _env
        except Exception:
            logging.getLogger(__name__).debug("ignored exception", exc_info=True)

        # v26 FIX (P0): повторяющиеся 4 ноты в припевах → hook_repeatability raw>0
        try:
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
            root_name = self.key.split()[0] if " " in self.key else "A"
            _root = root_freqs.get(root_name, 440.0)
            _mode = self.key.split()[-1].lower() if " " in self.key else "minor"
            _mot = (
                [_root, _root * 9 / 8, _root * 5 / 4, _root * 4 / 3]
                if _mode.startswith("maj")
                else [
                    _root,
                    _root * (2 ** (-2 / 12)),
                    _root * (2 ** (-5 / 12)),
                    _root * (2 ** (-7 / 12)),
                ]
            )
            beat_sec_local = 60.0 / self.bpm
            bar_sec_local = beat_sec_local * 4
            for _info in section_info:
                # Мотив хука обязан звучать в интро (TikTok-вход) и в припевах;
                # в остальных секциях он молчит, чтобы не «замылиться».
                if _info["name"] not in ("hook", "chorus", "intro"):
                    continue
                _hs = int(_info["start_sec"] * self.sr)
                _hn = int(_info["duration_sec"] * self.sr)
                _ns = int((bar_sec_local / 4.0) * self.sr)
                _t = np.arange(_ns, dtype=np.float32) / self.sr
                _env = np.exp(-_t * 4.0) * (1.0 - np.exp(-_t * 60.0))
                _pos = _hs
                _mi = 0
                while _pos + _ns < _hs + _hn and _pos + _ns < len(full_track):
                    _f = _mot[_mi % 4]
                    _lead = (
                        0.6 * np.sin(2 * np.pi * _f * _t)
                        + 0.25 * np.sin(2 * np.pi * _f * 2 * _t)
                        + 0.10 * np.sin(2 * np.pi * _f * 3 * _t)
                    ) * _env
                    # Хук-лид тоже панорамируем слегка для стерео-баланса
                    _lead_pan = 0.15 if _mi % 2 == 0 else -0.15
                    _lead_gain = 0.12 if _info["name"] in ("hook", "chorus") else 0.085
                    full_track[_pos : _pos + _ns] += (
                        self._pan_audio(_lead.astype(np.float32), _lead_pan) * _lead_gain
                    )
                    _pos += _ns
                    _mi += 1
        except Exception:
            logging.getLogger(__name__).debug("ignored exception", exc_info=True)

        # Обрезка/дополнение
        target_samples = int(duration_sec * self.sr)
        if len(full_track) > target_samples:
            full_track = full_track[:target_samples]
        elif len(full_track) < target_samples:
            full_track = np.pad(
                full_track, ((0, target_samples - len(full_track)), (0, 0))
            )
        peak = np.max(np.abs(full_track)) + 1e-9
        if peak > 0:
            full_track = full_track / peak * 0.9

        # v26 FIX (P0): финальная mid/side-ширина с сохранением моносовместимости.
        # Ранний Haas-mix только в правом канале оставлял corr≈0.986: формально
        # stereo, но практически почти моно. Контролируемая S-компонента даёт
        # устойчивую ширину без смещения центра или разрушения суммы L+R.
        stereo = np.asarray(full_track, dtype=np.float32).copy()
        try:
            from scipy.signal import butter as _bt26
            from scipy.signal import sosfilt as _sf26

            if stereo.ndim == 2 and stereo.shape[1] >= 2:
                _mid = (stereo[:, 0] + stereo[:, 1]) * 0.5
                _side = (stereo[:, 0] - stereo[:, 1]) * 0.5
                _sos_hp800 = _bt26(4, 800, btype="high", fs=self.sr, output="sos")
                _high_mid = _sf26(_sos_hp800, _mid)

                # Разность исходного и задержанного ВЧ-сигналов декоррелирована
                # с центром; её нормируем к заданной доле M вместо добавления
                # произвольной громкости в один канал.
                _delay_samples = max(1, int(self.sr * 0.015))
                _delayed = np.zeros_like(_high_mid)
                _delayed[_delay_samples:] = _high_mid[:-_delay_samples]
                _width_seed = _high_mid - _delayed
                _seed_rms = float(np.sqrt(np.mean(_width_seed ** 2)) + 1e-12)
                _mid_rms = float(np.sqrt(np.mean(_mid ** 2)) + 1e-12)
                _side_rms = float(np.sqrt(np.mean(_side ** 2)) + 1e-12)
                # S/M≈0.30 даёт целевую межканальную корреляцию около 0.83–0.95
                # на синтезированном материале: это заметная ширина без инверсии
                # фазы и без потери читаемости центра при сведении в mono.
                _target_side_rms = max(_side_rms, _mid_rms * 0.30)

                if _seed_rms > 1e-8 and _mid_rms > 1e-8:
                    _candidate_side = _side + _width_seed * (_target_side_rms / _seed_rms)
                    _candidate_rms = float(
                        np.sqrt(np.mean(_candidate_side ** 2)) + 1e-12
                    )
                    _side = _candidate_side * (_target_side_rms / _candidate_rms)
                    stereo = np.column_stack((_mid + _side, _mid - _side)).astype(
                        np.float32, copy=False
                    )

            _pk = float(np.max(np.abs(stereo)) + 1e-9)
            if _pk > 0.98:
                stereo = stereo / _pk * 0.95
        except Exception as exc:
            print(f"[beat_constructor] stereo width fallback: {exc}")

        # «Человеческие шероховатости» (план 4.7.2): дрейф темпа ±0.2 % и шум
        # комнаты. Применяются к уже сведённому стерео — до этого момента
        # политика ширины и уровня не меняется.
        from modules.beat import microtime, variation

        stereo, humanity = microtime.apply_humanity(
            stereo, self.sr, seed=self.seed if self.seed is not None else 0
        )
        _peak_after = float(np.max(np.abs(stereo))) + 1e-9
        if _peak_after > 0.98:
            stereo = stereo / _peak_after * 0.95

        out_dir = output_dir()
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, out_name)
        try:
            import soundfile as sf

            sf.write(out_path, stereo, self.sr, subtype="PCM_16")
        except Exception:
            try:
                from scipy.io import wavfile

                # Стерео запись через wavfile
                wavfile.write(out_path, self.sr, (stereo * 32767).astype(np.int16))
            except Exception:
                logging.getLogger(__name__).debug("ignored exception", exc_info=True)

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
            "samples_used": {
                "kicks": len(self.kick_samples),
                "snares": len(self.snare_samples),
                "claps": len(self.clap_samples),
                "hihats": len(self.hihat_samples),
                "open_hihats": len(self.open_hat_samples),
                "bass": len(self.bass_samples),
                "melody": len(self.melody_samples),
                "fx": len(self.fx_samples),
            },
        }
