# -*- coding: utf-8 -*-
"""
app/gui/wizard/record_dialog.py — окно записи голоса.

Запись идёт через `ui.karaoke_recorder.record_with_backing`: необязательный бит в
наушниках, выбранный стиль (8 стилей из Voice Vault), сохранение в `voice_vault/`
и регистрация в индексе. Пишем в отдельном потоке, чтобы окно не замирало на
30 секундах записи.

Важно: это не «имитация записи». Если `sounddevice` не установлен или микрофона
нет — окно говорит об этом прямо и предлагает выбрать готовый файл.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.core.i18n import t
from app.gui.wizard.ui import DIM, H2

LOGGER = logging.getLogger(__name__)

DEFAULT_PHRASES = (
    "ночь горит, дрифт не спит",
    "money over everything",
    "я иду по мокрому асфальту",
    "город в огнях, я в тумане",
)


def available_styles() -> list[str]:
    """Стили записи из единственного источника — `modules.voice_convert.STYLES`."""
    try:
        from modules.voice_convert import STYLES

        return list(STYLES)
    except Exception:  # noqa: BLE001 - без модуля остаётся один нейтральный стиль
        LOGGER.warning("voice styles unavailable", exc_info=True)
        return ["conversational"]


class _Recorder(QThread):
    """Фоновая запись: UI-поток не должен ждать `sd.wait()`."""

    finished_ok = Signal(dict)
    failed = Signal(str)

    def __init__(self, duration_sec: int, style: str, text: str, backing: str = ""):
        super().__init__()
        self.duration_sec = duration_sec
        self.style = style
        self.text = text
        self.backing = backing

    def run(self) -> None:  # pragma: no cover - требует реального микрофона
        try:
            from ui.karaoke_recorder import record_with_backing

            result = record_with_backing(
                self.backing,
                duration_sec=self.duration_sec,
                style=self.style,
                text=self.text,
            )
            if result.get("ok") is not True or not result.get("path"):
                self.failed.emit(str(result.get("error") or "recording did not produce a file"))
            else:
                self.finished_ok.emit(result)
        except Exception as error:  # noqa: BLE001 - сообщаем в диалог, не в лог
            self.failed.emit(f"{type(error).__name__}: {error}")


class RecordDialog(QDialog):
    """Минимальный рекордер: стиль, длина, фраза, кнопка записи."""

    def __init__(self, parent=None, default_text: str = "", default_backing: str = "",
                 default_duration: int = 20):
        super().__init__(parent)
        self.setWindowTitle(t("wizard.voice.karaoke"))
        self.resize(620, 360)
        self.result_path: str | None = None
        self._thread: _Recorder | None = None
        self._pending_accept = False
        self._backing = default_backing

        layout = QVBoxLayout(self)
        layout.addWidget(DIM(t("wizard.voice.hint")))

        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Стиль"))
        self.style = QComboBox()
        self.style.addItems(available_styles())
        style_row.addWidget(self.style, 1)
        style_row.addWidget(QLabel("Секунд"))
        self.duration = QSpinBox()
        self.duration.setRange(5, 300)
        self.duration.setValue(max(5, min(300, default_duration)))
        style_row.addWidget(self.duration)
        layout.addLayout(style_row)

        backing_row = QHBoxLayout()
        self.backing_label = QLabel(self._backing or "Без минуса (можно выбрать свой бит)")
        self.backing_label.setWordWrap(True)
        choose_backing = QPushButton("Выбрать минус…")
        choose_backing.clicked.connect(self._choose_backing)
        clear_backing = QPushButton("✕")
        clear_backing.setToolTip(t("wizard.material.clear"))
        clear_backing.clicked.connect(self._clear_backing)
        backing_row.addWidget(self.backing_label, 1)
        backing_row.addWidget(choose_backing)
        backing_row.addWidget(clear_backing)
        layout.addLayout(backing_row)
        layout.addWidget(DIM("Используйте наушники: минус воспроизводится во время записи, но не записывается в вокальный файл."))

        layout.addWidget(H2("Что читаем"))
        self.phrase = QComboBox()
        self.phrase.setEditable(True)
        self.phrase.addItems(DEFAULT_PHRASES)
        if default_text:
            self.phrase.setCurrentText(default_text)
        layout.addWidget(self.phrase)

        buttons = QHBoxLayout()
        self.btn_record = QPushButton("● Записать")
        self.btn_record.clicked.connect(self.start_recording)
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.reject)
        buttons.addWidget(self.btn_record)
        buttons.addStretch()
        buttons.addWidget(self.btn_close)
        layout.addLayout(buttons)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color:#9a9aa4;")
        layout.addWidget(self.status)
        layout.addStretch()

    def _choose_backing(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать минус", "", "Audio (*.wav *.flac *.ogg)")
        if path:
            self._backing = path
            self.backing_label.setText(path)

    def _clear_backing(self) -> None:
        self._backing = ""
        self.backing_label.setText("Без минуса (можно выбрать свой бит)")

    def reject(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            self.status.setText("Дождитесь завершения записи перед закрытием окна.")
            return
        super().reject()

    def closeEvent(self, event) -> None:
        if self._thread is not None and self._thread.isRunning():
            self.status.setText("Дождитесь завершения записи перед закрытием окна.")
            event.ignore()
            return
        super().closeEvent(event)

    def start_recording(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            return
        self.btn_record.setEnabled(False)
        self.status.setText(f"Запись {self.duration.value()} с… (говори в микрофон)")
        self._thread = _Recorder(
            duration_sec=int(self.duration.value()),
            style=self.style.currentText(),
            text=self.phrase.currentText(),
            backing=self._backing,
        )
        self._thread.finished_ok.connect(self._on_recorded)
        self._thread.failed.connect(self._on_failed)
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.start()

    def _on_recorded(self, result: dict) -> None:
        self.result_path = result.get("path")
        self.status.setText(f"Готово: {self.result_path}")
        if result.get("warning"):
            QMessageBox.warning(self, t("wizard.voice.karaoke"), str(result["warning"]))
        self._pending_accept = True
        if self._thread is None or not self._thread.isRunning():
            self.accept()

    def _on_thread_finished(self) -> None:
        self.btn_record.setEnabled(True)
        if self._pending_accept:
            self.accept()

    def _on_failed(self, message: str) -> None:
        self.status.setText(f"{t('dialog.error')}: {message}")
        QMessageBox.warning(self, t("wizard.voice.karaoke"), message)
