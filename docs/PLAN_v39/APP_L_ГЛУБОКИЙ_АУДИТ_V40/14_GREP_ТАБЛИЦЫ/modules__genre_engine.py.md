# grep-таблицы `modules/genre_engine.py`

## `import` — 6 совпадений
```
    9 | import json
   10 | import os
   11 | from typing import Dict, List
   12 | from dataclasses import dataclass, field
   81 |                 from app.core.logger import app_logger
  101 |         import random
```

## `print` — 3 совпадений
```
  124 |     print(f"Available genres: {len(reg.list_genres())}")
  126 |     print(f"Generated Lo-Fi state: {factory.create_wizard_state('lo-fi_hip_hop')}")
  127 |     print(f"Generated Techno state: {factory.create_wizard_state('techno')}")
```

## `except` — 1 совпадений
```
   80 |             except Exception as e:
```

## `try` — 1 совпадений
```
   53 |             try:
```

## `def` — 8 совпадений
```
   27 |     def __new__(cls, *args, **kwargs):
   33 |     def __init__(self):
   40 |     def _load_defaults(self):
   84 |     def register(self, profile: GenreProfile):
   87 |     def get_profile(self, name: str) -> GenreProfile:
   92 |     def list_genres(self) -> List[str]:
   96 |     def __init__(self, registry: StyleRegistry):
   99 |     def create_wizard_state(self, genre_name: str, override: dict = None) -> dict:
```

## `class` — 3 совпадений
```
   15 | class GenreProfile:
   24 | class StyleRegistry:
   95 | class GenreFactory:
```

## `raise` — 1 совпадений
```
   58 |                         raise ValueError("Genre config must be a JSON object")
```

## `return` — 5 совпадений
```
   31 |         return cls._instance
   35 |             return
   90 |         return self.genres.get(name, self.genres.get(safe_name, self.genres.get("drift_phonk")))
   93 |         return list(self.genres.keys())
  119 |         return state
```

## `if` — 7 совпадений
```
   28 |         if not cls._instance:
   34 |         if self._initialized:
   52 |         if os.path.exists(config_path):
   57 |                     if not isinstance(data, dict):
   61 |                         if not isinstance(genre_list, list):
  116 |         if override:
  121 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
   60 |                     for category, genre_list in data.items():
   63 |                         for g_name in genre_list:
```

## `with` — 1 совпадений
```
   54 |                 with open(config_path, "r", encoding="utf-8") as f:
```

## `open` — 1 совпадений
```
   54 |                 with open(config_path, "r", encoding="utf-8") as f:
```
