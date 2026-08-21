# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/groove_extractor.py`

**Всего строк:** 234

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 117 | 50.0 |
| blank | 34 | 14.5 |
| docstring | 21 | 9.0 |
| branch | 21 | 9.0 |
| comment | 14 | 6.0 |
| loop | 12 | 5.1 |
| import | 5 | 2.1 |
| return | 5 | 2.1 |
| try_block | 2 | 0.9 |
| def | 2 | 0.9 |
| raise | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [2b] groove_extractor.py — Rhythm DNA / Groove Extractor v2 (НОВЫЙ)
    3 [docstring ] Извлекает из референса не ноты и не лупы, а ритмическую ДНК:
    4 [docstring ]   • где кик, где снейр, насколько плотный хэт
    5 [docstring ]   • triplet-rolls, свинг
    6 [docstring ]   • как часто меняется паттерн
    7 [docstring ]   • "кач" дропа
    8 [docstring ] Создаёт абстрактный groove_template для пересборки другими звуками.
    9 [docstring ] """
   10 [blank     ] 
   11 [import    ] import json
   12 [import    ] import os
   13 [blank     ] 
   14 [import    ] import numpy as np
   15 [blank     ] 
   16 [try_block ] try:
   17 [import    ]     import librosa
   18 [try_block ] except ImportError:
   19 [code      ]     librosa = None
   20 [blank     ] 
   21 [blank     ] 
   22 [def       ] def extract_groove(audio_path: str, bpm: float = None) -> dict:
   23 [docstring ]     """
   24 [docstring ]     Извлекает ритмический шаблон из трека.
   25 [docstring ]     Возвращает groove_template с:
   26 [docstring ]       - kick_pattern: бинарный массив (такт × 16 шагов)
   27 [docstring ]       - snare_pattern: бинарный массив
   28 [docstring ]       - hihat_density: 0-1
   29 [docstring ]       - swing: 0-1 (0 = straight, 1 = full swing)
   30 [docstring ]       - triplet_rolls: bool
   31 [docstring ]       - pattern_changes: список где паттерн меняется
   32 [docstring ]       - drop_intensity: 0-1
   33 [docstring ]     """
   34 [branch    ]     if librosa is None:
   35 [raise     ]         raise RuntimeError("librosa не установлен")
   36 [blank     ] 
   37 [code      ]     y, sr = librosa.load(audio_path, sr=22050, mono=True)
   38 [blank     ] 
   39 [comment   ]     # BPM если не передан
   40 [branch    ]     if bpm is None:
   41 [code      ]         tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
   42 [code      ]         bpm = float(tempo) if np.ndim(tempo) == 0 else float(tempo[0])
   43 [blank     ] 
   44 [comment   ]     # Длительность такта в секундах (4/4)
   45 [code      ]     beat_sec = 60.0 / bpm
   46 [code      ]     bar_sec = beat_sec * 4
   47 [code      ]     steps_per_bar = 16
   48 [code      ]     step_sec = bar_sec / steps_per_bar
   49 [blank     ] 
   50 [comment   ]     # Извлекаем kick (низкие частоты)
   51 [code      ]     S = np.abs(librosa.stft(y, n_fft=1024, hop_length=512))
   52 [code      ]     freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
   53 [code      ]     kick_mask = freqs < 80
   54 [code      ]     kick_envelope = S[kick_mask].mean(axis=0)
   55 [blank     ] 
   56 [comment   ]     # Извлекаем snare (200-400 Hz + высокий ZCR)
   57 [code      ]     snare_mask = (freqs >= 150) & (freqs <= 400)
   58 [code      ]     snare_envelope = S[snare_mask].mean(axis=0)
   59 [blank     ] 
   60 [comment   ]     # Извлекаем hihat (высокие частоты > 5000 Hz)
   61 [code      ]     hihat_mask = freqs > 5000
   62 [code      ]     hihat_envelope = (
   63 [code      ]         S[hihat_mask].mean(axis=0) if hihat_mask.any() else np.zeros(S.shape[1])
   64 [code      ]     )
   65 [blank     ] 
   66 [comment   ]     # Вычисляем огибающие по 16 шагам в такте
   67 [code      ]     hop = 512
   68 [code      ]     frames_per_step = max(1, int(step_sec * sr / hop))
   69 [blank     ] 
   70 [code      ]     total_frames = len(kick_envelope)
   71 [code      ]     total_steps = min(total_frames // frames_per_step, steps_per_bar * 8)  # 8 тактов
   72 [blank     ] 
   73 [code      ]     kick_pattern = []
   74 [code      ]     snare_pattern = []
   75 [code      ]     hihat_pattern = []
   76 [blank     ] 
   77 [loop      ]     for step in range(total_steps):
   78 [code      ]         start = step * frames_per_step
   79 [code      ]         end = start + frames_per_step
   80 [branch    ]         if end > total_frames:
   81 [code      ]             break
   82 [code      ]         kick_val = float(kick_envelope[start:end].mean())
   83 [code      ]         snare_val = float(snare_envelope[start:end].mean())
   84 [code      ]         hihat_val = float(hihat_envelope[start:end].mean())
   85 [code      ]         kick_pattern.append(kick_val)
   86 [code      ]         snare_pattern.append(snare_val)
   87 [code      ]         hihat_pattern.append(hihat_val)
   88 [blank     ] 
   89 [branch    ]     if not kick_pattern:
   90 [return    ]         return {"error": "Не удалось извлечь groove (слишком короткий трек)"}
   91 [blank     ] 
   92 [comment   ]     # Нормализуем и бинаризуем
   93 [code      ]     kick_thresh = np.mean(kick_pattern) + 0.3 * np.std(kick_pattern)
   94 [code      ]     snare_thresh = np.mean(snare_pattern) + 0.3 * np.std(snare_pattern)
   95 [code      ]     kick_binary = [1 if v > kick_thresh else 0 for v in kick_pattern]
   96 [code      ]     snare_binary = [1 if v > snare_thresh else 0 for v in snare_pattern]
   97 [blank     ] 
   98 [comment   ]     # Hihat density
   99 [code      ]     hihat_mean = float(np.mean(hihat_pattern)) if hihat_pattern else 0
  100 [code      ]     hihat_std = float(np.std(hihat_pattern)) if hihat_pattern else 0
  101 [code      ]     hihat_density = min(1.0, hihat_mean / (max(hihat_pattern) + 1e-9))
  102 [blank     ] 
  103 [comment   ]     # Свинг: проверяем смещение нечётных шагов
  104 [code      ]     n_bars = len(kick_pattern) // steps_per_bar
  105 [code      ]     swing_vals = []
  106 [loop      ]     for bar in range(n_bars):
  107 [code      ]         bar_start = bar * steps_per_bar
  108 [loop      ]         for step in range(0, steps_per_bar, 2):  # нечётные 16-е
  109 [code      ]             idx = bar_start + step + 1
  110 [branch    ]             if idx < len(kick_pattern):
  111 [code      ]                 swing_vals.append(kick_pattern[idx])
  112 [code      ]     swing = 0.0
  113 [branch    ]     if swing_vals:
  114 [code      ]         even_vals = [
  115 [code      ]             kick_pattern[bar * steps_per_bar + step]
  116 [loop      ]             for bar in range(n_bars)
  117 [loop      ]             for step in range(0, steps_per_bar, 2)
  118 [branch    ]             if bar * steps_per_bar + step < len(kick_pattern)
  119 [code      ]         ]
  120 [branch    ]         if even_vals and swing_vals:
  121 [code      ]             swing = min(
  122 [code      ]                 1.0,
  123 [code      ]                 abs(np.mean(swing_vals) - np.mean(even_vals))
  124 [code      ]                 / (np.mean(even_vals) + 1e-9),
  125 [code      ]             )
  126 [blank     ] 
  127 [comment   ]     # Triplet rolls: ищем триольные группы
  128 [code      ]     triplet_rolls = False
  129 [branch    ]     if n_bars > 0:
  130 [comment   ]         # Проверяем наличие быстрых групп по 3
  131 [loop      ]         for bar in range(min(n_bars, 4)):
  132 [code      ]             bar_start = bar * steps_per_bar
  133 [loop      ]             for step in range(steps_per_bar - 2):
  134 [code      ]                 idx = bar_start + step
  135 [branch    ]                 if idx + 2 < len(kick_binary):
  136 [branch    ]                     if sum(kick_binary[idx : idx + 3]) >= 2:
  137 [code      ]                         triplet_rolls = True
  138 [code      ]                         break
  139 [blank     ] 
  140 [comment   ]     # Pattern changes: где меняется ритм
  141 [code      ]     pattern_changes = []
  142 [branch    ]     if n_bars >= 2:
  143 [loop      ]         for bar in range(1, n_bars):
  144 [code      ]             prev_start = (bar - 1) * steps_per_bar
  145 [code      ]             curr_start = bar * steps_per_bar
  146 [code      ]             prev_pat = kick_binary[prev_start : prev_start + steps_per_bar]
  147 [code      ]             curr_pat = kick_binary[curr_start : curr_start + steps_per_bar]
  148 [branch    ]             if prev_pat != curr_pat:
  149 [code      ]                 pattern_changes.append(
  150 [code      ]                     {"bar": bar, "time_sec": round(bar * bar_sec, 2)}
  151 [code      ]                 )
  152 [blank     ] 
  153 [comment   ]     # Drop intensity: разница между самым энергичным и средним тактом
  154 [code      ]     bar_energies = []
  155 [loop      ]     for bar in range(n_bars):
  156 [code      ]         bar_start = bar * steps_per_bar
  157 [code      ]         bar_end = bar_start + steps_per_bar
  158 [branch    ]         if bar_end <= len(kick_pattern):
  159 [code      ]             bar_energies.append(float(np.mean(kick_pattern[bar_start:bar_end])))
  160 [code      ]     drop_intensity = 0.0
  161 [branch    ]     if bar_energies:
  162 [code      ]         drop_intensity = min(
  163 [code      ]             1.0, max(bar_energies) / (np.mean(bar_energies) + 1e-9) - 1.0
  164 [code      ]         )
  165 [blank     ] 
  166 [code      ]     groove_template = {
  167 [code      ]         "source": os.path.basename(audio_path),
  168 [code      ]         "bpm": round(bpm, 2),
  169 [code      ]         "steps_per_bar": steps_per_bar,
  170 [code      ]         "kick_pattern": kick_binary[:steps_per_bar],  # первый такт как основной
  171 [code      ]         "kick_pattern_full": kick_binary,
  172 [code      ]         "snare_pattern": snare_binary[:steps_per_bar],
  173 [code      ]         "snare_pattern_full": snare_binary,
  174 [code      ]         "hihat_density": round(hihat_density, 3),
  175 [code      ]         "swing": round(swing, 3),
  176 [code      ]         "triplet_rolls": triplet_rolls,
  177 [code      ]         "pattern_changes": pattern_changes,
  178 [code      ]         "drop_intensity": round(drop_intensity, 3),
  179 [code      ]         "n_bars_analyzed": n_bars,
  180 [code      ]         "bar_sec": round(bar_sec, 3),
  181 [code      ]     }
  182 [return    ]     return groove_template
  183 [blank     ] 
  184 [blank     ] 
  185 [def       ] def merge_grooves(grooves: list, weights: list = None) -> dict:
  186 [docstring ]     """Объединяет несколько groove templates в один (взвешенное слияние)."""
  187 [branch    ]     if not grooves:
  188 [return    ]         return {}
  189 [branch    ]     if len(grooves) == 1:
  190 [return    ]         return grooves[0]
  191 [blank     ] 
  192 [branch    ]     if weights is None:
  193 [code      ]         weights = [1.0 / len(grooves)] * len(grooves)
  194 [code      ]     weights = [w / sum(weights) for w in weights]
  195 [blank     ] 
  196 [code      ]     spb = 16  # steps per bar
  197 [code      ]     merged_kick = [0] * spb
  198 [code      ]     merged_snare = [0] * spb
  199 [blank     ] 
  200 [loop      ]     for g, w in zip(grooves, weights):
  201 [code      ]         kp = g.get("kick_pattern", [0] * spb)
  202 [code      ]         sp = g.get("snare_pattern", [0] * spb)
  203 [loop      ]         for i in range(min(spb, len(kp))):
  204 [code      ]             merged_kick[i] += kp[i] * w
  205 [loop      ]         for i in range(min(spb, len(sp))):
  206 [code      ]             merged_snare[i] += sp[i] * w
  207 [blank     ] 
  208 [comment   ]     # Бинаризуем по порогу 0.4
  209 [code      ]     merged_kick = [1 if v > 0.4 else 0 for v in merged_kick]
  210 [code      ]     merged_snare = [1 if v > 0.4 else 0 for v in merged_snare]
  211 [blank     ] 
  212 [code      ]     avg_hihat = sum(g.get("hihat_density", 0) * w for g, w in zip(grooves, weights))
  213 [code      ]     avg_swing = sum(g.get("swing", 0) * w for g, w in zip(grooves, weights))
  214 [blank     ] 
  215 [return    ]     return {
  216 [code      ]         "bpm": grooves[0].get("bpm", 128),
  217 [code      ]         "steps_per_bar": spb,
  218 [code      ]         "kick_pattern": merged_kick,
  219 [code      ]         "snare_pattern": merged_snare,
  220 [code      ]         "hihat_density": round(avg_hihat, 3),
  221 [code      ]         "swing": round(avg_swing, 3),
  222 [code      ]         "triplet_rolls": any(g.get("triplet_rolls", False) for g in grooves),
  223 [code      ]         "sources": [g.get("source", "?") for g in grooves],
  224 [code      ]         "merged": True,
  225 [code      ]     }
  226 [blank     ] 
  227 [blank     ] 
  228 [branch    ] if __name__ == "__main__":
  229 [import    ]     import sys
  230 [blank     ] 
  231 [branch    ]     if len(sys.argv) < 2:
  232 [code      ]         print("Usage: python groove_extractor.py <track.mp3>")
  233 [branch    ]     else:
  234 [code      ]         print(json.dumps(extract_groove(sys.argv[1]), ensure_ascii=False, indent=2))
```