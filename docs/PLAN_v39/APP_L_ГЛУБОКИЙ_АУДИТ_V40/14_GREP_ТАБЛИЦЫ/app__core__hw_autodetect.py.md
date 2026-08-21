# grep-таблицы `app/core/hw_autodetect.py`

## `import` — 10 совпадений
```
   16 | from __future__ import annotations
   18 | import json
   19 | import os
   20 | import platform
   21 | import time
   22 | from pathlib import Path
   37 |         import psutil
   50 |         import torch
   63 |         import torch_directml as dml
   72 |             import subprocess
```

## `print` — 3 совпадений
```
  210 |     print(json.dumps(p, ensure_ascii=False, indent=2))
  211 |     print()
  212 |     print(human_summary(p))
```

## `except` — 8 совпадений
```
   40 |     except Exception:
   59 |     except Exception:
   68 |         except Exception:
   93 |         except Exception:
   96 |     except Exception:
  105 |     except Exception:
  117 |         except Exception:
  154 |     except Exception:
```

## `try` — 8 совпадений
```
   36 |     try:
   49 |     try:
   62 |     try:
   66 |         try:
   71 |         try:
   99 |     try:
  113 |         try:
  150 |     try:
```

## `def` — 5 совпадений
```
   29 | def _cpu_info() -> dict:
   45 | def _gpu_info() -> dict:
  110 | def detect(force: bool = False) -> dict:
  159 | def _recommendations(mode: str, vram: float, ram: float, gpu_kind: str) -> dict:
  192 | def human_summary(profile: dict) -> str:
```

## `return` — 11 совпадений
```
   42 |     return info
   58 |             return g
   95 |         return g
  104 |             return g
  107 |     return g
  116 |                 return cached
  156 |     return profile
  161 |         return {
  170 |         return {
  178 |     return {
  205 |     return "\n".join(lines)
```

## `if` — 11 совпадений
```
   52 |         if torch.cuda.is_available():
   88 |                 if len(parts) >= 3 and parts[-1].isdigit():
   90 |                     if v > g["vram_gb"]:
  100 |         if os.path.exists("/opt/rocm"):
  112 |     if not force and HW_CACHE.exists():
  115 |             if time.time() - cached.get("ts", 0) < 86400:
  126 |     if gpu["kind"] == "cuda" and vram >= 10 and ram >= 20:
  160 |     if mode == "full":
  169 |     if mode == "mid":
  182 |             if gpu_kind != "cpu"
  208 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
   86 |             for line in out.splitlines():
  203 |     for k, v in profile.get("recommendations", {}).items():
```

## `subprocess` — 2 совпадений
```
   74 |             out = subprocess.check_output(
   84 |                 stderr=subprocess.DEVNULL,
```
