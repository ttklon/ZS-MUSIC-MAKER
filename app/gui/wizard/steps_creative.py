# -*- coding: utf-8 -*-
"""
app/gui/wizard/steps_creative.py — творческие шаги: жанровый пресет, браузер сэмплов, текст, голос.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QSpinBox, QSplitter, QTextEdit, QVBoxLayout

from app.gui.wizard.ui import DIM, H1, H2, StepBase

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
            logging.getLogger(__name__).debug("ignored exception", exc_info=True)
    def commit(self, recipe):
        modes = ["pro", "lazy", "off"]
        recipe["voice_mode"] = modes[self.mode.currentIndex()]
    def help_text(self):
        return (
            "Pro-режим: ты сам поёшь под бит, RVC полирует. Основной.\n"
            "Lazy: синтезируем текст → RVC переодевает голос в твой.\n"
            "Обучение RVC идёт в фоне, можно продолжать работать."
        )
