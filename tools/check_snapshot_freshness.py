"""Проверка, что снимок готовности в репозитории соответствует пересчёту.

Зачем: `data/desktop/readiness.json` и `inventory.md` — это данные, которые
окно показывает человеку. Если они отстают от кода, окно говорит неправду,
и заметить это можно только сверкой.

Что сравнивается и почему не всё:

* `inventory.md` — состав модулей и их статусы (пути, статус, синтаксис,
  достижимость). Колонка «Test refs» — это число вхождений имени модуля в
  тексте тестов, и она законно меняется от любой правки тестов, кода не
  касающейся. Сверять её — значит требовать «не менять тесты», а не
  «держать снимок в актуальном состоянии»;
* `readiness.json` — только `module_inventory` (сколько модулей и в каком
  статусе) и `caps_triggered`. Проценты и `raw_probes` зависят от того, какие
  пакеты установлены в окружении (наличие `pedalboard`, `torch`, PySide6),
  поэтому в CI и на машине разработчика они законно разные. Сверять их —
  значит требовать одинакового набора пакетов везде, а это неправда.

Режимы сверки
-------------
В режиме `--tree` сверяется **рабочее дерево**: снимок на диске против
пересчёта во временный каталог. Это то, что нужно локально: правка модуля
обязана сразу валить pytest, а не только CI-шаг после пуша.

`--head` (по умолчанию) сверяет снимок с тем, что закоммичено в `HEAD`:
пересчёт совпал, но снимок не закоммичен — значит в CI он разойдётся.

Почему раньше было больно: сверка шла только с `HEAD`, поэтому локально после
правки кода тест был зелёным (в `HEAD` лежал старый снимок и старый код —
они «совпадали»), а CI падал уже после пуша и тега. Два релиза подряд.

Кода возврата два: 0 — снимок свежий, 1 — устарел, 2 — сравнивать не с чем
(нет git или HEAD, например при прогоне из архива). «Не с чем сравнить» — не
то же самое, что «всё хорошо», поэтому это отдельный код.
"""

from __future__ import annotations

import difflib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "desktop" / "readiness.json"
INVENTORY = ROOT / "data" / "desktop" / "inventory.md"


def committed(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"HEAD:{path.relative_to(ROOT).as_posix()}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def payload(text: str) -> dict:
    data = json.loads(text)
    data.pop("generated_at", None)
    return data


def inventory_rows(text: str) -> dict[str, tuple[str, str, str]]:
    """Разобрать inventory.md: путь → (статус, синтаксис, ссылки в проде).

    Последняя колонка (ссылки из тестов) намеренно не входит: она меняется от
    правок тестов и к актуальности снимка отношения не имеет.
    """
    rows: dict[str, tuple[str, str, str]] = {}
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0].startswith("Versioned") or set(cells[0]) <= {"-"}:
            continue
        path, status, syntax, production_refs = cells[0], cells[1], cells[2], cells[3]
        rows[path] = (status, syntax, production_refs)
    return rows


def inventory_signature(text: str) -> str:
    """Тот же inventory, но построчно и без колонки тестов — для диффа."""
    lines = []
    for path, (status, syntax, production_refs) in sorted(inventory_rows(text).items()):
        lines.append(f"{path} | {status} | {syntax} | {production_refs}")
    return "\n".join(lines)


def _diff_excerpt(before: str, after: str, limit: int = 6) -> str:
    """Первые различающиеся строки — их видно в annotation без логов CI."""
    diff = list(
        difflib.unified_diff(
            before.splitlines(), after.splitlines(), lineterm="", n=0,
        )
    )
    changed = [line for line in diff if line.startswith(("-", "+")) and not line.startswith(("---", "+++"))]
    return " | ".join(changed[:limit])


def have_history() -> bool:
    """Есть ли HEAD, с которым можно сравнивать (в архиве git может не быть)."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _recompute_into(tmp_dir: Path) -> int:
    """Пересчитать снимок во временный каталог, не трогая рабочие файлы."""
    node = shutil.which("node")
    if not node:
        print("::warning title=snapshot::node не найден — пересчёт невозможен")
        return 2
    script = ROOT / "desktop" / "scripts" / "snapshot-readiness.js"
    env = dict(os.environ, ZSMM_SNAPSHOT_OUT=str(tmp_dir))
    proc = subprocess.run(
        [node, str(script)], cwd=str(ROOT), capture_output=True, text=True, env=env,
    )
    if proc.returncode != 0:
        print(f"::error title=snapshot::пересчёт не удался: {(proc.stderr or '')[-500:]}")
        return 1
    return 0


def _compare_tree() -> tuple[int, list[str]]:
    """Сверить файлы на диске с пересчётом во временный каталог."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        code = _recompute_into(target)
        if code != 0:
            return code, []
        problems: list[str] = []
        fresh_ready = target / "readiness.json"
        fresh_inv = target / "inventory.md"
        if not fresh_ready.is_file():
            return 2, ["пересчёт не создал readiness.json (нет ZSMM_SNAPSHOT_OUT?)"]
        old = payload(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.is_file() else {}
        new = payload(fresh_ready.read_text(encoding="utf-8"))
        for field in ("module_inventory", "caps_triggered"):
            if old.get(field) != new.get(field):
                problems.append(f"readiness.json: {field} устарел относительно кода")
        if INVENTORY.is_file() and fresh_inv.is_file():
            before = INVENTORY.read_text(encoding="utf-8")
            after = fresh_inv.read_text(encoding="utf-8")
            if inventory_rows(before) != inventory_rows(after):
                problems.append(
                    "inventory.md устарел относительно кода: "
                    + _diff_excerpt(inventory_signature(before), inventory_signature(after))
                )
        return (1 if problems else 0), problems


def main() -> int:
    problems: list[str] = []

    mode = "tree" if "--tree" in sys.argv else "head"
    if mode == "tree":
        code, tree_problems = _compare_tree()
        if code == 2:
            print("снимок: пересчёт недоступен (нет node или каталога) — сверка пропущена")
            return 2
        if code == 1:
            for problem in tree_problems:
                print(f"::error title=snapshot drift::{problem} — перегенерируйте снимок")
            print("снимок устарел: " + "; ".join(tree_problems))
            return 1
        print("снимок готовности соответствует пересчёту (рабочее дерево)")
        return 0

    if not have_history():
        print("::warning title=snapshot::нет git-истории — сравнить снимок не с чем")
        return 2

    if SNAPSHOT.is_file():
        before = committed(SNAPSHOT)
        if not before:
            problems.append("readiness.json нет в коммите — снимок не сохранён")
        else:
            old = payload(before)
            new = payload(SNAPSHOT.read_text(encoding="utf-8"))
            for field in ("module_inventory", "caps_triggered"):
                if old.get(field) != new.get(field):
                    problems.append(f"readiness.json: {field} расходится с пересчётом")
    else:
        problems.append("readiness.json не сгенерирован")

    if INVENTORY.is_file():
        before = committed(INVENTORY)
        if not before:
            problems.append("inventory.md нет в коммите")
        else:
            after = INVENTORY.read_text(encoding="utf-8")
            old = inventory_rows(before)
            new = inventory_rows(after)
            if old != new:
                problems.append(
                    "inventory.md расходится с пересчётом: "
                    + _diff_excerpt(inventory_signature(before), inventory_signature(after))
                )
    else:
        problems.append("inventory.md не сгенерирован")

    if problems:
        for problem in problems:
            print(f"::error title=snapshot drift::{problem} — перегенерируйте снимок")
        print("снимок устарел: " + "; ".join(problems))
        return 1

    print("снимок готовности соответствует пересчёту")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
