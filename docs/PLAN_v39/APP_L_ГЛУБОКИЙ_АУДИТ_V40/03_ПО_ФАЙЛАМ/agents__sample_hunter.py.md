# АУДИТ ФАЙЛА: `agents/sample_hunter.py`

**LOC:** 205  |  **Размер:** 6914 байт  |  **Проблем:** 5  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 17 | `__future__.annotations` | from |
| 19 | `json` | import |
| 20 | `os` | import |
| 21 | `urllib.parse` | import |
| 22 | `pathlib.Path` | from |
| 23 | `app.core.security_utils.safe_hash` | from |
| 23 | `app.core.security_utils.download_file` | from |
| 23 | `app.core.security_utils.get_json` | from |
| 154 | `app.core.license_manager.is_free_commercial` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 31 | `list_local` | 21 | 6 | ✅ |
| 56 | `search_wikimedia` | 31 | 4 | ✅ |
| 90 | `search_freesound_public` | 9 | 1 | ✅ |
| 102 | `search_pixabay` | 24 | 4 | ✅ |
| 129 | `search_online` | 6 | 0 | ✅ |
| 139 | `hunt` | 39 | 2 | ✅ |
| 181 | `download_to_cache` | 20 | 6 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 86** — print() вместо logger

  ```
         84 |             )
         85 |     except Exception as e:
  >>>    86 |         print(f"[sample_hunter.wikimedia] {e}")
         87 |     return results
         88 | 
  ```

- **строка 200** — print() вместо logger

  ```
        198 |         return None
        199 |     except Exception as e:
  >>>   200 |         print(f"[sample_hunter.download] {e}")
        201 |         return None
        202 | 
  ```

- **строка 205** — print() вместо logger

  ```
        203 | 
        204 | if __name__ == "__main__":
  >>>   205 |     print(json.dumps(hunt("phonk 808", max_results=3), ensure_ascii=False, indent=2))
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 17** — import 'annotations' не используется в теле файла

  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | import json
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 159** — except: pass — тихое подавление ошибок

  ```
        157 |                 s for s in online if is_free_commercial(s.get("license", "unknown"))
        158 |             ]
  >>>   159 |         except Exception:
        160 |             pass
        161 | 
  ```
