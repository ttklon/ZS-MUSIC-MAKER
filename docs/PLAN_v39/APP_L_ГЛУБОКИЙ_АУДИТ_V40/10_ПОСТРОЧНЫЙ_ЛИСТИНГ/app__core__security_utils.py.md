# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/security_utils.py`

**Всего строк:** 52

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| docstring | 12 | 23.1 |
| code | 9 | 17.3 |
| blank | 7 | 13.5 |
| return | 6 | 11.5 |
| import | 5 | 9.6 |
| try_block | 4 | 7.7 |
| def | 3 | 5.8 |
| branch | 2 | 3.8 |
| comment | 1 | 1.9 |
| raise | 1 | 1.9 |
| stmt | 1 | 1.9 |
| loop | 1 | 1.9 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — security_utils.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Безопасная работа с данными и сетью.
    6 [docstring ] Заменяет уязвимые urllib и MD5 на SHA-256 и валидированные запросы.
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] import hashlib
   10 [import    ] import requests
   11 [import    ] import os
   12 [import    ] from typing import Optional
   13 [import    ] from urllib.parse import urlparse
   14 [blank     ] 
   15 [def       ] def safe_hash(data: str) -> str:
   16 [docstring ]     """Безопасное хеширование через SHA-256 (вместо MD5)."""
   17 [return    ]     return hashlib.sha256(data.encode("utf-8")).hexdigest()
   18 [blank     ] 
   19 [def       ] def download_file(url: str, target_path: str, timeout: int = 30) -> bool:
   20 [docstring ]     """
   21 [docstring ]     Безопасная загрузка файла с валидацией схемы и таймаутом.
   22 [docstring ]     Заменяет уязвимый urllib.request.urlretrieve.
   23 [docstring ]     """
   24 [code      ]     parsed = urlparse(url)
   25 [branch    ]     if parsed.scheme not in ("http", "https"):
   26 [raise     ]         raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
   27 [blank     ] 
   28 [try_block ]     try:
   29 [code      ]         response = requests.get(url, timeout=timeout, stream=True)
   30 [code      ]         response.raise_for_status()
   31 [blank     ]         
   32 [code      ]         os.makedirs(os.path.dirname(target_path), exist_ok=True)
   33 [stmt      ]         with open(target_path, 'wb') as f:
   34 [loop      ]             for chunk in response.iter_content(chunk_size=8192):
   35 [code      ]                 f.write(chunk)
   36 [return    ]         return True
   37 [try_block ]     except Exception as e:
   38 [code      ]         print(f"Download failed: {e}")
   39 [return    ]         return False
   40 [blank     ] 
   41 [def       ] def get_json(url: str, timeout: int = 15) -> Optional[dict]:
   42 [docstring ]     """Безопасное получение JSON через requests."""
   43 [code      ]     parsed = urlparse(url)
   44 [branch    ]     if parsed.scheme not in ("http", "https"):
   45 [return    ]         return None
   46 [blank     ]         
   47 [try_block ]     try:
   48 [code      ]         response = requests.get(url, timeout=timeout)
   49 [code      ]         response.raise_for_status()
   50 [return    ]         return response.json()
   51 [try_block ]     except Exception:
   52 [return    ]         return None
```