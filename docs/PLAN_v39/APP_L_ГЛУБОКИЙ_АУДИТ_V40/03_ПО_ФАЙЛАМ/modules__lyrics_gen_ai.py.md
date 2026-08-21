# АУДИТ ФАЙЛА: `modules/lyrics_gen_ai.py`

**LOC:** 57  |  **Размер:** 2899 байт  |  **Проблем:** 2  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 4 | `json` | import |
| 4 | `re` | import |
| 4 | `time` | import |
| 5 | `pathlib.Path` | from |
| 6 | `typing.Any` | from |
| 6 | `typing.Dict` | from |
| 7 | `app.ai.registry.registry` | from |
| 8 | `app.ai.prompts` | from |
| 9 | `app.ai.llm_service` | from |
| 10 | `modules.artist_dossier.DossierManager` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 17 | `generate_lyrics_ai` | 40 | 11 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - modules/lyrics_gen_ai.py (v38 AI-first)"""
  >>>     3 | from __future__ import annotations
          4 | import json, re, time
          5 | from pathlib import Path
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 17** — public function 'generate_lyrics_ai' без docstring

  ```
         15 | 
         16 | 
  >>>    17 | def generate_lyrics_ai(theme, style_vector=None, n_verses=2, user_lyrics_lines=None,
         18 |                        bilingual=True, artist_slug=None, track_id=None,
         19 |                        genre="phonk") -> Dict[str, Any]:
  ```
