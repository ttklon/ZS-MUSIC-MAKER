# grep-таблицы `modules/vocal_fx.py`

## `import` — 9 совпадений
```
   24 | from __future__ import annotations
   26 | import json
   27 | import math
   28 | from dataclasses import dataclass
   29 | from pathlib import Path
   30 | from typing import Any
   33 |     import numpy as _np
   34 |     import soundfile as _sf
  330 |                 import shutil
```

## `print` — 1 совпадений
```
  370 |     print(json.dumps(capability_report(), indent=2))
```

## `except` — 5 совпадений
```
   37 | except Exception:
  210 |     except Exception as e:
  289 |     except Exception as e:
  334 |             except Exception:
  346 |     except Exception:
```

## `try` — 5 совпадений
```
   32 | try:
  177 |     try:
  238 |     try:
  329 |             try:
  342 |     try:
```

## `def` — 11 совпадений
```
   48 | def _read(wav_path: str) -> tuple[Any, int]:
   53 | def _write(wav_path: str, y, sr: int) -> str:
   59 | def _resample_linear(y, factor: float):
   80 | def _detune_cents(y, sr: int, cents: float):
   86 | def _fit_len(y, n: int):
   95 | def _rms_db(x) -> float:
  100 | def _find_phrase_ends(
  156 | def apply_vocal_double(
  216 | def apply_delay_throw(
  295 | def process_vocal(
  361 | def capability_report() -> dict[str, Any]:
```

## `class` — 1 совпадений
```
  144 | class VocalFxResult:
```

## `return` — 21 совпадений
```
   50 |     return y.astype("float32"), int(sr)
   56 |     return wav_path
   68 |         return y
   73 |         return _np.interp(x_new, x_old, y).astype("float32")
   77 |     return out
   83 |     return _resample_linear(y, factor)
   88 |         return y
   90 |         return y[:n]
   92 |     return _np.concatenate([y, pad], axis=0)
   97 |     return 20.0 * math.log10(r)
  135 |     return ends
  166 |         return VocalFxResult(
  200 |         return VocalFxResult(
  211 |         return VocalFxResult(
  227 |         return VocalFxResult(
  279 |         return VocalFxResult(
  290 |         return VocalFxResult(
  306 |         return {"ok": False, "engine": "none", "reason": "numpy/soundfile unavailable"}
  339 |         return {"ok": False, "engine": "none", "reason": "double and throw both failed"}
  349 |     return {
  362 |     return {
```

## `if` — 20 совпадений
```
   67 |     if n < 2:
   72 |     if y.ndim == 1:
   87 |     if len(y) == n:
   89 |     if len(y) > n:
  121 |         if voiced[i]:
  130 |             if (k - j) >= min_sil_frames and j > 0:
  165 |     if not _OK:
  196 |         if peak > 1.0:
  226 |     if not _OK:
  252 |             if len(tail) < 16:
  261 |                 if ping_pong and wet.shape[1] >= 2:
  276 |         if peak > 1.0:
  305 |     if not _OK:
  313 |     if use_double:
  315 |         if r.ok:
  319 |     if use_throw:
  323 |         if r.ok:
  337 |     if not stages:
  344 |         if p.exists() and cur != tmp_double:
  369 | if __name__ == "__main__":
```

## `for` — 4 совпадений
```
   75 |     for c in range(y.shape[1]):
  112 |     for i in range(n_fr):
  192 |         for c in range(out.shape[1]):
  248 |         for e in ends:
```

## `while` — 4 совпадений
```
  120 |     while i < n_fr:
  124 |             while j < n_fr and voiced[j]:
  128 |             while k < n_fr and not voiced[k]:
  258 |             while pos < n and level > 0.02 and taps < 5:
```
