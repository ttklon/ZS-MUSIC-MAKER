# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/gui/onboarding.py`

**Всего строк:** 236

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 177 | 75.0 |
| blank | 24 | 10.2 |
| docstring | 10 | 4.2 |
| def | 6 | 2.5 |
| branch | 6 | 2.5 |
| import | 5 | 2.1 |
| return | 3 | 1.3 |
| try_block | 2 | 0.8 |
| class | 1 | 0.4 |
| loop | 1 | 0.4 |
| comment | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] onboarding.py — Scriptable Tour при первом запуске.
    3 [blank     ] 
    4 [docstring ] Полноэкранное приветственное окно с пошаговым туром по интерфейсу.
    5 [docstring ] Появляется автоматически при первом запуске (user_profile.first_run=True).
    6 [docstring ] Можно вручную запустить из меню "Помощь".
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] from __future__ import annotations
   10 [blank     ] 
   11 [import    ] from PySide6.QtWidgets import (
   12 [code      ]     QCheckBox,
   13 [code      ]     QDialog,
   14 [code      ]     QHBoxLayout,
   15 [code      ]     QLabel,
   16 [code      ]     QPushButton,
   17 [code      ]     QTextBrowser,
   18 [code      ]     QVBoxLayout,
   19 [code      ] )
   20 [blank     ] 
   21 [code      ] TOUR_STEPS = [
   22 [code      ]     {
   23 [code      ]         "title": "🎛 Добро пожаловать в MM ZS v7",
   24 [code      ]         "text": (
   25 [code      ]             "Это ZS Music Maker v7 — твоя локальная студия хитов.\n\n"
   26 [code      ]             "Мы собираем оригинальные треки на твоём ПК, без подписок и облаков. "
   27 [code      ]             "Всё бесплатно, всё локально.\n\n"
   28 [code      ]             "Через 5 минут ты сделаешь свой первый трек.\n\n"
   29 [code      ]             "Двинули?"
   30 [code      ]         ),
   31 [code      ]     },
   32 [code      ]     {
   33 [code      ]         "title": "① Референсы — что качает",
   34 [code      ]         "text": (
   35 [code      ]             "Первый шаг — покажи, какая музыка тебе нравится.\n\n"
   36 [code      ]             "Просто перетащи 1–7 треков (mp3/wav) в окно. Программа НЕ КОПИРУЕТ их — "
   37 [code      ]             "она вытянет вайб, BPM, ритм-паттерн, тональность.\n\n"
   38 [code      ]             "Хочешь без референсов? Пропусти шаг — на шаге ② выбери пресет."
   39 [code      ]         ),
   40 [code      ]     },
   41 [code      ]     {
   42 [code      ]         "title": "② Стиль — тема, длина, режим",
   43 [code      ]         "text": (
   44 [code      ]             "Выбери:\n"
   45 [code      ]             "  • Что должно быть в тексте (тема)\n"
   46 [code      ]             "  • Длину трека (от 1:30 до 3:30)\n"
   47 [code      ]             "  • Режим: Быстрый (10-15 мин) / Качественный (30-60 мин) / Максимальный (1-3 часа)\n\n"
   48 [code      ]             "По умолчанию — Качественный. Максимальный для релизов."
   49 [code      ]         ),
   50 [code      ]     },
   51 [code      ]     {
   52 [code      ]         "title": "③ Сэмплы — только чистые (CC0/Royalty-Free)",
   53 [code      ]         "text": (
   54 [code      ]             "Слева — твоя локальная библиотека (samples_cache/).\n"
   55 [code      ]             "Справа — интернет-поиск (Wikimedia CC0, Pixabay, Freesound).\n\n"
   56 [code      ]             "Программа блокирует всё, что нельзя выпускать коммерчески. "
   57 [code      ]             "Ты выпускаешь под своим именем — юридически чисто с первого трека."
   58 [code      ]         ),
   59 [code      ]     },
   60 [code      ]     {
   61 [code      ]         "title": "④ Текст — русские куплеты + английский хук",
   62 [code      ]         "text": (
   63 [code      ]             "У тебя есть ОБЯЗАТЕЛЬНОЕ поле «Моя тема / Мои строчки».\n"
   64 [code      ]             "Что впишешь — то ГАРАНТИРОВАННО попадёт в трек, дословно.\n\n"
   65 [code      ]             "Куплеты — по-русски. Хуки — короткие английские фразы.\n\n"
   66 [code      ]             "Тексты пишет Llama 3 через Ollama (если запущено). Или наш шаблонник."
   67 [code      ]         ),
   68 [code      ]     },
   69 [code      ]     {
   70 [code      ]         "title": "⑤ Голос — ФУНДАМЕНТ",
   71 [code      ]         "text": (
   72 [code      ]             "Это самый важный шаг для «не-нейроношности».\n\n"
   73 [code      ]             "  • Lazy — синтезируем текст → RVC переодевает голос под тебя\n"
   74 [code      ]             "  • Pro — ТЫ САМ поёшь под бит в наушниках → RVC полирует\n\n"
   75 [code      ]             "Voice Vault копит твои записи по 8 стилям (медленно, быстро, "
   76 [code      ]             "агрессивно, шёпот, с хрипом, нараспев и т.д.).\n\n"
   77 [code      ]             "Обучение RVC: ~30 минут на 12GB VRAM, до 3 часов на слабом железе. "
   78 [code      ]             "Идёт в фоне — не блокирует работу."
   79 [code      ]         ),
   80 [code      ]     },
   81 [code      ]     {
   82 [code      ]         "title": "⑥ Мастеринг → 3 стенда прослушивания",
   83 [code      ]         "text": (
   84 [code      ]             "Мы делаем не один мастер, а сразу три:\n"
   85 [code      ]             "  🚗 Автомобиль — жирный саб, буст низов\n"
   86 [code      ]             "  🎧 Клуб — громкость + суб\n"
   87 [code      ]             "  📱 Стриминг — нейтральный, для Spotify/Yandex\n\n"
   88 [code      ]             "Каждый под свою среду. Матчеринг подгоняет под ЛЮБОЙ выбранный референс."
   89 [code      ]         ),
   90 [code      ]     },
   91 [code      ]     {
   92 [code      ]         "title": "⑦ Релиз-пакет — 20+ файлов автоматически",
   93 [code      ]         "text": (
   94 [code      ]             "В конце получаешь всё сразу:\n"
   95 [code      ]             "  • master.wav (24-bit) + mp3 320 + flac\n"
   96 [code      ]             "  • instrumental + acapella\n"
   97 [code      ]             "  • стемы (drums/bass/vocals/other)\n"
   98 [code      ]             "  • lyrics.txt + lyrics.lrc (караоке)\n"
   99 [code      ]             "  • cover.png (обложка)\n"
  100 [code      ]             "  • tiktok.mp4 + reels.mp4 (15-30 сек, вертикально)\n"
  101 [code      ]             "  • car/club/streaming мастера\n"
  102 [code      ]             "  • recipe.json (пересобрать этот же трек по recipe)\n"
  103 [code      ]             "  • manifest.json (лицензии сэмплов)\n\n"
  104 [code      ]             "Всё с твоим именем в ID3-тегах. Готово к загрузке в дистрибьютор."
  105 [code      ]         ),
  106 [code      ]     },
  107 [code      ]     {
  108 [code      ]         "title": "🎯 На результате — 3 кнопки",
  109 [code      ]         "text": (
  110 [code      ]             "Не понравилось? Не проблема.\n\n"
  111 [code      ]             "  🔁 Пересобрать всё — полный рестарт с теми же настройками\n"
  112 [code      ]             "  ✂️ Переделать часть — только бит / только текст / только голос / только мастер\n"
  113 [code      ]             "  🎲 3 варианта — параллельно сделает 3 версии для сравнения\n\n"
  114 [code      ]             "И ещё: ставь в очередь до 5+ проектов на ночь. Утром — готовый пак."
  115 [code      ]         ),
  116 [code      ]     },
  117 [code      ]     {
  118 [code      ]         "title": "🔧 Экспертный режим",
  119 [code      ]         "text": (
  120 [code      ]             "Всё, что ты видел до этого — Wizard, «средний контроль».\n\n"
  121 [code      ]             "Хочешь глубже? Ctrl+E — откроется старый Gradio-режим v5 со всеми "
  122 [code      ]             "15+ вкладками: BPM-override, EQ, Whisper-параметры, тонкие настройки "
  123 [code      ]             "мастеринга, humanization, groove-веса и т.д.\n\n"
  124 [code      ]             "По умолчанию всё это спрятано — не пугает новичка."
  125 [code      ]         ),
  126 [code      ]     },
  127 [code      ]     {
  128 [code      ]         "title": "🚀 Готово!",
  129 [code      ]         "text": (
  130 [code      ]             "Всё, ты в теме. Программа работает автономно, локально, бесплатно.\n\n"
  131 [code      ]             "Иди на шаг ①, кинь пару треков — и запускай.\n\n"
  132 [code      ]             "Помощь (F1) на каждом шаге. Тур можно повторить в меню Помощь."
  133 [code      ]         ),
  134 [code      ]     },
  135 [code      ] ]
  136 [blank     ] 
  137 [blank     ] 
  138 [class     ] class OnboardingDialog(QDialog):
  139 [def       ]     def __init__(self, parent=None):
  140 [code      ]         super().__init__(parent)
  141 [code      ]         self.setWindowTitle("MM ZS v7 — Обучающий тур")
  142 [code      ]         self.resize(720, 520)
  143 [code      ]         self.step = 0
  144 [blank     ] 
  145 [code      ]         v = QVBoxLayout(self)
  146 [blank     ] 
  147 [code      ]         self.title = QLabel()
  148 [code      ]         self.title.setStyleSheet("font-size:22px;font-weight:700;color:#ff5a28;")
  149 [code      ]         v.addWidget(self.title)
  150 [blank     ] 
  151 [code      ]         self.body = QTextBrowser()
  152 [code      ]         self.body.setStyleSheet(
  153 [code      ]             "background:#17171d;color:#e8e8ee;border:1px solid #2a2a34;padding:12px;font-size:14px;"
  154 [code      ]         )
  155 [code      ]         v.addWidget(self.body, 1)
  156 [blank     ] 
  157 [code      ]         self.dont_show = QCheckBox("Больше не показывать при запуске")
  158 [code      ]         v.addWidget(self.dont_show)
  159 [blank     ] 
  160 [code      ]         bar = QHBoxLayout()
  161 [code      ]         self.btn_prev = QPushButton("← Назад")
  162 [code      ]         self.btn_skip = QPushButton("Пропустить")
  163 [code      ]         self.btn_next = QPushButton("Далее →")
  164 [code      ]         self.progress = QLabel()
  165 [code      ]         self.progress.setStyleSheet("color:#9a9aa4;")
  166 [loop      ]         for b in (self.btn_prev, self.btn_skip):
  167 [code      ]             bar.addWidget(b)
  168 [code      ]         bar.addStretch()
  169 [code      ]         bar.addWidget(self.progress)
  170 [code      ]         bar.addStretch()
  171 [code      ]         bar.addWidget(self.btn_next)
  172 [code      ]         v.addLayout(bar)
  173 [blank     ] 
  174 [code      ]         self.btn_prev.clicked.connect(self.prev)
  175 [code      ]         self.btn_next.clicked.connect(self.next)
  176 [code      ]         self.btn_skip.clicked.connect(self.reject)
  177 [blank     ] 
  178 [code      ]         self.render()
  179 [blank     ] 
  180 [def       ]     def render(self):
  181 [code      ]         s = TOUR_STEPS[self.step]
  182 [code      ]         self.title.setText(s["title"])
  183 [comment   ]         # HTML для абзацев + сохранения переносов
  184 [code      ]         html = s["text"].replace("\n\n", "<br><br>").replace("\n", "<br>")
  185 [code      ]         self.body.setHtml(
  186 [code      ]             f"<div style='font-family:Segoe UI,Arial;line-height:1.5;'>{html}</div>"
  187 [code      ]         )
  188 [code      ]         self.progress.setText(f"Шаг {self.step+1} / {len(TOUR_STEPS)}")
  189 [code      ]         self.btn_prev.setEnabled(self.step > 0)
  190 [code      ]         self.btn_next.setText(
  191 [code      ]             "Закрыть ✓" if self.step == len(TOUR_STEPS) - 1 else "Далее →"
  192 [code      ]         )
  193 [blank     ] 
  194 [def       ]     def prev(self):
  195 [branch    ]         if self.step > 0:
  196 [code      ]             self.step -= 1
  197 [code      ]             self.render()
  198 [blank     ] 
  199 [def       ]     def next(self):
  200 [branch    ]         if self.step < len(TOUR_STEPS) - 1:
  201 [code      ]             self.step += 1
  202 [code      ]             self.render()
  203 [branch    ]         else:
  204 [code      ]             self.accept()
  205 [blank     ] 
  206 [blank     ] 
  207 [def       ] def maybe_show_onboarding(parent=None) -> bool:
  208 [docstring ]     """
  209 [docstring ]     Показать тур если это первый запуск. Возвращает True если показан.
  210 [docstring ]     """
  211 [try_block ]     try:
  212 [import    ]         from modules.user_profile import is_first_run, mark_onboarded
  213 [try_block ]     except Exception:
  214 [return    ]         return False
  215 [branch    ]     if not is_first_run():
  216 [return    ]         return False
  217 [code      ]     d = OnboardingDialog(parent)
  218 [code      ]     d.exec()
  219 [branch    ]     if d.dont_show.isChecked() or True:  # всегда фиксируем, что первый запуск прошёл
  220 [code      ]         mark_onboarded()
  221 [return    ]     return True
  222 [blank     ] 
  223 [blank     ] 
  224 [def       ] def show_help_tour(parent=None) -> None:
  225 [docstring ]     """Ручной вызов тура из меню «Помощь»."""
  226 [code      ]     OnboardingDialog(parent).exec()
  227 [blank     ] 
  228 [blank     ] 
  229 [branch    ] if __name__ == "__main__":
  230 [import    ]     import sys
  231 [blank     ] 
  232 [import    ]     from PySide6.QtWidgets import QApplication
  233 [blank     ] 
  234 [code      ]     a = QApplication(sys.argv)
  235 [code      ]     d = OnboardingDialog()
  236 [code      ]     d.exec()
```