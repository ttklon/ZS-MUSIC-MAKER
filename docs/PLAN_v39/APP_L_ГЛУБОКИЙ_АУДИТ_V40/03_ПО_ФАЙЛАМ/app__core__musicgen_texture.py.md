# АУДИТ ФАЙЛА: `app/core/musicgen_texture.py`

**LOC:** 261  |  **Размер:** 10325 байт  |  **Проблем:** 6  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 16 | `__future__.annotations` | from |
| 18 | `hashlib` | import |
| 19 | `pathlib.Path` | from |
| 20 | `typing.Any` | from |
| 54 | `audiocraft.models.MusicGen` | from |
| 68 | `torch` | import |
| 89 | `torch` | import |
| 98 | `audiocraft` | import |
| 176 | `torchaudio` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 30 | `choose_size` | 12 | 2 | ✅ |
| 49 | `_load_musicgen` | 12 | 2 | ✅ |
| 64 | `unload_all` | 8 | 1 | ✅ |
| 76 | `detect_availability` | 35 | 2 | ✅ |
| 114 | `get_status` | 11 | 0 | ✅ |
| 129 | `_cache_key` | 2 | 0 | ❌ |
| 135 | `generate_texture` | 62 | 5 | ✅ |
| 200 | `generate_batch` | 10 | 1 | ✅ |
| 214 | `_pink_noise_fallback` | 7 | 0 | ✅ |
| 225 | `generate_atmosphere` | 18 | 0 | ✅ |
| 246 | `generate_fx_hits` | 10 | 0 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 4 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 60** — print() вместо logger

  ```
         58 |         return model
         59 |     except Exception as e:
  >>>    60 |         print(f"[musicgen_texture] audiocraft недоступен: {e}")
         61 |         return None
         62 | 
  ```

- **строка 165** — print() вместо logger

  ```
        163 |         # v35: честный лог причины один раз на вызов (не молчаливо)
        164 |         avail = detect_availability()
  >>>   165 |         print(f"[musicgen_texture] BLOCKED: {avail['reason']} | {avail['install_hint']}")
        166 |     if model is not None:
        167 |         try:
  ```

- **строка 187** — print() вместо logger

  ```
        185 |             }
        186 |         except Exception as e:
  >>>   187 |             print(f"[musicgen_texture] generation failed: {e}")
        188 | 
        189 |     # 3) Honest failure: pink noise is not MusicGen and must not be presented as it.
  ```

- **строка 261** — print() вместо logger

  ```
        259 | if __name__ == "__main__":
        260 |     r = generate_texture("dark phonk atmosphere", duration_sec=10, vram_gb=4.0)
  >>>   261 |     print(r)
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
         18 | import hashlib
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 71** — except: pass — тихое подавление ошибок

  ```
         69 | 
         70 |         torch.cuda.empty_cache()
  >>>    71 |     except Exception:
         72 |         pass
         73 | 
  ```
