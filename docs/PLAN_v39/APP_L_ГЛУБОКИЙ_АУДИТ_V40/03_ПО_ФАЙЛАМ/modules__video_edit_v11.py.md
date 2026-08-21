# АУДИТ ФАЙЛА: `modules/video_edit_v11.py`

**LOC:** 464  |  **Размер:** 15764 байт  |  **Проблем:** 10  |  **Risk score:** 7

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 15 | `__future__.annotations` | from |
| 17 | `json` | import |
| 18 | `math` | import |
| 19 | `os` | import |
| 20 | `struct` | import |
| 21 | `sys` | import |
| 22 | `wave` | import |
| 23 | `dataclasses.asdict` | from |
| 23 | `dataclasses.dataclass` | from |
| 256 | `app.core.font_utils.load_pil_font` | from |
| 207 | `moviepy.editor` | import |
| 217 | `PIL.Image` | from |
| 217 | `PIL.ImageDraw` | from |
| 217 | `PIL.ImageFilter` | from |
| 217 | `PIL.ImageFont` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 26 | `_safe_print` | 4 | 1 | ❌ |
| 72 | `_read_wav_mono` | 44 | 11 | ❌ |
| 119 | `_rms_windows` | 9 | 2 | ❌ |
| 131 | `detect_hook` | 36 | 11 | ✅ |
| 170 | `_parse_lrc` | 32 | 12 | ❌ |
| 205 | `_try_moviepy` | 7 | 1 | ❌ |
| 215 | `_try_pil` | 6 | 1 | ❌ |
| 224 | `_make_static_bg` | 21 | 4 | ❌ |
| 248 | `_draw_title` | 17 | 4 | ❌ |
| 268 | `build_video` | 15 | 4 | ❌ |
| 286 | `_build_with_moviepy` | 76 | 13 | ❌ |
| 365 | `_build_fallback` | 55 | 5 | ❌ |
| 423 | `build_release_edits` | 26 | 2 | ❌ |
| 452 | `_self_test` | 8 | 3 | ❌ |
| 48 | `resolution` | 5 | 2 | ❌ |
| 66 | `to_dict` | 3 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 34 | `VideoEditRequest` | ❌ |
| 57 | `VideoEditResult` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 34** — public class 'VideoEditRequest' без docstring

  ```
         32 | 
         33 | @dataclass
  >>>    34 | class VideoEditRequest:
         35 |     master_wav: str
         36 |     cover_png: str | None = None
  ```

- **строка 57** — public class 'VideoEditResult' без docstring

  ```
         55 | 
         56 | @dataclass
  >>>    57 | class VideoEditResult:
         58 |     ok: bool
         59 |     output_path: str
  ```

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 268** — public function 'build_video' без docstring

  ```
        266 | 
        267 | 
  >>>   268 | def build_video(req: VideoEditRequest) -> VideoEditResult:
        269 |     os.makedirs(os.path.dirname(os.path.abspath(req.output_path)) or ".", exist_ok=True)
        270 |     tmp_dir = os.path.join(
  ```

- **строка 423** — public function 'build_release_edits' без docstring

  ```
        421 | 
        422 | 
  >>>   423 | def build_release_edits(
        424 |     master_wav, cover_png, lyrics_lrc, bpm, title, artist, out_dir
        425 | ) -> dict:
  ```

### SILENT_EXCEPT_PASS — 2 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 352** — except: pass — тихое подавление ошибок

  ```
        350 |             final.close()
        351 |             audio.close()
  >>>   352 |         except Exception:
        353 |             pass
        354 |     return VideoEditResult(
  ```

- **строка 194** — except: pass — тихое подавление ошибок

  ```
        192 |                                 secs = float(m) * 60 + float(s)
        193 |                                 out.append((secs, text))
  >>>   194 |                             except Exception:
        195 |                                 pass
        196 |                         i = j + 1
  ```

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 28** — print() вместо logger

  ```
         26 | def _safe_print(msg: str) -> None:
         27 |     try:
  >>>    28 |         print(msg)
         29 |     except UnicodeEncodeError:
         30 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
  ```

- **строка 464** — print() вместо logger

  ```
        462 | 
        463 | if __name__ == "__main__":
  >>>   464 |     print("video_edit_v11 self-test:", "OK" if _self_test() else "FAIL")
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 15** — import 'annotations' не используется в теле файла

  ```
         13 | """
         14 | 
  >>>    15 | from __future__ import annotations
         16 | 
         17 | import json
  ```

### HARDCODED_POSIX_PATH — 1 шт. — 🟠 HIGH
**Смысл:** Захардкоженный POSIX-путь (/home/... /Users/...)
**Fix:** Path из config.settings/tempfile.gettempdir().

- **строка 453** — /tmp/_v11_lrc_test.lrc

  ```
        451 | 
        452 | def _self_test() -> bool:
  >>>   453 |     tmp = "/tmp/_v11_lrc_test.lrc"
        454 |     with open(tmp, "w", encoding="utf-8") as f:
        455 |         f.write("[00:01.00]hello\n[00:02.50]world\n[bad]skip\n")
  ```
