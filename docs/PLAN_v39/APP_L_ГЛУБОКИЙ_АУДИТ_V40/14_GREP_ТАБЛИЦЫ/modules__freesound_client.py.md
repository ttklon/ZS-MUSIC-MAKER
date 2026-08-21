# grep-таблицы `modules/freesound_client.py`

## `import` — 10 совпадений
```
   16 | from __future__ import annotations
   18 | import hashlib
   19 | import json
   20 | import logging
   21 | import os
   22 | import time
   23 | from pathlib import Path
   24 | from typing import Any
   29 |     import requests
  196 |     import sys
```

## `print` — 1 совпадений
```
  200 |     print(json.dumps(res, ensure_ascii=False, indent=2)[:2000])
```

## `except` — 4 совпадений
```
   30 | except Exception:
  107 |     except Exception as e:
  166 |     except Exception as e:
  177 |         except Exception:
```

## `try` — 4 совпадений
```
   28 | try:
   84 |     try:
  159 |     try:
  175 |         try:
```

## `def` — 5 совпадений
```
   43 | def _load_key() -> str | None:
   55 | def search(
  112 | def _offline_search(query: str) -> dict[str, Any]:
  145 | def download_preview(
  171 | def _append_manifest(item: dict[str, Any], local_path: str) -> None:
```

## `return` — 12 совпадений
```
   47 |         return k.strip()
   51 |         return cfg.read_text(encoding="utf-8").strip()
   52 |     return None
   69 |         return _offline_search(query)
   88 |             return _offline_search(query)
  106 |         return {"ok": True, "count": len(results), "results": results, "offline": False}
  109 |         return _offline_search(query)
  117 |         return {"ok": True, "count": 0, "results": [], "offline": True}
  142 |     return {"ok": True, "count": len(out), "results": out, "offline": True}
  154 |         return item.get("local_path")
  165 |             return str(out)
  168 |     return None
```

## `if` — 13 совпадений
```
   46 |     if k:
   50 |     if cfg.exists():
   67 |     if not (requests and api_key):
   72 |     if bpm_min and bpm_max:
   74 |     if license_only_cc0:
   86 |         if r.status_code != 200:
  116 |     if not DEFAULT_CACHE.exists():
  121 |         if q in p.name.lower():
  132 |         if q in p.name.lower():
  153 |     if not url or not requests:
  161 |         if r.status_code == 200:
  174 |     if DEFAULT_MANIFEST.exists():
  195 | if __name__ == "__main__":
```

## `for` — 3 совпадений
```
   91 |         for item in data.get("results", []):
  120 |     for p in DEFAULT_CACHE.rglob("*.wav"):
  131 |     for p in DEFAULT_CACHE.rglob("*.mp3"):
```

## `with` — 1 совпадений
```
  162 |             with open(out, "wb") as f:
```

## `requests` — 2 совпадений
```
   85 |         r = requests.get(FS_ENDPOINT, params=params, timeout=15)
  160 |         r = requests.get(url, timeout=30, stream=True)
```

## `open` — 1 совпадений
```
  162 |             with open(out, "wb") as f:
```
