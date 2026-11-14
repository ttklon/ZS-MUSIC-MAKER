"""Синтез бита: шаги проверяются по отдельности, а не «через весь трек».

`app/core/stages/beat_synth.py` появился при разгрузке `_synth_beat` (T20) и
сначала не был покрыт вообще: тесты дергали только готовую стадию. Здесь
каждая ступень синтеза проверяется там, где её видно — секции, драм-лейн,
808, ризеры, стерео, запись, — и в первую очередь **детерминизм**: при одном
и том же seed бит обязан совпадать бит-в-бит, это обещание продукта.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pytest
import soundfile as sf

from app.core.stages import beat_synth


def _sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
#  Структура
# --------------------------------------------------------------------------- #

def test_scale_sections_shrinks_for_short_track() -> None:
    bar_sec = (60.0 / 128) * 4
    sections = beat_synth.scale_sections(duration=10, bar_sec=bar_sec)

    assert sum(bars for _, bars in sections) <= 48
    assert all(bars >= 1 for _, bars in sections)
    assert [name for name, _ in sections][:2] == ["intro", "verse"]


def test_scale_sections_extends_for_long_track() -> None:
    bar_sec = (60.0 / 128) * 4
    sections = beat_synth.scale_sections(duration=600, bar_sec=bar_sec)

    total = sum(bars for _, bars in sections)
    assert total > 48
    # растягиваются именно припевы: там нужен «мясной» участок
    chorus = [bars for name, bars in sections if name == "chorus"]
    assert min(chorus) > 8


def test_scale_sections_keeps_structure_for_exact_length() -> None:
    bar_sec = (60.0 / 128) * 4
    sections = beat_synth.scale_sections(duration=sum(b for _, b in beat_synth.BASE_SECTIONS) * bar_sec, bar_sec=bar_sec)

    assert [(name, bars) for name, bars in sections] == list(beat_synth.BASE_SECTIONS)


# --------------------------------------------------------------------------- #
#  Драм-лейн
# --------------------------------------------------------------------------- #

def test_render_drum_lane_fills_buffer_and_reports_sections() -> None:
    sr, bpm = 8000, 128
    bar_sec = (60.0 / bpm) * 4
    step_sec = bar_sec / 16
    beat_sec = 60.0 / bpm
    sections = [("intro", 1), ("verse", 1), ("pre", 1), ("chorus", 1)]
    total = int(sum(bars for _, bars in sections) * bar_sec * sr)
    y = np.zeros(total, dtype="float32")

    info = beat_synth.render_drum_lane(
        y, np, sr, sections, bar_sec, step_sec, beat_sec, root_hz=55.0
    )

    assert [item["name"] for item in info] == ["intro", "verse", "pre", "chorus"]
    assert info[0]["start_sec"] == 0
    assert info[-1]["start_sec"] > 0
    assert float(np.max(np.abs(y))) > 0, "лейн не записал ни одного сэмпла"
    assert np.isfinite(y).all(), "в буфере NaN/inf"


def test_intro_has_no_kick_or_snare() -> None:
    """Интро — атмосфера: кик и снейр в него не пишутся (это слышно)."""
    sr, bpm = 8000, 128
    bar_sec = (60.0 / bpm) * 4
    y = np.zeros(int(bar_sec * sr), dtype="float32")

    beat_synth.render_drum_lane(
        y, np, sr, [("intro", 1)], bar_sec, bar_sec / 16, 60.0 / bpm, 55.0
    )

    # в интро только хэты: пик заметно ниже, чем у кика
    assert float(np.max(np.abs(y))) < 0.9


def test_pre_section_has_stop_time_before_hook() -> None:
    """Последние два шага pre приглушаются — иначе дроп не читается."""
    sr, bpm = 8000, 128
    bar_sec = (60.0 / bpm) * 4
    step_sec = bar_sec / 16
    y = np.zeros(int(bar_sec * sr), dtype="float32")

    beat_synth.render_drum_lane(
        y, np, sr, [("pre", 1)], bar_sec, step_sec, 60.0 / bpm, 55.0
    )

    cut = int(step_sec * 2 * sr)
    tail = float(np.max(np.abs(y[-cut:])))
    body = float(np.max(np.abs(y[: len(y) - cut])))
    assert tail < body, "стоп-тайм перед хуком пропал"


def test_drum_lane_is_deterministic_with_seed() -> None:
    """Один seed — один и тот же бит: это обещание, а не пожелание."""
    sr, bpm = 8000, 128
    bar_sec = (60.0 / bpm) * 4
    sections = [("verse", 2), ("chorus", 2)]

    def render() -> np.ndarray:
        np.random.seed(7)
        y = np.zeros(int(sum(b for _, b in sections) * bar_sec * sr), dtype="float32")
        beat_synth.render_drum_lane(
            y, np, sr, sections, bar_sec, bar_sec / 16, 60.0 / bpm, 55.0
        )
        return y

    assert np.array_equal(render(), render())


def test_write_slice_never_overruns_buffer() -> None:
    target = np.zeros(10, dtype="float32")
    source = np.ones(100, dtype="float32")

    beat_synth._write_slice(target, source, 5, len(target), gain=0.5)

    assert np.allclose(target[5:], 0.5)
    assert np.allclose(target[:5], 0.0)


def test_write_slice_ignores_start_past_the_end() -> None:
    target = np.zeros(4, dtype="float32")

    beat_synth._write_slice(target, np.ones(10, dtype="float32"), 99, len(target))

    assert not target.any()


# --------------------------------------------------------------------------- #
#  Генераторы сэмплов
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("factory", ["_kick", "_snare", "_hat"])
def test_drum_generators_return_finite_audio(factory: str) -> None:
    generator = getattr(beat_synth, factory)

    audio = generator(np, 8000)

    assert len(audio) > 0
    assert np.isfinite(audio).all()
    assert float(np.max(np.abs(audio))) > 0


def test_open_hat_is_longer_and_louder_than_closed() -> None:
    closed = beat_synth._hat(np, 8000, open_=False)
    opened = beat_synth._hat(np, 8000, open_=True)

    assert float(np.max(np.abs(opened))) > float(np.max(np.abs(closed)))


def test_808_is_bounded_by_tanh() -> None:
    audio = beat_synth._808(np, 8000, dur=0.5, freq=55.0)

    assert float(np.max(np.abs(audio))) <= 1.0


@pytest.mark.parametrize("kind", ["white", "sub"])
def test_risers_are_finite(kind: str) -> None:
    audio = beat_synth._riser(np, 8000, dur=0.2, kind=kind)

    assert len(audio) > 0 and np.isfinite(audio).all()


# --------------------------------------------------------------------------- #
#  Стерео и файл
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("sr", [8000, 22050, 44100])
def test_stereoize_keeps_low_end_mono(sr: int) -> None:
    """Ниже 200 Гц — моно-основа: иначе саб «расплывается» в моно-сумме.

    Проверяется и на низком `sr`: фильтр 5 кГц там выше Найквиста, и раньше
    это роняло всю стерео-обработку в аварийный Haas — низ переставал быть
    моно. Теперь срез ограничен, и поведение одинаково на любом `sr`.
    """
    t = np.arange(sr, dtype="float32") / sr
    low = np.sin(2 * np.pi * 60 * t).astype("float32")

    stereo = beat_synth.stereoize(low, np, sr)

    assert stereo.shape == (sr, 2)
    # Края сигнала — переходный процесс фильтра; моно-основа проверяется
    # там, где сигнал уже установился.
    middle = slice(sr // 4, sr * 3 // 4)
    left, right = stereo[middle, 0], stereo[middle, 1]
    assert float(np.max(np.abs(left - right))) < 0.02
    assert float(np.max(np.abs(left))) > 0.5, "низ потерялся целиком"


def test_stereoize_widens_high_end() -> None:
    sr = 22050
    t = np.arange(sr, dtype="float32") / sr
    high = np.sin(2 * np.pi * 4000 * t).astype("float32")

    stereo = beat_synth.stereoize(high, np, sr)

    middle = slice(sr // 4, sr * 3 // 4)
    assert float(np.max(np.abs(stereo[middle, 0] - stereo[middle, 1]))) > 1e-3


def test_synth_beat_writes_readable_wav(tmp_path) -> None:
    from app.core.stages.beat import _synth_beat

    out = tmp_path / "beat.wav"
    result = _synth_beat(str(out), duration=8, bpm=140, key_root="A", key_name="A minor")

    assert result["ok"] is True
    assert result["fallback_used"] is True
    assert result["engine"] == "synth_beat_v22"
    assert result["key"] == "A minor"
    data, sr = sf.read(out)
    assert sr == 44100 and data.shape[1] == 2
    assert result["duration_sec"] == pytest.approx(len(data) / sr, abs=0.05)


def test_synth_beat_is_reproducible(tmp_path) -> None:
    from app.core.stages.beat import _synth_beat

    np.random.seed(11)
    first = _synth_beat(str(tmp_path / "a.wav"), duration=6, bpm=128, key_root="A")
    np.random.seed(11)
    second = _synth_beat(str(tmp_path / "b.wav"), duration=6, bpm=128, key_root="A")

    assert first["ok"] and second["ok"]
    assert _sha(tmp_path / "a.wav") == _sha(tmp_path / "b.wav")


def test_synth_beat_reports_failure_instead_of_raising(tmp_path) -> None:
    from app.core.stages.beat import _synth_beat

    result = _synth_beat(str(tmp_path / "nope" / "x" / "beat.wav"), duration=0, bpm=0, key_root="A")

    assert "ok" in result
    if result["ok"] is False:
        assert result["reason"]
