# grep-таблицы `modules/presets.py`

## `import` — 2 совпадений
```
    6 | import json
    7 | import os
```

## `print` — 1 совпадений
```
  170 |     print(json.dumps(list_presets(), ensure_ascii=False, indent=2))
```

## `except` — 2 совпадений
```
   99 |         except Exception:
  133 |         except Exception:
```

## `try` — 2 совпадений
```
   97 |         try:
  131 |         try:
```

## `def` — 5 совпадений
```
   95 | def _load_all() -> dict:
  108 | def list_presets() -> list:
  121 | def get_preset(key: str) -> dict:
  128 | def save_user_preset(key: str, preset: dict) -> dict:
  142 | def preset_to_style_vector(key: str) -> dict:
```

## `return` — 7 совпадений
```
  105 |     return merged
  109 |     return [
  124 |         return {"error": f"пресет '{key}' не найден"}
  125 |     return p
  139 |     return {"ok": True, "key": key, "saved_to": PRESETS_FILE}
  145 |         return p
  146 |     return {
```

## `if` — 5 совпадений
```
   96 |     if os.path.exists(PRESETS_FILE):
  123 |     if not p:
  130 |     if os.path.exists(PRESETS_FILE):
  144 |     if "error" in p:
  169 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
  117 |         for k, v in _load_all().items()
```

## `open` — 3 совпадений
```
   98 |             user = json.load(open(PRESETS_FILE, encoding="utf-8"))
  132 |             user = json.load(open(PRESETS_FILE, encoding="utf-8"))
  137 |         user, open(PRESETS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2
```
