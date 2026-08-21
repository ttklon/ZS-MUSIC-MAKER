# grep-таблицы `agents/sample_hunter.py`

## `import` — 7 совпадений
```
   17 | from __future__ import annotations
   19 | import json
   20 | import os
   21 | import urllib.parse
   22 | from pathlib import Path
   23 | from app.core.security_utils import safe_hash, download_file, get_json
  154 |             from app.core.license_manager import is_free_commercial
```

## `print` — 3 совпадений
```
   86 |         print(f"[sample_hunter.wikimedia] {e}")
  200 |         print(f"[sample_hunter.download] {e}")
  205 |     print(json.dumps(hunt("phonk 808", max_results=3), ensure_ascii=False, indent=2))
```

## `except` — 5 совпадений
```
   85 |     except Exception as e:
   98 |     except Exception:
  125 |     except Exception:
  159 |         except Exception:
  199 |     except Exception as e:
```

## `try` — 5 совпадений
```
   59 |     try:
   93 |     try:
  107 |     try:
  153 |         try:
  188 |     try:
```

## `def` — 7 совпадений
```
   31 | def list_local(query: str = "") -> list[dict]:
   56 | def search_wikimedia(query: str, max_results: int = 10) -> list[dict]:
   90 | def search_freesound_public(query: str, max_results: int = 10) -> list[dict]:
  102 | def search_pixabay(query: str, max_results: int = 10) -> list[dict]:
  129 | def search_online(query: str, max_results: int = 10) -> list[dict]:
  139 | def hunt(
  181 | def download_to_cache(item: dict) -> str | None:
```

## `return` — 17 совпадений
```
   52 |     return out
   67 |             return []
   87 |     return results
   97 |         return results
   99 |         return results
  106 |         return []
  111 |             return []
  124 |         return results
  126 |         return []
  135 |     return results[:max_results]
  162 |     return {
  184 |         return item.get("path")
  187 |         return None
  195 |             return str(target)
  197 |             return str(target)
  198 |         return None
  201 |         return None
```

## `if` — 13 совпадений
```
   36 |         if not p.is_file():
   38 |         if p.suffix.lower() not in (".wav", ".mp3", ".flac", ".ogg", ".m4a"):
   40 |         if q and q not in p.name.lower():
   66 |         if not data:
   70 |             if not any(
  105 |     if not api_key:
  110 |         if not data:
  152 |     if license_filter:
  183 |     if item.get("source") == "local":
  186 |     if not url:
  194 |         if target.exists():
  196 |         if download_file(url, str(target)):
  204 | if __name__ == "__main__":
```

## `for` — 4 совпадений
```
   35 |     for p in sorted(CACHE.glob("**/*")):
   68 |         for item in data.get("query", {}).get("search", []):
  112 |         for hit in data.get("hits", []):
  176 |             for s in online
```
