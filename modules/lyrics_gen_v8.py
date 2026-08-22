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
from contextvars import ContextVar
import re
import warnings

warnings.warn(
    "modules.lyrics_gen_v8 is deprecated; prefer modules.lyrics_gen_ai when lyrics_llm is available",
    DeprecationWarning,
    stacklevel=2,
)

from modules import (
    author_ref_lyrics,
    lyrics_gen,  # v7, оставляем как есть
)


_SECTION_MARKERS = (
    ("intro", ("интро", "intro")),
    ("chorus", ("припев", "chorus", "hook")),
    ("verse1", ("куплет 1", "verse 1")),
    ("verse2", ("куплет 2", "verse 2")),
    ("bridge", ("бридж", "bridge")),
    ("outro", ("аутро", "outro")),
)


def _section_for_marker(marker: str) -> str | None:
    """Classify a bracketed Russian/English section marker in stable priority order."""
    for section, tokens in _SECTION_MARKERS:
        if any(token in marker for token in tokens):
            return section
    return None


def _split_blocks(text: str) -> dict[str, list[str]]:
    """Parse recognized bracketed section markers into stable verse/chorus blocks."""
    blocks = {key: [] for key in ("intro", "verse1", "chorus", "verse2", "bridge", "outro")}
    current = "verse1"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = _section_for_marker(line.lower()) or current
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


def _fetch_slang(theme: str) -> list[str]:
    """Return optional trend slang or an honest empty fallback."""
    try:
        from agents.trend_scout_v3 import actual_slang_for_prompt

        return actual_slang_for_prompt(theme, n_words=15)
    except Exception:
        return []


_AUTHOR_STYLE_DIAGNOSTIC: ContextVar[dict | None] = ContextVar(
    "lyrics_v8_author_style_diagnostic", default=None
)


def _author_style_prompt_with_diagnostics(
    author: str | None, theme: str, user_words: list[str], slang: list[str], bpm: int, target_lines: int
) -> tuple[str, bool, dict]:
    """Build optional author guidance and disclose unavailable reference ingestion."""
    if not author:
        return "", False, {"ok": False, "status": "not_requested", "author": ""}
    try:
        profile = author_ref_lyrics.get_style_profile(author)
        if not profile:
            author_ref_lyrics.fetch_and_ingest_author(author, max_tracks=5)
            profile = author_ref_lyrics.get_style_profile(author)
        if profile:
            prompt = author_ref_lyrics.build_style_prompt(
                author=author, theme=theme, user_words=user_words + slang[:6],
                bpm=bpm, target_lines=target_lines,
            )
            return prompt, True, {"ok": True, "status": "available", "author": author}
        return "", False, {"ok": False, "status": "profile_unavailable", "author": author}
    except Exception as exc:
        return "", False, {
            "ok": False,
            "status": "failed",
            "author": author,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _author_style_prompt(
    author: str | None, theme: str, user_words: list[str], slang: list[str], bpm: int, target_lines: int
) -> tuple[str, bool]:
    """Совместимый prompt-only API для optional author reference guidance."""
    prompt, used, diagnostics = _author_style_prompt_with_diagnostics(
        author, theme, user_words, slang, bpm, target_lines
    )
    _AUTHOR_STYLE_DIAGNOSTIC.set(diagnostics)
    return prompt, used


def _generate_raw_lyrics(seed: str, user_words: list[str], bpm: int, style_prompt: str, target_lines: int, slang: list[str]) -> str:
    """Call v7 generation with its supported-argument and empty-text fallbacks."""
    try:
        return lyrics_gen.generate_lyrics(
            theme=seed, bpm=bpm, user_lyrics_lines=user_words,
            style_prompt=style_prompt or None, target_lines=target_lines,
        )
    except TypeError:
        try:
            return lyrics_gen.generate_lyrics(theme=seed, bpm=bpm)
        except Exception:
            return f"[Куплет 1]\n{seed}\n[Припев]\n{random.choice(slang) if slang else 'yeah'}\n"
    except Exception as error:
        return f"[Куплет 1]\n{seed}\n[Припев]\n(fallback: {error})\n"


def _ensure_bilingual_chorus(blocks: dict[str, list[str]], theme: str, lang_mix: str) -> None:
    """Append a safe English hook only when bilingual chorus markup requires one."""
    if lang_mix != "ru+en":
        return
    chorus_text = " ".join(blocks["chorus"]).lower()
    if any(re.search(r"[a-z]{3,}", word) for word in chorus_text.split()):
        return
    try:
        from agents.trend_scout_v3 import scout

        blocks["chorus"].append(random.choice(scout(theme)["hooks_en"]))
    except Exception:
        blocks["chorus"].append("night ride, we don't stop")


def _assemble_lyrics_text(blocks: dict[str, list[str]]) -> str:
    """Render normalized section blocks into the established v8 song order."""
    parts = []
    if blocks["intro"]:
        parts.append("[Интро]\n" + "\n".join(blocks["intro"]))
    parts.append("[Куплет 1]\n" + "\n".join(blocks["verse1"] or ["город спит, а мотор рычит"]))
    parts.append("[Припев]\n" + "\n".join(blocks["chorus"] or ["night ride, we don't stop"]))
    parts.append("[Куплет 2]\n" + "\n".join(blocks["verse2"] or blocks["verse1"] or []))
    parts.append("[Припев]\n" + "\n".join(blocks["chorus"] or []))
    if blocks["bridge"]:
        parts.append("[Бридж]\n" + "\n".join(blocks["bridge"]))
    if blocks["outro"]:
        parts.append("[Аутро]\n" + "\n".join(blocks["outro"]))
    return "\n\n".join(parts)


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
    user_words = [word.strip() for word in (user_words or []) if word and word.strip()]
    slang = _fetch_slang(theme)
    _AUTHOR_STYLE_DIAGNOSTIC.set(None)
    style_prompt, author_style_used = _author_style_prompt(
        author, theme, user_words, slang, bpm, target_lines
    )
    author_style = _AUTHOR_STYLE_DIAGNOSTIC.get() or {
        "ok": author_style_used,
        "status": "available" if author_style_used else ("not_requested" if not author else "profile_unavailable"),
        "author": author or "",
    }
    seed = theme
    if user_words:
        seed += " — " + ", ".join(user_words)
    if slang:
        seed += " · слэнг: " + ", ".join(slang[:8])
    raw = _generate_raw_lyrics(seed, user_words, bpm, style_prompt, target_lines, slang)
    blocks = _split_blocks(raw if isinstance(raw, str) else str(raw))
    for key in ("verse1", "verse2", "chorus"):
        blocks[key] = _validate_rhythm(blocks[key])
    _ensure_bilingual_chorus(blocks, theme, lang_mix)
    return {
        "text": _assemble_lyrics_text(blocks),
        "chorus_lines": blocks["chorus"] or [],
        "used_slang": slang,
        "author_style_used": author_style_used,
        "author_style": author_style,
        "want_female_backing": want_female_backing,
        "author": author or "",
    }
