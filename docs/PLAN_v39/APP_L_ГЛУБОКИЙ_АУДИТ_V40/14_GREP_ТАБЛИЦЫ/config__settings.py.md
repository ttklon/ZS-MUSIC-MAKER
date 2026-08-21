# grep-таблицы `config/settings.py`

## `import` — 5 совпадений
```
   15 | from __future__ import annotations
   17 | import os
   18 | from dataclasses import dataclass
   19 | from pathlib import Path
   20 | from typing import Optional
```

## `print` — 1 совпадений
```
   41 |         print(f"[settings] cannot read {path}: {e}")
```

## `except` — 3 совпадений
```
   40 |     except OSError as e:  # noqa: BLE001
   56 |     except (TypeError, ValueError):
   65 |     except (TypeError, ValueError):
```

## `try` — 3 совпадений
```
   30 |     try:
   54 |     try:
   63 |     try:
```

## `def` — 9 совпадений
```
   25 | def _parse_dotenv(path: Path) -> dict[str, str]:
   45 | def _as_bool(value, default: bool = False) -> bool:
   51 | def _as_int(value, default: int) -> int:
   60 | def _as_float(value, default: float) -> float:
   90 |     def load(cls, env_path: Optional[Path] = None) -> "Settings":
   95 |         def get(key: str, default=None):
  122 |     def dump(self) -> dict:
  148 | def get_settings() -> Settings:
  155 | def reset_settings() -> None:
```

## `class` — 1 совпадений
```
   70 | class Settings:
```

## `return` — 14 совпадений
```
   29 |         return out
   42 |     return out
   47 |         return default
   48 |     return str(value).strip().lower() in ("1", "true", "yes", "on")
   53 |         return default
   55 |         return int(float(str(value).strip()))
   57 |         return default
   62 |         return default
   64 |         return float(str(value).strip())
   66 |         return default
   96 |             return os.environ.get(key, dot.get(key, default))
  120 |         return s
  141 |         return d
  152 |     return _settings
```

## `if` — 7 совпадений
```
   28 |     if not path.exists():
   33 |             if not line or line.startswith("#") or "=" not in line:
   37 |             if not k:
   46 |     if value is None:
   52 |     if value is None:
   61 |     if value is None:
  150 |     if _settings is None:
```

## `for` — 1 совпадений
```
   31 |         for raw in path.read_text(encoding="utf-8").splitlines():
```
