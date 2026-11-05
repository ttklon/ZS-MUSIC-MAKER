# -*- coding: utf-8 -*-
"""
modules/beat/patterns.py — ритмические семейства на 16 шагов и velocity-карты.

Ритм — первое, что выдаёт «сгенерированный» трек. Три захардкоженных пресета
это гарантировали, поэтому здесь семейства грува, а не жанры: phonk, drift,
trap, drill, boom-bap, house, tech-house, dnb, jersey, reggaeton, afrobeat,
amapiano, lofi, hyperpop. Каталог `data/genre_presets/*.json` (50 жанров)
проецируется на семейства по ключевым словам — новый пресет сразу получает
осмысленный грув, а не дефолт.

Кроме шагов у семейства есть **velocity-карта**: акценты на сильных долях,
тише на слабых. Без неё «бочка-снейр-хэт» звучит ровной лентой.
"""

from __future__ import annotations

from typing import Any

SLOT_NAMES = ("kick", "snare", "hat", "bass", "melody")
STEPS = 16

PATTERN_FAMILIES: dict[str, dict[str, list[int]]] = {
    "phonk": {
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hat": [1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1],
        "bass": [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
        "melody": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    },
    "drift": {
        "kick": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
        "hat": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1],
        "bass": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0],
        "melody": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    },
    "trap": {
        "kick": [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hat": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "bass": [1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0],
        "melody": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    },
    "drill": {
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        "snare": [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hat": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1],
        "bass": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
        "melody": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    },
    "boom_bap": {
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hat": [1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1],
        "bass": [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],
        "melody": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    },
    "house": {
        "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hat": [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        "bass": [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        "melody": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
    "tech_house": {
        "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1],
        "snare": [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0],
        "hat": [1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1],
        "bass": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
        "melody": [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 2, 0],
    },
    "dnb": {
        "kick": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        "hat": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        "bass": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
        "melody": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    },
    "jersey": {
        "kick": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
        "hat": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "bass": [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        "melody": [1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1],
    },
    "reggaeton": {
        "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "snare": [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0],
        "hat": [1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1],
        "bass": [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "melody": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    },
    "afrobeat": {
        "kick": [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        "snare": [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1],
        "hat": [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1],
        "bass": [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0],
        "melody": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
    "amapiano": {
        "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "snare": [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1],
        "hat": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1],
        "bass": [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0],
        "melody": [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1],
    },
    "lofi": {
        "kick": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hat": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        "bass": [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        "melody": [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
    },
    "hyperpop": {
        "kick": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1],
        "hat": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "bass": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
        "melody": [1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0],
    },
    "hardstyle": {
        "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
        "hat": [1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1],
        "bass": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
        "melody": [1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0],
    },
}

# Акценты: 1.0 — ровно, >1 — сильная доля, <1 — слабая. Длина всегда 16.
VELOCITY_MAPS: dict[str, dict[str, list[float]]] = {
    "phonk": {
        "kick": [1.15, 1.0, 1.0, 1.0, 1.0, 1.0, 0.95, 1.0, 1.1, 1.0, 1.0, 1.0, 1.0, 0.9, 1.0, 1.0],
        "snare": [1.0, 1.0, 1.0, 1.0, 1.2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.15, 1.0, 1.0, 1.0],
        "hat": [1.1, 0.7, 0.9, 0.7, 1.05, 0.7, 0.95, 0.75, 1.1, 0.7, 0.9, 0.7, 1.05, 0.8, 0.95, 0.7],
    },
    "trap": {
        "kick": [1.2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.95, 1.0, 1.0, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0],
        "snare": [1.0, 1.0, 1.0, 1.0, 1.2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.2, 1.0, 1.0, 1.0],
        "hat": [1.15, 0.75, 1.0, 0.75, 1.1, 0.75, 1.0, 0.8, 1.15, 0.75, 1.0, 0.75, 1.1, 0.8, 1.0, 0.7],
    },
    "house": {
        "kick": [1.2, 1.0, 1.0, 1.0, 1.05, 1.0, 1.0, 1.0, 1.18, 1.0, 1.0, 1.0, 1.05, 1.0, 1.0, 1.0],
        "hat": [1.0, 1.0, 0.85, 1.0, 1.0, 1.0, 0.85, 1.0, 1.0, 1.0, 0.85, 1.0, 1.0, 1.0, 0.9, 1.0],
    },
    "drill": {
        "kick": [1.15, 1.0, 1.0, 1.0, 1.0, 1.0, 1.05, 1.0, 0.95, 1.0, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0],
        "hat": [1.1, 0.7, 0.95, 0.7, 1.05, 0.7, 0.95, 0.7, 1.1, 0.7, 0.95, 0.7, 1.05, 0.75, 0.95, 0.7],
    },
    "reggaeton": {
        "snare": [1.0, 1.0, 1.0, 0.8, 1.0, 1.0, 0.85, 1.0, 1.0, 1.0, 1.0, 0.8, 1.0, 1.0, 0.85, 1.0],
    },
}


def _family_key(genre: str | None) -> str:
    """Проекция названия жанра на ритмическое семейство."""
    key = (genre or "").strip().lower().replace("-", "_").replace(" ", "_")
    rules = (
        ("drift", "drift"),
        ("phonk", "phonk"),
        ("memphis", "phonk"),
        ("drill", "drill"),
        ("boom_bap", "boom_bap"),
        ("lofi", "lofi"),
        ("cloud_rap", "lofi"),
        ("plugg", "lofi"),
        ("tech_house", "tech_house"),
        ("house", "house"),
        ("techno", "house"),
        ("trance", "house"),
        ("retrowave", "house"),
        ("synthwave", "house"),
        ("garage", "house"),
        ("dnb", "dnb"),
        ("jungle", "dnb"),
        ("breakbeat", "dnb"),
        ("jersey", "jersey"),
        ("hyperpop", "hyperpop"),
        ("reggaeton", "reggaeton"),
        ("dembow", "reggaeton"),
        ("afro", "afrobeat"),
        ("amapiano", "amapiano"),
        ("hardstyle", "hardstyle"),
        ("rawstyle", "hardstyle"),
        ("hardcore", "hardstyle"),
        ("rage", "trap"),
        ("trap", "trap"),
        ("hip", "boom_bap"),
        ("rap", "boom_bap"),
        ("west_coast", "boom_bap"),
        ("pop", "house"),
        ("ambient", "lofi"),
        ("industrial", "trap"),
        ("witch", "trap"),
        ("cinematic", "drift"),
    )
    for needle, family in rules:
        if needle in key:
            return family
    return "phonk"


def family_for_genre(genre: str | None) -> str:
    """Имя семейства для жанра (публичная обёртка)."""
    return _family_key(genre)


def slot_preset_for_genre(genre: str | None) -> dict[str, list[int]]:
    """Полный набор из пяти слотов на 16 шагов для жанра."""
    return {slot: list(values) for slot, values in PATTERN_FAMILIES[_family_key(genre)].items()}


# Профиль акцентов семейства: (сильная доля, слабая доля, «и», хэт на доле,
# хэт на «и», хэт между). Числа — это и есть характер грува: у dnb хэт злой и
# рваный, у lofi — мягкий, у drill акцент уезжает на вторую долю.
ACCENT_PROFILES: dict[str, tuple[float, float, float, float, float, float]] = {
    "phonk": (1.15, 0.86, 0.95, 1.10, 0.70, 0.92),
    "drift": (1.10, 0.90, 0.97, 1.08, 0.78, 0.95),
    "trap": (1.18, 0.88, 1.00, 1.15, 0.75, 1.00),
    "drill": (1.12, 0.84, 0.92, 1.06, 0.68, 0.90),
    "boom_bap": (1.08, 0.92, 0.98, 1.05, 0.80, 0.96),
    "house": (1.10, 0.95, 1.00, 1.06, 0.90, 0.98),
    "tech_house": (1.14, 0.88, 0.96, 1.12, 0.74, 0.94),
    "dnb": (1.16, 0.82, 0.94, 1.14, 0.66, 0.88),
    "jersey": (1.12, 0.86, 0.98, 1.16, 0.72, 1.02),
    "reggaeton": (1.10, 0.88, 0.96, 1.08, 0.76, 0.94),
    "afrobeat": (1.06, 0.90, 1.02, 1.04, 0.82, 1.00),
    "amapiano": (1.08, 0.92, 1.00, 1.02, 0.84, 0.98),
    "lofi": (1.04, 0.94, 0.98, 1.02, 0.86, 0.96),
    "hyperpop": (1.16, 0.84, 1.04, 1.18, 0.70, 1.04),
    "hardstyle": (1.18, 0.86, 0.96, 1.12, 0.74, 0.92),
}


def derived_velocity_map(slot: str, family: str = "phonk") -> list[float]:
    """Акценты по сетке 16 шагов из профиля семейства."""
    strong, weak, off, hat_strong, hat_weak, hat_mid = ACCENT_PROFILES.get(
        family, ACCENT_PROFILES["phonk"]
    )
    values: list[float] = []
    for step in range(STEPS):
        if slot == "hat":
            if step % 4 == 0:
                values.append(hat_strong)
            elif step % 2:
                values.append(hat_weak)
            else:
                values.append(hat_mid)
        elif slot in ("kick", "bass"):
            values.append(strong if step % 8 == 0 else (off if step % 4 == 0 else weak))
        else:
            values.append(strong if step % 8 == 4 else (off if step % 4 == 0 else weak))
    return values


def velocity_map_for_genre(genre: str | None) -> dict[str, list[float]]:
    """Velocity-карта семейства: ручная, если есть, иначе из профиля акцентов."""
    family = _family_key(genre)
    base = {slot: derived_velocity_map(slot, family) for slot in SLOT_NAMES}
    for slot, values in VELOCITY_MAPS.get(family, {}).items():
        if len(values) == STEPS:
            base[slot] = list(values)
    return base


def families() -> tuple[str, ...]:
    return tuple(sorted(PATTERN_FAMILIES))


def family_summary() -> list[dict[str, Any]]:
    """Сводка для отчётов: семейство, плотность по слотам, число акцентов."""
    out: list[dict[str, Any]] = []
    for name, slots in sorted(PATTERN_FAMILIES.items()):
        out.append(
            {
                "family": name,
                "density": {slot: sum(1 for step in steps if step) for slot, steps in slots.items()},
                "accents": sum(
                    1
                    for values in VELOCITY_MAPS.get(name, {}).values()
                    for value in values
                    if value > 1.0
                ),
            }
        )
    return out


# Историческое имя реестра: внешний код и тесты обращаются к нему напрямую.
GENRE_SLOT_PRESETS = PATTERN_FAMILIES

LEGACY_SLOT_PRESET = {
    "kick": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    "hat": [0] * STEPS,
    "bass": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    "melody": [0] * STEPS,
}
