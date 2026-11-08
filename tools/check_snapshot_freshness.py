"""Проверка, что снимок готовности в репозитории соответствует пересчёту.

Зачем: `data/desktop/readiness.json` и `inventory.md` — это данные, которые
окно показывает человеку. Если они отстают от кода, окно говорит неправду,
и заметить это можно только сверкой. Пересчёт детерминирован, поэтому
сравнение корректно; исключение — `generated_at`, дата меняется от запуска.

Запускается после `node desktop/scripts/snapshot-readiness.js` в CI.
"""

from __future__ import annotations

import json
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


def main() -> int:
    problems = []

    if SNAPSHOT.is_file():
        before = committed(SNAPSHOT)
        if not before:
            problems.append("readiness.json нет в коммите — снимок не сохранён")
        elif payload(before) != payload(SNAPSHOT.read_text(encoding="utf-8")):
            problems.append("readiness.json расходится с пересчётом")
    else:
        problems.append("readiness.json не сгенерирован")

    if INVENTORY.is_file():
        before = committed(INVENTORY)
        if not before:
            problems.append("inventory.md нет в коммите")
        elif before != INVENTORY.read_text(encoding="utf-8"):
            problems.append("inventory.md расходится с пересчётом")
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
