# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/gui/wizard_v8_extensions.py`

**Всего строк:** 350

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 205 | 58.6 |
| blank | 46 | 13.1 |
| try_block | 18 | 5.1 |
| def | 17 | 4.9 |
| comment | 15 | 4.3 |
| docstring | 13 | 3.7 |
| import | 12 | 3.4 |
| return | 9 | 2.6 |
| branch | 6 | 1.7 |
| class | 5 | 1.4 |
| loop | 4 | 1.1 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v8] wizard_v8_extensions.py — дополнительные шаги/панели поверх wizard.py v7.
    3 [blank     ] 
    4 [docstring ] Не переписываем wizard.py v7 (сохраняем как есть), а добавляем новые компоненты
    5 [docstring ] как модули, которые wizard может подключить через include().
    6 [blank     ] 
    7 [docstring ] Компоненты:
    8 [docstring ]   • AuthorPickerPanel — выбор автора из референсов или ввод имени, показывает
    9 [docstring ]     какие треки автора уже в корпусе.
   10 [docstring ]   • FemaleBackingPanel — переключатель «Женский бэк на припеве» + предпрослушка.
   11 [docstring ]   • QualityBadge — цветной бейдж режима (FULL / MID / LITE) в шапке.
   12 [docstring ]   • AutoQAResultPanel — панель отчёта Auto QA + кнопка «Пересобрать конкретно».
   13 [docstring ]   • TemplateManagerDialog — окно управления шаблонами треков.
   14 [docstring ]   • RenderQueueDock — док-виджет со списком очереди рендера.
   15 [docstring ] """
   16 [blank     ] 
   17 [import    ] from __future__ import annotations
   18 [blank     ] 
   19 [try_block ] try:
   20 [import    ]     from PySide6.QtCore import Qt, Signal
   21 [import    ]     from PySide6.QtWidgets import (
   22 [code      ]         QCheckBox,
   23 [code      ]         QComboBox,
   24 [code      ]         QDialog,
   25 [code      ]         QFrame,
   26 [code      ]         QGroupBox,
   27 [code      ]         QHBoxLayout,
   28 [code      ]         QHeaderView,
   29 [code      ]         QLabel,
   30 [code      ]         QMessageBox,
   31 [code      ]         QPushButton,
   32 [code      ]         QScrollArea,
   33 [code      ]         QTableWidget,
   34 [code      ]         QTableWidgetItem,
   35 [code      ]         QVBoxLayout,
   36 [code      ]         QWidget,
   37 [code      ]     )
   38 [blank     ] 
   39 [code      ]     PYSIDE_OK = True
   40 [try_block ] except Exception:
   41 [code      ]     PYSIDE_OK = False
   42 [blank     ] 
   43 [blank     ] 
   44 [comment   ] # ============================================================
   45 [comment   ] # AuthorPickerPanel — выбор автора-референса для стиля текстов
   46 [comment   ] # ============================================================
   47 [branch    ] if PYSIDE_OK:
   48 [blank     ] 
   49 [class     ]     class AuthorPickerPanel(QGroupBox):
   50 [code      ]         author_changed = Signal(str)
   51 [blank     ] 
   52 [def       ]         def __init__(self, parent=None):
   53 [code      ]             super().__init__("Автор-референс для текста (стиль)", parent)
   54 [code      ]             lay = QVBoxLayout(self)
   55 [blank     ] 
   56 [code      ]             hint = QLabel(
   57 [code      ]                 "Выбери автора из библиотеки или впиши имя — система найдёт "
   58 [code      ]                 "его треки в интернете и напишет новый текст в его стиле, "
   59 [code      ]                 "сохранив твою тему и слова."
   60 [code      ]             )
   61 [code      ]             hint.setProperty("class", "dim")
   62 [code      ]             hint.setWordWrap(True)
   63 [code      ]             lay.addWidget(hint)
   64 [blank     ] 
   65 [code      ]             row = QHBoxLayout()
   66 [code      ]             self.combo = QComboBox()
   67 [code      ]             self.combo.setEditable(True)
   68 [code      ]             self.combo.setPlaceholderText("Автор (например: Тимати, MORGENSHTERN)")
   69 [code      ]             self.btn_scan = QPushButton("Сканировать библиотеку")
   70 [code      ]             self.btn_fetch = QPushButton("Найти в интернете")
   71 [code      ]             row.addWidget(self.combo, 1)
   72 [code      ]             row.addWidget(self.btn_scan)
   73 [code      ]             row.addWidget(self.btn_fetch)
   74 [code      ]             lay.addLayout(row)
   75 [blank     ] 
   76 [code      ]             self.status = QLabel("")
   77 [code      ]             self.status.setProperty("class", "dim")
   78 [code      ]             lay.addWidget(self.status)
   79 [blank     ] 
   80 [code      ]             self.btn_scan.clicked.connect(self._on_scan)
   81 [code      ]             self.btn_fetch.clicked.connect(self._on_fetch)
   82 [code      ]             self.combo.currentTextChanged.connect(self.author_changed.emit)
   83 [blank     ] 
   84 [code      ]             self._refresh_authors()
   85 [blank     ] 
   86 [def       ]         def _refresh_authors(self):
   87 [try_block ]             try:
   88 [import    ]                 from modules.author_ref_lyrics import list_authors
   89 [blank     ] 
   90 [code      ]                 self.combo.clear()
   91 [code      ]                 self.combo.addItem("(без автора-референса)")
   92 [loop      ]                 for a in list_authors():
   93 [code      ]                     self.combo.addItem(f"{a['name']}  ·  {a['files']} треков")
   94 [try_block ]             except Exception as e:
   95 [code      ]                 self.status.setText(f"Не удалось получить список: {e}")
   96 [blank     ] 
   97 [def       ]         def _on_scan(self):
   98 [try_block ]             try:
   99 [import    ]                 from modules.author_ref_lyrics import scan_library
  100 [blank     ] 
  101 [code      ]                 r = scan_library()
  102 [code      ]                 self.status.setText(
  103 [code      ]                     f"Проиндексировано: аудио {r['audio_ingested']}, "
  104 [code      ]                     f"текстов {r['text_ingested']}"
  105 [code      ]                 )
  106 [code      ]                 self._refresh_authors()
  107 [try_block ]             except Exception as e:
  108 [code      ]                 self.status.setText(f"Ошибка: {e}")
  109 [blank     ] 
  110 [def       ]         def _on_fetch(self):
  111 [code      ]             author = self.combo.currentText().split("·")[0].strip()
  112 [branch    ]             if not author or author.startswith("("):
  113 [code      ]                 self.status.setText("Впиши имя автора.")
  114 [return    ]                 return
  115 [code      ]             self.status.setText(f"Ищу {author} в интернете...")
  116 [try_block ]             try:
  117 [import    ]                 from modules.author_ref_lyrics import fetch_and_ingest_author
  118 [blank     ] 
  119 [code      ]                 r = fetch_and_ingest_author(author, max_tracks=8)
  120 [code      ]                 self.status.setText(
  121 [code      ]                     f"Подтянуто фрагментов: {r.get('ingested', 0)}. "
  122 [code      ]                     "Стилевой профиль обновлён."
  123 [code      ]                 )
  124 [code      ]                 self._refresh_authors()
  125 [try_block ]             except Exception as e:
  126 [code      ]                 self.status.setText(f"Ошибка: {e}")
  127 [blank     ] 
  128 [def       ]         def selected_author(self) -> str:
  129 [code      ]             t = self.combo.currentText()
  130 [branch    ]             if not t or t.startswith("("):
  131 [return    ]                 return ""
  132 [return    ]             return t.split("·")[0].strip()
  133 [blank     ] 
  134 [comment   ]     # ============================================================
  135 [comment   ]     # FemaleBackingPanel
  136 [comment   ]     # ============================================================
  137 [class     ]     class FemaleBackingPanel(QGroupBox):
  138 [def       ]         def __init__(self, parent=None):
  139 [code      ]             super().__init__("Женский бэк-вокал (Silero v4 — Ksenia/Baya)", parent)
  140 [code      ]             lay = QVBoxLayout(self)
  141 [code      ]             self.chk_enable = QCheckBox(
  142 [code      ]                 "Добавить женский подпев на припеве (мягко, микро-октава выше)"
  143 [code      ]             )
  144 [code      ]             lay.addWidget(self.chk_enable)
  145 [blank     ] 
  146 [code      ]             row = QHBoxLayout()
  147 [code      ]             self.combo_placement = QComboBox()
  148 [code      ]             self.combo_placement.addItems(
  149 [code      ]                 [
  150 [code      ]                     "На припеве (стандарт)",
  151 [code      ]                     "На припеве + адлибы между строк",
  152 [code      ]                     "Только адлибы (yeah, uh, mmm)",
  153 [code      ]                     "На всём треке (эксперимент)",
  154 [code      ]                 ]
  155 [code      ]             )
  156 [code      ]             row.addWidget(QLabel("Где:"))
  157 [code      ]             row.addWidget(self.combo_placement, 1)
  158 [code      ]             lay.addLayout(row)
  159 [blank     ] 
  160 [code      ]             self.btn_preview = QPushButton("Превью 2 сек")
  161 [code      ]             self.btn_preview.setObjectName("neon")
  162 [code      ]             lay.addWidget(self.btn_preview)
  163 [code      ]             self.btn_preview.clicked.connect(self._preview)
  164 [blank     ] 
  165 [code      ]             self.status = QLabel("")
  166 [code      ]             self.status.setProperty("class", "dim")
  167 [code      ]             lay.addWidget(self.status)
  168 [blank     ] 
  169 [def       ]         def is_enabled(self) -> bool:
  170 [return    ]             return self.chk_enable.isChecked()
  171 [blank     ] 
  172 [def       ]         def placement(self) -> str:
  173 [return    ]             return {0: "chorus", 1: "chorus_adlibs", 2: "adlibs_only", 3: "everywhere"}[
  174 [code      ]                 self.combo_placement.currentIndex()
  175 [code      ]             ]
  176 [blank     ] 
  177 [def       ]         def _preview(self):
  178 [code      ]             self.status.setText("Синтезирую превью...")
  179 [try_block ]             try:
  180 [import    ]                 from modules.female_backing import synth_female_line
  181 [blank     ] 
  182 [code      ]                 p = synth_female_line("night ride, we don't stop")
  183 [code      ]                 self.status.setText(f"Готово: {p}")
  184 [try_block ]             except Exception as e:
  185 [code      ]                 self.status.setText(f"Ошибка: {e}")
  186 [blank     ] 
  187 [comment   ]     # ============================================================
  188 [comment   ]     # QualityBadge
  189 [comment   ]     # ============================================================
  190 [class     ]     class QualityBadge(QLabel):
  191 [def       ]         def __init__(self, parent=None):
  192 [code      ]             super().__init__(parent)
  193 [code      ]             self.setAlignment(Qt.AlignCenter)
  194 [code      ]             self.setMinimumWidth(90)
  195 [code      ]             self.refresh()
  196 [blank     ] 
  197 [def       ]         def refresh(self):
  198 [try_block ]             try:
  199 [import    ]                 from app.core.hw_autodetect import detect
  200 [blank     ] 
  201 [code      ]                 p = detect()
  202 [code      ]                 mode = p.get("mode", "lite").upper()
  203 [try_block ]             except Exception:
  204 [code      ]                 mode = "?"
  205 [code      ]             color = {"FULL": "#3ecf8e", "MID": "#ffb020", "LITE": "#ff5573"}.get(
  206 [code      ]                 mode, "#888"
  207 [code      ]             )
  208 [code      ]             self.setText(f"HW: {mode}")
  209 [code      ]             self.setStyleSheet(
  210 [code      ]                 f"padding:4px 10px; border-radius:8px; "
  211 [code      ]                 f"background:{color}22; color:{color}; "
  212 [code      ]                 f"border:1px solid {color}; font-weight:700;"
  213 [code      ]             )
  214 [blank     ] 
  215 [comment   ]     # ============================================================
  216 [comment   ]     # AutoQAResultPanel
  217 [comment   ]     # ============================================================
  218 [class     ]     class AutoQAResultPanel(QGroupBox):
  219 [code      ]         rebuild_requested = Signal(list)  # список targets
  220 [blank     ] 
  221 [def       ]         def __init__(self, parent=None):
  222 [code      ]             super().__init__("Auto QA — сам проверю трек как человек", parent)
  223 [code      ]             self.lay = QVBoxLayout(self)
  224 [code      ]             self.verdict_lbl = QLabel("Ещё не проверено.")
  225 [code      ]             self.verdict_lbl.setObjectName("H2")
  226 [code      ]             self.lay.addWidget(self.verdict_lbl)
  227 [code      ]             self.actions_area = QScrollArea()
  228 [code      ]             self.actions_area.setWidgetResizable(True)
  229 [code      ]             self.actions_holder = QWidget()
  230 [code      ]             self.actions_lay = QVBoxLayout(self.actions_holder)
  231 [code      ]             self.actions_area.setWidget(self.actions_holder)
  232 [code      ]             self.lay.addWidget(self.actions_area, 1)
  233 [blank     ] 
  234 [def       ]         def set_report(self, report: dict):
  235 [loop      ]             for i in reversed(range(self.actions_lay.count())):
  236 [code      ]                 w = self.actions_lay.itemAt(i).widget()
  237 [branch    ]                 if w:
  238 [code      ]                     w.deleteLater()
  239 [blank     ] 
  240 [code      ]             verdict = report.get("verdict_text", "—")
  241 [code      ]             color = {
  242 [code      ]                 "release": "#3ecf8e",
  243 [code      ]                 "patch": "#ffb020",
  244 [code      ]                 "rebuild": "#ff5573",
  245 [code      ]             }.get(report.get("verdict"), "#888")
  246 [code      ]             self.verdict_lbl.setText(verdict)
  247 [code      ]             self.verdict_lbl.setStyleSheet(f"color:{color}; font-weight:700;")
  248 [blank     ] 
  249 [loop      ]             for a in report.get("actions", []):
  250 [code      ]                 box = QFrame()
  251 [code      ]                 box.setStyleSheet(
  252 [code      ]                     "background:#1c2130; border:1px solid #232838; "
  253 [code      ]                     "border-radius:8px; padding:8px;"
  254 [code      ]                 )
  255 [code      ]                 bl = QVBoxLayout(box)
  256 [code      ]                 bl.addWidget(QLabel(f"⚠ {a.get('target', '?').upper()}"))
  257 [code      ]                 r = QLabel(f"Причина: {a.get('reason', '')}")
  258 [code      ]                 r.setProperty("class", "dim")
  259 [code      ]                 r.setWordWrap(True)
  260 [code      ]                 bl.addWidget(r)
  261 [code      ]                 f = QLabel(f"Что сделаем: {a.get('fix', '')}")
  262 [code      ]                 f.setWordWrap(True)
  263 [code      ]                 bl.addWidget(f)
  264 [code      ]                 btn = QPushButton(f"Пересобрать {a.get('target')}")
  265 [code      ]                 btn.setObjectName("primary")
  266 [code      ]                 btn.clicked.connect(
  267 [code      ]                     lambda _, t=a.get("target"): self.rebuild_requested.emit([t])
  268 [code      ]                 )
  269 [code      ]                 bl.addWidget(btn)
  270 [code      ]                 self.actions_lay.addWidget(box)
  271 [code      ]             self.actions_lay.addStretch()
  272 [blank     ] 
  273 [comment   ]     # ============================================================
  274 [comment   ]     # TemplateManagerDialog
  275 [comment   ]     # ============================================================
  276 [class     ]     class TemplateManagerDialog(QDialog):
  277 [def       ]         def __init__(self, parent=None):
  278 [code      ]             super().__init__(parent)
  279 [code      ]             self.setWindowTitle("Шаблоны треков")
  280 [code      ]             self.resize(680, 460)
  281 [code      ]             lay = QVBoxLayout(self)
  282 [code      ]             self.tbl = QTableWidget(0, 4)
  283 [code      ]             self.tbl.setHorizontalHeaderLabels(["Название", "Тема", "Длина", "Создан"])
  284 [code      ]             self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
  285 [code      ]             lay.addWidget(self.tbl, 1)
  286 [blank     ] 
  287 [code      ]             row = QHBoxLayout()
  288 [code      ]             self.btn_run = QPushButton("Запустить")
  289 [code      ]             self.btn_run.setObjectName("primary")
  290 [code      ]             self.btn_delete = QPushButton("Удалить")
  291 [code      ]             self.btn_delete.setObjectName("ghost")
  292 [code      ]             self.btn_close = QPushButton("Закрыть")
  293 [code      ]             row.addWidget(self.btn_run)
  294 [code      ]             row.addWidget(self.btn_delete)
  295 [code      ]             row.addStretch()
  296 [code      ]             row.addWidget(self.btn_close)
  297 [code      ]             lay.addLayout(row)
  298 [code      ]             self.btn_close.clicked.connect(self.accept)
  299 [code      ]             self.btn_delete.clicked.connect(self._delete)
  300 [code      ]             self._reload()
  301 [blank     ] 
  302 [def       ]         def _reload(self):
  303 [try_block ]             try:
  304 [import    ]                 from modules.track_templates import list_templates
  305 [blank     ] 
  306 [code      ]                 items = list_templates()
  307 [try_block ]             except Exception:
  308 [code      ]                 items = []
  309 [code      ]             self.tbl.setRowCount(len(items))
  310 [code      ]             self._ids = []
  311 [loop      ]             for r, t in enumerate(items):
  312 [code      ]                 self._ids.append(t["id"])
  313 [code      ]                 self.tbl.setItem(r, 0, QTableWidgetItem(t.get("name", "?")))
  314 [code      ]                 self.tbl.setItem(r, 1, QTableWidgetItem(t["recipe"].get("theme", "")))
  315 [code      ]                 self.tbl.setItem(
  316 [code      ]                     r, 2, QTableWidgetItem(str(t["recipe"].get("duration_sec", 150)))
  317 [code      ]                 )
  318 [import    ]                 import time
  319 [blank     ] 
  320 [code      ]                 ts = t.get("created_at", 0)
  321 [code      ]                 self.tbl.setItem(
  322 [code      ]                     r,
  323 [code      ]                     3,
  324 [code      ]                     QTableWidgetItem(
  325 [code      ]                         time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
  326 [code      ]                     ),
  327 [code      ]                 )
  328 [blank     ] 
  329 [def       ]         def _delete(self):
  330 [code      ]             row = self.tbl.currentRow()
  331 [branch    ]             if row < 0:
  332 [return    ]                 return
  333 [try_block ]             try:
  334 [import    ]                 from modules.track_templates import delete_template
  335 [blank     ] 
  336 [code      ]                 delete_template(self._ids[row])
  337 [code      ]                 self._reload()
  338 [try_block ]             except Exception as e:
  339 [code      ]                 QMessageBox.warning(self, "Ошибка", str(e))
  340 [blank     ] 
  341 [def       ]         def selected_template(self) -> dict | None:
  342 [code      ]             row = self.tbl.currentRow()
  343 [branch    ]             if row < 0:
  344 [return    ]                 return None
  345 [try_block ]             try:
  346 [import    ]                 from modules.track_templates import load_template
  347 [blank     ] 
  348 [return    ]                 return load_template(self._ids[row])
  349 [try_block ]             except Exception:
  350 [return    ]                 return None
```