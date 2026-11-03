# -*- coding: utf-8 -*-
"""
app/gui/wizard/dialogs.py — диагностический диалог «AI: модели и пайплайн».

Статус — предварительная проверка пакетов и некоторых весов, не inference.
Аппаратный профиль измеряется отдельно и не гарантирует совместимость моделей.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.core.i18n import t
from app.gui.wizard.ui import DIM, H2

LOGGER = logging.getLogger(__name__)

REFRESH_MS = 5000


class AIStatusDialog(QDialog):
    """Список ролей с их реальной доступностью и кнопкой обновления."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("dialog.ai_title"))
        self.resize(760, 520)
        layout = QVBoxLayout(self)
        layout.addWidget(H2(t("dialog.ai_title")))
        layout.addWidget(DIM(t("dialog.ai_hint")))

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text, 1)

        row = QHBoxLayout()
        refresh = QPushButton(t("dialog.refresh"))
        refresh.clicked.connect(self.refresh)
        close = QPushButton("OK")
        close.clicked.connect(self.accept)
        row.addWidget(refresh)
        row.addStretch()
        row.addWidget(close)
        layout.addLayout(row)

        from app.core.hw_autodetect import detect, human_summary
        self.hardware_summary = human_summary(detect())
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(REFRESH_MS)
        self.refresh()

    def refresh(self) -> None:
        try:
            from app.ai.registry import MODEL_REGISTRY, registry

            runtime = registry.status()
            budget = runtime["budget"]
            lines = [
                self.hardware_summary,
                "Проверка пакетов/некоторых весов, не запуск модели:",
                f"VRAM budget: {budget['vram_gb']:.1f} GB | RAM: {budget['ram_gb']:.1f} GB "
                f"| current: {runtime['current'] or 'none'}",
                "",
            ]
            for key, spec in MODEL_REGISTRY.items():
                marker = "PREFLIGHT" if registry.is_available(key) else "MISSING / UNAVAILABLE"
                vram = float(spec.get("vram_est_gb", 0))
                lines.append(
                    f"[{marker}] {key} — {spec['role']} "
                    f"({spec['engine']}; ~{vram:.1f} GB VRAM)"
                )
            self.text.setPlainText("\n".join(lines))
        except Exception as error:  # noqa: BLE001 - диалог не должен падать
            LOGGER.warning("AI status unavailable: %s", error)
            self.text.setPlainText(f"{t('dialog.error')}: {type(error).__name__}: {error}")
