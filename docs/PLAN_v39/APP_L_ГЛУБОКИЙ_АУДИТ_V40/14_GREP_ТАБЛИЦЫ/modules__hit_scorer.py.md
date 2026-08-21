# grep-таблицы `modules/hit_scorer.py`

## `import` — 10 совпадений
```
   36 | from __future__ import annotations
   38 | import json
   39 | import math
   40 | import time
   41 | from pathlib import Path
   45 |     import numpy as np
   50 |     import librosa
   56 |     import soundfile as sf
   62 |     import pyloudnorm as pyln
  582 |     import sys
```

## `print` — 2 совпадений
```
  585 |         print("usage: python hit_scorer.py <master.wav> [out.json]")
  588 |     print(json.dumps(r, ensure_ascii=False, indent=2))
```

## `except` — 15 совпадений
```
   46 | except Exception:  # pragma: no cover
   52 | except Exception:
   58 | except Exception:
   64 | except ImportError:
  140 |         except Exception:
  159 |     except Exception:
  185 |     except Exception:
  254 |     except Exception:
  282 |         except Exception:
  321 |     except Exception:
  346 |     except Exception:
  362 |     except Exception:
  385 |     except Exception:
  401 |     except Exception:
  510 |     except Exception as e:
```

## `try` — 15 совпадений
```
   44 | try:
   49 | try:
   55 | try:
   61 | try:
  122 |         try:
  142 |     try:
  167 |     try:
  243 |     try:
  268 |         try:
  305 |     try:
  328 |     try:
  353 |     try:
  369 |     try:
  393 |     try:
  508 |     try:
```

## `def` — 19 совпадений
```
   69 | def _load_audio(path: str, sr: int = 22050):
   82 | def _rms(y) -> float:
   88 | def _db(x: float) -> float:
   93 | def _hook_energy(y, sr) -> tuple[float, float]:
  112 | def _hook_repeatability(y, sr) -> tuple[float, int]:
  163 | def _chorus_catchiness(y, sr) -> tuple[float, dict]:
  189 | def _drop_impact(y, sr) -> tuple[float, float]:
  206 | def _tiktok_hookability(y, sr) -> tuple[float, dict]:
  240 | def _bpm_dance_fitness(y, sr) -> tuple[float, float]:
  258 | def _loudness_lufs(y, sr) -> tuple[float, float]:
  301 | def _stereo_width(path: str) -> tuple[float, float]:
  325 | def _low_end_power(y, sr) -> tuple[float, float]:
  350 | def _vocal_presence(y, sr) -> tuple[float, float]:
  366 | def _structure_clarity(y, sr) -> tuple[float, int]:
  389 | def _novelty(y, sr) -> tuple[float, float]:
  422 | def _verdict(score: float) -> str:
  432 | def _actions(metrics: dict) -> list[str]:
  494 | def score_track(master_wav: str, out_json: str | None = None, sr: int = 22050) -> dict:
  515 |     def _add(name, val_tuple, hint=""):
```

## `raise` — 1 совпадений
```
   79 |     raise RuntimeError("Neither librosa nor soundfile available")
```

## `return` — 53 совпадений
```
   73 |         return y, s
   78 |         return y, s
   84 |         return 0.0
   85 |     return float(np.sqrt(np.mean(np.square(y)) + 1e-12))
   89 |     return float(20.0 * math.log10(max(x, 1e-9)))
   96 |         return 50.0, _rms(y)
  103 |         return 50.0, 0.0
  109 |     return score, ratio
  121 |             return 55.0, 0
  130 |                 return 55.0, 0
  139 |             return score, _peaks
  141 |             return 55.0, 0
  154 |                 return 50.0, 0
  158 |         return score, repeats
  160 |         return 50.0, 0
  166 |         return 55.0, {}
  180 |         return score, {
  186 |         return 55.0, {}
  192 |         return 50.0, 0.0
  197 |         return 50.0, 0.0
  203 |     return score, ratio
  209 |         return 40.0, {"start_sec": 0.0, "end_sec": 15.0, "reason": "трек короткий"}
  233 |     return min(100.0, best["score"] + 20.0), {
  242 |         return 60.0, 0.0
  253 |         return score, t
  255 |         return 60.0, 0.0
  265 |         return 60.0, -14.0
  281 |             return score, lufs
  298 |     return score, dbfs
  304 |         return 60.0, 1.0
  308 |             return 30.0, 1.0
  320 |         return score, corr
  322 |         return 60.0, 1.0
  327 |         return 60.0, 0.0
  345 |         return score, ratio
  347 |         return 60.0, 0.0
  352 |         return 60.0, 0.0
  361 |         return score, ratio
  363 |         return 60.0, 0.0
  368 |         return 55.0, 0
  384 |         return score, n
  386 |         return 55.0, 0
  392 |         return 60.0, 0.0
  400 |         return score, combined_var
  402 |         return 60.0, 0.0
  424 |         return "chart_ready"
  426 |         return "solid"
  428 |         return "needs_work"
  429 |     return "flop_risk"
  490 |     return out
  502 |         return {
  511 |         return {"error": f"load failed: {e}", "hit_score": 0.0, "verdict": "flop_risk"}
  577 |     return report
```

## `if` — 43 совпадений
```
   71 |     if HAS_LIBROSA:
   74 |     if HAS_SF:
   76 |         if hasattr(y, "ndim") and y.ndim > 1:
   83 |     if np is None or y is None or len(y) == 0:
   95 |     if np is None or len(y) < sr * 8:
  102 |     if not rms_curve:
  119 |     if not HAS_LIBROSA or len(y) < sr * 20:
  120 |         if np is None or len(y) < sr * 2:
  129 |             if len(rms_curve) < 8:
  136 |                 if ac > 0.5:
  151 |         if off >= ssm.shape[0]:
  153 |             if off >= ssm.shape[0] - 1 or off < 1:
  165 |     if not HAS_LIBROSA:
  191 |     if np is None or len(y) < sr * 8:
  196 |     if len(rms_curve) < 4:
  208 |     if np is None or len(y) < sr * 15:
  219 |         if head_rms > global_med * 0.9 and overall > global_med:
  223 |             if score > best["score"]:
  226 |     if best["score"] == 0.0:
  241 |     if not HAS_LIBROSA:
  250 |             if lo <= t <= hi:
  264 |     if np is None:
  267 |     if HAS_PYLOUDNORM:
  273 |             if -14.0 <= lufs <= -9.0:
  288 |     if -14.0 <= dbfs <= -10.0:
  303 |     if not HAS_SF or np is None:
  307 |         if y.shape[1] < 2:
  312 |         if 0.55 <= corr <= 0.85:
  326 |     if not HAS_LIBROSA:
  337 |         if 0.55 <= ratio <= 1.3:
  351 |     if not HAS_LIBROSA:
  367 |     if not HAS_LIBROSA or len(y) < sr * 30:
  378 |         if 3 <= n <= 8:
  391 |     if not HAS_LIBROSA:
  423 |     if score >= 82.0:
  425 |     if score >= 68.0:
  427 |     if score >= 50.0:
  436 |         if s >= 65.0:
  438 |         if name == "hook_energy":
  501 |     if not p.exists():
  573 |     if out_json:
  581 | if __name__ == "__main__":
  584 |     if len(sys.argv) < 2:
```

## `for` — 5 совпадений
```
  100 |     for i in range(0, len(y) - win, hop):
  134 |             for lag in range(4, min(len(rms_curve) - 1, 32)):
  214 |     for i in range(0, len(y) - win_len, hop):
  249 |         for lo, hi, s in best_ranges:
  434 |     for name, m in metrics.items():
```

## `np` — 20 совпадений
```
   85 |     return float(np.sqrt(np.mean(np.square(y)) + 1e-12))
  125 |             rms_curve = np.array(
  132 |             _norm = float(np.sum(rms_curve * rms_curve)) + 1e-9
  135 |                 ac = float(np.sum(rms_curve[:-lag] * rms_curve[lag:])) / _norm
  144 |         ssm = np.dot(chroma.T, chroma)
  146 |             np.linalg.norm(chroma, axis=0)[:, None]
  147 |             * np.linalg.norm(chroma, axis=0)[None, :]
  155 |         diag = np.diagonal(ssm, offset=off)
  177 |         chroma_var = float(np.mean(np.var(chroma, axis=1)))
  195 |     rms_curve = np.array([_rms(y[i : i + win]) for i in range(0, len(y) - win, hop)])
  198 |     diff = np.diff(rms_curve)
  200 |     baseline = float(np.median(np.abs(diff)))
  229 |         idx = int(np.argmax(rms_c)) if rms_c else 0
  310 |         corr = float(np.corrcoef(l, r)[0, 1])
  329 |         S = np.abs(librosa.stft(y, n_fft=2048))
  354 |         S = np.abs(librosa.stft(y, n_fft=2048))
  375 |         changes = np.where(np.abs(np.diff(rms)) > 1.2)[0]
  394 |         S = np.abs(librosa.stft(y, n_fft=2048))
  395 |         col_var = float(np.mean(np.var(S, axis=1)))
  396 |         row_var = float(np.mean(np.var(S, axis=0)))
```

## `sf` — 2 совпадений
```
   75 |         y, s = sf.read(path, always_2d=False)
  306 |         y, _ = sf.read(path, always_2d=True)
```
