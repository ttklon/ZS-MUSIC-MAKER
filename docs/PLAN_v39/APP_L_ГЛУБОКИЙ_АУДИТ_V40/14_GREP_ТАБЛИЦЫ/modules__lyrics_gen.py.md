# grep-таблицы `modules/lyrics_gen.py`

## `import` — 6 совпадений
```
   15 | from __future__ import annotations
   17 | import json
   18 | import random
   19 | import time
   20 | from pathlib import Path
  161 |         import requests
```

## `print` — 3 совпадений
```
  308 |     print(r["lyrics"])
  309 |     print("---")
  310 |     print("user_included:", r["user_lines_included"])
```

## `except` — 2 совпадений
```
  117 |             except Exception:
  170 |     except Exception:
```

## `try` — 2 совпадений
```
  115 |             try:
  160 |     try:
```

## `def` — 9 совпадений
```
  109 | def _load_lyric_memory() -> list:
  122 | def _save_lyric_memory(entry: dict) -> None:
  128 | def _pick_punches(theme: str, count: int = 4) -> list[str]:
  158 | def _try_ollama(prompt: str, model: str = "llama3") -> str | None:
  175 | def _template_verse(
  194 | def _template_hook_en(user_hooks: list[str]) -> list[str]:
  205 | def _is_english(s: str) -> bool:
  216 | def generate_lyrics(
  295 | def get_lyric_memory(limit: int = 20) -> list:
```

## `return` — 12 совпадений
```
  111 |         return []
  119 |     return out
  155 |     return collected[:count]
  169 |             return r.json().get("response", "").strip()
  172 |     return None
  191 |     return lines
  202 |     return hook * 2  # 4 строки припева
  208 |         return False
  211 |         return False
  213 |     return ascii_letters / len(letters) > 0.8
  282 |     return {
  298 |     return list(reversed(mem))[:limit]
```

## `if` — 14 совпадений
```
  110 |     if not LYRIC_MEMORY.exists():
  114 |         if line.strip():
  134 |     if "шансон" in theme_lower or "централ" in theme_lower or "ветер" in theme_lower or "жиган" in theme_lower:
  147 |         if key in theme_lower:
  150 |     if not collected:
  168 |         if r.status_code == 200:
  182 |         if used_user < len(user_lines) and i in (0, 2):
  200 |         if cand not in hook:
  207 |     if not s:
  210 |     if not letters:
  247 |     if ollama_out and len(ollama_out) > 50:
  261 |             if bilingual:
  269 |         if line.strip() and line.strip() not in lyrics_text:
  301 | if __name__ == "__main__":
```

## `for` — 7 совпадений
```
  113 |     for line in LYRIC_MEMORY.read_text(encoding="utf-8").splitlines():
  146 |     for key, punches in PUNCHES_RU.items():
  151 |         for punches in PUNCHES_RU.values():
  181 |     for i in range(4):
  189 |     for extra in user_lines[used_user:]:
  254 |         for i in range(n_verses):
  268 |     for line in user_lyrics_lines:
```

## `while` — 1 совпадений
```
  198 |     while len(hook) < 2:
```

## `with` — 1 совпадений
```
  124 |     with open(LYRIC_MEMORY, "a", encoding="utf-8") as f:
```

## `requests` — 1 совпадений
```
  163 |         r = requests.post(
```

## `open` — 1 совпадений
```
  124 |     with open(LYRIC_MEMORY, "a", encoding="utf-8") as f:
```
