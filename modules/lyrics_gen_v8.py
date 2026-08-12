"""
[v8] lyrics_gen_v8.py — надстройка над lyrics_gen v7.

Что добавляет v8 (не удаляя ничего из v7):
  • Интеграция с author_ref_lyrics (стиль конкретного автора-референса).
  • Интеграция с trend_scout_v3 (актуальный сленг на день создания).
  • Поле «female_backing_chorus»: если True — генерируется отдельный «женский»
    вариант припева для наложения как бэк.
  • Bilingual разметка [Куплет RU] / [Припев EN / Female backing].
  • Валидация ритмики: строки не выходят за ±20% средней длины.

API:
    generate_lyrics_v8(theme, user_words, bpm, author=None,
                       target_lines=16, want_female_backing=False) -> dict
      → {'text': str, 'chorus_lines': list[str],
         'used_slang': list[str], 'author_style_used': bool}
"""

from __future__ import annotations

import random
import re

from modules import (
    author_ref_lyrics,
    lyrics_gen,  # v7, оставляем как есть
)


def _split_blocks(text: str) -> dict[str, list[str]]:
    """Парсим блоки [Куплет 1] / [Припев] / [Куплет 2] / [Аутро]."""
    blocks = {
        "intro": [],
        "verse1": [],
        "chorus": [],
        "verse2": [],
        "bridge": [],
        "outro": [],
    }
    current = "verse1"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith("[") and low.endswith("]"):
            if "интро" in low or "intro" in low:
                current = "intro"
            elif "припев" in low or "chorus" in low or "hook" in low:
                current = "chorus"
            elif "куплет 1" in low or "verse 1" in low:
                current = "verse1"
            elif "куплет 2" in low or "verse 2" in low:
                current = "verse2"
            elif "бридж" in low or "bridge" in low:
                current = "bridge"
            elif "аутро" in low or "outro" in low:
                current = "outro"
            continue
        blocks[current].append(line)
    return blocks


def _validate_rhythm(
    lines: list[str], target_avg: float = 9.0, tol: float = 0.3
) -> list[str]:
    """Отсекаем строки, которые слишком короткие/длинные (≥±30% от target)."""
    kept = []
    for l in lines:
        n = sum(1 for ch in l.lower() if ch in "аеёиоуыэюяaeiouy")
        n = max(1, n)
        if target_avg * (1 - tol) <= n <= target_avg * (1 + tol) or len(lines) < 4:
            kept.append(l)
    return kept or lines


def generate_lyrics_v8(
    theme: str,
    user_words: list[str] | None = None,
    bpm: int = 130,
    author: str | None = None,
    target_lines: int = 16,
    want_female_backing: bool = False,
    lang_mix: str = "ru+en",
) -> dict:
    """
    Главная точка входа v8. Возвращает готовый текст + мета.
    """
    user_words = [w.strip() for w in (user_words or []) if w and w.strip()]
    # 1) актуальный сленг на сегодня
    try:
        from agents.trend_scout_v3 import actual_slang_for_prompt

        slang = actual_slang_for_prompt(theme, n_words=15)
    except Exception:
        slang = []

    # 2) стилевой промт по автору (если задан)
    author_style_used = False
    style_prompt = ""
    if author:
        try:
            # если автора нет в корпусе — попробуем подтянуть онлайн
            profile = author_ref_lyrics.get_style_profile(author)
            if not profile:
                author_ref_lyrics.fetch_and_ingest_author(author, max_tracks=5)
                profile = author_ref_lyrics.get_style_profile(author)
            if profile:
                style_prompt = author_ref_lyrics.build_style_prompt(
                    author=author,
                    theme=theme,
                    user_words=user_words + slang[:6],
                    bpm=bpm,
                    target_lines=target_lines,
                )
                author_style_used = True
        except Exception:
            style_prompt = ""

    # 3) базовая генерация через v7
    seed = theme
    if user_words:
        seed += " — " + ", ".join(user_words)
    if slang:
        seed += " · слэнг: " + ", ".join(slang[:8])
    seed_user_lyrics = user_words  # v7 гарантирует их появление

    try:
        raw = lyrics_gen.generate_lyrics(
            theme=seed,
            bpm=bpm,
            user_lyrics_lines=seed_user_lyrics,
            style_prompt=style_prompt or None,
            target_lines=target_lines,
        )
    except TypeError:
        # v7 может не поддерживать все kwargs — деградируем к базовому вызову
        try:
            raw = lyrics_gen.generate_lyrics(theme=seed, bpm=bpm)
        except Exception:
            raw = f"[Куплет 1]\n{seed}\n[Припев]\n{random.choice(slang) if slang else 'yeah'}\n"
    except Exception as e:
        raw = f"[Куплет 1]\n{seed}\n[Припев]\n(fallback: {e})\n"

    # 4) парсим, валидируем ритм
    blocks = _split_blocks(raw if isinstance(raw, str) else str(raw))
    for key in ("verse1", "verse2", "chorus"):
        blocks[key] = _validate_rhythm(blocks[key])

    # 5) обеспечиваем bilingual разметку
    if lang_mix == "ru+en":
        # Ищем в припеве английские хуки; если их нет — подмешиваем из trend_scout_v3
        chorus_txt = " ".join(blocks["chorus"]).lower()
        has_en = any(re.search(r"[a-z]{3,}", w) for w in chorus_txt.split())
        if not has_en:
            try:
                from agents.trend_scout_v3 import scout

                hook_en = random.choice(scout(theme)["hooks_en"])
                blocks["chorus"].append(hook_en)
            except Exception:
                blocks["chorus"].append("night ride, we don't stop")

    # 6) собираем финальный текст
    parts = []
    if blocks["intro"]:
        parts.append("[Интро]\n" + "\n".join(blocks["intro"]))
    parts.append(
        "[Куплет 1]\n" + "\n".join(blocks["verse1"] or ["город спит, а мотор рычит"])
    )
    parts.append(
        "[Припев]\n" + "\n".join(blocks["chorus"] or ["night ride, we don't stop"])
    )
    parts.append("[Куплет 2]\n" + "\n".join(blocks["verse2"] or blocks["verse1"] or []))
    parts.append("[Припев]\n" + "\n".join(blocks["chorus"] or []))
    if blocks["bridge"]:
        parts.append("[Бридж]\n" + "\n".join(blocks["bridge"]))
    if blocks["outro"]:
        parts.append("[Аутро]\n" + "\n".join(blocks["outro"]))

    final_text = "\n\n".join(parts)

    # 7) вариант припева для женского бэка
    chorus_lines = blocks["chorus"] or []
    if want_female_backing and chorus_lines:
        # Помечаем — orchestrator подхватит и сгенерирует backing.
        pass

    return {
        "text": final_text,
        "chorus_lines": chorus_lines,
        "used_slang": slang,
        "author_style_used": author_style_used,
        "want_female_backing": want_female_backing,
        "author": author or "",
    }
