"""
[2b] groove_extractor.py — Rhythm DNA / Groove Extractor v2 (НОВЫЙ)
Извлекает из референса не ноты и не лупы, а ритмическую ДНК:
  • где кик, где снейр, насколько плотный хэт
  • triplet-rolls, свинг
  • как часто меняется паттерн
  • "кач" дропа
Создаёт абстрактный groove_template для пересборки другими звуками.
"""

import json
import os

import numpy as np

try:
    import librosa
except ImportError:
    librosa = None


def _frequency_envelopes(samples: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract low, snare-band and high-frequency frame envelopes."""
    spectrum = np.abs(librosa.stft(samples, n_fft=1024, hop_length=512))
    frequencies = librosa.fft_frequencies(sr=sample_rate, n_fft=1024)
    kick = spectrum[frequencies < 80].mean(axis=0)
    snare = spectrum[(frequencies >= 150) & (frequencies <= 400)].mean(axis=0)
    hihat_mask = frequencies > 5000
    hihat = spectrum[hihat_mask].mean(axis=0) if hihat_mask.any() else np.zeros(spectrum.shape[1])
    return kick, snare, hihat


def _step_envelopes(
    kick: np.ndarray,
    snare: np.ndarray,
    hihat: np.ndarray,
    frames_per_step: int,
    max_steps: int,
) -> tuple[list[float], list[float], list[float]]:
    """Aggregate spectral envelopes into bounded sixteenth-note steps."""
    kick_steps: list[float] = []
    snare_steps: list[float] = []
    hihat_steps: list[float] = []
    for step in range(max_steps):
        start = step * frames_per_step
        end = start + frames_per_step
        if end > len(kick):
            break
        kick_steps.append(float(kick[start:end].mean()))
        snare_steps.append(float(snare[start:end].mean()))
        hihat_steps.append(float(hihat[start:end].mean()))
    return kick_steps, snare_steps, hihat_steps


def _swing_value(kick_steps: list[float], steps_per_bar: int) -> float:
    """Measure odd/even sixteenth-note energy displacement."""
    bars = len(kick_steps) // steps_per_bar
    odd = [
        kick_steps[bar * steps_per_bar + step + 1]
        for bar in range(bars)
        for step in range(0, steps_per_bar, 2)
        if bar * steps_per_bar + step + 1 < len(kick_steps)
    ]
    even = [
        kick_steps[bar * steps_per_bar + step]
        for bar in range(bars)
        for step in range(0, steps_per_bar, 2)
        if bar * steps_per_bar + step < len(kick_steps)
    ]
    if not odd or not even:
        return 0.0
    return min(1.0, abs(np.mean(odd) - np.mean(even)) / (np.mean(even) + 1e-9))


def _has_triplet_rolls(kick_binary: list[int], steps_per_bar: int) -> bool:
    """Detect a dense three-step kick group in the first four complete bars."""
    bars = len(kick_binary) // steps_per_bar
    return any(
        sum(kick_binary[bar * steps_per_bar + step : bar * steps_per_bar + step + 3]) >= 2
        for bar in range(min(bars, 4))
        for step in range(steps_per_bar - 2)
        if bar * steps_per_bar + step + 2 < len(kick_binary)
    )


def _pattern_changes(kick_binary: list[int], steps_per_bar: int, bar_sec: float) -> list[dict]:
    """Return time-marked kick-pattern changes between adjacent complete bars."""
    bars = len(kick_binary) // steps_per_bar
    return [
        {"bar": bar, "time_sec": round(bar * bar_sec, 2)}
        for bar in range(1, bars)
        if kick_binary[(bar - 1) * steps_per_bar : bar * steps_per_bar]
        != kick_binary[bar * steps_per_bar : (bar + 1) * steps_per_bar]
    ]


def _drop_intensity(kick_steps: list[float], steps_per_bar: int) -> float:
    """Measure the strongest complete bar against mean bar energy."""
    energies = [
        float(np.mean(kick_steps[bar * steps_per_bar : (bar + 1) * steps_per_bar]))
        for bar in range(len(kick_steps) // steps_per_bar)
    ]
    return min(1.0, max(energies) / (np.mean(energies) + 1e-9) - 1.0) if energies else 0.0


def _attack_envelope(samples: np.ndarray, sample_rate: int, hop_ms: float = 1.0, win_ms: float = 3.0):
    """Огибающая атак: RMS первой разности (клик удара), шаг 1 мс.

    Низкочастотная огибающая для микротайминга не годится: у 49-герцового
    кика RMS «набирается» 10–20 мс, и смещение уезжает вместе с ней. Первая
    разность подчёркивает транзиент, поэтому позиция атаки совпадает с ударом
    с точностью ~2 мс.
    """
    data = np.asarray(samples, dtype=np.float64)
    if len(data) < 64:
        return np.zeros(0), hop_ms / 1000.0
    diff = np.diff(data)
    hop = max(1, int(sample_rate * hop_ms / 1000.0))
    window = max(hop, int(sample_rate * win_ms / 1000.0))
    frames = max(1, (len(diff) - window) // hop)
    offsets = np.arange(frames) * hop
    cumulative = np.concatenate([[0.0], np.cumsum(diff * diff)])
    energy = np.sqrt(
        np.maximum(cumulative[offsets + window] - cumulative[offsets], 0.0) / window
    )
    return energy, hop / float(sample_rate)


def _kick_attack_offsets_ms(
    samples: np.ndarray,
    sample_rate: int,
    bpm: float,
    steps_per_bar: int = 16,
    bars: int = 8,
) -> tuple[list[float], float]:
    """Смещения атак от сетки (мс), измеренные по самому аудио.

    Для каждой шестнадцатой и каждого такта берём окно ±35 % шага, находим
    пик огибающей атак и считаем смещение точки, где огибающая достигает
    половины пика. По тактам берём медиану: одиночный выброс (например, хэт
    поверх бочки) результат не портит. Пики у краёв окна и «плоские» окна
    отбрасываются — это хвосты предыдущих ударов, а не атаки.
    """
    if samples is None or bpm <= 0 or len(samples) < sample_rate // 2:
        return [], 0.0
    energy, hop_sec = _attack_envelope(samples, sample_rate)
    if len(energy) < 16:
        return [], 0.0

    step_sec = (60.0 / float(bpm)) / 4.0
    search = int(round(step_sec * 0.35 / hop_sec))
    if search < 4:
        return [], 0.0
    gate = float(np.median(energy) + 3.0 * np.std(energy))

    offsets: list[float] = []
    hits = 0
    for step in range(steps_per_bar):
        per_bar: list[float] = []
        for bar in range(bars):
            grid = (bar * steps_per_bar + step) * step_sec
            center = int(round(grid / hop_sec))
            low_index = max(0, center - search)
            high_index = min(len(energy), center + search + 1)
            if high_index - low_index < 6:
                continue
            segment = energy[low_index:high_index]
            peak_index = int(np.argmax(segment))
            peak = float(segment[peak_index])
            if peak < gate:
                continue
            edge = max(1, int(len(segment) * 0.15))
            if peak_index < edge or peak_index >= len(segment) - edge:
                continue
            before = float(energy[max(0, low_index - 3)])
            if peak < before * 1.5:
                continue
            attack = low_index + int(np.argmax(segment >= peak * 0.5))
            per_bar.append((attack * hop_sec - grid) * 1000.0)
        if per_bar:
            offsets.append(round(float(np.median(per_bar)), 2))
            hits += 1
        else:
            offsets.append(0.0)
    return offsets, round(hits / max(1, steps_per_bar), 3)


def extract_groove(audio_path: str, bpm: float = None) -> dict:
    """
    Извлекает ритмический шаблон из трека.
    Возвращает groove_template с:
      - kick_pattern: бинарный массив (такт × 16 шагов)
      - snare_pattern: бинарный массив
      - hihat_density: 0-1
      - swing: 0-1 (0 = straight, 1 = full swing)
      - triplet_rolls: bool
      - pattern_changes: список где паттерн меняется
      - drop_intensity: 0-1
    """
    if librosa is None:
        raise RuntimeError("librosa не установлен")

    y, sr = librosa.load(audio_path, sr=22050, mono=True)

    # BPM если не передан
    if bpm is None:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo) if np.ndim(tempo) == 0 else float(tempo[0])

    # Длительность такта в секундах (4/4)
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4
    steps_per_bar = 16
    step_sec = bar_sec / steps_per_bar

    kick_envelope, snare_envelope, hihat_envelope = _frequency_envelopes(y, sr)
    frames_per_step = max(1, int(step_sec * sr / 512))
    total_steps = min(len(kick_envelope) // frames_per_step, steps_per_bar * 8)
    kick_pattern, snare_pattern, hihat_pattern = _step_envelopes(
        kick_envelope, snare_envelope, hihat_envelope, frames_per_step, total_steps
    )

    if not kick_pattern:
        return {"error": "Не удалось извлечь groove (слишком короткий трек)"}

    # Нормализуем и бинаризуем
    kick_thresh = np.mean(kick_pattern) + 0.3 * np.std(kick_pattern)
    snare_thresh = np.mean(snare_pattern) + 0.3 * np.std(snare_pattern)
    kick_binary = [1 if v > kick_thresh else 0 for v in kick_pattern]
    snare_binary = [1 if v > snare_thresh else 0 for v in snare_pattern]

    # Hihat density
    hihat_mean = float(np.mean(hihat_pattern)) if hihat_pattern else 0
    hihat_density = min(1.0, hihat_mean / (max(hihat_pattern) + 1e-9))

    n_bars = len(kick_pattern) // steps_per_bar
    swing = _swing_value(kick_pattern, steps_per_bar)
    timing_offsets_ms, timing_confidence = _kick_attack_offsets_ms(y, sr, bpm, steps_per_bar)
    triplet_rolls = _has_triplet_rolls(kick_binary, steps_per_bar)
    pattern_changes = _pattern_changes(kick_binary, steps_per_bar, bar_sec)
    drop_intensity = _drop_intensity(kick_pattern, steps_per_bar)

    groove_template = {
        "source": os.path.basename(audio_path),
        "bpm": round(bpm, 2),
        "steps_per_bar": steps_per_bar,
        "kick_pattern": kick_binary[:steps_per_bar],  # первый такт как основной
        "kick_pattern_full": kick_binary,
        "snare_pattern": snare_binary[:steps_per_bar],
        "snare_pattern_full": snare_binary,
        "hihat_density": round(hihat_density, 3),
        "swing": round(swing, 3),
        "timing_offsets_ms": timing_offsets_ms,
        "timing_confidence": timing_confidence,
        "triplet_rolls": triplet_rolls,
        "pattern_changes": pattern_changes,
        "drop_intensity": round(drop_intensity, 3),
        "n_bars_analyzed": n_bars,
        "bar_sec": round(bar_sec, 3),
    }
    return groove_template


def merge_grooves(grooves: list, weights: list = None) -> dict:
    """Объединяет несколько groove templates в один (взвешенное слияние)."""
    if not grooves:
        return {}
    if len(grooves) == 1:
        return grooves[0]

    if weights is None:
        weights = [1.0 / len(grooves)] * len(grooves)
    weights = [w / sum(weights) for w in weights]

    spb = 16  # steps per bar
    merged_kick = [0] * spb
    merged_snare = [0] * spb

    for g, w in zip(grooves, weights):
        kp = g.get("kick_pattern", [0] * spb)
        sp = g.get("snare_pattern", [0] * spb)
        for i in range(min(spb, len(kp))):
            merged_kick[i] += kp[i] * w
        for i in range(min(spb, len(sp))):
            merged_snare[i] += sp[i] * w

    # Бинаризуем по порогу 0.4
    merged_kick = [1 if v > 0.4 else 0 for v in merged_kick]
    merged_snare = [1 if v > 0.4 else 0 for v in merged_snare]

    avg_hihat = sum(g.get("hihat_density", 0) * w for g, w in zip(grooves, weights))
    avg_swing = sum(g.get("swing", 0) * w for g, w in zip(grooves, weights))

    return {
        "bpm": grooves[0].get("bpm", 128),
        "steps_per_bar": spb,
        "kick_pattern": merged_kick,
        "snare_pattern": merged_snare,
        "hihat_density": round(avg_hihat, 3),
        "swing": round(avg_swing, 3),
        "triplet_rolls": any(g.get("triplet_rolls", False) for g in grooves),
        "sources": [g.get("source", "?") for g in grooves],
        "merged": True,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python groove_extractor.py <track.mp3>")
    else:
        print(json.dumps(extract_groove(sys.argv[1]), ensure_ascii=False, indent=2))
