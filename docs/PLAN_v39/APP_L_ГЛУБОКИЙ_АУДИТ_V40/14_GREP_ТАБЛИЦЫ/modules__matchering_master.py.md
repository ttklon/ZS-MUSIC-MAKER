# grep-таблицы `modules/matchering_master.py`

## `import` — 6 совпадений
```
   17 | from __future__ import annotations
   19 | import logging
   20 | from pathlib import Path
   21 | from typing import Any
   26 |     import matchering as mg  # type: ignore
  104 |         from pydub import AudioSegment
```

## `print` — 1 совпадений
```
  133 |     print("Matchering available:", MG_OK)
```

## `except` — 3 совпадений
```
   29 | except Exception:
   53 |         except Exception as e:
  127 |     except Exception as e:
```

## `try` — 3 совпадений
```
   25 | try:
   41 |         try:
  103 |     try:
```

## `def` — 4 совпадений
```
   33 | def match_to_reference(
   63 | def master_to_stand(
   87 | def master_all_stands(target: str, out_dir: str) -> dict[str, Any]:
  100 | def _pydub_fallback(
```

## `return` — 7 совпадений
```
   47 |             return {
   55 |     return {
   75 |         return {
   82 |     return _pydub_fallback(
   97 |     return {"ok": True, "stands": out}
  119 |         return {
  129 |         return {"ok": False, "reason": str(e)}
```

## `if` — 5 совпадений
```
   40 |     if MG_OK:
   44 |             if out_mp3:
   74 |     if not MG_OK:
  115 |         if stand == "club":
  132 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
   93 |     for stand in ("streaming", "car", "club", "tiktok"):
```
