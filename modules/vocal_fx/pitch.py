# -*- coding: utf-8 -*-
"""modules/vocal_fx/pitch.py — тюн вокала: детекция высоты и мягкая коррекция (4.4.1).

Без нейросетей и без «просто ресемпла всего файла» (он меняет длительность и
портит форманты). Здесь классический TD-PSOLA:

1. детекция F0 по нормированной автокорреляции с YIN-порогом (кадр 40 мс,
   шаг 10 мс, диапазон 70–1000 Гц, вероятность голоса как уверенность);
2. квантизация к тонике/ладу: цель = ближайшая ступень, сдвиг ограничен
   `MAX_SHIFT_CENTS` (по умолчанию 100 центов), сила коррекции 0…1. Поэтому
   вибрато и живая интонация не «выпрямляются в линейку» — снимается только
   фальшь;
3. ресинтез фазовым вокодером с identity phase-locking и обратным
   пересэмплированием по монотонной карте → длительность сохраняется до
   семпла, высота сдвигается точно.

Всё детерминировано: один и тот же вход → один и тот же выход.
"""

from __future__ import annotations

from typing import Any

import numpy as np

__all__ = [
    "NOTE_NAMES",
    "SCALES",
    "track_pitch",
    "quantize_cents",
    "correct_pitch",
    "pitch_report",
]

MIN_F0 = 70.0
MAX_F0 = 1000.0
FRAME_SEC = 0.040
HOP_SEC = 0.010
VOICING_THRESHOLD = 0.45
MAX_SHIFT_CENTS = 100.0

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
SCALES = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "pentatonic_minor": (0, 3, 5, 7, 10),
}


def note_to_hz(note: str, octave: int = 4) -> float:
    """«A4» → 440.0 Гц (равномерная темперация, A4 = 440)."""
    name = note.strip().upper()
    if name not in NOTE_NAMES:
        raise ValueError(f"unknown note: {note}")
    midi = 12 * (int(octave) + 1) + NOTE_NAMES.index(name)
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def _frames(mono: np.ndarray, sample_rate: int) -> tuple[np.ndarray, int, int]:
    frame = max(64, int(FRAME_SEC * sample_rate))
    hop = max(16, int(HOP_SEC * sample_rate))
    if mono.size < frame:
        padded = np.pad(mono, (0, frame - mono.size))
        return padded[None, :], frame, hop
    count = 1 + (mono.size - frame) // hop
    index = np.arange(frame)[None, :] + hop * np.arange(count)[:, None]
    return mono[index], frame, hop


def _frame_f0(frame: np.ndarray, sample_rate: int) -> tuple[float, float]:
    """F0 и уверенность для одного кадра (нормированная автокорреляция)."""
    x = frame - frame.mean()
    energy = float(np.dot(x, x))
    if energy < 1e-9:
        return 0.0, 0.0
    size = 1 << int(np.ceil(np.log2(2 * x.size)))
    spectrum = np.fft.rfft(x, size)
    acf = np.fft.irfft(spectrum * np.conj(spectrum), size)[: x.size]
    acf = acf / (acf[0] + 1e-12)
    min_lag = max(2, int(sample_rate / MAX_F0))
    max_lag = min(x.size - 1, int(sample_rate / MIN_F0))
    if max_lag <= min_lag + 1:
        return 0.0, 0.0
    segment = acf[min_lag:max_lag]
    peak = int(np.argmax(segment)) + min_lag
    confidence = float(acf[peak])
    if confidence < VOICING_THRESHOLD:
        return 0.0, max(0.0, confidence)
    # параболическая интерполяция вокруг пика — точность лучше бина
    left, center, right = acf[peak - 1], acf[peak], acf[peak + 1]
    denominator = left - 2.0 * center + right
    offset = 0.5 * (left - right) / denominator if abs(denominator) > 1e-12 else 0.0
    lag = peak + float(np.clip(offset, -0.5, 0.5))
    return float(sample_rate / lag), confidence


def track_pitch(mono: np.ndarray, sample_rate: int) -> dict[str, np.ndarray]:
    """Кадровая дорожка: время (с), F0 (Гц, 0 = невокал), уверенность."""
    frames, _, hop = _frames(mono, sample_rate)
    f0 = np.zeros(frames.shape[0], dtype=np.float64)
    confidence = np.zeros(frames.shape[0], dtype=np.float64)
    for index, frame in enumerate(frames):
        f0[index], confidence[index] = _frame_f0(frame, sample_rate)
    times = np.arange(frames.shape[0]) * hop / sample_rate
    return {"time": times, "f0": f0, "confidence": confidence}


def _hz_to_cents(hz: np.ndarray) -> np.ndarray:
    return 1200.0 * np.log2(np.maximum(hz, 1e-6) / 440.0) + 6900.0


def quantize_cents(
    f0: np.ndarray,
    tonic: str = "A",
    scale: str = "minor",
    strength: float = 0.7,
    max_shift_cents: float = MAX_SHIFT_CENTS,
) -> np.ndarray:
    """Целевые частоты: ближайшая ступень лада, сдвиг ограничен и взвешен."""
    steps = SCALES.get(scale, SCALES["minor"])
    voiced = f0 > 0.0
    target = np.array(f0, dtype=np.float64)
    if not np.any(voiced):
        return target
    tonic_cents = _hz_to_cents(np.array([note_to_hz(tonic, 4)]))[0]
    # всё в полутонах: 100 центов = 1 полутон, 12 полутонов = октава
    semitones = (_hz_to_cents(f0[voiced]) - tonic_cents) / 100.0
    degree = np.array(steps, dtype=np.float64)
    octave = np.floor(semitones / 12.0)
    within = semitones - octave * 12.0
    # расстояние до каждой ступени с учётом переноса через октаву
    distances = within[:, None] - degree[None, :]
    distances = (distances + 6.0) % 12.0 - 6.0
    nearest = np.argmin(np.abs(distances), axis=1)
    # расстояния в полутонах → обратно в центы (100 центов = полутон)
    shift = -distances[np.arange(semitones.size), nearest] * 100.0
    # адаптивная сила: небольшая фальшь (вибрато, живая интонация) правится
    # мягко, грубая — почти до нуля. Так сохраняется «человечность» и при этом
    # фальшивые ноты действительно выправляются.
    base = float(np.clip(strength, 0.0, 1.0))
    deviation = np.abs(shift)
    adaptive = base + (1.0 - base) * np.clip((deviation - 15.0) / 25.0, 0.0, 1.0)
    shift = np.clip(shift * adaptive, -max_shift_cents, max_shift_cents)
    target[voiced] = f0[voiced] * 2.0 ** (shift / 1200.0)
    return target


def _interp_track(track: np.ndarray, times: np.ndarray, sample_rate: int, length: int, fallback: float) -> np.ndarray:
    centers = np.clip(times * sample_rate, 0, length - 1)
    values = np.where(track > 0.0, track, fallback)
    positions = np.arange(length, dtype=np.float64)
    return np.interp(positions, centers, values)


def _smooth_track(values: np.ndarray, sample_rate: int, seconds: float = 0.030) -> np.ndarray:
    size = max(1, int(seconds * sample_rate))
    if size <= 1:
        return values
    kernel = np.ones(size, dtype=np.float64) / size
    return np.convolve(values, kernel, mode="same")


def _pitch_shift(channel: np.ndarray, sample_rate: int, f_in: np.ndarray, f_out: np.ndarray) -> np.ndarray:
    """Сдвиг высоты фазовым вокодером (identity phase-locking), длина сохраняется.

    Почему не «гранулы»: при перекрытии гранул, центрированных на входе, фазы
    соседних копий совпадают с исходной периодичностью, и сумма reinforce-ит
    *исходную* частоту — сдвиг не слышен. Фазовый вокодер переносит фазу по
    измеренной истинной частоте бина, поэтому смена высоты реальна.

    Схема (коэффициент `r = f_out / f_in` меняется по кадрам):

    1. анализ идёт с шагом `hop / r` (при r > 1 — медленнее, это растяжение), фаза
       каждого бина продвигается на измеренную истинную частоту;
    2. синтез — на равномерной сетке `hop`, окно Ханна, нормировка суммы окон;
    3. сжатый/растянутый сигнал пересэмплируется обратно на исходную
       длительность по монотонной карте «вход ↔ синтез», поэтому итог всегда
       один и тот же размер, а высота = `f_out` в каждой точке.
    """
    length = channel.size
    win = 1 << int(np.ceil(np.log2(max(64.0, 0.023 * sample_rate))))
    hop = max(1, win // 4)
    window = np.hanning(win)
    ratio = np.clip(_smooth_track(f_out / np.maximum(f_in, 1e-6), sample_rate), 0.5, 2.0)
    source = np.pad(channel.astype(np.float64), (win, win + hop), mode="edge")
    center_offset = win  # позиция нуля исходного времени в padded-массиве

    positions: list[float] = []
    spectrums: list[np.ndarray] = []
    position = 0.0
    while True:
        start = int(round(position)) + center_offset - win // 2
        if start + win > source.size:
            break
        positions.append(position)
        spectrums.append(np.fft.rfft(source[start : start + win] * window))
        local = int(np.clip(round(position), 0, length - 1))
        position += hop / float(ratio[local])
        if len(positions) > 4 * (length // hop + 4):  # предохранитель
            break
    if not spectrums:
        return np.array(channel, dtype=np.float64, copy=True)

    bins = spectrums[0].size
    omega = 2.0 * np.pi * np.arange(bins) / win  # ожидаемая фаза на сэмпл
    out_length = len(spectrums) * hop + win
    out = np.zeros(out_length + win, dtype=np.float64)
    weight = np.zeros_like(out)
    phase = np.angle(spectrums[0])
    previous = spectrums[0]
    for index, spectrum in enumerate(spectrums):
        magnitude = np.abs(spectrum)
        if index > 0:
            delta = float(positions[index] - positions[index - 1])
            advanced = np.angle(spectrum) - np.angle(previous)
            expected = omega * delta
            residual = (advanced - expected + np.pi) % (2.0 * np.pi) - np.pi
            true_omega = omega + residual / max(delta, 1e-9)
            phase = phase + true_omega * hop
            # identity phase-locking: соседи пика сохраняют *относительную*
            # фазу анализа (плоское выравнивание убивает форму волны)
            phase = _lock_phase(phase, np.angle(spectrum), magnitude)
        frame = np.fft.irfft(magnitude * np.exp(1j * phase), win)
        place = index * hop
        out[place : place + win] += frame * window
        # кадр уже оконен на анализе, синтез даёт window² — нормируем по нему (WOLA)
        weight[place : place + win] += window * window
        previous = spectrum
    stretched = out[:out_length] / np.maximum(weight[:out_length], 1e-3)

    # карта «вход → синтез»: для каждого входного сэмпла — позиция в синтезе
    source_times = np.asarray(positions, dtype=np.float64)
    synth_times = np.arange(len(positions), dtype=np.float64) * hop
    query = np.arange(length, dtype=np.float64)
    mapped = np.interp(query, source_times, synth_times)
    result = np.interp(mapped, np.arange(stretched.size, dtype=np.float64), stretched)
    return result[:length]


def _lock_phase(
    propagated: np.ndarray, analysis: np.ndarray, magnitude: np.ndarray
) -> np.ndarray:
    """Identity phase-locking: соседи пика держат относительную фазу анализа.

    Абсолютную фазу задаёт пик (она уже продвинута по истинной частоте), а
    соседние бины получают своё исходное смещение относительно пика. Так форма
    импульса сохраняется, и амплитуда не «схлопывается».
    """
    if magnitude.size < 5:
        return propagated
    peaks = np.flatnonzero(
        (magnitude[1:-1] > magnitude[:-2]) & (magnitude[1:-1] >= magnitude[2:])
    ) + 1
    if peaks.size == 0:
        return propagated
    locked = np.array(propagated, copy=True)
    for peak in peaks:
        left = max(0, peak - 2)
        right = min(propagated.size, peak + 3)
        locked[left:right] = propagated[peak] + (analysis[left:right] - analysis[peak])
    return locked


def correct_pitch(
    audio: np.ndarray,
    sample_rate: int,
    tonic: str = "A",
    scale: str = "minor",
    strength: float = 0.7,
    max_shift_cents: float = MAX_SHIFT_CENTS,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Скорректировать высоту и вернуть отчёт измерений до/после."""
    data = np.asarray(audio, dtype=np.float64)
    stereo = data.ndim == 2
    channels = [data] if not stereo else [data[:, c] for c in range(data.shape[1])]
    mono = np.mean(data, axis=1) if stereo else data
    track = track_pitch(mono, sample_rate)
    f0 = track["f0"]
    confidence = track["confidence"]
    voiced = (f0 > 0.0) & (confidence >= VOICING_THRESHOLD)

    target = quantize_cents(f0, tonic=tonic, scale=scale, strength=strength, max_shift_cents=max_shift_cents)
    safe_f0 = np.maximum(f0, 1e-6)
    shift_cents = np.where(
        voiced & (f0 > 0.0), 1200.0 * np.log2(np.maximum(target, 1e-6) / safe_f0), 0.0
    )

    median_f0 = float(np.median(f0[voiced])) if np.any(voiced) else 0.0
    fallback_in = median_f0 if median_f0 > 0.0 else 200.0

    corrected_channels = []
    for channel in channels:
        f_in_track = _interp_track(np.where(voiced, f0, 0.0), track["time"], sample_rate, channel.size, fallback_in)
        f_out_track = _interp_track(np.where(voiced, target, 0.0), track["time"], sample_rate, channel.size, fallback_in)
        # Невокальные участки не трогаем: там ratio = 1.
        voiced_samples = np.interp(
            np.arange(channel.size),
            np.clip(track["time"] * sample_rate, 0, channel.size - 1),
            voiced.astype(np.float64),
        ) > 0.5
        f_out_track = np.where(voiced_samples, f_out_track, f_in_track)
        shifted = _pitch_shift(channel, sample_rate, f_in_track, f_out_track)
        # PSOLA не трогает громкость, но DC/пики проверяем: сохраняем длину и пик
        peak_in = float(np.max(np.abs(channel))) or 1.0
        peak_out = float(np.max(np.abs(shifted))) or 1.0
        if peak_out > peak_in:
            shifted = shifted * (peak_in / peak_out)
        corrected_channels.append(shifted)

    result = np.stack(corrected_channels, axis=1) if stereo else corrected_channels[0]
    after_track = track_pitch(np.mean(result, axis=1) if stereo else result, sample_rate)
    after_voiced = (after_track["f0"] > 0.0) & (after_track["confidence"] >= VOICING_THRESHOLD)
    report = {
        "engine": "phase_vocoder",
        "tonic": tonic,
        "scale": scale,
        "strength": round(float(strength), 3),
        "frames": int(f0.size),
        "voiced_frames": int(np.count_nonzero(voiced)),
        "voiced_ratio": round(float(np.count_nonzero(voiced) / max(1, f0.size)), 3),
        "median_f0_hz": round(median_f0, 1),
        "shift_cents_median": round(float(np.median(np.abs(shift_cents[voiced]))) if np.any(voiced) else 0.0, 2),
        "shift_cents_p95": round(float(np.percentile(np.abs(shift_cents[voiced]), 95)) if np.any(voiced) else 0.0, 2),
        "shift_cents_max": round(float(np.max(np.abs(shift_cents))) if shift_cents.size else 0.0, 2),
        "in_tune_before_pct": _in_tune_pct(f0, voiced, tonic, scale)[0],
        "deviation_cents_before": _in_tune_pct(f0, voiced, tonic, scale)[1],
        "in_tune_after_pct": _in_tune_pct(after_track["f0"], after_voiced, tonic, scale)[0],
        "deviation_cents_after": _in_tune_pct(after_track["f0"], after_voiced, tonic, scale)[1],
        "length_preserved": bool(result.shape[0] == data.shape[0]),
    }
    return result, report


def _in_tune_pct(
    f0: np.ndarray, voiced: np.ndarray, tonic: str = "A", scale: str = "minor"
) -> tuple[float, float]:
    """Доля кадров в ±25 центах от ступени лада и медианное отклонение.

    Считается по самой частоте, а не по «цели»: поэтому метрика честна и для
    исходника, и для результата с любой силой коррекции.
    """
    if not np.any(voiced):
        return 0.0, 0.0
    steps = np.array(SCALES.get(scale, SCALES["minor"]), dtype=np.float64)
    tonic_cents = _hz_to_cents(np.array([note_to_hz(tonic, 4)]))[0]
    semitones = (_hz_to_cents(f0[voiced]) - tonic_cents) / 100.0
    within = semitones % 12.0
    raw = np.abs(within[:, None] - steps[None, :])
    distance = np.min(np.minimum(raw, 12.0 - raw), axis=1) * 100.0
    return round(float(np.mean(distance <= 25.0) * 100.0), 1), round(float(np.median(distance)), 1)


def pitch_report(report: dict[str, Any]) -> str:
    """Короткая строка для лога/отчёта пайплайна."""
    return (
        f"tune {report.get('engine')} {report.get('tonic')}{' ' if report.get('tonic') else ''}"
        f"{report.get('scale')}: voiced {report.get('voiced_ratio', 0) * 100:.0f} %, "
        f"сдвиг медиана {report.get('shift_cents_median', 0)} центов, "
        f"в тоне {report.get('in_tune_before_pct', 0)} → {report.get('in_tune_after_pct', 0)} %, "
        f"отклонение {report.get('deviation_cents_before', 0)} → "
        f"{report.get('deviation_cents_after', 0)} центов"
    )
