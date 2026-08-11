# -*- coding: utf-8 -*-
"""
[v7] AI Detector Pro — 9 метрик для оценки «нейроношности» трека.

v6 метрики (6): dynamic_range, rms_periodicity, spectral_stability,
                harmonic_ratio, hi_flatness, zcr_consistency.
v7 добавлено (3): hook_repeatability, volume_uniformity, vocal_liveliness.

По разделу 20.2.3 ТЗ — оценка признаков нейроношности из раздела 14.
Выдаёт вердикт + конкретные рекомендации что переделать.
"""
from __future__ import annotations
import os
from pathlib import Path

# Пороги — эмпирические. При выходе за пределы = флаг «нейроношно».
THRESHOLDS = {
    "dynamic_range":       (7.0, 30.0),   # слишком плоско / слишком рвано
    "rms_periodicity":     (0.0, 0.85),   # >0.85 = слишком повторяющееся
    "spectral_stability":  (0.0, 0.92),   # >0.92 = стерильно, «пластик»
    "harmonic_ratio":      (0.25, 0.85),
    "hi_flatness":         (0.05, 0.75),
    "zcr_consistency":     (0.0, 0.88),
    # v7:
    "hook_repeatability":  (0.30, 0.85),  # хук повторяется но не 100%
    "volume_uniformity":   (0.0, 0.90),   # если громкость идеально ровная = флаг
    "vocal_liveliness":    (0.35, 1.0),   # низкая живость = флаг
}

METRIC_ADVICE = {
    "dynamic_range":      "Плоская динамика — добавь тише-громче вариации между куплетом/припевом.",
    "rms_periodicity":    "Слишком ровно повторяется. Добавь брейки, стопы, filter-sweep.",
    "spectral_stability": "Спектр слишком стерильный. Больше живого верха, шума ленты, вибрато.",
    "harmonic_ratio":     "Гармоники неестественные. Проверь микс — вокал может резать середину.",
    "hi_flatness":        "Верхи плоские. Добавь варьирующийся hi-hat, шейкер, air.",
    "zcr_consistency":    "Согласные смазаны. Проверь дикцию, добавь атаки на транзиенты.",
    "hook_repeatability": "Хук слишком одинаково повторяется. Меняй интонацию, добавь адлибы.",
    "volume_uniformity":  "Громкость слишком ровная — «плоский нейро-микс». Верни динамику.",
    "vocal_liveliness":   "Вокал безжизненный. Оставь дыхания, микро-фальш, живые вдохи.",
}


def analyze_track(audio_path: str) -> dict:
    """
    Основная функция. Возвращает JSON с метриками, вердиктом и советами.
    """
    if not audio_path or not os.path.exists(audio_path):
        return {"error": f"файл не найден: {audio_path}"}

    try:
        import librosa
        import numpy as np
    except ImportError:
        return {"error": "librosa/numpy не установлены"}

    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=180)
    except Exception as e:
        return {"error": f"load failed: {e}"}

    metrics = {}
    frame_length, hop = 2048, 512

    # 1) Dynamic range (dB между 95й и 5й перцентилем RMS)
    try:
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop)[0]
        rms_db = 20 * np.log10(rms + 1e-9)
        metrics["dynamic_range"] = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 5))
    except Exception:
        metrics["dynamic_range"] = 0.0

    # 2) RMS periodicity — автокорреляция огибающей громкости
    try:
        env = rms - np.mean(rms)
        corr = np.correlate(env, env, mode="full")[len(env)-1:]
        corr = corr / (corr[0] + 1e-9)
        # Максимум автокорреляции в диапазоне 1-8 сек = регулярность
        lag_min = int(1.0 * sr / hop)
        lag_max = int(8.0 * sr / hop)
        peak = float(np.max(corr[lag_min:lag_max])) if len(corr) > lag_max else 0.0
        metrics["rms_periodicity"] = min(1.0, max(0.0, peak))
    except Exception:
        metrics["rms_periodicity"] = 0.5

    # 3) Spectral stability — сходство спектрограммы между окнами
    try:
        S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
        # Средняя корреляция между соседними колонками
        cols = S / (np.linalg.norm(S, axis=0, keepdims=True) + 1e-9)
        corrs = np.sum(cols[:, 1:] * cols[:, :-1], axis=0)
        metrics["spectral_stability"] = float(np.mean(corrs))
    except Exception:
        metrics["spectral_stability"] = 0.5

    # 4) Harmonic ratio — доля гармонической части
    try:
        y_h, y_p = librosa.effects.hpss(y)
        eh, ep = float(np.mean(y_h**2)), float(np.mean(y_p**2))
        metrics["harmonic_ratio"] = eh / (eh + ep + 1e-9)
    except Exception:
        metrics["harmonic_ratio"] = 0.5

    # 5) Hi-flatness — плоскость верха
    try:
        flat = librosa.feature.spectral_flatness(y=y)[0]
        metrics["hi_flatness"] = float(np.mean(flat))
    except Exception:
        metrics["hi_flatness"] = 0.3

    # 6) ZCR consistency — стабильность zero-crossing (согласные)
    try:
        zcr = librosa.feature.zero_crossing_rate(y=y, frame_length=frame_length, hop_length=hop)[0]
        # Если std/mean маленький — слишком однородно
        metrics["zcr_consistency"] = float(1.0 - min(1.0, np.std(zcr) / (np.mean(zcr) + 1e-9)))
    except Exception:
        metrics["zcr_consistency"] = 0.5

    # 7) [v7] Hook repeatability — повторяемость хука через chroma
    try:
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop)
        # Автокорр по времени
        c = chroma - np.mean(chroma, axis=1, keepdims=True)
        c = c / (np.linalg.norm(c, axis=0, keepdims=True) + 1e-9)
        sim = np.dot(c.T, c)
        # Средняя off-diagonal similarity
        off = sim - np.diag(np.diag(sim))
        metrics["hook_repeatability"] = float(np.mean(np.abs(off)))
    except Exception:
        metrics["hook_repeatability"] = 0.6

    # 8) [v7] Volume uniformity — насколько равномерна громкость (LUFS-proxy)
    try:
        rms_norm = rms / (np.max(rms) + 1e-9)
        # Меньше std = равномернее
        metrics["volume_uniformity"] = float(1.0 - min(1.0, np.std(rms_norm) * 2))
    except Exception:
        metrics["volume_uniformity"] = 0.7

    # 9) [v7] Vocal liveliness — мера «живости» через spectral centroid variance
    try:
        cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
        # Живой вокал — центроид гуляет; пластик — стоит.
        v = float(np.std(cent) / (np.mean(cent) + 1e-9))
        metrics["vocal_liveliness"] = min(1.0, v * 3)
    except Exception:
        metrics["vocal_liveliness"] = 0.5

    # ---- вердикт + рекомендации ----
    flags = []
    advice = []
    for m, (lo, hi) in THRESHOLDS.items():
        v = metrics.get(m, 0.5)
        if v < lo or v > hi:
            flags.append(m)
            advice.append(METRIC_ADVICE.get(m, m))

    score = (len(THRESHOLDS) - len(flags)) / len(THRESHOLDS)   # 1.0 = идеально
    if score > 0.85: verdict = "✅ Живо, коммерческий уровень"
    elif score > 0.65: verdict = "🟡 Нормально, но есть что улучшить"
    elif score > 0.45: verdict = "🟠 Есть признаки нейроношности"
    else: verdict = "🔴 Сильно похоже на нейросеть, надо пересобрать"

    return {
        "ok": True,
        "metrics": {k: round(v, 3) for k, v in metrics.items()},
        "flags": flags,
        "score": round(score, 3),
        "verdict": verdict,
        "advice": advice,
        "path": audio_path,
    }


if __name__ == "__main__":
    import sys
    r = analyze_track(sys.argv[1] if len(sys.argv) > 1 else "")
    import json
    print(json.dumps(r, ensure_ascii=False, indent=2))
