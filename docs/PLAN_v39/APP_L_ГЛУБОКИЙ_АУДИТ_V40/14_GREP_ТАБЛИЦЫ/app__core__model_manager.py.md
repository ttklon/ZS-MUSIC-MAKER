# grep-таблицы `app/core/model_manager.py`

## `import` — 4 совпадений
```
    9 | from pathlib import Path
   10 | from app.core.security_utils import download_file
   11 | from app.core.logger import app_logger
   50 |             import torch
```

## `except` — 1 совпадений
```
   51 |         except ImportError as e:
```

## `try` — 1 совпадений
```
   49 |         try:
```

## `def` — 3 совпадений
```
   19 |     def __init__(self):
   31 |     def ensure_model(self, model_id: str) -> str:
   47 |     def load_torch_model(self, model_id: str, map_location="cpu"):
```

## `class` — 1 совпадений
```
   18 | class ModelManager:
```

## `raise` — 2 совпадений
```
   43 |                 raise RuntimeError(f"Failed to download model {model_id}")
   52 |             raise RuntimeError(
```

## `return` — 3 совпадений
```
   35 |             return str(self.base_dir / model_id)
   45 |         return str(target_path)
   59 |         return torch.load(path, map_location=map_location, weights_only=True)
```

## `if` — 3 совпадений
```
   33 |         if model_id not in self.registry:
   40 |         if not target_path.exists():
   42 |             if not download_file(info["url"], str(target_path)):
```
