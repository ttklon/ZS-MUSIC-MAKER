# -*- coding: utf-8 -*-
"""
ZS Music Maker — tools/ast_dead_imports.py (v39.5, ШАГ 010 PLAN_v39)
========================================================================
AST-аудит: находит top-level импорты, чьи имена нигде больше не
используются в модуле (аналог pyflakes F401 на чистом ast).

Правила:
  * import X  или  import X.Y  → tracked name = X (или asname)
  * from X import a, b         → tracked names = a, b (по отдельности)
  * строка с комментарием `# noqa: F401` / `# noqa:E401` — пропускается
  * относительные импорты (from . import …,  from ..x import …) не трогаем
  * динамические загрузки по строке (importlib/__import__) скрипт не видит —
    такие имена могут остаться, их надо чистить вручную с осторожностью

Использование:
    python tools/ast_dead_imports.py            # все каталоги
    python tools/ast_dead_imports.py app/core   # только каталог

Exit code: 0 если чисто, 1 если есть кандидаты.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRS = ["app", "modules", "agents", "tools", "ui", "updater"]
EXTRA_FILES = ["main.py", "install.py"]

NOQA_RE = "# noqa"


def _top_level_imports(tree: ast.AST, source_lines: list[str]) -> list[tuple[int, str]]:
    """Возвращает [(lineno, tracked_name)] для топ-левел импортов."""
    out: list[tuple[int, str]] = []
    for node in tree.body:
        line_txt = source_lines[node.lineno - 1] if node.lineno <= len(source_lines) else ""
        if NOQA_RE in line_txt:
            continue
        if isinstance(node, ast.Import):
            for a in node.names:
                name = a.asname or a.name.split(".")[0]
                out.append((node.lineno, name))
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative
                continue
            if node.module and node.module.split(".")[0] == "__future__":
                continue
            if any(isinstance(a, ast.alias) and a.name == "*" for a in node.names):
                continue
            for a in node.names:
                out.append((node.lineno, a.asname or a.name))
    return out


def _used_names_and_attr_roots(tree: ast.AST) -> set[str]:
    """Все Name-идентификаторы + корни Attribute-цепочек (os.path → os)."""
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            used.add(node.value.id)
    return used


def scan_file(path: Path) -> list[tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except SyntaxError:
        return []
    source_lines = text.splitlines()
    imports = _top_level_imports(tree, source_lines)
    used = _used_names_and_attr_roots(tree)
    dead = [(ln, name) for ln, name in imports if name not in used]
    return dead


def scan_all(dirs: list[str]) -> dict[str, list[tuple[int, str]]]:
    report: dict[str, list[tuple[int, str]]] = {}
    files: list[Path] = []
    for d in dirs:
        base = ROOT / d
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            files.append(p)
    for f in EXTRA_FILES:
        p = ROOT / f
        if p.exists():
            files.append(p)
    total = 0
    for f in files:
        dead = scan_file(f)
        if dead:
            rel = str(f.relative_to(ROOT))
            report[rel] = dead
            total += len(dead)
    return report


def main() -> int:
    dirs = sys.argv[1:] or DEFAULT_DIRS
    report = scan_all(dirs)
    if not report:
        print("AST dead-imports: CLEAN (0)")
        return 0
    print("AST dead-imports: FOUND")
    total = 0
    for rel, items in sorted(report.items()):
        for lineno, name in items:
            print(f"  {rel}:{lineno}  {name}")
            total += 1
    print(f"total: {total}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
