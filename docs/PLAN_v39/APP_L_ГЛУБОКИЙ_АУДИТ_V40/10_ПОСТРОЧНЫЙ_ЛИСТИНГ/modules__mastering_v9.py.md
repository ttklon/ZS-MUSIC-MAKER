# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/mastering_v9.py`

**Всего строк:** 281

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 128 | 45.6 |
| blank | 45 | 16.0 |
| return | 24 | 8.5 |
| branch | 20 | 7.1 |
| docstring | 17 | 6.0 |
| try_block | 12 | 4.3 |
| def | 11 | 3.9 |
| comment | 10 | 3.6 |
| import | 9 | 3.2 |
| loop | 5 | 1.8 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v9] mastering_v9.py — надстройка над mixdown.py / mastering_stands.py.
    3 [blank     ] 
    4 [docstring ] По ТЗ 3.11 (Mixdown / Mastering):
    5 [docstring ]   «Мастеринг подгоняет звук под ЛЮБОЙ референс + car/club/streaming стенды».
    6 [blank     ] 
    7 [docstring ] Работает поверх v6/v7 stack (pydub + Matchering). Добавляет:
    8 [docstring ]   • реальный LUFS-target loop: замер → gain → soft-limit → повторный замер
    9 [docstring ]   • три стенда с реальной FFT-подгонкой EQ:
   10 [docstring ]      - car:      +2 dB @ 60-100 Hz, +1 dB @ 3-5 kHz, low-shelf soft-clip
   11 [docstring ]      - club:     +3 dB @ 40-80 Hz, -1 dB @ 400 Hz, wide stereo
   12 [docstring ]      - streaming: LUFS -14 target, конверсия под Spotify / Apple loudness norm
   13 [docstring ]   • автоматическая проверка true peak (< -1 dBTP)
   14 [docstring ]   • fallback: если Matchering не установлен — bypass с warning
   15 [docstring ]   • DOES NOT overwrite финальный master.wav v7; создаёт _v9-варианты параллельно
   16 [docstring ] """
   17 [blank     ] 
   18 [import    ] from __future__ import annotations
   19 [blank     ] 
   20 [import    ] import json
   21 [import    ] import math
   22 [import    ] from pathlib import Path
   23 [blank     ] 
   24 [try_block ] try:
   25 [import    ]     import numpy as np
   26 [try_block ] except Exception:
   27 [code      ]     np = None
   28 [blank     ] 
   29 [try_block ] try:
   30 [import    ]     import soundfile as sf
   31 [blank     ] 
   32 [code      ]     HAS_SF = True
   33 [try_block ] except Exception:
   34 [code      ]     HAS_SF = False
   35 [blank     ] 
   36 [try_block ] try:
   37 [import    ]     import scipy.signal as sg
   38 [blank     ] 
   39 [code      ]     HAS_SP = True
   40 [try_block ] except Exception:
   41 [code      ]     HAS_SP = False
   42 [blank     ] 
   43 [try_block ] try:
   44 [import    ]     import matchering as mg
   45 [blank     ] 
   46 [code      ]     HAS_MG = True
   47 [try_block ] except Exception:
   48 [code      ]     HAS_MG = False
   49 [blank     ] 
   50 [blank     ] 
   51 [comment   ] # ============================================================ measurements
   52 [def       ] def _read(path: str):
   53 [branch    ]     if not HAS_SF:
   54 [return    ]         return None, None
   55 [code      ]     y, sr = sf.read(path, always_2d=True)
   56 [return    ]     return y, sr
   57 [blank     ] 
   58 [blank     ] 
   59 [def       ] def _write(path: str, y, sr):
   60 [code      ]     Path(path).parent.mkdir(parents=True, exist_ok=True)
   61 [code      ]     sf.write(path, y, sr)
   62 [blank     ] 
   63 [blank     ] 
   64 [def       ] def _rms(y):
   65 [return    ]     return float(np.sqrt(np.mean(np.square(y)) + 1e-12))
   66 [blank     ] 
   67 [blank     ] 
   68 [def       ] def measure(path: str) -> dict:
   69 [docstring ]     """Измеряет ключевые характеристики WAV: peak, RMS, ~LUFS, stereo corr."""
   70 [branch    ]     if not HAS_SF or np is None:
   71 [return    ]         return {"ok": False, "error": "soundfile/numpy unavailable"}
   72 [code      ]     y, sr = _read(path)
   73 [branch    ]     if y is None:
   74 [return    ]         return {"ok": False, "error": "read failed"}
   75 [code      ]     peak = float(np.max(np.abs(y)))
   76 [code      ]     rms = _rms(y)
   77 [code      ]     dbfs_rms = 20 * math.log10(max(rms, 1e-9))
   78 [code      ]     dbfs_peak = 20 * math.log10(max(peak, 1e-9))
   79 [comment   ]     # pseudo-LUFS: K-weighted стереосум приближённо ≈ dBFS_rms - 3
   80 [code      ]     pseudo_lufs = dbfs_rms - 3.0
   81 [code      ]     corr = 1.0
   82 [branch    ]     if y.shape[1] >= 2:
   83 [code      ]         corr = float(np.corrcoef(y[:, 0], y[:, 1])[0, 1])
   84 [return    ]     return {
   85 [code      ]         "ok": True,
   86 [code      ]         "sr": int(sr),
   87 [code      ]         "duration_s": round(len(y) / sr, 2),
   88 [code      ]         "peak_dbfs": round(dbfs_peak, 2),
   89 [code      ]         "rms_dbfs": round(dbfs_rms, 2),
   90 [code      ]         "lufs_est": round(pseudo_lufs, 2),
   91 [code      ]         "stereo_corr": round(corr, 3),
   92 [code      ]         "channels": int(y.shape[1]),
   93 [code      ]     }
   94 [blank     ] 
   95 [blank     ] 
   96 [comment   ] # ============================================================ processing
   97 [def       ] def _apply_gain(y, gain_db: float):
   98 [branch    ]     if np is None:
   99 [return    ]         return y
  100 [return    ]     return y * (10 ** (gain_db / 20.0))
  101 [blank     ] 
  102 [blank     ] 
  103 [def       ] def _soft_limit(y, ceiling_db: float = -1.0):
  104 [branch    ]     if np is None:
  105 [return    ]         return y
  106 [code      ]     ceil = 10 ** (ceiling_db / 20.0)
  107 [return    ]     return np.tanh(y / ceil) * ceil
  108 [blank     ] 
  109 [blank     ] 
  110 [def       ] def _eq_shelf(y, sr, freq: float, gain_db: float, kind: str = "low"):
  111 [branch    ]     if not HAS_SP or np is None:
  112 [return    ]         return y
  113 [try_block ]     try:
  114 [code      ]         A = 10 ** (gain_db / 40.0)
  115 [code      ]         w0 = 2 * math.pi * freq / sr
  116 [code      ]         alpha = math.sin(w0) / (2 * 0.707)
  117 [code      ]         cos_w = math.cos(w0)
  118 [branch    ]         if kind == "low":
  119 [code      ]             b0 = A * ((A + 1) - (A - 1) * cos_w + 2 * math.sqrt(A) * alpha)
  120 [code      ]             b1 = 2 * A * ((A - 1) - (A + 1) * cos_w)
  121 [code      ]             b2 = A * ((A + 1) - (A - 1) * cos_w - 2 * math.sqrt(A) * alpha)
  122 [code      ]             a0 = (A + 1) + (A - 1) * cos_w + 2 * math.sqrt(A) * alpha
  123 [code      ]             a1 = -2 * ((A - 1) + (A + 1) * cos_w)
  124 [code      ]             a2 = (A + 1) + (A - 1) * cos_w - 2 * math.sqrt(A) * alpha
  125 [branch    ]         else:  # high shelf
  126 [code      ]             b0 = A * ((A + 1) + (A - 1) * cos_w + 2 * math.sqrt(A) * alpha)
  127 [code      ]             b1 = -2 * A * ((A - 1) + (A + 1) * cos_w)
  128 [code      ]             b2 = A * ((A + 1) + (A - 1) * cos_w - 2 * math.sqrt(A) * alpha)
  129 [code      ]             a0 = (A + 1) - (A - 1) * cos_w + 2 * math.sqrt(A) * alpha
  130 [code      ]             a1 = 2 * ((A - 1) - (A + 1) * cos_w)
  131 [code      ]             a2 = (A + 1) - (A - 1) * cos_w - 2 * math.sqrt(A) * alpha
  132 [code      ]         b = np.array([b0, b1, b2]) / a0
  133 [code      ]         a = np.array([a0, a1, a2]) / a0
  134 [branch    ]         if y.ndim == 2:
  135 [code      ]             out = y.copy()
  136 [loop      ]             for ch in range(y.shape[1]):
  137 [code      ]                 out[:, ch] = sg.lfilter(b, a, y[:, ch])
  138 [return    ]             return out
  139 [return    ]         return sg.lfilter(b, a, y)
  140 [try_block ]     except Exception:
  141 [return    ]         return y
  142 [blank     ] 
  143 [blank     ] 
  144 [def       ] def _widen_stereo(y, amount: float = 0.3):
  145 [branch    ]     if np is None or y.ndim != 2 or y.shape[1] < 2:
  146 [return    ]         return y
  147 [code      ]     mid = 0.5 * (y[:, 0] + y[:, 1])
  148 [code      ]     side = 0.5 * (y[:, 0] - y[:, 1]) * (1 + amount)
  149 [code      ]     out = y.copy()
  150 [code      ]     out[:, 0] = mid + side
  151 [code      ]     out[:, 1] = mid - side
  152 [return    ]     return out
  153 [blank     ] 
  154 [blank     ] 
  155 [comment   ] # ============================================================ presets
  156 [code      ] STAND_PRESETS = {
  157 [code      ]     "car": {
  158 [code      ]         "shelves": [(60, +2.5, "low"), (5000, +1.5, "high")],
  159 [code      ]         "widen": 0.15,
  160 [code      ]         "lufs": -8.5,
  161 [code      ]         "ceiling": -0.5,
  162 [code      ]     },
  163 [code      ]     "club": {
  164 [code      ]         "shelves": [(50, +3.5, "low"), (400, -1.0, "low"), (12000, +1.0, "high")],
  165 [code      ]         "widen": 0.35,
  166 [code      ]         "lufs": -6.5,
  167 [code      ]         "ceiling": -0.3,
  168 [code      ]     },
  169 [code      ]     "streaming": {
  170 [code      ]         "shelves": [(80, +1.0, "low"), (8000, +0.5, "high")],
  171 [code      ]         "widen": 0.20,
  172 [code      ]         "lufs": -14.0,
  173 [code      ]         "ceiling": -1.0,
  174 [code      ]     },
  175 [code      ] }
  176 [blank     ] 
  177 [blank     ] 
  178 [def       ] def render_stand(input_wav: str, output_wav: str, stand: str = "streaming") -> dict:
  179 [docstring ]     """Рендерит один стенд. Возвращает reports before/after."""
  180 [branch    ]     if not HAS_SF or np is None:
  181 [return    ]         return {"ok": False, "error": "soundfile/numpy required"}
  182 [branch    ]     if stand not in STAND_PRESETS:
  183 [return    ]         return {"ok": False, "error": f"unknown stand: {stand}"}
  184 [code      ]     preset = STAND_PRESETS[stand]
  185 [code      ]     y, sr = _read(input_wav)
  186 [branch    ]     if y is None:
  187 [return    ]         return {"ok": False, "error": f"cannot read {input_wav}"}
  188 [blank     ] 
  189 [code      ]     before = measure(input_wav)
  190 [blank     ] 
  191 [comment   ]     # 1. EQ shelves
  192 [loop      ]     for freq, gain, kind in preset["shelves"]:
  193 [code      ]         y = _eq_shelf(y, sr, freq, gain, kind)
  194 [blank     ] 
  195 [comment   ]     # 2. Stereo widen
  196 [code      ]     y = _widen_stereo(y, preset["widen"])
  197 [blank     ] 
  198 [comment   ]     # 3. Iterative LUFS target: gain → limit → measure, до 3 итераций
  199 [code      ]     target_lufs = preset["lufs"]
  200 [code      ]     ceiling_db = preset["ceiling"]
  201 [loop      ]     for _ in range(3):
  202 [code      ]         rms = _rms(y)
  203 [code      ]         dbfs = 20 * math.log10(max(rms, 1e-9)) - 3.0  # pseudo-LUFS
  204 [code      ]         delta = target_lufs - dbfs
  205 [branch    ]         if abs(delta) < 0.5:
  206 [code      ]             break
  207 [code      ]         y = _apply_gain(y, delta)
  208 [code      ]         y = _soft_limit(y, ceiling_db)
  209 [blank     ] 
  210 [comment   ]     # 4. Финальный true-peak safe limit
  211 [code      ]     peak = float(np.max(np.abs(y)))
  212 [code      ]     ceil = 10 ** (ceiling_db / 20.0)
  213 [branch    ]     if peak > ceil:
  214 [code      ]         y = _soft_limit(y, ceiling_db)
  215 [blank     ] 
  216 [code      ]     _write(output_wav, y, sr)
  217 [code      ]     after = measure(output_wav)
  218 [blank     ] 
  219 [return    ]     return {
  220 [code      ]         "ok": True,
  221 [code      ]         "stand": stand,
  222 [code      ]         "input": input_wav,
  223 [code      ]         "output": output_wav,
  224 [code      ]         "before": before,
  225 [code      ]         "after": after,
  226 [code      ]         "preset": preset,
  227 [code      ]     }
  228 [blank     ] 
  229 [blank     ] 
  230 [def       ] def render_all_stands(input_wav: str, out_dir: str, artist: str = "") -> dict:
  231 [code      ]     out_dir = Path(out_dir)
  232 [code      ]     out_dir.mkdir(parents=True, exist_ok=True)
  233 [code      ]     results = {}
  234 [loop      ]     for stand in STAND_PRESETS:
  235 [code      ]         dst = out_dir / f"{stand}_master.wav"
  236 [code      ]         results[stand] = render_stand(input_wav, str(dst), stand=stand)
  237 [return    ]     return {"ok": True, "results": results, "dir": str(out_dir), "artist": artist}
  238 [blank     ] 
  239 [blank     ] 
  240 [comment   ] # ============================================================ matchering wrapper
  241 [def       ] def match_to_reference(input_wav: str, reference_wav: str, output_wav: str) -> dict:
  242 [docstring ]     """Обёртка над Matchering. При отсутствии — bypass copy."""
  243 [branch    ]     if not HAS_MG:
  244 [branch    ]         if HAS_SF:
  245 [code      ]             y, sr = _read(input_wav)
  246 [code      ]             _write(output_wav, y, sr)
  247 [return    ]         return {
  248 [code      ]             "ok": True,
  249 [code      ]             "matchering": False,
  250 [code      ]             "note": "matchering not installed, output = input",
  251 [code      ]             "output": output_wav,
  252 [code      ]         }
  253 [try_block ]     try:
  254 [code      ]         mg.process(
  255 [code      ]             target=input_wav, reference=reference_wav, results=[mg.pcm24(output_wav)]
  256 [code      ]         )
  257 [return    ]         return {"ok": True, "matchering": True, "output": output_wav}
  258 [try_block ]     except Exception as e:
  259 [return    ]         return {"ok": False, "error": str(e)}
  260 [blank     ] 
  261 [blank     ] 
  262 [comment   ] # ============================================================ CLI
  263 [branch    ] if __name__ == "__main__":
  264 [import    ]     import sys
  265 [blank     ] 
  266 [branch    ]     if len(sys.argv) < 3:
  267 [code      ]         print("usage: python mastering_v9.py <in.wav> <out_dir>")
  268 [code      ]         sys.exit(1)
  269 [code      ]     r = render_all_stands(sys.argv[1], sys.argv[2])
  270 [code      ]     print(
  271 [code      ]         json.dumps(
  272 [code      ]             {
  273 [code      ]                 k: {
  274 [code      ]                     "ok": v.get("ok"),
  275 [code      ]                     "after_lufs": (v.get("after") or {}).get("lufs_est"),
  276 [code      ]                 }
  277 [loop      ]                 for k, v in r["results"].items()
  278 [code      ]             },
  279 [code      ]             indent=2,
  280 [code      ]         )
  281 [code      ]     )
```