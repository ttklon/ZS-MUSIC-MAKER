# grep-таблицы `modules/karaoke_engine.py`

## `import` — 8 совпадений
```
   14 | from __future__ import annotations
   16 | import json
   17 | import logging
   18 | import threading
   19 | import time
   20 | from collections.abc import Callable
   21 | from typing import Any
  156 |         import librosa
```

## `print` — 1 совпадений
```
  191 |     print(json.dumps(wm, ensure_ascii=False, indent=2))
```

## `except` — 2 совпадений
```
   63 |             except Exception as e:
  185 |     except Exception as e:
```

## `try` — 2 совпадений
```
   61 |             try:
  155 |     try:
```

## `def` — 10 совпадений
```
   31 |     def __init__(
   56 |     def on(self, event: str, cb: Callable) -> None:
   59 |     def _fire(self, event: str, *args, **kwargs) -> None:
   66 |     def elapsed_ms(self) -> int:
   71 |     def current_word(self) -> dict[str, Any] | None:
   80 |     def start(self) -> None:
   85 |     def stop(self) -> None:
   89 |     def _run(self) -> None:
  126 | def make_wordmap_from_lyrics(
  148 | def score_take(
```

## `class` — 1 совпадений
```
   26 | class KaraokeSession:
```

## `return` — 8 совпадений
```
   68 |             return 0
   69 |         return int((time.time() - self._start_ts) * 1000)
   77 |                 return w
   78 |         return None
   95 |                 return
  145 |     return words
  178 |         return {
  186 |         return {"ok": False, "reason": str(e), "score": 0}
```

## `if` — 8 совпадений
```
   67 |         if not self._start_ts:
   76 |             if start <= t < start + dur:
   94 |             if self._stop.is_set():
  105 |             if self.lyrics
  110 |             if now >= next_beat_at:
  117 |                 if start <= t_ms and idx > last_word_idx:
  162 |             if expected_word_map
  189 | if __name__ == "__main__":
```

## `for` — 6 совпадений
```
   60 |         for cb in self._callbacks.get(event, []):
   73 |         for w in self.lyrics:
   91 |         for i in range(self.count_in_beats):
  115 |             for idx, w in enumerate(self.lyrics):
  138 |     for line in lyrics_text.strip().splitlines():
  139 |         for w in line.split():
```

## `while` — 1 совпадений
```
  108 |         while time.time() < end_time and not self._stop.is_set():
```

## `sleep` — 2 совпадений
```
   93 |             time.sleep(self.beat_ms / 1000.0)
  121 |             time.sleep(0.02)
```
