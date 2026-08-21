# grep-таблицы `modules/provenance.py`

## `import` — 3 совпадений
```
    7 | import json
    8 | import os
    9 | import time
```

## `print` — 1 совпадений
```
  142 |     print(json.dumps(check_commercial_safe(), ensure_ascii=False, indent=2))
```

## `except` — 1 совпадений
```
   66 |         except Exception:
```

## `try` — 1 совпадений
```
   64 |         try:
```

## `def` — 6 совпадений
```
   62 | def _load():
   71 | def _save(data):
   75 | def add_sample(
  104 | def list_samples() -> list:
  108 | def check_commercial_safe() -> dict:
  128 | def generate_attribution_text() -> str:
```

## `return` — 7 совпадений
```
   65 |             return json.load(open(VAULT, encoding="utf-8"))
   67 |             return []
   68 |     return []
  101 |     return entry
  105 |     return _load()
  116 |     return {
  138 |     return "\n".join(lines) if len(lines) > 1 else "Атрибуция не требуется."
```

## `if` — 3 совпадений
```
   63 |     if os.path.exists(VAULT):
  134 |         if info.get("attribution"):
  141 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
  132 |     for s in data:
```

## `open` — 2 совпадений
```
   65 |             return json.load(open(VAULT, encoding="utf-8"))
   72 |     json.dump(data, open(VAULT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
```
