# -*- coding: utf-8 -*-
"""
ZS Music Maker — install.py (GOD MODE Refactored)
========================================================================
Универсальный инсталлятор продукта.
Автоматизирует настройку окружения, установку зависимостей и проверку GPU
с надежным контролем ошибок и отчетностью.
"""

import os
import sys
import subprocess
import platform

def run_cmd(cmd, critical=False):
    print(f"Executing: {cmd}")
    try:
        subprocess.check_call(cmd, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed with exit code {e.returncode}: {e}")
        if critical:
            print("[CRITICAL] Critical dependency installation failed. Aborting.")
            sys.exit(1)
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error executing command: {e}")
        if critical:
            sys.exit(1)
        return False

def setup():
    print("=== ZS Music Maker Installer (Singularity Refactored) ===")
    os_name = platform.system()
    print(f"Detected OS: {os_name}")

    # 1. Системные зависимости (на Linux)
    if os_name == "Linux":
        run_cmd("sudo apt-get update && sudo apt-get install -y ffmpeg graphviz libsndfile1", critical=False)

    # 2. Основные Python зависимости
    req_file = "requirements.txt"
    print("Installing core Python dependencies...")
    success = run_cmd(f"{sys.executable} -m pip install -r {req_file}", critical=True)
    if not success:
        print("[CRITICAL] Failed to install core requirements.")
        sys.exit(1)

    # 3. Опциональные тяжелые зависимости (Torch / Audio ML)
    print("Checking/Installing optional heavy neural dependencies (torch, torchaudio)...")
    run_cmd(f"{sys.executable} -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu", critical=False)

    # 4. Проверка GPU / Hardware
    print("Checking for hardware acceleration...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"CUDA Detected: {torch.cuda.get_device_name(0)}")
        else:
            print("CUDA not found, using CPU / Optimized Fallback.")
    except Exception:
        print("Torch CUDA check skipped (Torch not present).")

    # 5. Инициализация менеджера моделей
    print("Initializing Model Manager...")
    try:
        sys.path.insert(0, os.path.abspath("."))
        from app.core.model_manager import models
        models.ensure_model("whisper_tiny")
        print("Base models verified successfully.")
    except Exception as e:
        print(f"[WARNING] Model initialization notice: {e}")

    # 6. Создание необходимых директорий
    dirs = [
        "output/logs",
        "output/god_cli",
        "output/async_cli",
        "models",
        "samples_cache",
        "checkpoints"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    print("\n=== INSTALLATION & VERIFICATION COMPLETE ===")
    print("To start CLI God Mode, run: python main.py --god")
    print("To start Desktop GUI, run: python main.py --desktop")

if __name__ == "__main__":
    setup()
