# -*- coding: utf-8 -*-
"""ZS Music Maker - app/ai/prompts.py (v38): промпты для локальных LLM."""
from __future__ import annotations

SYSTEM_LYRICS = """Ты - русскоязычный автор-хитмейкер (рэп/трэп/фонк/поп-рэп/шансон). Правила:
1. Каждая строчка двигает историю, даёт punchline или усиливает эмоцию. Никаких пустых нейро-наборов.
2. Живой язык: сленг, конкретика, детали - не абстракции.
3. 6-10 слогов в строке под BPM. Схема AABB или ABAB, внутренние рифмы приветствуются.
4. Куплет = развитие мысли, не 4 несвязанных афоризма.
5. Хук = короткая цепляющая фраза, повтор 2-4 раза.
6. Референс-артиста соблюдать по лексике/флоу, но НЕ копировать его строки.
7. Только чистый текст с метками [Куплет 1]/[Припев]/[Bridge]. Без комментариев."""

SYSTEM_ANALYSIS = """Ты - музыкальный аналитик. Строишь досье артиста на русском в JSON:
{"core_themes": [...], "lexicon": [...], "flow": "...", "rhyme_style": "...",
"emotional_range": [...], "signature_tricks": [...], "audience": "...",
"story_arcs": [...], "avoid": [...]}
Только валидный JSON без комментариев."""

SYSTEM_TRACK_ANALYSIS = """Ты - аналитик отдельного трека. Выдай JSON:
{"title_meaning": "...", "storyline": "...",
"line_breakdown": [{"line": "...", "meaning": "...", "device": "..."}],
"hook": "...", "hook_repetitions": N, "energy_curve": "...",
"reusable_elements": [...]}
Только валидный JSON. line_breakdown обязателен для каждой строки."""

SYSTEM_METADATA = """Ты - маркетолог инди-музыки. Выдай JSON:
{title, spotify_desc, youtube_desc, tags_tiktok (15), tags_instagram (10)}.
Только валидный JSON, без комментариев."""


def build_lyrics_prompt(theme, genre, bpm, n_verses, bilingual,
                        user_lines=None, artist_dossier=None, track_reference=None):
    parts = [f"Тема: {theme}", f"Жанр: {genre}", f"BPM: {bpm}",
             f"Куплетов: {n_verses}",
             f"Билингвал (RU куплеты + EN хук): {'да' if bilingual else 'нет'}"]
    if user_lines:
        parts.append("ОБЯЗАТЕЛЬНЫЕ строки (впитать дословно):")
        parts += [f"  - {l}" for l in user_lines]
    if artist_dossier:
        parts.append("Стиль референс-артиста (досье):")
        parts.append(f"  темы: {', '.join(artist_dossier.get('core_themes', [])[:8])}")
        parts.append(f"  лексика: {', '.join(artist_dossier.get('lexicon', [])[:15])}")
        parts.append(f"  флоу: {artist_dossier.get('flow', '-')}")
        parts.append(f"  фишки: {', '.join(artist_dossier.get('signature_tricks', [])[:5])}")
        parts.append(f"  избегает: {', '.join(artist_dossier.get('avoid', [])[:5])}")
    if track_reference:
        parts.append("Референс-трек (в его духе, не копия):")
        parts.append(f"  сюжет: {track_reference.get('storyline', '-')}")
        parts.append(f"  hook: {track_reference.get('hook', '-')}")
        parts.append(f"  энергия: {track_reference.get('energy_curve', '-')}")
    parts.append("")
    parts.append("Пиши текст трека сейчас. Без комментариев.")
    return "\n".join(parts)


def build_dossier_prompt(artist, tracks_text):
    return (f"Артист: {artist}\n\nВсе известные тексты:\n=====\n"
            f"{tracks_text[:20000]}\n=====\n\nПострой досье JSON строго по schema.")


def build_track_dossier_prompt(title, lyrics, features):
    return (f"Трек: {title}\nBPM: {features.get('bpm', '?')}\n"
            f"Тональность: {features.get('key', '?')}\n"
            f"Теги (авто): {', '.join(features.get('tags', []))}\n"
            f"Длительность: {features.get('duration_sec', '?')} сек\n\n"
            f"Текст:\n=====\n{lyrics}\n=====\n\nВерни JSON по schema.")


def build_metadata_prompt(theme, style, snippet):
    return (f"Тема: {theme}\nСтиль: {style}\n\nКусок лирики:\n{snippet[:1200]}\n\n"
            "Выдай JSON {title, spotify_desc, youtube_desc, tags_tiktok, tags_instagram}.")


def build_music_prompt(genre, bpm, key, mood, reference_artist=None,
                       reference_track_features=None):
    parts = [f"{genre}", f"{bpm} BPM", f"{key} key", f"mood: {mood}"]
    if reference_artist:
        parts.append(f"in the style of {reference_artist}")
    if reference_track_features:
        instr = reference_track_features.get("instruments", [])
        if instr:
            parts.append("instruments: " + ", ".join(instr[:6]))
        atmo = reference_track_features.get("atmosphere")
        if atmo:
            parts.append(atmo)
    parts.append("professional mix, punchy drums, clean stereo image")
    return ", ".join(parts)


def build_cover_prompt(title, artist, genre, mood):
    return (f"Album cover for song '{title}' by {artist}. Genre: {genre}. "
            f"Mood: {mood}. Cinematic, high contrast, bold typography, square 1400x1400, "
            f"no watermark, professional music release cover.")
