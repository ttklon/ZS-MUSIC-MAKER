# grep-таблицы `tools/real_e2e_v14.py`

## `import` — 10 совпадений
```
   13 | from __future__ import annotations
   15 | import json
   16 | import sys
   17 | import time
   18 | from pathlib import Path
   31 |     import numpy as np
   32 |     import soundfile as sf
   67 |         import soundfile as sf
   97 |     from app.core.orchestrator import run_full_pipeline
  134 |     from tools import fallback_audit, readiness
```

## `print` — 15 совпадений
```
   83 |     print("=" * 64)
   84 |     print("ZS Music Maker v14 — real_e2e_v14 (non-dry pipeline)")
   85 |     print("=" * 64)
   93 |     print(
  165 |     print()
  166 |     print("─" * 64)
  167 |     print(f"Verdict:            {summary['pipeline_verdict']}")
  168 |     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
  169 |     print(f"Fallback stages:    {summary['stages_fallback']}")
  170 |     print(f"Masters generated:  {len(stands_check)}/8")
  171 |     print(f"Release files:      {len(release_check)}")
  172 |     print(f"Readiness (formula):{summary['readiness_percent']}%")
  173 |     print(f"Red flags:          {summary['fallback_red_flags_count']}")
  174 |     print(f"Full JSON:          {workdir / 'e2e_summary.json'}")
  175 |     print()
```

## `except` — 1 совпадений
```
   78 |     except Exception as e:
```

## `try` — 1 совпадений
```
   66 |     try:
```

## `def` — 3 совпадений
```
   28 | def _synthesize_reference(
   65 | def _check_wav(path: str) -> dict:
   82 | def main() -> int:
```

## `raise` — 1 совпадений
```
  186 |     raise SystemExit(main())
```

## `return` — 5 совпадений
```
   62 |     return {"path": str(out_wav), "sr": sr, "duration": duration, "bpm": bpm}
   70 |         return {
   79 |         return {"exists": False, "path": path, "error": str(e)}
  181 |         return 0
  182 |     return 1
```

## `if` — 8 совпадений
```
   24 | if str(ROOT) not in sys.path:
   42 |         if i % 2 == 0:
  118 |         if p.exists():
  123 |     if masters_dir.exists():
  129 |     if release_dir.exists():
  131 |             if f.is_file():
  177 |     if (
  185 | if __name__ == "__main__":
```

## `for` — 5 совпадений
```
   39 |     for i in range(int(duration / beat)):
   53 |     for j in range(int(duration / (beat / 2))):
  116 |     for cand in ("beat.wav", "voice_preview.wav", "mix_ducked.wav", "polished.wav"):
  124 |         for m in masters_dir.glob("master_*.wav"):
  130 |         for f in release_dir.iterdir():
```

## `np` — 12 совпадений
```
   35 |     t = np.arange(n) / sr
   36 |     y = np.zeros(n, dtype="float32")
   43 |             tt = np.arange(e - s) / sr
   44 |             freq = 55 * np.exp(-tt * 15)
   45 |             y[s:e] += np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-tt * 8) * 0.9
   47 |             tt = np.arange(e - s) / sr
   48 |             tone = np.sin(2 * np.pi * 220 * tt) * np.exp(-tt * 25)
   49 |             noise = np.random.randn(e - s).astype("float32") * np.exp(-tt * 10)
   51 |         y[s:e] += np.sin(2 * np.pi * 55 * t[s:e]) * 0.15
   56 |         tt = np.arange(e - s) / sr
   57 |         y[s:e] += np.random.randn(e - s).astype("float32") * np.exp(-tt * 60) * 0.35
   59 |     y = y / (np.max(np.abs(y)) + 1e-9) * 0.9
```

## `sf` — 2 совпадений
```
   61 |     sf.write(str(out_wav), y, sr)
   69 |         info = sf.info(path)
```
