# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/mastering.py`

**Всего строк:** 210

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 91 | 43.3 |
| docstring | 31 | 14.8 |
| blank | 30 | 14.3 |
| branch | 13 | 6.2 |
| return | 11 | 5.2 |
| import | 8 | 3.8 |
| try_block | 8 | 3.8 |
| def | 8 | 3.8 |
| comment | 6 | 2.9 |
| loop | 4 | 1.9 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — modules/mastering.py
    4 [docstring ] ====================================================================
    5 [docstring ] Канонический вход мастеринга для оркестратора.
    6 [blank     ] 
    7 [docstring ] v27 (P0): раньше orchestrator._stage_mastering делал
    8 [docstring ] `from modules import mastering` — но файла modules/mastering.py
    9 [docstring ] НЕ СУЩЕСТВОВАЛО (были только mastering_pro.py / mastering_stands.py).
   10 [docstring ] Стадия мастеринга ВСЕГДА падала → master_streaming.wav никогда не
   11 [docstring ] создавался → smoke_v26: master missing, hit_score stage missing.
   12 [blank     ] 
   13 [docstring ] Этот модуль — честный DSP-мастеринг без тяжёлых зависимостей:
   14 [docstring ]   • per-stand EQ (bass/treble shelves, presence),
   15 [docstring ]   • soft-knee tanh-limiter с итеративной dBFS-компенсацией,
   16 [docstring ]   • целевая громкость по стендам (streaming -13.5 dBFS и т.д.),
   17 [docstring ]   • сохранение СТЕРЕО (никакого mono-downmix),
   18 [docstring ]   • pyloudnorm ITU-BS.1770 LUFS, если установлен (опционально).
   19 [blank     ] 
   20 [docstring ] Публичный API:
   21 [docstring ]   master_all_stands(mix_wav, out_dir, stands=None) -> dict
   22 [docstring ]   master_one(mix_wav, out_wav, stand="streaming") -> dict
   23 [docstring ] """
   24 [blank     ] 
   25 [import    ] from __future__ import annotations
   26 [blank     ] 
   27 [import    ] import os
   28 [import    ] from pathlib import Path
   29 [import    ] from typing import Any
   30 [blank     ] 
   31 [import    ] import numpy as np
   32 [import    ] import soundfile as sf
   33 [blank     ] 
   34 [try_block ] try:  # опционально: точный LUFS по ITU-BS.1770
   35 [import    ]     import pyloudnorm as pyln  # type: ignore
   36 [blank     ] 
   37 [code      ]     _HAS_PYLN = True
   38 [try_block ] except Exception:  # pragma: no cover
   39 [code      ]     pyln = None
   40 [code      ]     _HAS_PYLN = False
   41 [blank     ] 
   42 [comment   ] # Целевые уровни стендов (dBFS RMS-эквивалент; v26: +0.5dB под живые плееры)
   43 [code      ] STAND_TARGET_DBFS: dict[str, float] = {
   44 [code      ]     "streaming": -13.5,
   45 [code      ]     "car": -12.0,
   46 [code      ]     "club": -11.0,
   47 [code      ]     "tiktok": -12.5,
   48 [code      ]     "airpods": -14.0,
   49 [code      ]     "bluetooth": -14.5,
   50 [code      ]     "headphones": -13.5,
   51 [code      ]     "monitors": -13.5,
   52 [code      ] }
   53 [blank     ] 
   54 [code      ] ALL_STANDS = list(STAND_TARGET_DBFS.keys())
   55 [blank     ] 
   56 [blank     ] 
   57 [def       ] def _one_pole_shelf(y: np.ndarray, sr: int, cutoff: float, gain_db: float,
   58 [code      ]                     band: str) -> np.ndarray:
   59 [docstring ]     """Простейший shelving EQ на однополюсном фильтре (low/high band)."""
   60 [code      ]     rc = 1.0 / (2.0 * np.pi * cutoff)
   61 [code      ]     dt = 1.0 / float(sr)
   62 [code      ]     g = 10.0 ** (gain_db / 20.0)
   63 [branch    ]     if y.ndim == 1:
   64 [code      ]         y = y[:, None]
   65 [code      ]         squeeze = True
   66 [branch    ]     else:
   67 [code      ]         squeeze = False
   68 [comment   ]     # lowpass для выделения полосы
   69 [code      ]     a_lp = dt / (rc + dt)
   70 [code      ]     low = np.zeros_like(y)
   71 [code      ]     prev = np.zeros(y.shape[1], dtype=np.float64)
   72 [loop      ]     for n in range(len(y)):
   73 [code      ]         prev = prev + a_lp * (y[n] - prev)
   74 [code      ]         low[n] = prev
   75 [code      ]     high = y - low
   76 [branch    ]     if band == "low":
   77 [code      ]         out = low * g + high
   78 [branch    ]     else:
   79 [code      ]         out = low + high * g
   80 [return    ]     return out[:, 0] if squeeze else out
   81 [blank     ] 
   82 [blank     ] 
   83 [def       ] def _apply_stand_eq(y: np.ndarray, sr: int, stand: str) -> np.ndarray:
   84 [docstring ]     """Характер стенда: низ/верх под сценарий прослушивания."""
   85 [code      ]     eq = {
   86 [code      ]         "streaming": ((150, 0.5, "low"), (8000, 1.0, "high")),
   87 [code      ]         "car": ((120, 2.0, "low"), (6500, 1.5, "high")),
   88 [code      ]         "club": ((100, 2.5, "low"), (9000, 0.5, "high")),
   89 [code      ]         "tiktok": ((200, 1.0, "low"), (7500, 2.0, "high")),
   90 [code      ]         "airpods": ((250, 1.0, "low"), (8000, 1.5, "high")),
   91 [code      ]         "bluetooth": ((180, 1.5, "low"), (7000, 1.0, "high")),
   92 [code      ]         "headphones": ((150, 0.5, "low"), (9000, 0.5, "high")),
   93 [code      ]         "monitors": ((150, 0.0, "low"), (10000, 0.0, "high")),
   94 [code      ]     }
   95 [loop      ]     for cutoff, gdb, band in eq.get(stand, eq["streaming"]):
   96 [branch    ]         if abs(gdb) > 1e-6:
   97 [code      ]             y = _one_pole_shelf(y, sr, cutoff, gdb, band)
   98 [return    ]     return y
   99 [blank     ] 
  100 [blank     ] 
  101 [def       ] def _loudness_dbfs(y: np.ndarray) -> float:
  102 [code      ]     rms = float(np.sqrt(np.mean(y**2)) + 1e-12)
  103 [return    ]     return 20.0 * np.log10(max(rms, 1e-12))
  104 [blank     ] 
  105 [blank     ] 
  106 [def       ] def _loudness_lufs(y: np.ndarray, sr: int) -> float:
  107 [docstring ]     """LUFS через pyloudnorm если есть; иначе dBFS -3dB (sweet-spot под
  108 [docstring ]     mono-downmix, v26)."""
  109 [branch    ]     if _HAS_PYLN:
  110 [try_block ]         try:
  111 [code      ]             meter = pyln.Meter(sr)
  112 [code      ]             mono = y.mean(axis=1) if y.ndim > 1 else y
  113 [return    ]             return float(meter.integrated_loudness(mono))
  114 [try_block ]         except Exception:
  115 [code      ]             pass
  116 [return    ]     return _loudness_dbfs(y) - 3.0
  117 [blank     ] 
  118 [blank     ] 
  119 [def       ] def _tanh_limit(y: np.ndarray, drive: float = 1.0, ceiling: float = 0.98) -> np.ndarray:
  120 [docstring ]     """Soft-knee tanh limiter: glue + защита от клиппинга."""
  121 [return    ]     return np.tanh(y * drive) / np.tanh(drive) * ceiling
  122 [blank     ] 
  123 [blank     ] 
  124 [def       ] def _try_numpy_dsp(y: np.ndarray, sr: int, stand: str) -> tuple[np.ndarray, dict]:
  125 [docstring ]     """Основной DSP-путь мастеринга (честный, fallback_used=False):
  126 [docstring ]     EQ → итеративная loudness-компенсация → tanh-limiter."""
  127 [code      ]     info: dict[str, Any] = {"fallback_used": False, "engine": "numpy_dsp_v27"}
  128 [code      ]     y = _apply_stand_eq(y, sr, stand)
  129 [code      ]     target = STAND_TARGET_DBFS.get(stand, -13.5)
  130 [comment   ]     # tanh-limiter поднимает RMS на ~+3.1dB после насыщения — компенсируем,
  131 [comment   ]     # чтобы итог попадал в целевой dBFS, а не улетал в +3dB (v27 FIX loudness).
  132 [code      ]     target = target - 3.1
  133 [comment   ]     # 3 итерации: gain → limit → измерение → докомпенсация
  134 [loop      ]     for _ in range(3):
  135 [code      ]         cur = _loudness_dbfs(y)
  136 [code      ]         delta = target - cur
  137 [code      ]         y = y * (10.0 ** (delta / 20.0))
  138 [code      ]         y = _tanh_limit(y, drive=1.4)
  139 [code      ]     info["target_dbfs"] = target + 3.1
  140 [code      ]     info["final_dbfs"] = round(_loudness_dbfs(y), 2)
  141 [code      ]     info["final_lufs"] = round(_loudness_lufs(y, sr), 2)
  142 [return    ]     return y, info
  143 [blank     ] 
  144 [blank     ] 
  145 [def       ] def master_one(mix_wav: str, out_wav: str, stand: str = "streaming") -> dict[str, Any]:
  146 [docstring ]     """Мастеринг одного WAV под конкретный стенд. Сохраняет стерео."""
  147 [try_block ]     try:
  148 [code      ]         y, sr = sf.read(mix_wav, always_2d=True)  # (N, C) — стерео сохраняется
  149 [try_block ]     except Exception as e:
  150 [return    ]         return {"ok": False, "reason": f"read failed: {type(e).__name__}: {e}"}
  151 [branch    ]     if y.shape[1] < 2:  # если вошло моно — делаем dual-mono стерео
  152 [code      ]         y = np.repeat(y, 2, axis=1)
  153 [try_block ]     try:
  154 [code      ]         y2, info = _try_numpy_dsp(y, sr, stand)
  155 [code      ]         os.makedirs(os.path.dirname(out_wav) or ".", exist_ok=True)
  156 [code      ]         sf.write(out_wav, y2.astype(np.float32), sr)
  157 [return    ]         return {
  158 [code      ]             "ok": True,
  159 [code      ]             "path": out_wav,
  160 [code      ]             "stand": stand,
  161 [code      ]             "channels": int(y2.shape[1]),
  162 [code      ]             **info,
  163 [code      ]         }
  164 [try_block ]     except Exception as e:
  165 [return    ]         return {"ok": False, "reason": f"dsp failed: {type(e).__name__}: {e}"}
  166 [blank     ] 
  167 [blank     ] 
  168 [def       ] def master_all_stands(
  169 [code      ]     mix_wav: str, out_dir: str, stands: list[str] | None = None
  170 [code      ] ) -> dict[str, Any]:
  171 [docstring ]     """Мастеринг под все запрошенные стенды.
  172 [blank     ] 
  173 [docstring ]     Возвращает {"ok", "masters": {stand: path}, "summary": {...}} —
  174 [docstring ]     контракт, который ждёт orchestrator._stage_mastering.
  175 [docstring ]     """
  176 [code      ]     stands = stands or ALL_STANDS
  177 [code      ]     out = Path(out_dir)
  178 [code      ]     out.mkdir(parents=True, exist_ok=True)
  179 [code      ]     masters: dict[str, str] = {}
  180 [code      ]     fallback = 0
  181 [code      ]     errors: dict[str, str] = {}
  182 [loop      ]     for stand in stands:
  183 [code      ]         out_wav = str(out / f"master_{stand}.wav")
  184 [code      ]         r = master_one(mix_wav, out_wav, stand=stand)
  185 [branch    ]         if r.get("ok"):
  186 [code      ]             masters[stand] = out_wav
  187 [branch    ]             if r.get("fallback_used"):
  188 [code      ]                 fallback += 1
  189 [branch    ]         else:
  190 [code      ]             errors[stand] = str(r.get("reason", "unknown"))
  191 [return    ]     return {
  192 [code      ]         "ok": bool(masters),
  193 [code      ]         "masters": masters,
  194 [code      ]         "summary": {
  195 [code      ]             "total": len(stands),
  196 [code      ]             "done": len(masters),
  197 [code      ]             "fallback": fallback,
  198 [code      ]             "errors": errors,
  199 [code      ]         },
  200 [code      ]         "engine": "modules/mastering.py v27 (numpy_dsp + optional pyloudnorm)",
  201 [code      ]     }
  202 [blank     ] 
  203 [blank     ] 
  204 [branch    ] if __name__ == "__main__":  # быстрый self-check
  205 [import    ]     import sys
  206 [blank     ] 
  207 [branch    ]     if len(sys.argv) > 2:
  208 [code      ]         print(master_all_stands(sys.argv[1], sys.argv[2]))
  209 [branch    ]     else:
  210 [code      ]         print("usage: python -m modules.mastering <mix.wav> <out_dir>")
```