# АУДИТ ФАЙЛА: `modules/lyrics_gen.py`

**LOC:** 310  |  **Размер:** 12671 байт  |  **Проблем:** 6  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 15 | `__future__.annotations` | from |
| 17 | `json` | import |
| 18 | `random` | import |
| 19 | `time` | import |
| 20 | `pathlib.Path` | from |
| 161 | `requests` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 109 | `_load_lyric_memory` | 10 | 4 | ❌ |
| 122 | `_save_lyric_memory` | 3 | 1 | ❌ |
| 128 | `_pick_punches` | 27 | 7 | ✅ |
| 158 | `_try_ollama` | 14 | 2 | ✅ |
| 175 | `_template_verse` | 16 | 4 | ✅ |
| 194 | `_template_hook_en` | 8 | 2 | ✅ |
| 205 | `_is_english` | 8 | 2 | ✅ |
| 216 | `generate_lyrics` | 76 | 12 | ✅ |
| 295 | `get_lyric_memory` | 3 | 0 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 308** — print() вместо logger

  ```
        306 |         bilingual=True,
        307 |     )
  >>>   308 |     print(r["lyrics"])
        309 |     print("---")
        310 |     print("user_included:", r["user_lines_included"])
  ```

- **строка 309** — print() вместо logger

  ```
        307 |     )
        308 |     print(r["lyrics"])
  >>>   309 |     print("---")
        310 |     print("user_included:", r["user_lines_included"])
  ```

- **строка 310** — print() вместо logger

  ```
        308 |     print(r["lyrics"])
        309 |     print("---")
  >>>   310 |     print("user_included:", r["user_lines_included"])
  ```

### SILENT_EXCEPT_PASS — 2 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 170** — except: pass — тихое подавление ошибок

  ```
        168 |         if r.status_code == 200:
        169 |             return r.json().get("response", "").strip()
  >>>   170 |     except Exception:
        171 |         pass
        172 |     return None
  ```

- **строка 117** — except: pass — тихое подавление ошибок

  ```
        115 |             try:
        116 |                 out.append(json.loads(line))
  >>>   117 |             except Exception:
        118 |                 pass
        119 |     return out
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 15** — import 'annotations' не используется в теле файла

  ```
         13 | """
         14 | 
  >>>    15 | from __future__ import annotations
         16 | 
         17 | import json
  ```
