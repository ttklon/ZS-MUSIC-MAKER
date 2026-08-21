# АУДИТ ФАЙЛА: `modules/beat_gen_ai.py`

**LOC:** 52  |  **Размер:** 2390 байт  |  **Проблем:** 3  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 4 | `math` | import |
| 5 | `pathlib.Path` | from |
| 6 | `typing.Any` | from |
| 6 | `typing.Dict` | from |
| 6 | `typing.Optional` | from |
| 7 | `app.ai.registry.registry` | from |
| 15 | `numpy` | import |
| 15 | `soundfile` | import |
| 15 | `torch` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 10 | `render_beat_ai` | 42 | 10 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - modules/beat_gen_ai.py (v38, MusicGen-large, чанки 20с)."""
  >>>     3 | from __future__ import annotations
          4 | import math
          5 | from pathlib import Path
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 10** — public function 'render_beat_ai' без docstring

  ```
          8 | 
          9 | 
  >>>    10 | def render_beat_ai(prompt: str, bpm: int = 140, duration_sec: int = 120,
         11 |                    out_path: str = "beat.wav", reference_wav: Optional[str] = None,
         12 |                    chunk_sec: int = 20) -> Dict[str, Any]:
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 23** — except: pass — тихое подавление ошибок

  ```
         21 |             model.set_generation_params(duration=min(chunk_sec, 30), top_k=250,
         22 |                                         top_p=0.0, temperature=1.0, cfg_coef=3.0)
  >>>    23 |         except Exception:
         24 |             pass
         25 |         sr = getattr(model, "sample_rate", 32000)
  ```
