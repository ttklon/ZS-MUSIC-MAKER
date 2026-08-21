# АУДИТ ФАЙЛА: `app/core/font_utils.py`

**LOC:** 120  |  **Размер:** 4935 байт  |  **Проблем:** 3  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 13 | `__future__.annotations` | from |
| 15 | `os` | import |
| 16 | `sys` | import |
| 17 | `pathlib.Path` | from |
| 18 | `typing.Iterable` | from |
| 18 | `typing.Optional` | from |
| 98 | `PIL.ImageFont` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 23 | `_config_font_candidates` | 13 | 3 | ✅ |
| 39 | `font_candidates` | 49 | 7 | ✅ |
| 91 | `load_pil_font` | 18 | 3 | ✅ |
| 112 | `first_available_font_path` | 8 | 4 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 35** — print() вместо logger

  ```
         33 |         ]
         34 |     except OSError as e:  # noqa: BLE001 — сообщаем причину и работаем без конфига
  >>>    35 |         print(f"[font_utils] cannot read {cfg}: {e}", file=sys.stderr)
         36 |         return []
         37 | 
  ```

- **строка 107** — print() вместо logger

  ```
        105 |             continue  # штатное отсутствие
        106 |         except Exception as e:  # noqa: BLE001
  >>>   107 |             print(f"[font_utils] TTF load error {cand}: {e}", file=sys.stderr)
        108 |             continue
        109 |     return ImageFont.load_default()
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 13** — import 'annotations' не используется в теле файла

  ```
         11 | C:\\ и /home/ubuntu в production-коде.
         12 | """
  >>>    13 | from __future__ import annotations
         14 | 
         15 | import os
  ```
