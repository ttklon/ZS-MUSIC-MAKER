# АУДИТ ФАЙЛА: `app/core/orchestrator_v8_patch.py`

**LOC:** 136  |  **Размер:** 5649 байт  |  **Проблем:** 2  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 16 | `__future__.annotations` | from |
| 18 | `traceback` | import |
| 19 | `pathlib.Path` | from |
| 40 | `modules.lyrics_gen_v8.generate_lyrics_v8` | from |
| 78 | `modules.female_backing.make_chorus_backing` | from |
| 78 | `modules.female_backing.mix_backing_into_vocal` | from |
| 101 | `modules.auto_qa.audit_track` | from |
| 101 | `modules.auto_qa.should_retry` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 22 | `_stage` | 5 | 2 | ❌ |
| 30 | `run_pipeline_v8` | 94 | 15 | ✅ |
| 127 | `apply` | 9 | 2 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 16** — import 'annotations' не используется в теле файла

  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import traceback
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 26** — except: pass — тихое подавление ошибок

  ```
         24 |         if callable(hook):
         25 |             hook(name, progress)
  >>>    26 |     except Exception:
         27 |         pass
         28 | 
  ```
