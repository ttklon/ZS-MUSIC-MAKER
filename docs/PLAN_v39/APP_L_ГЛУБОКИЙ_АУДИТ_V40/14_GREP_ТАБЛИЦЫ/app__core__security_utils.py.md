# grep-таблицы `app/core/security_utils.py`

## `import` — 5 совпадений
```
    9 | import hashlib
   10 | import requests
   11 | import os
   12 | from typing import Optional
   13 | from urllib.parse import urlparse
```

## `print` — 1 совпадений
```
   38 |         print(f"Download failed: {e}")
```

## `except` — 2 совпадений
```
   37 |     except Exception as e:
   51 |     except Exception:
```

## `try` — 2 совпадений
```
   28 |     try:
   47 |     try:
```

## `def` — 3 совпадений
```
   15 | def safe_hash(data: str) -> str:
   19 | def download_file(url: str, target_path: str, timeout: int = 30) -> bool:
   41 | def get_json(url: str, timeout: int = 15) -> Optional[dict]:
```

## `raise` — 1 совпадений
```
   26 |         raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
```

## `return` — 6 совпадений
```
   17 |     return hashlib.sha256(data.encode("utf-8")).hexdigest()
   36 |         return True
   39 |         return False
   45 |         return None
   50 |         return response.json()
   52 |         return None
```

## `if` — 2 совпадений
```
   25 |     if parsed.scheme not in ("http", "https"):
   44 |     if parsed.scheme not in ("http", "https"):
```

## `for` — 1 совпадений
```
   34 |             for chunk in response.iter_content(chunk_size=8192):
```

## `with` — 1 совпадений
```
   33 |         with open(target_path, 'wb') as f:
```

## `requests` — 3 совпадений
```
   29 |         response = requests.get(url, timeout=timeout, stream=True)
   42 |     """Безопасное получение JSON через requests."""
   48 |         response = requests.get(url, timeout=timeout)
```

## `open` — 1 совпадений
```
   33 |         with open(target_path, 'wb') as f:
```
