# grep-таблицы `agents/trend_scout_v3.py`

## `import` — 9 совпадений
```
   16 | from __future__ import annotations
   18 | import json
   19 | import re
   20 | import time
   21 | import urllib.parse
   22 | import urllib.request
   23 | from pathlib import Path
  237 |     import random
  244 |     import sys
```

## `print` — 1 совпадений
```
  247 |     print(json.dumps(scout(theme, offline_only=True), ensure_ascii=False, indent=2))
```

## `except` — 3 совпадений
```
  142 |         except Exception:
  168 |     except Exception:
  184 |     except Exception:
```

## `try` — 3 совпадений
```
  140 |         try:
  153 |     try:
  173 |     try:
```

## `def` — 6 совпадений
```
  138 | def _load_cache() -> dict:
  147 | def _save_cache(d: dict) -> None:
  151 | def _ddg(query: str, max_res: int = 5) -> list[str]:
  172 | def _reddit_hot(subreddit: str, limit: int = 10) -> list[str]:
  188 | def scout(theme: str, offline_only: bool = False) -> dict:
  233 | def actual_slang_for_prompt(theme: str, n_words: int = 20) -> list[str]:
```

## `return` — 10 совпадений
```
  141 |             return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
  143 |             return {}
  144 |     return {}
  167 |         return out
  169 |         return []
  183 |         return out
  185 |         return []
  198 |         return cache[cache_key]["data"]
  230 |     return result
  240 |     return pool[:n_words]
```

## `if` — 7 совпадений
```
  139 |     if CACHE_FILE.exists():
  163 |             if 15 <= len(t) <= 200:
  165 |             if len(out) >= max_res:
  181 |             if 10 <= len(t) <= 200:
  197 |     if cache_key in cache and time.time() - cache[cache_key].get("ts", 0) < 86400:
  212 |     if not offline_only:
  243 | if __name__ == "__main__":
```

## `for` — 3 совпадений
```
  160 |         for s in snippets:
  179 |         for post in data.get("data", {}).get("children", []):
  214 |         for q in (
```

## `with` — 2 совпадений
```
  156 |         with urllib.request.urlopen(req, timeout=8) as r:
  176 |         with urllib.request.urlopen(req, timeout=8) as r:
```
