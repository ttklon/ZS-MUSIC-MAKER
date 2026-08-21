# grep-таблицы `modules/lyrics_gen_v8.py`

## `import` — 6 совпадений
```
   19 | from __future__ import annotations
   21 | import random
   22 | import re
   24 | from modules import (
   92 |         from agents.trend_scout_v3 import actual_slang_for_prompt
  157 |                 from agents.trend_scout_v3 import scout
```

## `except` — 6 совпадений
```
   95 |     except Exception:
  117 |         except Exception:
  136 |     except TypeError:
  140 |         except Exception:
  142 |     except Exception as e:
  161 |             except Exception:
```

## `try` — 5 совпадений
```
   91 |     try:
  102 |         try:
  128 |     try:
  138 |         try:
  156 |             try:
```

## `def` — 3 совпадений
```
   30 | def _split_blocks(text: str) -> dict[str, list[str]]:
   64 | def _validate_rhythm(
   77 | def generate_lyrics_v8(
```

## `return` — 3 совпадений
```
   61 |     return blocks
   74 |     return kept or lines
  189 |     return {
```

## `if` — 15 совпадений
```
   43 |         if not line:
   46 |         if low.startswith("[") and low.endswith("]"):
   47 |             if "интро" in low or "intro" in low:
   72 |         if target_avg * (1 - tol) <= n <= target_avg * (1 + tol) or len(lines) < 4:
  101 |     if author:
  105 |             if not profile:
  108 |             if profile:
  122 |     if user_words:
  124 |     if slang:
  151 |     if lang_mix == "ru+en":
  155 |         if not has_en:
  166 |     if blocks["intro"]:
  176 |     if blocks["bridge"]:
  178 |     if blocks["outro"]:
  185 |     if want_female_backing and chorus_lines:
```

## `for` — 3 совпадений
```
   41 |     for raw_line in text.splitlines():
   69 |     for l in lines:
  147 |     for key in ("verse1", "verse2", "chorus"):
```
