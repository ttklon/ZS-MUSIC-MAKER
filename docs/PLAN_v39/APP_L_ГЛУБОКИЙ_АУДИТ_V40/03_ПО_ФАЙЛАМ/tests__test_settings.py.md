# АУДИТ ФАЙЛА: `tests/test_settings.py`

**LOC:** 72  |  **Размер:** 1954 байт  |  **Проблем:** 4  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 5 | `os` | import |
| 6 | `pathlib.Path` | from |
| 8 | `pytest` | import |
| 10 | `config.settings` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 14 | `_clean_settings` | 3 | 0 | ❌ |
| 20 | `test_defaults_sane` | 7 | 0 | ❌ |
| 30 | `test_env_override` | 10 | 0 | ❌ |
| 43 | `test_dotenv_file_override` | 9 | 0 | ❌ |
| 55 | `test_os_environ_beats_dotenv` | 5 | 0 | ❌ |
| 63 | `test_get_settings_singleton` | 3 | 0 | ❌ |
| 69 | `test_invalid_values_fall_back_to_default` | 3 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 3 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — tests for config/settings (ШАГ 007)."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import os
  ```

- **строка 5** — import 'os' не используется в теле файла

  ```
          3 | from __future__ import annotations
          4 | 
  >>>     5 | import os
          6 | from pathlib import Path
          7 | 
  ```

- **строка 6** — import 'Path' не используется в теле файла

  ```
          4 | 
          5 | import os
  >>>     6 | from pathlib import Path
          7 | 
          8 | import pytest
  ```

### HARDCODED_POSIX_PATH — 1 шт. — 🟠 HIGH
**Смысл:** Захардкоженный POSIX-путь (/home/... /Users/...)
**Fix:** Path из config.settings/tempfile.gettempdir().

- **строка 52** — /tmp/custom_beats

  ```
         50 |     s = S.Settings.load(env_path=env_file)
         51 |     assert s.vram_gb == 20.0
  >>>    52 |     assert str(s.beats_dir) == "/tmp/custom_beats"
         53 | 
         54 | 
  ```
