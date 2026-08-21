# grep-таблицы `tests/test_ast_dead_imports.py`

## `import` — 4 совпадений
```
    3 | from __future__ import annotations
    5 | import sys
    6 | from pathlib import Path
   10 | from tools.ast_dead_imports import DEFAULT_DIRS, scan_all, scan_file  # noqa: E402
```

## `def` — 5 совпадений
```
   13 | def test_scan_finds_dead_import(tmp_path):
   22 | def test_scan_ignores_noqa_import(tmp_path):
   29 | def test_scan_keeps_attr_root(tmp_path):
   38 | def test_scan_line_with_two_imports(tmp_path):
   47 | def test_repo_is_clean_of_dead_imports():
```

## `assert` — 7 совпадений
```
   18 |     assert "os" in names
   19 |     assert "json" not in names
   26 |     assert dead == []
   34 |     assert "os" not in names
   35 |     assert "json" in names
   44 |     assert {"os", "sys"} <= names
   49 |     assert report == {}, f"dead imports found: {report}"
```
