# АУДИТ ФАЙЛА: `modules/distribution_export_v11.py`

**LOC:** 474  |  **Размер:** 16453 байт  |  **Проблем:** 13  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `__future__.annotations` | from |
| 11 | `csv` | import |
| 12 | `json` | import |
| 13 | `os` | import |
| 14 | `shutil` | import |
| 15 | `sys` | import |
| 16 | `dataclasses.asdict` | from |
| 16 | `dataclasses.dataclass` | from |
| 16 | `dataclasses.field` | from |
| 17 | `datetime.datetime` | from |
| 17 | `datetime.timezone` | from |
| 435 | `tempfile` | import |
| 62 | `app.core.isrc.is_valid_isrc` | from |
| 62 | `app.core.isrc.generate_isrc` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 20 | `_safe_print` | 4 | 1 | ❌ |
| 93 | `_copy_safe` | 9 | 4 | ❌ |
| 105 | `build_spotify_package` | 62 | 10 | ❌ |
| 170 | `build_yandex_vk_package` | 61 | 4 | ❌ |
| 234 | `build_tiktok_package` | 72 | 7 | ❌ |
| 309 | `build_youtube_package` | 70 | 6 | ❌ |
| 382 | `build_shazam_package` | 20 | 1 | ❌ |
| 405 | `build_all_distribution_packages` | 26 | 1 | ❌ |
| 434 | `_self_test` | 36 | 3 | ❌ |
| 50 | `ensure` | 21 | 7 | ❌ |
| 89 | `existing` | 1 | 1 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 28 | `TrackMetadata` | ❌ |
| 75 | `ReleaseFiles` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 7 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 105** — public function 'build_spotify_package' без docstring

  ```
        103 | 
        104 | 
  >>>   105 | def build_spotify_package(meta, files, out_dir):
        106 |     d = os.path.join(out_dir, "spotify_dsp")
        107 |     os.makedirs(d, exist_ok=True)
  ```

- **строка 170** — public function 'build_yandex_vk_package' без docstring

  ```
        168 | 
        169 | 
  >>>   170 | def build_yandex_vk_package(meta, files, out_dir):
        171 |     d = os.path.join(out_dir, "yandex_vk_ru")
        172 |     os.makedirs(d, exist_ok=True)
  ```

- **строка 234** — public function 'build_tiktok_package' без docstring

  ```
        232 | 
        233 | 
  >>>   234 | def build_tiktok_package(meta, files, out_dir):
        235 |     d = os.path.join(out_dir, "tiktok")
        236 |     os.makedirs(d, exist_ok=True)
  ```

- **строка 309** — public function 'build_youtube_package' без docstring

  ```
        307 | 
        308 | 
  >>>   309 | def build_youtube_package(meta, files, out_dir):
        310 |     d = os.path.join(out_dir, "youtube")
        311 |     os.makedirs(d, exist_ok=True)
  ```

- **строка 382** — public function 'build_shazam_package' без docstring

  ```
        380 | 
        381 | 
  >>>   382 | def build_shazam_package(meta, out_dir):
        383 |     d = os.path.join(out_dir, "shazam_ready")
        384 |     os.makedirs(d, exist_ok=True)
  ```

- **строка 405** — public function 'build_all_distribution_packages' без docstring

  ```
        403 | 
        404 | 
  >>>   405 | def build_all_distribution_packages(meta, files, out_dir):
        406 |     meta.ensure()
        407 |     os.makedirs(out_dir, exist_ok=True)
  ```

- **строка 50** — public function 'ensure' без docstring

  ```
         48 |     lyrics_en_hook: str = ""
         49 | 
  >>>    50 |     def ensure(self):
         51 |         if not self.release_date:
         52 |             self.release_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
  ```

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 28** — public class 'TrackMetadata' без docstring

  ```
         26 | 
         27 | @dataclass
  >>>    28 | class TrackMetadata:
         29 |     title: str
         30 |     artist: str
  ```

- **строка 75** — public class 'ReleaseFiles' без docstring

  ```
         73 | 
         74 | @dataclass
  >>>    75 | class ReleaseFiles:
         76 |     master_wav: str = ""
         77 |     mp3_320: str = ""
  ```

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 22** — print() вместо logger

  ```
         20 | def _safe_print(msg):
         21 |     try:
  >>>    22 |         print(msg)
         23 |     except UnicodeEncodeError:
         24 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
  ```

- **строка 474** — print() вместо logger

  ```
        472 | 
        473 | if __name__ == "__main__":
  >>>   474 |     print("distribution_export_v11 self-test:", "OK" if _self_test() else "FAIL")
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 9** — import 'annotations' не используется в теле файла

  ```
          7 | """
          8 | 
  >>>     9 | from __future__ import annotations
         10 | 
         11 | import csv
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 70** — except: pass — тихое подавление ошибок

  ```
         68 |                 if gen:
         69 |                     self.isrc = gen
  >>>    70 |         except ImportError:
         71 |             pass
         72 | 
  ```
