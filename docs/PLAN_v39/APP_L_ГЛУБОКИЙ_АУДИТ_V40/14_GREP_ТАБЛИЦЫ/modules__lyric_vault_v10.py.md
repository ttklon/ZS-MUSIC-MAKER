# grep-таблицы `modules/lyric_vault_v10.py`

## `import` — 8 совпадений
```
   15 | from __future__ import annotations
   17 | import hashlib
   18 | import json
   19 | import logging
   20 | import time
   21 | from collections import Counter
   22 | from pathlib import Path
   23 | from typing import Any
```

## `print` — 1 совпадений
```
  252 |     print(json.dumps(r, ensure_ascii=False, indent=2))
```

## `except` — 2 совпадений
```
   95 |             except Exception:
  240 |         except Exception:
```

## `try` — 2 совпадений
```
   93 |             try:
  238 |         try:
```

## `def` — 10 совпадений
```
   33 | def _syllable_count(line: str) -> int:
   50 | def add_line(
   79 | def load_all() -> list[dict[str, Any]]:
  109 | def find_lines(
  150 | def mark_used(line_ids: list[str], track_id: str) -> None:
  161 | def rebuild_index() -> dict[str, Any]:
  182 | def export_lrc(
  212 | def _recently_used_ids(last_n_tracks: int = 5) -> set:
  236 | def _load_usage() -> dict[str, list]:
  245 | def _save_usage(u: dict[str, list]) -> None:
```

## `return` — 11 совпадений
```
   47 |     return max(1, n)
   76 |     return entry
   86 |         return []
  106 |     return out
  147 |     return matched[:limit]
  179 |     return idx
  209 |     return out_lrc
  233 |     return used
  239 |             return json.loads(USAGE_LOG.read_text(encoding="utf-8"))
  241 |             return {}
  242 |     return {}
```

## `if` — 19 совпадений
```
   44 |         if is_v and not prev_vowel:
   85 |     if not MEMORY_JSONL.exists():
   91 |             if not line:
   98 |             if "id" not in entry:
  101 |             if "text" not in entry:
  103 |             if "syllables" not in entry:
  128 |         if e["id"] in recently_used:
  130 |         if bpm and e.get("bpm") and abs(e["bpm"] - bpm) > 15:
  132 |         if emotion and e.get("emotion") != emotion:
  134 |         if topic and e.get("topic") != topic:
  136 |         if lang and e.get("lang") != lang:
  139 |         if syllable_min and syl < syllable_min:
  141 |         if syllable_max and syl > syllable_max:
  199 |             if isinstance(e, dict):
  223 |         if t not in seen:
  225 |         if len(seen) >= last_n_tracks:
  231 |             if e["track"] in recent_tracks:
  237 |     if USAGE_LOG.exists():
  250 | if __name__ == "__main__":
```

## `for` — 10 совпадений
```
   42 |     for ch in line:
   89 |         for i, line in enumerate(f):
  127 |     for e in all_lines:
  156 |     for lid in line_ids:
  198 |         for e in lines:
  216 |     for lid, entries in usage.items():
  217 |         for e in entries:
  222 |     for _, t in all_tracks:
  229 |     for lid, entries in usage.items():
  230 |         for e in entries:
```

## `with` — 3 совпадений
```
   74 |     with open(MEMORY_JSONL, "a", encoding="utf-8") as f:
   88 |     with open(MEMORY_JSONL, "r", encoding="utf-8") as f:
  195 |     with open(out_lrc, "w", encoding="utf-8") as f:
```

## `open` — 3 совпадений
```
   74 |     with open(MEMORY_JSONL, "a", encoding="utf-8") as f:
   88 |     with open(MEMORY_JSONL, "r", encoding="utf-8") as f:
  195 |     with open(out_lrc, "w", encoding="utf-8") as f:
```
