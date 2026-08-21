# grep-таблицы `tools/ab_compare.py`

## `import` — 12 совпадений
```
   17 | from __future__ import annotations
   19 | import argparse
   20 | import json
   21 | import sys
   22 | from pathlib import Path
   23 | from typing import Any
   26 |     import numpy as np
   27 |     import pyloudnorm as pyln
   28 |     import soundfile as sf
   34 |     import matplotlib
   37 |     import matplotlib.pyplot as plt
   85 |     from numpy.lib.stride_tricks import sliding_window_view
```

## `print` — 2 совпадений
```
   30 |     print(f"[ab_compare] deps missing: {e}", file=sys.stderr)
  221 |     print(
```

## `except` — 4 совпадений
```
   29 | except Exception as e:
   40 | except Exception:
   55 |     except Exception:
  148 |         except Exception:
```

## `try` — 4 совпадений
```
   25 | try:
   33 | try:
   52 |     try:
  136 |         try:
```

## `def` — 8 совпадений
```
   44 | def _load_stereo(path: str):
   51 | def _lufs(data, sr):
   59 | def _true_peak_db(data):
   66 | def _stereo_width(data):
   77 | def _spectrogram(data, sr, out_png: Path, title: str):
  112 | def compare(user_wav: str, ref_wav: str, out_dir: str) -> dict[str, Any]:
  194 | def _verdict(u_l, r_l, u_tp, r_tp, u_w, r_w):
  213 | def main():
```

## `raise` — 1 совпадений
```
   31 |     raise
```

## `return` — 14 совпадений
```
   48 |     return data.astype(np.float32), sr
   54 |         return float(meter.integrated_loudness(data))
   56 |         return None
   62 |         return -120.0
   63 |     return 20.0 * np.log10(peak)
   68 |         return 0.0
   72 |         return 0.0
   74 |     return 1.0 - abs(c)  # ширина = 1 - abs corr
   79 |         return False
   88 |         return False
  109 |     return True
  191 |     return result
  210 |     return notes
  232 |     return 0
```

## `if` — 15 совпадений
```
   46 |     if data.ndim == 1:
   61 |     if peak <= 0:
   67 |     if data.ndim < 2 or data.shape[1] < 2:
   71 |     if np.std(L) < 1e-9 or np.std(R) < 1e-9:
   78 |     if not HAS_PLT:
   87 |     if len(mono) < n_fft:
  135 |     if HAS_PLT:
  140 |                 if path.exists():
  173 |                 if u_lufs is not None and r_lufs is not None
  196 |     if u_l is not None and r_l is not None:
  198 |         if abs(d) < 1.0:
  204 |     if u_tp - r_tp > 0.3:
  206 |     if abs(u_w - r_w) > 0.15:
  208 |     if not notes:
  235 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
  139 |             for ax, path, title in ((axes[0], u_png, "USER"), (axes[1], r_png, "REF")):
```

## `np` — 11 совпадений
```
   47 |         data = np.stack([data, data], axis=1)
   48 |     return data.astype(np.float32), sr
   60 |     peak = float(np.max(np.abs(data))) if data.size else 0.0
   63 |     return 20.0 * np.log10(peak)
   71 |     if np.std(L) < 1e-9 or np.std(R) < 1e-9:
   73 |     c = float(np.corrcoef(L, R)[0, 1])
   89 |     window = np.hanning(n_fft)
   91 |     spec = np.abs(np.fft.rfft(frames * window, axis=1)).T
   92 |     spec_db = 20.0 * np.log10(spec + 1e-9)
  121 |     u_rms = float(np.sqrt(np.mean(u_data**2)))
  122 |     r_rms = float(np.sqrt(np.mean(r_data**2)))
```

## `sf` — 1 совпадений
```
   45 |     data, sr = sf.read(path, always_2d=False)
```
