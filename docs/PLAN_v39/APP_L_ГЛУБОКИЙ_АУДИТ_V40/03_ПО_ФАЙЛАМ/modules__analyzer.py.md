# АУДИТ ФАЙЛА: `modules/analyzer.py`

**LOC:** 257  |  **Размер:** 9032 байт  |  **Проблем:** 3  |  **Risk score:** 2

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 11 | `json` | import |
| 12 | `os` | import |
| 14 | `numpy` | import |
| 17 | `librosa` | import |
| 250 | `sys` | import |
| 80 | `essentia.standard` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 26 | `_safe_load` | 4 | 1 | ❌ |
| 33 | `analyze_single` | 74 | 1 | ✅ |
| 110 | `_infer_vibe` | 22 | 10 | ❌ |
| 135 | `_bpm_range` | 20 | 0 | ✅ |
| 158 | `analyze_multi` | 65 | 7 | ✅ |
| 226 | `_save_to_vault` | 11 | 2 | ❌ |
| 240 | `list_cached_analyses` | 6 | 2 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 254** — print() вместо logger

  ```
        252 |     files = sys.argv[1:]
        253 |     if not files:
  >>>   254 |         print("Usage: python analyzer.py <ref1.mp3> [ref2.mp3 ...]")
        255 |     else:
        256 |         result = analyze_multi(files) if len(files) > 1 else analyze_single(files[0])
  ```

- **строка 257** — print() вместо logger

  ```
        255 |     else:
        256 |         result = analyze_multi(files) if len(files) > 1 else analyze_single(files[0])
  >>>   257 |         print(json.dumps(result, ensure_ascii=False, indent=2))
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 86** — except: pass — тихое подавление ошибок

  ```
         84 |         danceability = estd.Danceability()(audio)
         85 |         essentia_desc["danceability"] = round(float(danceability[0]), 3)
  >>>    86 |     except Exception:
         87 |         pass
         88 | 
  ```
