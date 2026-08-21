# grep-таблицы `modules/beat_gen_ai.py`

## `import` — 6 совпадений
```
    3 | from __future__ import annotations
    4 | import math
    5 | from pathlib import Path
    6 | from typing import Any, Dict, Optional
    7 | from app.ai.registry import registry
   15 |     import numpy as np, soundfile as sf, torch
```

## `except` — 2 совпадений
```
   23 |         except Exception:
   34 |             except Exception:
```

## `try` — 2 совпадений
```
   20 |         try:
   28 |             try:
```

## `def` — 1 совпадений
```
   10 | def render_beat_ai(prompt: str, bpm: int = 140, duration_sec: int = 120,
```

## `return` — 2 совпадений
```
   14 |         return {"ok": False, "reason": "music_generation unavailable - install audiocraft"}
   50 |     return {"ok": True, "beat_path": out_path, "duration_sec": duration_sec,
```

## `if` — 6 совпадений
```
   13 |     if not registry.is_available("music_generation"):
   30 |                 if any(p.is_cuda for p in model.lm.parameters()):
   38 |     if full.shape[-1] > total:
   40 |     if full.ndim == 1:
   44 |         if full.shape[1] == 1:
   47 |     if peak > 0.99:
```

## `for` — 1 совпадений
```
   27 |         for i in range(1, n_chunks):
```

## `with` — 1 совпадений
```
   18 |     with registry.use("music_generation") as m:
```

## `np` — 4 совпадений
```
   36 |     full = np.concatenate(chunks, axis=-1)
   41 |         full = np.stack([full, full], axis=-1)
   45 |             full = np.concatenate([full, full], axis=1)
   46 |     peak = float(np.max(np.abs(full)) + 1e-9)
```

## `sf` — 1 совпадений
```
   49 |     sf.write(out_path, full.astype("float32"), int(sr), subtype="PCM_16")
```
