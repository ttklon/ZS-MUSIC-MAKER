# АУДИТ ФАЙЛА: `install.py`

**LOC:** 97  |  **Размер:** 3801 байт  |  **Проблем:** 20  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 10 | `os` | import |
| 11 | `sys` | import |
| 12 | `subprocess` | import |
| 13 | `platform` | import |
| 14 | `shlex` | import |
| 62 | `torch` | import |
| 74 | `app.core.model_manager.models` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 16 | `run_cmd` | 19 | 3 | ✅ |
| 37 | `setup` | 57 | 6 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 19 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 20** — print() вместо logger

  ```
         18 |     риск injection + поломка на путях с пробелами. cmd может быть строкой
         19 |     (разбивается shlex) или списком аргументов."""
  >>>    20 |     print(f"Executing: {cmd}")
         21 |     try:
         22 |         args = shlex.split(cmd) if isinstance(cmd, str) else cmd
  ```

- **строка 26** — print() вместо logger

  ```
         24 |         return True
         25 |     except subprocess.CalledProcessError as e:
  >>>    26 |         print(f"[ERROR] Command failed with exit code {e.returncode}: {e}")
         27 |         if critical:
         28 |             print("[CRITICAL] Critical dependency installation failed. Aborting.")
  ```

- **строка 28** — print() вместо logger

  ```
         26 |         print(f"[ERROR] Command failed with exit code {e.returncode}: {e}")
         27 |         if critical:
  >>>    28 |             print("[CRITICAL] Critical dependency installation failed. Aborting.")
         29 |             sys.exit(1)
         30 |         return False
  ```

- **строка 32** — print() вместо logger

  ```
         30 |         return False
         31 |     except Exception as e:
  >>>    32 |         print(f"[ERROR] Unexpected error executing command: {e}")
         33 |         if critical:
         34 |             sys.exit(1)
  ```

- **строка 38** — print() вместо logger

  ```
         36 | 
         37 | def setup():
  >>>    38 |     print("=== ZS Music Maker Installer (Singularity Refactored) ===")
         39 |     os_name = platform.system()
         40 |     print(f"Detected OS: {os_name}")
  ```

- **строка 40** — print() вместо logger

  ```
         38 |     print("=== ZS Music Maker Installer (Singularity Refactored) ===")
         39 |     os_name = platform.system()
  >>>    40 |     print(f"Detected OS: {os_name}")
         41 | 
         42 |     # 1. Системные зависимости (на Linux)
  ```

- **строка 48** — print() вместо logger

  ```
         46 |     # 2. Основные Python зависимости
         47 |     req_file = "requirements.txt"
  >>>    48 |     print("Installing core Python dependencies...")
         49 |     success = run_cmd([sys.executable, "-m", "pip", "install", "-r", req_file], critical=True)
         50 |     if not success:
  ```

- **строка 51** — print() вместо logger

  ```
         49 |     success = run_cmd([sys.executable, "-m", "pip", "install", "-r", req_file], critical=True)
         50 |     if not success:
  >>>    51 |         print("[CRITICAL] Failed to install core requirements.")
         52 |         sys.exit(1)
         53 | 
  ```

- **строка 55** — print() вместо logger

  ```
         53 | 
         54 |     # 3. Опциональные тяжелые зависимости (Torch / Audio ML)
  >>>    55 |     print("Checking/Installing optional heavy neural dependencies (torch, torchaudio)...")
         56 |     run_cmd([sys.executable, "-m", "pip", "install", "torch", "torchaudio",
         57 |              "--index-url", "https://download.pytorch.org/whl/cpu"], critical=False)
  ```

- **строка 60** — print() вместо logger

  ```
         58 | 
         59 |     # 4. Проверка GPU / Hardware
  >>>    60 |     print("Checking for hardware acceleration...")
         61 |     try:
         62 |         import torch
  ```

- **строка 64** — print() вместо logger

  ```
         62 |         import torch
         63 |         if torch.cuda.is_available():
  >>>    64 |             print(f"CUDA Detected: {torch.cuda.get_device_name(0)}")
         65 |         else:
         66 |             print("CUDA not found, using CPU / Optimized Fallback.")
  ```

- **строка 66** — print() вместо logger

  ```
         64 |             print(f"CUDA Detected: {torch.cuda.get_device_name(0)}")
         65 |         else:
  >>>    66 |             print("CUDA not found, using CPU / Optimized Fallback.")
         67 |     except Exception:
         68 |         print("Torch CUDA check skipped (Torch not present).")
  ```

- **строка 68** — print() вместо logger

  ```
         66 |             print("CUDA not found, using CPU / Optimized Fallback.")
         67 |     except Exception:
  >>>    68 |         print("Torch CUDA check skipped (Torch not present).")
         69 | 
         70 |     # 5. Инициализация менеджера моделей
  ```

- **строка 71** — print() вместо logger

  ```
         69 | 
         70 |     # 5. Инициализация менеджера моделей
  >>>    71 |     print("Initializing Model Manager...")
         72 |     try:
         73 |         sys.path.insert(0, os.path.abspath("."))
  ```

- **строка 76** — print() вместо logger

  ```
         74 |         from app.core.model_manager import models
         75 |         models.ensure_model("whisper_tiny")
  >>>    76 |         print("Base models verified successfully.")
         77 |     except Exception as e:
         78 |         print(f"[WARNING] Model initialization notice: {e}")
  ```

- **строка 78** — print() вместо logger

  ```
         76 |         print("Base models verified successfully.")
         77 |     except Exception as e:
  >>>    78 |         print(f"[WARNING] Model initialization notice: {e}")
         79 | 
         80 |     # 6. Создание необходимых директорий
  ```

- **строка 92** — print() вместо logger

  ```
         90 |         os.makedirs(d, exist_ok=True)
         91 | 
  >>>    92 |     print("\n=== INSTALLATION & VERIFICATION COMPLETE ===")
         93 |     print("To start CLI God Mode, run: python main.py --god")
         94 |     print("To start Desktop GUI, run: python main.py --desktop")
  ```

- **строка 93** — print() вместо logger

  ```
         91 | 
         92 |     print("\n=== INSTALLATION & VERIFICATION COMPLETE ===")
  >>>    93 |     print("To start CLI God Mode, run: python main.py --god")
         94 |     print("To start Desktop GUI, run: python main.py --desktop")
         95 | 
  ```

- **строка 94** — print() вместо logger

  ```
         92 |     print("\n=== INSTALLATION & VERIFICATION COMPLETE ===")
         93 |     print("To start CLI God Mode, run: python main.py --god")
  >>>    94 |     print("To start Desktop GUI, run: python main.py --desktop")
         95 | 
         96 | if __name__ == "__main__":
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 37** — public function 'setup' без docstring

  ```
         35 |         return False
         36 | 
  >>>    37 | def setup():
         38 |     print("=== ZS Music Maker Installer (Singularity Refactored) ===")
         39 |     os_name = platform.system()
  ```
