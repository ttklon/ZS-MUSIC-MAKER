# grep-таблицы `tests/test_data_inventory.py`

## `import` — 2 совпадений
```
    3 | from __future__ import annotations
    5 | from tools.audit_data_inventory import scan_data
```

## `def` — 2 совпадений
```
    8 | def test_repository_data_inventory_is_clean() -> None:
   16 | def test_inventory_reports_unknown_and_invalid_assets(tmp_path) -> None:
```

## `assert` — 6 совпадений
```
   11 |     assert report["files"]
   12 |     assert report["unknown"] == []
   13 |     assert report["invalid"] == []
   23 |     assert report["unknown"] == ["unmanaged.json"]
   24 |     assert report["invalid"][0]["path"] == "unmanaged.json"
   25 |     assert report["invalid"][0]["error"].startswith(
```
