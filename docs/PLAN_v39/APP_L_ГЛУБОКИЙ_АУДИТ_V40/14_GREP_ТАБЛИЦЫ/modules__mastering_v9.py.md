# grep-таблицы `modules/mastering_v9.py`

## `import` — 9 совпадений
```
   18 | from __future__ import annotations
   20 | import json
   21 | import math
   22 | from pathlib import Path
   25 |     import numpy as np
   30 |     import soundfile as sf
   37 |     import scipy.signal as sg
   44 |     import matchering as mg
  264 |     import sys
```

## `print` — 2 совпадений
```
  267 |         print("usage: python mastering_v9.py <in.wav> <out_dir>")
  270 |     print(
```

## `except` — 6 совпадений
```
   26 | except Exception:
   33 | except Exception:
   40 | except Exception:
   47 | except Exception:
  140 |     except Exception:
  258 |     except Exception as e:
```

## `try` — 6 совпадений
```
   24 | try:
   29 | try:
   36 | try:
   43 | try:
  113 |     try:
  253 |     try:
```

## `def` — 11 совпадений
```
   52 | def _read(path: str):
   59 | def _write(path: str, y, sr):
   64 | def _rms(y):
   68 | def measure(path: str) -> dict:
   97 | def _apply_gain(y, gain_db: float):
  103 | def _soft_limit(y, ceiling_db: float = -1.0):
  110 | def _eq_shelf(y, sr, freq: float, gain_db: float, kind: str = "low"):
  144 | def _widen_stereo(y, amount: float = 0.3):
  178 | def render_stand(input_wav: str, output_wav: str, stand: str = "streaming") -> dict:
  230 | def render_all_stands(input_wav: str, out_dir: str, artist: str = "") -> dict:
  241 | def match_to_reference(input_wav: str, reference_wav: str, output_wav: str) -> dict:
```

## `return` — 24 совпадений
```
   54 |         return None, None
   56 |     return y, sr
   65 |     return float(np.sqrt(np.mean(np.square(y)) + 1e-12))
   71 |         return {"ok": False, "error": "soundfile/numpy unavailable"}
   74 |         return {"ok": False, "error": "read failed"}
   84 |     return {
   99 |         return y
  100 |     return y * (10 ** (gain_db / 20.0))
  105 |         return y
  107 |     return np.tanh(y / ceil) * ceil
  112 |         return y
  138 |             return out
  139 |         return sg.lfilter(b, a, y)
  141 |         return y
  146 |         return y
  152 |     return out
  181 |         return {"ok": False, "error": "soundfile/numpy required"}
  183 |         return {"ok": False, "error": f"unknown stand: {stand}"}
  187 |         return {"ok": False, "error": f"cannot read {input_wav}"}
  219 |     return {
  237 |     return {"ok": True, "results": results, "dir": str(out_dir), "artist": artist}
  247 |         return {
  257 |         return {"ok": True, "matchering": True, "output": output_wav}
  259 |         return {"ok": False, "error": str(e)}
```

## `if` — 19 совпадений
```
   53 |     if not HAS_SF:
   70 |     if not HAS_SF or np is None:
   73 |     if y is None:
   82 |     if y.shape[1] >= 2:
   98 |     if np is None:
  104 |     if np is None:
  111 |     if not HAS_SP or np is None:
  118 |         if kind == "low":
  134 |         if y.ndim == 2:
  145 |     if np is None or y.ndim != 2 or y.shape[1] < 2:
  180 |     if not HAS_SF or np is None:
  182 |     if stand not in STAND_PRESETS:
  186 |     if y is None:
  205 |         if abs(delta) < 0.5:
  213 |     if peak > ceil:
  243 |     if not HAS_MG:
  244 |         if HAS_SF:
  263 | if __name__ == "__main__":
  266 |     if len(sys.argv) < 3:
```

## `for` — 5 совпадений
```
  136 |             for ch in range(y.shape[1]):
  192 |     for freq, gain, kind in preset["shelves"]:
  201 |     for _ in range(3):
  234 |     for stand in STAND_PRESETS:
  277 |                 for k, v in r["results"].items()
```

## `np` — 7 совпадений
```
   65 |     return float(np.sqrt(np.mean(np.square(y)) + 1e-12))
   75 |     peak = float(np.max(np.abs(y)))
   83 |         corr = float(np.corrcoef(y[:, 0], y[:, 1])[0, 1])
  107 |     return np.tanh(y / ceil) * ceil
  132 |         b = np.array([b0, b1, b2]) / a0
  133 |         a = np.array([a0, a1, a2]) / a0
  211 |     peak = float(np.max(np.abs(y)))
```

## `sf` — 2 совпадений
```
   55 |     y, sr = sf.read(path, always_2d=True)
   61 |     sf.write(path, y, sr)
```
