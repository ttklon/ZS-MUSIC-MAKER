# -*- coding: utf-8 -*-
"""tools/size_guard.py — не даёт репозиторию тихо растолстеть.

Исторический инцидент: в `demo_site/` лежали восемь демо-WAV на **55 МБ**.
Их не использовал ни один тест (проверено `grep` по `tests/`, `tools/`,
`desktop/test/`), зато каждый клон и каждая копия источника тащила их за собой,
а source-ZIP для обновления раздувался. То, что «пусть будет, вдруг пригодится»,
стоит реальных мегабайт у каждого пользователя.

Сторож смотрит на **отслеживаемые** файлы (не на диск) и падает, если хотя бы
один больше порога. Исключения — только те, что действительно нужны тестам
или являются ресурсом сборки; каждое названо по имени, а не покрыто шаблоном.

    python tools/size_guard.py            # человекочитаемый отчёт
    python tools/size_guard.py --json     # машиночитаемо (exit 1 при находках)
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Порог на один файл: 4 МБ. Крупнее — почти всегда артефакт рендера, а не
# исходник. Фикстуры тестов до 2.6 МБ проходят с запасом.
MAX_FILE_BYTES = 4 * 1024 * 1024
# Порог на весь репозиторий: 40 МБ. Сейчас ~21 МБ, запас на рост.
MAX_TOTAL_BYTES = 40 * 1024 * 1024

# Файлы, которым разрешено быть большими. Каждый — с причиной.
ALLOWED: dict[str, str] = {
    # нет: аудио-фикстуры тестов укладываются в общий порог
}


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("git ls-files не выполнился: это не рабочая копия git?")
    names = result.stdout.decode("utf-8", "replace").split("\0")
    return [ROOT / name for name in names if name]


def audit() -> dict[str, object]:
    """Найти отслеживаемые файлы больше порога и суммарный размер."""
    oversized: list[dict[str, object]] = []
    total = 0
    for path in _tracked_files():
        if not path.is_file():
            continue
        size = path.stat().st_size
        total += size
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if size > MAX_FILE_BYTES and rel not in ALLOWED:
            oversized.append({"path": rel, "bytes": size, "mb": round(size / 1048576, 2)})
    oversized.sort(key=lambda item: -int(item["bytes"]))
    return {
        "max_file_mb": MAX_FILE_BYTES // 1048576,
        "max_total_mb": MAX_TOTAL_BYTES // 1048576,
        "total_mb": round(total / 1048576, 2),
        "oversized": oversized,
        "total_ok": total <= MAX_TOTAL_BYTES,
        "ok": not oversized and total <= MAX_TOTAL_BYTES,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Сторож размера репозитория")
    parser.add_argument("--json", action="store_true", help="машиночитаемый вывод")
    args = parser.parse_args(argv)

    report = audit()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Размер отслеживаемого: {report['total_mb']} МБ (порог {report['max_total_mb']} МБ)")
        if report["oversized"]:
            print(f"Файлы больше {report['max_file_mb']} МБ:")
            for item in report["oversized"]:
                print(f"  {item['mb']:>6} МБ  {item['path']}")
        elif report["total_ok"]:
            print("Крупных файлов нет")
        if not report["total_ok"]:
            print("Репозиторий тяжелее порога: часть артефактов стоит убрать из git")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
