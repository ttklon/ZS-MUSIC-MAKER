# -*- coding: utf-8 -*-
"""modules/arrangement_genres.py — имена жанров пользователя → шаблоны аранжировки.

Рецепт визарда приходит со «слаговыми» именами (`drift_phonk`), движок
аранжировки работает на крупных семействах (`phonk / drift`). Раскладка живёт
отдельно от шаблонов, чтобы её можно было расширять без правки движка.
"""

from __future__ import annotations

GENRE_TEMPLATE_KEYS = (
    "phonk / drift",
    "dance / edm",
    "trap / hip-hop",
    "pop / r&b",
    "hardstyle / techno",
    "generic hit",
)

# ---------------------------------------------------------- genre mapping
# Рецепт визарда приходит со «слаговыми» именами жанров (`drift_phonk`),
# а движок работает на крупных семействах. Раскладка явная и единственная:
# молчаливого `generic hit` для фонка/хаус-вариантов быть не должно.
GENRE_ALIASES = {
    "drift_phonk": "phonk / drift",
    "phonk": "phonk / drift",
    "memphis": "phonk / drift",
    "edm": "dance / edm",
    "house": "dance / edm",
    "techno": "dance / edm",
    "dance": "dance / edm",
    "trance": "dance / edm",
    "trap": "trap / hip-hop",
    "hip-hop": "trap / hip-hop",
    "hiphop": "trap / hip-hop",
    "rap": "trap / hip-hop",
    "drill": "trap / hip-hop",
    "pop": "pop / r&b",
    "r&b": "pop / r&b",
    "rnb": "pop / r&b",
    "soul": "pop / r&b",
    "hardstyle": "hardstyle / techno",
    "hardcore": "hardstyle / techno",
}


def normalize_genre(name: str | None) -> str:
    """Привести пользовательское имя жанра к ключу `GENRE_TEMPLATES`.

    Неизвестное имя не подменяется молча «универсальным»: возвращается как есть,
    чтобы вызывающая сторона видела, что шаблон не найден.
    """
    raw = str(name or "").strip().lower()
    if not raw:
        return "generic hit"
    if raw in GENRE_TEMPLATE_KEYS:
        return raw
    if raw in GENRE_ALIASES:
        return GENRE_ALIASES[raw]
    # «drift_phonk» / «phonk-drift»: ищем известное слово внутри слага
    for token in raw.replace("/", " ").replace("-", " ").replace("_", " ").split():
        if token in GENRE_ALIASES:
            return GENRE_ALIASES[token]
    return raw


