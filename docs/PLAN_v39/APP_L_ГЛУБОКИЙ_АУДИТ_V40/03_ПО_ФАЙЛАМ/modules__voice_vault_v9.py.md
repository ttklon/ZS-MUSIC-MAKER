# АУДИТ ФАЙЛА: `modules/voice_vault_v9.py`

**LOC:** 314  |  **Размер:** 10301 байт  |  **Проблем:** 8  |  **Risk score:** 5

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 21 | `__future__.annotations` | from |
| 23 | `hashlib` | import |
| 24 | `json` | import |
| 25 | `math` | import |
| 26 | `shutil` | import |
| 27 | `time` | import |
| 28 | `pathlib.Path` | from |
| 31 | `numpy` | import |
| 36 | `soundfile` | import |
| 130 | `faster_whisper.WhisperModel` | from |
| 138 | `whisper` | import |
| 292 | `modules.rvc_trainer_v9` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 69 | `_load_index` | 6 | 2 | ❌ |
| 78 | `_save_index` | 3 | 0 | ❌ |
| 84 | `_md5` | 4 | 1 | ❌ |
| 92 | `_snr_and_clipping` | 23 | 6 | ❌ |
| 118 | `_guess_style` | 6 | 4 | ❌ |
| 128 | `_transcribe` | 16 | 3 | ❌ |
| 147 | `calculate_phoneme_coverage` | 19 | 1 | ✅ |
| 170 | `add_recording` | 44 | 5 | ❌ |
| 217 | `list_recordings` | 5 | 1 | ❌ |
| 225 | `clean_stats` | 29 | 13 | ❌ |
| 257 | `export_manifest_for_rvc` | 25 | 7 | ❌ |
| 285 | `maybe_trigger_retrain` | 24 | 4 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 4 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 170** — public function 'add_recording' без docstring

  ```
        168 | 
        169 | # ============================================================ main API
  >>>   170 | def add_recording(
        171 |     src_path: str,
        172 |     style_hint: str | None = None,
  ```

- **строка 225** — public function 'clean_stats' без docstring

  ```
        223 | 
        224 | 
  >>>   225 | def clean_stats() -> dict:
        226 |     idx = _load_index()
        227 |     items = list(idx.get("items", {}).values())
  ```

- **строка 257** — public function 'export_manifest_for_rvc' без docstring

  ```
        255 | 
        256 | 
  >>>   257 | def export_manifest_for_rvc(out_path: str | None = None) -> str:
        258 |     idx = _load_index()
        259 |     good = []
  ```

- **строка 285** — public function 'maybe_trigger_retrain' без docstring

  ```
        283 | 
        284 | 
  >>>   285 | def maybe_trigger_retrain(rvc_trainer=None) -> dict:
        286 |     stats = clean_stats()
        287 |     if not stats["ready_for_retrain"]:
  ```

### SILENT_EXCEPT_PASS — 2 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 135** — except: pass — тихое подавление ошибок

  ```
        133 |         segs, _ = m.transcribe(str(path))
        134 |         return " ".join(s.text.strip() for s in segs)[:500]
  >>>   135 |     except Exception:
        136 |         pass
        137 |     try:
  ```

- **строка 142** — except: pass — тихое подавление ошибок

  ```
        140 |         m = whisper.load_model("tiny")
        141 |         return (m.transcribe(str(path)).get("text") or "")[:500]
  >>>   142 |     except Exception:
        143 |         pass
        144 |     return None
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 21** — import 'annotations' не используется в теле файла

  ```
         19 | """
         20 | 
  >>>    21 | from __future__ import annotations
         22 | 
         23 | import hashlib
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 314** — print() вместо logger

  ```
        312 | # ============================================================ CLI
        313 | if __name__ == "__main__":
  >>>   314 |     print(json.dumps(clean_stats(), ensure_ascii=False, indent=2))
  ```
