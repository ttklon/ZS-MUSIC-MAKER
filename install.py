# -*- coding: utf-8 -*-
"""
ZS Music Maker — install.py (GOD MODE)
========================================================================
Универсальный инсталлятор продукта.
Автоматизирует настройку окружения, установку зависимостей и проверку GPU.
"""

import os
import sys
import subprocess
import platform

def run_cmd(cmd):
    print(f"Executing: {cmd}")
    try:
        subprocess.check_call(cmd, shell=True)
        return True
    except Exception as e:
        print(f"Error executing command: {e}")
        return False

def setup():
    print("=== ZS Music Maker Installer (Singularity) ===")
    os_name = platform.system()
    print(f"Detected OS: {os_name}")

    # 1. Зависимости
    if os_name == "Linux":
        print("Installing system libraries (Linux)...")
        run_cmd("sudo apt-get update && sudo apt-get install -y ffmpeg graphviz libsndfile1")
    
    print("Installing Python dependencies...")
    deps = [
        "numpy", "scipy", "soundfile", "pedalboard", 
        "audiomentations", "pyloudnorm", "essentia", 
        "music21", "pyAudioAnalysis", "mingus", 
        "pytest", "radon", "bandit", "requests", 
        "tqdm", "colorama", "psutil"
    ]
    run_cmd(f"{sys.executable} -m pip install {' '.join(deps)}")

    # 2. Проверка GPU
    print("Checking for hardware acceleration...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"CUDA Detected: {torch.cuda.get_device_name(0)}")
        else:
            print("CUDA not found, using CPU.")
    except:
        print("Torch not installed yet.")

    # 3. Базовые модели
    print("Initializing Model Manager...")
    try:
        sys.path.insert(0, os.path.abspath("."))
        from app.core.model_manager import models
        # Предзагрузка базовой модели для проверки
        models.ensure_model("whisper_tiny")
        print("Base models verified.")
    except Exception as e:
        print(f"Model initialization failed: {e}")

    # 4. Директории
    for d in ["output/logs", "output/god_cli", "models", "samples_cache"]:
        os.makedirs(d, exist_ok=True)

    print("\n=== INSTALLATION COMPLETE ===")
    print("To start, run: python main.py --god")

if __name__ == "__main__":
    setup()
