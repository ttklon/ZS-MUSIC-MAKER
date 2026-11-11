# -*- coding: utf-8 -*-
"""
Оценка хита должна слышать клиппинг.

Замер на настоящем бите движка (30 с, мастер стенда streaming, база 69,23):

    как есть            69,23  solid
    клиппинг ×6         69,11  solid     ← минус 0,12
    кирпич tanh         69,73  solid     ← плюс 0,50

Трек, вдавленный в потолок, получал ту же оценку, что чистый мастер: в
наборе метрик не было ничего про искажения. Это самый дорогой вид брака —
его слышно на всех площадках, и человек узнаёт о нём уже после релиза.
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.hit_scorer.scoring import score_track

SR = 22_050
SECONDS = 20


def _clean_music() -> np.ndarray:
    """Простой, но живой микс: бас, аккорд, шум — без клиппинга."""
    rng = np.random.RandomState(3)
    t = np.arange(SR * SECONDS) / SR
    bass = 0.3 * np.sin(2 * np.pi * 55 * t)
    chord = 0.12 * np.sin(2 * np.pi * 220 * t) + 0.1 * np.sin(2 * np.pi * 277 * t)
    hats = 0.04 * rng.randn(len(t)) * (np.sin(2 * np.pi * 4 * t) > 0.3)
    left = bass + chord + hats
    right = bass + 0.9 * chord + 0.9 * hats
    return np.stack([left, right], axis=1)


def _write(path, stereo) -> str:
    sf.write(str(path), np.asarray(stereo, dtype=np.float32), SR)
    return str(path)


def test_clean_mix_has_no_distortion_penalty(tmp_path) -> None:
    report = score_track(_write(tmp_path / "clean.wav", _clean_music()))

    assert "distortion" in report["metrics"], "метрики искажений нет"
    assert report["metrics"]["distortion"]["score"] >= 65, report["metrics"]["distortion"]


def test_hard_clipping_is_heard_and_costs_points(tmp_path) -> None:
    mix = _clean_music()
    clean = score_track(_write(tmp_path / "clean.wav", mix))
    clipped = score_track(_write(tmp_path / "clipped.wav", np.clip(mix * 6.0, -1.0, 1.0)))

    assert clipped["metrics"]["distortion"]["score"] < 40, clipped["metrics"]["distortion"]
    assert clipped["metrics"]["distortion"]["raw"]["clipped_share"] > 0.01
    # Раньше разница была −0,12 балла; теперь искажение обязано стоить заметно.
    assert clean["hit_score"] - clipped["hit_score"] >= 8, (
        clean["hit_score"],
        clipped["hit_score"],
    )


def test_clipped_master_is_not_called_solid(tmp_path) -> None:
    mix = _clean_music()
    squashed = np.tanh(mix * 12.0) * 0.99
    report = score_track(_write(tmp_path / "squashed.wav", squashed))

    assert report["verdict"] != "solid", report["verdict"]
    assert any("клипп" in action.lower() or "искажен" in action.lower() for action in report["actions"]), (
        report["actions"]
    )


def test_silence_still_wins_over_distortion_check(tmp_path) -> None:
    """Пустой файл остаётся invalid_audio, а не «искажённым треком»."""
    report = score_track(_write(tmp_path / "silence.wav", np.zeros((SR * SECONDS, 2))))

    assert report["verdict"] == "invalid_audio"
