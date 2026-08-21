# grep-таблицы `tools/smoke_v29.py`

## `import` — 14 совпадений
```
   16 | from __future__ import annotations
   18 | import json
   19 | import shutil
   20 | import subprocess
   21 | import sys
   22 | from pathlib import Path
   24 | import numpy as np
   25 | import soundfile as sf
   58 |     from modules import midi_generator
   80 |     from app.core.orchestrator_god import run_god_pipeline
  123 |     from modules import mastering_pro
  160 |     import json
  161 |     import time
  162 |     from pathlib import Path
```

## `print` — 7 совпадений
```
   35 |     print(f"[PASS] {name:40s} {extra}")
   40 |     print(f"[FAIL] {name:40s} {extra}")
  142 |     print("=" * 64)
  143 |     print("ZS Music Maker v29 — smoke_v29 (God Mode E2E)")
  144 |     print("=" * 64)
  149 |     print("-" * 64)
  153 |     print(f"RESULT: {passed} PASS / {failed} FAIL / {total} total")
```

## `except` — 2 совпадений
```
   53 |     except Exception as e:
  183 |     except Exception:
```

## `try` — 2 совпадений
```
   44 |     try:
  164 |     try:
```

## `def` — 8 совпадений
```
   33 | def _ok(name: str, extra: str = "") -> None:
   38 | def _fail(name: str, extra: str = "") -> None:
   43 | def test_version_cli() -> None:
   57 | def test_midi_generator() -> None:
   76 | def test_god_mode_e2e() -> None:
  121 | def test_mastering_pro_metrics() -> None:
  141 | def main() -> int:
  158 | def _write_report(name: str, passed: int, failed: int) -> None:
```

## `return` — 3 совпадений
```
   87 |         return
   92 |         return
  155 |     return 0 if failed == 0 else 1
```

## `if` — 13 совпадений
```
   49 |         if out.returncode == 0 and "ZS Music Maker" in out.stdout:
   63 |     if st["ok"]:
   64 |         if drum and mel and Path(drum).exists() and Path(mel).exists():
   70 |         if drum == "" and mel == "":
   78 |     if out_root.exists():
   83 |     if res.get("status") == "completed":
   90 |     if not master or not Path(master).exists():
   95 |     if audio.ndim == 2 and audio.shape[1] == 2:
  101 |     if 110 <= dur <= 130:
  109 |     if peak_db <= -0.5:
  115 |     if 0.03 <= rms <= 0.6:
  134 |     if r.get("ok") and "output_peak_db" in r and "channels" in r:
  187 | if __name__ == "__main__":
```

## `subprocess` — 1 совпадений
```
   45 |         out = subprocess.run(
```

## `np` — 6 совпадений
```
  106 |     peak = float(np.max(np.abs(audio))) if audio.size else 0.0
  107 |     peak_db = 20.0 * np.log10(peak + 1e-12)
  114 |     rms = float(np.sqrt(np.mean(audio ** 2)))
  126 |     t = np.linspace(0, 3.0, sr * 3, endpoint=False)
  127 |     x = 0.3 * np.sin(2 * np.pi * 220 * t).astype(np.float32)
  128 |     stereo = np.stack([x, x], axis=1)
```

## `sf` — 2 совпадений
```
   94 |     audio, sr = sf.read(master)
  132 |     sf.write(str(in_wav), stereo, sr)
```
