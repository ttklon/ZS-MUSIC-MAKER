# АУДИТ ФАЙЛА: `modules/release_pack_full.py`

**LOC:** 952  |  **Размер:** 33752 байт  |  **Проблем:** 8  |  **Risk score:** 8

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 50 | `__future__.annotations` | from |
| 52 | `json` | import |
| 53 | `shutil` | import |
| 54 | `time` | import |
| 55 | `wave` | import |
| 56 | `pathlib.Path` | from |
| 57 | `typing.Any` | from |
| 60 | `numpy` | import |
| 65 | `soundfile` | import |
| 70 | `pydub.AudioSegment` | from |
| 77 | `PIL.Image` | from |
| 77 | `PIL.ImageDraw` | from |
| 77 | `PIL.ImageFilter` | from |
| 77 | `PIL.ImageFont` | from |
| 396 | `app.core.isrc.get_isrc` | from |
| 475 | `app.core.isrc.get_isrc` | from |
| 491 | `app.core.isrc.is_placeholder_isrc` | from |
| 859 | `mutagen.id3.APIC` | from |
| 859 | `mutagen.id3.ID3` | from |
| 859 | `mutagen.id3.TALB` | from |
| 859 | `mutagen.id3.TBPM` | from |
| 859 | `mutagen.id3.TCON` | from |
| 859 | `mutagen.id3.TDRC` | from |
| 859 | `mutagen.id3.TIT2` | from |
| 859 | `mutagen.id3.TKEY` | from |
| 859 | `mutagen.id3.TPE1` | from |
| 859 | `mutagen.id3.TPUB` | from |
| 859 | `mutagen.id3.TSRC` | from |
| 884 | `app.core.isrc.get_isrc` | from |
| 913 | `tempfile` | import |
| 921 | `numpy` | import |
| 258 | `scipy.signal.butter` | from |
| 258 | `scipy.signal.sosfiltfilt` | from |
| 540 | `app.core.isrc.generate_isrc` | from |
| 904 | `sys` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 87 | `_read_wav` | 22 | 6 | ✅ |
| 112 | `_write_wav` | 4 | 1 | ❌ |
| 119 | `_ensure_stereo` | 5 | 2 | ❌ |
| 127 | `_hires_resample_48k` | 16 | 3 | ✅ |
| 149 | `_make_cover` | 48 | 4 | ❌ |
| 203 | `_lyrics_to_lrc` | 11 | 2 | ❌ |
| 217 | `_lyrics_to_srt` | 17 | 2 | ❌ |
| 240 | `_fake_stems` | 46 | 8 | ✅ |
| 289 | `_instrumental_and_acapella` | 34 | 5 | ❌ |
| 329 | `_find_hook` | 21 | 5 | ✅ |
| 353 | `_make_clip` | 33 | 4 | ✅ |
| 392 | `_distrokid_xml` | 30 | 0 | ❌ |
| 425 | `_spotify_description` | 8 | 0 | ❌ |
| 436 | `_youtube_description_html` | 24 | 0 | ❌ |
| 463 | `_vk_prefill` | 7 | 0 | ❌ |
| 473 | `_shazam_jsonld` | 13 | 0 | ❌ |
| 489 | `_is_placeholder_isrc` | 3 | 0 | ❌ |
| 495 | `_is_placeholder_upc` | 4 | 2 | ❌ |
| 502 | `_production_notes` | 48 | 10 | ❌ |
| 570 | `build_pack` | 285 | 51 | ✅ |
| 858 | `_apply_id3` | 50 | 5 | ❌ |
| 227 | `fmt` | 4 | 0 | ❌ |
| 260 | `band` | 9 | 1 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 916** — print() вместо logger

  ```
        914 | 
        915 |     if sf is None:
  >>>   916 |         print("soundfile not available")
        917 |         raise SystemExit(1)
        918 |     tmp = Path(tempfile.mkdtemp())
  ```

- **строка 945** — print() вместо logger

  ```
        943 |         hit_metrics={"score": 72, "verdict": "solid"},
        944 |     )
  >>>   945 |     print(
        946 |         json.dumps(
        947 |             {k: v for k, v in result.items() if k != "files"},
  ```

- **строка 952** — print() вместо logger

  ```
        950 |         )
        951 |     )
  >>>   952 |     print("Files:", len(result["files"]))
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 50** — import 'annotations' не используется в теле файла

  ```
         48 | """
         49 | 
  >>>    50 | from __future__ import annotations
         51 | 
         52 | import json
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 570** — build_pack: 285 LOC (>100) — декомпозиция

  ```
        568 | 
        569 | 
  >>>   570 | def build_pack(
        571 |     master_wav: str,
        572 |     out_dir: str,
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 570** — build_pack: сложность ≈ 51 (>15)

  ```
        568 | 
        569 | 
  >>>   570 | def build_pack(
        571 |     master_wav: str,
        572 |     out_dir: str,
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 906** — except: pass — тихое подавление ошибок

  ```
        904 |             import sys as _s
        905 |             _s.stderr.write(f"[release_pack_full] ID3/cover embed failed: {e}\n")
  >>>   906 |         except Exception:
        907 |             pass
        908 |     id3.save(str(mp3_path))
  ```

### MARKER_XXX — 1 шт. — 🟡 MEDIUM
**Смысл:** XXX в коде — требуется внимание
**Fix:** Закрыть отдельным шагом.

- **строка 395** — # v39.4 (ШАГ 003): реальный ISRC вместо заглушки XX-XXX-00-00000

  ```
        393 |     title = meta.get("title", "ZS Track")
        394 |     artist = meta.get("artist", "ZS Artist")
  >>>   395 |     # v39.4 (ШАГ 003): реальный ISRC вместо заглушки XX-XXX-00-00000
        396 |     from app.core.isrc import get_isrc
        397 |     isrc = get_isrc(meta, fallback="UNREGISTERED")
  ```
