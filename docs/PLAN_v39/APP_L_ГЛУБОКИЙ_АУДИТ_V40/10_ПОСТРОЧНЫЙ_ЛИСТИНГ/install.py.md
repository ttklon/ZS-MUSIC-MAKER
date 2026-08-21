# ПОСТРОЧНЫЙ ЛИСТИНГ: `install.py`

**Всего строк:** 97

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 42 | 43.3 |
| blank | 11 | 11.3 |
| docstring | 10 | 10.3 |
| comment | 7 | 7.2 |
| import | 7 | 7.2 |
| try_block | 7 | 7.2 |
| branch | 7 | 7.2 |
| return | 3 | 3.1 |
| def | 2 | 2.1 |
| loop | 1 | 1.0 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — install.py (GOD MODE Refactored)
    4 [docstring ] ========================================================================
    5 [docstring ] Универсальный инсталлятор продукта.
    6 [docstring ] Автоматизирует настройку окружения, установку зависимостей и проверку GPU
    7 [docstring ] с надежным контролем ошибок и отчетностью.
    8 [docstring ] """
    9 [blank     ] 
   10 [import    ] import os
   11 [import    ] import sys
   12 [import    ] import subprocess
   13 [import    ] import platform
   14 [import    ] import shlex
   15 [blank     ] 
   16 [def       ] def run_cmd(cmd, critical=False):
   17 [docstring ]     """Выполнить команду. v33 FIX (P1, SESSION_LOG v32.5): убран shell=True —
   18 [docstring ]     риск injection + поломка на путях с пробелами. cmd может быть строкой
   19 [docstring ]     (разбивается shlex) или списком аргументов."""
   20 [code      ]     print(f"Executing: {cmd}")
   21 [try_block ]     try:
   22 [code      ]         args = shlex.split(cmd) if isinstance(cmd, str) else cmd
   23 [code      ]         subprocess.check_call(args)
   24 [return    ]         return True
   25 [try_block ]     except subprocess.CalledProcessError as e:
   26 [code      ]         print(f"[ERROR] Command failed with exit code {e.returncode}: {e}")
   27 [branch    ]         if critical:
   28 [code      ]             print("[CRITICAL] Critical dependency installation failed. Aborting.")
   29 [code      ]             sys.exit(1)
   30 [return    ]         return False
   31 [try_block ]     except Exception as e:
   32 [code      ]         print(f"[ERROR] Unexpected error executing command: {e}")
   33 [branch    ]         if critical:
   34 [code      ]             sys.exit(1)
   35 [return    ]         return False
   36 [blank     ] 
   37 [def       ] def setup():
   38 [code      ]     print("=== ZS Music Maker Installer (Singularity Refactored) ===")
   39 [code      ]     os_name = platform.system()
   40 [code      ]     print(f"Detected OS: {os_name}")
   41 [blank     ] 
   42 [comment   ]     # 1. Системные зависимости (на Linux)
   43 [branch    ]     if os_name == "Linux":
   44 [code      ]         run_cmd("sudo apt-get update && sudo apt-get install -y ffmpeg graphviz libsndfile1", critical=False)
   45 [blank     ] 
   46 [comment   ]     # 2. Основные Python зависимости
   47 [code      ]     req_file = "requirements.txt"
   48 [code      ]     print("Installing core Python dependencies...")
   49 [code      ]     success = run_cmd([sys.executable, "-m", "pip", "install", "-r", req_file], critical=True)
   50 [branch    ]     if not success:
   51 [code      ]         print("[CRITICAL] Failed to install core requirements.")
   52 [code      ]         sys.exit(1)
   53 [blank     ] 
   54 [comment   ]     # 3. Опциональные тяжелые зависимости (Torch / Audio ML)
   55 [code      ]     print("Checking/Installing optional heavy neural dependencies (torch, torchaudio)...")
   56 [code      ]     run_cmd([sys.executable, "-m", "pip", "install", "torch", "torchaudio",
   57 [code      ]              "--index-url", "https://download.pytorch.org/whl/cpu"], critical=False)
   58 [blank     ] 
   59 [comment   ]     # 4. Проверка GPU / Hardware
   60 [code      ]     print("Checking for hardware acceleration...")
   61 [try_block ]     try:
   62 [import    ]         import torch
   63 [branch    ]         if torch.cuda.is_available():
   64 [code      ]             print(f"CUDA Detected: {torch.cuda.get_device_name(0)}")
   65 [branch    ]         else:
   66 [code      ]             print("CUDA not found, using CPU / Optimized Fallback.")
   67 [try_block ]     except Exception:
   68 [code      ]         print("Torch CUDA check skipped (Torch not present).")
   69 [blank     ] 
   70 [comment   ]     # 5. Инициализация менеджера моделей
   71 [code      ]     print("Initializing Model Manager...")
   72 [try_block ]     try:
   73 [code      ]         sys.path.insert(0, os.path.abspath("."))
   74 [import    ]         from app.core.model_manager import models
   75 [code      ]         models.ensure_model("whisper_tiny")
   76 [code      ]         print("Base models verified successfully.")
   77 [try_block ]     except Exception as e:
   78 [code      ]         print(f"[WARNING] Model initialization notice: {e}")
   79 [blank     ] 
   80 [comment   ]     # 6. Создание необходимых директорий
   81 [code      ]     dirs = [
   82 [code      ]         "output/logs",
   83 [code      ]         "output/god_cli",
   84 [code      ]         "output/async_cli",
   85 [code      ]         "models",
   86 [code      ]         "samples_cache",
   87 [code      ]         "checkpoints"
   88 [code      ]     ]
   89 [loop      ]     for d in dirs:
   90 [code      ]         os.makedirs(d, exist_ok=True)
   91 [blank     ] 
   92 [code      ]     print("\n=== INSTALLATION & VERIFICATION COMPLETE ===")
   93 [code      ]     print("To start CLI God Mode, run: python main.py --god")
   94 [code      ]     print("To start Desktop GUI, run: python main.py --desktop")
   95 [blank     ] 
   96 [branch    ] if __name__ == "__main__":
   97 [code      ]     setup()
```