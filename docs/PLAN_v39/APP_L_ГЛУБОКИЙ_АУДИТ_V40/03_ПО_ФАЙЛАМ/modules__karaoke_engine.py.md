# АУДИТ ФАЙЛА: `modules/karaoke_engine.py`

**LOC:** 191  |  **Размер:** 6660 байт  |  **Проблем:** 4  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 14 | `__future__.annotations` | from |
| 16 | `json` | import |
| 17 | `logging` | import |
| 18 | `threading` | import |
| 19 | `time` | import |
| 20 | `collections.abc.Callable` | from |
| 21 | `typing.Any` | from |
| 156 | `librosa` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 126 | `make_wordmap_from_lyrics` | 19 | 2 | ✅ |
| 148 | `score_take` | 38 | 1 | ✅ |
| 31 | `__init__` | 23 | 0 | ✅ |
| 56 | `on` | 1 | 0 | ❌ |
| 59 | `_fire` | 5 | 2 | ❌ |
| 66 | `elapsed_ms` | 3 | 1 | ❌ |
| 71 | `current_word` | 7 | 2 | ❌ |
| 80 | `start` | 3 | 0 | ❌ |
| 85 | `stop` | 2 | 0 | ❌ |
| 89 | `_run` | 34 | 8 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 26 | `KaraokeSession` | ✅ |

## Проблемы (детально, с цитатой кода)

### BLOCKING_SLEEP — 2 шт. — 🟢 LOW
**Смысл:** time.sleep() без комментария/аргументации
**Fix:** Комментарий или await asyncio.sleep().

- **строка 93** — time.sleep(...) без пояснения

  ```
         91 |         for i in range(self.count_in_beats):
         92 |             self._fire("on_beat", {"beat": i + 1, "is_count_in": True})
  >>>    93 |             time.sleep(self.beat_ms / 1000.0)
         94 |             if self._stop.is_set():
         95 |                 return
  ```

- **строка 121** — time.sleep(...) без пояснения

  ```
        119 |                     last_word_idx = idx
        120 |                     break
  >>>   121 |             time.sleep(0.02)
        122 |         self.state = "finished"
        123 |         self._fire("on_end", {"duration_ms": self.elapsed_ms()})
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 14** — import 'annotations' не используется в теле файла

  ```
         12 | """
         13 | 
  >>>    14 | from __future__ import annotations
         15 | 
         16 | import json
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 191** — print() вместо logger

  ```
        189 | if __name__ == "__main__":
        190 |     wm = make_wordmap_from_lyrics("Тачки летят по трассе\nЛето жарит нас", bpm=140)
  >>>   191 |     print(json.dumps(wm, ensure_ascii=False, indent=2))
  ```
