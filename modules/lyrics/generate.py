# -*- coding: utf-8 -*-
"""
modules/lyrics/generate.py — базовый генератор текста.

Порядок источников: Ollama (если поднята) → punch-библиотека. Строки
пользователя (`user_lyrics_lines`) всегда попадают в результат дословно —
это требование ТЗ, а не пожелание.
"""

from __future__ import annotations


from modules.lyrics.memory import _save_lyric_memory
from modules.lyrics.punchlines import (
    _is_english,
    _pick_punches,
    _template_hook_en,
    _template_verse,
)


def _try_ollama_with_diagnostics(prompt: str, model: str = "llama3") -> dict:
    """Пробует local Ollama и раскрывает status without claiming generation."""
    try:
        import requests

        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        if response.status_code == 200:
            text = response.json().get("response", "").strip()
            return {"text": text or None, "status": "responded" if text else "empty_response"}
        return {"text": None, "status": "http_error", "http_status": response.status_code}
    except Exception as exc:
        return {"text": None, "status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}


def _try_ollama(prompt: str, model: str = "llama3") -> str | None:
    """Совместимый local Ollama helper для existing lyrics callers."""
    return _try_ollama_with_diagnostics(prompt, model)["text"]


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
