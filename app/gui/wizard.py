"""
[v7] Wizard — единое окно, 9 шагов, тёмная тема.

Изменения относительно v6:
  • Шаг 0 — ArtistName (при первом запуске, из user_profile.first_run)
  • Ползунок duration: 90-300 сек, default 150 (2:30) — из ТЗ 20.2 вопрос 5
  • Переключатель QualityMode: fast / quality / max — ТЗ 20.2 вопрос 29
  • Sample Browser split-view: local list + online results
  • Три кнопки на StepResult: 🔁 Пересобрать всё / ✂️ Переделать часть / 🎲 3 варианта
  • Voice Mode: ProVoice — основной, Lazy — второстепенный (ТЗ 20.1)
  • Queue-режим: 5+ проектов на ночь (ТЗ 20.2 вопрос 7)
  • Onboarding при первом запуске (Scriptable Tour)
  • Меню «Помощь» с F1 на каждом шаге
"""

from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QDragEnterEvent,
    QDropEvent,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


# ============================================================
#   утилиты
# ============================================================
def H1(text):
    l = QLabel(text)
    l.setObjectName("H1")
    return l


def H2(text):
    l = QLabel(text)
    l.setObjectName("H2")
    return l


def DIM(text):
    l = QLabel(text)
    l.setProperty("class", "dim")
    l.setStyleSheet("color:#9a9aa4;")
    l.setWordWrap(True)
    return l


def HR():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color:#2a2a34;")
    return line


class StepBase(QWidget):
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(30, 20, 30, 20)
        self.root.setSpacing(12)

    def enter(self):
        pass

    def commit(self, recipe: dict):
        pass

    def help_text(self) -> str:
        return ""


# ============================================================
# Шаг 0: имя артиста (только при первом запуске)
# ============================================================
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


# ============================================================
# Шаг 1: референсы + тема + длительность
# ============================================================
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


# ============================================================
# Шаг 2: стиль (пресет) + режим генерации + стенды
# ============================================================
class StepPreset(StepBase):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1("② Стиль и режим"))

        # Пресет
        self.root.addWidget(DIM("Быстрый старт без референсов — выбери пресет."))
        self.combo = QComboBox()
        self.combo.addItems(
            [
                "Из референсов (по умолчанию)",
                "tamam_like — восточный фонк-эдит",
                "brazilian_phonk — агрессия, drift",
                "hyperpop_edit — TikTok-хайп",
                "lofi_drift — вечерний драйв",
                "trap_ru — русский трэп",
            ]
        )
        self.root.addWidget(self.combo)

        # Режим генерации — из ТЗ 20.2 вопрос 29
        self.root.addWidget(H2("Режим генерации"))
        self.root.addWidget(
            DIM(
                "Быстрый (10-15 мин): для черновиков и проб.\n"
                "Качественный (30-60 мин): по умолчанию, для релизов.\n"
                "Максимальный (1-3 часа): максимум качества, для главных треков."
            )
        )
        self.mode = QComboBox()
        self.mode.addItems(
            ["Быстрый (10-15 мин)", "Качественный (30-60 мин)", "Максимальный (1-3 ч)"]
        )
        self.mode.setCurrentIndex(1)  # quality default
        self.root.addWidget(self.mode)

        # Экстра-промпт
        self.root.addWidget(H2("Экстра-промт (опционально)"))
        self.extra = QTextEdit()
        self.extra.setPlaceholderText(
            "«больше 808 в припеве, Silvia в тумане, дрифт-вайб»."
        )
        self.extra.setMaximumHeight(100)
        self.root.addWidget(self.extra)

        # Стенды прослушивания
        gb = QGroupBox("Стенды прослушивания (три мастера)")
        gl = QHBoxLayout(gb)
        self.chk_car = QCheckBox("🚗 Автомобиль")
        self.chk_car.setChecked(True)
        self.chk_club = QCheckBox("🎧 Клуб")
        self.chk_club.setChecked(True)
        self.chk_str = QCheckBox("📱 Стриминг")
        self.chk_str.setChecked(True)
        for c in (self.chk_car, self.chk_club, self.chk_str):
            gl.addWidget(c)
        gl.addStretch()
        self.root.addWidget(gb)

    def commit(self, recipe):
        keys = [
            None,
            "tamam_like",
            "brazilian_phonk",
            "hyperpop_edit",
            "lofi_drift",
            "trap_ru",
        ]
        recipe["preset"] = keys[self.combo.currentIndex()]
        modes = ["fast", "quality", "max"]
        recipe["quality_mode"] = modes[self.mode.currentIndex()]
        recipe["user_extra_prompt"] = self.extra.toPlainText().strip()
        recipe["stands"] = [
            k
            for k, w in [
                ("car", self.chk_car),
                ("club", self.chk_club),
                ("streaming", self.chk_str),
            ]
            if w.isChecked()
        ]

    def help_text(self):
        return (
            "Пресеты — 5 готовых стилей, если нет референсов. "
            "Режим генерации: быстрый (для проб), качественный (по умолчанию), "
            "максимальный (для главных релизов, 1-3 часа)."
        )


# ============================================================
# Шаг 3: Sample Browser — split-view local vs online
# ============================================================
class StepSamples(StepBase):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1("③ Сэмплы (Sample Browser)"))
        self.root.addWidget(
            DIM(
                "Слева — твоя локальная библиотека. Справа — интернет-поиск. "
                "Только CC0 / Royalty-Free — коммерчески безопасно."
            )
        )

        # Поиск
        top = QHBoxLayout()
        self.q = QLineEdit()
        self.q.setPlaceholderText("phonk kick, 808 sub, dark pad, cowbell…")
        b_search = QPushButton("🔍 Найти")
        b_search.clicked.connect(self.search)
        top.addWidget(self.q, 1)
        top.addWidget(b_search)
        self.root.addLayout(top)

        # Split view
        splitter = QSplitter(Qt.Horizontal)
        # Local
        local_box = QGroupBox("Локальная библиотека")
        lv = QVBoxLayout(local_box)
        self.local_list = QListWidget()
        lv.addWidget(self.local_list)
        splitter.addWidget(local_box)
        # Online
        online_box = QGroupBox("Из интернета (CC0/CC-BY)")
        ov = QVBoxLayout(online_box)
        self.online_list = QListWidget()
        ov.addWidget(self.online_list)
        splitter.addWidget(online_box)
        splitter.setSizes([1, 1])
        self.root.addWidget(splitter, 1)

        # Options
        opt = QHBoxLayout()
        self.chk_online = QCheckBox("Разрешить онлайн-поиск")
        self.chk_online.setChecked(True)
        self.chk_lic = QCheckBox("Фильтр CC0/CC-BY (коммерчески безопасно)")
        self.chk_lic.setChecked(True)
        opt.addWidget(self.chk_online)
        opt.addWidget(self.chk_lic)
        opt.addStretch()
        self.root.addLayout(opt)

    def search(self):
        try:
            from agents import sample_hunter

            r = sample_hunter.hunt(
                self.q.text().strip(),
                max_results=15,
                allow_online=self.chk_online.isChecked(),
                license_filter=self.chk_lic.isChecked(),
            )
            self.local_list.clear()
            self.online_list.clear()
            for it in r.get("local", []):
                self.local_list.addItem(f"[LOCAL] {it['name']} ({it['size_kb']} KB)")
            for it in r.get("online", []):
                self.online_list.addItem(
                    f"[{it['source']}] {it['name']}  <{it['license']}>"
                )
        except Exception as e:
            QMessageBox.warning(self, "Sample Hunter", f"Поиск не удался: {e}")

    def commit(self, recipe):
        recipe["sample_query"] = self.q.text().strip()
        recipe["allow_online_samples"] = self.chk_online.isChecked()
        recipe["license_filter"] = self.chk_lic.isChecked()

    def help_text(self):
        return "Введи что ищешь и нажми «Найти». Двойной клик добавляет сэмпл в проект."


# ============================================================
# Шаг 4: Текст (bilingual + user_lyrics_lines)
# ============================================================
class StepLyrics(StepBase):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1("④ Текст"))
        self.root.addWidget(
            DIM(
                "Куплеты — русский. Хук — короткая английская фраза.\n"
                "МОИ СТРОЧКИ — если впишешь, программа ГАРАНТИРОВАННО добавит их в трек."
            )
        )
        self.own = QTextEdit()
        self.own.setPlaceholderText(
            "Например:\n«ночь горит, Supra летит»\n«money over everything»\n"
            "(RU строки идут в куплеты, EN — в хуки)"
        )
        self.root.addWidget(self.own)
        self.chk_bi = QCheckBox("Двуязычная структура (RU куплеты + EN хуки)")
        self.chk_bi.setChecked(True)
        self.root.addWidget(self.chk_bi)

        row = QHBoxLayout()
        row.addWidget(QLabel("Куплетов:"))
        self.verses = QSpinBox()
        self.verses.setRange(1, 4)
        self.verses.setValue(2)
        row.addWidget(self.verses)
        row.addStretch()
        self.root.addLayout(row)

    def commit(self, recipe):
        recipe["user_lyrics_lines"] = [
            l for l in self.own.toPlainText().splitlines() if l.strip()
        ]
        recipe["bilingual"] = self.chk_bi.isChecked()
        recipe["n_verses"] = int(self.verses.value())

    def help_text(self):
        return "Что впишешь в «Мои строчки» — 100% попадёт в текст. Это твоя мысль, не нейросети."


# ============================================================
# Шаг 5: Голос — ProVoice основной
# ============================================================
class StepVoice(StepBase):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1("⑤ Голос — фундамент трека"))
        self.root.addWidget(
            DIM("Голос делает трек живым. Мы обучаем RVC v2 под тебя — это ФУНДАМЕНТ.")
        )
        self.mode = QComboBox()
        self.mode.addItems(
            [
                "Pro — я пою под бит, RVC полирует (РЕКОМЕНДУЕТСЯ)",
                "Lazy — синтез текста + RVC-переодевание",
                "Off — без вокала (инструментал)",
            ]
        )
        self.mode.setCurrentIndex(0)
        self.root.addWidget(self.mode)

        self.root.addWidget(H2("Voice Vault (твои записи + RVC-модель)"))
        self.vault_info = QLabel("Проверю при заходе на шаг…")
        self.vault_info.setWordWrap(True)
        self.root.addWidget(self.vault_info)

        row = QHBoxLayout()
        b_kar = QPushButton("🎤 Открыть Караоке (записать голос)")
        b_kar.clicked.connect(self.open_karaoke)
        b_tr = QPushButton("🔥 Обучить RVC (фон, 30 мин — 3 ч)")
        b_tr.clicked.connect(self.train_rvc)
        b_night = QPushButton("🌙 Ночной режим (для слабого GPU)")
        b_night.clicked.connect(lambda: self.train_rvc(night=True))
        row.addWidget(b_kar)
        row.addWidget(b_tr)
        row.addWidget(b_night)
        self.root.addLayout(row)

        self.status = QLabel("")
        self.status.setStyleSheet("color:#9a9aa4;")
        self.root.addWidget(self.status)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(2000)

    def enter(self):
        try:
            from modules.voice_convert import vault_summary

            v = vault_summary()
            self.vault_info.setText(
                f"Записей: {v['recordings']}, всего минут: {v['total_minutes']:.1f}, "
                f"покрытие фонем: {v['phoneme_coverage_pct']}%. "
                f"Готово к обучению: {'ДА' if v['ready_for_training'] else 'нет (нужно ≥5 мин)'}.\n"
                f"Не хватает стилей: {', '.join(v['recommended_next_styles'][:3]) or 'все ок'}"
            )
        except Exception as e:
            self.vault_info.setText(f"Voice Vault недоступен: {e}")

    def open_karaoke(self):
        try:
            QMessageBox.information(
                self,
                "Караоке",
                "Модуль karaoke_recorder готов.\n"
                "Записывай фразы по 8 стилям — Voice Vault копит их автоматически.\n"
                "На 5-10 минутах голоса — можно обучать RVC.",
            )
        except Exception as e:
            QMessageBox.warning(self, "Караоке", f"Пока недоступно: {e}")

    def train_rvc(self, night: bool = False):
        try:
            from modules.voice_convert import train_rvc_model

            r = train_rvc_model(voice_name="my_voice", epochs=100, night_mode=night)
            QMessageBox.information(
                self,
                "RVC",
                f"Обучение запущено в фоне.\nБэкенд: {r.get('backend')}, "
                f"форк: {r.get('fork')}, устройство: {r.get('device')}\n"
                f"Эпох: {r.get('epochs')}. Можешь продолжать работать.",
            )
        except Exception as e:
            QMessageBox.warning(self, "RVC", f"Ошибка запуска: {e}")

    def refresh_status(self):
        try:
            from modules.voice_convert import get_training_status

            s = get_training_status("my_voice")
            if s:
                st = s.get("status", "?")
                stage = s.get("stage", "")
                prog = s.get("progress", 0.0)
                self.status.setText(
                    f"[RVC training] {st}  |  {stage}  |  {int(prog*100)}%"
                )
        except Exception:
            pass

    def commit(self, recipe):
        modes = ["pro", "lazy", "off"]
        recipe["voice_mode"] = modes[self.mode.currentIndex()]

    def help_text(self):
        return (
            "Pro-режим: ты сам поёшь под бит, RVC полирует. Основной.\n"
            "Lazy: синтезируем текст → RVC переодевает голос в твой.\n"
            "Обучение RVC идёт в фоне, можно продолжать работать."
        )


# ============================================================
# Шаг 6: Экспертные опции
# ============================================================
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


# ============================================================
# Шаг 7: Запуск + очередь
# ============================================================
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


# ============================================================
# Шаг 8: Результат — 3 кнопки (Пересобрать / Переделать часть / 3 варианта)
# ============================================================
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
                webbrowser.open(f"file://{p}")
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


# ============================================================
# Wizard — главное окно
# ============================================================
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
        self.btn_back = QPushButton("← Назад")
        self.btn_back.clicked.connect(self.back)
        self.btn_next = QPushButton("Далее →")
        self.btn_next.clicked.connect(self.next)
        self.btn_help = QPushButton("❓ Помощь (F1)")
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
        help_menu = mb.addMenu("Помощь")
        a_tour = QAction("Обучающий тур", self)
        a_tour.triggered.connect(self._show_tour)
        help_menu.addAction(a_tour)
        a_about = QAction("О программе", self)
        a_about.triggered.connect(self._about)
        help_menu.addAction(a_about)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.launch_gradio_expert)
        QShortcut(QKeySequence("F1"), self, activated=self.show_help)

        # Onboarding при первом запуске
        self._maybe_onboarding()

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
        time.sleep(2)
        webbrowser.open("http://127.0.0.1:7860")
