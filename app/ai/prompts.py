"""ZS Music Maker prompt catalog and role-specific prompt builders."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "data" / "prompts"

# Every versioned prompt asset is intentionally mapped to a current role.  This
# allowlist is also a path-traversal boundary for user-controlled prompt keys.
PROMPT_ASSETS: dict[str, str] = {
    "cover_art_prompt.prompt.txt": "cover_art",
    "hashtags_insta.prompt.txt": "metadata",
    "hashtags_tiktok.prompt.txt": "metadata",
    "hashtags_youtube.prompt.txt": "metadata",
    "lyrics_adlibs.prompt.txt": "lyrics",
    "lyrics_chorus.prompt.txt": "lyrics",
    "lyrics_hook.prompt.txt": "lyrics",
    "lyrics_verse.prompt.txt": "lyrics",
    "slang_extraction.prompt.txt": "analysis",
    "spotify_description.prompt.txt": "metadata",
    "track_description_long.prompt.txt": "metadata",
    "track_description_short.prompt.txt": "metadata",
    "track_title.prompt.txt": "metadata",
    "trend_analysis.prompt.txt": "trend_analysis",
    "youtube_description.prompt.txt": "metadata",
}

_DEFAULT_CONTEXT = {
    "title": "Untitled",
    "artist": "Independent artist",
    "theme": "night drive",
    "genre": "phonk",
    "bpm": "130",
    "key": "unknown",
    "mood_tags": "dark, energetic",
    "mood": "dark, energetic",
    "language": "ru",
    "user_lines": "(нет обязательных строк)",
    "hook_phrase": "(подбери хук)",
    "corpus_text": "(корпус не предоставлен)",
    "region": "global",
    "days": "30",
}

SYSTEM_LYRICS = """Ты - русскоязычный автор-хитмейкер (рэп/трэп/фонк/поп-рэп/шансон). Правила:
1. Каждая строчка двигает историю, даёт punchline или усиливает эмоцию. Никаких пустых нейро-наборов.
2. Живой язык: сленг, конкретика, детали - не абстракции.
3. 6-10 слогов в строке под BPM. Схема AABB или ABAB, внутренние рифмы приветствуются.
4. Куплет = развитие мысли, не 4 несвязанных афоризма.
5. Хук = короткая цепляющая фраза, повтор 2-4 раза.
6. Референс-артиста соблюдать по лексике/флоу, но НЕ копировать его строки.
7. Только чистый текст с метками [Куплет 1]/[Припев]/[Bridge]. Без комментариев."""

SYSTEM_ANALYSIS = """Ты - музыкальный аналитик. Строишь досье артиста на русском в JSON.
Обязательная схема:
{"bio": "краткий творческий профиль только из доступных текстов/метаданных", "themes": [...],
 "slang": [...], "flow": "...", "analogs": [...], "core_themes": [...], "lexicon": [...],
 "rhyme_style": "...", "emotional_range": [...], "signature_tricks": [...],
 "audience": "...", "story_arcs": [...], "avoid": [...]}
Не выдумывай биографические факты. Если доказательств нет, в bio укажи, что биографические данные не предоставлены.
Только валидный JSON без комментариев."""

SYSTEM_TRACK_ANALYSIS = """Ты - аналитик отдельного трека. Выдай JSON:
{"title_meaning": "...", "theme": "...", "storyline": "...", "key_lines": [...], "analysis": "...",
 "line_breakdown": [{"line": "...", "meaning": "...", "device": "..."}],
 "hook": "...", "hook_repetitions": N, "energy_curve": "...", "reusable_elements": [...]}
Тема, key_lines и analysis обязательны. Не приписывай тексту отсутствующие строки.
Только валидный JSON. line_breakdown обязателен для каждой доступной строки."""

SYSTEM_METADATA = """Ты - маркетолог инди-музыки. Выдай JSON:
{title, spotify_desc, youtube_desc, tags_tiktok (15), tags_instagram (10)}.
Только валидный JSON, без комментариев."""


def prompt_asset_names() -> tuple[str, ...]:
    """Return all supported versioned prompt filenames in stable order."""
    return tuple(sorted(PROMPT_ASSETS))


def prompt_assets_for_role(role: str) -> tuple[str, ...]:
    """Return the assets declared for a current AI role or support capability."""
    return tuple(name for name in prompt_asset_names() if PROMPT_ASSETS[name] == role)


def load_prompt_asset(name: str) -> str:
    """Read one allowlisted prompt asset; reject unknown names and missing assets."""
    if name not in PROMPT_ASSETS:
        raise KeyError(f"Unknown prompt asset: {name}")
    path = PROMPTS_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Versioned prompt asset missing: {name}")
    return path.read_text(encoding="utf-8").strip()


def render_prompt_asset(name: str, **context: Any) -> str:
    """Render an allowlisted asset with defaults for its documented placeholders."""
    values = defaultdict(str, _DEFAULT_CONTEXT)
    values.update({key: str(value) for key, value in context.items() if value is not None})
    return load_prompt_asset(name).format_map(values)


def validate_prompt_catalog() -> list[str]:
    """Return factual catalog errors: missing map/files or unrenderable templates."""
    errors: list[str] = []
    disk_names = {path.name for path in PROMPTS_DIR.glob("*.prompt.txt")}
    mapped_names = set(PROMPT_ASSETS)
    for name in sorted(disk_names - mapped_names):
        errors.append(f"unmapped prompt asset: {name}")
    for name in sorted(mapped_names - disk_names):
        errors.append(f"mapped prompt asset missing on disk: {name}")
    for name in prompt_asset_names():
        try:
            render_prompt_asset(name)
        except (KeyError, ValueError) as exc:
            errors.append(f"unrenderable prompt asset {name}: {exc}")
    return errors


def _render_role_assets(role: str, **context: Any) -> str:
    return "\n\n".join(render_prompt_asset(name, **context) for name in prompt_assets_for_role(role))


def build_lyrics_prompt(
    theme: str,
    genre: str,
    bpm: int | float,
    n_verses: int,
    bilingual: bool,
    user_lines: list[str] | None = None,
    artist_dossier: dict[str, Any] | None = None,
    track_reference: dict[str, Any] | None = None,
) -> str:
    context = {
        "theme": theme,
        "genre": genre,
        "bpm": bpm,
        "language": "ru",
        "user_lines": "\n".join(user_lines or []) or _DEFAULT_CONTEXT["user_lines"],
    }
    parts = [SYSTEM_LYRICS, _render_role_assets("lyrics", **context)]
    parts.extend(
        [
            f"Тема: {theme}",
            f"Жанр: {genre}",
            f"BPM: {bpm}",
            f"Куплетов: {n_verses}",
            f"Билингвал (RU куплеты + EN хук): {'да' if bilingual else 'нет'}",
        ]
    )
    if user_lines:
        parts.append("ОБЯЗАТЕЛЬНЫЕ строки (впитать дословно):")
        parts.extend(f"  - {line}" for line in user_lines)
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
    parts.extend(("", "Пиши текст трека сейчас. Без комментариев."))
    return "\n".join(parts)


def build_dossier_prompt(artist: str, tracks_text: str) -> str:
    return "\n\n".join(
        (
            SYSTEM_ANALYSIS,
            _render_role_assets("analysis", corpus_text=tracks_text[:20_000]),
            f"Артист: {artist}\n\nВсе известные тексты:\n=====\n{tracks_text[:20_000]}\n=====\n\nПострой досье JSON строго по schema.",
        )
    )


def build_track_dossier_prompt(title: str, lyrics: str, features: dict[str, Any]) -> str:
    return (
        f"Трек: {title}\nBPM: {features.get('bpm', '?')}\n"
        f"Тональность: {features.get('key', '?')}\n"
        f"Теги (авто): {', '.join(features.get('tags', []))}\n"
        f"Длительность: {features.get('duration_sec', '?')} сек\n\n"
        f"Текст:\n=====\n{lyrics}\n=====\n\nВерни JSON по schema."
    )


def build_metadata_prompt(theme: str, style: str, snippet: str) -> str:
    context = {"theme": theme, "genre": style, "title": "Untitled", "artist": "Independent artist"}
    return "\n\n".join(
        (
            SYSTEM_METADATA,
            _render_role_assets("metadata", **context),
            f"Тема: {theme}\nСтиль: {style}\n\nКусок лирики:\n{snippet[:1200]}\n\nВыдай JSON {{title, spotify_desc, youtube_desc, tags_tiktok, tags_instagram}}.",
        )
    )


def build_music_prompt(
    genre: str,
    bpm: int | float,
    key: str,
    mood: str,
    reference_artist: str | None = None,
    reference_track_features: dict[str, Any] | None = None,
) -> str:
    parts = [f"{genre}", f"{bpm} BPM", f"{key} key", f"mood: {mood}"]
    if reference_artist:
        parts.append(f"in the style of {reference_artist}")
    if reference_track_features:
        instruments = reference_track_features.get("instruments", [])
        if instruments:
            parts.append("instruments: " + ", ".join(instruments[:6]))
        atmosphere = reference_track_features.get("atmosphere")
        if atmosphere:
            parts.append(atmosphere)
    parts.append("professional mix, punchy drums, clean stereo image")
    return ", ".join(parts)


def build_cover_prompt(title: str, artist: str, genre: str, mood: str) -> str:
    # Load the role asset to keep the versioned template part of the active
    # catalog; the final SDXL-facing prompt remains concise English text.
    render_prompt_asset("cover_art_prompt.prompt.txt", title=title, genre=genre, mood_tags=mood, theme=mood)
    return (
        f"Album cover for song '{title}' by {artist}. Genre: {genre}. "
        f"Mood: {mood}. Cinematic, high contrast, bold typography, square 1400x1400, "
        "no watermark, professional music release cover."
    )
