# -*- coding: utf-8 -*-
"""Лёгкие детерминированные проверки outputs локальных LLM-ролей.

Валидаторы не оценивают художественную ценность текста. Они отсекают только
объективно непригодные результаты: пустой/слишком короткий ответ, чрезмерные
дубли строк и неполное структурированное досье. Это позволяет честно включать
fallback до сохранения артефакта на диск.
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


def validate_analysis_json(payload: Any, *, track_level: bool = False) -> dict[str, Any]:
    """Проверить минимальный контракт JSON-ответа analysis_llm."""
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "analysis response is not an object", "metrics": {}}

    required = ("storyline", "hook", "reusable_elements") if track_level else (
        "core_themes",
        "lexicon",
        "flow",
    )
    missing = [key for key in required if not payload.get(key)]
    if missing:
        return {
            "ok": False,
            "reason": "missing analysis fields: " + ", ".join(missing),
            "metrics": {"keys": len(payload), "missing": len(missing)},
        }
    return {
        "ok": True,
        "reason": None,
        "metrics": {"keys": len(payload), "missing": 0},
    }
