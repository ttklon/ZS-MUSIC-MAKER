# grep-таблицы `modules/lyrics_gen_ai.py`

## `import` — 8 совпадений
```
    3 | from __future__ import annotations
    4 | import json, re, time
    5 | from pathlib import Path
    6 | from typing import Any, Dict
    7 | from app.ai.registry import registry
    8 | from app.ai import prompts as P
    9 | from app.ai import llm_service as LLM
   10 | from modules.artist_dossier import DossierManager
```

## `def` — 1 совпадений
```
   17 | def generate_lyrics_ai(theme, style_vector=None, n_verses=2, user_lyrics_lines=None,
```

## `return` — 3 совпадений
```
   33 |         return {"ok": False, "lyrics": "",
   41 |         return {"ok": False, "lyrics": text or "", "reason": "empty LLM output",
   54 |     return {"ok": True, "lyrics": text, "source": "lyrics_llm",
```

## `if` — 4 совпадений
```
   24 |     if artist_slug:
   32 |     if not registry.is_available("lyrics_llm"):
   40 |     if not text or len(text) < 60:
   46 |     if missing:
```

## `with` — 2 совпадений
```
   36 |     with registry.use("lyrics_llm") as m:
   49 |     with open(MEMORY, "a", encoding="utf-8") as f:
```

## `open` — 1 совпадений
```
   49 |     with open(MEMORY, "a", encoding="utf-8") as f:
```
