"""`modules/video_edit/audio.py`: мастер читается без тяжёлых зависимостей.

Вертикальный клип строится по «хуку» — самому энергичному участку мастера.
Пока этот модуль был покрыт на треть, ошибка в разборе WAV означала не
исключение, а клип из тишины: `detect_hook` ловит любое исключение и
возвращает начало трека.

Проверяется то, что реально приходит от пользователя: 16-битные мастера
(основной случай), 8/24/32 бита, моно и стерео, а также границы поиска.
"""

from __future__ import annotations

import math
import struct
import wave

import numpy as np
import pytest

from modules.video_edit import audio


def _write_wav(path, samples, sr: int = 8000, width: int = 2, channels: int = 1):
    """WAV заданной ширины сэмпла: 1, 2, 3 или 4 байта на канал."""
    if channels == 1:
        frames_data = list(samples)
    else:
        frames_data = [value for value in samples for _ in range(channels)]
    payload = bytearray()
    for value in frames_data:
        clipped = max(-1.0, min(1.0, float(value)))
        if width == 1:  # 8-битный WAV беззнаковый
            payload += struct.pack("<B", int(round(clipped * 127 + 128)))
        elif width == 2:
            payload += struct.pack("<h", int(round(clipped * 32767)))
        elif width == 3:
            payload += int(round(clipped * (2**23 - 1))).to_bytes(3, "little", signed=True)
        else:
            payload += struct.pack("<i", int(round(clipped * (2**31 - 1))))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(width)
        wf.setframerate(sr)
        wf.writeframes(bytes(payload))
    return path


def _sine(seconds: float = 1.0, freq: float = 440.0, sr: int = 8000, amp: float = 0.5):
    t = np.arange(int(sr * seconds)) / sr
    return (amp * np.sin(2 * np.pi * freq * t)).tolist()


# --------------------------------------------------------------------------- #
#  Чтение
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("width", [2, 3, 4])
def test_read_wav_returns_normalized_float(tmp_path, width: int) -> None:
    path = _write_wav(tmp_path / "tone.wav", _sine(0.1), width=width)

    samples, sr = audio._read_wav_mono(str(path))

    assert sr == 8000
    assert samples and all(-1.0 <= value <= 1.0 for value in samples)
    assert max(abs(value) for value in samples) == pytest.approx(0.5, abs=0.02)


def test_read_wav_stereo_is_downmixed(tmp_path) -> None:
    path = _write_wav(tmp_path / "stereo.wav", _sine(0.05), channels=2)

    samples, sr = audio._read_wav_mono(str(path))

    assert sr == 8000
    assert len(samples) == 400  # 0.05 c * 8000, а не удвоенное число каналов
    assert max(abs(value) for value in samples) == pytest.approx(0.5, abs=0.02)


def test_read_wav_rejects_unsupported_width(tmp_path) -> None:
    path = tmp_path / "odd.wav"
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(1)
        wf.setframerate(8000)
        wf.writeframes(b"\x80" * 10)

    with pytest.raises(ValueError, match="Unsupported sample width"):
        audio._read_wav_mono(str(path))


def test_read_wav_missing_file_raises(tmp_path) -> None:
    with pytest.raises(Exception):
        audio._read_wav_mono(str(tmp_path / "nope.wav"))


# --------------------------------------------------------------------------- #
#  RMS-окна
# --------------------------------------------------------------------------- #

def test_rms_windows_split_by_seconds() -> None:
    samples = [0.5] * 8000 * 2 + [0.0] * 8000

    windows = audio._rms_windows(samples, 8000, win_sec=1.0)

    assert len(windows) == 3
    assert windows[0] == pytest.approx(0.5)
    assert windows[2] == pytest.approx(0.0)


def test_rms_windows_handle_tail_and_empty() -> None:
    assert audio._rms_windows([], 8000) == []
    tail = audio._rms_windows([0.25] * 4000, 8000, win_sec=1.0)
    assert tail == [pytest.approx(0.25)]


def test_rms_windows_win_sec_cannot_be_zero() -> None:
    windows = audio._rms_windows([0.1, 0.1, 0.1], 8000, win_sec=0.0)

    assert len(windows) == 3  # окно не вырождается в деление на ноль


# --------------------------------------------------------------------------- #
#  Поиск хука
# --------------------------------------------------------------------------- #

def test_detect_hook_finds_the_loud_part(tmp_path) -> None:
    """Тишина → громкий участок → тишина: хук обязан попасть в громкий."""
    sr = 8000
    quiet = [0.02 * math.sin(2 * math.pi * 220 * i / sr) for i in range(sr * 10)]
    loud = [0.8 * math.sin(2 * math.pi * 220 * i / sr) for i in range(sr * 12)]
    path = _write_wav(tmp_path / "song.wav", quiet + loud + quiet, sr=sr)

    start, end = audio.detect_hook(str(path), target_sec=10)

    assert end - start == pytest.approx(10, abs=0.01)
    # «предпочитать вторую половину» сдвигает окно вправо, но не за громкий блок
    assert start >= 9.0
    assert end <= 33.0


def test_short_track_returns_whole_file(tmp_path) -> None:
    path = _write_wav(tmp_path / "short.wav", _sine(2.0))

    start, end = audio.detect_hook(str(path), target_sec=20)

    assert (start, end) == (0.0, pytest.approx(2.0))


def test_unreadable_master_degrades_to_the_start(tmp_path, capsys) -> None:
    """Битый мастер — не повод падать: клип начнётся с нуля, причина в выводе."""
    broken = tmp_path / "broken.wav"
    broken.write_bytes(b"not a wav at all")

    start, end = audio.detect_hook(str(broken), target_sec=15)

    assert (start, end) == (0.0, 15.0)
    assert "hook detect fail" in capsys.readouterr().out


def test_target_longer_than_track_is_clamped(tmp_path) -> None:
    path = _write_wav(tmp_path / "mid.wav", _sine(25.0))

    start, end = audio.detect_hook(str(path), target_sec=40)

    assert start == 0.0
    assert end == pytest.approx(25.0)


def test_windows_never_exceed_track(tmp_path) -> None:
    path = _write_wav(tmp_path / "long.wav", _sine(60.0))

    start, end = audio.detect_hook(str(path), target_sec=20)

    assert 0.0 <= start < end <= 60.0
