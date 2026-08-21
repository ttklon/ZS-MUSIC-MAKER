# АУДИТ ФАЙЛА: `modules/voice_convert.py`

**LOC:** 204  |  **Размер:** 7085 байт  |  **Проблем:** 1  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 11 | `json` | import |
| 12 | `shutil` | import |
| 13 | `pathlib.Path` | from |
| 129 | `modules.rvc_manager` | from |
| 153 | `modules.rvc_manager` | from |
| 166 | `modules.rvc_manager` | from |
| 195 | `modules.rvc_manager` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 21 | `_ensure_dirs` | 6 | 1 | ✅ |
| 49 | `_load_index` | 6 | 2 | ❌ |
| 58 | `_save_index` | 4 | 0 | ❌ |
| 65 | `add_recording` | 22 | 1 | ✅ |
| 90 | `vault_summary` | 22 | 1 | ✅ |
| 115 | `rate_recording` | 6 | 2 | ❌ |
| 125 | `train_rvc_model` | 18 | 0 | ✅ |
| 146 | `incremental_finetune` | 2 | 0 | ✅ |
| 151 | `get_training_status` | 4 | 0 | ✅ |
| 159 | `convert` | 11 | 0 | ✅ |
| 173 | `polish_vocal` | 12 | 0 | ✅ |
| 188 | `polish_vocal_offline` | 12 | 0 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 204** — print() вместо logger

  ```
        202 | 
        203 | if __name__ == "__main__":
  >>>   204 |     print(json.dumps(vault_summary(), indent=2, ensure_ascii=False))
  ```
