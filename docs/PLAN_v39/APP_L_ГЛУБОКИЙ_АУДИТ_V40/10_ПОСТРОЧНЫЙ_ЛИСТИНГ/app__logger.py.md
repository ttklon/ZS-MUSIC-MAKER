# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/logger.py`

**Всего строк:** 43

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 17 | 39.5 |
| blank | 8 | 18.6 |
| import | 4 | 9.3 |
| def | 4 | 9.3 |
| try_block | 4 | 9.3 |
| docstring | 2 | 4.7 |
| return | 2 | 4.7 |
| class | 1 | 2.3 |
| branch | 1 | 2.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """UTF-8 в файл, CP866-safe в консоль Windows."""
    2 [blank     ] 
    3 [import    ] import logging
    4 [import    ] import os
    5 [import    ] import sys
    6 [import    ] from logging.handlers import RotatingFileHandler
    7 [blank     ] 
    8 [blank     ] 
    9 [class     ] class SafeStream:
   10 [docstring ]     """Не даёт консоли Windows упасть на emoji/кириллице."""
   11 [blank     ] 
   12 [def       ]     def __init__(self, s):
   13 [code      ]         self.s = s
   14 [blank     ] 
   15 [def       ]     def write(self, msg):
   16 [try_block ]         try:
   17 [code      ]             self.s.write(msg)
   18 [try_block ]         except UnicodeEncodeError:
   19 [code      ]             self.s.write(msg.encode("utf-8", "replace").decode("cp866", "replace"))
   20 [blank     ] 
   21 [def       ]     def flush(self):
   22 [try_block ]         try:
   23 [code      ]             self.s.flush()
   24 [try_block ]         except Exception:
   25 [code      ]             pass
   26 [blank     ] 
   27 [blank     ] 
   28 [def       ] def setup_logger(name: str = "mmzs") -> logging.Logger:
   29 [code      ]     os.makedirs("logs", exist_ok=True)
   30 [code      ]     log = logging.getLogger(name)
   31 [branch    ]     if log.handlers:
   32 [return    ]         return log
   33 [code      ]     log.setLevel(logging.INFO)
   34 [code      ]     fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
   35 [code      ]     fh = RotatingFileHandler(
   36 [code      ]         "logs/app.log", maxBytes=10_000_000, backupCount=5, encoding="utf-8"
   37 [code      ]     )
   38 [code      ]     fh.setFormatter(fmt)
   39 [code      ]     log.addHandler(fh)
   40 [code      ]     sh = logging.StreamHandler(SafeStream(sys.stdout))
   41 [code      ]     sh.setFormatter(fmt)
   42 [code      ]     log.addHandler(sh)
   43 [return    ]     return log
```