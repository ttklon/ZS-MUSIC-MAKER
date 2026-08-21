# АУДИТ ФАЙЛА: `app/core/license_manager.py`

**LOC:** 66  |  **Размер:** 2126 байт  |  **Проблем:** 3  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 7 | `__future__.annotations` | from |
| 9 | `dataclasses.dataclass` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 31 | `normalize` | 17 | 12 | ❌ |
| 51 | `is_free_commercial` | 6 | 2 | ❌ |
| 60 | `check` | 6 | 2 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 25 | `LicenseCheck` | ❌ |

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 7** — import 'annotations' не используется в теле файла

  ```
          5 | """
          6 | 
  >>>     7 | from __future__ import annotations
          8 | 
          9 | from dataclasses import dataclass
  ```

### MISSING_CLASS_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 25** — public class 'LicenseCheck' без docstring

  ```
         23 | 
         24 | @dataclass
  >>>    25 | class LicenseCheck:
         26 |     ok: bool
         27 |     needs_attribution: bool
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 31** — public function 'normalize' без docstring

  ```
         29 | 
         30 | 
  >>>    31 | def normalize(lic: str) -> str:
         32 |     n = (lic or "").strip().lower().replace("_", " ")
         33 |     # v34 FIX: лицензии часто приходят как URL (archive.org licenseurl,
  ```
