# -*- coding: utf-8 -*-
"""
app/gui/wizard/steps_tuning.py — шаг 4: тонкая настройка.

Всё здесь имеет рабочий дефолт: можно пройти шаг не меняя ничего. BPM, агрессия
транзиентов, набор стендов мастеринга, экспорт видео/стемов, экстра-промпт и
поиск сэмплов (только CC0/CC-BY — коммерчески безопасно).
"""

from __future__ import annotations

import logging

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox

from app.core.i18n import t
from app.gui.wizard.ui import DIM, H1, H2, HR, StepBase

LOGGER = logging.getLogger(__name__)


class StepTuning(StepBase):
    """Шаг 4: тонкая настройка — BPM, агрессия, стенды, экспорт, сэмплы."""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1(t("wizard.tuning.title")))
        self.root.addWidget(DIM(t("wizard.tuning.hint")))

        bpm_row = QHBoxLayout()
        bpm_row.addWidget(QLabel(t("wizard.tuning.bpm")))
        self.bpm = QSpinBox()
        self.bpm.setRange(0, 220)
        self.bpm.setValue(0)
        bpm_row.addWidget(self.bpm)
        bpm_row.addStretch()
        bpm_row.addWidget(QLabel(t("wizard.tuning.aggression")))
        self.aggression = QSpinBox()
        self.aggression.setRange(30, 100)
        self.aggression.setValue(70)
        self.aggression.setSuffix(" %")
        bpm_row.addWidget(self.aggression)
        self.root.addLayout(bpm_row)

        self.root.addWidget(H2(t("wizard.tuning.stands")))
        stands_row = QHBoxLayout()
        self.stand_car = QCheckBox(t("wizard.tuning.car"))
        self.stand_club = QCheckBox(t("wizard.tuning.club"))
        self.stand_stream = QCheckBox(t("wizard.tuning.streaming"))
        for box in (self.stand_car, self.stand_club, self.stand_stream):
            box.setChecked(True)
            stands_row.addWidget(box)
        stands_row.addStretch()
        self.root.addLayout(stands_row)

        self.stems = QCheckBox(t("wizard.tuning.stems"))
        self.stems.setChecked(True)
        self.root.addWidget(self.stems)

        self.root.addWidget(H2(t("wizard.tuning.extra")))
        self.extra = QLineEdit()
        self.extra.setPlaceholderText(t("wizard.tuning.extra_placeholder"))
        self.root.addWidget(self.extra)

        self.root.addWidget(HR())
        self.root.addWidget(H2(t("wizard.tuning.samples")))
        sample_row = QHBoxLayout()
        self.sample_query = QLineEdit()
        self.sample_query.setPlaceholderText("phonk kick, 808 sub, dark pad…")
        search = QPushButton(t("wizard.tuning.search"))
        search.clicked.connect(self._search_samples)
        sample_row.addWidget(self.sample_query, 1)
        sample_row.addWidget(search)
        self.root.addLayout(sample_row)

        flags = QHBoxLayout()
        self.allow_online = QCheckBox(t("wizard.tuning.online"))
        self.allow_online.setChecked(True)
        self.license_only = QCheckBox(t("wizard.tuning.license"))
        self.license_only.setChecked(True)
        flags.addWidget(self.allow_online)
        flags.addWidget(self.license_only)
        flags.addStretch()
        self.root.addLayout(flags)
        self.sample_result = DIM("")
        self.root.addWidget(self.sample_result)
        self.root.addStretch()

    def _search_samples(self) -> None:
        query = self.sample_query.text().strip()
        if not query:
            self.sample_result.setText(t("wizard.run.need_genre"))
            return
        try:
            from agents import sample_hunter

            found = sample_hunter.hunt(
                query,
                max_results=15,
                allow_online=self.allow_online.isChecked(),
                license_filter=self.license_only.isChecked(),
            )
            self.sample_result.setText(
                f"local: {len(found.get('local', []))}, online: {len(found.get('online', []))}"
            )
        except Exception as error:  # noqa: BLE001 - поиск сэмплов не должен ронять мастер
            LOGGER.warning("sample search failed: %s", error)
            self.sample_result.setText(f"{t('dialog.error')}: {error}")

    def commit(self, recipe: dict) -> None:
        recipe["bpm_override"] = int(self.bpm.value()) or None
        recipe["aggression"] = self.aggression.value() / 100.0
        recipe["stands"] = [
            name
            for name, box in (
                ("car", self.stand_car),
                ("club", self.stand_club),
                ("streaming", self.stand_stream),
            )
            if box.isChecked()
        ]
        recipe["export_stems"] = self.stems.isChecked()
        recipe["user_extra_prompt"] = self.extra.text().strip()

    def help_text(self) -> str:
        return t("wizard.tuning.hint")
