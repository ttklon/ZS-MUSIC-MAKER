# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/model_manager.py`

**Всего строк:** 62

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 19 | 30.6 |
| blank | 9 | 14.5 |
| comment | 8 | 12.9 |
| docstring | 8 | 12.9 |
| import | 4 | 6.5 |
| def | 3 | 4.8 |
| branch | 3 | 4.8 |
| return | 3 | 4.8 |
| raise | 2 | 3.2 |
| try_block | 2 | 3.2 |
| class | 1 | 1.6 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — model_manager.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Автоматическое управление нейросетевыми моделями.
    6 [docstring ] Решает проблему "Модельного Голода" и "Уязвимой Десериализации".
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] from pathlib import Path
   10 [import    ] from app.core.security_utils import download_file
   11 [import    ] from app.core.logger import app_logger
   12 [blank     ] 
   13 [comment   ] # v34 FIX (P2.8): torch больше не импортируется на верхнем уровне.
   14 [comment   ] # Раньше `import app.core.model_manager` (core-слой!) мгновенно падал на
   15 [comment   ] # машине без torch — это роняло install.py (шаг 5) и весь core import-граф.
   16 [comment   ] # torch нужен ТОЛЬКО для load_torch_model → ленивый импорт внутри метода.
   17 [blank     ] 
   18 [class     ] class ModelManager:
   19 [def       ]     def __init__(self):
   20 [code      ]         self.base_dir = Path(__file__).resolve().parents[2] / "models"
   21 [code      ]         self.base_dir.mkdir(parents=True, exist_ok=True)
   22 [comment   ]         # Маппинг моделей и их источников (примеры)
   23 [code      ]         self.registry = {
   24 [code      ]             "whisper_tiny": {
   25 [code      ]                 "url": "https://openaipublic.azureedge.net/main/whisper/models/6514702301534eab811cb7871f6610179f57213b63d17d07e318e0d12c61d2/tiny.pt",
   26 [code      ]                 "path": "whisper/tiny.pt",
   27 [code      ]                 "expected_hash": "6514702301534eab811cb7871f6610179f57213b63d17d07e318e0d12c61d2"
   28 [code      ]             }
   29 [code      ]         }
   30 [blank     ] 
   31 [def       ]     def ensure_model(self, model_id: str) -> str:
   32 [docstring ]         """Проверяет наличие модели и скачивает её при необходимости."""
   33 [branch    ]         if model_id not in self.registry:
   34 [code      ]             app_logger.warning(f"Model {model_id} not in registry, assuming local path.")
   35 [return    ]             return str(self.base_dir / model_id)
   36 [blank     ] 
   37 [code      ]         info = self.registry[model_id]
   38 [code      ]         target_path = self.base_dir / info["path"]
   39 [blank     ]         
   40 [branch    ]         if not target_path.exists():
   41 [code      ]             app_logger.info(f"Downloading model {model_id}...")
   42 [branch    ]             if not download_file(info["url"], str(target_path)):
   43 [raise     ]                 raise RuntimeError(f"Failed to download model {model_id}")
   44 [blank     ]         
   45 [return    ]         return str(target_path)
   46 [blank     ] 
   47 [def       ]     def load_torch_model(self, model_id: str, map_location="cpu"):
   48 [docstring ]         """Безопасная загрузка PyTorch модели (weights_only=True)."""
   49 [try_block ]         try:
   50 [import    ]             import torch
   51 [try_block ]         except ImportError as e:
   52 [raise     ]             raise RuntimeError(
   53 [code      ]                 "PyTorch не установлен — загрузка нейромоделей недоступна. "
   54 [code      ]                 "Установите: pip install torch (или запустите install.py)"
   55 [code      ]             ) from e
   56 [code      ]         path = self.ensure_model(model_id)
   57 [code      ]         app_logger.info(f"Safely loading model: {model_id}")
   58 [comment   ]         # B614 FIX: weights_only=True
   59 [return    ]         return torch.load(path, map_location=map_location, weights_only=True)
   60 [blank     ] 
   61 [comment   ] # Глобальный менеджер
   62 [code      ] models = ModelManager()
```