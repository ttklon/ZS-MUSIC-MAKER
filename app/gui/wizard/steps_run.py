# -*- coding: utf-8 -*-
"""
app/gui/wizard/steps_run.py — запуск и результат: экспертные настройки, очередь/ночная пачка, итог.
"""

from __future__ import annotations

from pathlib import Path
import os
import sys
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QInputDialog, QLabel, QMessageBox, QProgressBar, QPushButton, QSlider, QSpinBox, QTextEdit

from app.gui.wizard.ui import DIM, H1, HR, StepBase

class StepExpert(StepBase):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1("⑥ Экспертные опции"))
        self.root.addWidget(DIM("Можно оставить по умолчанию. Ctrl+E — старый Gradio."))
        row = QHBoxLayout()
        row.addWidget(QLabel("BPM override:"))
        self.bpm = QSpinBox()
        self.bpm.setRange(0, 200)
        self.bpm.setValue(0)
        row.addWidget(self.bpm)
        row.addStretch()
        self.root.addLayout(row)
        self.chk_full_musicgen = QCheckBox("Полный MusicGen (при VRAM ≥ 10 GB)")
        self.chk_full_musicgen.setChecked(True)
        self.root.addWidget(self.chk_full_musicgen)
        self.chk_video = QCheckBox("Собрать TikTok + Reels MP4 + обложку")
        self.chk_video.setChecked(True)
        self.root.addWidget(self.chk_video)
        self.chk_stems = QCheckBox("Экспортировать стемы (drums/bass/vocals/other)")
        self.chk_stems.setChecked(True)
        self.root.addWidget(self.chk_stems)
        row = QHBoxLayout()
        row.addWidget(QLabel("Агрессия транзиентов:"))
        self.aggro = QSlider(Qt.Horizontal)
        self.aggro.setRange(3, 10)
        self.aggro.setValue(7)
        row.addWidget(self.aggro, 1)
        self.root.addLayout(row)
    def commit(self, recipe):
        recipe["bpm_override"] = int(self.bpm.value()) or None
        recipe["full_musicgen"] = self.chk_full_musicgen.isChecked()
        recipe["make_video"] = self.chk_video.isChecked()
        recipe["export_stems"] = self.chk_stems.isChecked()
        recipe["aggression"] = self.aggro.value() / 10.0
    def help_text(self):
        return "Можно ничего не менять. Или Ctrl+E — старый Gradio v5 со всеми настройками."
class StepRun(StepBase):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1("⑦ Запуск"))
        self.root.addWidget(
            DIM(
                "«В очередь» — один трек. «Ночная пачка» — постановка сразу 5 треков "
                "с разными темами. Утром — готовый набор."
            )
        )
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.root.addWidget(self.progress)
        self.status = QLabel("Ожидание запуска…")
        self.root.addWidget(self.status)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(180)
        self.root.addWidget(self.log)
        row = QHBoxLayout()
        self.btn_start = QPushButton("🚀 В очередь")
        self.btn_start.clicked.connect(self.start)
        self.btn_batch = QPushButton("🌙 Ночная пачка (5 треков)")
        self.btn_batch.clicked.connect(self.start_batch)
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_batch)
        row.addStretch()
        self.root.addLayout(row)
        self.queue_label = QLabel("Очередь пуста")
        self.queue_label.setStyleSheet("color:#9a9aa4;")
        self.root.addWidget(self.queue_label)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.current_tid = None
        self.batch_tids = []
    def start(self):
        recipe = self.wizard.recipe
        if not recipe.get("references") and not recipe.get("preset"):
            QMessageBox.warning(
                self,
                "Мало данных",
                "Кинь хотя бы 1 референс на шаге ① или выбери пресет на ②.",
            )
            return
        self.current_tid = self.wizard.orch.enqueue(recipe)
        self.log.append(f"[{self.current_tid}] в очереди")
        self.btn_start.setEnabled(False)
    def start_batch(self):
        recipe = self.wizard.recipe
        if not recipe.get("preset") and not recipe.get("references"):
            QMessageBox.warning(
                self, "Мало данных", "Выбери пресет на ② или закинь референсы на ①."
            )
            return
        # Готовим 5 recipes с разными темами
        themes = [
            "лето, тачки, деньги",
            "ночь, драйв, дрифт",
            "клуб, движ, огонь",
            "Стамбул, вечер, чай",
            "агрессия, скорость, рёв мотора",
        ]
        recipes = []
        for t in themes:
            r = dict(recipe)
            r["theme"] = t
            recipes.append(r)
        self.batch_tids = self.wizard.orch.enqueue_batch(recipes)
        self.log.append(
            f"[BATCH] в очереди {len(self.batch_tids)} треков: {', '.join(self.batch_tids)}"
        )
        self.queue_label.setText(f"Очередь: {len(self.batch_tids)} треков в работе")
    def tick(self):
        # обновляем очередь
        active = list(self.batch_tids) + (
            [self.current_tid] if self.current_tid else []
        )
        active = [t for t in active if t]
        if not active:
            return
        lines = []
        for tid in active:
            j = self.wizard.orch.jobs.get(tid)
            if not j:
                continue
            lines.append(f"  {tid}: {j.status} | {j.stage} | {int(j.progress*100)}%")
            if j.status in ("done", "error") and j == self.wizard.orch.jobs.get(
                self.current_tid
            ):
                if j.status == "done":
                    self.log.append(f"[{tid}] ✅ DONE → {j.project_dir}")
                else:
                    self.log.append(f"[{tid}] ❌ {j.error}")
                self.btn_start.setEnabled(True)
                self.current_tid = None
                # переводим Wizard на StepResult
                if self.wizard.stack.currentIndex() == self.wizard.stack.indexOf(self):
                    self.wizard.go_to_result(j)
        self.queue_label.setText(f"Очередь: {len(active)}\n" + "\n".join(lines))
        # общий прогресс
        if active:
            avg = sum(
                (
                    self.wizard.orch.jobs.get(t).progress
                    if self.wizard.orch.jobs.get(t)
                    else 0
                )
                for t in active
            ) / len(active)
            self.progress.setValue(int(avg * 100))
    def commit(self, recipe):
        pass
    def help_text(self):
        return (
            "В очередь — один трек. Ночная пачка — 5 треков сразу "
            "(программа посчитает их за ночь)."
        )
class StepResult(StepBase):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1("⑧ Результат"))
        self.info = QLabel("Ожидание готового трека…")
        self.info.setWordWrap(True)
        self.root.addWidget(self.info)
        self.detector = QLabel("")
        self.detector.setWordWrap(True)
        self.detector.setStyleSheet(
            "background:#17171d;border:1px solid #2a2a34;padding:8px;"
        )
        self.root.addWidget(self.detector)
        # 3 кнопки — из ТЗ 20.2 вопрос 25
        row = QHBoxLayout()
        self.btn_full = QPushButton("🔁 Пересобрать всё")
        self.btn_full.clicked.connect(self.rebuild_full)
        self.btn_part = QPushButton("✂️ Переделать часть")
        self.btn_part.clicked.connect(self.rebuild_part)
        self.btn_three = QPushButton("🎲 Показать 3 варианта")
        self.btn_three.clicked.connect(self.three_variants)
        row.addWidget(self.btn_full)
        row.addWidget(self.btn_part)
        row.addWidget(self.btn_three)
        self.root.addLayout(row)
        self.root.addWidget(HR())
        row2 = QHBoxLayout()
        self.btn_folder = QPushButton("📂 Открыть папку релиза")
        self.btn_folder.clicked.connect(self.open_folder)
        self.btn_expert = QPushButton("🛠 Экспертный режим (Gradio v5)")
        self.btn_expert.clicked.connect(lambda: self.wizard.launch_gradio_expert())
        row2.addWidget(self.btn_folder)
        row2.addWidget(self.btn_expert)
        row2.addStretch()
        self.root.addLayout(row2)
        self.current_job = None
    def show_result(self, job):
        self.current_job = job
        result = job.result or {}
        rel = result.get("release", {}).get("release_dir", "?")
        master = result.get("master") or result.get("master_path", "?")
        self.info.setText(
            f"✅ Готово!\n\n"
            f"Track ID: {job.track_id}\n"
            f"Мастер: {master}\n"
            f"Релиз-пакет: {rel}\n"
            f"Время: {job.finished_at - job.started_at:.1f} сек"
        )
        ai = result.get("ai_detector", {})
        if ai.get("ok"):
            adv = "\n".join(f"  • {a}" for a in ai.get("advice", [])[:4])
            self.detector.setText(
                f"🧪 AI-детектор (9 метрик): {ai.get('verdict')}  |  score={ai.get('score')}\n"
                f"Флаги: {', '.join(ai.get('flags', [])) or 'нет'}\n"
                f"{adv}"
            )
        else:
            self.detector.setText("🧪 AI-детектор: пока не запускался")
    def open_folder(self):
        if not self.current_job:
            return
        p = self.current_job.project_dir
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(p))
            else:
                import webbrowser
                from pathlib import Path
                webbrowser.open(Path(p).absolute().as_uri())
        except Exception:
            pass
    def rebuild_full(self):
        if not self.current_job:
            return
        self.wizard.orch.enqueue(self.current_job.recipe)
        QMessageBox.information(self, "Готово", "Полная пересборка в очереди.")
    def rebuild_part(self):
        parts = ["Бит", "Текст", "Голос", "Мастер"]
        item, ok = QInputDialog.getItem(
            self, "Что переделать?", "Компонент:", parts, 0, False
        )
        if not ok or not self.current_job:
            return
        r = dict(self.current_job.recipe)
        r["rebuild_only"] = item.lower()
        self.wizard.orch.enqueue(r)
        QMessageBox.information(self, "Готово", f"«{item}» пойдёт заново в очередь.")
    def three_variants(self):
        if not self.current_job:
            return
        recipes = []
        for i in range(3):
            r = dict(self.current_job.recipe)
            r["variant"] = i + 1
            r["aggression"] = 0.4 + i * 0.2  # разная агрессия
            recipes.append(r)
        tids = self.wizard.orch.enqueue_batch(recipes)
        QMessageBox.information(
            self,
            "3 варианта",
            f"3 версии в очереди: {', '.join(tids)}. Сравнишь готовые файлы.",
        )
    def commit(self, recipe):
        pass
    def help_text(self):
        return (
            "3 кнопки: полная пересборка, переделать только часть, "
            "сделать сразу 3 варианта для сравнения."
        )
