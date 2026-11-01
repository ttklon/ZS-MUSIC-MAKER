# -*- coding: utf-8 -*-
"""tools/audit_honesty.py — аудит «честности» кода (план 6.6).

Что проверяется (всё статически, по AST):

1. **Глухие `except: pass`** — исключение проглочено без следа. Именно так в
   проекте годами жили поломки вида «стадия всегда падает в FALLBACK».
2. **`except` без логирования** — тело-заглушка (`...`), пустой список или
   только `return` без комментария/лога: ошибка не видна в логах.
3. **Маркеры подделки в проде** — `fake`, `simulate`, `stub`, `dummy`,
   `pretend` в именах функций/классов вне тестов и `tools/`.

Запуск:
    python -m tools.audit_honesty            # отчёт, код 1 если есть находки
    python -m tools.audit_honesty --json     # машинный отчёт
    python -m tools.audit_honesty --quiet    # только итог

Инструмент намеренно не «лечит» код: он только показывает факты.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "output",
    "release",
    "node_modules",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
}
PRODUCTION_DIRS = ("app", "modules", "agents")
FAKE_MARKERS = ("fake", "simulate", "stub", "dummy", "pretend", "mock_")


@dataclass
class Finding:
    kind: str
    path: str
    line: int
    detail: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0

    def add(self, kind: str, path: Path, line: int, detail: str) -> None:
        try:
            shown = str(path.relative_to(ROOT))
        except ValueError:  # путь вне репозитория (например, во временном каталоге)
            shown = str(path)
        self.findings.append(Finding(kind, shown, line, detail))

    def as_dict(self) -> dict[str, object]:
        by_kind: dict[str, int] = {}
        for finding in self.findings:
            by_kind[finding.kind] = by_kind.get(finding.kind, 0) + 1
        return {
            "files_scanned": self.files_scanned,
            "total": len(self.findings),
            "by_kind": by_kind,
            "findings": [
                {"kind": f.kind, "path": f.path, "line": f.line, "detail": f.detail}
                for f in self.findings
            ],
            "clean": not self.findings,
        }


def _iter_files(base: Path):
    for path in base.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _is_silent_body(body: list[ast.stmt]) -> str | None:
    """Определить «немой» обработчик: только pass, только ..., или пустой return."""
    if len(body) != 1:
        return None
    statement = body[0]
    if isinstance(statement, ast.Pass):
        return "pass"
    if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
        if statement.value.value is Ellipsis:
            return "..."
    if isinstance(statement, ast.Return) and statement.value is None:
        return "return"
    return None


def _mentions_logging(body: list[ast.stmt]) -> bool:
    """Есть ли в теле логирование? (иначе ошибка останется невидимой)."""
    for node in ast.walk(ast.Module(body=body, type_ignores=[])):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "attr", None) or getattr(func, "id", None)
            if name in {"debug", "info", "warning", "error", "exception", "critical"}:
                return True
            if name in {"print", "warn"}:
                return True
    return False


def _check_except_blocks(tree: ast.AST, path: Path, report: Report) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        silent = _is_silent_body(node.body)
        if silent is None:
            continue
        if _mentions_logging(node.body):
            continue
        kind = "silent_except" if silent == "pass" else "silent_except_body"
        exc_type = ast.unparse(node.type) if node.type is not None else "bare"
        report.add(kind, path, node.lineno, f"except {exc_type}: {silent}")


def _check_fake_markers(tree: ast.AST, path: Path, report: Report) -> None:
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError:  # путь вне репозитория
        relative = path.as_posix()
    if not relative.startswith(PRODUCTION_DIRS):
        return
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name.lower()
            marker = next((m for m in FAKE_MARKERS if m in name), None)
            if marker and not name.startswith("_"):
                report.add("fake_marker", path, node.lineno, f"{node.name} содержит '{marker}'")


def audit(roots: list[Path] | None = None) -> Report:
    report = Report()
    targets = roots or [ROOT / "app", ROOT / "modules", ROOT / "agents", ROOT / "tools"]
    for base in targets:
        if not base.exists():
            continue
        for path in _iter_files(base):
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(path))
            except (SyntaxError, UnicodeDecodeError) as exc:
                report.add("unparsable", path, 0, f"{type(exc).__name__}: {exc}")
                continue
            report.files_scanned += 1
            _check_except_blocks(tree, path, report)
            _check_fake_markers(tree, path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Аудит честности: немые except и маркеры подделки")
    parser.add_argument("--json", action="store_true", help="машинный отчёт")
    parser.add_argument("--quiet", action="store_true", help="только итог")
    parser.add_argument(
        "--path", action="append", default=None, help="ограничить каталог (можно несколько)"
    )
    args = parser.parse_args(argv)

    roots = [Path(p).resolve() for p in args.path] if args.path else None
    report = audit(roots)
    payload = report.as_dict()

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if not args.quiet:
            for finding in report.findings:
                print(f"{finding.path}:{finding.line}  [{finding.kind}] {finding.detail}")
        status = "CLEAN" if payload["clean"] else f"FOUND {payload['total']}"
        print(f"honesty audit: {status} ({report.files_scanned} файлов)")
    return 0 if payload["clean"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
