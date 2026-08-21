# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_font_utils.py`

**Всего строк:** 29

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| blank | 9 | 31.0 |
| stmt | 6 | 20.7 |
| code | 5 | 17.2 |
| def | 4 | 13.8 |
| comment | 2 | 6.9 |
| import | 2 | 6.9 |
| docstring | 1 | 3.4 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker — tests for app/core/font_utils (ШАГ 002)."""
    3 [import    ] from __future__ import annotations
    4 [blank     ] 
    5 [import    ] from app.core import font_utils as F
    6 [blank     ] 
    7 [blank     ] 
    8 [def       ] def test_candidates_non_empty():
    9 [code      ]     cands = F.font_candidates(bold=True)
   10 [stmt      ]     assert isinstance(cands, list)
   11 [stmt      ]     assert cands  # хотя бы 1
   12 [comment   ]     # никаких дублей
   13 [stmt      ]     assert len(cands) == len(set(cands))
   14 [blank     ] 
   15 [blank     ] 
   16 [def       ] def test_candidates_regular_variant():
   17 [code      ]     cands = F.font_candidates(bold=False)
   18 [stmt      ]     assert cands
   19 [blank     ] 
   20 [blank     ] 
   21 [def       ] def test_env_override(monkeypatch):
   22 [code      ]     monkeypatch.setenv("ZSMM_FONT_PATH", "/custom/font.ttf")
   23 [code      ]     cands = F.font_candidates(bold=True)
   24 [stmt      ]     assert cands[0] == "/custom/font.ttf"
   25 [blank     ] 
   26 [blank     ] 
   27 [def       ] def test_load_pil_font_returns_something():
   28 [code      ]     f = F.load_pil_font(24, bold=True)
   29 [stmt      ]     assert f is not None
```