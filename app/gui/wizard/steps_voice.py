# -*- coding: utf-8 -*-
"""
app/gui/wizard/steps_voice.py — шаг 3: голос.

Своя запись с микрофона — основной путь (`own_vocal_wav`): стадия вокала берёт
её как есть и честно помечает `engine="user_recording"`. Синтез и RVC остаются
FALLBACK-ветками и в интерфейсе названы именно так — никакого «как будто спел
нейросетью» под видом живого вокала.

Таймер статуса обучения RVC стартует лениво (только когда шаг реально открыт):
раньше `QTimer` создавался в конструкторе без импорта и мастер падал на старте.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
)

from app.core.i18n import t
from app.gui.wizard.ui import DIM, H1, H2, StepBase

LOGGER = logging.getLogger(__name__)

VOICE_MODES = ("pro", "lazy", "off")
AUDIO_SUFFIXES = (".wav", ".flac", ".mp3", ".m4a", ".ogg")

# раз в 2 секунды смотреть прогресс обучения RVC — этого достаточно и не грузит диск
STATUS_INTERVAL_MS = 2000


class StepVoice(StepBase):
    """Режим вокала + своя запись + караоке/RVC + голосовой архив."""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1(t("wizard.voice.title")))
        self.root.addWidget(DIM(t("wizard.voice.hint")))

        self.root.addWidget(H2(t("wizard.voice.mode")))
        self.mode = QComboBox()
        self.mode.addItems(
            [
                t("wizard.voice.mode_pro"),
                t("wizard.voice.mode_lazy"),
                t("wizard.voice.mode_off"),
            ]
        )
        self.mode.setCurrentIndex(0)
        self.root.addWidget(self.mode)

        self.root.addWidget(H2(t("wizard.voice.own")))
        own_row = QHBoxLayout()
        self.own_label = QLabel(t("wizard.voice.none"))
        self.own_label.setWordWrap(True)
        pick = QPushButton(t("wizard.voice.choose"))
        pick.clicked.connect(self.pick_own_vocal)
        drop = QPushButton("✕")
        drop.setToolTip(t("wizard.material.clear"))
        drop.clicked.connect(self.clear_own_vocal)
        own_row.addWidget(self.own_label, 1)
        own_row.addWidget(pick)
        own_row.addWidget(drop)
        self.root.addLayout(own_row)
        self._own_vocal: str | None = None

        self.root.addWidget(H2(t("wizard.voice.vault")))
        self.vault_label = QLabel("…")
        self.vault_label.setWordWrap(True)
        self.root.addWidget(self.vault_label)

        actions = QHBoxLayout()
        karaoke = QPushButton(t("wizard.voice.karaoke"))
        karaoke.clicked.connect(self.open_karaoke)
        train = QPushButton(t("wizard.voice.rvc"))
        train.clicked.connect(lambda: self.train_rvc(night=False))
        night = QPushButton(t("wizard.voice.night"))
        night.clicked.connect(lambda: self.train_rvc(night=True))
        actions.addWidget(karaoke)
        actions.addWidget(train)
        actions.addWidget(night)
        actions.addStretch()
        self.root.addLayout(actions)

        self.training_label = QLabel("")
        self.training_label.setStyleSheet("color:#9a9aa4;")
        self.root.addWidget(self.training_label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_training)
        self._timer_started = False

    # --- вход на шаг -------------------------------------------------------
    def enter(self) -> None:
        self.refresh_vault()
        if not self._timer_started:
            self._timer.start(STATUS_INTERVAL_MS)
            self._timer_started = True

    def refresh_vault(self) -> None:
        try:
            from modules.voice_convert import vault_summary

            summary = vault_summary()
            ready = "ДА" if summary["ready_for_training"] else "нет (нужно ≥ 5 мин)"
            missing = ", ".join(summary["recommended_next_styles"][:3]) or "все ок"
            self.vault_label.setText(
                f"Записей: {summary['recordings']}, минут: {summary['total_minutes']:.1f}, "
                f"покрытие фонем: {summary['phoneme_coverage_pct']}%.\n"
                f"Готово к обучению: {ready}. Не хватает стилей: {missing}"
            )
        except Exception as error:  # noqa: BLE001 - архив может отсутствовать
            LOGGER.warning("voice vault unavailable: %s", error)
            self.vault_label.setText(f"Voice Vault недоступен: {error}")

    def refresh_training(self) -> None:
        try:
            from modules.voice_convert import get_training_status

            status = get_training_status("my_voice")
            if not status:
                return
            self.training_label.setText(
                f"[RVC] {status.get('status', '?')} | {status.get('stage', '')} "
                f"| {int(float(status.get('progress', 0.0)) * 100)}%"
            )
        except Exception:  # noqa: BLE001 - статус обучения не критичен
            LOGGER.debug("training status unavailable", exc_info=True)

    # --- своя запись -------------------------------------------------------
    def pick_own_vocal(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("wizard.voice.own"),
            "",
            "Audio (*.wav *.flac *.mp3 *.m4a *.ogg)",
        )
        if path:
            self.set_own_vocal(path)

    def set_own_vocal(self, path: str) -> None:
        """Принять запись пользователя; несуществующий файл не принимаем молча."""
        if not path:
            return
        file = Path(path)
        if not file.exists() or file.suffix.lower() not in AUDIO_SUFFIXES:
            self._own_vocal = None
            self.own_label.setText(f"{t('dialog.error')}: {path}")
            return
        self._own_vocal = str(file)
        size_mb = file.stat().st_size / (1024 * 1024)
        self.own_label.setText(f"{file.name}  ({size_mb:.1f} MB)")

    def clear_own_vocal(self) -> None:
        self._own_vocal = None
        self.own_label.setText(t("wizard.voice.none"))

    def own_vocal(self) -> str | None:
        return self._own_vocal

    # --- караоке и RVC -----------------------------------------------------
    def open_karaoke(self) -> None:
        """Запись голоса в отдельном окне; удачная запись сразу становится вокалом."""
        try:
            from app.gui.wizard.record_dialog import RecordDialog

            dialog = RecordDialog(self)
            if dialog.exec() == dialog.Accepted and dialog.result_path:
                self.set_own_vocal(dialog.result_path)
            self.refresh_vault()
        except Exception as error:  # noqa: BLE001 - рекордер опционален
            QMessageBox.warning(self, t("wizard.voice.karaoke"), str(error))

    def train_rvc(self, night: bool = False) -> None:
        try:
            from modules.voice_convert import train_rvc_model

            result = train_rvc_model(voice_name="my_voice", epochs=100, night_mode=night)
            QMessageBox.information(
                self,
                t("wizard.voice.rvc"),
                f"Обучение запущено в фоне.\nБэкенд: {result.get('backend')}, "
                f"устройство: {result.get('device')}, эпох: {result.get('epochs')}.",
            )
        except Exception as error:  # noqa: BLE001 - обучение опционально
            QMessageBox.warning(self, t("wizard.voice.rvc"), str(error))

    # --- шаг ---------------------------------------------------------------
    def commit(self, recipe: dict) -> None:
        index = max(0, min(self.mode.currentIndex(), len(VOICE_MODES) - 1))
        recipe["voice_mode"] = VOICE_MODES[index]
        recipe["own_vocal_wav"] = self._own_vocal

    def help_text(self) -> str:
        return t("wizard.voice.hint")
