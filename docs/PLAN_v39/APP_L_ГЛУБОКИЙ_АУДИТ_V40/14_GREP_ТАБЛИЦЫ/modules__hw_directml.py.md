# grep-таблицы `modules/hw_directml.py`

## `import` — 9 совпадений
```
   11 | from __future__ import annotations
   13 | import json
   14 | import logging
   15 | import platform
   16 | import subprocess
   17 | from pathlib import Path
   18 | from typing import Any
   41 |         import torch
   60 |             import torch_directml  # type: ignore
```

## `print` — 1 совпадений
```
  145 |     print(json.dumps(p, ensure_ascii=False, indent=2))
```

## `except` — 4 совпадений
```
   52 |             except Exception:
   54 |     except Exception as e:
   69 |         except Exception as e:
  115 |     except Exception:
```

## `try` — 4 совпадений
```
   40 |     try:
   48 |             try:
   59 |         try:
  102 |     try:
```

## `def` — 4 совпадений
```
   23 | def detect() -> dict[str, Any]:
  101 | def _wmic_vram_mb() -> int:
  119 | def save_profile(out_json: str = "data/hw_profile_v10.json") -> dict[str, Any]:
  127 | def choose_musicgen_variant(profile: dict[str, Any] | None = None) -> str:
```

## `return` — 8 совпадений
```
   98 |     return out
  114 |         return max_bytes // (1024 * 1024)
  116 |         return 0
  124 |     return prof
  135 |         return "small"
  137 |         return "large"
  139 |         return "medium"
  140 |     return "small"
```

## `if` — 12 совпадений
```
   43 |         if torch.cuda.is_available():
   58 |     if out["backend"] == "cpu":
   64 |             if n > 0:
   73 |     if (
   78 |         if vram > 0:
   82 |     if out["backend"] == "cpu":
  112 |             if line.isdigit():
  131 |     if profile is None:
  134 |     if profile.get("backend") == "cpu":
  136 |     if vram >= 12000:
  138 |     if vram >= 8000:
  143 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
  110 |         for line in r.stdout.splitlines():
```

## `with` — 1 совпадений
```
  122 |     with open(out_json, "w", encoding="utf-8") as f:
```

## `todo` — 2 совпадений
```
   55 |         log.debug("no torch cuda: %s", e)
   70 |             log.debug("no directml: %s", e)
```

## `subprocess` — 1 совпадений
```
  103 |         r = subprocess.run(
```

## `open` — 1 совпадений
```
  122 |     with open(out_json, "w", encoding="utf-8") as f:
```
