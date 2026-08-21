# grep-таблицы `modules/phoneme_coverage.py`

## `import` — 5 совпадений
```
   14 | from __future__ import annotations
   16 | import json
   17 | from collections import Counter
   18 | from pathlib import Path
   19 | from typing import Any
```

## `print` — 1 совпадений
```
  137 |     print(json.dumps(r, ensure_ascii=False, indent=2))
```

## `except` — 2 совпадений
```
   53 |         except Exception:
   64 |         except Exception:
```

## `try` — 2 совпадений
```
   51 |         try:
   56 |         try:
```

## `def` — 3 совпадений
```
   45 | def _collect_transcripts() -> list[str]:
   69 | def compute_coverage() -> dict[str, Any]:
  111 | def _make_suggestions(ru_missing, en_missing, di_missing) -> list[str]:
```

## `return` — 3 совпадений
```
   66 |     return texts
  108 |     return report
  132 |     return pool[:5]
```

## `if` — 11 совпадений
```
   58 |             if isinstance(data, dict) and "transcript" in data:
   62 |                     if isinstance(item, dict) and "transcript" in item:
  116 |     if "ъ" in ru_missing or "ы" in ru_missing:
  118 |     if "ж" in ru_missing or "щ" in ru_missing:
  120 |     if "х" in ru_missing:
  122 |     if "ц" in ru_missing:
  124 |     if any(x in en_missing for x in "xzqj"):
  126 |     if "th" in di_missing:
  128 |     if "sh" in di_missing:
  130 |     if not pool:
  135 | if __name__ == "__main__":
```

## `for` — 3 совпадений
```
   50 |     for p in VAULT_DIR.rglob("*.txt"):
   55 |     for p in VAULT_DIR.rglob("*.json"):
   61 |                 for item in data:
```
