# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/vocal_fx.py`

**Всего строк:** 370

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 187 | 50.5 |
| blank | 52 | 14.1 |
| docstring | 31 | 8.4 |
| branch | 23 | 6.2 |
| return | 21 | 5.7 |
| comment | 16 | 4.3 |
| def | 11 | 3.0 |
| try_block | 10 | 2.7 |
| import | 9 | 2.4 |
| loop | 8 | 2.2 |
| decorator | 1 | 0.3 |
| class | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v18 — modules/vocal_fx.py (vocal double + delay throw, TZ 4.x)
    3 [docstring ] ================================================================================
    4 [blank     ] 
    5 [docstring ] Назначение: дать вокалу «хитовую» плотность БЕЗ нейросетей и платных API —
    6 [docstring ] классический студийный приём double-tracking + delay throw на конце фраз.
    7 [blank     ] 
    8 [docstring ] Два эффекта, оба честные DSP (не имитация):
    9 [blank     ] 
   10 [docstring ]   1) double  — «второй дабл»: вокал слегка растягивается по времени
   11 [docstring ]      (±0.6 %) и детюнится (±8 центов), микшируется тихо под основной.
   12 [docstring ]      Это имитирует живой второй дубль (именно так делают «толстый» хук
   13 [docstring ]      на реальных записях), а НЕ выдаётся за RVC/нейросеть.
   14 [docstring ]   2) throw   — ping-pong delay throw: на конце фразы (по VAD-тишине)
   15 [docstring ]      появляется эхо-бросок, который заполняет паузу перед хуком.
   16 [docstring ]      Даёт драматургию и современное звучание.
   17 [blank     ] 
   18 [docstring ] Честные ограничения:
   19 [docstring ]   — работает только на numpy + soundfile (без scipy/torch/audiocraft);
   20 [docstring ]   — если soundfile недоступен -> ok=False, reason (НЕ молчаливый copy);
   21 [docstring ]   — параметры консервативны, чтобы не превратить вокал в «плывущий» сигнал.
   22 [docstring ] """
   23 [blank     ] 
   24 [import    ] from __future__ import annotations
   25 [blank     ] 
   26 [import    ] import json
   27 [import    ] import math
   28 [import    ] from dataclasses import dataclass
   29 [import    ] from pathlib import Path
   30 [import    ] from typing import Any
   31 [blank     ] 
   32 [try_block ] try:
   33 [import    ]     import numpy as _np
   34 [import    ]     import soundfile as _sf
   35 [blank     ] 
   36 [code      ]     _OK = True
   37 [try_block ] except Exception:
   38 [code      ]     _np = None
   39 [code      ]     _sf = None
   40 [code      ]     _OK = False
   41 [blank     ] 
   42 [blank     ] 
   43 [comment   ] # ---------------------------------------------------------------------------
   44 [comment   ] # helpers
   45 [comment   ] # ---------------------------------------------------------------------------
   46 [blank     ] 
   47 [blank     ] 
   48 [def       ] def _read(wav_path: str) -> tuple[Any, int]:
   49 [code      ]     y, sr = _sf.read(wav_path, always_2d=True)
   50 [return    ]     return y.astype("float32"), int(sr)
   51 [blank     ] 
   52 [blank     ] 
   53 [def       ] def _write(wav_path: str, y, sr: int) -> str:
   54 [code      ]     Path(wav_path).parent.mkdir(parents=True, exist_ok=True)
   55 [code      ]     _sf.write(wav_path, _np.clip(y, -1.0, 1.0), sr)
   56 [return    ]     return wav_path
   57 [blank     ] 
   58 [blank     ] 
   59 [def       ] def _resample_linear(y, factor: float):
   60 [docstring ]     """Честный линейный ресемпл по времени (без scipy).
   61 [blank     ] 
   62 [docstring ]     factor > 1 — сигнал короче/выше; < 1 — длиннее/ниже.
   63 [docstring ]     Используется для микро-растяжения дабла (0.994–1.006), где
   64 [docstring ]     линейная интерполяция не даёт слышимых артефактов.
   65 [docstring ]     """
   66 [code      ]     n = len(y)
   67 [branch    ]     if n < 2:
   68 [return    ]         return y
   69 [code      ]     new_n = max(2, int(round(n / factor)))
   70 [code      ]     x_old = _np.linspace(0.0, 1.0, n)
   71 [code      ]     x_new = _np.linspace(0.0, 1.0, new_n)
   72 [branch    ]     if y.ndim == 1:
   73 [return    ]         return _np.interp(x_new, x_old, y).astype("float32")
   74 [code      ]     out = _np.empty((new_n, y.shape[1]), dtype="float32")
   75 [loop      ]     for c in range(y.shape[1]):
   76 [code      ]         out[:, c] = _np.interp(x_new, x_old, y[:, c])
   77 [return    ]     return out
   78 [blank     ] 
   79 [blank     ] 
   80 [def       ] def _detune_cents(y, sr: int, cents: float):
   81 [docstring ]     """Детюн в центах через ресемпл (честный pitch+time shift)."""
   82 [code      ]     factor = 2.0 ** (cents / 1200.0)
   83 [return    ]     return _resample_linear(y, factor)
   84 [blank     ] 
   85 [blank     ] 
   86 [def       ] def _fit_len(y, n: int):
   87 [branch    ]     if len(y) == n:
   88 [return    ]         return y
   89 [branch    ]     if len(y) > n:
   90 [return    ]         return y[:n]
   91 [code      ]     pad = _np.zeros((n - len(y),) + y.shape[1:], dtype=y.dtype)
   92 [return    ]     return _np.concatenate([y, pad], axis=0)
   93 [blank     ] 
   94 [blank     ] 
   95 [def       ] def _rms_db(x) -> float:
   96 [code      ]     r = float(_np.sqrt(_np.mean(x**2)) + 1e-9)
   97 [return    ]     return 20.0 * math.log10(r)
   98 [blank     ] 
   99 [blank     ] 
  100 [def       ] def _find_phrase_ends(
  101 [code      ]     mono, sr: int, silence_db: float = -40.0, min_silence_ms: int = 180
  102 [code      ] ) -> list[int]:
  103 [docstring ]     """Грубый VAD: ищем концы фраз = начало длинной паузы.
  104 [blank     ] 
  105 [docstring ]     Возвращает список sample-индексов, где фраза заканчивается
  106 [docstring ]     (за ними идёт тишина). На них вешаем delay throw.
  107 [docstring ]     """
  108 [code      ]     frame = max(1, int(sr * 0.02))  # 20 ms окно
  109 [code      ]     hop = frame
  110 [code      ]     n_fr = max(1, len(mono) // hop)
  111 [code      ]     rms = _np.empty(n_fr, dtype="float32")
  112 [loop      ]     for i in range(n_fr):
  113 [code      ]         seg = mono[i * hop : (i + 1) * hop]
  114 [code      ]         rms[i] = float(_np.sqrt(_np.mean(seg**2)) + 1e-9)
  115 [code      ]     thr = 10.0 ** (silence_db / 20.0)
  116 [code      ]     voiced = rms > thr
  117 [code      ]     min_sil_frames = max(1, int(min_silence_ms / 20.0))
  118 [code      ]     ends: list[int] = []
  119 [code      ]     i = 0
  120 [loop      ]     while i < n_fr:
  121 [branch    ]         if voiced[i]:
  122 [comment   ]             # ищем конец voiced-участка
  123 [code      ]             j = i
  124 [loop      ]             while j < n_fr and voiced[j]:
  125 [code      ]                 j += 1
  126 [comment   ]             # j — первый тихий фрейм; если тишина длинная — это конец фразы
  127 [code      ]             k = j
  128 [loop      ]             while k < n_fr and not voiced[k]:
  129 [code      ]                 k += 1
  130 [branch    ]             if (k - j) >= min_sil_frames and j > 0:
  131 [code      ]                 ends.append(j * hop)
  132 [code      ]             i = k
  133 [branch    ]         else:
  134 [code      ]             i += 1
  135 [return    ]     return ends
  136 [blank     ] 
  137 [blank     ] 
  138 [comment   ] # ---------------------------------------------------------------------------
  139 [comment   ] # public API
  140 [comment   ] # ---------------------------------------------------------------------------
  141 [blank     ] 
  142 [blank     ] 
  143 [decorator ] @dataclass
  144 [class     ] class VocalFxResult:
  145 [code      ]     ok: bool
  146 [code      ]     out_wav: str
  147 [code      ]     engine: str
  148 [code      ]     double_used: bool
  149 [code      ]     throw_used: bool
  150 [code      ]     throws_applied: int
  151 [code      ]     in_rms_db: float
  152 [code      ]     out_rms_db: float
  153 [code      ]     reason: str | None = None
  154 [blank     ] 
  155 [blank     ] 
  156 [def       ] def apply_vocal_double(
  157 [code      ]     vocal_wav: str,
  158 [code      ]     out_wav: str,
  159 [code      ]     double_level_db: float = -10.0,
  160 [code      ]     detune_cents: float = 8.0,
  161 [code      ]     time_stretch: float = 0.006,
  162 [code      ]     pre_delay_ms: float = 22.0,
  163 [code      ] ) -> VocalFxResult:
  164 [docstring ]     """Классический double-tracking: детюн+микро-растянутый дабл под основой."""
  165 [branch    ]     if not _OK:
  166 [return    ]         return VocalFxResult(
  167 [code      ]             False,
  168 [code      ]             "",
  169 [code      ]             "none",
  170 [code      ]             False,
  171 [code      ]             False,
  172 [code      ]             0,
  173 [code      ]             -100.0,
  174 [code      ]             -100.0,
  175 [code      ]             reason="numpy/soundfile unavailable",
  176 [code      ]         )
  177 [try_block ]     try:
  178 [code      ]         y, sr = _read(vocal_wav)
  179 [code      ]         n = len(y)
  180 [code      ]         mono = y.mean(axis=1)
  181 [blank     ] 
  182 [comment   ]         # дабл: детюн + лёгкое растяжение -> «второй голос»
  183 [code      ]         dbl = _detune_cents(mono, sr, detune_cents)
  184 [code      ]         dbl = _resample_linear(dbl, 1.0 + time_stretch)
  185 [comment   ]         # pre-delay, чтобы дабл не совпадал покадрово (comb-filter guard)
  186 [code      ]         pd = max(1, int(sr * pre_delay_ms / 1000.0))
  187 [code      ]         dbl = _np.concatenate([_np.zeros(pd, dtype="float32"), dbl])
  188 [code      ]         dbl = _fit_len(dbl, n)
  189 [code      ]         gain = 10.0 ** (double_level_db / 20.0)
  190 [blank     ] 
  191 [code      ]         out = y.copy()
  192 [loop      ]         for c in range(out.shape[1]):
  193 [code      ]             out[:, c] = out[:, c] + dbl * gain
  194 [comment   ]         # нормализация, чтобы не клиппить
  195 [code      ]         peak = float(_np.max(_np.abs(out)) + 1e-9)
  196 [branch    ]         if peak > 1.0:
  197 [code      ]             out = out / peak * 0.98
  198 [blank     ] 
  199 [code      ]         _write(out_wav, out, sr)
  200 [return    ]         return VocalFxResult(
  201 [code      ]             True,
  202 [code      ]             out_wav,
  203 [code      ]             "numpy_double_tracking",
  204 [code      ]             double_used=True,
  205 [code      ]             throw_used=False,
  206 [code      ]             throws_applied=0,
  207 [code      ]             in_rms_db=_rms_db(y),
  208 [code      ]             out_rms_db=_rms_db(out),
  209 [code      ]         )
  210 [try_block ]     except Exception as e:
  211 [return    ]         return VocalFxResult(
  212 [code      ]             False, "", "none", False, False, 0, -100.0, -100.0, reason=str(e)
  213 [code      ]         )
  214 [blank     ] 
  215 [blank     ] 
  216 [def       ] def apply_delay_throw(
  217 [code      ]     vocal_wav: str,
  218 [code      ]     out_wav: str,
  219 [code      ]     delay_ms: float = 320.0,
  220 [code      ]     feedback: float = 0.32,
  221 [code      ]     throw_level_db: float = -9.0,
  222 [code      ]     silence_db: float = -40.0,
  223 [code      ]     ping_pong: bool = True,
  224 [code      ] ) -> VocalFxResult:
  225 [docstring ]     """Delay throw: эхо-бросок в паузах на концах фраз (заполняет воздух)."""
  226 [branch    ]     if not _OK:
  227 [return    ]         return VocalFxResult(
  228 [code      ]             False,
  229 [code      ]             "",
  230 [code      ]             "none",
  231 [code      ]             False,
  232 [code      ]             False,
  233 [code      ]             0,
  234 [code      ]             -100.0,
  235 [code      ]             -100.0,
  236 [code      ]             reason="numpy/soundfile unavailable",
  237 [code      ]         )
  238 [try_block ]     try:
  239 [code      ]         y, sr = _read(vocal_wav)
  240 [code      ]         n = len(y)
  241 [code      ]         mono = y.mean(axis=1)
  242 [code      ]         ends = _find_phrase_ends(mono, sr, silence_db=silence_db)
  243 [code      ]         d = max(1, int(sr * delay_ms / 1000.0))
  244 [code      ]         gain = 10.0 ** (throw_level_db / 20.0)
  245 [blank     ] 
  246 [code      ]         wet = _np.zeros_like(y)
  247 [code      ]         throws = 0
  248 [loop      ]         for e in ends:
  249 [comment   ]             # источник броска — короткий хвост фразы перед паузой
  250 [code      ]             tail_s = max(0, e - int(sr * 0.25))
  251 [code      ]             tail = y[tail_s:e].copy()
  252 [branch    ]             if len(tail) < 16:
  253 [code      ]                 continue
  254 [code      ]             throws += 1
  255 [code      ]             pos = e
  256 [code      ]             level = gain
  257 [code      ]             taps = 0
  258 [loop      ]             while pos < n and level > 0.02 and taps < 5:
  259 [code      ]                 seg = tail * level
  260 [code      ]                 room = min(len(seg), n - pos)
  261 [branch    ]                 if ping_pong and wet.shape[1] >= 2:
  262 [comment   ]                     # ping-pong: чередуем каналы по номеру отражения
  263 [code      ]                     ch = taps % wet.shape[1]
  264 [code      ]                     seg2 = _np.zeros_like(seg)
  265 [code      ]                     seg2[:, ch] = seg[:, ch]
  266 [code      ]                     seg2[:, 1 - ch] = seg[:, 1 - ch] * 0.7
  267 [code      ]                     wet[pos : pos + room] += seg2[:room]
  268 [branch    ]                 else:
  269 [code      ]                     wet[pos : pos + room] += seg[:room]
  270 [code      ]                 pos += d
  271 [code      ]                 level *= feedback
  272 [code      ]                 taps += 1
  273 [blank     ] 
  274 [code      ]         out = y + wet
  275 [code      ]         peak = float(_np.max(_np.abs(out)) + 1e-9)
  276 [branch    ]         if peak > 1.0:
  277 [code      ]             out = out / peak * 0.98
  278 [code      ]         _write(out_wav, out, sr)
  279 [return    ]         return VocalFxResult(
  280 [code      ]             True,
  281 [code      ]             out_wav,
  282 [code      ]             "numpy_delay_throw",
  283 [code      ]             double_used=False,
  284 [code      ]             throw_used=True,
  285 [code      ]             throws_applied=throws,
  286 [code      ]             in_rms_db=_rms_db(y),
  287 [code      ]             out_rms_db=_rms_db(out),
  288 [code      ]         )
  289 [try_block ]     except Exception as e:
  290 [return    ]         return VocalFxResult(
  291 [code      ]             False, "", "none", False, False, 0, -100.0, -100.0, reason=str(e)
  292 [code      ]         )
  293 [blank     ] 
  294 [blank     ] 
  295 [def       ] def process_vocal(
  296 [code      ]     vocal_wav: str,
  297 [code      ]     out_wav: str,
  298 [code      ]     use_double: bool = True,
  299 [code      ]     use_throw: bool = True,
  300 [code      ]     double_level_db: float = -10.0,
  301 [code      ]     throw_level_db: float = -9.0,
  302 [code      ]     delay_ms: float = 320.0,
  303 [code      ] ) -> dict[str, Any]:
  304 [docstring ]     """Единая точка: double -> throw -> out. Возвращает dict-результат."""
  305 [branch    ]     if not _OK:
  306 [return    ]         return {"ok": False, "engine": "none", "reason": "numpy/soundfile unavailable"}
  307 [blank     ] 
  308 [code      ]     cur = vocal_wav
  309 [code      ]     stages: list[str] = []
  310 [code      ]     throws = 0
  311 [code      ]     tmp_double = str(Path(out_wav).with_name("_fx_double_tmp.wav"))
  312 [blank     ] 
  313 [branch    ]     if use_double:
  314 [code      ]         r = apply_vocal_double(cur, tmp_double, double_level_db=double_level_db)
  315 [branch    ]         if r.ok:
  316 [code      ]             cur = tmp_double
  317 [code      ]             stages.append("double")
  318 [blank     ] 
  319 [branch    ]     if use_throw:
  320 [code      ]         r = apply_delay_throw(
  321 [code      ]             cur, out_wav, delay_ms=delay_ms, throw_level_db=throw_level_db
  322 [code      ]         )
  323 [branch    ]         if r.ok:
  324 [code      ]             cur = out_wav
  325 [code      ]             stages.append("throw")
  326 [code      ]             throws = r.throws_applied
  327 [branch    ]         else:
  328 [comment   ]             # throw не критичен — остаёмся на double
  329 [try_block ]             try:
  330 [import    ]                 import shutil
  331 [blank     ] 
  332 [code      ]                 shutil.copy(cur, out_wav)
  333 [code      ]                 cur = out_wav
  334 [try_block ]             except Exception:
  335 [code      ]                 pass
  336 [blank     ] 
  337 [branch    ]     if not stages:
  338 [comment   ]         # оба не сработали — честно сообщаем, не делаем скрытый copy
  339 [return    ]         return {"ok": False, "engine": "none", "reason": "double and throw both failed"}
  340 [blank     ] 
  341 [comment   ]     # подчистить временный файл
  342 [try_block ]     try:
  343 [code      ]         p = Path(tmp_double)
  344 [branch    ]         if p.exists() and cur != tmp_double:
  345 [code      ]             p.unlink()
  346 [try_block ]     except Exception:
  347 [code      ]         pass
  348 [blank     ] 
  349 [return    ]     return {
  350 [code      ]         "ok": True,
  351 [code      ]         "engine": "numpy_vocal_fx",
  352 [code      ]         "path": cur,
  353 [code      ]         "out_wav": cur,
  354 [code      ]         "stages": stages,
  355 [code      ]         "throws_applied": throws,
  356 [code      ]         "double_used": "double" in stages,
  357 [code      ]         "throw_used": "throw" in stages,
  358 [code      ]     }
  359 [blank     ] 
  360 [blank     ] 
  361 [def       ] def capability_report() -> dict[str, Any]:
  362 [return    ]     return {
  363 [code      ]         "numpy_soundfile": _OK,
  364 [code      ]         "real_double_possible": _OK,
  365 [code      ]         "real_throw_possible": _OK,
  366 [code      ]     }
  367 [blank     ] 
  368 [blank     ] 
  369 [branch    ] if __name__ == "__main__":
  370 [code      ]     print(json.dumps(capability_report(), indent=2))
```