"""Bounded analysis of user-supplied reference text and creative notes.

This is descriptive word/line counting, not ASR, semantic analysis or live trends.
Raw reference lyrics are not included in the generation prompt or report.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

MAX_REFERENCE_CHARS = 20000
MAX_NOTES_CHARS = 600
_STOP = frozenset("""это этот эта эти был была были быть как что чтобы когда тогда если уже ещё
так там тут где вот мне меня тебе тебя нас вас для над под без или его её она
они оно всё свои свой через очень the and for with that this you your are was
were from into have has not but all our their would about just yeah""".split())
_TOKEN = re.compile(r"[^\W\d_]+(?:[-'][^\W\d_]+)?", re.UNICODE)


def build_lyric_context(reference: str, notes: str) -> tuple[dict[str, Any], str]:
    reference, notes = str(reference or ""), str(notes or "")
    sample, note_sample = reference[:MAX_REFERENCE_CHARS], notes[:MAX_NOTES_CHARS].strip()
    lines = [line.strip() for line in sample.splitlines() if line.strip() and not line.strip().startswith("[")]
    words = [word.lower() for word in _TOKEN.findall("\n".join(lines))]
    counts = Counter(word for word in words if len(word) >= 4 and word not in _STOP)
    keywords = [word for word, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:8]]
    metrics = {
        "reference_source": "user_supplied_text" if sample.strip() else "not_provided",
        "analysis": "word_and_line_counts_only" if sample.strip() else "not_performed",
        "lines": len(lines),
        "words": len(words),
        "mean_words_per_line": round(len(words) / len(lines), 1) if lines else 0,
        "keywords": keywords,
        "reference_truncated": len(reference) > MAX_REFERENCE_CHARS,
        "trend_source": "user_notes_unverified" if note_sample else "not_provided",
        "trend_notes_truncated": len(notes) > MAX_NOTES_CHARS,
        "live_trend_research": False,
    }
    parts = []
    if lines:
        parts.append(f"Данные ручного текстового референса: строк {len(lines)}, "
                     f"среднее число слов в строке {metrics['mean_words_per_line']}; "
                     f"частые слова: {', '.join(keywords) or 'нет'}. "
                     "Не копируй исходные строки и создай оригинальный текст.")
    if note_sample:
        parts.append(f"Заметки пользователя о языке и темах (не проверенные тренды): {note_sample}")
    return metrics, "\n".join(parts)
