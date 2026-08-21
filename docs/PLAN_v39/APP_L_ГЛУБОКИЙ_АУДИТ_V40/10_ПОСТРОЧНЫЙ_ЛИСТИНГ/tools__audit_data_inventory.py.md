# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/audit_data_inventory.py`

**Всего строк:** 136

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 53 | 39.0 |
| blank | 23 | 16.9 |
| branch | 14 | 10.3 |
| return | 13 | 9.6 |
| docstring | 11 | 8.1 |
| import | 5 | 3.7 |
| def | 5 | 3.7 |
| loop | 4 | 2.9 |
| try_block | 4 | 2.9 |
| comment | 3 | 2.2 |
| raise | 1 | 0.7 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """Аудит versioned-данных ZS Music Maker.
    3 [blank     ] 
    4 [docstring ] Инструмент читает каждый файл из ``data/``, валидирует его формат и относит
    5 [docstring ] к явной категории жизненного цикла. Это предотвращает незаметное накопление
    6 [docstring ] нечитаемых seed-ов, тестовых manifest-ов и кэшей между релизами.
    7 [blank     ] 
    8 [docstring ] Запуск:
    9 [docstring ]     python tools/audit_data_inventory.py
   10 [docstring ]     python tools/audit_data_inventory.py --json
   11 [docstring ] """
   12 [import    ] from __future__ import annotations
   13 [blank     ] 
   14 [import    ] import argparse
   15 [import    ] import json
   16 [import    ] from pathlib import Path
   17 [import    ] from typing import Any
   18 [blank     ] 
   19 [blank     ] 
   20 [code      ] ROOT = Path(__file__).resolve().parents[1]
   21 [code      ] DATA_DIR = ROOT / "data"
   22 [blank     ] 
   23 [comment   ] # Каталоги содержат versioned assets, которые загружаются по glob или служат
   24 [comment   ] # проверяемыми seed/fixture-данными для соответствующих runtime-компонентов.
   25 [code      ] MANAGED_DIRECTORIES = {
   26 [code      ]     "genre_presets": "genre preset catalog",
   27 [code      ]     "kpi_history_seed": "KPI schema seed",
   28 [code      ]     "prompts": "prompt catalog",
   29 [code      ]     "reference_cache": "reference-analysis cache fixture",
   30 [code      ]     "sample_manifests": "sample manifest fixture",
   31 [code      ] }
   32 [code      ] MANAGED_FILES = {
   33 [code      ]     "README.md": "data catalog documentation",
   34 [code      ]     "tutorial_settings.json": "onboarding settings",
   35 [code      ]     "hw_profile.json": "hardware profile seed",
   36 [code      ]     ".gitkeep": "directory retention marker",
   37 [code      ] }
   38 [blank     ] 
   39 [blank     ] 
   40 [def       ] def classify_data_file(path: Path, data_dir: Path = DATA_DIR) -> str | None:
   41 [docstring ]     """Вернуть назначение versioned data-файла или ``None`` для неизвестного."""
   42 [code      ]     relative = path.relative_to(data_dir)
   43 [branch    ]     if relative.name in MANAGED_FILES:
   44 [return    ]         return MANAGED_FILES[relative.name]
   45 [branch    ]     if relative.parts and relative.parts[0] in MANAGED_DIRECTORIES:
   46 [return    ]         return MANAGED_DIRECTORIES[relative.parts[0]]
   47 [return    ]     return None
   48 [blank     ] 
   49 [blank     ] 
   50 [def       ] def _validate_jsonl(path: Path) -> tuple[bool, str | None]:
   51 [loop      ]     for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
   52 [branch    ]         if not line.strip():
   53 [code      ]             continue
   54 [try_block ]         try:
   55 [code      ]             json.loads(line)
   56 [try_block ]         except json.JSONDecodeError as exc:
   57 [return    ]             return False, f"line {number}: {exc.msg}"
   58 [return    ]     return True, None
   59 [blank     ] 
   60 [blank     ] 
   61 [def       ] def validate_data_file(path: Path) -> tuple[bool, str | None]:
   62 [docstring ]     """Проверить кодировку и формат поддерживаемого versioned data-файла."""
   63 [try_block ]     try:
   64 [branch    ]         if path.name == ".gitkeep":
   65 [return    ]             return True, None
   66 [branch    ]         if path.suffix == ".json":
   67 [code      ]             json.loads(path.read_text(encoding="utf-8"))
   68 [branch    ]         elif path.suffix == ".jsonl":
   69 [return    ]             return _validate_jsonl(path)
   70 [branch    ]         else:
   71 [branch    ]             if not path.read_text(encoding="utf-8").strip():
   72 [return    ]                 return False, "empty text asset"
   73 [try_block ]     except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
   74 [return    ]         return False, str(exc)
   75 [return    ]     return True, None
   76 [blank     ] 
   77 [blank     ] 
   78 [def       ] def scan_data(data_dir: Path = DATA_DIR) -> dict[str, Any]:
   79 [docstring ]     """Прочитать все файлы data/ и вернуть машиночитаемый инвентаризационный отчёт."""
   80 [code      ]     entries: list[dict[str, Any]] = []
   81 [code      ]     unknown: list[str] = []
   82 [code      ]     invalid: list[dict[str, str]] = []
   83 [blank     ] 
   84 [branch    ]     if not data_dir.exists():
   85 [return    ]         return {"data_dir": str(data_dir), "files": entries, "unknown": [], "invalid": []}
   86 [blank     ] 
   87 [loop      ]     for path in sorted(item for item in data_dir.rglob("*") if item.is_file()):
   88 [code      ]         purpose = classify_data_file(path, data_dir)
   89 [code      ]         valid, error = validate_data_file(path)
   90 [code      ]         relative = path.relative_to(data_dir).as_posix()
   91 [code      ]         entry = {
   92 [code      ]             "path": relative,
   93 [code      ]             "purpose": purpose,
   94 [code      ]             "bytes": path.stat().st_size,
   95 [code      ]             "valid": valid,
   96 [code      ]             "error": error,
   97 [code      ]         }
   98 [code      ]         entries.append(entry)
   99 [branch    ]         if purpose is None:
  100 [code      ]             unknown.append(relative)
  101 [branch    ]         if not valid:
  102 [code      ]             invalid.append({"path": relative, "error": error or "invalid"})
  103 [blank     ] 
  104 [return    ]     return {
  105 [code      ]         "data_dir": str(data_dir),
  106 [code      ]         "files": entries,
  107 [code      ]         "managed_count": len(entries) - len(unknown),
  108 [code      ]         "unknown": unknown,
  109 [code      ]         "invalid": invalid,
  110 [code      ]     }
  111 [blank     ] 
  112 [blank     ] 
  113 [def       ] def main(argv: list[str] | None = None) -> int:
  114 [code      ]     parser = argparse.ArgumentParser(description="Validate and inventory versioned data assets")
  115 [code      ]     parser.add_argument("--json", action="store_true", help="print the complete report as JSON")
  116 [code      ]     args = parser.parse_args(argv)
  117 [code      ]     report = scan_data()
  118 [blank     ] 
  119 [branch    ]     if args.json:
  120 [code      ]         print(json.dumps(report, ensure_ascii=False, indent=2))
  121 [branch    ]     else:
  122 [code      ]         print(
  123 [code      ]             "data inventory: "
  124 [code      ]             f"files={len(report['files'])} managed={report['managed_count']} "
  125 [code      ]             f"unknown={len(report['unknown'])} invalid={len(report['invalid'])}"
  126 [code      ]         )
  127 [loop      ]         for entry in report["invalid"]:
  128 [code      ]             print(f"INVALID {entry['path']}: {entry['error']}")
  129 [loop      ]         for path in report["unknown"]:
  130 [code      ]             print(f"UNKNOWN {path}")
  131 [blank     ] 
  132 [return    ]     return 0 if not report["unknown"] and not report["invalid"] else 1
  133 [blank     ] 
  134 [blank     ] 
  135 [branch    ] if __name__ == "__main__":
  136 [raise     ]     raise SystemExit(main())
```