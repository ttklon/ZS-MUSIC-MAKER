# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/hw_directml.py`

**Всего строк:** 145

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 61 | 42.1 |
| blank | 21 | 14.5 |
| docstring | 14 | 9.7 |
| branch | 14 | 9.7 |
| import | 9 | 6.2 |
| try_block | 8 | 5.5 |
| return | 8 | 5.5 |
| def | 4 | 2.8 |
| comment | 4 | 2.8 |
| loop | 1 | 0.7 |
| stmt | 1 | 0.7 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v10 — DirectML / AMD ускорение
    3 [docstring ] ==============================================
    4 [docstring ] ТЗ 15.2: если решение требует NVIDIA CUDA, а у пользователя AMD —
    5 [docstring ] ищем альтернативу (DirectML, CPU-режим, ONNX).
    6 [blank     ] 
    7 [docstring ] Автодетект и настройка torch-directml для AMD RX 580 на Windows.
    8 [docstring ] Также логика fallback на CPU и оценка VRAM.
    9 [docstring ] """
   10 [blank     ] 
   11 [import    ] from __future__ import annotations
   12 [blank     ] 
   13 [import    ] import json
   14 [import    ] import logging
   15 [import    ] import platform
   16 [import    ] import subprocess
   17 [import    ] from pathlib import Path
   18 [import    ] from typing import Any
   19 [blank     ] 
   20 [code      ] log = logging.getLogger("zsmm.hw_directml")
   21 [blank     ] 
   22 [blank     ] 
   23 [def       ] def detect() -> dict[str, Any]:
   24 [docstring ]     """
   25 [docstring ]     Возвращает {gpu_kind, backend, device_str, vram_mb, recommendations}
   26 [docstring ]     """
   27 [code      ]     out = {
   28 [code      ]         "os": platform.system(),
   29 [code      ]         "arch": platform.machine(),
   30 [code      ]         "gpu_kind": "unknown",
   31 [code      ]         "backend": "cpu",
   32 [code      ]         "device_str": "cpu",
   33 [code      ]         "vram_mb": 0,
   34 [code      ]         "torch_cuda": False,
   35 [code      ]         "torch_directml": False,
   36 [code      ]         "recommendations": [],
   37 [code      ]     }
   38 [blank     ] 
   39 [comment   ]     # 1) torch + CUDA
   40 [try_block ]     try:
   41 [import    ]         import torch
   42 [blank     ] 
   43 [branch    ]         if torch.cuda.is_available():
   44 [code      ]             out["torch_cuda"] = True
   45 [code      ]             out["gpu_kind"] = "nvidia"
   46 [code      ]             out["backend"] = "cuda"
   47 [code      ]             out["device_str"] = "cuda:0"
   48 [try_block ]             try:
   49 [code      ]                 props = torch.cuda.get_device_properties(0)
   50 [code      ]                 out["vram_mb"] = int(props.total_memory / (1024 * 1024))
   51 [code      ]                 out["gpu_name"] = props.name
   52 [try_block ]             except Exception:
   53 [code      ]                 pass
   54 [try_block ]     except Exception as e:
   55 [code      ]         log.debug("no torch cuda: %s", e)
   56 [blank     ] 
   57 [comment   ]     # 2) DirectML (AMD/Intel на Windows)
   58 [branch    ]     if out["backend"] == "cpu":
   59 [try_block ]         try:
   60 [import    ]             import torch_directml  # type: ignore
   61 [blank     ] 
   62 [code      ]             out["torch_directml"] = True
   63 [code      ]             n = torch_directml.device_count()
   64 [branch    ]             if n > 0:
   65 [code      ]                 out["backend"] = "directml"
   66 [code      ]                 out["device_str"] = "privateuseone:0"
   67 [code      ]                 out["gpu_kind"] = "amd_or_intel"
   68 [code      ]                 out["gpu_name"] = torch_directml.device_name(0)
   69 [try_block ]         except Exception as e:
   70 [code      ]             log.debug("no directml: %s", e)
   71 [blank     ] 
   72 [comment   ]     # 3) Оценка VRAM через wmic (Windows only) для AMD
   73 [branch    ]     if (
   74 [code      ]         out["gpu_kind"] in ("amd_or_intel", "unknown")
   75 [code      ]         and platform.system() == "Windows"
   76 [code      ]     ):
   77 [code      ]         vram = _wmic_vram_mb()
   78 [branch    ]         if vram > 0:
   79 [code      ]             out["vram_mb"] = vram
   80 [blank     ] 
   81 [comment   ]     # Рекомендации
   82 [branch    ]     if out["backend"] == "cpu":
   83 [code      ]         out["recommendations"].append(
   84 [code      ]             "GPU-ускорение недоступно. MusicGen/RVC будут работать медленно на CPU. "
   85 [code      ]             "Используйте лёгкие модели (musicgen-small, RVC 40k)."
   86 [code      ]         )
   87 [branch    ]     elif out["vram_mb"] and out["vram_mb"] < 6000:
   88 [code      ]         out["recommendations"].append(
   89 [code      ]             f"VRAM {out['vram_mb']} MB — включён режим экономии: batch=1, precision=fp16, "
   90 [code      ]             f"musicgen-small, RVC поэтапно."
   91 [code      ]         )
   92 [branch    ]     elif out["vram_mb"] and out["vram_mb"] >= 12000:
   93 [code      ]         out["recommendations"].append(
   94 [code      ]             f"VRAM {out['vram_mb']} MB — доступны тяжёлые режимы: musicgen-medium/large, "
   95 [code      ]             f"RVC v2 полный трейн, batch=4."
   96 [code      ]         )
   97 [blank     ] 
   98 [return    ]     return out
   99 [blank     ] 
  100 [blank     ] 
  101 [def       ] def _wmic_vram_mb() -> int:
  102 [try_block ]     try:
  103 [code      ]         r = subprocess.run(
  104 [code      ]             ["wmic", "path", "win32_VideoController", "get", "AdapterRAM"],
  105 [code      ]             capture_output=True,
  106 [code      ]             text=True,
  107 [code      ]             timeout=10,
  108 [code      ]         )
  109 [code      ]         max_bytes = 0
  110 [loop      ]         for line in r.stdout.splitlines():
  111 [code      ]             line = line.strip()
  112 [branch    ]             if line.isdigit():
  113 [code      ]                 max_bytes = max(max_bytes, int(line))
  114 [return    ]         return max_bytes // (1024 * 1024)
  115 [try_block ]     except Exception:
  116 [return    ]         return 0
  117 [blank     ] 
  118 [blank     ] 
  119 [def       ] def save_profile(out_json: str = "data/hw_profile_v10.json") -> dict[str, Any]:
  120 [code      ]     prof = detect()
  121 [code      ]     Path(out_json).parent.mkdir(parents=True, exist_ok=True)
  122 [stmt      ]     with open(out_json, "w", encoding="utf-8") as f:
  123 [code      ]         json.dump(prof, f, ensure_ascii=False, indent=2)
  124 [return    ]     return prof
  125 [blank     ] 
  126 [blank     ] 
  127 [def       ] def choose_musicgen_variant(profile: dict[str, Any] | None = None) -> str:
  128 [docstring ]     """
  129 [docstring ]     Возвращает 'small' / 'medium' / 'large' в зависимости от железа.
  130 [docstring ]     """
  131 [branch    ]     if profile is None:
  132 [code      ]         profile = detect()
  133 [code      ]     vram = profile.get("vram_mb", 0)
  134 [branch    ]     if profile.get("backend") == "cpu":
  135 [return    ]         return "small"
  136 [branch    ]     if vram >= 12000:
  137 [return    ]         return "large"
  138 [branch    ]     if vram >= 8000:
  139 [return    ]         return "medium"
  140 [return    ]     return "small"
  141 [blank     ] 
  142 [blank     ] 
  143 [branch    ] if __name__ == "__main__":
  144 [code      ]     p = save_profile()
  145 [code      ]     print(json.dumps(p, ensure_ascii=False, indent=2))
```