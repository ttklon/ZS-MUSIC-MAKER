# grep-таблицы `app/core/isrc.py`

## `import` — 5 совпадений
```
   20 | from __future__ import annotations
   22 | import hashlib
   23 | import re
   24 | import time
   25 | from typing import Any, Optional
```

## `except` — 2 совпадений
```
   93 |     except (TypeError, ValueError):
  104 |         except (TypeError, ValueError):
```

## `try` — 2 совпадений
```
   91 |     try:
  102 |         try:
```

## `def` — 6 совпадений
```
   30 | def is_valid_isrc(isrc: Optional[str]) -> bool:
   44 | def is_placeholder_isrc(isrc: Optional[str]) -> bool:
   52 | def _short_seq_from_title(title: str) -> str:
   61 | def _normalize_existing(existing: str) -> str:
   66 | def generate_isrc(
  111 | def get_isrc(meta: dict[str, Any], fallback: str = "") -> str:
```

## `return` — 11 совпадений
```
   33 |         return False
   36 |         return False
   40 |         return False
   41 |     return True
   47 |         return True
   49 |     return "XXXXX" in s or s.startswith("XX") or (s.endswith("00000") and "00" in s[5:7])
   58 |     return f"{n:05d}"
   63 |     return f"{s[:2]}-{s[2:5]}-{s[5:7]}-{s[7:12]}"
   85 |         return _normalize_existing(str(existing))
  108 |     return isrc if is_valid_isrc(isrc) else ""
  117 |     return isrc if is_valid_isrc(isrc) else fallback
```

## `if` — 7 совпадений
```
   32 |     if not isrc:
   35 |     if not _ISRC_RE.match(s):
   39 |     if core.startswith("XX") or (core.endswith("00000") and core[5:7] == "00"):
   46 |     if not isrc:
   54 |     if not title:
   84 |     if is_valid_isrc(existing):
   97 |     if seq is None:
```

## `todo` — 7 совпадений
```
    7 | Формат ISRC (ISO 3901): CC-XXX-YY-NNNNN
    9 |   XXX   — 3-символьный код регистранта (буквы или цифры)
   14 | метаданные содержали заглушку XX-XXX-00-00000 — трек уходил бы к
   37 |     # плейсхолдеры вида XX-XXX-00-00000 отбраковываем
   45 |     """True если это XX-XXX-00-00000 / пусто / любой очевидный placeholder."""
   49 |     return "XXXXX" in s or s.startswith("XX") or (s.endswith("00000") and "00" in s[5:7])
  114 |     fallback по-умолчанию — пустая строка (никогда не XX-XXX-00-00000).
```
