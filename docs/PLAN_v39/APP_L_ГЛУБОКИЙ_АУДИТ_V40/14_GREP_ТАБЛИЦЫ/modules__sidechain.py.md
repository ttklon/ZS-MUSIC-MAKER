# grep-таблицы `modules/sidechain.py`

## `import` — 12 совпадений
```
   16 | from __future__ import annotations
   18 | import json
   19 | import math
   20 | from dataclasses import dataclass
   21 | from pathlib import Path
   22 | from typing import Any
   25 |     import pedalboard as _pb  # type: ignore
   33 |     import numpy as _np
   34 |     import soundfile as _sf
   44 |     from scipy.signal import butter as _butter
   45 |     from scipy.signal import sosfilt as _sosfilt
  162 |             import scipy.signal as ss
```

## `print` — 1 совпадений
```
  290 |     print(json.dumps(capability_report(), indent=2))
```

## `except` — 7 совпадений
```
   28 | except Exception:
   37 | except Exception:
   48 | except Exception:
  133 |     except Exception:
  184 |         except Exception:
  220 |     except Exception as e:
  254 |     except Exception:
```

## `try` — 7 совпадений
```
   24 | try:
   32 | try:
   43 | try:
  110 |     try:
  158 |     try:
  180 |         try:
  237 |     try:
```

## `def` — 7 совпадений
```
   67 | def _envelope_from_kick(
   90 | def _bandpass_numpy(kick_y, sr: int, lo_hz: float = 30.0, hi_hz: float = 200.0):
  107 | def _detect_kick_onsets(kick_y, sr: int):
  137 | def _numpy_dsp(
  234 | def measure_ducking_effect(bus_before, bus_after, kick, sr: int) -> float:
  258 | def apply_sidechain(
  279 | def capability_report() -> dict[str, Any]:
```

## `class` — 1 совпадений
```
   55 | class SidechainResult:
```

## `return` — 16 совпадений
```
   71 |         return None
   87 |     return env
   99 |         return kick_y
  104 |     return _np.fft.irfft(spec, n=n).astype("float32")
  109 |         return []
  132 |         return onsets
  134 |         return []
  147 |         return SidechainResult(
  210 |         return SidechainResult(
  221 |         return SidechainResult(
  236 |         return 0.0
  240 |             return 0.0
  253 |         return float(_np.mean(deltas)) if deltas else 0.0
  255 |         return 0.0
  276 |     return r.__dict__
  280 |     return {
```

## `if` — 16 совпадений
```
   70 |     if _np is None:
   74 |     if w > 1:
   82 |         if x[i] > y:
   98 |     if n < 4:
  108 |     if _np is None:
  111 |         if SCIPY_OK:
  120 |         if w > 1:
  128 |             if env[i] > thr and env[i] > env[i - 1] and env[i] >= env[i + 1]:
  129 |                 if i - last > min_gap:
  146 |     if not NP_OK:
  161 |         if sr_k != sr_b:
  174 |         if _np.ndim(kick) > 1:
  235 |     if _np is None:
  239 |         if not onsets:
  248 |             if e - s < 10:
  289 | if __name__ == "__main__":
```

## `for` — 4 совпадений
```
   81 |     for i in range(len(x)):
  127 |         for i in range(1, len(env) - 1):
  198 |         for c in range(bus.shape[1]):
  245 |         for o in onsets:
```
