# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/gui/wizard.py`

**Всего строк:** 1042

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 659 | 63.2 |
| blank | 131 | 12.6 |
| def | 63 | 6.0 |
| comment | 53 | 5.1 |
| branch | 30 | 2.9 |
| try_block | 24 | 2.3 |
| return | 23 | 2.2 |
| import | 22 | 2.1 |
| docstring | 14 | 1.3 |
| loop | 12 | 1.2 |
| class | 11 | 1.1 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] Wizard — единое окно, 9 шагов, тёмная тема.
    3 [blank     ] 
    4 [docstring ] Изменения относительно v6:
    5 [docstring ]   • Шаг 0 — ArtistName (при первом запуске, из user_profile.first_run)
    6 [docstring ]   • Ползунок duration: 90-300 сек, default 150 (2:30) — из ТЗ 20.2 вопрос 5
    7 [docstring ]   • Переключатель QualityMode: fast / quality / max — ТЗ 20.2 вопрос 29
    8 [docstring ]   • Sample Browser split-view: local list + online results
    9 [docstring ]   • Три кнопки на StepResult: 🔁 Пересобрать всё / ✂️ Переделать часть / 🎲 3 варианта
   10 [docstring ]   • Voice Mode: ProVoice — основной, Lazy — второстепенный (ТЗ 20.1)
   11 [docstring ]   • Queue-режим: 5+ проектов на ночь (ТЗ 20.2 вопрос 7)
   12 [docstring ]   • Onboarding при первом запуске (Scriptable Tour)
   13 [docstring ]   • Меню «Помощь» с F1 на каждом шаге
   14 [docstring ] """
   15 [blank     ] 
   16 [import    ] from __future__ import annotations
   17 [blank     ] 
   18 [import    ] import os
   19 [import    ] import sys
   20 [import    ] import threading
   21 [import    ] import time
   22 [import    ] import webbrowser
   23 [import    ] from pathlib import Path
   24 [blank     ] 
   25 [import    ] from PySide6.QtCore import Qt, QTimer
   26 [import    ] from PySide6.QtGui import (
   27 [code      ]     QAction,
   28 [code      ]     QDragEnterEvent,
   29 [code      ]     QDropEvent,
   30 [code      ]     QKeySequence,
   31 [code      ]     QShortcut,
   32 [code      ] )
   33 [import    ] from PySide6.QtWidgets import (
   34 [code      ]     QCheckBox,
   35 [code      ]     QComboBox,
   36 [code      ]     QFileDialog,
   37 [code      ]     QFrame,
   38 [code      ]     QGroupBox,
   39 [code      ]     QHBoxLayout,
   40 [code      ]     QInputDialog,
   41 [code      ]     QLabel,
   42 [code      ]     QLineEdit,
   43 [code      ]     QListWidget,
   44 [code      ]     QMainWindow,
   45 [code      ]     QMessageBox,
   46 [code      ]     QProgressBar,
   47 [code      ]     QPushButton,
   48 [code      ]     QSlider,
   49 [code      ]     QSpinBox,
   50 [code      ]     QSplitter,
   51 [code      ]     QStackedWidget,
   52 [code      ]     QTextEdit,
   53 [code      ]     QVBoxLayout,
   54 [code      ]     QWidget,
   55 [code      ] )
   56 [blank     ] 
   57 [code      ] ROOT = Path(__file__).resolve().parents[2]
   58 [code      ] DATA = ROOT / "data"
   59 [blank     ] 
   60 [blank     ] 
   61 [comment   ] # ============================================================
   62 [comment   ] #   утилиты
   63 [comment   ] # ============================================================
   64 [def       ] def H1(text):
   65 [code      ]     l = QLabel(text)
   66 [code      ]     l.setObjectName("H1")
   67 [return    ]     return l
   68 [blank     ] 
   69 [blank     ] 
   70 [def       ] def H2(text):
   71 [code      ]     l = QLabel(text)
   72 [code      ]     l.setObjectName("H2")
   73 [return    ]     return l
   74 [blank     ] 
   75 [blank     ] 
   76 [def       ] def DIM(text):
   77 [code      ]     l = QLabel(text)
   78 [code      ]     l.setProperty("class", "dim")
   79 [code      ]     l.setStyleSheet("color:#9a9aa4;")
   80 [code      ]     l.setWordWrap(True)
   81 [return    ]     return l
   82 [blank     ] 
   83 [blank     ] 
   84 [def       ] def HR():
   85 [code      ]     line = QFrame()
   86 [code      ]     line.setFrameShape(QFrame.HLine)
   87 [code      ]     line.setStyleSheet("color:#2a2a34;")
   88 [return    ]     return line
   89 [blank     ] 
   90 [blank     ] 
   91 [class     ] class StepBase(QWidget):
   92 [def       ]     def __init__(self, wizard):
   93 [code      ]         super().__init__()
   94 [code      ]         self.wizard = wizard
   95 [code      ]         self.root = QVBoxLayout(self)
   96 [code      ]         self.root.setContentsMargins(30, 20, 30, 20)
   97 [code      ]         self.root.setSpacing(12)
   98 [blank     ] 
   99 [def       ]     def enter(self):
  100 [code      ]         pass
  101 [blank     ] 
  102 [def       ]     def commit(self, recipe: dict):
  103 [code      ]         pass
  104 [blank     ] 
  105 [def       ]     def help_text(self) -> str:
  106 [return    ]         return ""
  107 [blank     ] 
  108 [blank     ] 
  109 [comment   ] # ============================================================
  110 [comment   ] # Шаг 0: имя артиста (только при первом запуске)
  111 [comment   ] # ============================================================
  112 [class     ] class StepArtist(StepBase):
  113 [def       ]     def __init__(self, wizard):
  114 [code      ]         super().__init__(wizard)
  115 [code      ]         self.root.addWidget(H1("🎤 Как тебя зовут?"))
  116 [code      ]         self.root.addWidget(
  117 [code      ]             DIM(
  118 [code      ]                 "Это твоё артист-имя. Оно попадёт в ID3-теги всех твоих треков "
  119 [code      ]                 "(Spotify, Yandex, TikTok — везде будет видно именно его). "
  120 [code      ]                 "Можно поменять позже в меню Профиль."
  121 [code      ]             )
  122 [code      ]         )
  123 [code      ]         self.name = QLineEdit()
  124 [code      ]         self.name.setPlaceholderText("Например: ZS ARTIST, MC Night, Supra Kid…")
  125 [code      ]         self.name.setStyleSheet("font-size:18px; padding:12px;")
  126 [code      ]         self.root.addWidget(self.name)
  127 [code      ]         self.root.addStretch()
  128 [blank     ] 
  129 [def       ]     def enter(self):
  130 [try_block ]         try:
  131 [import    ]             from modules.user_profile import get_artist_name
  132 [blank     ] 
  133 [code      ]             self.name.setText(get_artist_name())
  134 [try_block ]         except Exception:
  135 [code      ]             pass
  136 [blank     ] 
  137 [def       ]     def commit(self, recipe):
  138 [try_block ]         try:
  139 [import    ]             from modules.user_profile import set_artist_name
  140 [blank     ] 
  141 [code      ]             set_artist_name(self.name.text().strip() or "ZSMM Artist")
  142 [try_block ]         except Exception:
  143 [code      ]             pass
  144 [code      ]         recipe["artist_name"] = self.name.text().strip() or "ZSMM Artist"
  145 [blank     ] 
  146 [def       ]     def help_text(self):
  147 [return    ]         return "Артист-имя — то, под которым ты выпускаешь треки."
  148 [blank     ] 
  149 [blank     ] 
  150 [comment   ] # ============================================================
  151 [comment   ] # Шаг 1: референсы + тема + длительность
  152 [comment   ] # ============================================================
  153 [class     ] class StepReferences(StepBase):
  154 [def       ]     def __init__(self, wizard):
  155 [code      ]         super().__init__(wizard)
  156 [code      ]         self.root.addWidget(H1("① Референсы"))
  157 [code      ]         self.root.addWidget(
  158 [code      ]             DIM(
  159 [code      ]                 "Перетащи 1–7 треков (mp3/wav). Первый — главный. "
  160 [code      ]                 "Мы НЕ КОПИРУЕМ их — вытянем только BPM, ритм, вайб."
  161 [code      ]             )
  162 [code      ]         )
  163 [code      ]         self.list = QListWidget()
  164 [code      ]         self.list.setAcceptDrops(True)
  165 [code      ]         self.list.setDragDropMode(QListWidget.InternalMove)
  166 [code      ]         self.list.setMinimumHeight(180)
  167 [code      ]         self.root.addWidget(self.list)
  168 [blank     ] 
  169 [code      ]         br = QHBoxLayout()
  170 [code      ]         b_add = QPushButton("＋ Добавить файлы")
  171 [code      ]         b_add.clicked.connect(self.pick_files)
  172 [code      ]         b_clr = QPushButton("Очистить")
  173 [code      ]         b_clr.clicked.connect(self.list.clear)
  174 [code      ]         br.addWidget(b_add)
  175 [code      ]         br.addWidget(b_clr)
  176 [code      ]         br.addStretch()
  177 [code      ]         self.root.addLayout(br)
  178 [blank     ] 
  179 [code      ]         self.root.addWidget(HR())
  180 [code      ]         self.root.addWidget(H2("Тема трека / моя тема (обязательно попадёт в текст)"))
  181 [code      ]         self.theme = QLineEdit()
  182 [code      ]         self.theme.setPlaceholderText(
  183 [code      ]             "лето, тачки, деньги, Турция, Supra, вечер, Стамбул…"
  184 [code      ]         )
  185 [code      ]         self.root.addWidget(self.theme)
  186 [blank     ] 
  187 [comment   ]         # Duration — из ТЗ 20.2 вопрос 5: 1:30 — 3:30+, default 2:30
  188 [code      ]         self.root.addWidget(H2("Длительность (сек): 90 — 300, по умолчанию 150 (2:30)"))
  189 [code      ]         dur_row = QHBoxLayout()
  190 [code      ]         self.dur = QSlider(Qt.Horizontal)
  191 [code      ]         self.dur.setRange(90, 300)
  192 [code      ]         self.dur.setValue(150)
  193 [code      ]         self.dur.setSingleStep(1)
  194 [code      ]         self.dur.setPageStep(10)
  195 [code      ]         self.dur_label = QLabel("2:30")
  196 [code      ]         self.dur.valueChanged.connect(
  197 [code      ]             lambda v: self.dur_label.setText(f"{v//60}:{v%60:02d}  ({v} сек)")
  198 [code      ]         )
  199 [code      ]         dur_row.addWidget(self.dur, 1)
  200 [code      ]         dur_row.addWidget(self.dur_label)
  201 [code      ]         self.root.addLayout(dur_row)
  202 [code      ]         self.setAcceptDrops(True)
  203 [blank     ] 
  204 [def       ]     def dragEnterEvent(self, e: QDragEnterEvent):
  205 [branch    ]         if e.mimeData().hasUrls():
  206 [code      ]             e.acceptProposedAction()
  207 [blank     ] 
  208 [def       ]     def dropEvent(self, e: QDropEvent):
  209 [loop      ]         for u in e.mimeData().urls():
  210 [code      ]             p = u.toLocalFile()
  211 [branch    ]             if p and p.lower().endswith((".mp3", ".wav", ".flac", ".m4a", ".ogg")):
  212 [code      ]                 self.list.addItem(p)
  213 [blank     ] 
  214 [def       ]     def pick_files(self):
  215 [code      ]         files, _ = QFileDialog.getOpenFileNames(
  216 [code      ]             self, "Выбери референсы", "", "Audio (*.mp3 *.wav *.flac *.m4a *.ogg)"
  217 [code      ]         )
  218 [loop      ]         for f in files:
  219 [code      ]             self.list.addItem(f)
  220 [blank     ] 
  221 [def       ]     def commit(self, recipe):
  222 [code      ]         recipe["references"] = [
  223 [code      ]             self.list.item(i).text() for i in range(self.list.count())
  224 [code      ]         ]
  225 [code      ]         recipe["theme"] = self.theme.text().strip() or "лето, тачки, деньги"
  226 [code      ]         recipe["duration_sec"] = int(self.dur.value())
  227 [blank     ] 
  228 [def       ]     def help_text(self):
  229 [return    ]         return (
  230 [code      ]             "Референсы — что тебе нравится по звуку. "
  231 [code      ]             "1-7 файлов, перетаскивай прямо в окно. "
  232 [code      ]             "Если референсов нет — иди на шаг ② и выбери пресет."
  233 [code      ]         )
  234 [blank     ] 
  235 [blank     ] 
  236 [comment   ] # ============================================================
  237 [comment   ] # Шаг 2: стиль (пресет) + режим генерации + стенды
  238 [comment   ] # ============================================================
  239 [class     ] class StepPreset(StepBase):
  240 [def       ]     def __init__(self, wizard):
  241 [code      ]         super().__init__(wizard)
  242 [code      ]         self.root.addWidget(H1("② Стиль и режим"))
  243 [blank     ] 
  244 [comment   ]         # Пресет
  245 [code      ]         self.root.addWidget(DIM("Быстрый старт без референсов — выбери пресет."))
  246 [code      ]         self.combo = QComboBox()
  247 [code      ]         self.combo.addItems(
  248 [code      ]             [
  249 [code      ]                 "Из референсов (по умолчанию)",
  250 [code      ]                 "tamam_like — восточный фонк-эдит",
  251 [code      ]                 "brazilian_phonk — агрессия, drift",
  252 [code      ]                 "hyperpop_edit — TikTok-хайп",
  253 [code      ]                 "lofi_drift — вечерний драйв",
  254 [code      ]                 "trap_ru — русский трэп",
  255 [code      ]             ]
  256 [code      ]         )
  257 [code      ]         self.root.addWidget(self.combo)
  258 [blank     ] 
  259 [comment   ]         # Режим генерации — из ТЗ 20.2 вопрос 29
  260 [code      ]         self.root.addWidget(H2("Режим генерации"))
  261 [code      ]         self.root.addWidget(
  262 [code      ]             DIM(
  263 [code      ]                 "Быстрый (10-15 мин): для черновиков и проб.\n"
  264 [code      ]                 "Качественный (30-60 мин): по умолчанию, для релизов.\n"
  265 [code      ]                 "Максимальный (1-3 часа): максимум качества, для главных треков."
  266 [code      ]             )
  267 [code      ]         )
  268 [code      ]         self.mode = QComboBox()
  269 [code      ]         self.mode.addItems(
  270 [code      ]             ["Быстрый (10-15 мин)", "Качественный (30-60 мин)", "Максимальный (1-3 ч)"]
  271 [code      ]         )
  272 [code      ]         self.mode.setCurrentIndex(1)  # quality default
  273 [code      ]         self.root.addWidget(self.mode)
  274 [blank     ] 
  275 [comment   ]         # Экстра-промпт
  276 [code      ]         self.root.addWidget(H2("Экстра-промт (опционально)"))
  277 [code      ]         self.extra = QTextEdit()
  278 [code      ]         self.extra.setPlaceholderText(
  279 [code      ]             "«больше 808 в припеве, Silvia в тумане, дрифт-вайб»."
  280 [code      ]         )
  281 [code      ]         self.extra.setMaximumHeight(100)
  282 [code      ]         self.root.addWidget(self.extra)
  283 [blank     ] 
  284 [comment   ]         # Стенды прослушивания
  285 [code      ]         gb = QGroupBox("Стенды прослушивания (три мастера)")
  286 [code      ]         gl = QHBoxLayout(gb)
  287 [code      ]         self.chk_car = QCheckBox("🚗 Автомобиль")
  288 [code      ]         self.chk_car.setChecked(True)
  289 [code      ]         self.chk_club = QCheckBox("🎧 Клуб")
  290 [code      ]         self.chk_club.setChecked(True)
  291 [code      ]         self.chk_str = QCheckBox("📱 Стриминг")
  292 [code      ]         self.chk_str.setChecked(True)
  293 [loop      ]         for c in (self.chk_car, self.chk_club, self.chk_str):
  294 [code      ]             gl.addWidget(c)
  295 [code      ]         gl.addStretch()
  296 [code      ]         self.root.addWidget(gb)
  297 [blank     ] 
  298 [def       ]     def commit(self, recipe):
  299 [code      ]         keys = [
  300 [code      ]             None,
  301 [code      ]             "tamam_like",
  302 [code      ]             "brazilian_phonk",
  303 [code      ]             "hyperpop_edit",
  304 [code      ]             "lofi_drift",
  305 [code      ]             "trap_ru",
  306 [code      ]         ]
  307 [code      ]         recipe["preset"] = keys[self.combo.currentIndex()]
  308 [code      ]         modes = ["fast", "quality", "max"]
  309 [code      ]         recipe["quality_mode"] = modes[self.mode.currentIndex()]
  310 [code      ]         recipe["user_extra_prompt"] = self.extra.toPlainText().strip()
  311 [code      ]         recipe["stands"] = [
  312 [code      ]             k
  313 [loop      ]             for k, w in [
  314 [code      ]                 ("car", self.chk_car),
  315 [code      ]                 ("club", self.chk_club),
  316 [code      ]                 ("streaming", self.chk_str),
  317 [code      ]             ]
  318 [branch    ]             if w.isChecked()
  319 [code      ]         ]
  320 [blank     ] 
  321 [def       ]     def help_text(self):
  322 [return    ]         return (
  323 [code      ]             "Пресеты — 5 готовых стилей, если нет референсов. "
  324 [code      ]             "Режим генерации: быстрый (для проб), качественный (по умолчанию), "
  325 [code      ]             "максимальный (для главных релизов, 1-3 часа)."
  326 [code      ]         )
  327 [blank     ] 
  328 [blank     ] 
  329 [comment   ] # ============================================================
  330 [comment   ] # Шаг 3: Sample Browser — split-view local vs online
  331 [comment   ] # ============================================================
  332 [class     ] class StepSamples(StepBase):
  333 [def       ]     def __init__(self, wizard):
  334 [code      ]         super().__init__(wizard)
  335 [code      ]         self.root.addWidget(H1("③ Сэмплы (Sample Browser)"))
  336 [code      ]         self.root.addWidget(
  337 [code      ]             DIM(
  338 [code      ]                 "Слева — твоя локальная библиотека. Справа — интернет-поиск. "
  339 [code      ]                 "Только CC0 / Royalty-Free — коммерчески безопасно."
  340 [code      ]             )
  341 [code      ]         )
  342 [blank     ] 
  343 [comment   ]         # Поиск
  344 [code      ]         top = QHBoxLayout()
  345 [code      ]         self.q = QLineEdit()
  346 [code      ]         self.q.setPlaceholderText("phonk kick, 808 sub, dark pad, cowbell…")
  347 [code      ]         b_search = QPushButton("🔍 Найти")
  348 [code      ]         b_search.clicked.connect(self.search)
  349 [code      ]         top.addWidget(self.q, 1)
  350 [code      ]         top.addWidget(b_search)
  351 [code      ]         self.root.addLayout(top)
  352 [blank     ] 
  353 [comment   ]         # Split view
  354 [code      ]         splitter = QSplitter(Qt.Horizontal)
  355 [comment   ]         # Local
  356 [code      ]         local_box = QGroupBox("Локальная библиотека")
  357 [code      ]         lv = QVBoxLayout(local_box)
  358 [code      ]         self.local_list = QListWidget()
  359 [code      ]         lv.addWidget(self.local_list)
  360 [code      ]         splitter.addWidget(local_box)
  361 [comment   ]         # Online
  362 [code      ]         online_box = QGroupBox("Из интернета (CC0/CC-BY)")
  363 [code      ]         ov = QVBoxLayout(online_box)
  364 [code      ]         self.online_list = QListWidget()
  365 [code      ]         ov.addWidget(self.online_list)
  366 [code      ]         splitter.addWidget(online_box)
  367 [code      ]         splitter.setSizes([1, 1])
  368 [code      ]         self.root.addWidget(splitter, 1)
  369 [blank     ] 
  370 [comment   ]         # Options
  371 [code      ]         opt = QHBoxLayout()
  372 [code      ]         self.chk_online = QCheckBox("Разрешить онлайн-поиск")
  373 [code      ]         self.chk_online.setChecked(True)
  374 [code      ]         self.chk_lic = QCheckBox("Фильтр CC0/CC-BY (коммерчески безопасно)")
  375 [code      ]         self.chk_lic.setChecked(True)
  376 [code      ]         opt.addWidget(self.chk_online)
  377 [code      ]         opt.addWidget(self.chk_lic)
  378 [code      ]         opt.addStretch()
  379 [code      ]         self.root.addLayout(opt)
  380 [blank     ] 
  381 [def       ]     def search(self):
  382 [try_block ]         try:
  383 [import    ]             from agents import sample_hunter
  384 [blank     ] 
  385 [code      ]             r = sample_hunter.hunt(
  386 [code      ]                 self.q.text().strip(),
  387 [code      ]                 max_results=15,
  388 [code      ]                 allow_online=self.chk_online.isChecked(),
  389 [code      ]                 license_filter=self.chk_lic.isChecked(),
  390 [code      ]             )
  391 [code      ]             self.local_list.clear()
  392 [code      ]             self.online_list.clear()
  393 [loop      ]             for it in r.get("local", []):
  394 [code      ]                 self.local_list.addItem(f"[LOCAL] {it['name']} ({it['size_kb']} KB)")
  395 [loop      ]             for it in r.get("online", []):
  396 [code      ]                 self.online_list.addItem(
  397 [code      ]                     f"[{it['source']}] {it['name']}  <{it['license']}>"
  398 [code      ]                 )
  399 [try_block ]         except Exception as e:
  400 [code      ]             QMessageBox.warning(self, "Sample Hunter", f"Поиск не удался: {e}")
  401 [blank     ] 
  402 [def       ]     def commit(self, recipe):
  403 [code      ]         recipe["sample_query"] = self.q.text().strip()
  404 [code      ]         recipe["allow_online_samples"] = self.chk_online.isChecked()
  405 [code      ]         recipe["license_filter"] = self.chk_lic.isChecked()
  406 [blank     ] 
  407 [def       ]     def help_text(self):
  408 [return    ]         return "Введи что ищешь и нажми «Найти». Двойной клик добавляет сэмпл в проект."
  409 [blank     ] 
  410 [blank     ] 
  411 [comment   ] # ============================================================
  412 [comment   ] # Шаг 4: Текст (bilingual + user_lyrics_lines)
  413 [comment   ] # ============================================================
  414 [class     ] class StepLyrics(StepBase):
  415 [def       ]     def __init__(self, wizard):
  416 [code      ]         super().__init__(wizard)
  417 [code      ]         self.root.addWidget(H1("④ Текст"))
  418 [code      ]         self.root.addWidget(
  419 [code      ]             DIM(
  420 [code      ]                 "Куплеты — русский. Хук — короткая английская фраза.\n"
  421 [code      ]                 "МОИ СТРОЧКИ — если впишешь, программа ГАРАНТИРОВАННО добавит их в трек."
  422 [code      ]             )
  423 [code      ]         )
  424 [code      ]         self.own = QTextEdit()
  425 [code      ]         self.own.setPlaceholderText(
  426 [code      ]             "Например:\n«ночь горит, Supra летит»\n«money over everything»\n"
  427 [code      ]             "(RU строки идут в куплеты, EN — в хуки)"
  428 [code      ]         )
  429 [code      ]         self.root.addWidget(self.own)
  430 [code      ]         self.chk_bi = QCheckBox("Двуязычная структура (RU куплеты + EN хуки)")
  431 [code      ]         self.chk_bi.setChecked(True)
  432 [code      ]         self.root.addWidget(self.chk_bi)
  433 [blank     ] 
  434 [code      ]         row = QHBoxLayout()
  435 [code      ]         row.addWidget(QLabel("Куплетов:"))
  436 [code      ]         self.verses = QSpinBox()
  437 [code      ]         self.verses.setRange(1, 4)
  438 [code      ]         self.verses.setValue(2)
  439 [code      ]         row.addWidget(self.verses)
  440 [code      ]         row.addStretch()
  441 [code      ]         self.root.addLayout(row)
  442 [blank     ] 
  443 [def       ]     def commit(self, recipe):
  444 [code      ]         recipe["user_lyrics_lines"] = [
  445 [code      ]             l for l in self.own.toPlainText().splitlines() if l.strip()
  446 [code      ]         ]
  447 [code      ]         recipe["bilingual"] = self.chk_bi.isChecked()
  448 [code      ]         recipe["n_verses"] = int(self.verses.value())
  449 [blank     ] 
  450 [def       ]     def help_text(self):
  451 [return    ]         return "Что впишешь в «Мои строчки» — 100% попадёт в текст. Это твоя мысль, не нейросети."
  452 [blank     ] 
  453 [blank     ] 
  454 [comment   ] # ============================================================
  455 [comment   ] # Шаг 5: Голос — ProVoice основной
  456 [comment   ] # ============================================================
  457 [class     ] class StepVoice(StepBase):
  458 [def       ]     def __init__(self, wizard):
  459 [code      ]         super().__init__(wizard)
  460 [code      ]         self.root.addWidget(H1("⑤ Голос — фундамент трека"))
  461 [code      ]         self.root.addWidget(
  462 [code      ]             DIM("Голос делает трек живым. Мы обучаем RVC v2 под тебя — это ФУНДАМЕНТ.")
  463 [code      ]         )
  464 [code      ]         self.mode = QComboBox()
  465 [code      ]         self.mode.addItems(
  466 [code      ]             [
  467 [code      ]                 "Pro — я пою под бит, RVC полирует (РЕКОМЕНДУЕТСЯ)",
  468 [code      ]                 "Lazy — синтез текста + RVC-переодевание",
  469 [code      ]                 "Off — без вокала (инструментал)",
  470 [code      ]             ]
  471 [code      ]         )
  472 [code      ]         self.mode.setCurrentIndex(0)
  473 [code      ]         self.root.addWidget(self.mode)
  474 [blank     ] 
  475 [code      ]         self.root.addWidget(H2("Voice Vault (твои записи + RVC-модель)"))
  476 [code      ]         self.vault_info = QLabel("Проверю при заходе на шаг…")
  477 [code      ]         self.vault_info.setWordWrap(True)
  478 [code      ]         self.root.addWidget(self.vault_info)
  479 [blank     ] 
  480 [code      ]         row = QHBoxLayout()
  481 [code      ]         b_kar = QPushButton("🎤 Открыть Караоке (записать голос)")
  482 [code      ]         b_kar.clicked.connect(self.open_karaoke)
  483 [code      ]         b_tr = QPushButton("🔥 Обучить RVC (фон, 30 мин — 3 ч)")
  484 [code      ]         b_tr.clicked.connect(self.train_rvc)
  485 [code      ]         b_night = QPushButton("🌙 Ночной режим (для слабого GPU)")
  486 [code      ]         b_night.clicked.connect(lambda: self.train_rvc(night=True))
  487 [code      ]         row.addWidget(b_kar)
  488 [code      ]         row.addWidget(b_tr)
  489 [code      ]         row.addWidget(b_night)
  490 [code      ]         self.root.addLayout(row)
  491 [blank     ] 
  492 [code      ]         self.status = QLabel("")
  493 [code      ]         self.status.setStyleSheet("color:#9a9aa4;")
  494 [code      ]         self.root.addWidget(self.status)
  495 [blank     ] 
  496 [code      ]         self.timer = QTimer(self)
  497 [code      ]         self.timer.timeout.connect(self.refresh_status)
  498 [code      ]         self.timer.start(2000)
  499 [blank     ] 
  500 [def       ]     def enter(self):
  501 [try_block ]         try:
  502 [import    ]             from modules.voice_convert import vault_summary
  503 [blank     ] 
  504 [code      ]             v = vault_summary()
  505 [code      ]             self.vault_info.setText(
  506 [code      ]                 f"Записей: {v['recordings']}, всего минут: {v['total_minutes']:.1f}, "
  507 [code      ]                 f"покрытие фонем: {v['phoneme_coverage_pct']}%. "
  508 [code      ]                 f"Готово к обучению: {'ДА' if v['ready_for_training'] else 'нет (нужно ≥5 мин)'}.\n"
  509 [code      ]                 f"Не хватает стилей: {', '.join(v['recommended_next_styles'][:3]) or 'все ок'}"
  510 [code      ]             )
  511 [try_block ]         except Exception as e:
  512 [code      ]             self.vault_info.setText(f"Voice Vault недоступен: {e}")
  513 [blank     ] 
  514 [def       ]     def open_karaoke(self):
  515 [try_block ]         try:
  516 [code      ]             QMessageBox.information(
  517 [code      ]                 self,
  518 [code      ]                 "Караоке",
  519 [code      ]                 "Модуль karaoke_recorder готов.\n"
  520 [code      ]                 "Записывай фразы по 8 стилям — Voice Vault копит их автоматически.\n"
  521 [code      ]                 "На 5-10 минутах голоса — можно обучать RVC.",
  522 [code      ]             )
  523 [try_block ]         except Exception as e:
  524 [code      ]             QMessageBox.warning(self, "Караоке", f"Пока недоступно: {e}")
  525 [blank     ] 
  526 [def       ]     def train_rvc(self, night: bool = False):
  527 [try_block ]         try:
  528 [import    ]             from modules.voice_convert import train_rvc_model
  529 [blank     ] 
  530 [code      ]             r = train_rvc_model(voice_name="my_voice", epochs=100, night_mode=night)
  531 [code      ]             QMessageBox.information(
  532 [code      ]                 self,
  533 [code      ]                 "RVC",
  534 [code      ]                 f"Обучение запущено в фоне.\nБэкенд: {r.get('backend')}, "
  535 [code      ]                 f"форк: {r.get('fork')}, устройство: {r.get('device')}\n"
  536 [code      ]                 f"Эпох: {r.get('epochs')}. Можешь продолжать работать.",
  537 [code      ]             )
  538 [try_block ]         except Exception as e:
  539 [code      ]             QMessageBox.warning(self, "RVC", f"Ошибка запуска: {e}")
  540 [blank     ] 
  541 [def       ]     def refresh_status(self):
  542 [try_block ]         try:
  543 [import    ]             from modules.voice_convert import get_training_status
  544 [blank     ] 
  545 [code      ]             s = get_training_status("my_voice")
  546 [branch    ]             if s:
  547 [code      ]                 st = s.get("status", "?")
  548 [code      ]                 stage = s.get("stage", "")
  549 [code      ]                 prog = s.get("progress", 0.0)
  550 [code      ]                 self.status.setText(
  551 [code      ]                     f"[RVC training] {st}  |  {stage}  |  {int(prog*100)}%"
  552 [code      ]                 )
  553 [try_block ]         except Exception:
  554 [code      ]             pass
  555 [blank     ] 
  556 [def       ]     def commit(self, recipe):
  557 [code      ]         modes = ["pro", "lazy", "off"]
  558 [code      ]         recipe["voice_mode"] = modes[self.mode.currentIndex()]
  559 [blank     ] 
  560 [def       ]     def help_text(self):
  561 [return    ]         return (
  562 [code      ]             "Pro-режим: ты сам поёшь под бит, RVC полирует. Основной.\n"
  563 [code      ]             "Lazy: синтезируем текст → RVC переодевает голос в твой.\n"
  564 [code      ]             "Обучение RVC идёт в фоне, можно продолжать работать."
  565 [code      ]         )
  566 [blank     ] 
  567 [blank     ] 
  568 [comment   ] # ============================================================
  569 [comment   ] # Шаг 6: Экспертные опции
  570 [comment   ] # ============================================================
  571 [class     ] class StepExpert(StepBase):
  572 [def       ]     def __init__(self, wizard):
  573 [code      ]         super().__init__(wizard)
  574 [code      ]         self.root.addWidget(H1("⑥ Экспертные опции"))
  575 [code      ]         self.root.addWidget(DIM("Можно оставить по умолчанию. Ctrl+E — старый Gradio."))
  576 [blank     ] 
  577 [code      ]         row = QHBoxLayout()
  578 [code      ]         row.addWidget(QLabel("BPM override:"))
  579 [code      ]         self.bpm = QSpinBox()
  580 [code      ]         self.bpm.setRange(0, 200)
  581 [code      ]         self.bpm.setValue(0)
  582 [code      ]         row.addWidget(self.bpm)
  583 [code      ]         row.addStretch()
  584 [code      ]         self.root.addLayout(row)
  585 [blank     ] 
  586 [code      ]         self.chk_full_musicgen = QCheckBox("Полный MusicGen (при VRAM ≥ 10 GB)")
  587 [code      ]         self.chk_full_musicgen.setChecked(True)
  588 [code      ]         self.root.addWidget(self.chk_full_musicgen)
  589 [blank     ] 
  590 [code      ]         self.chk_video = QCheckBox("Собрать TikTok + Reels MP4 + обложку")
  591 [code      ]         self.chk_video.setChecked(True)
  592 [code      ]         self.root.addWidget(self.chk_video)
  593 [blank     ] 
  594 [code      ]         self.chk_stems = QCheckBox("Экспортировать стемы (drums/bass/vocals/other)")
  595 [code      ]         self.chk_stems.setChecked(True)
  596 [code      ]         self.root.addWidget(self.chk_stems)
  597 [blank     ] 
  598 [code      ]         row = QHBoxLayout()
  599 [code      ]         row.addWidget(QLabel("Агрессия транзиентов:"))
  600 [code      ]         self.aggro = QSlider(Qt.Horizontal)
  601 [code      ]         self.aggro.setRange(3, 10)
  602 [code      ]         self.aggro.setValue(7)
  603 [code      ]         row.addWidget(self.aggro, 1)
  604 [code      ]         self.root.addLayout(row)
  605 [blank     ] 
  606 [def       ]     def commit(self, recipe):
  607 [code      ]         recipe["bpm_override"] = int(self.bpm.value()) or None
  608 [code      ]         recipe["full_musicgen"] = self.chk_full_musicgen.isChecked()
  609 [code      ]         recipe["make_video"] = self.chk_video.isChecked()
  610 [code      ]         recipe["export_stems"] = self.chk_stems.isChecked()
  611 [code      ]         recipe["aggression"] = self.aggro.value() / 10.0
  612 [blank     ] 
  613 [def       ]     def help_text(self):
  614 [return    ]         return "Можно ничего не менять. Или Ctrl+E — старый Gradio v5 со всеми настройками."
  615 [blank     ] 
  616 [blank     ] 
  617 [comment   ] # ============================================================
  618 [comment   ] # Шаг 7: Запуск + очередь
  619 [comment   ] # ============================================================
  620 [class     ] class StepRun(StepBase):
  621 [def       ]     def __init__(self, wizard):
  622 [code      ]         super().__init__(wizard)
  623 [code      ]         self.root.addWidget(H1("⑦ Запуск"))
  624 [code      ]         self.root.addWidget(
  625 [code      ]             DIM(
  626 [code      ]                 "«В очередь» — один трек. «Ночная пачка» — постановка сразу 5 треков "
  627 [code      ]                 "с разными темами. Утром — готовый набор."
  628 [code      ]             )
  629 [code      ]         )
  630 [blank     ] 
  631 [code      ]         self.progress = QProgressBar()
  632 [code      ]         self.progress.setRange(0, 100)
  633 [code      ]         self.root.addWidget(self.progress)
  634 [blank     ] 
  635 [code      ]         self.status = QLabel("Ожидание запуска…")
  636 [code      ]         self.root.addWidget(self.status)
  637 [blank     ] 
  638 [code      ]         self.log = QTextEdit()
  639 [code      ]         self.log.setReadOnly(True)
  640 [code      ]         self.log.setMinimumHeight(180)
  641 [code      ]         self.root.addWidget(self.log)
  642 [blank     ] 
  643 [code      ]         row = QHBoxLayout()
  644 [code      ]         self.btn_start = QPushButton("🚀 В очередь")
  645 [code      ]         self.btn_start.clicked.connect(self.start)
  646 [code      ]         self.btn_batch = QPushButton("🌙 Ночная пачка (5 треков)")
  647 [code      ]         self.btn_batch.clicked.connect(self.start_batch)
  648 [code      ]         row.addWidget(self.btn_start)
  649 [code      ]         row.addWidget(self.btn_batch)
  650 [code      ]         row.addStretch()
  651 [code      ]         self.root.addLayout(row)
  652 [blank     ] 
  653 [code      ]         self.queue_label = QLabel("Очередь пуста")
  654 [code      ]         self.queue_label.setStyleSheet("color:#9a9aa4;")
  655 [code      ]         self.root.addWidget(self.queue_label)
  656 [blank     ] 
  657 [code      ]         self.timer = QTimer(self)
  658 [code      ]         self.timer.timeout.connect(self.tick)
  659 [code      ]         self.timer.start(1000)
  660 [code      ]         self.current_tid = None
  661 [code      ]         self.batch_tids = []
  662 [blank     ] 
  663 [def       ]     def start(self):
  664 [code      ]         recipe = self.wizard.recipe
  665 [branch    ]         if not recipe.get("references") and not recipe.get("preset"):
  666 [code      ]             QMessageBox.warning(
  667 [code      ]                 self,
  668 [code      ]                 "Мало данных",
  669 [code      ]                 "Кинь хотя бы 1 референс на шаге ① или выбери пресет на ②.",
  670 [code      ]             )
  671 [return    ]             return
  672 [code      ]         self.current_tid = self.wizard.orch.enqueue(recipe)
  673 [code      ]         self.log.append(f"[{self.current_tid}] в очереди")
  674 [code      ]         self.btn_start.setEnabled(False)
  675 [blank     ] 
  676 [def       ]     def start_batch(self):
  677 [code      ]         recipe = self.wizard.recipe
  678 [branch    ]         if not recipe.get("preset") and not recipe.get("references"):
  679 [code      ]             QMessageBox.warning(
  680 [code      ]                 self, "Мало данных", "Выбери пресет на ② или закинь референсы на ①."
  681 [code      ]             )
  682 [return    ]             return
  683 [comment   ]         # Готовим 5 recipes с разными темами
  684 [code      ]         themes = [
  685 [code      ]             "лето, тачки, деньги",
  686 [code      ]             "ночь, драйв, дрифт",
  687 [code      ]             "клуб, движ, огонь",
  688 [code      ]             "Стамбул, вечер, чай",
  689 [code      ]             "агрессия, скорость, рёв мотора",
  690 [code      ]         ]
  691 [code      ]         recipes = []
  692 [loop      ]         for t in themes:
  693 [code      ]             r = dict(recipe)
  694 [code      ]             r["theme"] = t
  695 [code      ]             recipes.append(r)
  696 [code      ]         self.batch_tids = self.wizard.orch.enqueue_batch(recipes)
  697 [code      ]         self.log.append(
  698 [code      ]             f"[BATCH] в очереди {len(self.batch_tids)} треков: {', '.join(self.batch_tids)}"
  699 [code      ]         )
  700 [code      ]         self.queue_label.setText(f"Очередь: {len(self.batch_tids)} треков в работе")
  701 [blank     ] 
  702 [def       ]     def tick(self):
  703 [comment   ]         # обновляем очередь
  704 [code      ]         active = list(self.batch_tids) + (
  705 [code      ]             [self.current_tid] if self.current_tid else []
  706 [code      ]         )
  707 [code      ]         active = [t for t in active if t]
  708 [branch    ]         if not active:
  709 [return    ]             return
  710 [code      ]         lines = []
  711 [loop      ]         for tid in active:
  712 [code      ]             j = self.wizard.orch.jobs.get(tid)
  713 [branch    ]             if not j:
  714 [code      ]                 continue
  715 [code      ]             lines.append(f"  {tid}: {j.status} | {j.stage} | {int(j.progress*100)}%")
  716 [branch    ]             if j.status in ("done", "error") and j == self.wizard.orch.jobs.get(
  717 [code      ]                 self.current_tid
  718 [code      ]             ):
  719 [branch    ]                 if j.status == "done":
  720 [code      ]                     self.log.append(f"[{tid}] ✅ DONE → {j.project_dir}")
  721 [branch    ]                 else:
  722 [code      ]                     self.log.append(f"[{tid}] ❌ {j.error}")
  723 [code      ]                 self.btn_start.setEnabled(True)
  724 [code      ]                 self.current_tid = None
  725 [comment   ]                 # переводим Wizard на StepResult
  726 [branch    ]                 if self.wizard.stack.currentIndex() == self.wizard.stack.indexOf(self):
  727 [code      ]                     self.wizard.go_to_result(j)
  728 [code      ]         self.queue_label.setText(f"Очередь: {len(active)}\n" + "\n".join(lines))
  729 [comment   ]         # общий прогресс
  730 [branch    ]         if active:
  731 [code      ]             avg = sum(
  732 [code      ]                 (
  733 [code      ]                     self.wizard.orch.jobs.get(t).progress
  734 [branch    ]                     if self.wizard.orch.jobs.get(t)
  735 [code      ]                     else 0
  736 [code      ]                 )
  737 [loop      ]                 for t in active
  738 [code      ]             ) / len(active)
  739 [code      ]             self.progress.setValue(int(avg * 100))
  740 [blank     ] 
  741 [def       ]     def commit(self, recipe):
  742 [code      ]         pass
  743 [blank     ] 
  744 [def       ]     def help_text(self):
  745 [return    ]         return (
  746 [code      ]             "В очередь — один трек. Ночная пачка — 5 треков сразу "
  747 [code      ]             "(программа посчитает их за ночь)."
  748 [code      ]         )
  749 [blank     ] 
  750 [blank     ] 
  751 [comment   ] # ============================================================
  752 [comment   ] # Шаг 8: Результат — 3 кнопки (Пересобрать / Переделать часть / 3 варианта)
  753 [comment   ] # ============================================================
  754 [class     ] class StepResult(StepBase):
  755 [def       ]     def __init__(self, wizard):
  756 [code      ]         super().__init__(wizard)
  757 [code      ]         self.root.addWidget(H1("⑧ Результат"))
  758 [code      ]         self.info = QLabel("Ожидание готового трека…")
  759 [code      ]         self.info.setWordWrap(True)
  760 [code      ]         self.root.addWidget(self.info)
  761 [blank     ] 
  762 [code      ]         self.detector = QLabel("")
  763 [code      ]         self.detector.setWordWrap(True)
  764 [code      ]         self.detector.setStyleSheet(
  765 [code      ]             "background:#17171d;border:1px solid #2a2a34;padding:8px;"
  766 [code      ]         )
  767 [code      ]         self.root.addWidget(self.detector)
  768 [blank     ] 
  769 [comment   ]         # 3 кнопки — из ТЗ 20.2 вопрос 25
  770 [code      ]         row = QHBoxLayout()
  771 [code      ]         self.btn_full = QPushButton("🔁 Пересобрать всё")
  772 [code      ]         self.btn_full.clicked.connect(self.rebuild_full)
  773 [code      ]         self.btn_part = QPushButton("✂️ Переделать часть")
  774 [code      ]         self.btn_part.clicked.connect(self.rebuild_part)
  775 [code      ]         self.btn_three = QPushButton("🎲 Показать 3 варианта")
  776 [code      ]         self.btn_three.clicked.connect(self.three_variants)
  777 [code      ]         row.addWidget(self.btn_full)
  778 [code      ]         row.addWidget(self.btn_part)
  779 [code      ]         row.addWidget(self.btn_three)
  780 [code      ]         self.root.addLayout(row)
  781 [blank     ] 
  782 [code      ]         self.root.addWidget(HR())
  783 [code      ]         row2 = QHBoxLayout()
  784 [code      ]         self.btn_folder = QPushButton("📂 Открыть папку релиза")
  785 [code      ]         self.btn_folder.clicked.connect(self.open_folder)
  786 [code      ]         self.btn_expert = QPushButton("🛠 Экспертный режим (Gradio v5)")
  787 [code      ]         self.btn_expert.clicked.connect(lambda: self.wizard.launch_gradio_expert())
  788 [code      ]         row2.addWidget(self.btn_folder)
  789 [code      ]         row2.addWidget(self.btn_expert)
  790 [code      ]         row2.addStretch()
  791 [code      ]         self.root.addLayout(row2)
  792 [blank     ] 
  793 [code      ]         self.current_job = None
  794 [blank     ] 
  795 [def       ]     def show_result(self, job):
  796 [code      ]         self.current_job = job
  797 [code      ]         result = job.result or {}
  798 [code      ]         rel = result.get("release", {}).get("release_dir", "?")
  799 [code      ]         master = result.get("master") or result.get("master_path", "?")
  800 [code      ]         self.info.setText(
  801 [code      ]             f"✅ Готово!\n\n"
  802 [code      ]             f"Track ID: {job.track_id}\n"
  803 [code      ]             f"Мастер: {master}\n"
  804 [code      ]             f"Релиз-пакет: {rel}\n"
  805 [code      ]             f"Время: {job.finished_at - job.started_at:.1f} сек"
  806 [code      ]         )
  807 [code      ]         ai = result.get("ai_detector", {})
  808 [branch    ]         if ai.get("ok"):
  809 [code      ]             adv = "\n".join(f"  • {a}" for a in ai.get("advice", [])[:4])
  810 [code      ]             self.detector.setText(
  811 [code      ]                 f"🧪 AI-детектор (9 метрик): {ai.get('verdict')}  |  score={ai.get('score')}\n"
  812 [code      ]                 f"Флаги: {', '.join(ai.get('flags', [])) or 'нет'}\n"
  813 [code      ]                 f"{adv}"
  814 [code      ]             )
  815 [branch    ]         else:
  816 [code      ]             self.detector.setText("🧪 AI-детектор: пока не запускался")
  817 [blank     ] 
  818 [def       ]     def open_folder(self):
  819 [branch    ]         if not self.current_job:
  820 [return    ]             return
  821 [code      ]         p = self.current_job.project_dir
  822 [try_block ]         try:
  823 [branch    ]             if sys.platform.startswith("win"):
  824 [code      ]                 os.startfile(str(p))
  825 [branch    ]             else:
  826 [import    ]                 import webbrowser
  827 [import    ]                 from pathlib import Path
  828 [code      ]                 webbrowser.open(Path(p).absolute().as_uri())
  829 [try_block ]         except Exception:
  830 [code      ]             pass
  831 [blank     ] 
  832 [def       ]     def rebuild_full(self):
  833 [branch    ]         if not self.current_job:
  834 [return    ]             return
  835 [code      ]         self.wizard.orch.enqueue(self.current_job.recipe)
  836 [code      ]         QMessageBox.information(self, "Готово", "Полная пересборка в очереди.")
  837 [blank     ] 
  838 [def       ]     def rebuild_part(self):
  839 [code      ]         parts = ["Бит", "Текст", "Голос", "Мастер"]
  840 [code      ]         item, ok = QInputDialog.getItem(
  841 [code      ]             self, "Что переделать?", "Компонент:", parts, 0, False
  842 [code      ]         )
  843 [branch    ]         if not ok or not self.current_job:
  844 [return    ]             return
  845 [code      ]         r = dict(self.current_job.recipe)
  846 [code      ]         r["rebuild_only"] = item.lower()
  847 [code      ]         self.wizard.orch.enqueue(r)
  848 [code      ]         QMessageBox.information(self, "Готово", f"«{item}» пойдёт заново в очередь.")
  849 [blank     ] 
  850 [def       ]     def three_variants(self):
  851 [branch    ]         if not self.current_job:
  852 [return    ]             return
  853 [code      ]         recipes = []
  854 [loop      ]         for i in range(3):
  855 [code      ]             r = dict(self.current_job.recipe)
  856 [code      ]             r["variant"] = i + 1
  857 [code      ]             r["aggression"] = 0.4 + i * 0.2  # разная агрессия
  858 [code      ]             recipes.append(r)
  859 [code      ]         tids = self.wizard.orch.enqueue_batch(recipes)
  860 [code      ]         QMessageBox.information(
  861 [code      ]             self,
  862 [code      ]             "3 варианта",
  863 [code      ]             f"3 версии в очереди: {', '.join(tids)}. Сравнишь готовые файлы.",
  864 [code      ]         )
  865 [blank     ] 
  866 [def       ]     def commit(self, recipe):
  867 [code      ]         pass
  868 [blank     ] 
  869 [def       ]     def help_text(self):
  870 [return    ]         return (
  871 [code      ]             "3 кнопки: полная пересборка, переделать только часть, "
  872 [code      ]             "сделать сразу 3 варианта для сравнения."
  873 [code      ]         )
  874 [blank     ] 
  875 [blank     ] 
  876 [comment   ] # ============================================================
  877 [comment   ] # Wizard — главное окно
  878 [comment   ] # ============================================================
  879 [class     ] class Wizard(QMainWindow):
  880 [def       ]     def __init__(self, orch, hw, log):
  881 [code      ]         super().__init__()
  882 [code      ]         self.orch, self.hw, self.log = orch, hw, log
  883 [code      ]         self.setWindowTitle(
  884 [code      ]             f"ZS Music Maker v7  |  {hw.gpu_name} ({hw.backend}, {hw.mode})"
  885 [code      ]         )
  886 [code      ]         self.resize(1200, 820)
  887 [blank     ] 
  888 [code      ]         self.recipe = {}
  889 [code      ]         self.stack = QStackedWidget()
  890 [comment   ]         # 9 шагов
  891 [code      ]         self.steps = [
  892 [code      ]             StepArtist(self),
  893 [code      ]             StepReferences(self),
  894 [code      ]             StepPreset(self),
  895 [code      ]             StepSamples(self),
  896 [code      ]             StepLyrics(self),
  897 [code      ]             StepVoice(self),
  898 [code      ]             StepExpert(self),
  899 [code      ]             StepRun(self),
  900 [code      ]             StepResult(self),
  901 [code      ]         ]
  902 [loop      ]         for s in self.steps:
  903 [code      ]             self.stack.addWidget(s)
  904 [blank     ] 
  905 [comment   ]         # Bottom bar
  906 [code      ]         self.crumbs = QLabel(self._crumb_text())
  907 [code      ]         self.crumbs.setStyleSheet("color:#9a9aa4;")
  908 [code      ]         self.btn_back = QPushButton("← Назад")
  909 [code      ]         self.btn_back.clicked.connect(self.back)
  910 [code      ]         self.btn_next = QPushButton("Далее →")
  911 [code      ]         self.btn_next.clicked.connect(self.next)
  912 [code      ]         self.btn_help = QPushButton("❓ Помощь (F1)")
  913 [code      ]         self.btn_help.clicked.connect(self.show_help)
  914 [blank     ] 
  915 [code      ]         bar = QHBoxLayout()
  916 [code      ]         bar.addWidget(self.btn_back)
  917 [code      ]         bar.addStretch()
  918 [code      ]         bar.addWidget(self.btn_help)
  919 [code      ]         bar.addSpacing(20)
  920 [code      ]         bar.addWidget(self.crumbs)
  921 [code      ]         bar.addStretch()
  922 [code      ]         bar.addWidget(self.btn_next)
  923 [blank     ] 
  924 [code      ]         root = QVBoxLayout()
  925 [code      ]         root.addWidget(self.stack)
  926 [code      ]         root.addLayout(bar)
  927 [code      ]         w = QWidget()
  928 [code      ]         w.setLayout(root)
  929 [code      ]         self.setCentralWidget(w)
  930 [blank     ] 
  931 [comment   ]         # Menu bar
  932 [code      ]         mb = self.menuBar()
  933 [code      ]         help_menu = mb.addMenu("Помощь")
  934 [code      ]         a_tour = QAction("Обучающий тур", self)
  935 [code      ]         a_tour.triggered.connect(self._show_tour)
  936 [code      ]         help_menu.addAction(a_tour)
  937 [code      ]         a_about = QAction("О программе", self)
  938 [code      ]         a_about.triggered.connect(self._about)
  939 [code      ]         help_menu.addAction(a_about)
  940 [blank     ] 
  941 [comment   ]         # Shortcuts
  942 [code      ]         QShortcut(QKeySequence("Ctrl+E"), self, activated=self.launch_gradio_expert)
  943 [code      ]         QShortcut(QKeySequence("F1"), self, activated=self.show_help)
  944 [blank     ] 
  945 [comment   ]         # Onboarding при первом запуске
  946 [code      ]         self._maybe_onboarding()
  947 [blank     ] 
  948 [def       ]     def _crumb_text(self):
  949 [code      ]         i = self.stack.currentIndex() if hasattr(self, "stack") else 0
  950 [return    ]         return f"Шаг {i+1} / {len(self.steps)}"
  951 [blank     ] 
  952 [def       ]     def _maybe_onboarding(self):
  953 [try_block ]         try:
  954 [import    ]             from app.gui.onboarding import maybe_show_onboarding
  955 [blank     ] 
  956 [code      ]             shown = maybe_show_onboarding(self)
  957 [branch    ]             if shown:
  958 [code      ]                 self.log.info("Onboarding tour shown")
  959 [try_block ]         except Exception as e:
  960 [code      ]             self.log.warning(f"onboarding failed: {e}")
  961 [blank     ] 
  962 [def       ]     def _show_tour(self):
  963 [try_block ]         try:
  964 [import    ]             from app.gui.onboarding import show_help_tour
  965 [blank     ] 
  966 [code      ]             show_help_tour(self)
  967 [try_block ]         except Exception as e:
  968 [code      ]             QMessageBox.warning(self, "Помощь", f"Тур недоступен: {e}")
  969 [blank     ] 
  970 [def       ]     def _about(self):
  971 [code      ]         QMessageBox.information(
  972 [code      ]             self,
  973 [code      ]             "О программе",
  974 [code      ]             "ZS Music Maker v7 (MM ZS)\n\n"
  975 [code      ]             "Локальная студия хитовых треков.\n"
  976 [code      ]             "Windows 11 + PySide6 + RVC v2 + MusicGen + Matchering + Silero.\n\n"
  977 [code      ]             "Всё бесплатно, всё локально, ничего в облаке.\n"
  978 [code      ]             "https://github.com/… (open-source)",
  979 [code      ]         )
  980 [blank     ] 
  981 [def       ]     def show_help(self):
  982 [code      ]         cur = self.stack.currentWidget()
  983 [code      ]         txt = (
  984 [code      ]             cur.help_text()
  985 [branch    ]             if hasattr(cur, "help_text")
  986 [code      ]             else "Помощь по этому шагу пока не написана."
  987 [code      ]         )
  988 [code      ]         QMessageBox.information(self, "Помощь", txt)
  989 [blank     ] 
  990 [def       ]     def back(self):
  991 [code      ]         i = self.stack.currentIndex()
  992 [branch    ]         if i > 0:
  993 [code      ]             self.stack.setCurrentIndex(i - 1)
  994 [code      ]         self.crumbs.setText(self._crumb_text())
  995 [blank     ] 
  996 [def       ]     def next(self):
  997 [code      ]         cur = self.stack.currentWidget()
  998 [code      ]         cur.commit(self.recipe)
  999 [code      ]         i = self.stack.currentIndex()
 1000 [branch    ]         if i < self.stack.count() - 1:
 1001 [code      ]             self.stack.setCurrentIndex(i + 1)
 1002 [code      ]             nxt = self.stack.currentWidget()
 1003 [code      ]             nxt.enter()
 1004 [code      ]         self.crumbs.setText(self._crumb_text())
 1005 [blank     ] 
 1006 [def       ]     def go_to_result(self, job):
 1007 [docstring ]         """Автоматический переход на StepResult, когда трек готов."""
 1008 [try_block ]         try:
 1009 [code      ]             idx = None
 1010 [loop      ]             for i, s in enumerate(self.steps):
 1011 [branch    ]                 if isinstance(s, StepResult):
 1012 [code      ]                     idx = i
 1013 [code      ]                     break
 1014 [branch    ]             if idx is None:
 1015 [return    ]                 return
 1016 [code      ]             self.stack.setCurrentIndex(idx)
 1017 [code      ]             self.steps[idx].show_result(job)
 1018 [code      ]             self.crumbs.setText(self._crumb_text())
 1019 [try_block ]         except Exception as e:
 1020 [code      ]             self.log.warning(f"go_to_result failed: {e}")
 1021 [blank     ] 
 1022 [def       ]     def launch_gradio_expert(self):
 1023 [code      ]         self.log.info("Ctrl+E → v5 Gradio")
 1024 [blank     ] 
 1025 [def       ]         def _run():
 1026 [try_block ]             try:
 1027 [import    ]                 import main as v5main
 1028 [blank     ] 
 1029 [branch    ]                 if hasattr(v5main, "build_ui"):
 1030 [code      ]                     v5main.build_ui().launch(
 1031 [code      ]                         server_port=7860, inbrowser=True, share=False
 1032 [code      ]                     )
 1033 [branch    ]                 else:
 1034 [import    ]                     import runpy
 1035 [blank     ] 
 1036 [code      ]                     runpy.run_path(str(ROOT / "main.py"), run_name="__main__")
 1037 [try_block ]             except Exception as e:
 1038 [code      ]                 self.log.exception(f"Gradio expert failed: {e}")
 1039 [blank     ] 
 1040 [code      ]         threading.Thread(target=_run, daemon=True).start()
 1041 [code      ]         time.sleep(2)
 1042 [code      ]         webbrowser.open("http://127.0.0.1:7860")
```