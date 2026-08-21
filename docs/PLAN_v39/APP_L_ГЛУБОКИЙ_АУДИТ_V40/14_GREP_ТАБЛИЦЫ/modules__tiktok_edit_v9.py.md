# grep-таблицы `modules/tiktok_edit_v9.py`

## `import` — 8 совпадений
```
   19 | from __future__ import annotations
   21 | import json
   22 | import shutil
   23 | import subprocess
   24 | from pathlib import Path
   27 |     import numpy as np
   32 |     import soundfile as sf
  253 |     import sys
```

## `print` — 2 совпадений
```
  256 |         print("usage: python tiktok_edit_v9.py <in.wav> <out_dir>")
  259 |     print(
```

## `except` — 3 совпадений
```
   28 | except Exception:
   35 | except Exception:
  248 |     except Exception as e:
```

## `try` — 3 совпадений
```
   26 | try:
   31 | try:
  243 |     try:
```

## `def` — 8 совпадений
```
   39 | def _read(path: str):
   46 | def _write(path: str, y, sr):
   51 | def _find_hot_slice(y, sr, want_sec: float = 25.0) -> tuple[float, float]:
   73 | def _fade_in_out(y, sr, in_ms: float = 40.0, out_ms: float = 120.0):
   93 | def cut_slice(
  118 | def make_all_cuts(
  183 | def _has_ffmpeg() -> bool:
  187 | def make_vertical_video(
```

## `return` — 19 совпадений
```
   41 |         return None, None
   43 |     return y, sr
   54 |         return 0.0, want_sec
   61 |         return 0.0, len(mono) / sr
   70 |     return best_start / sr, (best_start + win_len) / sr
   75 |         return y
   90 |     return y
   97 |         return {"ok": False, "error": "soundfile/numpy required"}
  100 |         return {"ok": False, "error": "read failed"}
  104 |         return {"ok": False, "error": "invalid slice"}
  109 |     return {
  126 |         return {"ok": False, "error": "soundfile/numpy required"}
  129 |         return {"ok": False, "error": "read failed"}
  173 |     return {
  184 |     return shutil.which("ffmpeg") is not None
  195 |         return {"ok": False, "error": "ffmpeg not available"}
  246 |             return {"ok": False, "error": p.stderr[-500:].decode("utf-8", "ignore")}
  247 |         return {"ok": True, "output": output_mp4}
  249 |         return {"ok": False, "error": str(e)}
```

## `if` — 27 совпадений
```
   40 |     if not HAS_SF:
   53 |     if np is None or len(y) == 0:
   55 |     if y.ndim == 2:
   60 |     if len(mono) <= win_len:
   67 |         if r > best_rms:
   74 |     if np is None:
   78 |     if in_n < len(y):
   80 |         if y.ndim == 2:
   84 |     if out_n < len(y):
   86 |         if y.ndim == 2:
   96 |     if not HAS_SF or np is None:
   99 |     if y is None:
  103 |     if e <= s:
  106 |     if fade:
  125 |     if not HAS_SF or np is None:
  128 |     if y is None:
  137 |     if hit_report and "tiktok_slice" in hit_report:
  141 |     if start is None:
  157 |     if arrangement_plan and arrangement_plan.get("sections"):
  161 |             if s.get("name", "").startswith(("chorus", "drop"))
  163 |         if chorus:
  167 |     if hook_start is None:
  194 |     if not _has_ffmpeg():
  197 |     if cover_png and Path(cover_png).exists():
  245 |         if p.returncode != 0:
  252 | if __name__ == "__main__":
  255 |     if len(sys.argv) < 3:
```

## `for` — 3 совпадений
```
   65 |     for i in range(0, len(mono) - win_len, hop):
  160 |             for s in arrangement_plan["sections"]
  263 |                 for k, v in r.get("results", {}).items()
```

## `subprocess` — 1 совпадений
```
  244 |         p = subprocess.run(cmd, capture_output=True, timeout=180)
```

## `np` — 3 совпадений
```
   66 |         r = float(np.sqrt(np.mean(mono[i : i + win_len] ** 2) + 1e-12))
   79 |         ramp = np.linspace(0.0, 1.0, in_n)
   85 |         ramp = np.linspace(1.0, 0.0, out_n)
```

## `sf` — 2 совпадений
```
   42 |     y, sr = sf.read(path, always_2d=True)
   48 |     sf.write(path, y, sr)
```
