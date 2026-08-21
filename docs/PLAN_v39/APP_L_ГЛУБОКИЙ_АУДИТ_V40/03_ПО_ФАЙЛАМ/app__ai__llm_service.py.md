# АУДИТ ФАЙЛА: `app/ai/llm_service.py`

**LOC:** 45  |  **Размер:** 1743 байт  |  **Проблем:** 3  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 4 | `json` | import |
| 5 | `typing.Any` | from |
| 5 | `typing.Optional` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 8 | `complete` | 20 | 3 | ❌ |
| 31 | `complete_json` | 14 | 5 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 8** — public function 'complete' без docstring

  ```
          6 | 
          7 | 
  >>>     8 | def complete(handle: Any, system: str, user: str, max_tokens: int = 1024,
          9 |              temperature: float = 0.85, top_p: float = 0.95,
         10 |              repeat_penalty: float = 1.1) -> str:
  ```

- **строка 31** — public function 'complete_json' без docstring

  ```
         29 | 
         30 | 
  >>>    31 | def complete_json(handle: Any, system: str, user: str, max_tokens: int = 2048,
         32 |                   temperature: float = 0.4) -> Optional[dict]:
         33 |     txt = complete(handle, system, user, max_tokens=max_tokens, temperature=temperature)
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - app/ai/llm_service.py (v38): обёртка над llama-cpp."""
  >>>     3 | from __future__ import annotations
          4 | import json
          5 | from typing import Any, Optional
  ```
