# АУДИТ ФАЙЛА: `modules/presets.py`

**LOC:** 170  |  **Размер:** 6437 байт  |  **Проблем:** 3  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 6 | `json` | import |
| 7 | `os` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 95 | `_load_all` | 10 | 2 | ❌ |
| 108 | `list_presets` | 10 | 0 | ❌ |
| 121 | `get_preset` | 4 | 1 | ❌ |
| 128 | `save_user_preset` | 11 | 2 | ❌ |
| 142 | `preset_to_style_vector` | 24 | 1 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 128** — public function 'save_user_preset' без docstring

  ```
        126 | 
        127 | 
  >>>   128 | def save_user_preset(key: str, preset: dict) -> dict:
        129 |     user = {}
        130 |     if os.path.exists(PRESETS_FILE):
  ```

- **строка 142** — public function 'preset_to_style_vector' без docstring

  ```
        140 | 
        141 | 
  >>>   142 | def preset_to_style_vector(key: str) -> dict:
        143 |     p = get_preset(key)
        144 |     if "error" in p:
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 170** — print() вместо logger

  ```
        168 | 
        169 | if __name__ == "__main__":
  >>>   170 |     print(json.dumps(list_presets(), ensure_ascii=False, indent=2))
  ```
