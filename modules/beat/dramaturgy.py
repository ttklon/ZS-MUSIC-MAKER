# -*- coding: utf-8 -*-
"""
modules/beat/dramaturgy.py — драматургия трека: секции, энергия, плотность.

Трек отличается от «лупа на 3 минуты» тем, что у него есть кривая: вход,
нарастание, дроп, спад, второй дроп, выход. Модуль отвечает за три вещи:

* `plan_sections()` — структура под целевую длительность 2:30–3:30 с правилом
  «хук в первые 15 секунд»: интро сразу играет мотив хука, а первый припев
  приходит задолго до середины;
* `energy_curve()` — энергия каждой секции 0…1 и гейн в дБ. Разница между
  куплетом и хуком ≥4 дБ, дроп получает дополнительный импакт;
* `layers_for_section()` — потолок плотности: в куплете не может звучать
  восемь слоёв одновременно, иначе получается «каша», а не аранжировка.

Все функции чистые и детерминированные: одинаковый вход — одинаковая структура.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# Энергия секции по умолчанию (0…1). Дроп — 1.0, куплет — около 0.6.
SECTION_ENERGY = {
    "intro": 0.42,
    "intro_pad": 0.32,
    "verse": 0.62,
    "pre_chorus": 0.78,
    "hook": 1.0,
    "chorus": 1.0,
    "bridge": 0.48,
    "breakdown": 0.30,
    "breakdown_silent": 0.0,
    "outro": 0.40,
    "outro_fade": 0.28,
}

# Потолок одновременных слоёв: анти-«каша».
MAX_LAYERS = {
    "intro": 3,
    "intro_pad": 2,
    "verse": 5,
    "pre_chorus": 5,
    "hook": 7,
    "chorus": 7,
    "bridge": 3,
    "breakdown": 2,
    "breakdown_silent": 0,
    "outro": 3,
    "outro_fade": 2,
}

LAYER_ORDER = ("drums", "bass", "pad", "keys", "melody", "fx", "hook_lead")

# Трим низа по секциям: куплет звучит «суше», дроп — полноценно. Это реальная
# практика сведения, а не костыль: контраст низа ≥6 дБ достигается осознанно.
LOW_TRIM = {
    "intro": 0.58,
    "intro_pad": 0.48,
    "verse": 0.55,
    "pre_chorus": 0.80,
    "hook": 1.0,
    "chorus": 1.0,
    "bridge": 0.50,
    "breakdown": 0.45,
    "breakdown_silent": 0.0,
    "outro": 0.60,
    "outro_fade": 0.50,
}

# Базовые размеры секций в тактах (4/4).
BASE_BARS = {"intro": 4, "verse": 8, "pre_chorus": 4, "hook": 8, "bridge": 4, "outro": 4}

TARGET_MIN_SEC = 150.0
TARGET_MAX_SEC = 210.0
HOOK_WITHIN_SEC = 15.0


@dataclass(frozen=True)
class SectionPlan:
    name: str
    bars: int
    energy: float
    layers: tuple[str, ...]

    @property
    def gain_db(self) -> float:
        """Гейн секции: 0 дБ на дропе, −12 дБ в полной тишине."""
        return round(-12.0 * (1.0 - self.energy), 2)

    @property
    def bass_gain(self) -> float:
        """Трим низа: в куплете −3 дБ, в дропе 0 дБ."""
        return round(LOW_TRIM.get(self.name, 0.8), 3)


def energy_curve(names: Iterable[str]) -> list[float]:
    """Энергия по именам секций (без побочных эффектов)."""
    return [SECTION_ENERGY.get(name, 0.6) for name in names]


def layers_for_section(name: str, energy: float) -> tuple[str, ...]:
    """Слои секции с учётом потолка плотности и её энергии."""
    limit = MAX_LAYERS.get(name, 5)
    if energy >= 0.9:
        limit = max(limit, 6)
    allowed = list(LAYER_ORDER[:limit])
    if name in ("intro", "intro_pad"):
        # Правило TikTok: мотив хука звучит с первых тактов. В интро нет
        # барабанной «каши», но хук-лид уже есть — трек узнаётся за 15 секунд.
        allowed = [layer for layer in ("drums", "pad", "hook_lead") if layer in LAYER_ORDER]
    if name in ("outro", "outro_fade", "breakdown"):
        # В аутро и бридже остаётся атмосфера, мотив уходит в тень.
        allowed = [layer for layer in ("pad", "keys", "drums") if layer in LAYER_ORDER]
    if name in ("verse", "pre_chorus") and "hook_lead" in allowed:
        allowed.remove("hook_lead")
    return tuple(allowed)


def _skeleton(include_intro: bool, include_bridge: bool, include_outro: bool) -> list[str]:
    names: list[str] = []
    if include_intro:
        names.append("intro")
    names.append("verse")
    names.append("pre_chorus")
    names.append("hook")
    if include_bridge:
        names.append("bridge")
    names.append("hook")
    if include_outro:
        names.append("outro")
    return names


def plan_sections(
    bpm: float,
    duration_sec: float,
    include_intro: bool = True,
    include_outro: bool = True,
    include_bridge: bool = True,
    n_verses: int = 2,
    n_choruses: int = 2,
) -> list[SectionPlan]:
    """Раскладывает целевую длительность на осмысленные секции.

    Скелет: intro → (verse → pre_chorus → hook) × n → bridge → hook × n → outro.
    Если тактов меньше, чем нужно для скелета, секции укорачиваются
    пропорционально, но не меньше двух тактов; если больше — добавляются
    пары «куплет + припев», а не бесконечный луп одного припева.
    """
    if bpm <= 0:
        raise ValueError("bpm must be positive")
    bar_sec = 240.0 / float(bpm)
    target_bars = max(8, int(round(max(duration_sec, 1.0) / bar_sec)))

    names: list[str] = []
    if include_intro:
        names.append("intro")
    for index in range(max(1, n_verses)):
        names.extend(["verse", "pre_chorus", "hook"])
    if include_bridge:
        names.append("bridge")
    for _ in range(max(1, n_choruses) - 1):
        names.append("hook")
    if include_outro:
        names.append("outro")

    # Короткий заказ: лишние секции убираем, а не растягиваем трек. Секция
    # короче двух тактов не читается, поэтому «минимум» = 2 такта на секцию.
    def _drop_one() -> bool:
        for candidate in ("pre_chorus", "bridge", "hook", "verse"):
            for index in range(len(names) - 1, -1, -1):
                if names[index] != candidate:
                    continue
                if names.count(candidate) > 1 or candidate in ("pre_chorus", "bridge"):
                    del names[index]
                    return True
        return False

    while len(names) > 2 and len(names) * 2 > target_bars:
        if not _drop_one():
            break

    weights = [BASE_BARS.get(name, 4) for name in names]
    total_weight = sum(weights)
    bars = [max(2, int(round(weight / total_weight * target_bars))) for weight in weights]

    # Догоняем/срезаем разницу за счёт припевов: это музыкально безопаснее всего.
    hook_indexes = [index for index, name in enumerate(names) if name == "hook"]
    diff = target_bars - sum(bars)
    guard = 0
    while diff != 0 and guard < 512:
        guard += 1
        if diff > 0:
            index = hook_indexes[len(hook_indexes) // 2] if hook_indexes else len(bars) - 1
            bars[index] += 1
            diff -= 1
        else:
            candidates = [i for i, value in enumerate(bars) if value > 2]
            if not candidates:
                break
            bars[candidates[-1]] -= 1
            diff += 1

    plans = [
        SectionPlan(
            name=name,
            bars=bars[index],
            energy=SECTION_ENERGY.get(name, 0.6),
            layers=layers_for_section(name, SECTION_ENERGY.get(name, 0.6)),
        )
        for index, name in enumerate(names)
    ]
    return plans


def hook_position(sections: list[SectionPlan], bpm: float) -> float:
    """Секунда, на которой начинается первый припев."""
    bar_sec = 240.0 / float(bpm)
    cursor = 0.0
    for section in sections:
        if section.name in ("hook", "chorus"):
            return round(cursor, 2)
        cursor += section.bars * bar_sec
    return round(cursor, 2)


def hook_motif_start_sec(sections: list[SectionPlan], bpm: float) -> float:
    """Когда впервые звучит мотив хука.

    Если интро содержит слой `hook_lead`, мотив слышен с нулевой секунды —
    это и есть правило TikTok-входа. Иначе ждём первый припев.
    """
    bar_sec = 240.0 / float(bpm)
    cursor = 0.0
    for section in sections:
        if "hook_lead" in section.layers:
            return round(cursor, 2)
        cursor += section.bars * bar_sec
    return hook_position(sections, bpm)


def hook_within_limit(sections: list[SectionPlan], bpm: float) -> bool:
    """Правило TikTok: мотив хука должен звучать в первые 15 секунд."""
    return hook_motif_start_sec(sections, bpm) <= HOOK_WITHIN_SEC


def total_seconds(sections: list[SectionPlan], bpm: float) -> float:
    bar_sec = 240.0 / float(bpm)
    return round(sum(section.bars for section in sections) * bar_sec, 2)


def structure_report(sections: list[SectionPlan], bpm: float) -> dict:
    """Сводка для логов и отчёта: структура, энергия, дроп-контраст."""
    hooks = [section.energy for section in sections if section.name in ("hook", "chorus")]
    verses = [section.energy for section in sections if section.name == "verse"]
    drop_contrast = round(max(hooks) - min(verses), 3) if hooks and verses else 0.0
    return {
        "total_sec": total_seconds(sections, bpm),
        "sections": [
            {
                "name": section.name,
                "bars": section.bars,
                "energy": section.energy,
                "gain_db": section.gain_db,
                "bass_gain": section.bass_gain,
                "layers": list(section.layers),
            }
            for section in sections
        ],
        "hook_start_sec": hook_position(sections, bpm),
        "hook_motif_start_sec": hook_motif_start_sec(sections, bpm),
        "hook_within_15s": hook_within_limit(sections, bpm),
        "drop_contrast": drop_contrast,
        "max_layers": max((len(section.layers) for section in sections), default=0),
    }
