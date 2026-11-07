# -*- coding: utf-8 -*-
"""
modules/beat/track_assembly.py — пост-обработка собранного бита.

`BeatConstructor.build_track` занимал 252 строки и в одном теле держал план
секций, склейку, дроп перед хуком, лид-мотив, обрезку по длительности,
mid/side-ширину, «человечность» и запись файла. Здесь эти шаги разложены на
функции с одним эффектом каждая; `build_track` стал читаемой сборкой.

Числа (0.30 с провал, S/M≈0.30, панорама ±0.15, гейны 0.12/0.085) взяты один
в один из прежнего кода: это не новая обработка, а та же самая по частям.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable

import numpy as np

LOG = logging.getLogger(__name__)

ROOT_HZ = {
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

HOOK_NAMES = ("hook", "chorus")
MOTIF_NAMES = ("hook", "chorus", "intro")


def section_table(plans: list[Any], bar_sec: float) -> list[dict[str, Any]]:
    """Плоская карта секций для отчёта: имя, такты, старт, громкость."""
    info: list[dict[str, Any]] = []
    for plan in plans:
        info.append(
            {
                "name": plan.name,
                "arrangement_name": plan.source_name or plan.name,
                "bars": plan.bars,
                "start_sec": round(sum(item.bars for item in plans[: len(info)]) * bar_sec, 2),
                "duration_sec": round(plan.bars * bar_sec, 2),
                "energy": plan.energy,
                "gain_db": plan.gain_db,
                "bass_gain": plan.bass_gain,
                "layers": list(plan.layers),
            }
        )
    return info


def apply_drop(track: np.ndarray, section_info: list[dict[str, Any]], sr: int) -> np.ndarray:
    """300 мс глубокий провал перед первым хуком: иначе «drop» не читается."""
    try:
        first_hook_sec = None
        for info in section_info:
            if info["name"] in HOOK_NAMES:
                first_hook_sec = info["start_sec"]
                break
        if first_hook_sec is None:
            return track
        index = int(first_hook_sec * sr)
        fade = int(0.30 * sr)
        if index - fade <= 0:
            return track
        # Степень 4, а не линейный спад: нужен реальный провал тишины (~120 мс).
        env = ((1.0 - np.linspace(0.0, 1.0, fade)) ** 4).astype(np.float32)[:, np.newaxis]
        track[index - fade : index] *= env
    except Exception:
        LOG.debug("ignored exception", exc_info=True)
    return track


def _hook_motif(root: float, major: bool) -> list[float]:
    if major:
        return [root, root * 9 / 8, root * 5 / 4, root * 4 / 3]
    return [root, root * (2 ** (-2 / 12)), root * (2 ** (-5 / 12)), root * (2 ** (-7 / 12))]


def apply_hook_motif(
    track: np.ndarray,
    section_info: list[dict[str, Any]],
    sr: int,
    bpm: int,
    key: str,
    pan: Callable[[np.ndarray, float], np.ndarray],
) -> np.ndarray:
    """Повторяющийся лид-мотив в интро и припевах (hook_repeatability)."""
    try:
        root_name = key.split()[0] if " " in key else "A"
        mode = key.split()[-1].lower() if " " in key else "minor"
        motif = _hook_motif(ROOT_HZ.get(root_name, 440.0), mode.startswith("maj"))
        bar_sec = (60.0 / bpm) * 4
        note_samples = int((bar_sec / 4.0) * sr)
        t = np.arange(note_samples, dtype=np.float32) / sr
        env = np.exp(-t * 4.0) * (1.0 - np.exp(-t * 60.0))
        for info in section_info:
            # Мотив звучит в интро (TikTok-вход) и в припевах; в остальных
            # секциях молчит, чтобы не «замылиться».
            if info["name"] not in MOTIF_NAMES:
                continue
            start = int(info["start_sec"] * sr)
            length = int(info["duration_sec"] * sr)
            position = start
            index = 0
            while position + note_samples < start + length and position + note_samples < len(track):
                freq = motif[index % 4]
                lead = (
                    0.6 * np.sin(2 * np.pi * freq * t)
                    + 0.25 * np.sin(2 * np.pi * freq * 2 * t)
                    + 0.10 * np.sin(2 * np.pi * freq * 3 * t)
                ) * env
                lead_pan = 0.15 if index % 2 == 0 else -0.15
                lead_gain = 0.12 if info["name"] in HOOK_NAMES else 0.085
                track[position : position + note_samples] += (
                    pan(lead.astype(np.float32), lead_pan) * lead_gain
                )
                position += note_samples
                index += 1
    except Exception:
        LOG.debug("ignored exception", exc_info=True)
    return track


def fit_length(track: np.ndarray, target_samples: int) -> np.ndarray:
    """Обрезка/дополнение до запрошенной длительности и нормировка по пику."""
    if len(track) > target_samples:
        track = track[:target_samples]
    elif len(track) < target_samples:
        track = np.pad(track, ((0, target_samples - len(track)), (0, 0)))
    peak = np.max(np.abs(track)) + 1e-9
    if peak > 0:
        track = track / peak * 0.9
    return track


def finalize_stereo(stereo: np.ndarray, sr: int) -> np.ndarray:
    """Финальная mid/side-ширина с сохранением моносовместимости.

    Ранний Haas-mix только в правом канале оставлял corr≈0.986: формально
    стерео, практически моно. Контролируемая S-компонента даёт устойчивую
    ширину без смещения центра и разрушения суммы L+R.
    """
    stereo = np.asarray(stereo, dtype=np.float32).copy()
    try:
        from scipy.signal import butter as _butter
        from scipy.signal import sosfilt as _sosfilt

        if stereo.ndim == 2 and stereo.shape[1] >= 2:
            mid = (stereo[:, 0] + stereo[:, 1]) * 0.5
            side = (stereo[:, 0] - stereo[:, 1]) * 0.5
            high_mid = _sosfilt(
                _butter(4, 800, btype="high", fs=sr, output="sos"), mid
            )
            # Разность исходного и задержанного ВЧ-сигнала декоррелирована
            # с центром; нормируется к доле M, а не добавляет громкость в канал.
            delay = max(1, int(sr * 0.015))
            delayed = np.zeros_like(high_mid)
            delayed[delay:] = high_mid[:-delay]
            width_seed = high_mid - delayed
            seed_rms = float(np.sqrt(np.mean(width_seed**2)) + 1e-12)
            mid_rms = float(np.sqrt(np.mean(mid**2)) + 1e-12)
            side_rms = float(np.sqrt(np.mean(side**2)) + 1e-12)
            # S/M≈0.30 даёт межканальную корреляцию около 0.83–0.95 на
            # синтезированном материале: заметная ширина без инверсии фазы.
            target_side_rms = max(side_rms, mid_rms * 0.30)
            if seed_rms > 1e-8 and mid_rms > 1e-8:
                candidate = side + width_seed * (target_side_rms / seed_rms)
                candidate_rms = float(np.sqrt(np.mean(candidate**2)) + 1e-12)
                side = candidate * (target_side_rms / candidate_rms)
                stereo = np.column_stack((mid + side, mid - side)).astype(
                    np.float32, copy=False
                )
        peak = float(np.max(np.abs(stereo)) + 1e-9)
        if peak > 0.98:
            stereo = stereo / peak * 0.95
    except Exception as exc:
        print(f"[beat_constructor] stereo width fallback: {exc}")
    return stereo


def apply_humanity(stereo: np.ndarray, sr: int, seed: Any) -> tuple[np.ndarray, dict[str, Any]]:
    """«Человеческие шероховатости»: дрейф темпа ±0.2 % и шум комнаты."""
    from modules.beat import microtime

    stereo, humanity = microtime.apply_humanity(stereo, sr, seed=seed if seed is not None else 0)
    peak = float(np.max(np.abs(stereo))) + 1e-9
    if peak > 0.98:
        stereo = stereo / peak * 0.95
    return stereo, humanity


def write_track(out_dir: str, out_name: str, stereo: np.ndarray, sr: int) -> str:
    """WAV с PCM_16; при отказе soundfile — scipy.io.wavfile."""
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, out_name)
    try:
        import soundfile as sf

        sf.write(out_path, stereo, sr, subtype="PCM_16")
    except Exception:
        try:
            from scipy.io import wavfile

            wavfile.write(out_path, sr, (stereo * 32767).astype(np.int16))
        except Exception:
            LOG.debug("ignored exception", exc_info=True)
    return out_path
