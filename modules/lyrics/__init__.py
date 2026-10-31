# -*- coding: utf-8 -*-
"""
modules.lyrics — генерация текста песни (единственная точка входа).

    memory      Lyric Vault: память идей и диагностика
    punchlines  встроенные панчи, хуки, шаблонные строки
    generate    базовый генератор: Ollama → панчи
    ai          AI-first через локальную роль `lyrics_llm` (честный BLOCKED)
    author      стиль автора-референса + актуальный сленг + билингвальный припев

Жёсткое требование: строки пользователя (`user_lyrics_lines`) попадают в
результат дословно во всех трёх входах.
"""

from __future__ import annotations

from modules.lyrics.ai import generate_lyrics_ai  # noqa: F401 - публичный реэкспорт
from modules.lyrics.author import generate_lyrics_v8  # noqa: F401 - публичный реэкспорт
from modules.lyrics.generate import generate_lyrics  # noqa: F401 - публичный реэкспорт
from modules.lyrics.memory import get_lyric_memory  # noqa: F401 - публичный реэкспорт
from modules.lyrics.memory import get_lyric_memory_diagnostics  # noqa: F401 - публичный реэкспорт

__all__ = [
    "generate_lyrics",
    "generate_lyrics_ai",
    "generate_lyrics_v8",
    "get_lyric_memory",
    "get_lyric_memory_diagnostics",
]
