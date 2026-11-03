# -*- coding: utf-8 -*-
"""
app/gui/wizard/steps_brief.py — шаг 1: жанр, тема, артист, длительность, seed.

Один экран вместо трёх прежних (статус моделей → артист → референсы): всё, что
нужно для запуска, собрано здесь. Статус моделей переехал в меню (диалог), потому
что это диагностика, а не шаг творческого процесса.

Жанры берутся из единственного источника — `modules.genre_engine.StyleRegistry`
(119 жанров), а не из захардкоженного списка в GUI: раньше список в визарде и
движке расходился.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QSlider, QSpinBox

from app.core.i18n import t
from app.gui.wizard.ui import DIM, H1, H2, HR, StepBase

LOGGER = logging.getLogger(__name__)

DEFAULT_GENRE = "drift_phonk"
DEFAULT_THEME = "ночь, дрифт, огни города"


def available_genres() -> list[str]:
    """Список жанров из движка; если движок недоступен — только известный дефолт."""
    try:
        from modules.genre_engine import StyleRegistry

        genres = sorted(StyleRegistry().list_genres())
        if genres:
            return genres
    except Exception as error:  # noqa: BLE001 - GUI не должен падать на импорте
        LOGGER.warning("genre list unavailable: %s", error)
    return [DEFAULT_GENRE]


class StepBrief(StepBase):
    """Жанр + тема + артист + длительность + seed."""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1(t("wizard.brief.title")))
        self.root.addWidget(DIM(t("wizard.brief.hint")))

        self.root.addWidget(H2(t("wizard.brief.genre")))
        filter_row = QHBoxLayout()
        self.genre_filter = QLineEdit()
        self.genre_filter.setPlaceholderText(t("wizard.brief.genre_filter"))
        self.genre_filter.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self.genre_filter, 1)
        self.root.addLayout(filter_row)

        self.genre = QComboBox()
        self.genre.setEditable(False)
        self._genres = available_genres()
        self.genre.addItems(self._genres)
        if DEFAULT_GENRE in self._genres:
            self.genre.setCurrentText(DEFAULT_GENRE)
        self.root.addWidget(self.genre)
        self.genre_count = DIM("")
        self.root.addWidget(self.genre_count)
        self._update_count()

        self.root.addWidget(H2(t("wizard.brief.theme")))
        self.theme = QLineEdit()
        self.theme.setPlaceholderText(t("wizard.brief.theme_placeholder"))
        self.theme.setStyleSheet("font-size:16px; padding:10px;")
        self.root.addWidget(self.theme)

        self.root.addWidget(H2(t("wizard.brief.artist")))
        self.artist = QLineEdit()
        self.artist.setPlaceholderText("ZSMM Artist")
        self.root.addWidget(self.artist)

        self.root.addWidget(HR())
        self.root.addWidget(H2(t("wizard.brief.duration")))
        dur_row = QHBoxLayout()
        self.duration = QSlider(Qt.Horizontal)
        self.duration.setRange(90, 300)
        self.duration.setValue(150)
        self.duration.setSingleStep(1)
        self.duration.setPageStep(10)
        self.duration_label = QLabel(self._duration_text(150))
        self.duration.valueChanged.connect(
            lambda value: self.duration_label.setText(self._duration_text(value))
        )
        dur_row.addWidget(self.duration, 1)
        dur_row.addWidget(self.duration_label)
        self.root.addLayout(dur_row)

        seed_row = QHBoxLayout()
        seed_row.addWidget(QLabel(t("wizard.brief.seed")))
        self.seed = QSpinBox()
        self.seed.setRange(0, 2_000_000_000)
        self.seed.setValue(0)
        seed_row.addWidget(self.seed)
        seed_row.addStretch()
        self.root.addLayout(seed_row)
        self.root.addWidget(DIM(t("wizard.brief.seed_hint")))
        self.root.addStretch()

    @staticmethod
    def _duration_text(seconds: int) -> str:
        return f"{seconds // 60}:{seconds % 60:02d}  ({seconds} s)"

    def _update_count(self) -> None:
        self.genre_count.setText(t("wizard.brief.genre_count", count=len(self._genres)))

    def _apply_filter(self, text: str) -> None:
        """Сужение списка жанров по подстроке (регистр не важен)."""
        needle = text.strip().lower()
        current = self.genre.currentText()
        self.genre.blockSignals(True)
        self.genre.clear()
        self.genre.addItems([g for g in self._genres if needle in g.lower()])
        if current in [self.genre.itemText(i) for i in range(self.genre.count())]:
            self.genre.setCurrentText(current)
        self.genre.blockSignals(False)

    def enter(self) -> None:
        try:
            from modules.user_profile import get_artist_name

            self.artist.setText(get_artist_name())
        except Exception:  # noqa: BLE001 - профиль может быть пустым
            LOGGER.debug("artist profile unavailable", exc_info=True)
        if not self.theme.text().strip():
            self.theme.setText(DEFAULT_THEME)

    def commit(self, recipe: dict) -> None:
        genre = self.genre.currentText().strip() or DEFAULT_GENRE
        theme = self.theme.text().strip() or DEFAULT_THEME
        artist = self.artist.text().strip() or "ZSMM Artist"
        recipe["genre"] = genre
        recipe["theme"] = theme
        recipe["artist"] = artist
        recipe["artist_name"] = artist
        recipe["duration_sec"] = int(self.duration.value())
        seed = int(self.seed.value())
        recipe["seed"] = seed or None
        try:
            from modules.user_profile import set_artist_name

            set_artist_name(artist)
        except Exception:  # noqa: BLE001 - запись профиля не критична для рендера
            LOGGER.debug("artist profile save failed", exc_info=True)

    def help_text(self) -> str:
        return t("wizard.brief.hint")
