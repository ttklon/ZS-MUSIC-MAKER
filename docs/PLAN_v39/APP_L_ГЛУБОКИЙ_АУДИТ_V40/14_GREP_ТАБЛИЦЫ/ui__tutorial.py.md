# grep-таблицы `ui/tutorial.py`

## `import` — 2 совпадений
```
    8 | import json
    9 | import os
```

## `print` — 1 совпадений
```
  293 |         print(f"{i+1}. {s['title']}")
```

## `except` — 2 совпадений
```
   25 |     except Exception:
  228 |         except Exception:
```

## `try` — 2 совпадений
```
   18 |     try:
  226 |         try:
```

## `def` — 9 совпадений
```
   14 | def _resolve_settings_file() -> str:
  224 | def get_tutorial_settings() -> dict:
  233 | def save_tutorial_settings(settings: dict):
  242 | def get_step(index: int) -> dict:
  248 | def next_step() -> dict:
  265 | def prev_step() -> dict:
  275 | def skip_tutorial():
  282 | def reset_tutorial():
  287 | def get_total_steps() -> int:
```

## `return` — 11 совпадений
```
   27 |     return new
  227 |             return json.load(open(SETTINGS_FILE, encoding="utf-8"))
  229 |             return {}
  230 |     return {"enabled": True, "current_step": 0, "completed": False}
  244 |         return STEPS[index]
  245 |     return None
  254 |         return get_step(idx + 1)
  257 |     return {
  271 |         return get_step(idx - 1)
  272 |     return get_step(0)
  288 |     return len(STEPS)
```

## `if` — 6 совпадений
```
   20 |         if not os.path.exists(new) and os.path.exists(old):
  225 |     if os.path.exists(SETTINGS_FILE):
  243 |     if 0 <= index < len(STEPS):
  251 |     if idx < len(STEPS) - 1:
  268 |     if idx > 0:
  291 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
  292 |     for i, s in enumerate(STEPS):
```

## `with` — 2 совпадений
```
   21 |             with open(old, encoding="utf-8") as f:
   23 |             with open(new, "w", encoding="utf-8") as f:
```

## `open` — 4 совпадений
```
   21 |             with open(old, encoding="utf-8") as f:
   23 |             with open(new, "w", encoding="utf-8") as f:
  227 |             return json.load(open(SETTINGS_FILE, encoding="utf-8"))
  236 |         open(SETTINGS_FILE, "w", encoding="utf-8"),
```
