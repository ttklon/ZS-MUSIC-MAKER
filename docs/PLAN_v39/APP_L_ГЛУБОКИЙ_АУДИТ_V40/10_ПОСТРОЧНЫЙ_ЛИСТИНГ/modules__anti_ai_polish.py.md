# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/anti_ai_polish.py`

**Всего строк:** 317

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 122 | 38.5 |
| blank | 48 | 15.1 |
| branch | 36 | 11.4 |
| docstring | 30 | 9.5 |
| return | 28 | 8.8 |
| import | 12 | 3.8 |
| comment | 11 | 3.5 |
| def | 11 | 3.5 |
| try_block | 10 | 3.2 |
| loop | 9 | 2.8 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v9] anti_ai_polish.py — устранение «нейроношности».
    3 [blank     ] 
    4 [docstring ] По ТЗ раздел 14: «RVC делает финальную персонализацию, убирая нейроношность»
    5 [docstring ] + раздел 20 «Устранение ghost harmonies и формульных структур».
    6 [blank     ] 
    7 [docstring ] Модуль работает НА ФИНАЛЬНОМ mixdown WAV перед мастерингом. Применяет цепочку
    8 [docstring ] пост-эффектов, которые «оживляют» звук:
    9 [blank     ] 
   10 [docstring ]   1. micro_timing_jitter        — сдвигаем короткие сегменты на ±3-8 мс
   11 [docstring ]   2. breath_insert              — вставляем реальные дыхания из voice_vault
   12 [docstring ]   3. section_dynamics_variation — меняем громкость по секциям arrangement_plan
   13 [docstring ]   4. ghost_harmonies_kill       — вычитаем регулярные обертоны в 3-6 kHz
   14 [docstring ]   5. formulaic_structure_bust   — вносим лёгкую случайность в 8-барный цикл
   15 [docstring ]   6. tape_saturation            — soft-clip + пыль/шум ленты (very subtle)
   16 [docstring ]   7. imperfect_tuning           — расстраиваем ноты в самых длинных нотах на ±5 центов
   17 [docstring ]   8. lofi_pass                  — вариативное срезание верхов по секциям
   18 [blank     ] 
   19 [docstring ] Всё — post-processing, ничего не переписывает исходники. При отсутствии numpy —
   20 [docstring ] gracefully проходит через no-op с warning.
   21 [docstring ] """
   22 [blank     ] 
   23 [import    ] from __future__ import annotations
   24 [blank     ] 
   25 [import    ] import math
   26 [import    ] import random
   27 [import    ] import time
   28 [import    ] from pathlib import Path
   29 [blank     ] 
   30 [try_block ] try:
   31 [import    ]     import numpy as np
   32 [try_block ] except Exception:
   33 [code      ]     np = None
   34 [blank     ] 
   35 [try_block ] try:
   36 [import    ]     import soundfile as sf
   37 [blank     ] 
   38 [code      ]     HAS_SF = True
   39 [try_block ] except Exception:
   40 [code      ]     HAS_SF = False
   41 [blank     ] 
   42 [blank     ] 
   43 [comment   ] # ============================================================ IO
   44 [def       ] def _read(path: str):
   45 [branch    ]     if not HAS_SF:
   46 [return    ]         return None, None
   47 [code      ]     y, sr = sf.read(path, always_2d=True)
   48 [return    ]     return y, sr
   49 [blank     ] 
   50 [blank     ] 
   51 [def       ] def _write(path: str, y, sr):
   52 [code      ]     Path(path).parent.mkdir(parents=True, exist_ok=True)
   53 [code      ]     sf.write(path, y, sr)
   54 [blank     ] 
   55 [blank     ] 
   56 [comment   ] # ============================================================ effects
   57 [def       ] def _micro_timing_jitter(y, sr, amount_ms: float = 5.0, seed: int | None = None):
   58 [branch    ]     if np is None:
   59 [return    ]         return y
   60 [code      ]     rng = np.random.default_rng(seed or int(time.time()))
   61 [code      ]     seg_len = int(sr * 0.5)  # 500 мс блоки
   62 [code      ]     max_shift = int(sr * amount_ms / 1000.0)
   63 [branch    ]     if max_shift <= 0:
   64 [return    ]         return y
   65 [code      ]     out = np.zeros_like(y)
   66 [code      ]     pos = 0
   67 [loop      ]     while pos < len(y):
   68 [code      ]         seg = y[pos : pos + seg_len]
   69 [code      ]         shift = int(rng.integers(-max_shift, max_shift + 1))
   70 [code      ]         start = max(0, pos + shift)
   71 [code      ]         end = min(len(out), start + len(seg))
   72 [code      ]         out[start:end] += seg[: end - start] * 0.98
   73 [code      ]         pos += seg_len
   74 [code      ]     peak = float(np.max(np.abs(out))) or 1.0
   75 [branch    ]     if peak > 0.99:
   76 [code      ]         out = out * (0.99 / peak)
   77 [return    ]     return out
   78 [blank     ] 
   79 [blank     ] 
   80 [def       ] def _breath_insert(
   81 [code      ]     y, sr, breath_samples: list, positions_sec: list, volume_db: float = -22.0
   82 [code      ] ):
   83 [branch    ]     if np is None or not breath_samples:
   84 [return    ]         return y
   85 [code      ]     out = y.copy()
   86 [code      ]     gain = 10 ** (volume_db / 20.0)
   87 [loop      ]     for t in positions_sec:
   88 [code      ]         idx = int(t * sr)
   89 [branch    ]         if idx >= len(out):
   90 [code      ]             continue
   91 [code      ]         br = breath_samples[hash(t) % len(breath_samples)]
   92 [branch    ]         if br is None:
   93 [code      ]             continue
   94 [code      ]         L = min(len(br), len(out) - idx)
   95 [branch    ]         if out.ndim == 2 and br.ndim == 1:
   96 [code      ]             out[idx : idx + L, 0] += br[:L] * gain
   97 [branch    ]             if out.shape[1] > 1:
   98 [code      ]                 out[idx : idx + L, 1] += br[:L] * gain * 0.9
   99 [branch    ]         else:
  100 [code      ]             out[idx : idx + L] += br[:L] * gain
  101 [return    ]     return out
  102 [blank     ] 
  103 [blank     ] 
  104 [def       ] def _section_dynamics_variation(y, sr, sections: list, seed: int | None = None):
  105 [branch    ]     if np is None or not sections:
  106 [return    ]         return y
  107 [code      ]     rng = random.Random(seed or int(time.time()))
  108 [code      ]     out = y.copy()
  109 [loop      ]     for sec in sections:
  110 [code      ]         s = int(sec.get("start_sec", 0.0) * sr)
  111 [code      ]         e = int(sec.get("end_sec", 0.0) * sr)
  112 [branch    ]         if e <= s or s >= len(out):
  113 [code      ]             continue
  114 [code      ]         e = min(e, len(out))
  115 [code      ]         energy = float(sec.get("energy", 0.7))
  116 [code      ]         span_db = 1.5 if energy < 0.5 else 0.7
  117 [code      ]         gain_db = rng.uniform(-span_db, span_db)
  118 [code      ]         gain = 10 ** (gain_db / 20.0)
  119 [code      ]         out[s:e] = out[s:e] * gain
  120 [code      ]     peak = float(np.max(np.abs(out))) or 1.0
  121 [branch    ]     if peak > 0.99:
  122 [code      ]         out = out * (0.99 / peak)
  123 [return    ]     return out
  124 [blank     ] 
  125 [blank     ] 
  126 [def       ] def _ghost_harmonies_kill(y, sr):
  127 [docstring ]     """
  128 [docstring ]     Устранение "призрачных" гармоник, типичных для RVC/нейронок.
  129 [docstring ]     v14: Добавлены адаптивные частоты 3.2k, 4.8k, 6.4k, 8k.
  130 [docstring ]     """
  131 [branch    ]     if np is None:
  132 [return    ]         return y
  133 [try_block ]     try:
  134 [import    ]         import scipy.signal as sg
  135 [try_block ]     except Exception:
  136 [return    ]         return y
  137 [code      ]     out = y.copy()
  138 [comment   ]     # Нейронки часто свистят на кратных частотах
  139 [loop      ]     for freq in (3200.0, 4800.0, 6400.0, 8000.0):
  140 [branch    ]         if freq >= sr / 2:
  141 [code      ]             continue
  142 [code      ]         b, a = sg.iirnotch(w0=freq / (sr / 2), Q=35.0)  # Узкий notch
  143 [branch    ]         if out.ndim == 2:
  144 [loop      ]             for ch in range(out.shape[1]):
  145 [code      ]                 out[:, ch] = sg.filtfilt(b, a, out[:, ch])
  146 [branch    ]         else:
  147 [code      ]             out = sg.filtfilt(b, a, out)
  148 [return    ]     return out
  149 [blank     ] 
  150 [blank     ] 
  151 [def       ] def _formulaic_structure_bust(y, sr, seed: int | None = None):
  152 [branch    ]     if np is None:
  153 [return    ]         return y
  154 [code      ]     rng = random.Random(seed or int(time.time()))
  155 [code      ]     dur = len(y) / sr
  156 [branch    ]     if dur < 30:
  157 [return    ]         return y
  158 [code      ]     out = y.copy()
  159 [code      ]     n_drops = rng.randint(1, 2)
  160 [loop      ]     for _ in range(n_drops):
  161 [code      ]         t = rng.uniform(0.3 * dur, 0.85 * dur)
  162 [code      ]         drop_len = rng.uniform(0.05, 0.12)
  163 [code      ]         s = int(t * sr)
  164 [code      ]         e = int((t + drop_len) * sr)
  165 [code      ]         e = min(e, len(out))
  166 [branch    ]         if e <= s:
  167 [code      ]             continue
  168 [code      ]         out[s:e] *= rng.uniform(0.05, 0.20)
  169 [return    ]     return out
  170 [blank     ] 
  171 [blank     ] 
  172 [def       ] def _tape_saturation(y, amount: float = 0.06):
  173 [branch    ]     if np is None:
  174 [return    ]         return y
  175 [code      ]     x = np.clip(y * (1 + amount), -1.0, 1.0)
  176 [return    ]     return np.tanh(x * (1 + amount)) * (1 / (1 + amount))
  177 [blank     ] 
  178 [blank     ] 
  179 [def       ] def _imperfect_tuning(y, sr, cents: float = 4.0):
  180 [docstring ]     """
  181 [docstring ]     Реальное микро-расстроение (vibrato) через интерполяцию.
  182 [docstring ]     """
  183 [branch    ]     if np is None:
  184 [return    ]         return y
  185 [try_block ]     try:
  186 [import    ]         from scipy.interpolate import interp1d
  187 [try_block ]     except Exception:
  188 [return    ]         return y
  189 [blank     ] 
  190 [comment   ]     # LFO для сдвига фазы (времени)
  191 [comment   ]     # 0.3 Hz - медленное плавание
  192 [code      ]     t = np.arange(len(y)) / sr
  193 [comment   ]     # cents to frequency ratio: f_new = f_old * 2^(cents/1200)
  194 [comment   ]     # Мы имитируем это через модуляцию времени
  195 [code      ]     lfo = np.sin(2 * math.pi * 0.3 * t) * (cents / 1200.0)
  196 [blank     ] 
  197 [comment   ]     # Искажаем временную шкалу
  198 [code      ]     time_indices = np.arange(len(y))
  199 [comment   ]     # Интегрируем изменение частоты для получения изменения фазы/времени
  200 [comment   ]     # Но для малых отклонений можно просто добавить LFO к индексам
  201 [code      ]     modulated_indices = time_indices + lfo * 10.0  # небольшой джиттер
  202 [blank     ] 
  203 [branch    ]     if y.ndim == 2:
  204 [code      ]         out = np.zeros_like(y)
  205 [loop      ]         for ch in range(y.shape[1]):
  206 [code      ]             f = interp1d(
  207 [code      ]                 time_indices, y[:, ch], kind="linear", fill_value="extrapolate"
  208 [code      ]             )
  209 [code      ]             out[:, ch] = f(modulated_indices)
  210 [return    ]         return out
  211 [branch    ]     else:
  212 [code      ]         f = interp1d(time_indices, y, kind="linear", fill_value="extrapolate")
  213 [return    ]         return f(modulated_indices)
  214 [blank     ] 
  215 [blank     ] 
  216 [def       ] def _lofi_pass(y, sr, cutoff: float = 15000.0):
  217 [branch    ]     if np is None:
  218 [return    ]         return y
  219 [try_block ]     try:
  220 [import    ]         import scipy.signal as sg
  221 [try_block ]     except Exception:
  222 [return    ]         return y
  223 [code      ]     b, a = sg.butter(4, cutoff / (sr / 2), btype="low")
  224 [branch    ]     if y.ndim == 2:
  225 [code      ]         out = y.copy()
  226 [loop      ]         for ch in range(y.shape[1]):
  227 [code      ]             out[:, ch] = sg.filtfilt(b, a, y[:, ch])
  228 [return    ]         return out
  229 [return    ]     return sg.filtfilt(b, a, y)
  230 [blank     ] 
  231 [blank     ] 
  232 [comment   ] # ============================================================ main API
  233 [def       ] def polish_track(
  234 [code      ]     input_wav: str,
  235 [code      ]     output_wav: str,
  236 [code      ]     arrangement_plan: dict | None = None,
  237 [code      ]     breath_samples: list | None = None,
  238 [code      ]     preset: str = "standard",
  239 [code      ]     seed: int | None = None,
  240 [code      ] ) -> dict:
  241 [docstring ]     """
  242 [docstring ]     preset:
  243 [docstring ]       • gentle    — минимальная обработка (для sing/melodic)
  244 [docstring ]       • standard  — универсал (default)
  245 [docstring ]       • aggressive — жёсткое разрушение формульности (для phonk / trap)
  246 [docstring ]     """
  247 [branch    ]     if not HAS_SF:
  248 [return    ]         return {"ok": False, "error": "soundfile unavailable"}
  249 [code      ]     y, sr = _read(input_wav)
  250 [branch    ]     if y is None:
  251 [return    ]         return {"ok": False, "error": f"cannot read {input_wav}"}
  252 [blank     ] 
  253 [code      ]     stages_applied = []
  254 [blank     ] 
  255 [code      ]     amount_ms = {"gentle": 2.5, "standard": 5.0, "aggressive": 8.0}[preset]
  256 [code      ]     y = _micro_timing_jitter(y, sr, amount_ms=amount_ms, seed=seed)
  257 [code      ]     stages_applied.append(f"micro_timing_jitter({amount_ms}ms)")
  258 [blank     ] 
  259 [branch    ]     if breath_samples and arrangement_plan:
  260 [code      ]         secs = arrangement_plan.get("sections", [])
  261 [code      ]         positions = []
  262 [loop      ]         for s in secs:
  263 [branch    ]             if s.get("name", "").startswith(("verse", "chorus", "prechorus")):
  264 [code      ]                 positions.append(float(s.get("start_sec", 0.0)) + 0.05)
  265 [code      ]         y = _breath_insert(y, sr, breath_samples, positions, volume_db=-24.0)
  266 [code      ]         stages_applied.append(f"breath_insert(n={len(positions)})")
  267 [blank     ] 
  268 [branch    ]     if arrangement_plan and arrangement_plan.get("sections"):
  269 [code      ]         y = _section_dynamics_variation(y, sr, arrangement_plan["sections"], seed=seed)
  270 [code      ]         stages_applied.append("section_dynamics_variation")
  271 [blank     ] 
  272 [branch    ]     if preset in ("standard", "aggressive"):
  273 [code      ]         y = _ghost_harmonies_kill(y, sr)
  274 [code      ]         stages_applied.append("ghost_harmonies_kill")
  275 [blank     ] 
  276 [branch    ]     if preset == "aggressive":
  277 [code      ]         y = _formulaic_structure_bust(y, sr, seed=seed)
  278 [code      ]         stages_applied.append("formulaic_structure_bust")
  279 [blank     ] 
  280 [code      ]     y = _tape_saturation(
  281 [code      ]         y, amount={"gentle": 0.02, "standard": 0.05, "aggressive": 0.09}[preset]
  282 [code      ]     )
  283 [code      ]     stages_applied.append("tape_saturation")
  284 [blank     ] 
  285 [branch    ]     if preset in ("gentle", "standard"):
  286 [code      ]         y = _imperfect_tuning(y, sr, cents=3.0)
  287 [code      ]         stages_applied.append("imperfect_tuning")
  288 [blank     ] 
  289 [code      ]     cutoff = {"gentle": 17000.0, "standard": 16000.0, "aggressive": 14500.0}[preset]
  290 [code      ]     y = _lofi_pass(y, sr, cutoff=cutoff)
  291 [code      ]     stages_applied.append(f"lofi_pass({cutoff:.0f})")
  292 [blank     ] 
  293 [code      ]     _write(output_wav, y, sr)
  294 [return    ]     return {
  295 [code      ]         "ok": True,
  296 [code      ]         "input": input_wav,
  297 [code      ]         "output": output_wav,
  298 [code      ]         "preset": preset,
  299 [code      ]         "stages_applied": stages_applied,
  300 [code      ]         "sr": int(sr),
  301 [code      ]     }
  302 [blank     ] 
  303 [blank     ] 
  304 [branch    ] if __name__ == "__main__":
  305 [import    ]     import sys
  306 [blank     ] 
  307 [branch    ]     if len(sys.argv) < 3:
  308 [code      ]         print("usage: python anti_ai_polish.py <in.wav> <out.wav> [preset]")
  309 [code      ]         sys.exit(1)
  310 [code      ]     r = polish_track(
  311 [code      ]         sys.argv[1],
  312 [code      ]         sys.argv[2],
  313 [code      ]         preset=sys.argv[3] if len(sys.argv) > 3 else "standard",
  314 [code      ]     )
  315 [import    ]     import json
  316 [blank     ] 
  317 [code      ]     print(json.dumps(r, ensure_ascii=False, indent=2))
```