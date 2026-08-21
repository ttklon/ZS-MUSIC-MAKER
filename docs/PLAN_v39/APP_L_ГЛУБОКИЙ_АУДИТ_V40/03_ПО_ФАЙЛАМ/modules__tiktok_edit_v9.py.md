# АУДИТ ФАЙЛА: `modules/tiktok_edit_v9.py`

**LOC:** 267  |  **Размер:** 8080 байт  |  **Проблем:** 4  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 19 | `__future__.annotations` | from |
| 21 | `json` | import |
| 22 | `shutil` | import |
| 23 | `subprocess` | import |
| 24 | `pathlib.Path` | from |
| 27 | `numpy` | import |
| 32 | `soundfile` | import |
| 253 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 39 | `_read` | 4 | 1 | ❌ |
| 46 | `_write` | 2 | 0 | ❌ |
| 51 | `_find_hot_slice` | 19 | 6 | ✅ |
| 73 | `_fade_in_out` | 17 | 5 | ❌ |
| 93 | `cut_slice` | 22 | 5 | ❌ |
| 118 | `make_all_cuts` | 61 | 12 | ✅ |
| 183 | `_has_ffmpeg` | 1 | 0 | ❌ |
| 187 | `make_vertical_video` | 62 | 5 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 256** — print() вместо logger

  ```
        254 | 
        255 |     if len(sys.argv) < 3:
  >>>   256 |         print("usage: python tiktok_edit_v9.py <in.wav> <out_dir>")
        257 |         sys.exit(1)
        258 |     r = make_all_cuts(sys.argv[1], sys.argv[2])
  ```

- **строка 259** — print() вместо logger

  ```
        257 |         sys.exit(1)
        258 |     r = make_all_cuts(sys.argv[1], sys.argv[2])
  >>>   259 |     print(
        260 |         json.dumps(
        261 |             {
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 19** — import 'annotations' не используется в теле файла

  ```
         17 | """
         18 | 
  >>>    19 | from __future__ import annotations
         20 | 
         21 | import json
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 93** — public function 'cut_slice' без docstring

  ```
         91 | 
         92 | 
  >>>    93 | def cut_slice(
         94 |     input_wav: str, output_wav: str, start_sec: float, end_sec: float, fade: bool = True
         95 | ) -> dict:
  ```
