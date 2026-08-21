# АУДИТ ФАЙЛА: `tools/ab_compare.py`

**LOC:** 236  |  **Размер:** 6881 байт  |  **Проблем:** 5  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 17 | `__future__.annotations` | from |
| 19 | `argparse` | import |
| 20 | `json` | import |
| 21 | `sys` | import |
| 22 | `pathlib.Path` | from |
| 23 | `typing.Any` | from |
| 26 | `numpy` | import |
| 27 | `pyloudnorm` | import |
| 28 | `soundfile` | import |
| 34 | `matplotlib` | import |
| 37 | `matplotlib.pyplot` | import |
| 85 | `numpy.lib.stride_tricks.sliding_window_view` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 44 | `_load_stereo` | 4 | 1 | ❌ |
| 51 | `_lufs` | 5 | 1 | ❌ |
| 59 | `_true_peak_db` | 4 | 1 | ❌ |
| 66 | `_stereo_width` | 8 | 4 | ❌ |
| 77 | `_spectrogram` | 32 | 2 | ❌ |
| 112 | `compare` | 79 | 5 | ❌ |
| 194 | `_verdict` | 16 | 7 | ❌ |
| 213 | `main` | 19 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 112** — public function 'compare' без docstring

  ```
        110 | 
        111 | 
  >>>   112 | def compare(user_wav: str, ref_wav: str, out_dir: str) -> dict[str, Any]:
        113 |     out = Path(out_dir)
        114 |     out.mkdir(parents=True, exist_ok=True)
  ```

- **строка 213** — public function 'main' без docstring

  ```
        211 | 
        212 | 
  >>>   213 | def main():
        214 |     p = argparse.ArgumentParser()
        215 |     p.add_argument("user_wav")
  ```

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 30** — print() вместо logger

  ```
         28 |     import soundfile as sf
         29 | except Exception as e:
  >>>    30 |     print(f"[ab_compare] deps missing: {e}", file=sys.stderr)
         31 |     raise
         32 | 
  ```

- **строка 221** — print() вместо logger

  ```
        219 |     r = compare(a.user_wav, a.ref_wav, a.out)
        220 |     # Печатаем без spectrograms полных путей (короткая версия)
  >>>   221 |     print(
        222 |         json.dumps(
        223 |             {
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 17** — import 'annotations' не используется в теле файла

  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | import argparse
  ```
