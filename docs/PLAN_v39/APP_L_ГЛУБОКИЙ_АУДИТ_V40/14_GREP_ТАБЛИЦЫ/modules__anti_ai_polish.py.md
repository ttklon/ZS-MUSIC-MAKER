# grep-таблицы `modules/anti_ai_polish.py`

## `import` — 12 совпадений
```
   23 | from __future__ import annotations
   25 | import math
   26 | import random
   27 | import time
   28 | from pathlib import Path
   31 |     import numpy as np
   36 |     import soundfile as sf
  134 |         import scipy.signal as sg
  186 |         from scipy.interpolate import interp1d
  220 |         import scipy.signal as sg
  305 |     import sys
  315 |     import json
```

## `print` — 2 совпадений
```
  308 |         print("usage: python anti_ai_polish.py <in.wav> <out.wav> [preset]")
  317 |     print(json.dumps(r, ensure_ascii=False, indent=2))
```

## `except` — 5 совпадений
```
   32 | except Exception:
   39 | except Exception:
  135 |     except Exception:
  187 |     except Exception:
  221 |     except Exception:
```

## `try` — 5 совпадений
```
   30 | try:
   35 | try:
  133 |     try:
  185 |     try:
  219 |     try:
```

## `def` — 11 совпадений
```
   44 | def _read(path: str):
   51 | def _write(path: str, y, sr):
   57 | def _micro_timing_jitter(y, sr, amount_ms: float = 5.0, seed: int | None = None):
   80 | def _breath_insert(
  104 | def _section_dynamics_variation(y, sr, sections: list, seed: int | None = None):
  126 | def _ghost_harmonies_kill(y, sr):
  151 | def _formulaic_structure_bust(y, sr, seed: int | None = None):
  172 | def _tape_saturation(y, amount: float = 0.06):
  179 | def _imperfect_tuning(y, sr, cents: float = 4.0):
  216 | def _lofi_pass(y, sr, cutoff: float = 15000.0):
  233 | def polish_track(
```

## `return` — 28 совпадений
```
   46 |         return None, None
   48 |     return y, sr
   59 |         return y
   64 |         return y
   77 |     return out
   84 |         return y
  101 |     return out
  106 |         return y
  123 |     return out
  132 |         return y
  136 |         return y
  148 |     return out
  153 |         return y
  157 |         return y
  169 |     return out
  174 |         return y
  176 |     return np.tanh(x * (1 + amount)) * (1 / (1 + amount))
  184 |         return y
  188 |         return y
  210 |         return out
  213 |         return f(modulated_indices)
  218 |         return y
  222 |         return y
  228 |         return out
  229 |     return sg.filtfilt(b, a, y)
  248 |         return {"ok": False, "error": "soundfile unavailable"}
  251 |         return {"ok": False, "error": f"cannot read {input_wav}"}
  294 |     return {
```

## `if` — 33 совпадений
```
   45 |     if not HAS_SF:
   58 |     if np is None:
   63 |     if max_shift <= 0:
   75 |     if peak > 0.99:
   83 |     if np is None or not breath_samples:
   89 |         if idx >= len(out):
   92 |         if br is None:
   95 |         if out.ndim == 2 and br.ndim == 1:
   97 |             if out.shape[1] > 1:
  105 |     if np is None or not sections:
  112 |         if e <= s or s >= len(out):
  121 |     if peak > 0.99:
  131 |     if np is None:
  140 |         if freq >= sr / 2:
  143 |         if out.ndim == 2:
  152 |     if np is None:
  156 |     if dur < 30:
  166 |         if e <= s:
  173 |     if np is None:
  183 |     if np is None:
  203 |     if y.ndim == 2:
  217 |     if np is None:
  224 |     if y.ndim == 2:
  247 |     if not HAS_SF:
  250 |     if y is None:
  259 |     if breath_samples and arrangement_plan:
  263 |             if s.get("name", "").startswith(("verse", "chorus", "prechorus")):
  268 |     if arrangement_plan and arrangement_plan.get("sections"):
  272 |     if preset in ("standard", "aggressive"):
  276 |     if preset == "aggressive":
  285 |     if preset in ("gentle", "standard"):
  304 | if __name__ == "__main__":
  307 |     if len(sys.argv) < 3:
```

## `for` — 8 совпадений
```
   87 |     for t in positions_sec:
  109 |     for sec in sections:
  139 |     for freq in (3200.0, 4800.0, 6400.0, 8000.0):
  144 |             for ch in range(out.shape[1]):
  160 |     for _ in range(n_drops):
  205 |         for ch in range(y.shape[1]):
  226 |         for ch in range(y.shape[1]):
  262 |         for s in secs:
```

## `while` — 1 совпадений
```
   67 |     while pos < len(y):
```

## `np` — 10 совпадений
```
   60 |     rng = np.random.default_rng(seed or int(time.time()))
   65 |     out = np.zeros_like(y)
   74 |     peak = float(np.max(np.abs(out))) or 1.0
  120 |     peak = float(np.max(np.abs(out))) or 1.0
  175 |     x = np.clip(y * (1 + amount), -1.0, 1.0)
  176 |     return np.tanh(x * (1 + amount)) * (1 / (1 + amount))
  192 |     t = np.arange(len(y)) / sr
  195 |     lfo = np.sin(2 * math.pi * 0.3 * t) * (cents / 1200.0)
  198 |     time_indices = np.arange(len(y))
  204 |         out = np.zeros_like(y)
```

## `sf` — 2 совпадений
```
   47 |     y, sr = sf.read(path, always_2d=True)
   53 |     sf.write(path, y, sr)
```
