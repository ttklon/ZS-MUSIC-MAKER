# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/ai_detector_pro.py`

**Всего строк:** 190

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 92 | 48.4 |
| blank | 27 | 14.2 |
| try_block | 22 | 11.6 |
| comment | 19 | 10.0 |
| docstring | 11 | 5.8 |
| branch | 7 | 3.7 |
| import | 6 | 3.2 |
| return | 4 | 2.1 |
| def | 1 | 0.5 |
| loop | 1 | 0.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] AI Detector Pro — 9 метрик для оценки «нейроношности» трека.
    3 [blank     ] 
    4 [docstring ] v6 метрики (6): dynamic_range, rms_periodicity, spectral_stability,
    5 [docstring ]                 harmonic_ratio, hi_flatness, zcr_consistency.
    6 [docstring ] v7 добавлено (3): hook_repeatability, volume_uniformity, vocal_liveliness.
    7 [blank     ] 
    8 [docstring ] По разделу 20.2.3 ТЗ — оценка признаков нейроношности из раздела 14.
    9 [docstring ] Выдаёт вердикт + конкретные рекомендации что переделать.
   10 [docstring ] """
   11 [blank     ] 
   12 [import    ] from __future__ import annotations
   13 [blank     ] 
   14 [import    ] import os
   15 [blank     ] 
   16 [comment   ] # Пороги — эмпирические. При выходе за пределы = флаг «нейроношно».
   17 [code      ] THRESHOLDS = {
   18 [code      ]     "dynamic_range": (7.0, 30.0),  # слишком плоско / слишком рвано
   19 [code      ]     "rms_periodicity": (0.0, 0.85),  # >0.85 = слишком повторяющееся
   20 [code      ]     "spectral_stability": (0.0, 0.92),  # >0.92 = стерильно, «пластик»
   21 [code      ]     "harmonic_ratio": (0.25, 0.85),
   22 [code      ]     "hi_flatness": (0.05, 0.75),
   23 [code      ]     "zcr_consistency": (0.0, 0.88),
   24 [comment   ]     # v7:
   25 [code      ]     "hook_repeatability": (0.30, 0.85),  # хук повторяется но не 100%
   26 [code      ]     "volume_uniformity": (0.0, 0.90),  # если громкость идеально ровная = флаг
   27 [code      ]     "vocal_liveliness": (0.35, 1.0),  # низкая живость = флаг
   28 [code      ] }
   29 [blank     ] 
   30 [code      ] METRIC_ADVICE = {
   31 [code      ]     "dynamic_range": "Плоская динамика — добавь тише-громче вариации между куплетом/припевом.",
   32 [code      ]     "rms_periodicity": "Слишком ровно повторяется. Добавь брейки, стопы, filter-sweep.",
   33 [code      ]     "spectral_stability": "Спектр слишком стерильный. Больше живого верха, шума ленты, вибрато.",
   34 [code      ]     "harmonic_ratio": "Гармоники неестественные. Проверь микс — вокал может резать середину.",
   35 [code      ]     "hi_flatness": "Верхи плоские. Добавь варьирующийся hi-hat, шейкер, air.",
   36 [code      ]     "zcr_consistency": "Согласные смазаны. Проверь дикцию, добавь атаки на транзиенты.",
   37 [code      ]     "hook_repeatability": "Хук слишком одинаково повторяется. Меняй интонацию, добавь адлибы.",
   38 [code      ]     "volume_uniformity": "Громкость слишком ровная — «плоский нейро-микс». Верни динамику.",
   39 [code      ]     "vocal_liveliness": "Вокал безжизненный. Оставь дыхания, микро-фальш, живые вдохи.",
   40 [code      ] }
   41 [blank     ] 
   42 [blank     ] 
   43 [def       ] def analyze_track(audio_path: str) -> dict:
   44 [docstring ]     """
   45 [docstring ]     Основная функция. Возвращает JSON с метриками, вердиктом и советами.
   46 [docstring ]     """
   47 [branch    ]     if not audio_path or not os.path.exists(audio_path):
   48 [return    ]         return {"error": f"файл не найден: {audio_path}"}
   49 [blank     ] 
   50 [try_block ]     try:
   51 [import    ]         import librosa
   52 [import    ]         import numpy as np
   53 [try_block ]     except ImportError:
   54 [return    ]         return {"error": "librosa/numpy не установлены"}
   55 [blank     ] 
   56 [try_block ]     try:
   57 [code      ]         y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=180)
   58 [try_block ]     except Exception as e:
   59 [return    ]         return {"error": f"load failed: {e}"}
   60 [blank     ] 
   61 [code      ]     metrics = {}
   62 [code      ]     frame_length, hop = 2048, 512
   63 [blank     ] 
   64 [comment   ]     # 1) Dynamic range (dB между 95й и 5й перцентилем RMS)
   65 [try_block ]     try:
   66 [code      ]         rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop)[0]
   67 [code      ]         rms_db = 20 * np.log10(rms + 1e-9)
   68 [code      ]         metrics["dynamic_range"] = float(
   69 [code      ]             np.percentile(rms_db, 95) - np.percentile(rms_db, 5)
   70 [code      ]         )
   71 [try_block ]     except Exception:
   72 [code      ]         metrics["dynamic_range"] = 0.0
   73 [blank     ] 
   74 [comment   ]     # 2) RMS periodicity — автокорреляция огибающей громкости
   75 [try_block ]     try:
   76 [code      ]         env = rms - np.mean(rms)
   77 [code      ]         corr = np.correlate(env, env, mode="full")[len(env) - 1 :]
   78 [code      ]         corr = corr / (corr[0] + 1e-9)
   79 [comment   ]         # Максимум автокорреляции в диапазоне 1-8 сек = регулярность
   80 [code      ]         lag_min = int(1.0 * sr / hop)
   81 [code      ]         lag_max = int(8.0 * sr / hop)
   82 [code      ]         peak = float(np.max(corr[lag_min:lag_max])) if len(corr) > lag_max else 0.0
   83 [code      ]         metrics["rms_periodicity"] = min(1.0, max(0.0, peak))
   84 [try_block ]     except Exception:
   85 [code      ]         metrics["rms_periodicity"] = 0.5
   86 [blank     ] 
   87 [comment   ]     # 3) Spectral stability — сходство спектрограммы между окнами
   88 [try_block ]     try:
   89 [code      ]         S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
   90 [comment   ]         # Средняя корреляция между соседними колонками
   91 [code      ]         cols = S / (np.linalg.norm(S, axis=0, keepdims=True) + 1e-9)
   92 [code      ]         corrs = np.sum(cols[:, 1:] * cols[:, :-1], axis=0)
   93 [code      ]         metrics["spectral_stability"] = float(np.mean(corrs))
   94 [try_block ]     except Exception:
   95 [code      ]         metrics["spectral_stability"] = 0.5
   96 [blank     ] 
   97 [comment   ]     # 4) Harmonic ratio — доля гармонической части
   98 [try_block ]     try:
   99 [code      ]         y_h, y_p = librosa.effects.hpss(y)
  100 [code      ]         eh, ep = float(np.mean(y_h**2)), float(np.mean(y_p**2))
  101 [code      ]         metrics["harmonic_ratio"] = eh / (eh + ep + 1e-9)
  102 [try_block ]     except Exception:
  103 [code      ]         metrics["harmonic_ratio"] = 0.5
  104 [blank     ] 
  105 [comment   ]     # 5) Hi-flatness — плоскость верха
  106 [try_block ]     try:
  107 [code      ]         flat = librosa.feature.spectral_flatness(y=y)[0]
  108 [code      ]         metrics["hi_flatness"] = float(np.mean(flat))
  109 [try_block ]     except Exception:
  110 [code      ]         metrics["hi_flatness"] = 0.3
  111 [blank     ] 
  112 [comment   ]     # 6) ZCR consistency — стабильность zero-crossing (согласные)
  113 [try_block ]     try:
  114 [code      ]         zcr = librosa.feature.zero_crossing_rate(
  115 [code      ]             y=y, frame_length=frame_length, hop_length=hop
  116 [code      ]         )[0]
  117 [comment   ]         # Если std/mean маленький — слишком однородно
  118 [code      ]         metrics["zcr_consistency"] = float(
  119 [code      ]             1.0 - min(1.0, np.std(zcr) / (np.mean(zcr) + 1e-9))
  120 [code      ]         )
  121 [try_block ]     except Exception:
  122 [code      ]         metrics["zcr_consistency"] = 0.5
  123 [blank     ] 
  124 [comment   ]     # 7) [v7] Hook repeatability — повторяемость хука через chroma
  125 [try_block ]     try:
  126 [code      ]         chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop)
  127 [comment   ]         # Автокорр по времени
  128 [code      ]         c = chroma - np.mean(chroma, axis=1, keepdims=True)
  129 [code      ]         c = c / (np.linalg.norm(c, axis=0, keepdims=True) + 1e-9)
  130 [code      ]         sim = np.dot(c.T, c)
  131 [comment   ]         # Средняя off-diagonal similarity
  132 [code      ]         off = sim - np.diag(np.diag(sim))
  133 [code      ]         metrics["hook_repeatability"] = float(np.mean(np.abs(off)))
  134 [try_block ]     except Exception:
  135 [code      ]         metrics["hook_repeatability"] = 0.6
  136 [blank     ] 
  137 [comment   ]     # 8) [v7] Volume uniformity — насколько равномерна громкость (LUFS-proxy)
  138 [try_block ]     try:
  139 [code      ]         rms_norm = rms / (np.max(rms) + 1e-9)
  140 [comment   ]         # Меньше std = равномернее
  141 [code      ]         metrics["volume_uniformity"] = float(1.0 - min(1.0, np.std(rms_norm) * 2))
  142 [try_block ]     except Exception:
  143 [code      ]         metrics["volume_uniformity"] = 0.7
  144 [blank     ] 
  145 [comment   ]     # 9) [v7] Vocal liveliness — мера «живости» через spectral centroid variance
  146 [try_block ]     try:
  147 [code      ]         cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
  148 [comment   ]         # Живой вокал — центроид гуляет; пластик — стоит.
  149 [code      ]         v = float(np.std(cent) / (np.mean(cent) + 1e-9))
  150 [code      ]         metrics["vocal_liveliness"] = min(1.0, v * 3)
  151 [try_block ]     except Exception:
  152 [code      ]         metrics["vocal_liveliness"] = 0.5
  153 [blank     ] 
  154 [comment   ]     # ---- вердикт + рекомендации ----
  155 [code      ]     flags = []
  156 [code      ]     advice = []
  157 [loop      ]     for m, (lo, hi) in THRESHOLDS.items():
  158 [code      ]         v = metrics.get(m, 0.5)
  159 [branch    ]         if v < lo or v > hi:
  160 [code      ]             flags.append(m)
  161 [code      ]             advice.append(METRIC_ADVICE.get(m, m))
  162 [blank     ] 
  163 [code      ]     score = (len(THRESHOLDS) - len(flags)) / len(THRESHOLDS)  # 1.0 = идеально
  164 [branch    ]     if score > 0.85:
  165 [code      ]         verdict = "✅ Живо, коммерческий уровень"
  166 [branch    ]     elif score > 0.65:
  167 [code      ]         verdict = "🟡 Нормально, но есть что улучшить"
  168 [branch    ]     elif score > 0.45:
  169 [code      ]         verdict = "🟠 Есть признаки нейроношности"
  170 [branch    ]     else:
  171 [code      ]         verdict = "🔴 Сильно похоже на нейросеть, надо пересобрать"
  172 [blank     ] 
  173 [return    ]     return {
  174 [code      ]         "ok": True,
  175 [code      ]         "metrics": {k: round(v, 3) for k, v in metrics.items()},
  176 [code      ]         "flags": flags,
  177 [code      ]         "score": round(score, 3),
  178 [code      ]         "verdict": verdict,
  179 [code      ]         "advice": advice,
  180 [code      ]         "path": audio_path,
  181 [code      ]     }
  182 [blank     ] 
  183 [blank     ] 
  184 [branch    ] if __name__ == "__main__":
  185 [import    ]     import sys
  186 [blank     ] 
  187 [code      ]     r = analyze_track(sys.argv[1] if len(sys.argv) > 1 else "")
  188 [import    ]     import json
  189 [blank     ] 
  190 [code      ]     print(json.dumps(r, ensure_ascii=False, indent=2))
```