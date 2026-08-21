# АУДИТ ФАЙЛА: `app/core/hw_autodetect.py`

**LOC:** 212  |  **Размер:** 6901 байт  |  **Проблем:** 9  |  **Risk score:** 11

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 16 | `__future__.annotations` | from |
| 18 | `json` | import |
| 19 | `os` | import |
| 20 | `platform` | import |
| 21 | `time` | import |
| 22 | `pathlib.Path` | from |
| 37 | `psutil` | import |
| 50 | `torch` | import |
| 63 | `torch_directml` | import |
| 72 | `subprocess` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 29 | `_cpu_info` | 13 | 2 | ❌ |
| 45 | `_gpu_info` | 62 | 11 | ✅ |
| 110 | `detect` | 46 | 13 | ✅ |
| 159 | `_recommendations` | 30 | 2 | ❌ |
| 192 | `human_summary` | 13 | 1 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 5 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 59** — except: pass — тихое подавление ошибок

  ```
         57 |             )
         58 |             return g
  >>>    59 |     except Exception:
         60 |         pass
         61 |     # DirectML (AMD/Intel iGPU на Windows)
  ```

- **строка 96** — except: pass — тихое подавление ошибок

  ```
         94 |             g["vram_gb"] = 4.0  # осторожная оценка для RX 580
         95 |         return g
  >>>    96 |     except Exception:
         97 |         pass
         98 |     # ROCm (Linux)
  ```

- **строка 105** — except: pass — тихое подавление ошибок

  ```
        103 |             g["vram_gb"] = 8.0
        104 |             return g
  >>>   105 |     except Exception:
        106 |         pass
        107 |     return g
  ```

- **строка 154** — except: pass — тихое подавление ошибок

  ```
        152 |             json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
        153 |         )
  >>>   154 |     except Exception:
        155 |         pass
        156 |     return profile
  ```

- **строка 117** — except: pass — тихое подавление ошибок

  ```
        115 |             if time.time() - cached.get("ts", 0) < 86400:
        116 |                 return cached
  >>>   117 |         except Exception:
        118 |             pass
        119 | 
  ```

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 210** — print() вместо logger

  ```
        208 | if __name__ == "__main__":
        209 |     p = detect(force=True)
  >>>   210 |     print(json.dumps(p, ensure_ascii=False, indent=2))
        211 |     print()
        212 |     print(human_summary(p))
  ```

- **строка 211** — print() вместо logger

  ```
        209 |     p = detect(force=True)
        210 |     print(json.dumps(p, ensure_ascii=False, indent=2))
  >>>   211 |     print()
        212 |     print(human_summary(p))
  ```

- **строка 212** — print() вместо logger

  ```
        210 |     print(json.dumps(p, ensure_ascii=False, indent=2))
        211 |     print()
  >>>   212 |     print(human_summary(p))
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 16** — import 'annotations' не используется в теле файла

  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import json
  ```
