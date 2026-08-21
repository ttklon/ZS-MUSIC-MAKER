# grep-таблицы `agents/sample_hunter_v9.py`

## `import` — 8 совпадений
```
   26 | from __future__ import annotations
   28 | import json
   29 | import re
   30 | import time
   31 | from pathlib import Path
   32 | from urllib.parse import quote_plus
   35 |     import requests
  282 |         from app.core.license_manager import is_free_commercial
```

## `print` — 4 совпадений
```
  297 |             print(f"[sample_hunter_v9] BLOCKED non-free sample: "
  364 |     print("PLAN:", q)
  366 |     print(f"LOCAL: {len(local)} files")
  367 |     print(f"HAS_REQ: {HAS_REQ}")
```

## `except` — 6 совпадений
```
   38 | except Exception:
  158 |     except Exception:
  223 |     except Exception:
  263 |     except Exception:
  283 |     except Exception:
  312 |             except Exception:
```

## `try` — 6 совпадений
```
   34 | try:
  152 |     try:
  202 |     try:
  242 |     try:
  281 |     try:
  310 |             try:
```

## `def` — 10 совпадений
```
  111 | def plan_queries(style_vector: dict, max_queries: int = 8) -> list[str]:
  128 | def list_local(subdir: str = "") -> list[dict]:
  149 | def _http_get(url: str, timeout: float = 6.0) -> str | None:
  163 | def search_freesound_web(query: str, limit: int = 5) -> list[dict]:
  191 | def search_wikimedia(query: str, limit: int = 5) -> list[dict]:
  227 | def search_archive_org(query: str, limit: int = 5) -> list[dict]:
  269 | def _license_gate(items: list[dict], allow_user_override: bool = False) -> list[dict]:
  302 | def search_online(
  326 | def unified_search(
  346 | def save_manifest(items: list[dict], project_id: str) -> str:
```

## `return` — 23 совпадений
```
  121 |     return plan
  131 |         return []
  145 |     return items
  151 |         return None
  157 |             return r.text
  159 |         return None
  160 |     return None
  166 |         return []
  173 |         return []
  188 |     return out
  193 |         return []
  201 |         return []
  222 |         return out
  224 |         return []
  229 |         return []
  241 |         return []
  262 |         return out
  264 |         return []
  284 |         return items  # менеджер недоступен — не блокируем пайплайн
  299 |     return out
  323 |     return _license_gate(hits)
  343 |     return result
  357 |     return str(path)
```

## `if` — 19 совпадений
```
  130 |     if not root.exists():
  134 |         if p.is_file() and p.suffix.lower() in AUDIO_EXT:
  150 |     if not HAS_REQ:
  156 |         if r.status_code == 200:
  165 |     if not HAS_REQ:
  172 |     if not html:
  192 |     if not HAS_REQ:
  200 |     if not txt:
  207 |             if not any(title.lower().endswith(ext) for ext in AUDIO_EXT):
  228 |     if not HAS_REQ:
  240 |     if not txt:
  249 |             if not ident:
  289 |         if it.get("source") == "local":
  292 |         if is_free_commercial(lic, allow_user_override=allow_user_override):
  316 |                 if key in seen:
  320 |                 if len(hits) >= max_total:
  338 |     if include_local:
  340 |     if include_online:
  361 | if __name__ == "__main__":
```

## `for` — 8 совпадений
```
  133 |     for p in root.rglob("*"):
  176 |     for path, sid, name in m[:limit]:
  205 |         for row in j.get("query", {}).get("search", [])[:limit]:
  246 |         for d in docs[:limit]:
  286 |     for it in items:
  308 |     for q in queries:
  309 |         for finder in (search_freesound_web, search_wikimedia, search_archive_org):
  314 |             for r in results:
```

## `requests` — 1 совпадений
```
  153 |         r = requests.get(
```
