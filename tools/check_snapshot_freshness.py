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

Запускается после `node desktop/scripts/snapshot-readiness.js` в CI.

Кода возврата два: 0 — снимок свежий, 1 — устарел, 2 — сравнивать не с чем
(нет git или HEAD, например при прогоне из архива). «Не с чем сравнить» — не
то же самое, что «всё хорошо», поэтому это отдельный код.
"""

from __future__ import annotations

import difflib
import json
import subprocess
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


def main() -> int:
    problems: list[str] = []

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
