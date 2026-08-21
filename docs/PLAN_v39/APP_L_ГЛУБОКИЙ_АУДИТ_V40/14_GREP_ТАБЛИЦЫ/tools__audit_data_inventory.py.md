# grep-таблицы `tools/audit_data_inventory.py`

## `import` — 5 совпадений
```
   12 | from __future__ import annotations
   14 | import argparse
   15 | import json
   16 | from pathlib import Path
   17 | from typing import Any
```

## `print` — 4 совпадений
```
  120 |         print(json.dumps(report, ensure_ascii=False, indent=2))
  122 |         print(
  128 |             print(f"INVALID {entry['path']}: {entry['error']}")
  130 |             print(f"UNKNOWN {path}")
```

## `except` — 2 совпадений
```
   56 |         except json.JSONDecodeError as exc:
   73 |     except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
```

## `try` — 2 совпадений
```
   54 |         try:
   63 |     try:
```

## `def` — 5 совпадений
```
   40 | def classify_data_file(path: Path, data_dir: Path = DATA_DIR) -> str | None:
   50 | def _validate_jsonl(path: Path) -> tuple[bool, str | None]:
   61 | def validate_data_file(path: Path) -> tuple[bool, str | None]:
   78 | def scan_data(data_dir: Path = DATA_DIR) -> dict[str, Any]:
  113 | def main(argv: list[str] | None = None) -> int:
```

## `raise` — 1 совпадений
```
  136 |     raise SystemExit(main())
```

## `return` — 13 совпадений
```
   44 |         return MANAGED_FILES[relative.name]
   46 |         return MANAGED_DIRECTORIES[relative.parts[0]]
   47 |     return None
   57 |             return False, f"line {number}: {exc.msg}"
   58 |     return True, None
   65 |             return True, None
   69 |             return _validate_jsonl(path)
   72 |                 return False, "empty text asset"
   74 |         return False, str(exc)
   75 |     return True, None
   85 |         return {"data_dir": str(data_dir), "files": entries, "unknown": [], "invalid": []}
  104 |     return {
  132 |     return 0 if not report["unknown"] and not report["invalid"] else 1
```

## `if` — 11 совпадений
```
   43 |     if relative.name in MANAGED_FILES:
   45 |     if relative.parts and relative.parts[0] in MANAGED_DIRECTORIES:
   52 |         if not line.strip():
   64 |         if path.name == ".gitkeep":
   66 |         if path.suffix == ".json":
   71 |             if not path.read_text(encoding="utf-8").strip():
   84 |     if not data_dir.exists():
   99 |         if purpose is None:
  101 |         if not valid:
  119 |     if args.json:
  135 | if __name__ == "__main__":
```

## `for` — 4 совпадений
```
   51 |     for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
   87 |     for path in sorted(item for item in data_dir.rglob("*") if item.is_file()):
  127 |         for entry in report["invalid"]:
  129 |         for path in report["unknown"]:
```
