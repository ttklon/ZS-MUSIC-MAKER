# -*- coding: utf-8 -*-
"""
ZS Music Maker — logger.py (GOD MODE)
========================================================================
Централизованная система логирования.
Устраняет проблему "Silent Failures" (B110).
"""

import logging
import os
from pathlib import Path

def setup_logger(name: str, log_file: str = "app.log", level=logging.INFO):
    """Настраивает профессиональный логгер с выводом в консоль и файл."""
    log_dir = Path(__file__).resolve().parents[2] / "output" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Обработчик для файла
    file_handler = logging.FileHandler(log_dir / log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Глобальный логгер по умолчанию
app_logger = setup_logger("ZS_Music_Maker")
