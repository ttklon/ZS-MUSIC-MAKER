# -*- coding: utf-8 -*-
"""
app/gui/wizard/window.py — главное окно: пять шагов, меню, онбординг.

Мастер намеренно короткий: жанр и тема → материал → голос → тонкая настройка →
запуск. Всё, что раньше занимало отдельные шаги (статус моделей, имя артиста,
сэмплы), либо переехало в тот же экран, либо стало диалогом из меню — проходить
девять экранов, чтобы получить трек, было лишним.

Статус моделей — диагностика, а не шаг творчества, поэтому он в меню AI
(`dialogs.AIStatusDialog`) и в F2.
"""

from __future__ import annotations

import logging
import threading
import webbrowser
from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.i18n import t
from app.gui.wizard.steps_brief import StepBrief
from app.gui.wizard.steps_material import StepMaterial
from app.gui.wizard.steps_run import StepResult, StepRun
from app.gui.wizard.steps_tuning import StepTuning
from app.gui.wizard.steps_voice import StepVoice
from app.gui.wizard.ui import StepBase  # noqa: F401 - публичный реэкспорт для шагов

LOGGER = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]


def app_version() -> str:
    """Версия из единственного источника (`version.json` через `app.cli.env`)."""
    try:
        from app.cli.env import ctx

        return str(ctx.version)
    except Exception:  # noqa: BLE001 - окно должно открыться и без версии
        LOGGER.debug("version unavailable", exc_info=True)
        return "?"


class Wizard(QMainWindow):
    """Мастер из пяти шагов + экран результата."""

    def __init__(self, orch, hw, log):
        super().__init__()
        self.orch, self.hw, self.log = orch, hw, log
        self.setWindowTitle(
            f"ZS Music Maker {app_version()}  |  {hw.gpu_name} ({hw.backend}, {hw.mode})"
        )
        self.resize(1200, 820)
        self.recipe: dict = {}

        self.steps = [
            StepBrief(self),
            StepMaterial(self),
            StepVoice(self),
            StepTuning(self),
            StepRun(self),
        ]
        self.result_step = StepResult(self)
        self.stack = QStackedWidget()
        for step in self.steps:
            self.stack.addWidget(step)
        self.stack.addWidget(self.result_step)

        self.crumbs = QLabel(self._crumb_text())
        self.crumbs.setStyleSheet("color:#9a9aa4;")
        self.btn_back = QPushButton(t("nav.back"))
        self.btn_back.clicked.connect(self.back)
        self.btn_next = QPushButton(t("nav.next"))
        self.btn_next.clicked.connect(self.next)
        self.btn_help = QPushButton(t("nav.help"))
        self.btn_help.clicked.connect(self.show_help)

        bar = QHBoxLayout()
        bar.addWidget(self.btn_back)
        bar.addStretch()
        bar.addWidget(self.btn_help)
        bar.addSpacing(20)
        bar.addWidget(self.crumbs)
        bar.addStretch()
        bar.addWidget(self.btn_next)

        root = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.stack)
        root.addWidget(scroll)
        root.addLayout(bar)
        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

        self._build_menu()
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.launch_gradio_expert)
        QShortcut(QKeySequence("F1"), self, activated=self.show_help)
        QShortcut(QKeySequence("F2"), self, activated=self.show_ai_status)
        self._sync_nav()
        self._maybe_onboarding()

    # --- меню --------------------------------------------------------------
    def _build_menu(self) -> None:
        menu = self.menuBar()
        help_menu = menu.addMenu(t("menu.help"))
        tour = QAction(t("menu.tour"), self)
        tour.triggered.connect(self._show_tour)
        help_menu.addAction(tour)
        about = QAction(t("menu.about"), self)
        about.triggered.connect(self._about)
        help_menu.addAction(about)

        ai_menu = menu.addMenu(t("menu.ai"))
        status = QAction(t("menu.model_status"), self)
        status.triggered.connect(self.show_ai_status)
        ai_menu.addAction(status)

    # --- навигация ---------------------------------------------------------
    def _crumb_text(self) -> str:
        index = self.stack.currentIndex() if hasattr(self, "stack") else 0
        if index >= len(self.steps):
            return t("wizard.result_step")
        return t("wizard.step", index=index + 1, total=len(self.steps))

    def _sync_nav(self) -> None:
        index = self.stack.currentIndex()
        on_result = index >= len(self.steps)
        self.btn_next.setEnabled(not on_result and index < len(self.steps) - 1)
        self.btn_back.setEnabled(index > 0)
        self.btn_next.setText(t("nav.next"))

    def back(self) -> None:
        index = self.stack.currentIndex()
        if index > 0:
            self.stack.setCurrentIndex(index - 1)
            self.stack.currentWidget().enter()
        self.crumbs.setText(self._crumb_text())
        self._sync_nav()

    def next(self) -> None:
        current = self.stack.currentWidget()
        if isinstance(current, StepBase):
            current.commit(self.recipe)
        index = self.stack.currentIndex()
        if index < len(self.steps) - 1:
            self.stack.setCurrentIndex(index + 1)
            self.stack.currentWidget().enter()
        self.crumbs.setText(self._crumb_text())
        self._sync_nav()

    def go_to_result(self, job) -> None:
        """Открыть экран результата, когда трек готов."""
        try:
            self.stack.setCurrentWidget(self.result_step)
            self.result_step.show_result(job)
            self.crumbs.setText(self._crumb_text())
            self._sync_nav()
        except Exception:  # noqa: BLE001 - переход не должен ломать окно
            self.log.exception("go_to_result failed")

    def current_recipe(self) -> dict:
        """Собрать рецепт из всех шагов (для CLI-совместимости и тестов)."""
        for step in self.steps:
            step.commit(self.recipe)
        return dict(self.recipe)

    # --- диалоги -----------------------------------------------------------
    def show_ai_status(self) -> None:
        from app.gui.wizard.dialogs import AIStatusDialog

        AIStatusDialog(self).exec()

    def show_help(self) -> None:
        current = self.stack.currentWidget()
        text = getattr(current, "help_text", lambda: "")()
        QMessageBox.information(self, t("dialog.help_title"), text or "—")

    def go_to_ai_status(self) -> None:
        """Совместимость с прежним API: теперь это меню, а не шаг."""
        self.show_ai_status()

    def _maybe_onboarding(self) -> None:
        try:
            from app.gui.onboarding import maybe_show_onboarding

            if maybe_show_onboarding(self):
                self.log.info("Onboarding tour shown")
        except Exception:  # noqa: BLE001 - онбординг не критичен
            self.log.warning("onboarding failed", exc_info=True)

    def _show_tour(self) -> None:
        try:
            from app.gui.onboarding import show_help_tour

            show_help_tour(self)
        except Exception as error:  # noqa: BLE001 - тур опционален
            QMessageBox.warning(self, t("dialog.help_title"), str(error))

    def _about(self) -> None:
        QMessageBox.information(
            self,
            t("dialog.about_title"),
            f"ZS Music Maker {app_version()}\n\n"
            "Локальная студия треков: бит, вокал, микс, мастеринг под 8 стендов, "
            "обложка и релиз-пакет.\n"
            "Облачные провайдеры используются только при их настройке; "
            "часть моделей и возможностей требует отдельной установки.",
        )

    def launch_gradio_expert(self) -> None:
        """Ctrl+E — Gradio-интерфейс для тонкой ручной работы."""
        self.log.info("Ctrl+E → Gradio")

        def _run() -> None:
            try:
                import main as entry

                if hasattr(entry, "build_ui"):
                    entry.build_ui().launch(server_port=7860, inbrowser=True, share=False)
                else:
                    import runpy

                    runpy.run_path(str(ROOT / "main.py"), run_name="__main__")
            except Exception:  # noqa: BLE001 - поток, ошибку только логируем
                LOGGER.exception("Gradio expert failed")

        threading.Thread(target=_run, daemon=True).start()
        threading.Timer(2.0, webbrowser.open, args=("http://127.0.0.1:7860",)).start()
