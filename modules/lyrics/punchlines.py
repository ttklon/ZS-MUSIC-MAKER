# -*- coding: utf-8 -*-
"""
modules/lyrics/punchlines.py — встроенная библиотека панчей и шаблоны.

Последний рубеж генерации текста: если LLM недоступен, строки собираются из
пула панчей по теме и английских хуков — без обращения к сети.
"""

from __future__ import annotations

import random

PUNCHES_RU = {
    "лето": [
        "солнце жарит, плавит асфальт",
        "лето без страховки, полный газ вдаль",
        "тачка без крыши, ветер в лицо",
        "закат на Стамбул, золотое кольцо",
        "море, деньги, драйв — это наш финал",
        "жаркие ночи, танцпол закипал",
        "песок под ногами, ритм в груди",
        "лето не кончится, всё впереди",
    ],
    "тачки": [
        "Supra рвёт тишину, турбина свистит",
        "AMG в ночи, как чёрный магнит",
        "мотор кричит, просит ещё",
        "полёт по трассе, время течёт",
        "дрифт в тумане, жжёная резина",
        "скорость — мой яд, адреналин — бензин",
        "низкий клиренс, дерзкий обвес",
        "мы короли улиц, у нас есть вес",
    ],
    "деньги": [
        "кэш на кэше, стопки до небес",
        "чек за чеком, ловим интерес",
        "мани мани моуш, крутим дела",
        "деньги в кармане, удача пришла",
        "бриллианты блестят, как звёзды в ночи",
        "золотые цепи, от сейфа ключи",
        "успех — это труд, а не просто фарт",
        "мы строим империю, это наш старт",
    ],
    "движ": [
        "ночь моя, я в центре огней",
        "движ до утра, зови всех друзей",
        "клуб на пике, бас бьёт в висок",
        "звук качает, просыпайся, город-игрок",
        "лица в свете, тени в углах",
        "энергия прёт, забыли про страх",
        "мы здесь и сейчас, это наш момент",
        "музыка — жизнь, лучший элемент",
    ],
    "турция": [
        "Стамбул горит миллионами ламп",
        "Босфор шумит, проплывая сквозь храм",
        "чай крепче кофе, разговор до утра",
        "Турция как второй дом, родная земля",
        "Анталия ждёт, тёплый бриз у воды",
        "древние камни, наши следы",
        "восточная сказка в реальности дня",
        "здесь каждый закат — для тебя и меня",
    ],
    "агрессия": [
        "без тормозов, летим напролом",
        "рубим наотмашь, крушим этот дом",
        "молчание — предатель, кричи во весь голос",
        "рвём этот бит, как коса спелый колос",
        "ярость в глазах, сила в руках",
        "мы победим, оставив всех в дураках",
        "сталь в характере, лёд в словах",
        "путь к вершине — через боль и страх",
    ],
}


HOOKS_EN = [
    "money over everything, we never look back",
    "night, drift, we ride, strictly on track",
    "summer, cars, get high, feel the heat",
    "no brakes, we win, victory is sweet",
    "vibe on repeat, loud in the street",
    "shining like a star, never accept defeat",
    "put your hands up, touch the sky",
    "let it burn tonight, let the sparks fly",
    "we don't stop, we own the game",
    "living on the edge, remember the name",
    "top down, cruising, feeling so free",
    "this is the life, how it's meant to be",
]


def _pick_punches(theme: str, count: int = 4) -> list[str]:
    """Собираем панчи по темам из строки-запроса."""
    theme_lower = (theme or "").lower()
    collected = []
    
    # Если это шансон или тюремная/жизненная лирика
    if "шансон" in theme_lower or "централ" in theme_lower or "ветер" in theme_lower or "жиган" in theme_lower:
        collected.extend([
            "Владимирский централ, ветер северный,",
            "Этапный путь до тюрьмы, до каторги.",
            "Кольщик, наколо мне купола да кресты,",
            "Чтобы память жила до черты.",
            "А на воле весна, магаданский туман,",
            "Облака плывут в океан.",
            "Жиган-монпансье, воля вольная,",
            "Душа моя больная, доля горькая."
        ])
        
    for key, punches in PUNCHES_RU.items():
        if key in theme_lower:
            collected.extend(punches)
            
    if not collected:
        for punches in PUNCHES_RU.values():
            collected.extend(punches)
            
    random.shuffle(collected)
    return collected[:count]


def _template_verse(
    punches: list[str], user_lines: list[str], bpm: int, syllable_target: int
) -> list[str]:
    """Собираем куплет из панчей и пользовательских строк."""
    lines = []
    used_user = 0
    for i in range(16):
        if used_user < len(user_lines) and i in (0, 2):
            lines.append(user_lines[used_user])
            used_user += 1
        else:
            # Цикл по заранее перемешанному punch-list исключает случайный
            # loop одного и того же бара, но сохраняет разнообразие по теме.
            base = punches[i % len(punches)] if punches else "движ на движ"
            lines.append(base)
    # Оставшиеся пользовательские — добавим в конец
    for extra in user_lines[used_user:]:
        lines.append(extra)
    return lines


def _template_hook_en(user_hooks: list[str]) -> list[str]:
    """English хук: сначала пользовательские EN-строки, потом из HOOKS_EN."""
    en_user = [l for l in user_hooks if _is_english(l)]
    hook = list(en_user)[:2]
    while len(hook) < 2:
        cand = random.choice(HOOKS_EN)
        if cand not in hook:
            hook.append(cand)
    return hook * 2  # 4 строки припева


def _is_english(s: str) -> bool:
    """Груборечивая эвристика: строка содержит только ASCII/латиницу."""
    if not s:
        return False
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    ascii_letters = sum(1 for c in letters if ord(c) < 128)
    return ascii_letters / len(letters) > 0.8
