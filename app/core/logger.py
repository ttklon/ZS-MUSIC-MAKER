# -*- coding: utf-8 -*-
"""
ZS Music Maker — logger.py (GOD MODE)
========================================================================
Централизованная система логирования.
Устраняет проблему "Silent Failures" (B110).
"""

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_file: str = "app.log", level=logging.INFO):
    """Настраивает профессиональный логгер с ротацией файлов."""
    log_dir = Path(__file__).resolve().parents[2] / "output" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # v26: Ротация логов (макс 10MB, храним 5 файлов)
    file_handler = RotatingFileHandler(
        log_dir / log_file, 
        maxBytes=10*1024*1024, 
        backupCount=5, 
        encoding='utf-8'
    )
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


def log_stage(logger, stage: str, event: str = "start", duration_ms=None, **extra):
    """v39.4 (ШАГ 004): единый формат логов стадий — stage=/event=/duration_ms=."""
    parts = [f"stage={stage}", f"event={event}"]
    if duration_ms is not None:
        try:
            parts.append(f"duration_ms={int(round(float(duration_ms)))}")
        except (TypeError, ValueError):
            parts.append(f"duration_ms={duration_ms}")
    for k, v in extra.items():
        parts.append(f"{k}={v}")
    logger.info(" ".join(parts))
