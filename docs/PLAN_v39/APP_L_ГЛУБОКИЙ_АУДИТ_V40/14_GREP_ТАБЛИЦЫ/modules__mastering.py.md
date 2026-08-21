# grep-таблицы `modules/mastering.py`

## `import` — 8 совпадений
```
   25 | from __future__ import annotations
   27 | import os
   28 | from pathlib import Path
   29 | from typing import Any
   31 | import numpy as np
   32 | import soundfile as sf
   35 |     import pyloudnorm as pyln  # type: ignore
  205 |     import sys
```

## `print` — 2 совпадений
```
  208 |         print(master_all_stands(sys.argv[1], sys.argv[2]))
  210 |         print("usage: python -m modules.mastering <mix.wav> <out_dir>")
```

## `except` — 4 совпадений
```
   38 | except Exception:  # pragma: no cover
  114 |         except Exception:
  149 |     except Exception as e:
  164 |     except Exception as e:
```

## `try` — 4 совпадений
```
   34 | try:  # опционально: точный LUFS по ITU-BS.1770
  110 |         try:
  147 |     try:
  153 |     try:
```

## `def` — 8 совпадений
```
   57 | def _one_pole_shelf(y: np.ndarray, sr: int, cutoff: float, gain_db: float,
   83 | def _apply_stand_eq(y: np.ndarray, sr: int, stand: str) -> np.ndarray:
  101 | def _loudness_dbfs(y: np.ndarray) -> float:
  106 | def _loudness_lufs(y: np.ndarray, sr: int) -> float:
  119 | def _tanh_limit(y: np.ndarray, drive: float = 1.0, ceiling: float = 0.98) -> np.ndarray:
  124 | def _try_numpy_dsp(y: np.ndarray, sr: int, stand: str) -> tuple[np.ndarray, dict]:
  145 | def master_one(mix_wav: str, out_wav: str, stand: str = "streaming") -> dict[str, Any]:
  168 | def master_all_stands(
```

## `return` — 11 совпадений
```
   80 |     return out[:, 0] if squeeze else out
   98 |     return y
  103 |     return 20.0 * np.log10(max(rms, 1e-12))
  113 |             return float(meter.integrated_loudness(mono))
  116 |     return _loudness_dbfs(y) - 3.0
  121 |     return np.tanh(y * drive) / np.tanh(drive) * ceiling
  142 |     return y, info
  150 |         return {"ok": False, "reason": f"read failed: {type(e).__name__}: {e}"}
  157 |         return {
  165 |         return {"ok": False, "reason": f"dsp failed: {type(e).__name__}: {e}"}
  191 |     return {
```

## `if` — 9 совпадений
```
   63 |     if y.ndim == 1:
   76 |     if band == "low":
   96 |         if abs(gdb) > 1e-6:
  109 |     if _HAS_PYLN:
  151 |     if y.shape[1] < 2:  # если вошло моно — делаем dual-mono стерео
  185 |         if r.get("ok"):
  187 |             if r.get("fallback_used"):
  204 | if __name__ == "__main__":  # быстрый self-check
  207 |     if len(sys.argv) > 2:
```

## `for` — 4 совпадений
```
   72 |     for n in range(len(y)):
   95 |     for cutoff, gdb, band in eq.get(stand, eq["streaming"]):
  134 |     for _ in range(3):
  182 |     for stand in stands:
```

## `np` — 15 совпадений
```
   57 | def _one_pole_shelf(y: np.ndarray, sr: int, cutoff: float, gain_db: float,
   58 |                     band: str) -> np.ndarray:
   60 |     rc = 1.0 / (2.0 * np.pi * cutoff)
   70 |     low = np.zeros_like(y)
   71 |     prev = np.zeros(y.shape[1], dtype=np.float64)
   83 | def _apply_stand_eq(y: np.ndarray, sr: int, stand: str) -> np.ndarray:
  101 | def _loudness_dbfs(y: np.ndarray) -> float:
  102 |     rms = float(np.sqrt(np.mean(y**2)) + 1e-12)
  103 |     return 20.0 * np.log10(max(rms, 1e-12))
  106 | def _loudness_lufs(y: np.ndarray, sr: int) -> float:
  119 | def _tanh_limit(y: np.ndarray, drive: float = 1.0, ceiling: float = 0.98) -> np.ndarray:
  121 |     return np.tanh(y * drive) / np.tanh(drive) * ceiling
  124 | def _try_numpy_dsp(y: np.ndarray, sr: int, stand: str) -> tuple[np.ndarray, dict]:
  152 |         y = np.repeat(y, 2, axis=1)
  156 |         sf.write(out_wav, y2.astype(np.float32), sr)
```

## `sf` — 2 совпадений
```
  148 |         y, sr = sf.read(mix_wav, always_2d=True)  # (N, C) — стерео сохраняется
  156 |         sf.write(out_wav, y2.astype(np.float32), sr)
```
