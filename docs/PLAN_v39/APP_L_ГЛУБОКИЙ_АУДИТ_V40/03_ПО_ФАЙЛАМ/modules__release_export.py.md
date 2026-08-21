# АУДИТ ФАЙЛА: `modules/release_export.py`

**LOC:** 267  |  **Размер:** 8859 байт  |  **Проблем:** 5  |  **Risk score:** 4

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 20 | `csv` | import |
| 21 | `json` | import |
| 22 | `os` | import |
| 23 | `shutil` | import |
| 24 | `time` | import |
| 25 | `pathlib.Path` | from |
| 223 | `app.core.isrc.get_isrc` | from |
| 45 | `pydub.AudioSegment` | from |
| 76 | `mutagen.easyid3.EasyID3` | from |
| 77 | `mutagen.mp3.MP3` | from |
| 107 | `mutagen.flac.FLAC` | from |
| 142 | `modules.user_profile.get_artist_name` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 32 | `_copy_or_convert` | 31 | 8 | ✅ |
| 66 | `_write_id3` | 30 | 3 | ✅ |
| 99 | `_write_flac_tags` | 18 | 1 | ❌ |
| 120 | `export_release` | 143 | 28 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 58** — print() вместо logger

  ```
         56 |         return True
         57 |     except Exception as e:
  >>>    58 |         print(f"[release_export._copy_or_convert] {e}")
         59 |         try:
         60 |             shutil.copy(src, dst)
  ```

- **строка 95** — print() вместо logger

  ```
         93 |         return True
         94 |     except Exception as e:
  >>>    95 |         print(f"[release_export._write_id3] {e}")
         96 |         return False
         97 | 
  ```

- **строка 267** — print() вместо logger

  ```
        265 | 
        266 | if __name__ == "__main__":
  >>>   267 |     print("release_export v7 ready")
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 120** — export_release: 143 LOC (>100) — декомпозиция

  ```
        118 | 
        119 | 
  >>>   120 | def export_release(
        121 |     beat_path: str,
        122 |     vocal_path: str,
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 120** — export_release: сложность ≈ 28 (>15)

  ```
        118 | 
        119 | 
  >>>   120 | def export_release(
        121 |     beat_path: str,
        122 |     vocal_path: str,
  ```
