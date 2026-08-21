# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/version_info.py`

**Всего строк:** 14

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| docstring | 7 | 50.0 |
| code | 3 | 21.4 |
| import | 2 | 14.3 |
| comment | 1 | 7.1 |
| blank | 1 | 7.1 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — app/version_info.py (v39.5, ШАГ 009 PLAN_v39)
    4 [docstring ] ========================================================================
    5 [docstring ] Единый источник версии: читает version.json ПО ОДНОМУ РАЗУ при импорте.
    6 [docstring ] pyproject.toml ссылается на этот атрибут через [tool.setuptools.dynamic],
    7 [docstring ] main.py уже читает version.json напрямую — расхождений быть не может.
    8 [docstring ] """
    9 [import    ] import json
   10 [import    ] from pathlib import Path
   11 [blank     ] 
   12 [code      ] __version__: str = json.loads(
   13 [code      ]     (Path(__file__).resolve().parents[1] / "version.json").read_text(encoding="utf-8")
   14 [code      ] )["version"]
```