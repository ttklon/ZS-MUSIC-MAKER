# АУДИТ ФАЙЛА: `app/ai/quality.py`

**LOC:** 234  |  **Размер:** 11552 байт  |  **Проблем:** 1  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `__future__.annotations` | from |
| 11 | `re` | import |
| 12 | `collections.Counter` | from |
| 13 | `pathlib.Path` | from |
| 14 | `typing.Any` | from |
| 90 | `numpy` | import |
| 91 | `soundfile` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 20 | `lyrics_metrics` | 17 | 4 | ✅ |
| 40 | `validate_lyrics` | 18 | 6 | ✅ |
| 61 | `validate_metadata_json` | 23 | 8 | ✅ |
| 87 | `audio_metrics` | 28 | 3 | ✅ |
| 118 | `validate_audio_artifact` | 14 | 5 | ✅ |
| 135 | `validate_vocal_artifact` | 7 | 1 | ✅ |
| 145 | `validate_rvc_artifact` | 15 | 3 | ✅ |
| 163 | `validate_asr_transcript` | 15 | 5 | ✅ |
| 181 | `validate_stem_artifact` | 14 | 3 | ✅ |
| 198 | `validate_stereo_texture` | 12 | 4 | ✅ |
| 213 | `validate_analysis_json` | 21 | 2 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 9** — import 'annotations' не используется в теле файла

  ```
          7 | fallback до сохранения артефакта на диск.
          8 | """
  >>>     9 | from __future__ import annotations
         10 | 
         11 | import re
  ```
