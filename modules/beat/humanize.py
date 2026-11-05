# -*- coding: utf-8 -*-
"""
modules/beat/humanize.py — «человечность» бита: микротайминг, velocity, варианты.

Машина слышна не из-за нот, а из-за трёх вещей: абсолютно ровной сетки,
постоянной громкости удара и одного и того же сэмпла на каждом шаге. Модуль
даёт ровно эти три поправки:

* `timing_offset_ms` — у каждого инструмента свой характер: хэты играют чуть
  раньше сетки, снейр опаздывает на 2–7 мс, кик — почти в сетке; плюс свинг
  на нечётных шестнадцатых;
* `velocity_gain` — ±12 % к громкости, акценты на сильных долях, отдельный
  уровень для ghost-нот;
* `variant_index` — round-robin: одна и та же нота не звучит дважды одинаково.

Всё детерминировано: единственный источник случайности — переданные функции
`uniform(low, high)` / `random()`, полученные из RNG конструктора.
"""

from __future__ import annotations

from typing import Callable

# (min_ms, max_ms) — характер инструмента относительно сетки
PART_FEEL_MS = {
    "kick": (-1.2, 1.4),
    "snare": (2.0, 7.0),
    "clap": (3.0, 9.0),
    "hat": (-3.0, 2.4),
    "bass": (0.4, 3.6),
    "melody": (1.0, 6.0),
}

# шаги, на которых живёт акцент (сильные доли 16-шаговой сетки)
ACCENT_STEPS = frozenset({0, 4, 8, 12})
GHOST_VELOCITY = 0.28


def timing_offset_ms(
    uniform: Callable[[float, float], float],
    part: str,
    step: int,
    bar: int,
    swing: float = 0.0,
    step_ms: float = 117.0,
) -> float:
    """Смещение удара в миллисекундах (может быть отрицательным — «раньше сетки»)."""
    low, high = PART_FEEL_MS.get(part, (-2.0, 2.0))
    offset = float(uniform(low, high))
    # Свинг двигает только нечётные шестнадцатые: это и есть «качание».
    if swing and step % 2 == 1:
        offset += abs(float(swing)) * step_ms * 0.5
    # Раз в 4 такта инструмент «дышит» на пол-миллисекунды сильнее.
    if bar % 4 == 3:
        offset += float(uniform(-0.5, 0.5))
    return float(offset)


def velocity_gain(
    random: Callable[[], float],
    uniform: Callable[[float, float], float],
    part: str,
    step: int,
    bar: int,
    ghost: bool = False,
) -> float:
    """Громкость удара: акцент на сильной доле, ±12 % джиттера, ghost ≤ 30 %."""
    if ghost:
        return GHOST_VELOCITY * float(uniform(0.85, 1.15))
    gain = float(uniform(0.88, 1.12))
    if step in ACCENT_STEPS:
        gain *= 1.09
    if part in ("hat", "snare") and float(random()) < 0.06:
        # редкий «недобор» — человеческая неровность, а не ошибка паттерна
        gain *= 0.72
    if bar % 8 == 7 and part == "snare":
        gain *= 0.94
    return float(gain)


def ghost_note(
    random: Callable[[], float],
    part: str,
    step: int,
    probability: float = 0.18,
    steps: tuple[int, ...] = (3, 6, 11, 14),
) -> bool:
    """Ghost-нота на слабой доле: тихий удар, который «оживляет» грув."""
    if step not in steps:
        return False
    return float(random()) < probability


def variant_index(random: Callable[[], float], count: int) -> int:
    """Round-robin выбор варианта сэмпла/тембра."""
    if count <= 1:
        return 0
    return min(count - 1, int(float(random()) * count))


def is_fill_bar(bar: int, every: int = 8) -> bool:
    """Последний такт фразы — место для сбивки."""
    return every > 0 and bar % every == every - 1


def ghost_roll_steps(is_fill: bool, humanize: bool = True) -> tuple[int, ...]:
    """Шаги сбивки в конце фразы (малый барабан 32-ми): только на fill-такте."""
    if not is_fill or not humanize:
        return ()
    return (13, 14, 15)
