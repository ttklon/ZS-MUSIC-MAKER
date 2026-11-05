# -*- coding: utf-8 -*-
"""
Гейт 4.2.4: контраст дропа по низу ≥ 6 дБ и читаемый провал перед хуком.

Это проверка на слух в числах: в куплете низ «суше» (LOW_TRIM), в дропе
добавляются саб-хвосты кика и саб-слой, а перед хуком есть провал тишины.
"""

from __future__ import annotations

import random

import numpy as np
import pytest
import soundfile as sf

from modules.beat_constructor import BeatConstructor

pytest.importorskip("scipy.signal", reason="нужен фильтр для измерения низа")


def _render(genre: str, seed: int, duration: int = 120) -> dict:
    np.random.seed(seed)
    random.seed(seed)
    constructor = BeatConstructor(
        bpm=128, key="A minor", genre=genre, groove={"hihat_density": 0.45, "swing": 0.1}, seed=seed
    )
    return constructor.build_track(duration_sec=duration, out_name=f"contrast_gate_{seed}.wav")


def _low_band(path: str) -> tuple[np.ndarray, int]:
    from scipy.signal import butter, sosfilt

    data, sr = sf.read(path, always_2d=True)
    mono = data.mean(axis=1)
    sos = butter(3, 120.0, btype="low", fs=sr, output="sos")
    return sosfilt(sos, mono).astype(np.float32), sr


def _section_rms(low: np.ndarray, sr: int, section: dict, margin_sec: float = 1.0) -> float:
    start = int((section["start_sec"] + margin_sec) * sr)
    end = int((section["start_sec"] + section["duration_sec"] - margin_sec) * sr)
    segment = low[max(0, start) : max(1, end)]
    return float(np.sqrt(np.mean(segment**2))) if len(segment) else 0.0


@pytest.mark.parametrize("genre,seed", [("drift phonk", 7), ("trap", 11), ("tech house", 23)])
def test_drop_low_end_contrast_is_at_least_six_db(genre: str, seed: int) -> None:
    result = _render(genre, seed)
    low, sr = _low_band(result["beat_path"])
    sections = result["sections"]

    verse = np.mean([_section_rms(low, sr, s) for s in sections if s["name"] == "verse"])
    hook = np.mean([_section_rms(low, sr, s) for s in sections if s["name"] == "hook"])
    contrast_db = 20.0 * np.log10(max(hook, 1e-9) / max(verse, 1e-9))

    assert contrast_db >= 6.0, f"{genre}: контраст низа {contrast_db:.2f} дБ < 6 дБ"


def test_gap_before_first_hook_is_audible_silence() -> None:
    result = _render("drift phonk", 7, duration=90)
    data, sr = sf.read(result["beat_path"], always_2d=True)
    mono = data.mean(axis=1)
    hook = next(section for section in result["sections"] if section["name"] == "hook")
    gap_start = int((hook["start_sec"] - 0.28) * sr)
    gap_end = int((hook["start_sec"] - 0.03) * sr)
    gap_rms = float(np.sqrt(np.mean(mono[gap_start:gap_end] ** 2)))
    hook_rms = float(np.sqrt(np.mean(mono[int(hook["start_sec"] * sr) : int((hook["start_sec"] + 2) * sr)] ** 2)))

    assert gap_rms < hook_rms * 0.25, "перед дропом должен быть слышимый провал"


def test_low_trim_is_reported_and_ordered() -> None:
    result = _render("drift phonk", 7, duration=120)
    trims = {section["name"]: section["bass_gain"] for section in result["sections"]}

    assert trims["hook"] == 1.0
    assert trims["verse"] < trims["hook"]
    assert trims["bridge"] <= trims["verse"]
