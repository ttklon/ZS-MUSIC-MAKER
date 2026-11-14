# -*- coding: utf-8 -*-
"""
TikTok-хукабилити не должна выдавать одно число на все 25-секундные окна.

Как считается: перебираются окна по 25 с с шагом 2 с, и для каждого считается

    score = head_rms / global_med * 30 + overall_rms / global_med * 20

где `head_rms` — RMS первых **двух секунд окна**, а окно, как правило,
начинается в тишине или в самом начале трека. Вдобавок стоит условие
`head_rms > global_med * 0.9`, которое почти никогда не выполняется для
первых секунд. Поэтому почти всегда срабатывает фолбэк `score = 45`,
`+20` в конце — и метрика возвращает **65,0** независимо от трека.

Замер на восьми мастерах движка: 65,0 у всех восьми. Нарезка пробовалась от
20 до 60 секунд — тоже 65,0. Это константа с весом 1,5 (самый большой вес в
модели), то есть 11,5 % итогового балла не измеряют ничего.

Спорить о том, что «правильно» для TikTok, здесь не нужно: достаточно, чтобы
метрика измеряла то, что заявляет — насколько яркий и стабильный участок
трека можно поставить в Reels, и росла, когда такой участок действительно
есть.
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.hit_scorer.hook_metrics import _tiktok_hookability

SR = 22_050


def _samples(path, stereo) -> np.ndarray:
    """Записать и вернуть моно-сэмплы — метрика принимает сигнал, не путь."""
    data = np.asarray(stereo, dtype=np.float32)
    sf.write(str(path), data, SR)
    return data.mean(axis=1)


def _music(seconds: int, loud_span: tuple[float, float] | None = None) -> np.ndarray:
    """Ровный микс; если задан `loud_span`, этот участок громче в 4 раза."""
    t = np.arange(SR * seconds) / SR
    rng = np.random.RandomState(23)
    bass = 0.2 * np.sin(2 * np.pi * 55 * t)
    pad = 0.1 * np.sin(2 * np.pi * 220 * t) + 0.08 * np.sin(2 * np.pi * 330 * t)
    hats = 0.05 * rng.randn(len(t)) * (np.sin(2 * np.pi * 8 * t) > 0)
    mono = bass + pad + hats
    gain = np.ones_like(mono)
    if loud_span is not None:
        start, end = int(loud_span[0] * SR), int(loud_span[1] * SR)
        gain[start:end] = 4.0
    mono = mono * gain
    peak = np.abs(mono).max()
    if peak > 0.95:
        mono = mono * (0.95 / peak)
    return np.stack([mono, mono * 0.95], axis=1)


def test_quiet_start_scores_lower_than_loud_start(tmp_path) -> None:
    """Трек, который сразу бьёт, лучше трека с длинным тихим вступлением."""
    later = _tiktok_hookability(_samples(tmp_path / "quiet.wav", _music(60)), SR)[0]
    early = _tiktok_hookability(
        _samples(tmp_path / "loud.wav", _music(60, loud_span=(0, 25))), SR
    )[0]

    assert early > later, (early, later)
    assert early - later >= 10.0, (early, later)


def test_short_track_is_not_a_constant(tmp_path) -> None:
    """Два разных 20-секундных трека не должны получать одно и то же число."""
    steady = _tiktok_hookability(_samples(tmp_path / "a.wav", _music(20)), SR)[0]
    punchy = _tiktok_hookability(
        _samples(tmp_path / "b.wav", _music(20, loud_span=(0, 8))), SR
    )[0]

    assert steady != punchy, (steady, punchy)


def test_slice_is_named_and_fits_inside_track(tmp_path) -> None:
    score, slice_info = _tiktok_hookability(
        _samples(tmp_path / "c.wav", _music(60, loud_span=(20, 45))), SR
    )

    assert 0.0 <= score <= 100.0, score
    assert slice_info["start_sec"] >= 0.0
    assert slice_info["end_sec"] > slice_info["start_sec"]
    assert slice_info["end_sec"] <= 60.0, slice_info
    assert slice_info["reason"]


def test_short_file_is_honest_about_being_short(tmp_path) -> None:
    score, slice_info = _tiktok_hookability(
        _samples(tmp_path / "d.wav", _music(8)), SR
    )

    assert 0.0 <= score <= 100.0
    assert "коротк" in slice_info["reason"].lower(), slice_info
