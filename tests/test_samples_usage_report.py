# -*- coding: utf-8 -*-
"""Отчёт о сэмплах: «сколько прозвучало», а не «сколько путей в списке».

Баг был тихий и стыдный: `build_track()` отдавал `drum_engine.status =
REAL_PASS` с текстом «drums come from the licensed sample bank» и рядом
`samples_used`, где лежала длина списков (обычно 0). Отчёт сам себе
противоречил, и проверить «сэмплы реально звучат» было нечем.
"""

from __future__ import annotations

import numpy as np
import pytest

from modules.beat_constructor import construct_beat


def _beat(**kwargs) -> dict:
    style = {
        "genre": "drift_phonk", "target_bpm": 140, "target_mode": "minor",
        "key_root": "A", "seed": 5,
    }
    style.update(kwargs.pop("style", {}))
    return construct_beat({}, {}, style, duration_sec=12, out_name="test_samples_report.wav", **kwargs)


def test_samples_used_counts_real_hits_not_list_lengths() -> None:
    report = _beat()

    used = report["samples_used"]
    assert set(used) == {"by_instrument", "by_source", "total", "available"}
    # В репозитории есть лицензионный банк: удары обязаны быть слышны.
    assert used["total"] > 0, "банк есть, а счётчик пуст — отчёт врёт"
    assert used["by_source"].get("bank", 0) > 0
    # Кик, хэт и снейр — основа любого бита в этих жанрах.
    for instrument in ("kick", "hat", "snare"):
        assert used["by_instrument"].get(instrument, 0) > 0, instrument


def test_report_is_consistent_with_drum_engine_status() -> None:
    report = _beat()

    engine = report["drum_engine"]
    if engine["status"] == "REAL_PASS":
        assert report["samples_used"]["by_source"].get("bank", 0) > 0, (
            "REAL_PASS «drums come from the sample bank» без единого сэмпла — ложь"
        )


def test_available_is_separate_from_used() -> None:
    """`available` — что предложено в `samples=`, `by_instrument` — что звучало."""
    report = _beat()

    available = report["samples_used"]["available"]
    assert isinstance(available, dict)
    # Без `samples=` пользовательских файлов нет: все нули — это факт.
    assert all(value == 0 for value in available.values())


def test_counts_are_deterministic_for_same_seed() -> None:
    first = _beat()["samples_used"]
    second = _beat()["samples_used"]

    assert first == second


def test_sample_cache_returns_copies_and_survives_clearing() -> None:
    """Кэш чтения не должен отдавать один и тот же массив: его меняет питч-шифт."""
    from app.audio.samples import clear_sample_cache, read_sample

    path = "data/samples/kick/808-bd-tone0-decay50.wav"
    first = read_sample(path)
    assert first is not None

    first[:] = 0.0  # «испортили» массив, как это делает pitch_shift
    second = read_sample(path)
    assert np.abs(second).max() > 0.01, "кэш вернул испорченный массив"

    clear_sample_cache()
    third = read_sample(path)
    assert np.allclose(second, third)
