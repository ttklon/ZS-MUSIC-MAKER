# grep-таблицы `tools/ast_dead_imports.py`

## `import` — 4 совпадений
```
   22 | from __future__ import annotations
   24 | import ast
   25 | import sys
   26 | from pathlib import Path
```

## `print` — 4 совпадений
```
  111 |         print("AST dead-imports: CLEAN (0)")
  113 |     print("AST dead-imports: FOUND")
  117 |             print(f"  {rel}:{lineno}  {name}")
  119 |     print(f"total: {total}")
```

## `except` — 1 совпадений
```
   73 |     except SyntaxError:
```

## `try` — 1 совпадений
```
   70 |     try:
```

## `def` — 5 совпадений
```
   35 | def _top_level_imports(tree: ast.AST, source_lines: list[str]) -> list[tuple[int, str]]:
   58 | def _used_names_and_attr_roots(tree: ast.AST) -> set[str]:
   69 | def scan_file(path: Path) -> list[tuple[int, str]]:
   82 | def scan_all(dirs: list[str]) -> dict[str, list[tuple[int, str]]]:
  107 | def main() -> int:
```

## `return` — 7 совпадений
```
   55 |     return out
   66 |     return used
   74 |         return []
   79 |     return dead
  104 |     return report
  112 |         return 0
  120 |     return 1
```

## `if` — 12 совпадений
```
   40 |         if NOQA_RE in line_txt:
   42 |         if isinstance(node, ast.Import):
   47 |             if node.level:  # relative
   49 |             if node.module and node.module.split(".")[0] == "__future__":
   51 |             if any(isinstance(a, ast.alias) and a.name == "*" for a in node.names):
   62 |         if isinstance(node, ast.Name):
   87 |         if not base.exists():
   90 |             if "__pycache__" in p.parts:
   95 |         if p.exists():
  100 |         if dead:
  110 |     if not report:
  123 | if __name__ == "__main__":
```

## `for` — 10 совпадений
```
   38 |     for node in tree.body:
   43 |             for a in node.names:
   53 |             for a in node.names:
   61 |     for node in ast.walk(tree):
   85 |     for d in dirs:
   89 |         for p in sorted(base.rglob("*.py")):
   93 |     for f in EXTRA_FILES:
   98 |     for f in files:
  115 |     for rel, items in sorted(report.items()):
  116 |         for lineno, name in items:
```
