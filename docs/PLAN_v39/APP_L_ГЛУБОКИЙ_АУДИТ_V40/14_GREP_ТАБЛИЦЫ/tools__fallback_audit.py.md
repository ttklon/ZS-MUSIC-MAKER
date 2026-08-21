# grep-таблицы `tools/fallback_audit.py`

## `import` — 5 совпадений
```
   11 | from __future__ import annotations
   13 | import json
   14 | import re
   15 | from pathlib import Path
   16 | from typing import Any
```

## `print` — 1 совпадений
```
  155 |     print(
```

## `except` — 1 совпадений
```
   70 |     except Exception:
```

## `try` — 1 совпадений
```
   68 |     try:
```

## `def` — 4 совпадений
```
   44 | def _is_hard_refusal(text: str, def_line: str) -> bool:
   63 | def scan_file(path: Path) -> dict[str, list[dict[str, Any]]]:
  107 | def scan_all() -> dict[str, Any]:
  149 | def main() -> int:
```

## `raise` — 4 совпадений
```
   49 |     # тело функции должно содержать raise RuntimeError
   56 |     if "raise RuntimeError" not in body:
   93 |             # v18: hard-refusal (raise RuntimeError / deprecated-stub,
  171 |     raise SystemExit(main())
```

## `return` — 8 совпадений
```
   54 |         return False
   57 |         return False
   60 |     return len(calls) <= 1  # только само объявление
   66 |         return {}
   71 |         return hits
  104 |     return hits
  141 |     return {
  167 |     return 0 if not r["red_flags"] else 1
```

## `if` — 12 совпадений
```
   53 |     if not m:
   56 |     if "raise RuntimeError" not in body:
   65 |     if rel in SELF_SKIP:
   78 |                 if line_no - 1 < len(lines)
   91 |             if any(mk in window for mk in LEGIT_MARKERS):
   95 |             if snippet.startswith("def ") and _is_hard_refusal(text, snippet):
  112 |         if not base.exists():
  115 |             if "__pycache__" in str(p):
  131 |         if tag in all_hits:
  135 |                 if "legacy/" not in e["file"]
  138 |             if real:
  170 | if __name__ == "__main__":
```

## `for` — 7 совпадений
```
   73 |     for tag, pat in BAD_PATTERNS.items():
   74 |         for m in re.finditer(pat, text):
  110 |     for d in SCAN_DIRS:
  114 |         for p in base.rglob("*.py"):
  119 |             for tag, entries in h.items():
  124 |     for tag in (
  134 |                 for e in all_hits[tag]
```
