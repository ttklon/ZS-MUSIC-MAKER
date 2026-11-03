# -*- coding: utf-8 -*-
"""
app/gui/wizard/steps_material.py — шаг 2: референсы, пресет, режим, свои строчки.

Референсы — это измерение (BPM, ритм, вайб), а не копирование: программа ничего
не сэмплирует из чужих треков. Если референсов нет, работает пресет. Свои строчки
попадают в текст гарантированно — это проверяется стадией лирики, а не «на веру».
"""

from __future__ import annotations

import logging

from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSpinBox,
    QTextEdit,
)

from app.core.i18n import t
from app.gui.wizard.ui import DIM, H1, H2, HR, StepBase

LOGGER = logging.getLogger(__name__)

AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")

# ключ пресета — None означает «из референсов»
PRESETS: tuple[tuple[str, str | None], ...] = (
    ("tamam_like — восточный фонк-эдит", "tamam_like"),
    ("brazilian_phonk — агрессия, drift", "brazilian_phonk"),
    ("hyperpop_edit — TikTok-хайп", "hyperpop_edit"),
    ("lofi_drift — вечерний драйв", "lofi_drift"),
    ("trap_ru — русский трэп", "trap_ru"),
)

QUALITY_MODES = ("fast", "quality", "max")


class StepMaterial(StepBase):
    """Референсы + пресет + режим генерации + свои строчки."""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1(t("wizard.material.title")))
        self.root.addWidget(DIM(t("wizard.material.hint")))

        self.list = QListWidget()
        self.list.setAcceptDrops(True)
        self.list.setDragDropMode(QListWidget.InternalMove)
        self.list.setMinimumHeight(140)
        self.root.addWidget(self.list)

        buttons = QHBoxLayout()
        add = QPushButton(t("wizard.material.add"))
        add.clicked.connect(self.pick_files)
        clear = QPushButton(t("wizard.material.clear"))
        clear.clicked.connect(self.list.clear)
        buttons.addWidget(add)
        buttons.addWidget(clear)
        buttons.addStretch()
        buttons.addWidget(QLabel("↑↓"))
        self.root.addLayout(buttons)

        self.root.addWidget(HR())
        self.root.addWidget(H2(t("wizard.material.preset")))
        self.preset = QComboBox()
        self.preset.addItem(t("wizard.material.preset_auto"))
        for label, _key in PRESETS:
            self.preset.addItem(label)
        self.root.addWidget(self.preset)

        self.root.addWidget(H2(t("wizard.material.mode")))
        self.root.addWidget(DIM(t("wizard.material.mode_hint")))
        self.mode = QComboBox()
        self.mode.addItems(
            ["Быстрый (10–15 мин)", "Качественный (30–60 мин)", "Максимальный (1–3 ч)"]
        )
        self.mode.setCurrentIndex(1)
        self.root.addWidget(self.mode)

        self.root.addWidget(HR())
        self.root.addWidget(H2(t("wizard.material.lyrics")))
        self.lyrics = QTextEdit()
        self.lyrics.setPlaceholderText(t("wizard.material.lyrics_placeholder"))
        self.lyrics.setMinimumHeight(110)
        self.root.addWidget(self.lyrics)

        row = QHBoxLayout()
        self.bilingual = QCheckBox(t("wizard.material.bilingual"))
        self.bilingual.setChecked(True)
        row.addWidget(self.bilingual)
        row.addStretch()
        row.addWidget(QLabel(t("wizard.material.verses")))
        self.verses = QSpinBox()
        self.verses.setRange(1, 4)
        self.verses.setValue(2)
        row.addWidget(self.verses)
        self.root.addLayout(row)
        self.setAcceptDrops(True)

    # --- drag & drop -------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 - Qt API
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 - Qt API
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and path.lower().endswith(AUDIO_SUFFIXES):
                self.list.addItem(path)

    def pick_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            t("wizard.material.add"),
            "",
            "Audio (*.mp3 *.wav *.flac *.m4a *.ogg)",
        )
        for path in files:
            self.list.addItem(path)

    # --- шаг ---------------------------------------------------------------
    def references(self) -> list[str]:
        return [self.list.item(i).text() for i in range(self.list.count())]

    def commit(self, recipe: dict) -> None:
        recipe["references"] = self.references()
        index = self.preset.currentIndex()
        recipe["preset"] = PRESETS[index - 1][1] if index > 0 else None
        recipe["quality_mode"] = QUALITY_MODES[max(0, min(self.mode.currentIndex(), 2))]
        recipe["user_lyrics_lines"] = [
            line.strip() for line in self.lyrics.toPlainText().splitlines() if line.strip()
        ]
        recipe["bilingual"] = self.bilingual.isChecked()
        recipe["n_verses"] = int(self.verses.value())

    def help_text(self) -> str:
        return t("wizard.material.hint")
