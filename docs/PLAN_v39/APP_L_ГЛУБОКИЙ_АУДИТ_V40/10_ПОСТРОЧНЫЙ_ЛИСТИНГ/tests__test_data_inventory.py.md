# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_data_inventory.py`

**Всего строк:** 27

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| blank | 8 | 29.6 |
| code | 7 | 25.9 |
| stmt | 6 | 22.2 |
| import | 2 | 7.4 |
| def | 2 | 7.4 |
| comment | 1 | 3.7 |
| docstring | 1 | 3.7 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """Регрессии для versioned-каталога data и его статического аудита."""
    3 [import    ] from __future__ import annotations
    4 [blank     ] 
    5 [import    ] from tools.audit_data_inventory import scan_data
    6 [blank     ] 
    7 [blank     ] 
    8 [def       ] def test_repository_data_inventory_is_clean() -> None:
    9 [code      ]     report = scan_data()
   10 [blank     ] 
   11 [stmt      ]     assert report["files"]
   12 [stmt      ]     assert report["unknown"] == []
   13 [stmt      ]     assert report["invalid"] == []
   14 [blank     ] 
   15 [blank     ] 
   16 [def       ] def test_inventory_reports_unknown_and_invalid_assets(tmp_path) -> None:
   17 [code      ]     (tmp_path / "genre_presets").mkdir()
   18 [code      ]     (tmp_path / "genre_presets" / "valid.json").write_text("{}", encoding="utf-8")
   19 [code      ]     (tmp_path / "unmanaged.json").write_text("{broken", encoding="utf-8")
   20 [blank     ] 
   21 [code      ]     report = scan_data(tmp_path)
   22 [blank     ] 
   23 [stmt      ]     assert report["unknown"] == ["unmanaged.json"]
   24 [stmt      ]     assert report["invalid"][0]["path"] == "unmanaged.json"
   25 [stmt      ]     assert report["invalid"][0]["error"].startswith(
   26 [code      ]         "Expecting property name enclosed in double quotes"
   27 [code      ]     )
```