# grep-таблицы `app/logger.py`

## `import` — 4 совпадений
```
    3 | import logging
    4 | import os
    5 | import sys
    6 | from logging.handlers import RotatingFileHandler
```

## `except` — 2 совпадений
```
   18 |         except UnicodeEncodeError:
   24 |         except Exception:
```

## `try` — 2 совпадений
```
   16 |         try:
   22 |         try:
```

## `def` — 4 совпадений
```
   12 |     def __init__(self, s):
   15 |     def write(self, msg):
   21 |     def flush(self):
   28 | def setup_logger(name: str = "mmzs") -> logging.Logger:
```

## `class` — 1 совпадений
```
    9 | class SafeStream:
```

## `return` — 2 совпадений
```
   32 |         return log
   43 |     return log
```

## `if` — 1 совпадений
```
   31 |     if log.handlers:
```
