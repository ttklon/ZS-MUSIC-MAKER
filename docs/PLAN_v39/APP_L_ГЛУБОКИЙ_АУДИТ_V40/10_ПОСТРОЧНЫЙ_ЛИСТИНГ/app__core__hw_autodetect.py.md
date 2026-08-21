# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/hw_autodetect.py`

**Всего строк:** 212

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 109 | 51.4 |
| blank | 25 | 11.8 |
| try_block | 16 | 7.5 |
| branch | 15 | 7.1 |
| docstring | 14 | 6.6 |
| return | 11 | 5.2 |
| import | 10 | 4.7 |
| def | 5 | 2.4 |
| comment | 5 | 2.4 |
| loop | 2 | 0.9 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v8] hw_autodetect.py — единый детектор железа с чёткими режимами.
    3 [blank     ] 
    4 [docstring ] ТЗ 20.1 [ЖЕЛЕЗО]:
    5 [docstring ]   • Целевая платформа: 2× Xeon, 24 GB RAM, 12 GB VRAM, Windows 11 → mode="full"
    6 [docstring ]   • Fallback: RX 580 4GB / 16 GB RAM / 1× Xeon        → mode="lite"
    7 [blank     ] 
    8 [docstring ] Режимы:
    9 [docstring ]   full — MusicGen-large, RVC-full, XTTS клон, Bark-full, длинные окна.
   10 [docstring ]   mid  — MusicGen-medium, RVC-medium, Silero, средние окна (6-8 GB VRAM).
   11 [docstring ]   lite — MusicGen-small (CPU), RVC-lite (CPU/DirectML), Silero, короткие окна.
   12 [blank     ] 
   13 [docstring ] Возвращает dict, который используют Orchestrator, MusicGen, RVC, Voice Synth.
   14 [docstring ] """
   15 [blank     ] 
   16 [import    ] from __future__ import annotations
   17 [blank     ] 
   18 [import    ] import json
   19 [import    ] import os
   20 [import    ] import platform
   21 [import    ] import time
   22 [import    ] from pathlib import Path
   23 [blank     ] 
   24 [code      ] ROOT = Path(__file__).resolve().parents[2]
   25 [code      ] HW_CACHE = ROOT / "data" / "hw_profile.json"
   26 [code      ] HW_CACHE.parent.mkdir(parents=True, exist_ok=True)
   27 [blank     ] 
   28 [blank     ] 
   29 [def       ] def _cpu_info() -> dict:
   30 [code      ]     info = {
   31 [code      ]         "logical": os.cpu_count() or 1,
   32 [code      ]         "arch": platform.machine(),
   33 [code      ]         "system": platform.system(),
   34 [code      ]         "release": platform.release(),
   35 [code      ]     }
   36 [try_block ]     try:
   37 [import    ]         import psutil
   38 [blank     ] 
   39 [code      ]         info["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
   40 [try_block ]     except Exception:
   41 [code      ]         info["ram_gb"] = 0.0
   42 [return    ]     return info
   43 [blank     ] 
   44 [blank     ] 
   45 [def       ] def _gpu_info() -> dict:
   46 [docstring ]     """Определяем видеокарту и VRAM: CUDA → DirectML → ROCm → CPU."""
   47 [code      ]     g = {"kind": "cpu", "name": "CPU only", "vram_gb": 0.0, "ok": True}
   48 [comment   ]     # NVIDIA CUDA
   49 [try_block ]     try:
   50 [import    ]         import torch
   51 [blank     ] 
   52 [branch    ]         if torch.cuda.is_available():
   53 [code      ]             g["kind"] = "cuda"
   54 [code      ]             g["name"] = torch.cuda.get_device_name(0)
   55 [code      ]             g["vram_gb"] = round(
   56 [code      ]                 torch.cuda.get_device_properties(0).total_memory / (1024**3), 1
   57 [code      ]             )
   58 [return    ]             return g
   59 [try_block ]     except Exception:
   60 [code      ]         pass
   61 [comment   ]     # DirectML (AMD/Intel iGPU на Windows)
   62 [try_block ]     try:
   63 [import    ]         import torch_directml as dml
   64 [blank     ] 
   65 [code      ]         g["kind"] = "directml"
   66 [try_block ]         try:
   67 [code      ]             g["name"] = dml.device_name(0)
   68 [try_block ]         except Exception:
   69 [code      ]             g["name"] = "DirectML GPU"
   70 [comment   ]         # DirectML не даёт точный VRAM. Пробуем через WMIC на Windows.
   71 [try_block ]         try:
   72 [import    ]             import subprocess
   73 [blank     ] 
   74 [code      ]             out = subprocess.check_output(
   75 [code      ]                 [
   76 [code      ]                     "wmic",
   77 [code      ]                     "path",
   78 [code      ]                     "win32_VideoController",
   79 [code      ]                     "get",
   80 [code      ]                     "AdapterRAM,Name",
   81 [code      ]                     "/format:csv",
   82 [code      ]                 ],
   83 [code      ]                 timeout=5,
   84 [code      ]                 stderr=subprocess.DEVNULL,
   85 [code      ]             ).decode(errors="ignore")
   86 [loop      ]             for line in out.splitlines():
   87 [code      ]                 parts = [p.strip() for p in line.split(",") if p.strip()]
   88 [branch    ]                 if len(parts) >= 3 and parts[-1].isdigit():
   89 [code      ]                     v = int(parts[-1]) / (1024**3)
   90 [branch    ]                     if v > g["vram_gb"]:
   91 [code      ]                         g["vram_gb"] = round(v, 1)
   92 [code      ]                         g["name"] = parts[-2]
   93 [try_block ]         except Exception:
   94 [code      ]             g["vram_gb"] = 4.0  # осторожная оценка для RX 580
   95 [return    ]         return g
   96 [try_block ]     except Exception:
   97 [code      ]         pass
   98 [comment   ]     # ROCm (Linux)
   99 [try_block ]     try:
  100 [branch    ]         if os.path.exists("/opt/rocm"):
  101 [code      ]             g["kind"] = "rocm"
  102 [code      ]             g["name"] = "AMD ROCm GPU"
  103 [code      ]             g["vram_gb"] = 8.0
  104 [return    ]             return g
  105 [try_block ]     except Exception:
  106 [code      ]         pass
  107 [return    ]     return g
  108 [blank     ] 
  109 [blank     ] 
  110 [def       ] def detect(force: bool = False) -> dict:
  111 [docstring ]     """Полное определение. Кэш в data/hw_profile.json (24 часа)."""
  112 [branch    ]     if not force and HW_CACHE.exists():
  113 [try_block ]         try:
  114 [code      ]             cached = json.loads(HW_CACHE.read_text(encoding="utf-8"))
  115 [branch    ]             if time.time() - cached.get("ts", 0) < 86400:
  116 [return    ]                 return cached
  117 [try_block ]         except Exception:
  118 [code      ]             pass
  119 [blank     ] 
  120 [code      ]     cpu = _cpu_info()
  121 [code      ]     gpu = _gpu_info()
  122 [code      ]     ram = cpu.get("ram_gb", 0.0)
  123 [code      ]     vram = gpu.get("vram_gb", 0.0)
  124 [blank     ] 
  125 [comment   ]     # Определяем режим
  126 [branch    ]     if gpu["kind"] == "cuda" and vram >= 10 and ram >= 20:
  127 [code      ]         mode = "full"
  128 [code      ]         reason = "CUDA 10+ GB VRAM, 20+ GB RAM"
  129 [branch    ]     elif vram >= 10 and ram >= 20:
  130 [code      ]         mode = "full"
  131 [code      ]         reason = "10+ GB VRAM (не-CUDA) + 20+ GB RAM"
  132 [branch    ]     elif vram >= 6 and ram >= 16:
  133 [code      ]         mode = "mid"
  134 [code      ]         reason = "6-10 GB VRAM"
  135 [branch    ]     elif vram >= 3 and ram >= 12:
  136 [code      ]         mode = "lite"
  137 [code      ]         reason = "3-6 GB VRAM (RX 580 fallback)"
  138 [branch    ]     else:
  139 [code      ]         mode = "lite"
  140 [code      ]         reason = "CPU only / малый VRAM"
  141 [blank     ] 
  142 [code      ]     profile = {
  143 [code      ]         "cpu": cpu,
  144 [code      ]         "gpu": gpu,
  145 [code      ]         "mode": mode,
  146 [code      ]         "reason": reason,
  147 [code      ]         "ts": time.time(),
  148 [code      ]         "recommendations": _recommendations(mode, vram, ram, gpu["kind"]),
  149 [code      ]     }
  150 [try_block ]     try:
  151 [code      ]         HW_CACHE.write_text(
  152 [code      ]             json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
  153 [code      ]         )
  154 [try_block ]     except Exception:
  155 [code      ]         pass
  156 [return    ]     return profile
  157 [blank     ] 
  158 [blank     ] 
  159 [def       ] def _recommendations(mode: str, vram: float, ram: float, gpu_kind: str) -> dict:
  160 [branch    ]     if mode == "full":
  161 [return    ]         return {
  162 [code      ]             "musicgen": "large (12 GB VRAM)",
  163 [code      ]             "rvc": "full retraining + inference",
  164 [code      ]             "voice_synth": "Bark-full + XTTS + Silero",
  165 [code      ]             "windows_len_sec": 30,
  166 [code      ]             "queue_parallelism": 2,
  167 [code      ]             "quality_mode": "quality",
  168 [code      ]         }
  169 [branch    ]     if mode == "mid":
  170 [return    ]         return {
  171 [code      ]             "musicgen": "medium (6-8 GB VRAM)",
  172 [code      ]             "rvc": "inference + light training",
  173 [code      ]             "voice_synth": "Silero + Bark-small",
  174 [code      ]             "windows_len_sec": 15,
  175 [code      ]             "queue_parallelism": 1,
  176 [code      ]             "quality_mode": "quality",
  177 [code      ]         }
  178 [return    ]     return {
  179 [code      ]         "musicgen": "small (CPU) + опционально MusicGen-melody-only",
  180 [code      ]         "rvc": (
  181 [code      ]             "inference обязательно, training в ночном режиме " "≤3 часа"
  182 [branch    ]             if gpu_kind != "cpu"
  183 [code      ]             else "только inference, training только ночью на CPU"
  184 [code      ]         ),
  185 [code      ]         "voice_synth": "Silero v4 (CPU)",
  186 [code      ]         "windows_len_sec": 8,
  187 [code      ]         "queue_parallelism": 1,
  188 [code      ]         "quality_mode": "quality",  # даже на lite — качество приоритет
  189 [code      ]     }
  190 [blank     ] 
  191 [blank     ] 
  192 [def       ] def human_summary(profile: dict) -> str:
  193 [docstring ]     """Красивый текст для GUI."""
  194 [code      ]     cpu = profile["cpu"]
  195 [code      ]     gpu = profile["gpu"]
  196 [code      ]     lines = [
  197 [code      ]         f"🖥  Режим: {profile['mode'].upper()}  ({profile['reason']})",
  198 [code      ]         f"CPU: {cpu.get('logical', '?')} потоков · RAM: {cpu.get('ram_gb', 0)} GB",
  199 [code      ]         f"GPU: {gpu.get('name', '?')} ({gpu.get('kind')}, {gpu.get('vram_gb', 0)} GB VRAM)",
  200 [code      ]         "",
  201 [code      ]         "Рекомендуемая конфигурация:",
  202 [code      ]     ]
  203 [loop      ]     for k, v in profile.get("recommendations", {}).items():
  204 [code      ]         lines.append(f"  • {k}: {v}")
  205 [return    ]     return "\n".join(lines)
  206 [blank     ] 
  207 [blank     ] 
  208 [branch    ] if __name__ == "__main__":
  209 [code      ]     p = detect(force=True)
  210 [code      ]     print(json.dumps(p, ensure_ascii=False, indent=2))
  211 [code      ]     print()
  212 [code      ]     print(human_summary(p))
```