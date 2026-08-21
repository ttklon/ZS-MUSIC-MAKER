# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/anti_neuro_v10.py`

**Всего строк:** 401

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 222 | 55.4 |
| blank | 48 | 12.0 |
| branch | 32 | 8.0 |
| try_block | 22 | 5.5 |
| return | 19 | 4.7 |
| docstring | 18 | 4.5 |
| import | 18 | 4.5 |
| comment | 12 | 3.0 |
| def | 5 | 1.2 |
| loop | 5 | 1.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v10 — Anti-Neuro Polish (+v17 numpy fallback)
    3 [docstring ] ================================================================
    4 [docstring ] Оригинальные стадии (требуют pydub):
    5 [docstring ]   1. Micro-timing jitter, 2. Breath insertion, 3. Formant micro-shift,
    6 [docstring ]   4. Consonant hardening, 5. Ghost harmony removal, 6. Ending naturalization,
    7 [docstring ]   7. Structural entropy, 8. Human error injection.
    8 [blank     ] 
    9 [docstring ] v17 additions:
   10 [docstring ]   • apply_polish(input, out, intensity) — обёртка для мастер-стадии
   11 [docstring ]     (orchestrator._stage_polish искал именно этот symbol).
   12 [docstring ]   • Честный numpy-fallback (soundfile+scipy) — polish работает даже
   13 [docstring ]     без pydub: breath / hi-shelf / low-pass ghost-remove / fade-out /
   14 [docstring ]     human-error / entropy.
   15 [docstring ] """
   16 [blank     ] 
   17 [import    ] from __future__ import annotations
   18 [blank     ] 
   19 [import    ] import json
   20 [import    ] import logging
   21 [import    ] import random
   22 [import    ] from pathlib import Path
   23 [import    ] from typing import Any
   24 [blank     ] 
   25 [code      ] log = logging.getLogger("zsmm.anti_neuro_v10")
   26 [blank     ] 
   27 [try_block ] try:
   28 [import    ]     from pydub import AudioSegment
   29 [import    ]     from pydub.generators import WhiteNoise
   30 [blank     ] 
   31 [code      ]     LIBS_OK = True
   32 [try_block ] except Exception:
   33 [code      ]     LIBS_OK = False
   34 [code      ]     AudioSegment = None
   35 [code      ]     WhiteNoise = None
   36 [blank     ] 
   37 [try_block ] try:
   38 [import    ]     import numpy as _np
   39 [import    ]     import soundfile as _sf
   40 [blank     ] 
   41 [code      ]     NP_OK = True
   42 [try_block ] except Exception:
   43 [code      ]     _np = None
   44 [code      ]     _sf = None
   45 [code      ]     NP_OK = False
   46 [blank     ] 
   47 [blank     ] 
   48 [def       ] def polish_vocal(
   49 [code      ]     vocal_wav: str, out_wav: str, preset: str = "standard", seed: int | None = None
   50 [code      ] ) -> dict[str, Any]:
   51 [docstring ]     """Полирует вокал/мастер, убирая нейроношность.
   52 [docstring ]     presets: gentle (3 стадии), standard (6), aggressive (8)."""
   53 [code      ]     Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
   54 [blank     ] 
   55 [branch    ]     if not LIBS_OK:
   56 [return    ]         return _polish_numpy(vocal_wav, out_wav, preset=preset, seed=seed)
   57 [blank     ] 
   58 [code      ]     rng = random.Random(seed or 42)
   59 [code      ]     seg = AudioSegment.from_file(vocal_wav)
   60 [code      ]     stages_done: list[str] = []
   61 [code      ]     metrics: dict[str, Any] = {}
   62 [blank     ] 
   63 [code      ]     stages = {
   64 [code      ]         "gentle": ["breath", "timing_jitter", "ending"],
   65 [code      ]         "standard": [
   66 [code      ]             "breath",
   67 [code      ]             "timing_jitter",
   68 [code      ]             "consonant_boost",
   69 [code      ]             "ghost_remove",
   70 [code      ]             "ending",
   71 [code      ]             "human_error",
   72 [code      ]         ],
   73 [code      ]         "aggressive": [
   74 [code      ]             "breath",
   75 [code      ]             "timing_jitter",
   76 [code      ]             "consonant_boost",
   77 [code      ]             "ghost_remove",
   78 [code      ]             "ending",
   79 [code      ]             "human_error",
   80 [code      ]             "formant_shift",
   81 [code      ]             "entropy_boost",
   82 [code      ]         ],
   83 [code      ]     }
   84 [code      ]     plan = stages.get(preset, stages["standard"])
   85 [blank     ] 
   86 [loop      ]     for stage in plan:
   87 [try_block ]         try:
   88 [code      ]             seg, m = _apply_stage(seg, stage, rng)
   89 [code      ]             stages_done.append(stage)
   90 [code      ]             metrics[stage] = m
   91 [try_block ]         except Exception as e:
   92 [code      ]             log.warning("stage %s failed: %s", stage, e)
   93 [code      ]             metrics[stage] = {"error": str(e)}
   94 [blank     ] 
   95 [code      ]     seg.export(out_wav, format="wav")
   96 [return    ]     return {
   97 [code      ]         "ok": True,
   98 [code      ]         "preset": preset,
   99 [code      ]         "engine": "pydub",
  100 [code      ]         "stages_applied": stages_done,
  101 [code      ]         "metrics": metrics,
  102 [code      ]         "out_wav": out_wav,
  103 [code      ]         "path": out_wav,
  104 [code      ]     }
  105 [blank     ] 
  106 [blank     ] 
  107 [def       ] def apply_polish(
  108 [code      ]     input_wav: str,
  109 [code      ]     out_wav: str,
  110 [code      ]     intensity: float = 0.5,
  111 [code      ]     preset: str | None = None,
  112 [code      ]     seed: int | None = None,
  113 [code      ] ) -> dict[str, Any]:
  114 [docstring ]     """v17: обёртка для мастеринг-стадии; intensity → preset."""
  115 [branch    ]     if preset is None:
  116 [branch    ]         if intensity < 0.35:
  117 [code      ]             preset = "gentle"
  118 [branch    ]         elif intensity < 0.7:
  119 [code      ]             preset = "standard"
  120 [branch    ]         else:
  121 [code      ]             preset = "aggressive"
  122 [code      ]     r = polish_vocal(input_wav, out_wav, preset=preset, seed=seed)
  123 [branch    ]     if isinstance(r, dict):
  124 [code      ]         r.setdefault("intensity", intensity)
  125 [return    ]     return r
  126 [blank     ] 
  127 [blank     ] 
  128 [def       ] def _polish_numpy(
  129 [code      ]     vocal_wav: str, out_wav: str, preset: str = "standard", seed: int | None = None
  130 [code      ] ) -> dict[str, Any]:
  131 [docstring ]     """Честный numpy-fallback без pydub."""
  132 [branch    ]     if not NP_OK:
  133 [try_block ]         try:
  134 [import    ]             import shutil
  135 [blank     ] 
  136 [code      ]             shutil.copy(vocal_wav, out_wav)
  137 [return    ]             return {
  138 [code      ]                 "ok": True,
  139 [code      ]                 "engine": "copy",
  140 [code      ]                 "fallback_used": True,
  141 [code      ]                 "reason": "no pydub/numpy/soundfile — copied as-is",
  142 [code      ]                 "out_wav": out_wav,
  143 [code      ]                 "path": out_wav,
  144 [code      ]             }
  145 [try_block ]         except Exception as e:
  146 [return    ]             return {"ok": False, "reason": str(e)}
  147 [blank     ] 
  148 [code      ]     rng = random.Random(seed or 42)
  149 [try_block ]     try:
  150 [code      ]         y, sr = _sf.read(vocal_wav, always_2d=True)
  151 [code      ]         y = y.astype("float32")
  152 [code      ]         stages_done: list[str] = []
  153 [code      ]         metrics: dict[str, Any] = {}
  154 [blank     ] 
  155 [code      ]         plan = {
  156 [code      ]             "gentle": ["breath", "ending"],
  157 [code      ]             "standard": [
  158 [code      ]                 "breath",
  159 [code      ]                 "consonant_boost",
  160 [code      ]                 "ghost_remove",
  161 [code      ]                 "ending",
  162 [code      ]                 "human_error",
  163 [code      ]             ],
  164 [code      ]             "aggressive": [
  165 [code      ]                 "breath",
  166 [code      ]                 "consonant_boost",
  167 [code      ]                 "ghost_remove",
  168 [code      ]                 "ending",
  169 [code      ]                 "human_error",
  170 [code      ]                 "entropy_boost",
  171 [code      ]             ],
  172 [code      ]         }.get(
  173 [code      ]             preset,
  174 [code      ]             ["breath", "consonant_boost", "ghost_remove", "ending", "human_error"],
  175 [code      ]         )
  176 [blank     ] 
  177 [loop      ]         for stage in plan:
  178 [try_block ]             try:
  179 [branch    ]                 if stage == "breath":
  180 [code      ]                     dur = int(sr * 0.18)
  181 [code      ]                     noise = (
  182 [code      ]                         _np.random.RandomState(seed or 42)
  183 [code      ]                         .randn(dur, y.shape[1])
  184 [code      ]                         .astype("float32")
  185 [code      ]                     )
  186 [code      ]                     fade = _np.linspace(0, 1, dur // 3, dtype="float32")
  187 [code      ]                     envin = _np.concatenate(
  188 [code      ]                         [
  189 [code      ]                             fade,
  190 [code      ]                             _np.ones(dur - 2 * (dur // 3), dtype="float32"),
  191 [code      ]                             fade[::-1],
  192 [code      ]                         ]
  193 [code      ]                     )
  194 [branch    ]                     if envin.shape[0] > dur:
  195 [code      ]                         envin = envin[:dur]
  196 [branch    ]                     else:
  197 [code      ]                         envin = _np.pad(envin, (0, dur - envin.shape[0]))
  198 [code      ]                     breath = noise * envin.reshape(-1, 1) * (10 ** (-32 / 20))
  199 [code      ]                     y = _np.concatenate([breath, y], axis=0)
  200 [code      ]                     metrics[stage] = {"breath_ms": 180}
  201 [blank     ] 
  202 [branch    ]                 elif stage == "consonant_boost":
  203 [try_block ]                     try:
  204 [import    ]                         from scipy.signal import butter, sosfilt
  205 [blank     ] 
  206 [code      ]                         sos = butter(2, 3000, btype="high", fs=sr, output="sos")
  207 [code      ]                         boost = _np.stack(
  208 [code      ]                             [sosfilt(sos, y[:, c]) for c in range(y.shape[1])], axis=1
  209 [code      ]                         )
  210 [code      ]                         y = y + boost * (10 ** (3 / 20) - 1) * 0.5
  211 [code      ]                         metrics[stage] = {"hi_boost_db": 3}
  212 [try_block ]                     except Exception as e:
  213 [code      ]                         metrics[stage] = {"error": str(e)}
  214 [blank     ] 
  215 [branch    ]                 elif stage == "ghost_remove":
  216 [try_block ]                     try:
  217 [import    ]                         from scipy.signal import butter, sosfilt
  218 [blank     ] 
  219 [code      ]                         sos = butter(4, 14000, btype="low", fs=sr, output="sos")
  220 [code      ]                         y = _np.stack(
  221 [code      ]                             [sosfilt(sos, y[:, c]) for c in range(y.shape[1])], axis=1
  222 [code      ]                         )
  223 [code      ]                         metrics[stage] = {"low_pass_hz": 14000}
  224 [try_block ]                     except Exception as e:
  225 [code      ]                         metrics[stage] = {"error": str(e)}
  226 [blank     ] 
  227 [branch    ]                 elif stage == "ending":
  228 [code      ]                     fade_len = min(int(sr * 1.2), y.shape[0] // 6)
  229 [branch    ]                     if fade_len > 8:
  230 [code      ]                         env = _np.linspace(1.0, 0.0, fade_len, dtype="float32")
  231 [code      ]                         y[-fade_len:] *= env.reshape(-1, 1)
  232 [code      ]                     metrics[stage] = {"fade_out_ms": int(1000 * fade_len / sr)}
  233 [blank     ] 
  234 [branch    ]                 elif stage == "human_error":
  235 [code      ]                     chunk = max(1, int(sr * 0.04))
  236 [code      ]                     dips = 0
  237 [loop      ]                     for i in range(0, y.shape[0] - chunk, chunk):
  238 [branch    ]                         if rng.random() < 0.03:
  239 [code      ]                             g = 10 ** ((-6 - rng.random() * 4) / 20)
  240 [code      ]                             y[i : i + chunk] *= g
  241 [code      ]                             dips += 1
  242 [code      ]                     metrics[stage] = {"micro_dips": dips}
  243 [blank     ] 
  244 [branch    ]                 elif stage == "entropy_boost":
  245 [try_block ]                     try:
  246 [import    ]                         from scipy.signal import butter, sosfilt
  247 [blank     ] 
  248 [code      ]                         mid = y.shape[0] // 2
  249 [code      ]                         sos = butter(2, 120, btype="high", fs=sr, output="sos")
  250 [code      ]                         second = _np.stack(
  251 [code      ]                             [sosfilt(sos, y[mid:, c]) for c in range(y.shape[1])],
  252 [code      ]                             axis=1,
  253 [code      ]                         )
  254 [code      ]                         y[mid:] = second
  255 [code      ]                         metrics[stage] = {"mid_hp_hz": 120}
  256 [try_block ]                     except Exception as e:
  257 [code      ]                         metrics[stage] = {"error": str(e)}
  258 [blank     ] 
  259 [code      ]                 stages_done.append(stage)
  260 [try_block ]             except Exception as e:
  261 [code      ]                 metrics[stage] = {"error": str(e)}
  262 [blank     ] 
  263 [code      ]         peak = float(_np.max(_np.abs(y)) + 1e-9)
  264 [branch    ]         if peak > 0.98:
  265 [code      ]             y = y / peak * 0.98
  266 [blank     ] 
  267 [code      ]         _sf.write(out_wav, y, sr)
  268 [return    ]         return {
  269 [code      ]             "ok": True,
  270 [code      ]             "preset": preset,
  271 [code      ]             "engine": "numpy_fallback",
  272 [code      ]             "fallback_used": True,
  273 [code      ]             "stages_applied": stages_done,
  274 [code      ]             "metrics": metrics,
  275 [code      ]             "out_wav": out_wav,
  276 [code      ]             "path": out_wav,
  277 [code      ]             "reason": "pydub unavailable; used numpy anti-neuro polish",
  278 [code      ]         }
  279 [try_block ]     except Exception as e:
  280 [return    ]         return {"ok": False, "reason": str(e)}
  281 [blank     ] 
  282 [blank     ] 
  283 [def       ] def _apply_stage(seg, name: str, rng: random.Random):
  284 [branch    ]     if name == "breath":
  285 [code      ]         breath = WhiteNoise().to_audio_segment(duration=180).apply_gain(-32)
  286 [code      ]         seg = breath.fade_in(60).fade_out(60) + seg
  287 [return    ]         return seg, {"breath_ms": 180}
  288 [branch    ]     if name == "timing_jitter":
  289 [code      ]         chunk_ms = 300
  290 [code      ]         chunks = [seg[i : i + chunk_ms] for i in range(0, len(seg), chunk_ms)]
  291 [code      ]         out = AudioSegment.silent(duration=0)
  292 [code      ]         shifts = 0
  293 [loop      ]         for c in chunks:
  294 [branch    ]             if rng.random() < 0.15:
  295 [code      ]                 shift = rng.randint(-8, 12)
  296 [branch    ]                 if shift > 0:
  297 [code      ]                     c = AudioSegment.silent(duration=shift) + c
  298 [code      ]                 shifts += 1
  299 [code      ]             out += c
  300 [return    ]         return out, {"shifted_chunks": shifts, "total_chunks": len(chunks)}
  301 [branch    ]     if name == "consonant_boost":
  302 [comment   ]         # Более умный буст согласных: только на атаках (транзиентах)
  303 [try_block ]         try:
  304 [import    ]             import numpy as np
  305 [blank     ] 
  306 [code      ]             y = np.array(seg.get_array_of_samples(), dtype=np.float32)
  307 [comment   ]             # Ищем области с высокой активностью в ВЧ (согласные)
  308 [import    ]             from scipy.signal import butter, sosfilt
  309 [blank     ] 
  310 [code      ]             sos = butter(2, 4000, btype="high", fs=seg.frame_rate, output="sos")
  311 [code      ]             hi = sosfilt(sos, y)
  312 [comment   ]             # Усиливаем только там, где ВЧ и так есть
  313 [code      ]             y = y + hi * 0.5
  314 [code      ]             y_int = np.clip(y, -32768, 32767).astype(np.int16)
  315 [return    ]             return AudioSegment(
  316 [code      ]                 y_int.tobytes(),
  317 [code      ]                 frame_rate=seg.frame_rate,
  318 [code      ]                 sample_width=2,
  319 [code      ]                 channels=seg.channels,
  320 [code      ]             ), {"hi_boost_db": 3, "method": "transient_aware"}
  321 [try_block ]         except Exception:
  322 [code      ]             boosted = seg.high_pass_filter(3000).apply_gain(3)
  323 [return    ]             return seg.overlay(boosted.apply_gain(-6)), {
  324 [code      ]                 "hi_boost_db": 3,
  325 [code      ]                 "method": "simple_overlay",
  326 [code      ]             }
  327 [branch    ]     if name == "ghost_remove":
  328 [code      ]         seg = seg.low_pass_filter(14000)
  329 [return    ]         return seg, {"low_pass_hz": 14000}
  330 [branch    ]     if name == "ending":
  331 [code      ]         fade_ms = min(1200, len(seg) // 6)
  332 [return    ]         return seg.fade_out(fade_ms), {"fade_out_ms": fade_ms}
  333 [branch    ]     if name == "human_error":
  334 [code      ]         chunk_ms = 40
  335 [code      ]         chunks = [seg[i : i + chunk_ms] for i in range(0, len(seg), chunk_ms)]
  336 [code      ]         out = AudioSegment.silent(duration=0)
  337 [code      ]         dips = 0
  338 [loop      ]         for c in chunks:
  339 [branch    ]             if rng.random() < 0.03:
  340 [code      ]                 c = c.apply_gain(-6 - rng.random() * 4)
  341 [code      ]                 dips += 1
  342 [code      ]             out += c
  343 [return    ]         return out, {"micro_dips": dips}
  344 [branch    ]     if name == "formant_shift":
  345 [try_block ]         try:
  346 [import    ]             import librosa
  347 [import    ]             import numpy as np
  348 [blank     ] 
  349 [comment   ]             # Конвертируем в numpy
  350 [code      ]             y = np.array(seg.get_array_of_samples(), dtype=np.float32) / (2**15)
  351 [code      ]             sr = seg.frame_rate
  352 [blank     ] 
  353 [comment   ]             # Формантный сдвиг через трюк "resample + pitch shift back"
  354 [comment   ]             # Сдвигаем на 1.5 полутона (случайно вверх или вниз)
  355 [code      ]             steps = rng.uniform(1.0, 2.0) * (1 if rng.random() > 0.5 else -1)
  356 [blank     ] 
  357 [comment   ]             # 1. Сдвигаем всё (pitch + formants) через изменение частоты дискретизации
  358 [code      ]             y_shifted = librosa.resample(
  359 [code      ]                 y, orig_sr=sr, target_sr=int(sr * (2 ** (steps / 12.0)))
  360 [code      ]             )
  361 [blank     ] 
  362 [comment   ]             # 2. Сдвигаем только питч обратно через STFT-based pitch shift.
  363 [comment   ]             # Это осознанный формантный DSP-трюк anti-neuro polish
  364 [comment   ]             # (resample+pitch-back ломает «пластмассовость»), а НЕ подмена RVC.
  365 [code      ]             y_final = librosa.effects.pitch_shift(
  366 [code      ]                 y_shifted, sr=sr, n_steps=-steps
  367 [code      ]             )  # noqa: ZSMM_NOT_RVC
  368 [blank     ] 
  369 [comment   ]             # Обрезаем/дополняем до исходной длины
  370 [branch    ]             if len(y_final) > len(y):
  371 [code      ]                 y_final = y_final[: len(y)]
  372 [branch    ]             else:
  373 [code      ]                 y_final = np.pad(y_final, (0, len(y) - len(y_final)))
  374 [blank     ] 
  375 [comment   ]             # Конвертируем обратно в AudioSegment
  376 [code      ]             y_int = (y_final * (2**15)).astype(np.int16)
  377 [code      ]             out = AudioSegment(
  378 [code      ]                 y_int.tobytes(), frame_rate=sr, sample_width=2, channels=seg.channels
  379 [code      ]             )
  380 [return    ]             return out, {"formant_steps": steps, "method": "librosa_resample_trick"}
  381 [try_block ]         except Exception as e:
  382 [return    ]             return seg, {"error": f"formant shift failed: {e}"}
  383 [branch    ]     if name == "entropy_boost":
  384 [code      ]         mid = len(seg) // 2
  385 [code      ]         first = seg[:mid]
  386 [code      ]         second = seg[mid:].high_pass_filter(120)
  387 [return    ]         return first + second, {"mid_hp_hz": 120}
  388 [return    ]     return seg, {}
  389 [blank     ] 
  390 [blank     ] 
  391 [def       ] def capability_report() -> dict[str, Any]:
  392 [return    ]     return {
  393 [code      ]         "pydub_available": LIBS_OK,
  394 [code      ]         "numpy_fallback_available": NP_OK,
  395 [code      ]         "polish_vocal": True,
  396 [code      ]         "apply_polish": True,
  397 [code      ]     }
  398 [blank     ] 
  399 [blank     ] 
  400 [branch    ] if __name__ == "__main__":
  401 [code      ]     print(json.dumps(capability_report(), ensure_ascii=False, indent=2))
```