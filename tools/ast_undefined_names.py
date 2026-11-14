# -*- coding: utf-8 -*-
"""
ZS Music Maker — tools/ast_undefined_names.py
=============================================
Ищет имена, которые используются, но нигде не определены: ни в функции, ни во
внешней области модуля, ни среди встроенных.

Зачем отдельный инструмент. За один разбор нашлось четыре дефекта одного класса:
`_safe_print` в `modules/video_edit/audio.py`, `_parse_lrc` в `render.py`,
`asdict` в `models.py`, `normalize_master_loudness` в
`modules/mastering_reference.py`. Все они — `NameError` в рантайме, и все
выживали, потому что вызов сидел внутри широкого `except Exception` или в
ветке, которая на этой машине не выполнялась. `pyflakes` их видит, но он не
зависимость проекта; `tools/ast_dead_imports.py` проверяет обратное (импорт без
использования) и такой случай пропускает.

Как считается. Настоящий Python-компилятор даёт таблицу имён (`symtable`):
символ со `is_global()` и `is_referenced()` — это имя, которое ищут в модуле и
во встроенных. Если его нет среди имён, связанных на уровне модуля (импорты,
def/class, присваивания, for/with/except-цели), — это `NameError`. Тела
функций и классов при сборе модульных имён не обходятся: имя, присвоенное
только внутри функции, глобальным не становится.

Что не проверяется (честно):
  * имена, приходящие через `import *` — файл пропускается целиком;
  * имена, добавляемые в модуль в рантайме (`globals()[...] = ...`);
  * опечатки в именах атрибутов (`obj.methdo()`) — это другая проверка;
  * `typing`-аннотации: при `from __future__ import annotations` они не
    вычисляются, поэтому в отчёт не попадают (иначе шум на `Any` без импорта).

Использование:
    python tools/ast_undefined_names.py            # все каталоги проекта
    python tools/ast_undefined_names.py app/core   # только каталог

Exit code: 0 если чисто, 1 если есть находки.
"""
from __future__ import annotations

import ast
import builtins
import sys
import symtable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRS = ["app", "modules", "agents", "tools", "ui", "updater"]
EXTRA_FILES = ["main.py", "install.py"]

# Имена, которые Python кладёт в модуль сам, и встроенные функции.
MODULE_DUNDERS = {
    "__file__", "__name__", "__doc__", "__package__", "__spec__", "__loader__",
    "__builtins__", "__dict__", "__path__", "__annotations__", "__debug__",
    "__module__", "__qualname__", "__cached__",
}
KNOWN = set(dir(builtins)) | MODULE_DUNDERS


def _add_target(node: ast.AST, names: set[str]) -> None:
    if isinstance(node, ast.Name):
        names.add(node.id)
    elif isinstance(node, (ast.Tuple, ast.List)):
        for item in node.elts:
            _add_target(item, names)
    elif isinstance(node, ast.Starred):
        _add_target(node.value, names)


def _module_level_nodes(tree: ast.Module):
    """Тела модуля без захода внутрь функций и классов."""
    stack = list(tree.body)
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        stack.extend(ast.iter_child_nodes(node))


def module_bound_names(tree: ast.Module) -> set[str]:
    """Имена, существующие на уровне модуля к моменту вызова любой функции."""
    names: set[str] = set()
    for node in _module_level_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == "*":
                    names.add("*")
                else:
                    names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                _add_target(target, names)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            _add_target(node.target, names)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            _add_target(node.target, names)
        elif isinstance(node, ast.withitem) and node.optional_vars is not None:
            _add_target(node.optional_vars, names)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            names.update(node.names)
        elif isinstance(node, ast.MatchAs) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.MatchStar) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            names.add(node.rest)
    return names


def scan_source(source: str, filename: str = "<memory>") -> list[tuple[str, str]]:
    """[(область, имя)] — используемые и нигде не определённые имена."""
    tree = ast.parse(source, filename)
    bound = module_bound_names(tree)
    if "*" in bound:  # import * делает проверку недоказуемой — не врём
        return []

    table = symtable.symtable(source, filename, "exec")
    found: list[tuple[str, str]] = []

    def visit(scope: symtable.SymbolTable) -> None:
        for symbol in scope.get_symbols():
            name = symbol.get_name()
            if not symbol.is_referenced() or not symbol.is_global():
                continue
            if name in bound or name in KNOWN:
                continue
            found.append((scope.get_name(), name))
        for child in scope.get_children():
            visit(child)

    visit(table)
    return found


def scan_file(path: Path) -> list[tuple[str, str]]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        return scan_source(source, str(path))
    except SyntaxError:
        return []


def iter_files(dirs: list[str]) -> list[Path]:
    files: list[Path] = []
    for directory in dirs:
        base = ROOT / directory
        if not base.is_dir():
            continue
        files.extend(sorted(p for p in base.rglob("*.py") if "__pycache__" not in str(p)))
    for extra in EXTRA_FILES:
        candidate = ROOT / extra
        if candidate.is_file():
            files.append(candidate)
    return files


def scan_all(dirs: list[str] | None = None) -> dict[str, list[tuple[str, str]]]:
    report: dict[str, list[tuple[str, str]]] = {}
    for path in iter_files(dirs or DEFAULT_DIRS):
        found = scan_file(path)
        if found:
            report[str(path.relative_to(ROOT))] = found
    return report


def main(argv: list[str]) -> int:
    report = scan_all(argv[1:] or None)
    for path, found in report.items():
        for scope, name in found:
            print(f"{path}: {scope}: не определено имя {name!r}")
    print(f"файлов с находками: {len(report)}")
    return 1 if report else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
