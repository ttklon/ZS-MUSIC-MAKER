# -*- coding: utf-8 -*-
"""Параллельный мастеринг стендов: быстрее, но бит-в-бит тот же звук.

Стенды независимы друг от друга, поэтому считаются одновременно. Главное
требование — побитовая эквивалентность: скорость не имеет права менять трек.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from modules import mastering


def _write_mix(path: Path, seconds: float = 3.0, sr: int = 44100) -> Path:
    rng = np.random.default_rng(7)
    t = np.arange(int(seconds * sr)) / sr
    left = 0.2 * np.sin(2 * np.pi * 220 * t) + 0.05 * rng.standard_normal(t.size)
    right = 0.2 * np.sin(2 * np.pi * 220 * t + 0.4) + 0.05 * rng.standard_normal(t.size)
    sf.write(str(path), np.stack([left, right], axis=1).astype(np.float32), sr)
    return path


def test_workers_respect_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZSMM_MASTER_WORKERS", "2")
    assert mastering._stand_workers(8) == 2
    monkeypatch.setenv("ZSMM_MASTER_WORKERS", "1")
    assert mastering._stand_workers(8) == 1
    monkeypatch.setenv("ZSMM_MASTER_WORKERS", "garbage")
    assert mastering._stand_workers(3) >= 1


def test_workers_are_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ZSMM_MASTER_WORKERS", raising=False)
    assert mastering._stand_workers(1) == 1
    assert mastering._stand_workers(64) <= 4


def test_parallel_matches_serial_bit_for_bit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if (os.cpu_count() or 1) < 2:
        pytest.skip("нужно ≥ 2 ядра, чтобы проверить параллельный режим")
    mix = _write_mix(tmp_path / "mix.wav")
    stands = ["streaming", "car"]

    monkeypatch.setenv("ZSMM_MASTER_WORKERS", "1")
    serial = mastering.master_all_stands(str(mix), str(tmp_path / "serial"), stands=stands)

    monkeypatch.setenv("ZSMM_MASTER_WORKERS", "2")
    parallel = mastering.master_all_stands(str(mix), str(tmp_path / "parallel"), stands=stands)

    assert serial["summary"]["gates_passed"] == parallel["summary"]["gates_passed"]
    for stand in stands:
        first, sr_a = sf.read(serial["masters"][stand])
        second, sr_b = sf.read(parallel["masters"][stand])
        assert sr_a == sr_b
        assert np.array_equal(first, second), f"стенд {stand} изменился при параллельном счёте"
        assert serial["reports"][stand]["lufs"] == parallel["reports"][stand]["lufs"]
