# grep-таблицы `tools/genre_validator.py`

## `import` — 3 совпадений
```
    9 | import sys
   10 | from pathlib import Path
   15 | from modules.genre_engine import StyleRegistry, GenreFactory
```

## `print` — 5 совпадений
```
   18 |     print("=== Genre Integrity Audit (100+ Styles) ===")
   23 |     print(f"Total genres found: {len(genres)}")
   43 |         print("✅ All 119+ genres are VALID and BATTLE-READY.")
   46 |         print(f"❌ Found {len(errors)} issues:")
   48 |             print(f"  - {err}")
```

## `except` — 1 совпадений
```
   39 |         except Exception as e:
```

## `try` — 1 совпадений
```
   27 |         try:
```

## `def` — 1 совпадений
```
   17 | def validate_all():
```

## `return` — 2 совпадений
```
   44 |         return True
   49 |         return False
```

## `if` — 4 совпадений
```
   32 |                 if field not in state:
   36 |             if not (20 <= state["bpm_override"] <= 300):
   42 |     if not errors:
   51 | if __name__ == "__main__":
```

## `for` — 3 совпадений
```
   26 |     for g_name in genres:
   31 |             for field in required:
   47 |         for err in errors:
```
