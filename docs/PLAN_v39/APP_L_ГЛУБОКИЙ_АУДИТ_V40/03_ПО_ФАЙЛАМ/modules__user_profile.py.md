# АУДИТ ФАЙЛА: `modules/user_profile.py`

**LOC:** 157  |  **Размер:** 4810 байт  |  **Проблем:** 2  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 14 | `json` | import |
| 15 | `time` | import |
| 16 | `pathlib.Path` | from |
| 131 | `modules.voice_convert.vault_summary` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 37 | `get_profile` | 14 | 3 | ❌ |
| 54 | `save_profile` | 4 | 0 | ❌ |
| 61 | `update` | 5 | 1 | ❌ |
| 69 | `is_first_run` | 1 | 0 | ❌ |
| 73 | `mark_onboarded` | 1 | 0 | ❌ |
| 77 | `set_artist_name` | 3 | 2 | ✅ |
| 83 | `get_artist_name` | 1 | 1 | ❌ |
| 87 | `set_quality_mode` | 4 | 1 | ✅ |
| 94 | `add_to_history` | 5 | 0 | ❌ |
| 102 | `get_history` | 1 | 0 | ❌ |
| 106 | `add_favorite_theme` | 8 | 2 | ❌ |
| 117 | `add_favorite_preset` | 8 | 2 | ❌ |
| 128 | `sync_voice_progress` | 17 | 1 | ✅ |
| 148 | `save_last_settings` | 1 | 0 | ❌ |
| 152 | `get_last_settings` | 1 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 37** — public function 'get_profile' без docstring

  ```
         35 | 
         36 | 
  >>>    37 | def get_profile() -> dict:
         38 |     if not PROFILE_FILE.exists():
         39 |         p = dict(DEFAULT_PROFILE)
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 157** — print() вместо logger

  ```
        155 | 
        156 | if __name__ == "__main__":
  >>>   157 |     print(json.dumps(get_profile(), indent=2, ensure_ascii=False))
  ```
