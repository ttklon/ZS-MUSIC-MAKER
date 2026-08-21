# grep-таблицы `agents/training_texts.py`

## `import` — 2 совпадений
```
    8 | import json
    9 | import os
```

## `print` — 1 совпадений
```
  140 |     print(json.dumps(get_next_text(), ensure_ascii=False, indent=2))
```

## `def` — 5 совпадений
```
   69 | def get_next_text(style: str = None) -> dict:
   99 | def _styles_remaining(progress: dict) -> list:
  103 | def _instruction(style: str) -> str:
  116 | def all_styles() -> list:
  120 | def progress_summary() -> dict:
```

## `return` — 5 совпадений
```
   89 |     return {
  100 |     return [s for s in BANK if progress.get(s, 0) < len(BANK[s])]
  104 |     return {
  117 |     return list(BANK.keys())
  136 |     return summary
```

## `if` — 2 совпадений
```
   76 |     if style is None:
  139 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
  127 |     for style in BANK:
```

## `open` — 3 совпадений
```
   73 |         json.load(open(idx_file, encoding="utf-8")) if os.path.exists(idx_file) else {}
   86 |         progress, open(idx_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2
  124 |         json.load(open(idx_file, encoding="utf-8")) if os.path.exists(idx_file) else {}
```
