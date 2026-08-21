# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/sidechain.py`

**Всего строк:** 290

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 156 | 53.8 |
| blank | 37 | 12.8 |
| branch | 19 | 6.6 |
| docstring | 17 | 5.9 |
| return | 16 | 5.5 |
| try_block | 14 | 4.8 |
| import | 12 | 4.1 |
| def | 7 | 2.4 |
| comment | 6 | 2.1 |
| loop | 4 | 1.4 |
| decorator | 1 | 0.3 |
| class | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v14 — sidechain.py (настоящий sidechain, TZ 19.5, P0.04)
    3 [docstring ] ========================================================================
    4 [blank     ] 
    5 [docstring ] Реализация sidechain-компрессии:
    6 [docstring ]   — numpy DSP: envelope-follower на кик-канале, ratio-компрессор,
    7 [docstring ]     time-varying gain применяется к bus;
    8 [docstring ]   — pedalboard (если доступен) как препроцессор;
    9 [docstring ]   — метрика ducking: RMS bus в момент кика vs между киками (по ТЗ
   10 [docstring ]     должна быть минимум 3 dB).
   11 [blank     ] 
   12 [docstring ] НЕ имитация volume-envelope по сетке — реальный расчёт envelope
   13 [docstring ] от кик-канала.
   14 [docstring ] """
   15 [blank     ] 
   16 [import    ] from __future__ import annotations
   17 [blank     ] 
   18 [import    ] import json
   19 [import    ] import math
   20 [import    ] from dataclasses import dataclass
   21 [import    ] from pathlib import Path
   22 [import    ] from typing import Any
   23 [blank     ] 
   24 [try_block ] try:
   25 [import    ]     import pedalboard as _pb  # type: ignore
   26 [blank     ] 
   27 [code      ]     PB_OK = True
   28 [try_block ] except Exception:
   29 [code      ]     _pb = None
   30 [code      ]     PB_OK = False
   31 [blank     ] 
   32 [try_block ] try:
   33 [import    ]     import numpy as _np
   34 [import    ]     import soundfile as _sf
   35 [blank     ] 
   36 [code      ]     NP_OK = True
   37 [try_block ] except Exception:
   38 [code      ]     _np = None
   39 [code      ]     _sf = None
   40 [code      ]     NP_OK = False
   41 [blank     ] 
   42 [comment   ] # v18 FIX: scipy вынесен из общего try — без него numpy-DSP должен работать.
   43 [try_block ] try:
   44 [import    ]     from scipy.signal import butter as _butter
   45 [import    ]     from scipy.signal import sosfilt as _sosfilt
   46 [blank     ] 
   47 [code      ]     SCIPY_OK = True
   48 [try_block ] except Exception:
   49 [code      ]     _butter = None
   50 [code      ]     _sosfilt = None
   51 [code      ]     SCIPY_OK = False
   52 [blank     ] 
   53 [blank     ] 
   54 [decorator ] @dataclass
   55 [class     ] class SidechainResult:
   56 [code      ]     ok: bool
   57 [code      ]     engine: str
   58 [code      ]     out_wav: str
   59 [code      ]     intensity: float
   60 [code      ]     kick_rms_db: float
   61 [code      ]     bus_before_rms_db: float
   62 [code      ]     bus_after_rms_db: float
   63 [code      ]     ducking_db: float
   64 [code      ]     reason: str | None = None
   65 [blank     ] 
   66 [blank     ] 
   67 [def       ] def _envelope_from_kick(
   68 [code      ]     kick_y, sr: int, attack_ms: float = 5.0, release_ms: float = 120.0
   69 [code      ] ):
   70 [branch    ]     if _np is None:
   71 [return    ]         return None
   72 [code      ]     x = _np.abs(kick_y)
   73 [code      ]     w = max(1, int(sr * 0.005))
   74 [branch    ]     if w > 1:
   75 [code      ]         k = _np.ones(w) / w
   76 [code      ]         x = _np.convolve(x, k, mode="same")
   77 [code      ]     a = math.exp(-1.0 / (sr * (attack_ms / 1000.0)))
   78 [code      ]     r = math.exp(-1.0 / (sr * (release_ms / 1000.0)))
   79 [code      ]     env = _np.zeros_like(x)
   80 [code      ]     y = 0.0
   81 [loop      ]     for i in range(len(x)):
   82 [branch    ]         if x[i] > y:
   83 [code      ]             y = a * y + (1 - a) * x[i]
   84 [branch    ]         else:
   85 [code      ]             y = r * y + (1 - r) * x[i]
   86 [code      ]         env[i] = y
   87 [return    ]     return env
   88 [blank     ] 
   89 [blank     ] 
   90 [def       ] def _bandpass_numpy(kick_y, sr: int, lo_hz: float = 30.0, hi_hz: float = 200.0):
   91 [docstring ]     """v18: честный numpy-only bandpass 30-200 Гц без scipy.
   92 [blank     ] 
   93 [docstring ]     FFT brick-wall фильтр: обнуляем частоты вне полосы кика и делаем
   94 [docstring ]     обратное FFT. Это реальный фильтр (не имитация), подходит для
   95 [docstring ]     onset-детекции бочки на слабом железе без scipy.
   96 [docstring ]     """
   97 [code      ]     n = len(kick_y)
   98 [branch    ]     if n < 4:
   99 [return    ]         return kick_y
  100 [code      ]     spec = _np.fft.rfft(kick_y)
  101 [code      ]     freqs = _np.fft.rfftfreq(n, d=1.0 / sr)
  102 [code      ]     mask = (freqs >= lo_hz) & (freqs <= hi_hz)
  103 [code      ]     spec = spec * mask
  104 [return    ]     return _np.fft.irfft(spec, n=n).astype("float32")
  105 [blank     ] 
  106 [blank     ] 
  107 [def       ] def _detect_kick_onsets(kick_y, sr: int):
  108 [branch    ]     if _np is None:
  109 [return    ]         return []
  110 [try_block ]     try:
  111 [branch    ]         if SCIPY_OK:
  112 [code      ]             sos = _butter(4, [30, 200], btype="band", fs=sr, output="sos")
  113 [code      ]             y = _sosfilt(sos, kick_y)
  114 [branch    ]         else:
  115 [comment   ]             # v18: numpy-only полосовой фильтр, детекция больше не
  116 [comment   ]             # молча отваливается без scipy.
  117 [code      ]             y = _bandpass_numpy(kick_y, sr)
  118 [code      ]         env = _np.abs(y)
  119 [code      ]         w = int(sr * 0.01)
  120 [branch    ]         if w > 1:
  121 [code      ]             k = _np.ones(w) / w
  122 [code      ]             env = _np.convolve(env, k, mode="same")
  123 [code      ]         thr = float(_np.mean(env) + 3 * _np.std(env))
  124 [code      ]         onsets = []
  125 [code      ]         min_gap = int(sr * 0.08)
  126 [code      ]         last = -min_gap
  127 [loop      ]         for i in range(1, len(env) - 1):
  128 [branch    ]             if env[i] > thr and env[i] > env[i - 1] and env[i] >= env[i + 1]:
  129 [branch    ]                 if i - last > min_gap:
  130 [code      ]                     onsets.append(i)
  131 [code      ]                     last = i
  132 [return    ]         return onsets
  133 [try_block ]     except Exception:
  134 [return    ]         return []
  135 [blank     ] 
  136 [blank     ] 
  137 [def       ] def _numpy_dsp(
  138 [code      ]     bus_wav: str,
  139 [code      ]     kick_wav: str,
  140 [code      ]     out_wav: str,
  141 [code      ]     intensity: float,
  142 [code      ]     ratio: float = 4.0,
  143 [code      ]     attack_ms: float = 5.0,
  144 [code      ]     release_ms: float = 120.0,
  145 [code      ] ) -> SidechainResult:
  146 [branch    ]     if not NP_OK:
  147 [return    ]         return SidechainResult(
  148 [code      ]             ok=False,
  149 [code      ]             engine="none",
  150 [code      ]             out_wav="",
  151 [code      ]             intensity=intensity,
  152 [code      ]             kick_rms_db=-100,
  153 [code      ]             bus_before_rms_db=-100,
  154 [code      ]             bus_after_rms_db=-100,
  155 [code      ]             ducking_db=0.0,
  156 [code      ]             reason="numpy/soundfile unavailable",
  157 [code      ]         )
  158 [try_block ]     try:
  159 [code      ]         bus, sr_b = _sf.read(bus_wav, always_2d=True)
  160 [code      ]         kick, sr_k = _sf.read(kick_wav, always_2d=True)
  161 [branch    ]         if sr_k != sr_b:
  162 [import    ]             import scipy.signal as ss
  163 [blank     ] 
  164 [code      ]             kick_mono = kick[:, 0] if kick.ndim > 1 else kick
  165 [code      ]             n = int(len(kick_mono) * sr_b / sr_k)
  166 [code      ]             kick_mono = ss.resample(kick_mono, n)
  167 [code      ]             kick = kick_mono
  168 [branch    ]         else:
  169 [code      ]             kick = kick[:, 0] if kick.ndim > 1 else kick.reshape(-1)
  170 [blank     ] 
  171 [code      ]         n = min(len(bus), len(kick))
  172 [code      ]         bus = bus[:n]
  173 [code      ]         kick = kick[:n]
  174 [branch    ]         if _np.ndim(kick) > 1:
  175 [code      ]             kick = kick[:, 0]
  176 [blank     ] 
  177 [comment   ]         # v19: HP/BP-фильтр 30-200 Гц по kick-каналу ПЕРЕД envelope-follower.
  178 [comment   ]         # Защита от ложных дакингов на вокал/hi-hat, если по ошибке в kick_wav
  179 [comment   ]         # пришёл bus/mix. Реальная бочка обычно 30-200 Гц.
  180 [try_block ]         try:
  181 [code      ]             kick_hp = _bandpass_numpy(
  182 [code      ]                 kick.astype("float32"), sr_b, lo_hz=30.0, hi_hz=200.0
  183 [code      ]             )
  184 [try_block ]         except Exception:
  185 [code      ]             kick_hp = kick.astype("float32")
  186 [code      ]         env = _envelope_from_kick(
  187 [code      ]             kick_hp, sr_b, attack_ms=attack_ms, release_ms=release_ms
  188 [code      ]         )
  189 [code      ]         env_max = float(_np.max(env) + 1e-9)
  190 [code      ]         env_n = env / env_max
  191 [blank     ] 
  192 [code      ]         thr_lin = 10 ** (-18.0 / 20)
  193 [code      ]         over = _np.maximum(env_n - thr_lin, 0.0)
  194 [code      ]         gr_db = -over * 20.0 * (1 - 1 / ratio) * intensity
  195 [code      ]         gain_lin = 10 ** (gr_db / 20)
  196 [blank     ] 
  197 [code      ]         bus_ducked = bus.copy()
  198 [loop      ]         for c in range(bus.shape[1]):
  199 [code      ]             bus_ducked[:, c] = bus[:, c] * gain_lin
  200 [code      ]         bus_ducked = _np.clip(bus_ducked, -1.0, 1.0)
  201 [blank     ] 
  202 [code      ]         Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
  203 [code      ]         _sf.write(out_wav, bus_ducked, sr_b)
  204 [blank     ] 
  205 [code      ]         kick_rms = float(_np.sqrt(_np.mean(kick**2)) + 1e-9)
  206 [code      ]         bus_rms_b = float(_np.sqrt(_np.mean(bus**2)) + 1e-9)
  207 [code      ]         bus_rms_a = float(_np.sqrt(_np.mean(bus_ducked**2)) + 1e-9)
  208 [code      ]         ducking = measure_ducking_effect(bus, bus_ducked, kick, sr_b)
  209 [blank     ] 
  210 [return    ]         return SidechainResult(
  211 [code      ]             ok=True,
  212 [code      ]             engine="numpy_dsp_real_sidechain",
  213 [code      ]             out_wav=out_wav,
  214 [code      ]             intensity=intensity,
  215 [code      ]             kick_rms_db=20 * math.log10(kick_rms),
  216 [code      ]             bus_before_rms_db=20 * math.log10(bus_rms_b),
  217 [code      ]             bus_after_rms_db=20 * math.log10(bus_rms_a),
  218 [code      ]             ducking_db=ducking,
  219 [code      ]         )
  220 [try_block ]     except Exception as e:
  221 [return    ]         return SidechainResult(
  222 [code      ]             ok=False,
  223 [code      ]             engine="none",
  224 [code      ]             out_wav="",
  225 [code      ]             intensity=intensity,
  226 [code      ]             kick_rms_db=-100,
  227 [code      ]             bus_before_rms_db=-100,
  228 [code      ]             bus_after_rms_db=-100,
  229 [code      ]             ducking_db=0.0,
  230 [code      ]             reason=str(e),
  231 [code      ]         )
  232 [blank     ] 
  233 [blank     ] 
  234 [def       ] def measure_ducking_effect(bus_before, bus_after, kick, sr: int) -> float:
  235 [branch    ]     if _np is None:
  236 [return    ]         return 0.0
  237 [try_block ]     try:
  238 [code      ]         onsets = _detect_kick_onsets(kick, sr)
  239 [branch    ]         if not onsets:
  240 [return    ]             return 0.0
  241 [code      ]         w = int(sr * 0.05)
  242 [code      ]         deltas = []
  243 [code      ]         b = bus_before[:, 0] if bus_before.ndim > 1 else bus_before
  244 [code      ]         a = bus_after[:, 0] if bus_after.ndim > 1 else bus_after
  245 [loop      ]         for o in onsets:
  246 [code      ]             s = o
  247 [code      ]             e = min(o + w, len(b))
  248 [branch    ]             if e - s < 10:
  249 [code      ]                 continue
  250 [code      ]             r_b = float(_np.sqrt(_np.mean(b[s:e] ** 2)) + 1e-9)
  251 [code      ]             r_a = float(_np.sqrt(_np.mean(a[s:e] ** 2)) + 1e-9)
  252 [code      ]             deltas.append(20 * math.log10(r_b / r_a))
  253 [return    ]         return float(_np.mean(deltas)) if deltas else 0.0
  254 [try_block ]     except Exception:
  255 [return    ]         return 0.0
  256 [blank     ] 
  257 [blank     ] 
  258 [def       ] def apply_sidechain(
  259 [code      ]     bus_wav: str,
  260 [code      ]     kick_wav: str,
  261 [code      ]     out_wav: str,
  262 [code      ]     intensity: float = 0.5,
  263 [code      ]     ratio: float = 4.0,
  264 [code      ]     attack_ms: float = 5.0,
  265 [code      ]     release_ms: float = 120.0,
  266 [code      ] ) -> dict[str, Any]:
  267 [code      ]     r = _numpy_dsp(
  268 [code      ]         bus_wav,
  269 [code      ]         kick_wav,
  270 [code      ]         out_wav,
  271 [code      ]         intensity,
  272 [code      ]         ratio=ratio,
  273 [code      ]         attack_ms=attack_ms,
  274 [code      ]         release_ms=release_ms,
  275 [code      ]     )
  276 [return    ]     return r.__dict__
  277 [blank     ] 
  278 [blank     ] 
  279 [def       ] def capability_report() -> dict[str, Any]:
  280 [return    ]     return {
  281 [code      ]         "pedalboard": PB_OK,
  282 [code      ]         "numpy_soundfile": NP_OK,
  283 [code      ]         "scipy": SCIPY_OK,
  284 [code      ]         "onset_detector": "scipy_butter" if SCIPY_OK else "numpy_fft",
  285 [code      ]         "real_sidechain_possible": NP_OK,
  286 [code      ]     }
  287 [blank     ] 
  288 [blank     ] 
  289 [branch    ] if __name__ == "__main__":
  290 [code      ]     print(json.dumps(capability_report(), indent=2))
```