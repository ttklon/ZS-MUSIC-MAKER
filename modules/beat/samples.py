# -*- coding: utf-8 -*-
"""
modules/beat/samples.py — банк сэмплов бита: классификация, загрузка, выбор.

Два источника звука:
1. явный список путей (`samples=[...]`) — классификация по имени файла;
2. сэмпловый банк `data/samples/manifest.json` (через `app.audio.samples`) —
   velocity-слои, round-robin и лицензионная чистота.

Если нет ни того, ни другого, голоса синтезируются (`modules/beat/drums.py`)
и это честно отражается в `drum_engine.status`.
"""

from __future__ import annotations

import os

import numpy as np


class SampleBankMixin:
    def _classify_samples(self):
        """Грубо классифицирует сэмплы по имени файла."""
        for s in self.samples:
            name = os.path.basename(s).lower()
            if any(k in name for k in ["kick", "bd", "bass_drum", "808"]):
                self.kick_samples.append(s)
            elif "clap" in name:
                # Клэп — отдельный слой, он играет поверх снейра на 2/4 доле.
                self.clap_samples.append(s)
            elif any(k in name for k in ["openhat", "open_hat", "open-hh", "oh_"]):
                self.open_hat_samples.append(s)
            elif any(k in name for k in ["snare", "sd", "rim"]):
                self.snare_samples.append(s)
            elif any(
                k in name for k in ["hihat", "hat", "hh", "cymbal", "ride", "crash"]
            ):
                self.hihat_samples.append(s)
            elif any(k in name for k in ["bass", "sub", "808_bass", "reese"]):
                self.bass_samples.append(s)
            elif any(
                k in name
                for k in [
                    "melody",
                    "lead",
                    "saz",
                    "sitar",
                    "plucks",
                    "synth",
                    "arp",
                    "chord",
                    "pad",
                ]
            ):
                self.melody_samples.append(s)
            elif any(
                k in name
                for k in ["fx", "rise", "riser", "sweep", "impact", "sfx", "noise"]
            ):
                self.fx_samples.append(s)
            else:
                # Если не классифицировано — кладём в melody как fallback
                self.melody_samples.append(s)


    def _bank(self):
        """Ленивая загрузка манифеста банка (один раз на конструктор)."""
        if getattr(self, "_sample_bank", None) is None:
            try:
                from app.audio.samples import load_bank

                self._sample_bank = load_bank()
            except Exception:
                self._sample_bank = None
        return self._sample_bank

    def _bank_audio(self, instrument: str, velocity: float = 1.0):
        """Сэмпл из банка (mono float32) или None, если банк пуст/не разрешён."""
        bank = self._bank()
        if bank is None:
            return None
        entry = bank.choose(instrument, rng=self._np_rng, velocity=velocity)
        if entry is None:
            return None
        try:
            from app.audio.samples import pitch_shift, read_sample

            audio = read_sample(entry.path, sample_rate=self.sr)
        except Exception:
            return None
        if audio is None or not len(audio):
            return None
        if entry.tuning_hz and instrument in ("kick", "808"):
            # Подстройка тона one-shot'а под тонику трека — иначе низ «спорит».
            import math

            ratio = max(0.5, min(2.0, float(self._root_freq() / entry.tuning_hz)))
            audio = pitch_shift(audio, 12.0 * math.log2(ratio), self.sr)
        return audio

    def _load_audio(self, path: str) -> np.ndarray:
        """Загружает wav/mp3 в numpy массив (mono)."""
        try:
            from pydub import AudioSegment

            seg = AudioSegment.from_file(path)
            if seg.channels > 1:
                seg = seg.set_channels(1)
            seg = seg.set_frame_rate(self.sr)
            samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
            samples = samples / (2**15)  # normalize to -1..1
            return samples
        except Exception as e:
            print(f"[beat_constructor] load fail {path}: {e}")
            return np.zeros(self.sr, dtype=np.float32)
