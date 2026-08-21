# ПОСТРОЧНЫЙ ЛИСТИНГ: `updater/__init__.py`

**Всего строк:** 27

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 23 | 85.2 |
| blank | 2 | 7.4 |
| docstring | 1 | 3.7 |
| import | 1 | 3.7 |

## Полный листинг с классификацией
```
    1 [docstring ] """ZS Music Maker updater package — TZ P0.10..P0.13."""
    2 [blank     ] 
    3 [import    ] from .updater import (
    4 [code      ]     USER_PRESERVED,
    5 [code      ]     check_updates,
    6 [code      ]     ensure_user_dirs,
    7 [code      ]     install_from_zip,
    8 [code      ]     list_backups,
    9 [code      ]     make_backup,
   10 [code      ]     program_dir,
   11 [code      ]     rollback_last,
   12 [code      ]     user_data_dir,
   13 [code      ]     verify_zip,
   14 [code      ] )
   15 [blank     ] 
   16 [code      ] __all__ = [
   17 [code      ]     "USER_PRESERVED",
   18 [code      ]     "check_updates",
   19 [code      ]     "ensure_user_dirs",
   20 [code      ]     "install_from_zip",
   21 [code      ]     "list_backups",
   22 [code      ]     "make_backup",
   23 [code      ]     "program_dir",
   24 [code      ]     "rollback_last",
   25 [code      ]     "user_data_dir",
   26 [code      ]     "verify_zip",
   27 [code      ] ]
```