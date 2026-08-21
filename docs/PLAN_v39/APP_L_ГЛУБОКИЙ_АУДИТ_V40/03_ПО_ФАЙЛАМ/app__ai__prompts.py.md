# АУДИТ ФАЙЛА: `app/ai/prompts.py`

**LOC:** 94  |  **Размер:** 5710 байт  |  **Проблем:** 3  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 32 | `build_lyrics_prompt` | 22 | 3 | ❌ |
| 57 | `build_dossier_prompt` | 2 | 0 | ❌ |
| 62 | `build_track_dossier_prompt` | 5 | 0 | ❌ |
| 70 | `build_metadata_prompt` | 2 | 0 | ❌ |
| 75 | `build_music_prompt` | 13 | 4 | ❌ |
| 91 | `build_cover_prompt` | 3 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 32** — public function 'build_lyrics_prompt' без docstring

  ```
         30 | 
         31 | 
  >>>    32 | def build_lyrics_prompt(theme, genre, bpm, n_verses, bilingual,
         33 |                         user_lines=None, artist_dossier=None, track_reference=None):
         34 |     parts = [f"Тема: {theme}", f"Жанр: {genre}", f"BPM: {bpm}",
  ```

- **строка 75** — public function 'build_music_prompt' без docstring

  ```
         73 | 
         74 | 
  >>>    75 | def build_music_prompt(genre, bpm, key, mood, reference_artist=None,
         76 |                        reference_track_features=None):
         77 |     parts = [f"{genre}", f"{bpm} BPM", f"{key} key", f"mood: {mood}"]
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - app/ai/prompts.py (v38): промпты для локальных LLM."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | SYSTEM_LYRICS = """Ты - русскоязычный автор-хитмейкер (рэп/трэп/фонк/поп-рэп/шансон). Правила:
  ```
