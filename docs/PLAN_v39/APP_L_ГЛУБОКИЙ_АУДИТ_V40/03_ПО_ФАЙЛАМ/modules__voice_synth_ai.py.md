# АУДИТ ФАЙЛА: `modules/voice_synth_ai.py`

**LOC:** 40  |  **Размер:** 1840 байт  |  **Проблем:** 2  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 4 | `pathlib.Path` | from |
| 5 | `typing.Any` | from |
| 5 | `typing.Dict` | from |
| 5 | `typing.Optional` | from |
| 6 | `app.ai.registry.registry` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 9 | `synth_vocal_ai` | 31 | 13 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - modules/voice_synth_ai.py (v38): XTTS-v2 -> RVC."""
  >>>     3 | from __future__ import annotations
          4 | from pathlib import Path
          5 | from typing import Any, Dict, Optional
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 9** — public function 'synth_vocal_ai' без docstring

  ```
          7 | 
          8 | 
  >>>     9 | def synth_vocal_ai(text: str, out_path: str, speaker_wav: Optional[str] = None,
         10 |                    language: str = "ru", rvc_model: Optional[str] = None) -> Dict[str, Any]:
         11 |     if not text or not text.strip():
  ```
