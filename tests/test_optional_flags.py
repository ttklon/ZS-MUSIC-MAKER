"""T9: каждый `HAS_*`-флаг соответствует реальной проверке импорта.

`modules/voice_vault.py` содержал `try: HAS_LIBROSA = True / except: False`
без единого импорта внутри: флаг всегда `True` и ничего не проверял.
Такой код невозможно отличить от рабочей проверки зависимости, поэтому
гейт сканирует весь прод-код: либо в `try` есть `import`, либо флага нет.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DIRS = ("app", "modules", "agents", "tools", "updater", "ui")


def _production_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    return [
        ROOT / rel for rel in out
        if (ROOT / rel).is_file()
        and (rel.split("/", 1)[0] in PRODUCTION_DIRS or rel in ("main.py", "install.py"))
    ]


def _declared_flags(tree: ast.AST) -> list[tuple[int, str, bool]]:
    """Найти `HAS_*` в top-level try-блоках: (строка, имя, есть ли import)."""
    found: list[tuple[int, str, bool]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        has_import = any(
            isinstance(sub, (ast.Import, ast.ImportFrom)) for sub in ast.walk(node)
        )
        for statement in node.body:
            targets: list[ast.expr] = []
            if isinstance(statement, ast.Assign):
                targets = statement.targets
            elif isinstance(statement, ast.AnnAssign):
                targets = [statement.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.startswith("HAS_"):
                    found.append((statement.lineno, target.id, has_import))
    return found


def test_optional_flags_are_backed_by_a_real_import() -> None:
    offenders: list[str] = []
    for path in _production_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for lineno, name, has_import in _declared_flags(tree):
            if not has_import:
                offenders.append(f"{path.relative_to(ROOT)}:{lineno} {name}")

    assert not offenders, "HAS_*-флаги без проверки импорта: " + ", ".join(offenders)


def test_voice_vault_has_no_dead_librosa_flag() -> None:
    tree = ast.parse((ROOT / "modules" / "voice_vault.py").read_text(encoding="utf-8"))

    flags = [name for _, name, _ in _declared_flags(tree)]

    assert "HAS_LIBROSA" not in flags, "мёртвый флаг HAS_LIBROSA вернулся в voice_vault"
