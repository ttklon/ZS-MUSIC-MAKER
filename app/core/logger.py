# -*- coding: utf-8 -*-
"""
app/core/logger.py — единственная реализация логирования.

Раньше их было две: `app/logger.py` (писал в `logs/app.log` относительно текущего
каталога) и этот модуль (писал в `output/logs`). На Windows при запуске из ярлыка
рабочий каталог — не папка программы, поэтому логи могли уходить куда угодно, а
падать приложение «молча». Теперь:

* каталог журналов вычисляется один раз (`log_dir()`):
  `%LOCALAPPDATA%\\ZS Music Maker\\logs` на Windows, `~/.local/share/zs-music-maker/logs`
  на Linux/macOS, переменная окружения `ZSMM_LOG_DIR` перекрывает оба варианта;
  если каталог недоступен для записи — откат в `<проект>/output/logs`;
* секреты вычищаются из каждой записи (`redact_secrets`);
* консоль на Windows не падает на emoji (`SafeStream`);
* `install_excepthook()` пишет крэш-репорт `crash_*.txt` рядом с журналом и не
  глотает исключение — оно по-прежнему уходит в stderr.
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, TextIO

from app.core.security_utils import redact_secrets

APP_DIR_NAME = "ZS Music Maker"
POSIX_DIR_NAME = "zs-music-maker"
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5


def _candidate_dirs() -> list[Path]:
    candidates: list[Path] = []
    override = os.environ.get("ZSMM_LOG_DIR")
    if override:
        candidates.append(Path(override).expanduser())
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            candidates.append(Path(base) / APP_DIR_NAME / "logs")
    else:
        xdg = os.environ.get("XDG_STATE_HOME")
        candidates.append((Path(xdg) if xdg else Path.home() / ".local" / "share") / POSIX_DIR_NAME / "logs")
    project_logs = Path(__file__).resolve().parents[2] / "output" / "logs"
    candidates.append(project_logs)
    candidates.append(Path(tempfile.gettempdir()) / POSIX_DIR_NAME / "logs")
    return candidates


def log_dir() -> Path:
    """Каталог журналов; первый, куда реально можно писать."""
    for candidate in _candidate_dirs():
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path(tempfile.gettempdir())


class _SecretRedactingFilter(logging.Filter):
    """Не даёт ключам и токенам попасть в файл журнала."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = redact_secrets(record.getMessage())
        except Exception:  # noqa: BLE001 - логирование не должно падать
            record.msg = str(record.msg)
        record.args = ()
        return True


class SafeStream:
    """Обёртка над stdout для консолей Windows (cp866/cp1251)."""

    def __init__(self, stream: TextIO | None = None):
        self.stream = stream or sys.stdout

    def write(self, message: str) -> int:
        try:
            return self.stream.write(message)
        except UnicodeEncodeError:
            encoding = getattr(self.stream, "encoding", None) or "cp866"
            return self.stream.write(message.encode(encoding, "replace").decode(encoding, "replace"))

    def flush(self) -> None:
        stream = self.stream
        if getattr(stream, "closed", False):
            return  # процесс завершается: буфер уже закрыт, шуметь не нужно
        try:
            stream.flush()
        except (AttributeError, OSError, ValueError) as error:
            # поток закрылся при выходе из процесса: писать некуда, но факт
            # не теряем — не в лог, так в stderr (logging может быть уже снят)
            print(f"[logger] flush failed: {error}", file=sys.stderr)


def setup_logger(
    name: str = "ZS_Music_Maker",
    log_file: str = "app.log",
    level: int = logging.INFO,
    console: bool = True,
) -> logging.Logger:
    """Настроить логгер с ротацией. Повторный вызов обработчики не дублирует."""
    directory = log_dir()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.handlers:
        return logger

    try:
        handler: logging.Handler = RotatingFileHandler(
            directory / log_file, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
    except OSError:  # нет прав на файл — остаётся хотя бы консоль
        handler = logging.StreamHandler(SafeStream())
    handler.setFormatter(formatter)
    handler.addFilter(_SecretRedactingFilter())
    logger.addHandler(handler)

    console_enabled = console and os.environ.get("ZSMM_SILENT_CONSOLE") != "1"
    if console_enabled:
        stream_handler = logging.StreamHandler(SafeStream())
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(_SecretRedactingFilter())
        logger.addHandler(stream_handler)
    return logger


def make_logger(name: str = "ZS_Music_Maker") -> logging.Logger:
    """Совместимый короткий конструктор: один логгер на процесс."""
    return setup_logger(name)


def write_crash_report(error: BaseException, *, context: str = "") -> Path:
    """Сохранить текстовый крэш-репорт; вернуть путь к нему."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = log_dir() / f"crash_{stamp}.txt"
    body = [
        f"time: {datetime.now().isoformat(timespec='seconds')}",
        f"platform: {sys.platform}",
        f"python: {sys.version}",
        f"context: {context}" if context else "context: -",
        "",
        "".join(traceback.format_exception(type(error), error, error.__traceback__)),
    ]
    try:
        path.write_text(redact_secrets("\n".join(body)), encoding="utf-8")
    except OSError:
        return Path()
    return path


def install_excepthook(logger: logging.Logger | None = None, context: str = "unhandled") -> None:
    """Крэш-репорт на непойманные исключения (в том числе в Qt-цикле)."""
    log = logger or app_logger
    previous = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            previous(exc_type, exc_value, exc_tb)
            return
        report = write_crash_report(exc_value, context=context)
        log.error("unhandled exception; crash report: %s", report, exc_info=(exc_type, exc_value, exc_tb))
        previous(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook


app_logger = setup_logger("ZS_Music_Maker")


class TerminalStageProgress:
    """Прогресс стадий для консоли: без управляющих кодов, чтобы логи читались."""

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
    """Единый формат логов стадий: `stage=/event=/duration_ms=`."""
    parts = [f"stage={stage}", f"event={event}"]
    if duration_ms is not None:
        try:
            parts.append(f"duration_ms={int(round(float(duration_ms)))}")
        except (TypeError, ValueError):
            parts.append(f"duration_ms={duration_ms}")
    for key, value in extra.items():
        parts.append(f"{key}={value}")
    logger.info(" ".join(parts))
