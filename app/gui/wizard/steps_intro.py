# -*- coding: utf-8 -*-
"""
app/gui/wizard/steps_intro.py — первые шаги: статус локальных моделей, имя артиста, файлы референсов.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton, QSlider, QTextEdit

from app.gui.wizard.ui import DIM, H1, H2, HR, StepBase

class StepAIStatus(StepBase):
    """Отображает реальные availability состояния registry без загрузки моделей."""
    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1("AI: модели и pipeline"))
        self.root.addWidget(DIM(
            "Статус проверяется без загрузки весов в VRAM. READY означает, что роль "
            "доступна для runner; NO MODEL/DEPENDENCY — что pipeline честно применит fallback."
        ))
        self.info = QTextEdit()
        self.info.setReadOnly(True)
        self.info.setMinimumHeight(360)
        self.root.addWidget(self.info, 1)
        row = QHBoxLayout()
        self.btn_refresh = QPushButton("Обновить статусы")
        self.btn_refresh.clicked.connect(self.refresh)
        row.addWidget(self.btn_refresh)
        row.addStretch()
        self.root.addLayout(row)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)
    def refresh(self):
        try:
            from app.ai.registry import MODEL_REGISTRY, registry
            runtime = registry.status()
            lines = [
                f"VRAM budget: {runtime['budget']['vram_gb']:.1f} GB | "
                f"RAM: {runtime['budget']['ram_gb']:.1f} GB | current: {runtime['current'] or 'none'}",
                "",
            ]
            for key, spec in MODEL_REGISTRY.items():
                available = registry.is_available(key)
                marker = "READY" if available else "NO MODEL/DEPENDENCY"
                lines.append(
                    f"[{marker}] {key} — {spec['role']} "
                    f"({spec['engine']}; ~{float(spec.get('vram_est_gb', 0)):.1f} GB VRAM)"
                )
            self.info.setPlainText("\n".join(lines))
        except Exception as exc:
            self.info.setPlainText(f"AI status unavailable: {type(exc).__name__}: {exc}")
    def enter(self):
        self.refresh()
    def help_text(self):
        return "READY не загружает модель заранее: SequentialAIRunner держит в памяти только одну роль за раз."
class StepArtist(StepBase):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1("🎤 Как тебя зовут?"))
        self.root.addWidget(
            DIM(
                "Это твоё артист-имя. Оно попадёт в ID3-теги всех твоих треков "
                "(Spotify, Yandex, TikTok — везде будет видно именно его). "
                "Можно поменять позже в меню Профиль."
            )
        )
        self.name = QLineEdit()
        self.name.setPlaceholderText("Например: ZS ARTIST, MC Night, Supra Kid…")
        self.name.setStyleSheet("font-size:18px; padding:12px;")
        self.root.addWidget(self.name)
        self.root.addStretch()
    def enter(self):
        try:
            from modules.user_profile import get_artist_name
            self.name.setText(get_artist_name())
        except Exception:
            pass
    def commit(self, recipe):
        try:
            from modules.user_profile import set_artist_name
            set_artist_name(self.name.text().strip() or "ZSMM Artist")
        except Exception:
            pass
        recipe["artist_name"] = self.name.text().strip() or "ZSMM Artist"
    def help_text(self):
        return "Артист-имя — то, под которым ты выпускаешь треки."
class StepReferences(StepBase):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1("① Референсы"))
        self.root.addWidget(
            DIM(
                "Перетащи 1–7 треков (mp3/wav). Первый — главный. "
                "Мы НЕ КОПИРУЕМ их — вытянем только BPM, ритм, вайб."
            )
        )
        self.list = QListWidget()
        self.list.setAcceptDrops(True)
        self.list.setDragDropMode(QListWidget.InternalMove)
        self.list.setMinimumHeight(180)
        self.root.addWidget(self.list)
        br = QHBoxLayout()
        b_add = QPushButton("＋ Добавить файлы")
        b_add.clicked.connect(self.pick_files)
        b_clr = QPushButton("Очистить")
        b_clr.clicked.connect(self.list.clear)
        br.addWidget(b_add)
        br.addWidget(b_clr)
        br.addStretch()
        self.root.addLayout(br)
        self.root.addWidget(HR())
        self.root.addWidget(H2("Тема трека / моя тема (обязательно попадёт в текст)"))
        self.theme = QLineEdit()
        self.theme.setPlaceholderText(
            "лето, тачки, деньги, Турция, Supra, вечер, Стамбул…"
        )
        self.root.addWidget(self.theme)
        # Duration — из ТЗ 20.2 вопрос 5: 1:30 — 3:30+, default 2:30
        self.root.addWidget(H2("Длительность (сек): 90 — 300, по умолчанию 150 (2:30)"))
        dur_row = QHBoxLayout()
        self.dur = QSlider(Qt.Horizontal)
        self.dur.setRange(90, 300)
        self.dur.setValue(150)
        self.dur.setSingleStep(1)
        self.dur.setPageStep(10)
        self.dur_label = QLabel("2:30")
        self.dur.valueChanged.connect(
            lambda v: self.dur_label.setText(f"{v//60}:{v%60:02d}  ({v} сек)")
        )
        dur_row.addWidget(self.dur, 1)
        dur_row.addWidget(self.dur_label)
        self.root.addLayout(dur_row)
        self.setAcceptDrops(True)
    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
    def dropEvent(self, e: QDropEvent):
        for u in e.mimeData().urls():
            p = u.toLocalFile()
            if p and p.lower().endswith((".mp3", ".wav", ".flac", ".m4a", ".ogg")):
                self.list.addItem(p)
    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выбери референсы", "", "Audio (*.mp3 *.wav *.flac *.m4a *.ogg)"
        )
        for f in files:
            self.list.addItem(f)
    def commit(self, recipe):
        recipe["references"] = [
            self.list.item(i).text() for i in range(self.list.count())
        ]
        recipe["theme"] = self.theme.text().strip() or "лето, тачки, деньги"
        recipe["duration_sec"] = int(self.dur.value())
    def help_text(self):
        return (
            "Референсы — что тебе нравится по звуку. "
            "1-7 файлов, перетаскивай прямо в окно. "
            "Если референсов нет — иди на шаг ② и выбери пресет."
        )
