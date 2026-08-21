# grep-таблицы `install.py`

## `import` — 7 совпадений
```
   10 | import os
   11 | import sys
   12 | import subprocess
   13 | import platform
   14 | import shlex
   62 |         import torch
   74 |         from app.core.model_manager import models
```

## `print` — 19 совпадений
```
   20 |     print(f"Executing: {cmd}")
   26 |         print(f"[ERROR] Command failed with exit code {e.returncode}: {e}")
   28 |             print("[CRITICAL] Critical dependency installation failed. Aborting.")
   32 |         print(f"[ERROR] Unexpected error executing command: {e}")
   38 |     print("=== ZS Music Maker Installer (Singularity Refactored) ===")
   40 |     print(f"Detected OS: {os_name}")
   48 |     print("Installing core Python dependencies...")
   51 |         print("[CRITICAL] Failed to install core requirements.")
   55 |     print("Checking/Installing optional heavy neural dependencies (torch, torchaudio)...")
   60 |     print("Checking for hardware acceleration...")
   64 |             print(f"CUDA Detected: {torch.cuda.get_device_name(0)}")
   66 |             print("CUDA not found, using CPU / Optimized Fallback.")
   68 |         print("Torch CUDA check skipped (Torch not present).")
   71 |     print("Initializing Model Manager...")
   76 |         print("Base models verified successfully.")
   78 |         print(f"[WARNING] Model initialization notice: {e}")
   92 |     print("\n=== INSTALLATION & VERIFICATION COMPLETE ===")
   93 |     print("To start CLI God Mode, run: python main.py --god")
   94 |     print("To start Desktop GUI, run: python main.py --desktop")
```

## `except` — 4 совпадений
```
   25 |     except subprocess.CalledProcessError as e:
   31 |     except Exception as e:
   67 |     except Exception:
   77 |     except Exception as e:
```

## `try` — 3 совпадений
```
   21 |     try:
   61 |     try:
   72 |     try:
```

## `def` — 2 совпадений
```
   16 | def run_cmd(cmd, critical=False):
   37 | def setup():
```

## `return` — 3 совпадений
```
   24 |         return True
   30 |         return False
   35 |         return False
```

## `if` — 6 совпадений
```
   27 |         if critical:
   33 |         if critical:
   43 |     if os_name == "Linux":
   50 |     if not success:
   63 |         if torch.cuda.is_available():
   96 | if __name__ == "__main__":
```

## `for` — 1 совпадений
```
   89 |     for d in dirs:
```

## `subprocess` — 2 совпадений
```
   23 |         subprocess.check_call(args)
   25 |     except subprocess.CalledProcessError as e:
```
