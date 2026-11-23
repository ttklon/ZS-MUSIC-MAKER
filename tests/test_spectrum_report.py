# -*- coding: utf-8 -*-
"""Баланс полос микса: измерение, а не обещание.

Окно уже мерило полосы, пайплайн — нет: трек, собранный через `main.py`,
нельзя было проверить на «низ съел середину». Модуль `modules/beat/spectrum.py`
повторяет формулы окна, поэтому числа обязаны совпадать с JS.
"""

from __future__ import annotations

import numpy as np
import pytest

from modules.beat.spectrum import HIGH_HZ, LOW_HZ, WINDOW, spectrum_report

SR = 44100


def _tone(freq: float, seconds: float = 1.0, amplitude: float = 0.5) -> np.ndarray:
    t = np.arange(int(SR * seconds), dtype=np.float64) / SR
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_pure_low_tone_is_low_heavy() -> None:
    report = spectrum_report(_tone(50.0), SR)

    assert report["ok"] is True
    assert report["bands"]["low"] > 0.9
    assert report["low_heavy"] is True
    assert "низ перевесил" in report["reason"]


def test_pure_mid_tone_is_not_low_heavy_but_is_dull() -> None:
    """Один синус в середине: низа нет, но и верха нет — «глухо» это факт.

    Тест ловит и обратное: если бы «dull» считался по середине, трек из одного
    синуса объявлялся бы сбалансированным.
    """
    report = spectrum_report(_tone(1000.0), SR)

    assert report["bands"]["mid"] > 0.9
    assert report["low_heavy"] is False
    assert report["dull"] is True
    assert "глухо" in report["reason"]


def test_high_tone_is_not_dull() -> None:
    report = spectrum_report(_tone(12000.0), SR)

    assert report["bands"]["high"] > 0.5
    assert report["dull"] is False


def test_silence_and_short_signals_are_reported_honestly() -> None:
    silent = spectrum_report(np.zeros(SR, dtype=np.float32), SR)
    short = spectrum_report(np.zeros(WINDOW - 1, dtype=np.float32), SR)

    assert silent["ok"] is False and silent["bands"] is None
    assert short["ok"] is False
    assert "короче окна" in short["reason"]


def test_stereo_input_is_averaged_like_the_desktop_engine() -> None:
    mono = _tone(440.0, 1.0)
    stereo = np.column_stack((mono, mono))

    assert spectrum_report(stereo, SR)["bands"] == spectrum_report(mono, SR)["bands"]


def test_boundaries_match_the_window_port() -> None:
    """Границы полос — часть контракта: окно и пайплайн должны считать одинаково."""
    assert LOW_HZ == 120.0 and MID_HZ_ok()
    assert WINDOW == 4096


def MID_HZ_ok() -> bool:
    from modules.beat.spectrum import MID_HZ

    return MID_HZ == 5000.0


def test_master_report_carries_spectrum(tmp_path) -> None:
    """Мастер обязан приложить измерение: «сбалансировано» без чисел — не факт."""
    import soundfile as sf

    from modules.mastering_reference import master_ai

    source = _tone(60.0, 2.0) * 0.8
    in_wav = tmp_path / "in.wav"
    out_wav = tmp_path / "out.wav"
    sf.write(in_wav, np.column_stack((source, source)), SR, subtype="PCM_16")

    result = master_ai(str(in_wav), str(out_wav))

    assert result.get("ok") is True
    spectrum = result.get("spectrum")
    assert isinstance(spectrum, dict)
    assert spectrum.get("ok") is True
    assert set(spectrum["bands"]) == {"low", "mid", "high"}
    # На входе чистый низ — мастер не должен притворяться, что полосы сбалансированы.
    assert spectrum["bands"]["low"] > 0.8
