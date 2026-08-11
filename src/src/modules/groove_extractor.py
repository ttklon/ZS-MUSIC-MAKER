# -*- coding: utf-8 -*-
"""
[2b] groove_extractor.py — Rhythm DNA / Groove Extractor v2 (НОВЫЙ)
Извлекает из референса не ноты и не лупы, а ритмическую ДНК:
  • где кик, где снейр, насколько плотный хэт
  • triplet-rolls, свинг
  • как часто меняется паттерн
  • "кач" дропа
Создаёт абстрактный groove_template для пересборки другими звуками.
"""
import os, json, numpy as np

try:
    import librosa
except ImportError:
    librosa = None


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

    # Извлекаем kick (низкие частоты)
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
    kick_mask = freqs < 80
    kick_envelope = S[kick_mask].mean(axis=0)

    # Извлекаем snare (200-400 Hz + высокий ZCR)
    snare_mask = (freqs >= 150) & (freqs <= 400)
    snare_envelope = S[snare_mask].mean(axis=0)

    # Извлекаем hihat (высокие частоты > 5000 Hz)
    hihat_mask = freqs > 5000
    hihat_envelope = S[hihat_mask].mean(axis=0) if hihat_mask.any() else np.zeros(S.shape[1])

    # Вычисляем огибающие по 16 шагам в такте
    hop = 512
    frames_per_step = max(1, int(step_sec * sr / hop))

    total_frames = len(kick_envelope)
    total_steps = min(total_frames // frames_per_step, steps_per_bar * 8)  # 8 тактов

    kick_pattern = []
    snare_pattern = []
    hihat_pattern = []

    for step in range(total_steps):
        start = step * frames_per_step
        end = start + frames_per_step
        if end > total_frames:
            break
        kick_val = float(kick_envelope[start:end].mean())
        snare_val = float(snare_envelope[start:end].mean())
        hihat_val = float(hihat_envelope[start:end].mean())
        kick_pattern.append(kick_val)
        snare_pattern.append(snare_val)
        hihat_pattern.append(hihat_val)

    if not kick_pattern:
        return {"error": "Не удалось извлечь groove (слишком короткий трек)"}

    # Нормализуем и бинаризуем
    kick_thresh = np.mean(kick_pattern) + 0.3 * np.std(kick_pattern)
    snare_thresh = np.mean(snare_pattern) + 0.3 * np.std(snare_pattern)
    kick_binary = [1 if v > kick_thresh else 0 for v in kick_pattern]
    snare_binary = [1 if v > snare_thresh else 0 for v in snare_pattern]

    # Hihat density
    hihat_mean = float(np.mean(hihat_pattern)) if hihat_pattern else 0
    hihat_std = float(np.std(hihat_pattern)) if hihat_pattern else 0
    hihat_density = min(1.0, hihat_mean / (max(hihat_pattern) + 1e-9))

    # Свинг: проверяем смещение нечётных шагов
    n_bars = len(kick_pattern) // steps_per_bar
    swing_vals = []
    for bar in range(n_bars):
        bar_start = bar * steps_per_bar
        for step in range(0, steps_per_bar, 2):  # нечётные 16-е
            idx = bar_start + step + 1
            if idx < len(kick_pattern):
                swing_vals.append(kick_pattern[idx])
    swing = 0.0
    if swing_vals:
        even_vals = [kick_pattern[bar * steps_per_bar + step]
                     for bar in range(n_bars) for step in range(0, steps_per_bar, 2)
                     if bar * steps_per_bar + step < len(kick_pattern)]
        if even_vals and swing_vals:
            swing = min(1.0, abs(np.mean(swing_vals) - np.mean(even_vals)) /
                        (np.mean(even_vals) + 1e-9))

    # Triplet rolls: ищем триольные группы
    triplet_rolls = False
    if n_bars > 0:
        # Проверяем наличие быстрых групп по 3
        for bar in range(min(n_bars, 4)):
            bar_start = bar * steps_per_bar
            for step in range(steps_per_bar - 2):
                idx = bar_start + step
                if idx + 2 < len(kick_binary):
                    if sum(kick_binary[idx:idx+3]) >= 2:
                        triplet_rolls = True
                        break

    # Pattern changes: где меняется ритм
    pattern_changes = []
    if n_bars >= 2:
        for bar in range(1, n_bars):
            prev_start = (bar - 1) * steps_per_bar
            curr_start = bar * steps_per_bar
            prev_pat = kick_binary[prev_start:prev_start + steps_per_bar]
            curr_pat = kick_binary[curr_start:curr_start + steps_per_bar]
            if prev_pat != curr_pat:
                pattern_changes.append({"bar": bar, "time_sec": round(bar * bar_sec, 2)})

    # Drop intensity: разница между самым энергичным и средним тактом
    bar_energies = []
    for bar in range(n_bars):
        bar_start = bar * steps_per_bar
        bar_end = bar_start + steps_per_bar
        if bar_end <= len(kick_pattern):
            bar_energies.append(float(np.mean(kick_pattern[bar_start:bar_end])))
    drop_intensity = 0.0
    if bar_energies:
        drop_intensity = min(1.0, max(bar_energies) / (np.mean(bar_energies) + 1e-9) - 1.0)

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
