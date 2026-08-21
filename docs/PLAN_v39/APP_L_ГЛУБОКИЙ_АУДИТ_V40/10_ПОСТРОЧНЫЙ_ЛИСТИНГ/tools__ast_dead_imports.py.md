# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/ast_dead_imports.py`

**Всего строк:** 124

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 44 | 35.5 |
| docstring | 19 | 15.3 |
| blank | 18 | 14.5 |
| branch | 14 | 11.3 |
| loop | 10 | 8.1 |
| return | 7 | 5.6 |
| def | 5 | 4.0 |
| import | 4 | 3.2 |
| try_block | 2 | 1.6 |
| comment | 1 | 0.8 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — tools/ast_dead_imports.py (v39.5, ШАГ 010 PLAN_v39)
    4 [docstring ] ========================================================================
    5 [docstring ] AST-аудит: находит top-level импорты, чьи имена нигде больше не
    6 [docstring ] используются в модуле (аналог pyflakes F401 на чистом ast).
    7 [blank     ] 
    8 [docstring ] Правила:
    9 [docstring ]   * import X  или  import X.Y  → tracked name = X (или asname)
   10 [docstring ]   * from X import a, b         → tracked names = a, b (по отдельности)
   11 [docstring ]   * строка с комментарием `# noqa: F401` / `# noqa:E401` — пропускается
   12 [docstring ]   * относительные импорты (from . import …,  from ..x import …) не трогаем
   13 [docstring ]   * динамические загрузки по строке (importlib/__import__) скрипт не видит —
   14 [docstring ]     такие имена могут остаться, их надо чистить вручную с осторожностью
   15 [blank     ] 
   16 [docstring ] Использование:
   17 [docstring ]     python tools/ast_dead_imports.py            # все каталоги
   18 [docstring ]     python tools/ast_dead_imports.py app/core   # только каталог
   19 [blank     ] 
   20 [docstring ] Exit code: 0 если чисто, 1 если есть кандидаты.
   21 [docstring ] """
   22 [import    ] from __future__ import annotations
   23 [blank     ] 
   24 [import    ] import ast
   25 [import    ] import sys
   26 [import    ] from pathlib import Path
   27 [blank     ] 
   28 [code      ] ROOT = Path(__file__).resolve().parents[1]
   29 [code      ] DEFAULT_DIRS = ["app", "modules", "agents", "tools", "ui", "updater"]
   30 [code      ] EXTRA_FILES = ["main.py", "install.py"]
   31 [blank     ] 
   32 [code      ] NOQA_RE = "# noqa"
   33 [blank     ] 
   34 [blank     ] 
   35 [def       ] def _top_level_imports(tree: ast.AST, source_lines: list[str]) -> list[tuple[int, str]]:
   36 [docstring ]     """Возвращает [(lineno, tracked_name)] для топ-левел импортов."""
   37 [code      ]     out: list[tuple[int, str]] = []
   38 [loop      ]     for node in tree.body:
   39 [code      ]         line_txt = source_lines[node.lineno - 1] if node.lineno <= len(source_lines) else ""
   40 [branch    ]         if NOQA_RE in line_txt:
   41 [code      ]             continue
   42 [branch    ]         if isinstance(node, ast.Import):
   43 [loop      ]             for a in node.names:
   44 [code      ]                 name = a.asname or a.name.split(".")[0]
   45 [code      ]                 out.append((node.lineno, name))
   46 [branch    ]         elif isinstance(node, ast.ImportFrom):
   47 [branch    ]             if node.level:  # relative
   48 [code      ]                 continue
   49 [branch    ]             if node.module and node.module.split(".")[0] == "__future__":
   50 [code      ]                 continue
   51 [branch    ]             if any(isinstance(a, ast.alias) and a.name == "*" for a in node.names):
   52 [code      ]                 continue
   53 [loop      ]             for a in node.names:
   54 [code      ]                 out.append((node.lineno, a.asname or a.name))
   55 [return    ]     return out
   56 [blank     ] 
   57 [blank     ] 
   58 [def       ] def _used_names_and_attr_roots(tree: ast.AST) -> set[str]:
   59 [docstring ]     """Все Name-идентификаторы + корни Attribute-цепочек (os.path → os)."""
   60 [code      ]     used: set[str] = set()
   61 [loop      ]     for node in ast.walk(tree):
   62 [branch    ]         if isinstance(node, ast.Name):
   63 [code      ]             used.add(node.id)
   64 [branch    ]         elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
   65 [code      ]             used.add(node.value.id)
   66 [return    ]     return used
   67 [blank     ] 
   68 [blank     ] 
   69 [def       ] def scan_file(path: Path) -> list[tuple[int, str]]:
   70 [try_block ]     try:
   71 [code      ]         text = path.read_text(encoding="utf-8")
   72 [code      ]         tree = ast.parse(text)
   73 [try_block ]     except SyntaxError:
   74 [return    ]         return []
   75 [code      ]     source_lines = text.splitlines()
   76 [code      ]     imports = _top_level_imports(tree, source_lines)
   77 [code      ]     used = _used_names_and_attr_roots(tree)
   78 [code      ]     dead = [(ln, name) for ln, name in imports if name not in used]
   79 [return    ]     return dead
   80 [blank     ] 
   81 [blank     ] 
   82 [def       ] def scan_all(dirs: list[str]) -> dict[str, list[tuple[int, str]]]:
   83 [code      ]     report: dict[str, list[tuple[int, str]]] = {}
   84 [code      ]     files: list[Path] = []
   85 [loop      ]     for d in dirs:
   86 [code      ]         base = ROOT / d
   87 [branch    ]         if not base.exists():
   88 [code      ]             continue
   89 [loop      ]         for p in sorted(base.rglob("*.py")):
   90 [branch    ]             if "__pycache__" in p.parts:
   91 [code      ]                 continue
   92 [code      ]             files.append(p)
   93 [loop      ]     for f in EXTRA_FILES:
   94 [code      ]         p = ROOT / f
   95 [branch    ]         if p.exists():
   96 [code      ]             files.append(p)
   97 [code      ]     total = 0
   98 [loop      ]     for f in files:
   99 [code      ]         dead = scan_file(f)
  100 [branch    ]         if dead:
  101 [code      ]             rel = str(f.relative_to(ROOT))
  102 [code      ]             report[rel] = dead
  103 [code      ]             total += len(dead)
  104 [return    ]     return report
  105 [blank     ] 
  106 [blank     ] 
  107 [def       ] def main() -> int:
  108 [code      ]     dirs = sys.argv[1:] or DEFAULT_DIRS
  109 [code      ]     report = scan_all(dirs)
  110 [branch    ]     if not report:
  111 [code      ]         print("AST dead-imports: CLEAN (0)")
  112 [return    ]         return 0
  113 [code      ]     print("AST dead-imports: FOUND")
  114 [code      ]     total = 0
  115 [loop      ]     for rel, items in sorted(report.items()):
  116 [loop      ]         for lineno, name in items:
  117 [code      ]             print(f"  {rel}:{lineno}  {name}")
  118 [code      ]             total += 1
  119 [code      ]     print(f"total: {total}")
  120 [return    ]     return 1
  121 [blank     ] 
  122 [blank     ] 
  123 [branch    ] if __name__ == "__main__":
  124 [code      ]     sys.exit(main())
```