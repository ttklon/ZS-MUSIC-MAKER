# -*- coding: utf-8 -*-
"""
Структура трека: метрика не должна отдавать значение по умолчанию.

Как было: `_structure_clarity` нормировала кривую RMS (mean/std), искала
точки, где |ΔRMS| > 1.2, и требовала от 3 до 8 таких точек. Но при шаге
STFT 1024 (≈46 мс) соседние кадры различаются на единицы процентов, поэтому
порог 1.2 не достигался **никогда**, найденных точек было 0, и функция
отдавала ветку «меньше 3» — 50,0, если трек длиннее 30 с, и 55,0 через
`except`/ранний выход.

Замер: у восьми мастеров движка разной длины и жанра `raw` был 0 (20 с)
или 12–22 (60 с), а балл — 55,0 у всех. При этом 60-секундный трек получал
итог 82,2 против 71,1 у 20-секундного: часть этой разницы — просто
разрешение метрики по длине, а не структура.

Теперь сравниваются соседние секции (окна по 2 % длины трека) по уровню:
метрика ищет, сколько раз трек заметно меняет плотность, и различает ровный
бит без секций, трек с контрастными секциями и трек с рваной динамикой.
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.hit_scorer.mix_metrics import _structure_clarity

SR = 22_050


def _samples(tmp_path, name, sections) -> tuple[str, np.ndarray]:
    """Трек из секций заданной громкости; пишем в файл, считаем по сэмплам."""
    chunk = SR * 5
    parts = []
    rng = np.random.RandomState(31)
    for gain in sections:
        n = chunk
        t = np.arange(n) / SR
        part = gain * (0.2 * np.sin(2 * np.pi * 55 * t) + 0.1 * np.sin(2 * np.pi * 220 * t))
        part += 0.02 * gain * rng.randn(n)
        parts.append(part)
    mono = np.concatenate(parts)
    mono = mono * (0.9 / np.abs(mono).max())
    stereo = np.stack([mono, mono * 0.9], axis=1)
    path = str(tmp_path / name)
    sf.write(path, stereo.astype(np.float32), SR)
    return path, stereo.mean(axis=1)


def test_flat_beat_has_no_sections(tmp_path) -> None:
    """Ровный бит без секций — это не «хорошая структура»."""
    _, mono = _samples(tmp_path, "flat.wav", [1.0] * 10)

    score, raw = _structure_clarity(mono, SR)

    assert score < 60.0, (score, raw)
    assert raw <= 1, (score, raw)


def test_contrasting_sections_are_seen(tmp_path) -> None:
    """Куплет/припев с реальным контрастом должен находиться."""
    _, mono = _samples(
        tmp_path, "song.wav", [0.3, 0.3, 1.0, 1.0, 0.35, 0.35, 1.0, 1.0, 0.3, 0.3]
    )

    score, raw = _structure_clarity(mono, SR)

    assert raw >= 2, (score, raw)
    assert score >= 70.0, (score, raw)


def test_result_does_not_depend_on_default_branch(tmp_path) -> None:
    """Три разных трека — три разных ответа, а не одно и то же число."""
    _, flat = _samples(tmp_path, "f.wav", [1.0] * 10)
    _, song = _samples(tmp_path, "s.wav", [0.3, 1.0] * 5)
    _, chaotic = _samples(tmp_path, "c.wav", [0.2, 1.0, 0.4, 0.9, 0.25, 1.0, 0.5, 0.8, 0.2, 1.0])

    scores = [_structure_clarity(sig, SR)[0] for sig in (flat, song, chaotic)]

    assert len(set(round(s, 3) for s in scores)) >= 2, scores
    assert max(scores) - min(scores) >= 10.0, scores
