# -*- coding: utf-8 -*-
"""4.4: тюн (фазовый вокодер), динамический де-эссер, просодия, цепочка целиком."""

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.vocal_fx.desser import dynamic_deess
from modules.vocal_fx.pitch import (
    MAX_SHIFT_CENTS,
    correct_pitch,
    note_to_hz,
    quantize_cents,
    track_pitch,
)
from modules.vocal_fx.prosody import detect_phrases, process_prosody

RATE = 32_000


def _tone(cents_off: float, seconds: float = 2.0, rate: int = RATE) -> np.ndarray:
    time = np.arange(int(rate * seconds)) / rate
    freq = note_to_hz("A", 3) * 2.0 ** (cents_off / 1200.0)
    return 0.25 * np.sin(2 * np.pi * freq * time)


def _stereo(mono: np.ndarray) -> np.ndarray:
    return np.stack([mono, mono * 0.95], axis=1)


def _rms(audio: np.ndarray) -> float:
    return float(np.sqrt(np.mean(audio**2) + 1e-18))


def _band_energy(audio: np.ndarray, rate: int, low: float, high: float) -> float:
    from modules.vocal_fx.desser import _band

    band = _band(audio, rate, low, high)
    return 20.0 * np.log10(_rms(band) + 1e-12)


# --- детекция и квантизация -------------------------------------------------


def test_track_pitch_finds_reference_tone() -> None:
    track = track_pitch(_tone(0.0, seconds=1.0), RATE)
    voiced = track["f0"][track["f0"] > 0.0]

    assert voiced.size > 50
    assert abs(float(np.median(voiced)) - 220.0) < 2.0


def test_quantize_respects_max_shift() -> None:
    f0 = np.full(8, 220.0)
    target = quantize_cents(f0, tonic="A", scale="minor", strength=1.0, max_shift_cents=20.0)
    shift = 1200.0 * np.log2(target / f0)

    assert np.all(np.abs(shift) <= 20.0 + 1e-6)


# --- коррекция высоты -------------------------------------------------------


def test_correction_snaps_detuned_tone_into_scale() -> None:
    audio = _stereo(_tone(60.0))

    out, report = correct_pitch(audio, RATE, tonic="A", scale="minor", strength=1.0)

    assert report["engine"] == "phase_vocoder"
    assert report["length_preserved"] is True
    assert out.shape == audio.shape
    assert report["in_tune_before_pct"] <= 5.0
    assert report["in_tune_after_pct"] >= 95.0
    track = track_pitch(out.mean(axis=1), RATE)
    after = float(np.median(track["f0"][track["f0"] > 0.0]))
    assert abs(after - 220.0) < 3.0
    # уровень и пик не «схлопываются» (частая беда naive PSOLA)
    assert abs(20 * np.log10(_rms(out[2000:]) / _rms(audio[2000:]))) < 1.0
    assert float(np.max(np.abs(out))) <= float(np.max(np.abs(audio))) * 1.05


def test_correction_leaves_in_tune_tone_alone() -> None:
    audio = _stereo(_tone(0.0, seconds=1.0))

    out, report = correct_pitch(audio, RATE, tonic="A", scale="minor", strength=1.0)

    assert report["shift_cents_median"] < 8.0
    track = track_pitch(out.mean(axis=1), RATE)
    assert abs(float(np.median(track["f0"][track["f0"] > 0.0])) - 220.0) < 3.0


def test_correction_strength_is_gradual_for_small_deviation() -> None:
    """Малая фальшь правится пропорционально `strength`: вибрато сохраняется.

    Крупная фальшь (>40 центов) корректируется почти полностью даже при
    strength=0.3 — это осознанное поведение (адаптивная сила), поэтому тест
    проверяет именно «мягкий» режим.
    """
    audio = _stereo(_tone(22.0))
    _, strong = correct_pitch(audio, RATE, tonic="A", scale="minor", strength=1.0)
    _, weak = correct_pitch(audio, RATE, tonic="A", scale="minor", strength=0.3)

    assert weak["shift_cents_median"] < strong["shift_cents_median"]
    assert weak["shift_cents_max"] <= MAX_SHIFT_CENTS + 1e-6


def test_gross_detune_is_corrected_even_at_low_strength() -> None:
    audio = _stereo(_tone(90.0))
    out, report = correct_pitch(audio, RATE, tonic="A", scale="minor", strength=0.3)

    track = track_pitch(out.mean(axis=1), RATE)
    after = float(np.median(track["f0"][track["f0"] > 0.0]))
    assert abs(after - 220.0) < 12.0


# --- де-эссер ---------------------------------------------------------------


def _sibilant_signal() -> tuple[np.ndarray, np.ndarray]:
    from scipy.signal import butter, sosfilt

    time = np.arange(int(RATE * 4.0)) / RATE
    voice = 0.18 * np.sin(2 * np.pi * 180.0 * time)
    rng = np.random.default_rng(7)
    noise = rng.normal(0.0, 1.0, (time.size, 2))
    sos = butter(4, [5000 / (RATE / 2), 9000 / (RATE / 2)], btype="bandpass", output="sos")
    hiss = sosfilt(sos, noise, axis=0)
    mask = np.zeros(time.size)
    mask[int(RATE * 1.0) : int(RATE * 1.4)] = 1.0
    mask[int(RATE * 2.5) : int(RATE * 2.9)] = 1.0
    signal = np.stack([voice, voice * 0.9], axis=1) + hiss * mask[:, None] * 0.25
    return signal, mask


def test_deesser_reduces_sibilance_without_touching_vowels() -> None:
    signal, mask = _sibilant_signal()

    out, report = dynamic_deess(signal, RATE)

    assert report["length_preserved"] is True
    sibilant = mask.astype(bool)
    before = _band_energy(signal[sibilant], RATE, 5500, 9500)
    after = _band_energy(out[sibilant], RATE, 5500, 9500)
    assert before - after >= 3.0
    # вне шипящих (с запасом 40 мс на кольца фильтра) сигнал почти не меняется
    guard = np.convolve(sibilant.astype(float), np.ones(int(0.04 * RATE)), mode="same") > 0
    quiet = ~(sibilant | guard)
    assert float(np.max(np.abs(out[quiet] - signal[quiet]))) < 1e-3
    assert report["threshold_mode"] == "ratio_adaptive"


def test_deesser_skips_silence() -> None:
    silence = np.zeros((RATE, 2), dtype=np.float64)

    out, report = dynamic_deess(silence, RATE)

    assert report["reduction_active_pct"] == 0.0
    assert float(np.max(np.abs(out))) == 0.0


# --- просодия ---------------------------------------------------------------


def _phrased_signal() -> np.ndarray:
    time = np.arange(int(RATE * 6.0)) / RATE
    envelope = np.zeros_like(time)
    for start, stop in ((0.2, 1.2), (1.6, 2.4), (2.8, 4.1)):
        envelope[(time >= start) & (time < stop)] = 1.0
    body = 0.15 * np.sin(2 * np.pi * 180.0 * time) * envelope
    rng = np.random.default_rng(11)
    breath = 0.004 * rng.normal(0.0, 1.0, time.size) * (envelope + 0.4)
    return body + breath


def test_detect_phrases_finds_three_phrases() -> None:
    phrases = detect_phrases(_phrased_signal(), RATE)

    assert len(phrases) == 3
    starts = [round(start / RATE, 1) for start, _ in phrases]
    assert starts == [0.2, 1.6, 2.8]


def test_prosody_ducks_breaths_and_keeps_length() -> None:
    signal = _phrased_signal()

    out, report = process_prosody(signal, RATE, bpm=120)

    assert out.shape == signal.shape
    assert report["phrase_count"] == 3
    assert report["breaths"]["pauses"] == 2
    assert report["timing"]["max_shift_ms"] <= 30.0
    # пауза между фразами стала тише минимум на 15 дБ
    pause = slice(int(RATE * 1.35), int(RATE * 1.55))
    before = 20 * np.log10(_rms(signal[pause]) + 1e-12)
    after = 20 * np.log10(_rms(out[pause]) + 1e-12)
    assert before - after >= 15.0
    # тело фразы осталось на месте по уровню (гейн ограничен ±6 дБ)
    assert report["gain_range_db"] <= 6.0


# --- цепочка целиком --------------------------------------------------------


def test_process_vocal_runs_tune_deess_prosody(tmp_path) -> None:
    from modules.vocal_fx import process_vocal

    source = tmp_path / "vocal.wav"
    sf.write(str(source), _stereo(_tone(55.0, seconds=3.0)).astype(np.float32), RATE)
    out = tmp_path / "voice_fx.wav"

    result = process_vocal(
        str(source),
        str(out),
        use_double=False,
        use_throw=False,
        clean_before_fx=False,
        bpm=120.0,
        tonic="A",
        scale="minor",
    )

    assert result["ok"] is True, result
    assert out.exists()
    assert {"tune", "deess", "prosody"} <= set(result["stages"])
    assert result["tune"]["in_tune_after_pct"] > result["tune"]["in_tune_before_pct"]
    assert result["skipped"] == []
    data, rate = sf.read(str(out), always_2d=True)
    assert rate == RATE
    assert abs(data.shape[0] - int(RATE * 3.0)) <= 2
