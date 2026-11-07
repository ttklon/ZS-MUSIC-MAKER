"""P3: каталог жанров без дублей — имя жанра однозначно.

`config/genres_100.json` — единственный каталог жанров (120 записей в 6
категориях). В отчёте (§5.16/P3) зафиксировано: `Trap` и `Grime` встречались
дважды — в `electronic` и в `hiphop_rnb`. Пользователь видел один и тот же жанр
в двух категориях, а счётчик «118 уникальных из 120» нигде не проверялся.

Тест держит инвариант: каждое имя встречается ровно один раз, без учёта
регистра и лишних пробелов.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config" / "genres_100.json"


def _catalog() -> dict[str, list[str]]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def _flat() -> list[str]:
    return [name for items in _catalog().values() for name in items]


def test_catalog_has_no_duplicate_genre_names() -> None:
    names = _flat()
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for category, items in _catalog().items():
        for name in items:
            key = name.strip().lower()
            if key in seen:
                duplicates.append(f"{name!r} в {seen[key]} и {category}")
            else:
                seen[key] = category

    assert not duplicates, "дубли жанров: " + "; ".join(duplicates)
    assert len(seen) == len(names)


def test_catalog_size_and_shape() -> None:
    catalog = _catalog()

    assert len(_flat()) == 120
    assert all(len(items) == 20 for items in catalog.values())
    assert all(name.strip() == name and name for name in _flat())
