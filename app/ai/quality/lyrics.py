# -*- coding: utf-8 -*-
"""
app/ai/quality/lyrics.py — детерминированные проверки текста.

Валидатор не судит художественность. Он отсекает объективно непригодное:
пустой/слишком короткий текст, дубли строк, «AI-мусор» вроде «в этом
стихотворении», отсутствие обязательных пользовательских строк.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9']+")


def lyrics_metrics(text: str) -> dict[str, float | int]:
    """Вернуть воспроизводимые метрики длины и повторяемости текста песни."""
    normalized_lines = [
        re.sub(r"\s+", " ", line.strip()).lower()
        for line in (text or "").splitlines()
        if line.strip() and not line.lstrip().startswith("[")
    ]
    tokens = TOKEN_RE.findall((text or "").lower())
    line_counts = Counter(normalized_lines)
    max_repeated_line = max(line_counts.values(), default=0)
    unique_ratio = len(set(tokens)) / len(tokens) if tokens else 0.0
    return {
        "characters": len((text or "").strip()),
        "lines": len(normalized_lines),
        "tokens": len(tokens),
        "unique_token_ratio": round(unique_ratio, 3),
        "max_repeated_line": max_repeated_line,
    }


def validate_lyrics(text: str, *, min_characters: int = 60) -> dict[str, Any]:
    """Проверить минимальную пригодность текста для следующей audio-стадии."""
    metrics = lyrics_metrics(text)
    if not (text or "").strip():
        return {"ok": False, "reason": "empty lyrics", "metrics": metrics}
    if metrics["characters"] < min_characters:
        return {
            "ok": False,
            "reason": f"lyrics shorter than {min_characters} characters",
            "metrics": metrics,
        }
    if metrics["tokens"] < 12:
        return {"ok": False, "reason": "too few lyric tokens", "metrics": metrics}
    # До четырёх повторов допустимы для припева; больше — признак зацикливания.
    if metrics["max_repeated_line"] > 4:
        return {"ok": False, "reason": "line repetition exceeds hook limit", "metrics": metrics}
    if metrics["unique_token_ratio"] < 0.12:
        return {"ok": False, "reason": "token diversity too low", "metrics": metrics}
    return {"ok": True, "reason": None, "metrics": metrics}


def validate_song_lyrics(text: str, *, user_lines: list[str] | None = None,
                         min_words: int = 200, max_words: int = 800) -> dict[str, Any]:
    """Проверить release-структуру текста после базового lexical quality gate."""
    base = validate_lyrics(text, min_characters=60)
    metrics = dict(base["metrics"])
    lower = (text or "").lower()
    headers = [line.strip().lower() for line in (text or "").splitlines() if line.strip().startswith("[")]
    verse_headers = sum("куплет" in header or "verse" in header for header in headers)
    hook_headers = sum(any(marker in header for marker in ("припев", "hook", "chorus")) for header in headers)
    requested = [line.strip() for line in (user_lines or []) if line.strip()]
    included = [line for line in requested if line.lower() in lower]
    filler_terms = ("нейра-говно", "как ии", "language model", "as an ai")
    filler_hits = [term for term in filler_terms if term in lower]
    metrics.update({
        "words": metrics["tokens"],
        "verse_headers": verse_headers,
        "hook_headers": hook_headers,
        "user_lines_requested": len(requested),
        "user_lines_included": len(included),
        "filler_hits": filler_hits,
    })
    # Длинный structured текст закономерно повторяет служебные слова и hook.
    # Для release-form допускаем более низкую lexical diversity только при
    # сохранённом base repetition limit и последующих structure checks.
    if not base["ok"] and not (
        base["reason"] == "token diversity too low"
        and float(metrics["unique_token_ratio"]) >= 0.08
        and int(metrics["max_repeated_line"]) <= 4
    ):
        return {"ok": False, "reason": base["reason"], "metrics": metrics}
    if not min_words <= metrics["words"] <= max_words:
        return {"ok": False, "reason": "lyrics word count is outside release range", "metrics": metrics}
    if verse_headers < 2:
        return {"ok": False, "reason": "lyrics require at least two verses", "metrics": metrics}
    if hook_headers < 2:
        return {"ok": False, "reason": "lyrics require a repeated hook", "metrics": metrics}
    if len(included) != len(requested):
        return {"ok": False, "reason": "lyrics omit required user lines", "metrics": metrics}
    if filler_hits:
        return {"ok": False, "reason": "lyrics contain prohibited AI filler", "metrics": metrics}
    return {"ok": True, "reason": None, "metrics": metrics}
