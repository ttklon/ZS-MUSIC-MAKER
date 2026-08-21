# grep-таблицы `app/core/logger.py`

## `import` — 3 совпадений
```
    9 | import logging
   10 | from pathlib import Path
   11 | from logging.handlers import RotatingFileHandler
```

## `except` — 1 совпадений
```
   52 |         except (TypeError, ValueError):
```

## `try` — 1 совпадений
```
   50 |         try:
```

## `def` — 2 совпадений
```
   13 | def setup_logger(name: str, log_file: str = "app.log", level=logging.INFO):
   46 | def log_stage(logger, stage: str, event: str = "start", duration_ms=None, **extra):
```

## `return` — 1 совпадений
```
   40 |     return logger
```

## `if` — 2 совпадений
```
   36 |     if not logger.handlers:
   49 |     if duration_ms is not None:
```

## `for` — 1 совпадений
```
   54 |     for k, v in extra.items():
```
