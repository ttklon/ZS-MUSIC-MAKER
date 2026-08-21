# grep-таблицы `app/core/license_manager.py`

## `import` — 2 совпадений
```
    7 | from __future__ import annotations
    9 | from dataclasses import dataclass
```

## `def` — 3 совпадений
```
   31 | def normalize(lic: str) -> str:
   51 | def is_free_commercial(lic: str, allow_user_override: bool = False) -> bool:
   60 | def check(lic: str, allow_user_override: bool = False) -> LicenseCheck:
```

## `class` — 1 совпадений
```
   25 | class LicenseCheck:
```

## `return` — 13 совпадений
```
   38 |             return "public domain"
   40 |             return "cc-by-nc"
   42 |             return "cc-by-sa"
   44 |             return "cc-by"
   46 |             return "cc0"
   47 |         return "unknown"
   48 |     return n
   54 |         return True
   56 |         return True
   57 |     return False
   63 |         return LicenseCheck(True, n in NEEDS_ATTRIBUTION, "allowed")
   65 |         return LicenseCheck(allow_user_override, False, "requires user confirmation")
   66 |     return LicenseCheck(allow_user_override, False, f"unknown license: {lic}")
```

## `if` — 10 совпадений
```
   36 |     if "/" in n or "creativecommons.org" in n or "licenses" in n:
   37 |         if "publicdomain" in n or "public-domain" in n:
   39 |         if "by-nc-sa" in n or "by-nc-nd" in n or "by-nc" in n:
   41 |         if "by-sa" in n:
   43 |         if n.rstrip("/").endswith("/by") or "/by/" in n:
   45 |         if "zero" in n or "cc0" in n:
   53 |     if n in ALLOW_DEFAULT:
   55 |     if allow_user_override:
   62 |     if n in ALLOW_DEFAULT:
   64 |     if n in BLOCK_UNLESS_CONFIRMED:
```
