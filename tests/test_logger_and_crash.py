# -*- coding: utf-8 -*-
"""Один логгер, журнал в пользовательском каталоге, крэш-репорт без утечек.

Раньше логирование было реализовано дважды (`app/logger.py` и
`app/core/logger.py`), а каталог журналов зависел от текущей папки процесса: при
запуске из ярлыка на Windows лог писался «куда получится», а падение приложения
не оставляло следов вовсе.
"""

from __future__ import annotations

import logging
import sys

import pytest

from app.core import logger as app_logger_module


def test_single_logger_implementation() -> None:
    """Старый дубль `app/logger.py` удалён — осталась одна реализация."""
    root = __import__("pathlib").Path(__file__).resolve().parents[1]
    assert not (root / "app" / "logger.py").exists()


def test_log_dir_honours_environment_override(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZSMM_LOG_DIR", str(tmp_path / "logs"))
    assert app_logger_module.log_dir() == tmp_path / "logs"
    assert (tmp_path / "logs").is_dir()


def test_setup_logger_writes_rotating_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZSMM_LOG_DIR", str(tmp_path))
    logger = app_logger_module.setup_logger("zsmm-test-file")
    logger.info("stage=beat event=done")
    log_file = tmp_path / "app.log"
    assert log_file.exists()
    assert "stage=beat" in log_file.read_text(encoding="utf-8")


def test_logger_does_not_duplicate_handlers(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZSMM_LOG_DIR", str(tmp_path))
    first = app_logger_module.setup_logger("zsmm-test-once")
    handlers = len(first.handlers)
    second = app_logger_module.setup_logger("zsmm-test-once")
    assert second is first
    assert len(second.handlers) == handlers


def test_secrets_are_redacted_in_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZSMM_LOG_DIR", str(tmp_path))
    logger = app_logger_module.setup_logger("zsmm-test-secret")
    logger.info("api_key=sk-1234567890abcdef token=deadbeef")
    text = (tmp_path / "app.log").read_text(encoding="utf-8")
    assert "sk-1234567890abcdef" not in text


def test_crash_report_contains_traceback(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZSMM_LOG_DIR", str(tmp_path))
    try:
        raise ValueError("проверка крэш-репорта")
    except ValueError as error:
        report = app_logger_module.write_crash_report(error, context="unit-test")
    assert report.exists()
    body = report.read_text(encoding="utf-8")
    assert "ValueError" in body
    assert "unit-test" in body
    assert str(sys.platform) in body


def test_excepthook_writes_report_and_keeps_original(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZSMM_LOG_DIR", str(tmp_path))
    original = sys.excepthook
    called: list[str] = []

    def fake_hook(exc_type, exc_value, exc_tb):
        called.append(exc_type.__name__)

    sys.excepthook = fake_hook
    try:
        app_logger_module.install_excepthook(
            app_logger_module.setup_logger("zsmm-test-hook"), context="hook-test"
        )
        try:
            raise RuntimeError("hook-boom")
        except RuntimeError as error:
            sys.excepthook(RuntimeError, error, error.__traceback__)
    finally:
        installed = sys.excepthook
        sys.excepthook = original

    reports = list(tmp_path.glob("crash_*.txt"))
    assert reports, "крэш-репорт не создан"
    assert "hook-boom" in reports[0].read_text(encoding="utf-8")
    assert called == ["RuntimeError"], "исходный обработчик должен быть вызван"
    assert installed is not fake_hook


def test_console_can_be_silenced(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZSMM_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("ZSMM_SILENT_CONSOLE", "1")
    logger = app_logger_module.setup_logger("zsmm-test-silent")
    handlers = [type(handler) for handler in logger.handlers]
    assert all(handler is not logging.StreamHandler for handler in handlers)


def test_safe_stream_survives_narrow_encoding() -> None:
    class Narrow:
        encoding = "cp866"

        def __init__(self) -> None:
            self.chunks: list[str] = []

        def write(self, message):
            message.encode("cp866")  # как настоящая консоль: emoji не пройдёт
            self.chunks.append(message)
            return len(message)

        def flush(self) -> None:
            pass

    stream = app_logger_module.SafeStream(Narrow())
    stream.write("🎤 запись")  # не должно бросить UnicodeEncodeError


def test_default_log_file_name_is_stable() -> None:
    """Имя файла журнала — часть контракта: по нему ищут логи в поддержке."""
    import inspect

    default = inspect.signature(app_logger_module.setup_logger).parameters["log_file"].default
    assert default == "app.log"
