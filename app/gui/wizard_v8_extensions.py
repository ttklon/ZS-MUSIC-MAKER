"""
[v8] wizard_v8_extensions.py — дополнительные шаги/панели поверх wizard.py v7.

Не переписываем wizard.py v7 (сохраняем как есть), а добавляем новые компоненты
как модули, которые wizard может подключить через include().

Компоненты:
  • AuthorPickerPanel — выбор автора из референсов или ввод имени, показывает
    какие треки автора уже в корпусе.
  • FemaleBackingPanel — переключатель «Женский бэк на припеве» + предпрослушка.
  • QualityBadge — цветной бейдж режима (FULL / MID / LITE) в шапке.
  • AutoQAResultPanel — панель отчёта Auto QA + кнопка «Пересобрать конкретно».
  • TemplateManagerDialog — окно управления шаблонами треков.
  • RenderQueueDock — док-виджет со списком очереди рендера.
"""

from __future__ import annotations

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    PYSIDE_OK = True
except Exception:
    PYSIDE_OK = False


# ============================================================
# AuthorPickerPanel — выбор автора-референса для стиля текстов
# ============================================================
if PYSIDE_OK:

    class AuthorPickerPanel(QGroupBox):
        author_changed = Signal(str)

        def __init__(self, parent=None):
            super().__init__("Автор-референс для текста (стиль)", parent)
            lay = QVBoxLayout(self)

            hint = QLabel(
                "Выбери автора из библиотеки или впиши имя — система найдёт "
                "его треки в интернете и напишет новый текст в его стиле, "
                "сохранив твою тему и слова."
            )
            hint.setProperty("class", "dim")
            hint.setWordWrap(True)
            lay.addWidget(hint)

            row = QHBoxLayout()
            self.combo = QComboBox()
            self.combo.setEditable(True)
            self.combo.setPlaceholderText("Автор (например: Тимати, MORGENSHTERN)")
            self.btn_scan = QPushButton("Сканировать библиотеку")
            self.btn_fetch = QPushButton("Найти в интернете")
            row.addWidget(self.combo, 1)
            row.addWidget(self.btn_scan)
            row.addWidget(self.btn_fetch)
            lay.addLayout(row)

            self.status = QLabel("")
            self.status.setProperty("class", "dim")
            lay.addWidget(self.status)

            self.btn_scan.clicked.connect(self._on_scan)
            self.btn_fetch.clicked.connect(self._on_fetch)
            self.combo.currentTextChanged.connect(self.author_changed.emit)

            self._refresh_authors()

        def _refresh_authors(self):
            try:
                from modules.author_ref_lyrics import list_authors

                self.combo.clear()
                self.combo.addItem("(без автора-референса)")
                for a in list_authors():
                    self.combo.addItem(f"{a['name']}  ·  {a['files']} треков")
            except Exception as e:
                self.status.setText(f"Не удалось получить список: {e}")

        def _on_scan(self):
            try:
                from modules.author_ref_lyrics import scan_library

                r = scan_library()
                self.status.setText(
                    f"Проиндексировано: аудио {r['audio_ingested']}, "
                    f"текстов {r['text_ingested']}"
                )
                self._refresh_authors()
            except Exception as e:
                self.status.setText(f"Ошибка: {e}")

        def _on_fetch(self):
            author = self.combo.currentText().split("·")[0].strip()
            if not author or author.startswith("("):
                self.status.setText("Впиши имя автора.")
                return
            self.status.setText(f"Ищу {author} в интернете...")
            try:
                from modules.author_ref_lyrics import fetch_and_ingest_author

                r = fetch_and_ingest_author(author, max_tracks=8)
                self.status.setText(
                    f"Подтянуто фрагментов: {r.get('ingested', 0)}. "
                    "Стилевой профиль обновлён."
                )
                self._refresh_authors()
            except Exception as e:
                self.status.setText(f"Ошибка: {e}")

        def selected_author(self) -> str:
            t = self.combo.currentText()
            if not t or t.startswith("("):
                return ""
            return t.split("·")[0].strip()

    # ============================================================
    # FemaleBackingPanel
    # ============================================================
    class FemaleBackingPanel(QGroupBox):
        def __init__(self, parent=None):
            super().__init__("Женский бэк-вокал (Silero v4 — Ksenia/Baya)", parent)
            lay = QVBoxLayout(self)
            self.chk_enable = QCheckBox(
                "Добавить женский подпев на припеве (мягко, микро-октава выше)"
            )
            lay.addWidget(self.chk_enable)

            row = QHBoxLayout()
            self.combo_placement = QComboBox()
            self.combo_placement.addItems(
                [
                    "На припеве (стандарт)",
                    "На припеве + адлибы между строк",
                    "Только адлибы (yeah, uh, mmm)",
                    "На всём треке (эксперимент)",
                ]
            )
            row.addWidget(QLabel("Где:"))
            row.addWidget(self.combo_placement, 1)
            lay.addLayout(row)

            self.btn_preview = QPushButton("Превью 2 сек")
            self.btn_preview.setObjectName("neon")
            lay.addWidget(self.btn_preview)
            self.btn_preview.clicked.connect(self._preview)

            self.status = QLabel("")
            self.status.setProperty("class", "dim")
            lay.addWidget(self.status)

        def is_enabled(self) -> bool:
            return self.chk_enable.isChecked()

        def placement(self) -> str:
            return {0: "chorus", 1: "chorus_adlibs", 2: "adlibs_only", 3: "everywhere"}[
                self.combo_placement.currentIndex()
            ]

        def _preview(self):
            self.status.setText("Синтезирую превью...")
            try:
                from modules.female_backing import synth_female_line

                p = synth_female_line("night ride, we don't stop")
                self.status.setText(f"Готово: {p}")
            except Exception as e:
                self.status.setText(f"Ошибка: {e}")

    # ============================================================
    # QualityBadge
    # ============================================================
    class QualityBadge(QLabel):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setAlignment(Qt.AlignCenter)
            self.setMinimumWidth(90)
            self.refresh()

        def refresh(self):
            try:
                from app.core.hw_autodetect import detect

                p = detect()
                mode = p.get("mode", "lite").upper()
            except Exception:
                mode = "?"
            color = {"FULL": "#3ecf8e", "MID": "#ffb020", "LITE": "#ff5573"}.get(
                mode, "#888"
            )
            self.setText(f"HW: {mode}")
            self.setStyleSheet(
                f"padding:4px 10px; border-radius:8px; "
                f"background:{color}22; color:{color}; "
                f"border:1px solid {color}; font-weight:700;"
            )

    # ============================================================
    # AutoQAResultPanel
    # ============================================================
    class AutoQAResultPanel(QGroupBox):
        rebuild_requested = Signal(list)  # список targets

        def __init__(self, parent=None):
            super().__init__("Auto QA — сам проверю трек как человек", parent)
            self.lay = QVBoxLayout(self)
            self.verdict_lbl = QLabel("Ещё не проверено.")
            self.verdict_lbl.setObjectName("H2")
            self.lay.addWidget(self.verdict_lbl)
            self.actions_area = QScrollArea()
            self.actions_area.setWidgetResizable(True)
            self.actions_holder = QWidget()
            self.actions_lay = QVBoxLayout(self.actions_holder)
            self.actions_area.setWidget(self.actions_holder)
            self.lay.addWidget(self.actions_area, 1)

        def set_report(self, report: dict):
            for i in reversed(range(self.actions_lay.count())):
                w = self.actions_lay.itemAt(i).widget()
                if w:
                    w.deleteLater()

            verdict = report.get("verdict_text", "—")
            color = {
                "release": "#3ecf8e",
                "patch": "#ffb020",
                "rebuild": "#ff5573",
            }.get(report.get("verdict"), "#888")
            self.verdict_lbl.setText(verdict)
            self.verdict_lbl.setStyleSheet(f"color:{color}; font-weight:700;")

            for a in report.get("actions", []):
                box = QFrame()
                box.setStyleSheet(
                    "background:#1c2130; border:1px solid #232838; "
                    "border-radius:8px; padding:8px;"
                )
                bl = QVBoxLayout(box)
                bl.addWidget(QLabel(f"⚠ {a.get('target', '?').upper()}"))
                r = QLabel(f"Причина: {a.get('reason', '')}")
                r.setProperty("class", "dim")
                r.setWordWrap(True)
                bl.addWidget(r)
                f = QLabel(f"Что сделаем: {a.get('fix', '')}")
                f.setWordWrap(True)
                bl.addWidget(f)
                btn = QPushButton(f"Пересобрать {a.get('target')}")
                btn.setObjectName("primary")
                btn.clicked.connect(
                    lambda _, t=a.get("target"): self.rebuild_requested.emit([t])
                )
                bl.addWidget(btn)
                self.actions_lay.addWidget(box)
            self.actions_lay.addStretch()

    # ============================================================
    # TemplateManagerDialog
    # ============================================================
    class TemplateManagerDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Шаблоны треков")
            self.resize(680, 460)
            lay = QVBoxLayout(self)
            self.tbl = QTableWidget(0, 4)
            self.tbl.setHorizontalHeaderLabels(["Название", "Тема", "Длина", "Создан"])
            self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            lay.addWidget(self.tbl, 1)

            row = QHBoxLayout()
            self.btn_run = QPushButton("Запустить")
            self.btn_run.setObjectName("primary")
            self.btn_delete = QPushButton("Удалить")
            self.btn_delete.setObjectName("ghost")
            self.btn_close = QPushButton("Закрыть")
            row.addWidget(self.btn_run)
            row.addWidget(self.btn_delete)
            row.addStretch()
            row.addWidget(self.btn_close)
            lay.addLayout(row)
            self.btn_close.clicked.connect(self.accept)
            self.btn_delete.clicked.connect(self._delete)
            self._reload()

        def _reload(self):
            try:
                from modules.track_templates import list_templates

                items = list_templates()
            except Exception:
                items = []
            self.tbl.setRowCount(len(items))
            self._ids = []
            for r, t in enumerate(items):
                self._ids.append(t["id"])
                self.tbl.setItem(r, 0, QTableWidgetItem(t.get("name", "?")))
                self.tbl.setItem(r, 1, QTableWidgetItem(t["recipe"].get("theme", "")))
                self.tbl.setItem(
                    r, 2, QTableWidgetItem(str(t["recipe"].get("duration_sec", 150)))
                )
                import time

                ts = t.get("created_at", 0)
                self.tbl.setItem(
                    r,
                    3,
                    QTableWidgetItem(
                        time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
                    ),
                )

        def _delete(self):
            row = self.tbl.currentRow()
            if row < 0:
                return
            try:
                from modules.track_templates import delete_template

                delete_template(self._ids[row])
                self._reload()
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", str(e))

        def selected_template(self) -> dict | None:
            row = self.tbl.currentRow()
            if row < 0:
                return None
            try:
                from modules.track_templates import load_template

                return load_template(self._ids[row])
            except Exception:
                return None
