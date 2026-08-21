# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_version_consistency.py`

**Всего строк:** 64

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| blank | 17 | 26.6 |
| code | 15 | 23.4 |
| import | 7 | 10.9 |
| def | 7 | 10.9 |
| stmt | 7 | 10.9 |
| try_block | 4 | 6.2 |
| return | 4 | 6.2 |
| comment | 1 | 1.6 |
| docstring | 1 | 1.6 |
| branch | 1 | 1.6 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker — единый источник версии (ШАГ 009)."""
    3 [import    ] from __future__ import annotations
    4 [blank     ] 
    5 [import    ] import json
    6 [import    ] import subprocess
    7 [import    ] import sys
    8 [import    ] from pathlib import Path
    9 [blank     ] 
   10 [code      ] ROOT = Path(__file__).resolve().parents[1]
   11 [blank     ] 
   12 [blank     ] 
   13 [def       ] def _version_from_pyproject() -> str | None:
   14 [try_block ]     try:
   15 [import    ]         import tomllib
   16 [try_block ]     except ImportError:
   17 [return    ]         return None
   18 [try_block ]     try:
   19 [code      ]         data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
   20 [try_block ]     except Exception:
   21 [return    ]         return None
   22 [return    ]     return data.get("project", {}).get("version")
   23 [blank     ] 
   24 [blank     ] 
   25 [def       ] def _version_from_app() -> str:
   26 [import    ]     from app.version_info import __version__
   27 [blank     ] 
   28 [return    ]     return __version__
   29 [blank     ] 
   30 [blank     ] 
   31 [def       ] def test_version_json_matches_app_version_info():
   32 [code      ]     vj = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"]
   33 [stmt      ]     assert vj == _version_from_app()
   34 [blank     ] 
   35 [blank     ] 
   36 [def       ] def test_pyproject_static_version_if_present_matches():
   37 [code      ]     vj = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"]
   38 [code      ]     pv = _version_from_pyproject()
   39 [branch    ]     if pv is not None:
   40 [stmt      ]         assert vj == pv
   41 [blank     ] 
   42 [blank     ] 
   43 [def       ] def test_cli_version_exit_zero():
   44 [code      ]     r = subprocess.run(
   45 [code      ]         [sys.executable, str(ROOT / "main.py"), "--version"],
   46 [code      ]         capture_output=True, text=True, timeout=180,
   47 [code      ]     )
   48 [stmt      ]     assert r.returncode == 0
   49 [stmt      ]     assert "version" in (r.stdout + r.stderr).lower()
   50 [blank     ] 
   51 [blank     ] 
   52 [def       ] def test_cli_version_shows_config_path():
   53 [code      ]     r = subprocess.run(
   54 [code      ]         [sys.executable, str(ROOT / "main.py"), "--version"],
   55 [code      ]         capture_output=True, text=True, timeout=180,
   56 [code      ]     )
   57 [stmt      ]     assert r.returncode == 0
   58 [stmt      ]     assert "config" in (r.stdout + r.stderr)
   59 [blank     ] 
   60 [blank     ] 
   61 [def       ] def test_build_id_mentions_version():
   62 [code      ]     data = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
   63 [code      ]     build = data.get("build", "")
   64 [stmt      ]     assert build.startswith("v" + data["version"].split(".")[0])
```