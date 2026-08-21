# АУДИТ ФАЙЛА: `ui/karaoke_recorder.py`

**LOC:** 154  |  **Размер:** 4949 байт  |  **Проблем:** 7  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 12 | `__future__.annotations` | from |
| 14 | `json` | import |
| 15 | `os` | import |
| 16 | `time` | import |
| 17 | `pathlib.Path` | from |
| 27 | `numpy` | import |
| 28 | `soundfile` | import |
| 57 | `platform` | import |
| 88 | `numpy` | import |
| 89 | `sounddevice` | import |
| 90 | `soundfile` | import |
| 107 | `modules.voice_convert.add_recording` | from |
| 145 | `modules.voice_convert.vault_summary` | from |
| 60 | `winsound` | import |
| 67 | `subprocess` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 24 | `build_metronome` | 22 | 3 | ✅ |
| 49 | `play_backing_track` | 24 | 4 | ✅ |
| 76 | `record_with_backing` | 45 | 4 | ✅ |
| 124 | `karaoke_ui` | 15 | 0 | ✅ |
| 142 | `get_progress` | 7 | 1 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 5 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 45** — print() вместо logger

  ```
         43 |         return out
         44 |     except Exception as e:
  >>>    45 |         print(f"[karaoke.metronome] {e}")
         46 |         return ""
         47 | 
  ```

- **строка 72** — print() вместо logger

  ```
         70 |         return True
         71 |     except Exception as e:
  >>>    72 |         print(f"[karaoke.play_backing_track] {e}")
         73 |         return False
         74 | 
  ```

- **строка 97** — print() вместо logger

  ```
         95 |         play_backing_track(backing_path, in_headphones=True)
         96 | 
  >>>    97 |     print(f"[karaoke] Запись {duration_sec} сек в стиле '{style}' — ПОЕХАЛИ!")
         98 |     audio = sd.rec(int(duration_sec * sr), samplerate=sr, channels=1, dtype="float32")
         99 |     sd.wait()
  ```

- **строка 153** — print() вместо logger

  ```
        151 | 
        152 | if __name__ == "__main__":
  >>>   153 |     print(json.dumps(get_progress(), ensure_ascii=False, indent=2))
        154 |     print("Метроном для BPM=140:", build_metronome(140, duration_sec=4))
  ```

- **строка 154** — print() вместо logger

  ```
        152 | if __name__ == "__main__":
        153 |     print(json.dumps(get_progress(), ensure_ascii=False, indent=2))
  >>>   154 |     print("Метроном для BPM=140:", build_metronome(140, duration_sec=4))
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 12** — import 'annotations' не используется в теле файла

  ```
         10 | """
         11 | 
  >>>    12 | from __future__ import annotations
         13 | 
         14 | import json
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 118** — except: pass — тихое подавление ошибок

  ```
        116 |             },
        117 |         )
  >>>   118 |     except Exception:
        119 |         pass
        120 | 
  ```
