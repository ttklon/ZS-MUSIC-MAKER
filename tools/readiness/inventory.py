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


def _source_texts() -> tuple[str, str]:
    production = "\n".join(
        (ROOT / path).read_text(encoding="utf-8", errors="replace")
        for path in tracked_python_modules()
    )
    tests_dir = ROOT / TEST_ROOT
    tests = (
        "\n".join(
            p.read_text(encoding="utf-8", errors="replace")
            for p in tests_dir.glob("test_*.py")
        )
        if tests_dir.exists()
        else ""
    )
    return production, tests


def module_inventory() -> list[dict[str, Any]]:
    """Одна аудиторская строка на каждый версионированный production-модуль."""
    production, tests = _source_texts()
    rows: list[dict[str, Any]] = []
    for path in tracked_python_modules():
        source = (ROOT / path).read_text(encoding="utf-8", errors="replace")
        module_dot = path[:-3].replace("/", ".")
        basename = Path(path).stem
        try:
            ast.parse(source, filename=path)
            syntax_ok = True
        except SyntaxError:
            syntax_ok = False
        production_refs = max(0, production.count(module_dot) + production.count(basename) - 1)
        test_refs = tests.count(module_dot) + tests.count(basename)
        status = (
            "REAL_FAIL"
            if not syntax_ok
            else "REAL_PASS"
            if (production_refs or test_refs)
            else "PLANNED"
        )
        rows.append(
            {
                "path": path,
                "status": status,
                "syntax_ok": syntax_ok,
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
