# -*- coding: utf-8 -*-
"""
[2a] stem_splitter.py — Demucs v4 (анализ, не копирование)
Разбирает референс на vocals / drums / bass / other.
Используется ТОЛЬКО для АНАЛИЗА структуры, НЕ для прямого копирования.
"""
import os, subprocess, sys

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "stems")


def split_stems(input_path: str, model: str = "htdemucs") -> dict:
    """Возвращает пути к 4 стемам."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        import demucs.separate  # noqa
    except ImportError:
        return {"error": "Demucs не установлен. pip install demucs"}

    cmd = [
        sys.executable, "-m", "demucs.separate",
        "-n", model,
        "-o", OUTPUT_DIR,
        "--mp3",
        input_path,
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        return {"error": f"Demucs failed: {e}"}

    base = os.path.splitext(os.path.basename(input_path))[0]
    stem_dir = os.path.join(OUTPUT_DIR, model, base)
    result = {}
    for stem in ["vocals", "drums", "bass", "other"]:
        for ext in ("mp3", "wav"):
            p = os.path.join(stem_dir, f"{stem}.{ext}")
            if os.path.exists(p):
                result[stem] = p
                break
    result["note"] = "Стемы используются только как АНАЛИТИЧЕСКАЯ ссылка. Прямое копирование отключено."
    return result


def analyze_arrangement(stems: dict) -> dict:
    """Анализирует плотность стемов -> подсказка для BeatConstructor."""
    try:
        import librosa, numpy as np
    except ImportError:
        return {"error": "librosa не установлен"}
    report = {}
    for name in ["vocals", "drums", "bass", "other"]:
        p = stems.get(name)
        if not p or not os.path.exists(p):
            continue
        y, sr = librosa.load(p, sr=22050, mono=True)
        rms = float(np.mean(librosa.feature.rms(y=y)))
        report[name] = {"energy": round(rms, 4), "present": rms > 0.005}
    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stem_splitter.py <track.mp3>")
    else:
        print(split_stems(sys.argv[1]))
