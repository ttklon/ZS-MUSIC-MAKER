# -*- coding: utf-8 -*-
"""
modules/beat/samples.py — банк сэмплов бита: классификация и загрузка.

Классификация по имени файла (kick/snare/hat/bass/melody/fx); всё
неопознанное уходит в melody, чтобы сэмпл не потерялся молча.
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
