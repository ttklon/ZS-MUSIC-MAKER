# -*- coding: utf-8 -*-
"""
tools/readiness/inventory.py — статическая матрица версионированных модулей.

Инвентарь строится по `git ls-files "*.py"` (fallback — обход каталогов),
чтобы «модуль существует» означало «модуль в репозитории», а не «лежит на
диске у разработчика».
"""

from __future__ import annotations

import logging

import ast
import subprocess
from pathlib import Path
from typing import Any

from tools.readiness.paths import INVENTORY_ROOTS, ROOT, TEST_ROOT
from tools.readiness.reachability import module_name, reachable_modules


def _tracked_candidates() -> list[str]:
    """Return tracked production Python files (git if available, else filesystem)."""
    try:
        import subprocess

        out = subprocess.run(
            ["git", "ls-files", "*.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            paths = []
            for line in out.stdout.splitlines():
                rel = line.strip()
                if not rel or rel.startswith(TEST_ROOT + "/"):
                    continue
                top = rel.split("/", 1)[0]
                # root-level entrypoints (main.py, install.py) и пакеты из ROOTS
                if "/" not in rel or top in INVENTORY_ROOTS:
                    paths.append(rel)
            return sorted(paths)
    except Exception:  # pragma: no cover - git отсутствует
        logging.getLogger(__name__).debug("ignored exception", exc_info=True)
    paths = ["main.py"] if (ROOT / "main.py").exists() else []
    for root in INVENTORY_ROOTS:
        base = ROOT / root
        if not base.exists():
            continue
        paths.extend(str(p.relative_to(ROOT)) for p in base.rglob("*.py"))
    return sorted(paths)


def tracked_python_modules() -> list[str]:
    """Список модулей, реально присутствующих на диске.

    `git ls-files` может помнить удалённый файл (индекс ещё не обновлён),
    поэтому результат фильтруется по существованию: инвентарь описывает
    дерево, а не историю.
    """
    return [path for path in _tracked_candidates() if (ROOT / path).is_file()]


def _production_texts() -> dict[str, str]:
    """Текст каждого прод-модуля отдельно: упоминание в самом себе не считается."""
    return {
        path: (ROOT / path).read_text(encoding="utf-8", errors="replace")
        for path in tracked_python_modules()
    }


def _imported_by(texts: dict[str, str]) -> dict[str, int]:
    """Сколько прод-модулей импортируют модуль (AST, включая ленивые импорты).

    Текстовый поиск учитывал строковые литералы: `"modules.expert_mode"` в
    списке health-проб делал мёртвый модуль «используемым». Импорт — это
    единственная надёжная ссылка.
    """
    known = {module_name(path) for path in texts}
    counts: dict[str, int] = {name: 0 for name in known}
    for path, source in texts.items():
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        current = module_name(path)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Import):
                for alias in node.names:
                    candidate = alias.name
                    while candidate:
                        if candidate in known:
                            imported.add(candidate)
                            break
                        candidate = candidate.rpartition(".")[0]
            else:
                base = node.module or ""
                if node.level:
                    package = current.rpartition(".")[0]
                    for _ in range(node.level - 1):
                        package = package.rpartition(".")[0]
                    base = f"{package}.{base}" if base else package
                for alias in node.names:
                    for candidate in (f"{base}.{alias.name}", base):
                        if candidate in known:
                            imported.add(candidate)
                            break
        imported.discard(current)
        for name in imported:
            counts[name] += 1
    return counts


def _tests_text() -> str:
    tests_dir = ROOT / TEST_ROOT
    if not tests_dir.exists():
        return ""
    return "\n".join(
        p.read_text(encoding="utf-8", errors="replace") for p in tests_dir.glob("test_*.py")
    )


def module_inventory() -> list[dict[str, Any]]:
    """Одна аудиторская строка на каждый версионированный production-модуль.

    Статусы:
      * `REAL_FAIL` — файл не парсится;
      * `PLANNED`   — на модуль нет ссылок ни в проде, ни в тестах;
      * `DEPRECATED`— код есть, но из точек входа он недостижим (помечен в
                      `docs/IMPROVEMENT_PLAN.md` §5.16; удаление — отдельно);
      * `REAL_PASS` — достижим и на него есть ссылки.

    `production_references` считается без текста самого файла и без `tools/`:
    иначе модуль «ссылается сам на себя» и всегда выглядит используемым.
    """
    texts = _production_texts()
    tests = _tests_text()
    files = list(texts)
    reachable = reachable_modules(files, ROOT)
    import_counts = _imported_by(texts)

    rows: list[dict[str, Any]] = []
    for path in files:
        source = texts[path]
        module_dot = module_name(path)
        basename = Path(path).stem
        try:
            ast.parse(source, filename=path)
            syntax_ok = True
        except SyntaxError:
            syntax_ok = False

        production_refs = import_counts.get(module_dot, 0)
        test_refs = tests.count(module_dot) + tests.count(basename)
        is_reachable = module_dot in reachable

        if not syntax_ok:
            status = "REAL_FAIL"
        elif not is_reachable:
            status = "DEPRECATED"
        elif production_refs or test_refs:
            status = "REAL_PASS"
        else:
            status = "PLANNED"
        rows.append(
            {
                "path": path,
                "status": status,
                "syntax_ok": syntax_ok,
                "reachable": is_reachable,
                "production_references": production_refs,
                "test_references": test_refs,
            }
        )
    return rows


def module_inventory_summary() -> dict[str, int]:
    rows = module_inventory()
    return {
        "tracked_modules": len(rows),
        "REAL_PASS": sum(row["status"] == "REAL_PASS" for row in rows),
        "REAL_FAIL": sum(row["status"] == "REAL_FAIL" for row in rows),
        "PLANNED": sum(row["status"] == "PLANNED" for row in rows),
        "DEPRECATED": sum(row["status"] == "DEPRECATED" for row in rows),
    }


def inventory_markdown() -> str:
    lines = [
        "| Versioned module | Status | AST syntax | Production refs | Test refs |",
        "|---|---|---:|---:|---:|",
    ]
    for row in module_inventory():
        lines.append(
            "| {path} | {status} | {syntax} | {production} | {tests} |".format(
                path=row["path"],
                status=row["status"],
                syntax="PASS" if row["syntax_ok"] else "FAIL",
                production=row["production_references"],
                tests=row["test_references"],
            )
        )
    return "\n".join(lines)
