# -*- coding: utf-8 -*-
"""
ZS Music Maker — logger.py (GOD MODE)
========================================================================
Централизованная система логирования.
Устраняет проблему "Silent Failures" (B110).
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any, TextIO

from app.core.security_utils import redact_secrets


class _SecretRedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_secrets(record.getMessage())
        record.args = ()
        return True


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
    file_handler.addFilter(_SecretRedactingFilter())

    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(_SecretRedactingFilter())

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Глобальный логгер по умолчанию
app_logger = setup_logger("ZS_Music_Maker")


class TerminalStageProgress:
    """Small terminal-only progress renderer for real sequential AI stage events.

    It intentionally prints newline-delimited updates instead of terminal control
    codes so CI logs, redirected stdout and Windows consoles preserve every
    completed stage. All values come from runner callbacks; it never estimates
    a successful model run.
    """

    def __init__(self, total_stages: int, stream: TextIO | None = None):
        self.total_stages = max(1, int(total_stages))
        self.stream = stream or sys.stdout

    def _bar(self, completed: int) -> str:
        width = 12
        filled = min(width, round(width * max(0, completed) / self.total_stages))
        return "[" + "#" * filled + "-" * (width - filled) + "]"

    def stage_start(self, index: int, stage_name: str, vram_gb: float) -> None:
        print(
            f"[AI] {self._bar(index - 1)} {index}/{self.total_stages} "
            f"START {stage_name} | VRAM {float(vram_gb):.3f} GB",
            file=self.stream,
            flush=True,
        )

    def stage_finish(self, index: int, report: Any) -> None:
        if not bool(getattr(report, "ok", False)):
            status = "FAILED"
        elif "fallback" in str(getattr(report, "skipped_reason", "")).lower():
            status = "FALLBACK"
        elif getattr(report, "skipped_reason", None) or "skipped" in str(
            getattr(report, "output_summary", "")
        ).lower():
            status = "SKIPPED"
        else:
            status = "OK"
        print(
            f"[AI] {self._bar(index)} {index}/{self.total_stages} {status} "
            f"{getattr(report, 'name', 'stage')} | {float(getattr(report, 'duration_sec', 0.0)):.2f}s "
            f"| VRAM {float(getattr(report, 'vram_before_gb', 0.0)):.3f}"
            f"->{float(getattr(report, 'vram_after_gb', 0.0)):.3f} GB",
            file=self.stream,
            flush=True,
        )


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
