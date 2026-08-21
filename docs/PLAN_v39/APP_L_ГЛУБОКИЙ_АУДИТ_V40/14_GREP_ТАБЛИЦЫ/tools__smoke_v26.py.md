# grep-таблицы `tools/smoke_v26.py`

## `import` — 11 совпадений
```
   19 | from __future__ import annotations
   21 | import shutil
   22 | import sys
   23 | from pathlib import Path
   25 | import numpy as np
   26 | import soundfile as sf
   39 |     from app.core.orchestrator import run_full_pipeline
  158 |         from modules import hit_scorer as hs
  189 |     import json
  190 |     import time
  191 |     from pathlib import Path
```

## `print` — 6 совпадений
```
   35 |     print(f"[{'PASS' if ok else 'FAIL'}] {name:38s} {detail}")
   61 |     print("=" * 64)
   62 |     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
   63 |     print("=" * 64)
  177 |     print("-" * 64)
  180 |     print(f"RESULT: {p} PASS / {f} FAIL / {len(RESULTS)} total")
```

## `except` — 2 совпадений
```
  174 |     except Exception as e:
  212 |     except Exception:
```

## `try` — 2 совпадений
```
  157 |     try:
  193 |     try:
```

## `def` — 6 совпадений
```
   33 | def check(name, ok, detail=""):
   38 | def _run(project_id, recipe):
   47 | def _corr(p):
   54 | def _dbfs(p):
   60 | def main():
  185 | def _write_report(name: str, passed: int, failed: int) -> None:
```

## `raise` — 1 совпадений
```
  217 |     raise SystemExit(main())
```

## `return` — 5 совпадений
```
   44 |     return run_full_pipeline(project_id, recipe, dry_run=False, out_root=out_root)
   50 |         return 1.0
   51 |     return float(np.corrcoef(y[:, 0], y[:, 1])[0, 1])
   57 |     return 20.0 * np.log10(max(rms, 1e-12))
  182 |     return 0 if f == 0 else 1
```

## `if` — 11 совпадений
```
   42 |     if out_root.exists():
   49 |     if y.shape[1] < 2:
   80 |     if beat.exists():
   93 |     if master.exists():
  100 |     if master.exists():
  111 |     if beat.exists():
  113 |         if y.ndim > 1:
  127 |             if v:
  143 |         if s.get("name") == "_stage_hit_score":
  146 |     if hit:
  216 | if __name__ == "__main__":
```

## `for` — 4 совпадений
```
  120 |                 for i in range(0, len(y) - win, hop)
  126 |         for v in low:
  142 |     for s in res.get("stages", []):
  163 |         for i in range(5):
```

## `np` — 11 совпадений
```
   51 |     return float(np.corrcoef(y[:, 0], y[:, 1])[0, 1])
   56 |     rms = float(np.sqrt(np.mean(y**2)))
   57 |     return 20.0 * np.log10(max(rms, 1e-12))
  117 |         rms = np.array(
  119 |                 float(np.sqrt(np.mean(y[i : i + win] ** 2)) + 1e-12)
  123 |         med = float(np.median(rms))
  161 |         t = np.arange(sr * 5) / sr
  162 |         env = np.zeros_like(t)
  166 |             env[st:en] = np.linspace(1.0, 0.0, en - st)
  167 |         y = env * np.sin(2 * np.pi * 220 * t) * 0.5
  168 |         score, raw = hs._hook_repeatability(y.astype(np.float32), sr)
```

## `sf` — 4 совпадений
```
   48 |     y, _ = sf.read(p, always_2d=True)
   55 |     y, _ = sf.read(p, always_2d=True)
   81 |         y, sr = sf.read(str(beat), always_2d=True)
  112 |         y, sr = sf.read(str(beat), always_2d=False)
```
