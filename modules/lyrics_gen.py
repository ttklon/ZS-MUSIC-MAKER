"""
[v7] lyrics_gen.py — генератор текстов с ОБЯЗАТЕЛЬНЫМ впитыванием
пользовательских строк и bilingual структурой (RU куплеты + EN хуки).

Источники (по ТЗ 3.7):
  1. Ollama (Llama 3) — если локально запущено
  2. Trend-Scout — актуальные темы и сленг из интернета
  3. Lyric Vault — локальное хранилище идей
  4. Fallback — шаблонный генератор на встроенных панчах

Ключевое требование ТЗ 20.2 (вопрос 3): user_lyrics_lines — если
пользователь указал свои строки, они ОБЯЗАНЫ попасть в трек, дословно.
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAULT_DIR = ROOT / "lyric_vault"
# v22: ленивое создание (не при импорте)

LYRIC_MEMORY = VAULT_DIR / "lyrics_memory.jsonl"
SLANG_FILE = VAULT_DIR / "slang.txt"

# Панчи по темам — используются как fallback и как затравка для Llama
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


def _load_lyric_memory_with_errors() -> tuple[list, list[str]]:
    """Load valid JSONL memories while retaining line-level recovery diagnostics."""
    if not LYRIC_MEMORY.exists():
        return [], []
    memories: list = []
    errors: list[str] = []
    for line_number, line in enumerate(LYRIC_MEMORY.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            memories.append(json.loads(line))
        except json.JSONDecodeError as error:
            errors.append(f"line {line_number}: {type(error).__name__}: {error}")
    return memories, errors


def _load_lyric_memory() -> list:
    """Return valid lyric memories with the historical list-only private contract."""
    return _load_lyric_memory_with_errors()[0]


def _save_lyric_memory(entry: dict) -> None:
    entry["timestamp"] = time.time()
    with open(LYRIC_MEMORY, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


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


def _try_ollama(prompt: str, model: str = "llama3") -> str | None:
    """Пробуем Ollama через локальный HTTP API."""
    try:
        import requests

        r = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        if r.status_code == 200:
            return r.json().get("response", "").strip()
    except Exception:
        pass
    return None


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


def generate_lyrics(
    theme: str,
    style_vector: dict | None = None,
    n_verses: int = 2,
    user_lyrics_lines: list[str] | None = None,
    bilingual: bool = True,
) -> dict:
    """
    Главный API. Всегда возвращает {'lyrics': str, 'structure': [...], ...}.
    """
    user_lyrics_lines = user_lyrics_lines or []
    style_vector = style_vector or {}
    bpm = int(style_vector.get("target_bpm") or 140)

    # Разделяем пользовательские строки на русские и английские
    user_ru = [l.strip() for l in user_lyrics_lines if l.strip() and not _is_english(l)]
    user_en = [l.strip() for l in user_lyrics_lines if l.strip() and _is_english(l)]

    # Слоговая цель — 6-9 при бампирующем BPM
    syllable_target = 6 if bpm > 150 else 8

    # Попробуем Ollama если запущен
    ollama_prompt = (
        f"Напиши текст трека в стиле phonk/trap/hyperpop, BPM={bpm}, "
        f"тема: {theme}. Куплеты — по-русски, короткие рэп-строчки, "
        f"хук — по-английски, {2 if bilingual else 0} английских строк. "
        f"Обязательные строки: {', '.join(user_lyrics_lines) if user_lyrics_lines else 'нет'}. "
        f"Не пиши комментарии, только текст трека."
    )
    ollama_out = _try_ollama(ollama_prompt)

    if ollama_out and len(ollama_out) > 50:
        lyrics_text = ollama_out
        source = "ollama"
    else:
        # Fallback: template
        punches = _pick_punches(theme, count=8)
        blocks = []
        # Один hook повторяется после каждого куплета: это контролируемая
        # song-structure, а не случайно меняющийся набор строк.
        hook_lines = _template_hook_en(user_en) if bilingual else []
        for i in range(n_verses):
            blocks.append(f"[Куплет {i+1}]")
            blocks.extend(
                _template_verse(
                    punches, user_ru if i == 0 else [], bpm, syllable_target
                )
            )
            if hook_lines:
                blocks.append("[Hook]")
                blocks.extend(hook_lines)
        lyrics_text = "\n".join(blocks)
        source = "template"

    # Гарантируем что все user_lyrics впитаны
    for line in user_lyrics_lines:
        if line.strip() and line.strip() not in lyrics_text:
            lyrics_text += f"\n[User]\n{line.strip()}"

    _save_lyric_memory(
        {
            "theme": theme,
            "bpm": bpm,
            "lyrics": lyrics_text,
            "source": source,
            "user_lines": user_lyrics_lines,
        }
    )

    return {
        "ok": True,
        "lyrics": lyrics_text,
        "source": source,
        "bilingual": bilingual,
        "n_verses": n_verses,
        "bpm": bpm,
        "user_lines_included": all(
            l.strip() in lyrics_text for l in user_lyrics_lines if l.strip()
        ),
    }


def get_lyric_memory(limit: int = 20) -> list:
    """Вернуть последние валидные строки из Lyric Vault."""
    memories = _load_lyric_memory()
    return list(reversed(memories))[:limit]


def get_lyric_memory_diagnostics(limit: int = 20) -> dict:
    """Return recent valid memories together with non-fatal JSONL recovery diagnostics."""
    memories, read_errors = _load_lyric_memory_with_errors()
    return {"memories": list(reversed(memories))[:limit], "read_errors": read_errors}


if __name__ == "__main__":
    r = generate_lyrics(
        "лето, тачки, деньги",
        style_vector={"target_bpm": 140},
        user_lyrics_lines=["ночь горит, Supra летит", "money over everything"],
        bilingual=True,
    )
    print(r["lyrics"])
    print("---")
    print("user_included:", r["user_lines_included"])
