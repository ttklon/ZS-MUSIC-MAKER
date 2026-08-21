# grep-таблицы `agents/trend_scout.py`

## `import` — 6 совпадений
```
    8 | import json
    9 | import os
   10 | import re
   11 | import time
   13 | import requests
   45 |         from modules.lyrics_gen import load_slang_dictionary
```

## `print` — 1 совпадений
```
  156 |     print(json.dumps(scout_trends("phonk drift"), ensure_ascii=False, indent=2))
```

## `except` — 4 совпадений
```
   40 |     except Exception:
   48 |     except Exception:
  114 |         except Exception:
  147 |     except Exception:
```

## `try` — 4 совпадений
```
   38 |     try:
   44 |     try:
  112 |         try:
  143 |     try:
```

## `def` — 6 совпадений
```
   21 | def scout_trends(query: str, max_results: int = 10) -> list:
   65 | def _duckduckgo_search(query: str) -> list:
   81 | def _fallback_trends(query: str) -> list:
  110 | def _load_cache() -> dict:
  119 | def _save_cache(data: dict):
  125 | def get_hot_topics() -> list:
```

## `return` — 9 совпадений
```
   33 |             return entry.get("trends", [])
   62 |     return trends
   78 |     return clean[:5]
   83 |     return [
  113 |             return json.load(open(CACHE_FILE, encoding="utf-8"))
  115 |             return {}
  116 |     return {}
  129 |         return cache["hot_topics"].get("topics", [])
  152 |     return topics
```

## `if` — 8 совпадений
```
   30 |     if cache_key in cache:
   32 |         if time.time() - entry.get("ts", 0) < 86400:
   52 |     if not trends:
   76 |         if text and len(text) > 10:
  111 |     if os.path.exists(CACHE_FILE):
  128 |     if "hot_topics" in cache and time.time() - cache["hot_topics"].get("ts", 0) < 86400:
  145 |         if online:
  155 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
   74 |     for s in snippets:
```

## `requests` — 2 совпадений
```
   67 |     url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
   69 |     r = requests.get(url, headers=headers, timeout=10)
```

## `open` — 2 совпадений
```
  113 |             return json.load(open(CACHE_FILE, encoding="utf-8"))
  121 |         data, open(CACHE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2
```
