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
        "солнце жарит",
        "лето без страховки",
        "тачка без крыши",
        "закат на Стамбул",
        "море, деньги, драйв",
    ],
    "тачки": [
        "Supra рвёт",
        "AMG в ночи",
        "мотор кричит",
        "полёт по трассе",
        "дрифт в тумане",
    ],
    "деньги": [
        "кэш на кэше",
        "чек за чеком",
        "мани мани моуш",
        "деньги в кармане, вайб на автомате",
    ],
    "движ": ["ночь моя", "движ до утра", "клуб на пике", "звук качает", "лица в свете"],
    "турция": [
        "Стамбул горит",
        "Босфор шумит",
        "чай крепче кофе",
        "Турция как второй дом",
    ],
    "агрессия": [
        "без тормозов",
        "рубим наотмашь",
        "молчание — предатель",
        "рвём этот бит",
    ],
}

HOOKS_EN = [
    "money over everything",
    "night, drift, we ride",
    "summer, cars, get high",
    "no brakes, we win",
    "vibe on repeat",
    "shining like a star",
    "put your hands up",
    "let it burn tonight",
    "we don't stop",
    "living on the edge",
]


def _load_lyric_memory() -> list:
    if not LYRIC_MEMORY.exists():
        return []
    out = []
    for line in LYRIC_MEMORY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def _save_lyric_memory(entry: dict) -> None:
    entry["timestamp"] = time.time()
    with open(LYRIC_MEMORY, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _pick_punches(theme: str, count: int = 4) -> list[str]:
    """Собираем панчи по темам из строки-запроса."""
    theme_lower = (theme or "").lower()
    collected = []
    for key, punches in PUNCHES_RU.items():
        if key in theme_lower:
            collected.extend(punches)
    if not collected:
        # Дефолт — микс всего
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
    for i in range(4):
        if used_user < len(user_lines) and i in (0, 2):
            lines.append(user_lines[used_user])
            used_user += 1
        else:
            base = random.choice(punches) if punches else "движ на движ"
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
        for i in range(n_verses):
            blocks.append(f"[Куплет {i+1}]")
            blocks.extend(
                _template_verse(
                    punches, user_ru if i == 0 else [], bpm, syllable_target
                )
            )
            if bilingual:
                blocks.append("[Hook]")
                blocks.extend(_template_hook_en(user_en))
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
    """Вернуть последние строки из Lyric Vault."""
    mem = _load_lyric_memory()
    return list(reversed(mem))[:limit]


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
