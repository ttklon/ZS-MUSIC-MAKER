"""
Regression test for v27 P0 fix — unified `modules/mastering.py`.

До v27 отсутствие `modules/mastering.py` валило `_stage_mastering`,
и оркестратор оставлял только `mix_ducked.wav` без `master_*` файлов.
Эти тесты защищают от повторения этой регрессии.
"""

from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest
import soundfile as sf


def _make_stereo_sine(sr: int = 44100, dur_sec: float = 3.0) -> np.ndarray:
    t = np.linspace(0, dur_sec, int(sr * dur_sec), endpoint=False)
    left = 0.3 * np.sin(2 * np.pi * 220 * t).astype(np.float32)
    right = 0.3 * np.sin(2 * np.pi * 224 * t).astype(np.float32)
    return np.stack([left, right], axis=1)


def test_mastering_module_is_importable_by_orchestrator():
    """P0: `from modules import mastering` should never raise ImportError.

    Отсутствие этого модуля до v27 полностью ломало пайплайн после mix.
    """
    from modules import mastering  # noqa: F401
    assert hasattr(mastering, "master_all_stands")
    assert callable(mastering.master_all_stands)


def test_master_all_stands_accepts_stands_kwarg():
    """`_stage_mastering` вызывает `master_all_stands(..., stands=stands)`.
    Функция обязана принимать этот kwarg — иначе стадия молча падает.
    """
    from modules import mastering
    import inspect

    sig = inspect.signature(mastering.master_all_stands)
    assert "stands" in sig.parameters, (
        "master_all_stands must accept 'stands' kwarg — orchestrator "
        "passes stands=... from recipe.wizard_state"
    )


def test_master_all_stands_produces_streaming_master(tmp_path):
    """streaming включается всегда — hit_score / release / stems ждут его."""
    from modules import mastering

    mix = tmp_path / "mix.wav"
    y = _make_stereo_sine()
    sf.write(str(mix), y, 44100, subtype="FLOAT")

    out_dir = tmp_path / "masters"
    res = mastering.master_all_stands(str(mix), str(out_dir), stands=["car"])
    assert res.get("ok"), f"mastering failed: {res}"

    # streaming должен быть добавлен автоматически
    stream_wav = out_dir / "master_streaming.wav"
    assert stream_wav.exists(), (
        "master_streaming.wav must exist even when user asked only for 'car' — "
        "polish/hit_score/release depend on it."
    )

    # стерео должно сохраниться (было — mono-downmix)
    y_out, _ = sf.read(str(stream_wav), always_2d=True)
    assert y_out.shape[1] == 2, "master must be stereo, not mono"


def test_master_lufs_reaches_target_streaming(tmp_path):
    """LUFS master_streaming.wav должен приближаться к target -13.5±3 dB."""
    pytest.importorskip("pyloudnorm")
    import pyloudnorm as pyln
    from modules import mastering

    mix = tmp_path / "mix.wav"
    # тихий вход (RMS≈-20 dBFS) — до v27 pyloudnorm упирался в pedalboard
    # limiter и оставлял мастер на -16 LUFS.
    y = _make_stereo_sine() * 0.35
    sf.write(str(mix), y, 44100, subtype="FLOAT")

    out_dir = tmp_path / "masters"
    res = mastering.master_all_stands(str(mix), str(out_dir), stands=None)
    assert res.get("ok"), f"mastering failed: {res}"

    y_out, sr_out = sf.read(str(out_dir / "master_streaming.wav"), always_2d=True)
    meter = pyln.Meter(sr_out)
    lufs = meter.integrated_loudness(y_out)
    assert -17.0 <= lufs <= -10.0, (
        f"streaming LUFS out of window: got {lufs:.2f}, target ≈ -13.5"
    )


def test_master_rejects_missing_input(tmp_path):
    """Не должно молча создавать «мастера» из воздуха."""
    from modules import mastering

    res = mastering.master_all_stands(
        str(tmp_path / "does_not_exist.wav"), str(tmp_path / "out"),
    )
    assert res.get("ok") is False
    assert "not found" in res.get("reason", "").lower()
    assert not (tmp_path / "out" / "master_streaming.wav").exists()
