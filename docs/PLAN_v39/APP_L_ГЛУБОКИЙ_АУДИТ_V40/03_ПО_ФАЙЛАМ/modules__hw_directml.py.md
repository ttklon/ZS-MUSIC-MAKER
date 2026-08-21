# АУДИТ ФАЙЛА: `modules/hw_directml.py`

**LOC:** 145  |  **Размер:** 4644 байт  |  **Проблем:** 3  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 11 | `__future__.annotations` | from |
| 13 | `json` | import |
| 14 | `logging` | import |
| 15 | `platform` | import |
| 16 | `subprocess` | import |
| 17 | `pathlib.Path` | from |
| 18 | `typing.Any` | from |
| 41 | `torch` | import |
| 60 | `torch_directml` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 23 | `detect` | 75 | 14 | ✅ |
| 101 | `_wmic_vram_mb` | 15 | 3 | ❌ |
| 119 | `save_profile` | 5 | 1 | ❌ |
| 127 | `choose_musicgen_variant` | 13 | 4 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 11** — import 'annotations' не используется в теле файла

  ```
          9 | """
         10 | 
  >>>    11 | from __future__ import annotations
         12 | 
         13 | import json
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 52** — except: pass — тихое подавление ошибок

  ```
         50 |                 out["vram_mb"] = int(props.total_memory / (1024 * 1024))
         51 |                 out["gpu_name"] = props.name
  >>>    52 |             except Exception:
         53 |                 pass
         54 |     except Exception as e:
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 145** — print() вместо logger

  ```
        143 | if __name__ == "__main__":
        144 |     p = save_profile()
  >>>   145 |     print(json.dumps(p, ensure_ascii=False, indent=2))
  ```
