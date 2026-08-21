# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/hw_probe.py`

**Всего строк:** 65

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 25 | 38.5 |
| blank | 16 | 24.6 |
| import | 7 | 10.8 |
| try_block | 6 | 9.2 |
| branch | 3 | 4.6 |
| def | 2 | 3.1 |
| comment | 2 | 3.1 |
| docstring | 1 | 1.5 |
| decorator | 1 | 1.5 |
| class | 1 | 1.5 |
| return | 1 | 1.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """Автодетект железа: CUDA / DirectML / CPU + VRAM + режим full/fallback."""
    2 [blank     ] 
    3 [import    ] from __future__ import annotations
    4 [blank     ] 
    5 [import    ] import json
    6 [import    ] import platform
    7 [import    ] from dataclasses import asdict, dataclass
    8 [blank     ] 
    9 [blank     ] 
   10 [decorator ] @dataclass
   11 [class     ] class HW:
   12 [code      ]     gpu_name: str = "CPU"
   13 [code      ]     vram_gb: float = 0.0
   14 [code      ]     backend: str = "cpu"  # "cuda" | "directml" | "cpu"
   15 [code      ]     ram_gb: float = 0.0
   16 [code      ]     cpu_name: str = ""
   17 [code      ]     os_name: str = ""
   18 [code      ]     mode: str = "fallback"  # "full" | "fallback"
   19 [blank     ] 
   20 [blank     ] 
   21 [def       ] def probe() -> HW:
   22 [try_block ]     try:
   23 [import    ]         import psutil
   24 [blank     ] 
   25 [code      ]         ram_gb = round(psutil.virtual_memory().total / 1e9, 1)
   26 [try_block ]     except Exception:
   27 [code      ]         ram_gb = 0.0
   28 [code      ]     hw = HW(ram_gb=ram_gb, cpu_name=platform.processor(), os_name=platform.platform())
   29 [blank     ] 
   30 [comment   ]     # 1. CUDA
   31 [try_block ]     try:
   32 [import    ]         import torch
   33 [blank     ] 
   34 [branch    ]         if torch.cuda.is_available():
   35 [code      ]             hw.gpu_name = torch.cuda.get_device_name(0)
   36 [code      ]             hw.vram_gb = round(
   37 [code      ]                 torch.cuda.get_device_properties(0).total_memory / 1e9, 1
   38 [code      ]             )
   39 [code      ]             hw.backend = "cuda"
   40 [try_block ]     except Exception:
   41 [code      ]         pass
   42 [blank     ] 
   43 [comment   ]     # 2. DirectML (AMD/Intel iGPU на Windows)
   44 [branch    ]     if hw.backend == "cpu":
   45 [try_block ]         try:
   46 [import    ]             import torch_directml as dml
   47 [blank     ] 
   48 [code      ]             hw.gpu_name = (
   49 [code      ]                 dml.device_name(0) if hasattr(dml, "device_name") else "DirectML GPU"
   50 [code      ]             )
   51 [code      ]             hw.vram_gb = 4.0  # оценочно — уточняется через DXGI
   52 [code      ]             hw.backend = "directml"
   53 [try_block ]         except Exception:
   54 [code      ]             pass
   55 [blank     ] 
   56 [code      ]     hw.mode = "full" if hw.vram_gb >= 10 else "fallback"
   57 [return    ]     return hw
   58 [blank     ] 
   59 [blank     ] 
   60 [def       ] def main():
   61 [code      ]     print(json.dumps(asdict(probe()), ensure_ascii=False, indent=2))
   62 [blank     ] 
   63 [blank     ] 
   64 [branch    ] if __name__ == "__main__":
   65 [code      ]     main()
```