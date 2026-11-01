# -*- coding: utf-8 -*-
"""
Гейты «грува из референса» (Этап 4.2.3): смещения ударов измеряются по аудио
с точностью единиц миллисекунд и попадают в конструктор бита.
"""

from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf

from modules.beat_constructor import BeatConstructor

pytest.importorskip("librosa", reason="librosa нужен для анализа референса")

from modules.groove_extractor import extract_groove  # noqa: E402

SR = 44_100
BPM = 130.0
BAR = 60.0 / BPM * 4
STEP = BAR / 16
OFFBEAT_SHIFT_MS = 8.0


def _kick(sr: int = SR, seconds: float = 0.16) -> np.ndarray:
    time_axis = np.arange(int(sr * seconds)) / sr
    freq = 49.0 + 130.0 * np.exp(-time_axis * 38.0)
    return (np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-time_axis * 16.0)).astype(np.float32)


@pytest.fixture(scope="module")
def reference(tmp_path_factory) -> str:
    """Синтетический «референс»: бочка на 1, бочка на «и» с опозданием 8 мс."""
    audio = np.zeros(int(SR * BAR * 8), dtype=np.float32)
    hit = _kick()
    for bar in range(8):
        for step, shift_ms in ((0, 0.0), (8, OFFBEAT_SHIFT_MS)):
            position = int((bar * BAR + step * STEP + shift_ms / 1000.0) * SR)
            audio[position : position + len(hit)] += hit
    path = tmp_path_factory.mktemp("groove") / "reference.wav"
    sf.write(path, audio, SR)
    return str(path)


def test_reference_offsets_are_recovered_in_milliseconds(reference: str) -> None:
    groove = extract_groove(reference, bpm=BPM)
    offsets = groove["timing_offsets_ms"]

    assert len(offsets) == 16
    assert abs(offsets[0]) <= 4.0, f"сильная доля должна быть почти в сетке: {offsets[0]}"
    assert 4.0 <= offsets[8] <= 12.0, f"«и» сдвинуто на 8 мс, измерено {offsets[8]}"
    assert 0.05 <= groove["timing_confidence"] <= 0.6
    assert groove["steps_per_bar"] == 16


def test_constructor_uses_reference_offsets(reference: str) -> None:
    groove = extract_groove(reference, bpm=BPM)
    np.random.seed(4)
    constructor = BeatConstructor(bpm=BPM, genre="phonk", groove=groove, seed=4)

    on_grid = constructor._hit_offset_sec("kick", 0, 0) * 1000.0
    off_grid = constructor._hit_offset_sec("kick", 8, 0) * 1000.0

    assert abs(on_grid) <= 4.0
    assert off_grid >= on_grid + 4.0, "рисунок референса обязан переехать в бит"
    assert abs(off_grid) <= 20.0, "но не дальше ±20 мс — это уже рассинхрон"


def test_without_reference_offsets_behaviour_is_unchanged() -> None:
    np.random.seed(4)
    constructor = BeatConstructor(bpm=BPM, genre="phonk", groove={}, seed=4)
    offsets = [constructor._hit_offset_sec("snare", step, 0) * 1000.0 for step in range(16)]

    assert all(abs(value) <= 9.0 for value in offsets)
    assert len(set(round(value, 2) for value in offsets)) > 8, "без референса остаётся живой джиттер"


def test_groove_template_is_json_serialisable(reference: str) -> None:
    import json

    groove = extract_groove(reference, bpm=BPM)

    json.dumps(groove)
    assert isinstance(groove["timing_offsets_ms"], list)
    assert all(isinstance(value, (int, float)) for value in groove["timing_offsets_ms"])
