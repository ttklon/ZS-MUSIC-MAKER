# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/logger.py`

**Всего строк:** 56

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 22 | 39.3 |
| blank | 11 | 19.6 |
| docstring | 8 | 14.3 |
| comment | 4 | 7.1 |
| import | 3 | 5.4 |
| def | 2 | 3.6 |
| branch | 2 | 3.6 |
| try_block | 2 | 3.6 |
| return | 1 | 1.8 |
| loop | 1 | 1.8 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — logger.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Централизованная система логирования.
    6 [docstring ] Устраняет проблему "Silent Failures" (B110).
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] import logging
   10 [import    ] from pathlib import Path
   11 [import    ] from logging.handlers import RotatingFileHandler
   12 [blank     ] 
   13 [def       ] def setup_logger(name: str, log_file: str = "app.log", level=logging.INFO):
   14 [docstring ]     """Настраивает профессиональный логгер с ротацией файлов."""
   15 [code      ]     log_dir = Path(__file__).resolve().parents[2] / "output" / "logs"
   16 [code      ]     log_dir.mkdir(parents=True, exist_ok=True)
   17 [blank     ]     
   18 [code      ]     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
   19 [blank     ] 
   20 [comment   ]     # v26: Ротация логов (макс 10MB, храним 5 файлов)
   21 [code      ]     file_handler = RotatingFileHandler(
   22 [code      ]         log_dir / log_file, 
   23 [code      ]         maxBytes=10*1024*1024, 
   24 [code      ]         backupCount=5, 
   25 [code      ]         encoding='utf-8'
   26 [code      ]     )
   27 [code      ]     file_handler.setFormatter(formatter)
   28 [blank     ] 
   29 [comment   ]     # Обработчик для консоли
   30 [code      ]     console_handler = logging.StreamHandler()
   31 [code      ]     console_handler.setFormatter(formatter)
   32 [blank     ] 
   33 [code      ]     logger = logging.getLogger(name)
   34 [code      ]     logger.setLevel(level)
   35 [blank     ]     
   36 [branch    ]     if not logger.handlers:
   37 [code      ]         logger.addHandler(file_handler)
   38 [code      ]         logger.addHandler(console_handler)
   39 [blank     ] 
   40 [return    ]     return logger
   41 [blank     ] 
   42 [comment   ] # Глобальный логгер по умолчанию
   43 [code      ] app_logger = setup_logger("ZS_Music_Maker")
   44 [blank     ] 
   45 [blank     ] 
   46 [def       ] def log_stage(logger, stage: str, event: str = "start", duration_ms=None, **extra):
   47 [docstring ]     """v39.4 (ШАГ 004): единый формат логов стадий — stage=/event=/duration_ms=."""
   48 [code      ]     parts = [f"stage={stage}", f"event={event}"]
   49 [branch    ]     if duration_ms is not None:
   50 [try_block ]         try:
   51 [code      ]             parts.append(f"duration_ms={int(round(float(duration_ms)))}")
   52 [try_block ]         except (TypeError, ValueError):
   53 [code      ]             parts.append(f"duration_ms={duration_ms}")
   54 [loop      ]     for k, v in extra.items():
   55 [code      ]         parts.append(f"{k}={v}")
   56 [code      ]     logger.info(" ".join(parts))
```