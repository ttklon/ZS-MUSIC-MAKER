# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_ast_dead_imports.py`

**Всего строк:** 49

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 17 | 34.7 |
| blank | 13 | 26.5 |
| stmt | 7 | 14.3 |
| def | 5 | 10.2 |
| import | 4 | 8.2 |
| comment | 2 | 4.1 |
| docstring | 1 | 2.0 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker — AST dead-imports аудит (ШАГ 010)."""
    3 [import    ] from __future__ import annotations
    4 [blank     ] 
    5 [import    ] import sys
    6 [import    ] from pathlib import Path
    7 [blank     ] 
    8 [code      ] sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    9 [blank     ] 
   10 [import    ] from tools.ast_dead_imports import DEFAULT_DIRS, scan_all, scan_file  # noqa: E402
   11 [blank     ] 
   12 [blank     ] 
   13 [def       ] def test_scan_finds_dead_import(tmp_path):
   14 [code      ]     f = tmp_path / "m.py"
   15 [code      ]     f.write_text("import os\nimport json\nx = json.dumps({})\n", encoding="utf-8")
   16 [code      ]     dead = scan_file(f)
   17 [code      ]     names = {n for _, n in dead}
   18 [stmt      ]     assert "os" in names
   19 [stmt      ]     assert "json" not in names
   20 [blank     ] 
   21 [blank     ] 
   22 [def       ] def test_scan_ignores_noqa_import(tmp_path):
   23 [code      ]     f = tmp_path / "m.py"
   24 [code      ]     f.write_text("import os  # noqa: F401\nx = 1\n", encoding="utf-8")
   25 [code      ]     dead = scan_file(f)
   26 [stmt      ]     assert dead == []
   27 [blank     ] 
   28 [blank     ] 
   29 [def       ] def test_scan_keeps_attr_root(tmp_path):
   30 [code      ]     f = tmp_path / "m.py"
   31 [code      ]     f.write_text("import os\np = os.path.join('a', 'b')\nimport json\n", encoding="utf-8")
   32 [code      ]     dead = scan_file(f)
   33 [code      ]     names = {n for _, n in dead}
   34 [stmt      ]     assert "os" not in names
   35 [stmt      ]     assert "json" in names
   36 [blank     ] 
   37 [blank     ] 
   38 [def       ] def test_scan_line_with_two_imports(tmp_path):
   39 [comment   ]     # `import os, sys` на одной строке — оба должны быть учтены
   40 [code      ]     f = tmp_path / "m.py"
   41 [code      ]     f.write_text("import os, sys\nx = 1\n", encoding="utf-8")
   42 [code      ]     dead = scan_file(f)
   43 [code      ]     names = {n for _, n in dead}
   44 [stmt      ]     assert {"os", "sys"} <= names
   45 [blank     ] 
   46 [blank     ] 
   47 [def       ] def test_repo_is_clean_of_dead_imports():
   48 [code      ]     report = scan_all(DEFAULT_DIRS)
   49 [stmt      ]     assert report == {}, f"dead imports found: {report}"
```