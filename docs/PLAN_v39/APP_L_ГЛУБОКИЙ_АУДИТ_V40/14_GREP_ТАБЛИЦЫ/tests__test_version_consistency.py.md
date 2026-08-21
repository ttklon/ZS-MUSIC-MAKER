# grep-таблицы `tests/test_version_consistency.py`

## `import` — 7 совпадений
```
    3 | from __future__ import annotations
    5 | import json
    6 | import subprocess
    7 | import sys
    8 | from pathlib import Path
   15 |         import tomllib
   26 |     from app.version_info import __version__
```

## `except` — 2 совпадений
```
   16 |     except ImportError:
   20 |     except Exception:
```

## `try` — 2 совпадений
```
   14 |     try:
   18 |     try:
```

## `def` — 7 совпадений
```
   13 | def _version_from_pyproject() -> str | None:
   25 | def _version_from_app() -> str:
   31 | def test_version_json_matches_app_version_info():
   36 | def test_pyproject_static_version_if_present_matches():
   43 | def test_cli_version_exit_zero():
   52 | def test_cli_version_shows_config_path():
   61 | def test_build_id_mentions_version():
```

## `return` — 4 совпадений
```
   17 |         return None
   21 |         return None
   22 |     return data.get("project", {}).get("version")
   28 |     return __version__
```

## `if` — 1 совпадений
```
   39 |     if pv is not None:
```

## `assert` — 7 совпадений
```
   33 |     assert vj == _version_from_app()
   40 |         assert vj == pv
   48 |     assert r.returncode == 0
   49 |     assert "version" in (r.stdout + r.stderr).lower()
   57 |     assert r.returncode == 0
   58 |     assert "config" in (r.stdout + r.stderr)
   64 |     assert build.startswith("v" + data["version"].split(".")[0])
```

## `subprocess` — 2 совпадений
```
   44 |     r = subprocess.run(
   53 |     r = subprocess.run(
```
