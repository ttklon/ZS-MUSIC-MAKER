"""Responsive, cancellable preparation before a full rebuild is enqueued."""
from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog, QLabel, QMessageBox, QProgressBar, QPushButton, QVBoxLayout

from app.core.i18n import t
from app.core.input_prepare_task import InputPreparationTask


class InputPrepareDialog(QDialog):
    def __init__(self, replacements: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("wizard.inputs.preparing_title"))
        self.task = InputPreparationTask(replacements)
        self._cancel_requested = False
        layout = QVBoxLayout(self)
        label = QLabel(t("wizard.inputs.preparing"))
        label.setWordWrap(True)
        layout.addWidget(label)
        progress = QProgressBar()
        progress.setRange(0, 0)  # Indeterminate: no fabricated byte progress.
        layout.addWidget(progress)
        cancel = QPushButton(t("wizard.inputs.cancel"))
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(75)
        self.task.start()

    def _poll(self) -> None:
        if self._cancel_requested or not self.task.done.is_set():
            return
        self._timer.stop()
        if self.task.was_cancelled:
            super().reject()
        elif self.task.error is not None:
            QMessageBox.warning(self, t("dialog.error"), self.task.error)
            super().reject()
        else:
            super().accept()

    def reject(self) -> None:
        self._cancel_requested = True
        self.task.cancel()
        self._timer.stop()
        super().reject()

    def closeEvent(self, event) -> None:
        self._cancel_requested = True
        self.task.cancel()
        self._timer.stop()
        super().closeEvent(event)
