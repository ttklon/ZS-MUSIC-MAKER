# -*- coding: utf-8 -*-
"""tools/readiness/reachability.py — достижимость модулей по графу импортов.

Статика «на имя модуля есть ссылка в тексте» переоценивает связность: упоминание
в комментарии, в тесте-пустышке или в самом аудируемом файле делает модуль
«используемым». Здесь считается честная достижимость:

1. строятся рёбра `модуль → модуль` по AST (`import x`, `from x import y`,
   включая ленивые импорты внутри функций);
2. BFS идёт от точек входа — того, что реально запускается пользователем;
3. достижимые модули живут своей жизнью, остальные получают `DEPRECATED`.

`tools/` в граф **не входит**: обслуживающий скрипт, который дергает legacy-
модуль для отчёта, не делает этот модуль частью продукта.
"""

from __future__ import annotations

import ast
from collections import deque
from pathlib import Path

# Points of entry: что запускается пользователем или установщиком.
ENTRY_POINTS = (
    "main.py",
    "install.py",
    "app/__init__.py",
    "app/cli/__init__.py",
    "app/gui/__init__.py",
    "updater/__init__.py",
    "ui/__init__.py",
)

# Каталоги, которые не считаются прод-графом.
EXCLUDED_PREFIXES = ("tests/", "tools/")

# Скрипты обслуживания — самостоятельные точки входа: их запускают руками,
# из `.cmd`-обёрток и CI. Они не «мертвы» только потому, что их никто не
# импортирует.
SELF_ENTRY_PREFIXES = ("tools/",)


def module_name(path: str) -> str:
    """`app/core/recipe.py` → `app.core.recipe`, `main.py` → `main`."""
    text = str(path).replace("\\", "/")
    if text.endswith(".py"):
        text = text[:-3]
    if text.endswith("/__init__"):
        text = text[: -len("/__init__")]
    elif text == "__init__":
        return "app"
    return text.replace("/", ".")


def _resolve_import(node: ast.AST, current: str, known: set[str]) -> list[str]:
    """Куда ведут импорты одного узла — по известным модулям проекта."""
    found: list[str] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            candidate = alias.name
            while candidate:
                if candidate in known:
                    found.append(candidate)
                    break
                candidate = candidate.rpartition(".")[0]
        return found
    if isinstance(node, ast.ImportFrom):
        base = node.module or ""
        if node.level:
            # относительный импорт: `from . import x` внутри пакета
            package = current.rpartition(".")[0]
            for _ in range(node.level - 1):
                package = package.rpartition(".")[0]
            base = f"{package}.{base}" if base else package
        for alias in node.names:
            for candidate in (f"{base}.{alias.name}", base):
                if candidate in known:
                    found.append(candidate)
                    break
        return found
    return found


def reachable_modules(files: list[str], root: Path) -> set[str]:
    """Множество модулей, достижимых из точек входа.

    Скрипты `tools/` — самостоятельные точки входа (их запускают руками и из
    `.cmd`), поэтому они стартуют BFS, но сами в «мёртвый код» не попадают.
    """
    known = {module_name(path) for path in files}
    graph: dict[str, set[str]] = {name: set() for name in known}

    for path in files:
        try:
            tree = ast.parse((root / path).read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError):
            continue
        current = module_name(path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                graph[current].update(_resolve_import(node, current, known))

    starts = [module_name(p) for p in ENTRY_POINTS]
    starts += [
        module_name(p) for p in files
        if p.replace("\\", "/").startswith(SELF_ENTRY_PREFIXES)
    ]
    queue = deque(name for name in starts if name in known)
    seen: set[str] = set(queue)
    while queue:
        current = queue.popleft()
        for neighbour in graph.get(current, ()):
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)

    # Пакет «жив», если жив хотя бы один его подмодуль: `app.core` не должен
    # считаться мёртвым из-за того, что импортируется `app.core.orchestrator`.
    for name in list(seen):
        parts = name.split(".")
        while len(parts) > 1:
            parts.pop()
            parent = ".".join(parts)
            if parent in known:
                seen.add(parent)
    return seen
