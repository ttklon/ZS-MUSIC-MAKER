# -*- coding: utf-8 -*-
"""
app/gui/wizard/window.py — главное окно: навигация по шагам, меню, онбординг.
"""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.core.i18n import t
from app.gui.wizard.steps_creative import StepLyrics
from app.gui.wizard.steps_creative import StepPreset
from app.gui.wizard.steps_creative import StepSamples
from app.gui.wizard.steps_creative import StepVoice
from app.gui.wizard.steps_intro import StepAIStatus
from app.gui.wizard.steps_intro import StepArtist
from app.gui.wizard.steps_intro import StepReferences
from app.gui.wizard.steps_run import StepExpert
from app.gui.wizard.steps_run import StepResult
from app.gui.wizard.steps_run import StepRun
from app.gui.wizard.ui import DIM, H1, H2, HR, StepBase  # noqa: F401 - используется шагами окна

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"

class Wizard(QMainWindow):
    def __init__(self, orch, hw, log):
        super().__init__()
        self.orch, self.hw, self.log = orch, hw, log
        self.setWindowTitle(
            f"ZS Music Maker v7  |  {hw.gpu_name} ({hw.backend}, {hw.mode})"
        )
        self.resize(1200, 820)
        self.recipe = {}
        self.stack = QStackedWidget()
        # 9 шагов
        self.steps = [
            StepAIStatus(self),
            StepArtist(self),
            StepReferences(self),
            StepPreset(self),
            StepSamples(self),
            StepLyrics(self),
            StepVoice(self),
            StepExpert(self),
            StepRun(self),
            StepResult(self),
        ]
        for s in self.steps:
            self.stack.addWidget(s)
        # Bottom bar
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
        root.addWidget(self.stack)
        root.addLayout(bar)
        w = QWidget()
        w.setLayout(root)
        self.setCentralWidget(w)
        # Menu bar
        mb = self.menuBar()
        help_menu = mb.addMenu(t("menu.help"))
        a_tour = QAction(t("menu.tour"), self)
        a_tour.triggered.connect(self._show_tour)
        help_menu.addAction(a_tour)
        a_about = QAction(t("menu.about"), self)
        a_about.triggered.connect(self._about)
        help_menu.addAction(a_about)
        ai_menu = mb.addMenu(t("menu.ai"))
        a_ai_status = QAction(t("menu.model_status"), self)
        a_ai_status.triggered.connect(self.go_to_ai_status)
        ai_menu.addAction(a_ai_status)
        # Shortcuts
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.launch_gradio_expert)
        QShortcut(QKeySequence("F1"), self, activated=self.show_help)
        # Onboarding при первом запуске
        self._maybe_onboarding()
    def go_to_ai_status(self):
        self.stack.setCurrentWidget(self.steps[0])
        self.steps[0].enter()
        self.crumbs.setText(self._crumb_text())
    def _crumb_text(self):
        i = self.stack.currentIndex() if hasattr(self, "stack") else 0
        return f"Шаг {i+1} / {len(self.steps)}"
    def _maybe_onboarding(self):
        try:
            from app.gui.onboarding import maybe_show_onboarding
            shown = maybe_show_onboarding(self)
            if shown:
                self.log.info("Onboarding tour shown")
        except Exception as e:
            self.log.warning(f"onboarding failed: {e}")
    def _show_tour(self):
        try:
            from app.gui.onboarding import show_help_tour
            show_help_tour(self)
        except Exception as e:
            QMessageBox.warning(self, "Помощь", f"Тур недоступен: {e}")
    def _about(self):
        QMessageBox.information(
            self,
            "О программе",
            "ZS Music Maker v7 (MM ZS)\n\n"
            "Локальная студия хитовых треков.\n"
            "Windows 11 + PySide6 + RVC v2 + MusicGen + Matchering + Silero.\n\n"
            "Всё бесплатно, всё локально, ничего в облаке.\n"
            "https://github.com/… (open-source)",
        )
    def show_help(self):
        cur = self.stack.currentWidget()
        txt = (
            cur.help_text()
            if hasattr(cur, "help_text")
            else "Помощь по этому шагу пока не написана."
        )
        QMessageBox.information(self, "Помощь", txt)
    def back(self):
        i = self.stack.currentIndex()
        if i > 0:
            self.stack.setCurrentIndex(i - 1)
        self.crumbs.setText(self._crumb_text())
    def next(self):
        cur = self.stack.currentWidget()
        cur.commit(self.recipe)
        i = self.stack.currentIndex()
        if i < self.stack.count() - 1:
            self.stack.setCurrentIndex(i + 1)
            nxt = self.stack.currentWidget()
            nxt.enter()
        self.crumbs.setText(self._crumb_text())
    def go_to_result(self, job):
        """Автоматический переход на StepResult, когда трек готов."""
        try:
            idx = None
            for i, s in enumerate(self.steps):
                if isinstance(s, StepResult):
                    idx = i
                    break
            if idx is None:
                return
            self.stack.setCurrentIndex(idx)
            self.steps[idx].show_result(job)
            self.crumbs.setText(self._crumb_text())
        except Exception as e:
            self.log.warning(f"go_to_result failed: {e}")
    def launch_gradio_expert(self):
        self.log.info("Ctrl+E → v5 Gradio")
        def _run():
            try:
                import main as v5main
                if hasattr(v5main, "build_ui"):
                    v5main.build_ui().launch(
                        server_port=7860, inbrowser=True, share=False
                    )
                else:
                    import runpy
                    runpy.run_path(str(ROOT / "main.py"), run_name="__main__")
            except Exception as e:
                self.log.exception(f"Gradio expert failed: {e}")
        threading.Thread(target=_run, daemon=True).start()
        # Keep the server warm-up delay without blocking the Qt UI thread.
        threading.Timer(2.0, webbrowser.open, args=("http://127.0.0.1:7860",)).start()
