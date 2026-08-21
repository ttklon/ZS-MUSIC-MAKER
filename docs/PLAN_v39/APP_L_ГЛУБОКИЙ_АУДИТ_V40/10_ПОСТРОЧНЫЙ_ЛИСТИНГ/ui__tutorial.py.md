# ПОСТРОЧНЫЙ ЛИСТИНГ: `ui/tutorial.py`

**Всего строк:** 293

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 225 | 76.8 |
| blank | 24 | 8.2 |
| return | 11 | 3.8 |
| def | 9 | 3.1 |
| docstring | 6 | 2.0 |
| branch | 6 | 2.0 |
| try_block | 4 | 1.4 |
| comment | 3 | 1.0 |
| import | 2 | 0.7 |
| stmt | 2 | 0.7 |
| loop | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] UI: Tutorial System v2 (НОВЫЙ)
    3 [docstring ] Пошаговый интерактивный туториал — показывает весь функционал приложения.
    4 [docstring ] Пользователь идёт шаг за шагом, каждый шаг объясняет что и зачем.
    5 [docstring ] Можно включить/выключить.
    6 [docstring ] """
    7 [blank     ] 
    8 [import    ] import json
    9 [import    ] import os
   10 [blank     ] 
   11 [comment   ] # v34 FIX (P3.26): единый путь data/tutorial_settings.json (раньше этот модуль
   12 [comment   ] # писал в корень репо, а modules/onboarding_tour.py — в CWD: получалось ДВА
   13 [comment   ] # рассинхронизированных файла состояния). Миграция старого файла сохранена.
   14 [def       ] def _resolve_settings_file() -> str:
   15 [code      ]     root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   16 [code      ]     new = os.path.join(root, "data", "tutorial_settings.json")
   17 [code      ]     old = os.path.join(root, "tutorial_settings.json")
   18 [try_block ]     try:
   19 [code      ]         os.makedirs(os.path.dirname(new), exist_ok=True)
   20 [branch    ]         if not os.path.exists(new) and os.path.exists(old):
   21 [stmt      ]             with open(old, encoding="utf-8") as f:
   22 [code      ]                 payload = f.read()
   23 [stmt      ]             with open(new, "w", encoding="utf-8") as f:
   24 [code      ]                 f.write(payload)
   25 [try_block ]     except Exception:
   26 [code      ]         pass
   27 [return    ]     return new
   28 [blank     ] 
   29 [blank     ] 
   30 [code      ] SETTINGS_FILE = _resolve_settings_file()
   31 [blank     ] 
   32 [blank     ] 
   33 [code      ] STEPS = [
   34 [code      ]     {
   35 [code      ]         "id": "welcome",
   36 [code      ]         "title": "Добро пожаловать в ZS Music Maker!",
   37 [code      ]         "text": "Это автономная локальная студия для написания хитовых фонк/дрифт/эдит-треков. "
   38 [code      ]         "Всё работает бесплатно на твоём ПК. Давай пройдём по всем вкладкам за 2 минуты.",
   39 [code      ]         "action": "Нажми 'Далее' чтобы продолжить.",
   40 [code      ]         "tab": None,
   41 [code      ]     },
   42 [code      ]     {
   43 [code      ]         "id": "analysis",
   44 [code      ]         "title": "① Анализ референсов",
   45 [code      ]         "text": "Сюда ты закидываешь 1-7 треков, которые тебе нравятся. "
   46 [code      ]         "Программа проанализирует их: BPM, тональность, энергию, вайб. "
   47 [code      ]         "Если треков несколько — построит усреднённый style-vector. "
   48 [code      ]         "Ты можешь указать ВЕС каждого трека и что именно из него взять "
   49 [code      ]         "(бит, стиль чтения, образы, ритм). "
   50 [code      ]         "BPM определяется не как одно число, а как диапазон с режимами "
   51 [code      ]         "(кач/ускорить/замедлить/клубнее/TikTok-hooky).",
   52 [code      ]         "action": "Попробуй: закинь 2-3 трека и нажми 'Анализировать'.",
   53 [code      ]         "tab": "① Анализ",
   54 [code      ]     },
   55 [code      ]     {
   56 [code      ]         "id": "stems",
   57 [code      ]         "title": "② Сплит стемов",
   58 [code      ]         "text": "Demucs v4 разбирает трек на 4 дорожки: вокал, барабаны, бас, остальное. "
   59 [code      ]         "Это нужно ТОЛЬКО для АНАЛИЗА — как устроен грув, где хук, где дроп. "
   60 [code      ]         "Никакого копирования! Прямое заимствование стемов отключено.",
   61 [code      ]         "action": "Закинь трек и нажми 'Разобрать на стемы'.",
   62 [code      ]         "tab": "② Стемы",
   63 [code      ]     },
   64 [code      ]     {
   65 [code      ]         "id": "groove",
   66 [code      ]         "title": "③ Rhythm DNA",
   67 [code      ]         "text": "НОВОЕ: извлекает ритмическую ДНК из референса. "
   68 [code      ]         "Не ноты и не лупы, а абстрактный groove template: "
   69 [code      ]         "где кик, где снейр, плотность хэта, свинг, triplet-rolls. "
   70 [code      ]         "Потом этот шаблон пересобирается ДРУГИМИ звуками — "
   71 [code      ]         "похожий ритм, но оригинальное звучание.",
   72 [code      ]         "action": "Выбери референс и извлеки groove.",
   73 [code      ]         "tab": "③ Rhythm DNA",
   74 [code      ]     },
   75 [code      ]     {
   76 [code      ]         "id": "samples",
   77 [code      ]         "title": "④ Сэмплы — наше всё!",
   78 [code      ]         "text": "Три режима:\n"
   79 [code      ]         "• Find Online — поиск бесплатных сэмплов (Freesound, Pixabay)\n"
   80 [code      ]         "• Pick From Library — из локальной библиотеки\n"
   81 [code      ]         "• Upload My Sample — загрузить свой звук\n"
   82 [code      ]         "Фильтры по жанру, BPM, тональности, лицензии. "
   83 [code      ]         "Каждый сэмпл регистрируется в Provenance Manager "
   84 [code      ]         "(отслеживание лицензий для безопасности).",
   85 [code      ]         "action": "Попробуй найти сэмплы по запросу 'phonk 808'.",
   86 [code      ]         "tab": "④ Сэмплы",
   87 [code      ]     },
   88 [code      ]     {
   89 [code      ]         "id": "beat",
   90 [code      ]         "title": "⑤ Конструктор бита (ЯДРО)",
   91 [code      ]         "text": "Это ГЛАВНОЕ для твоего железа (RX 580 4GB). "
   92 [code      ]         "Бит собирается из сэмплов + groove template, а не из нейронки. "
   93 [code      ]         "Ты указываешь: длительность, количество куплетов/припевов, "
   94 [code      ]         "агрессию/качёвость. Программа собирает аранжировку из блоков: "
   95 [code      ]         "intro → verse → pre_chorus → hook → verse → hook → outro. "
   96 [code      ]         "Делает вариации: смена хэта, фильтр перед дропом, стоп-таймы. "
   97 [code      ]         "MusicGen (вкладка Текстуры) — для атмосферы и FX, не для основного бита.",
   98 [code      ]         "action": "Нажми 'Собрать бит' с groove из шага ③.",
   99 [code      ]         "tab": "⑤ Бит",
  100 [code      ]     },
  101 [code      ]     {
  102 [code      ]         "id": "textures",
  103 [code      ]         "title": "⑥ Нейро-текстуры (MusicGen)",
  104 [code      ]         "text": "MusicGen работает на CPU (медленно на RX 580, но работает). "
  105 [code      ]         "Используется ТОЛЬКО для: атмосферы, этнических пэдов, "
  106 [code      ]         "переходных FX, набросков хука. Не как основной движок! "
  107 [code      ]         "Когда купишь карту на 12GB — здесь можно будет генерить "
  108 [code      ]         "более жирные текстуры.",
  109 [code      ]         "action": "Сгенерируй 15-сек текстуру для интро.",
  110 [code      ]         "tab": "⑥ Текстуры",
  111 [code      ]     },
  112 [code      ]     {
  113 [code      ]         "id": "lyrics",
  114 [code      ]         "title": "⑦ Текст",
  115 [code      ]         "text": "Три источника:\n"
  116 [code      ]         "1. Твои идеи — тема, слова, эмоции\n"
  117 [code      ]         "2. Анализ референсов — транскрипция через Whisper\n"
  118 [code      ]         "3. Тренд-агент — ищет сленг и мемы в интернете\n"
  119 [code      ]         "Ollama (Llama 3) генерирует текст локально. "
  120 [code      ]         "Lyric Vault хранит все удачные строки, панчи, хуки. "
  121 [code      ]         "Тегируй их: заезжено/свежо/сильно/под лето/под машину. "
  122 [code      ]         "Можешь написать текст сам — просто вставь его.",
  123 [code      ]         "action": "Напиши тему и сгенерируй текст.",
  124 [code      ]         "tab": "⑦ Текст",
  125 [code      ]     },
  126 [code      ]     {
  127 [code      ]         "id": "voice",
  128 [code      ]         "title": "⑧ Голос — АНТИ-ПАЛЕВО (САМОЕ ВАЖНОЕ)",
  129 [code      ]         "text": "Voice Vault — постоянное хранилище твоего голоса. "
  130 [code      ]         "Чем больше записей — тем лучше модель. "
  131 [code      ]         "ПРОЦЕСС:\n"
  132 [code      ]         "1. Жми 'Дай текст для записи' → получишь текст + стиль\n"
  133 [code      ]         "2. Запиши через микрофон (8 стилей: медленно/громко/шёпот/пение...)\n"
  134 [code      ]         "3. Сохраняй в Voice Vault\n"
  135 [code      ]         "4. Повтори 20-50 раз (цель: ≥5 минут)\n"
  136 [code      ]         "5. Жми 'Обучить модель' — RVC дообучится\n\n"
  137 [code      ]         "Два режима вокала:\n"
  138 [code      ]         "• Lazy: Bark озвучивает текст → RVC подменяет тембр\n"
  139 [code      ]         "• Pro: ты поёшь в караоке → RVC полирует\n\n"
  140 [code      ]         "Программа отслеживает phoneme coverage — каких звуков не хватает.",
  141 [code      ]         "action": "Запиши первый сэмпл голоса прямо сейчас!",
  142 [code      ]         "tab": "⑧ Голос",
  143 [code      ]     },
  144 [code      ]     {
  145 [code      ]         "id": "karaoke",
  146 [code      ]         "title": "⑧-б Караоке-запись",
  147 [code      ]         "text": "Для режима Pro: программа генерирует 'как должно звучать' "
  148 [code      ]         "(референс-вокал), показывает текст с подсветкой слов, "
  149 [code      ]         "включает бит. Ты поёшь в микрофон, слыша референс в наушниках. "
  150 [code      ]         "Потом RVC полирует твой вокал под твой же голос.",
  151 [code      ]         "action": "Попробуй караоке-режим с готовым текстом.",
  152 [code      ]         "tab": "⑧ Голос",
  153 [code      ]     },
  154 [code      ]     {
  155 [code      ]         "id": "humanization",
  156 [code      ]         "title": "⑨ Анти-нейроношность",
  157 [code      ]         "text": "Проверяет вокал на AI-признаки:\n"
  158 [code      ]         "• слишком ровная динамика\n"
  159 [code      ]         "• смазанные согласные\n"
  160 [code      ]         "• переавтотюненность\n"
  161 [code      ]         "• 'ghost harmonies'\n"
  162 [code      ]         "Humanization Layer добавляет живости:\n"
  163 [code      ]         "• микро-timing сдвиги\n"
  164 [code      ]         "• дыхание в паузах\n"
  165 [code      ]         "• разные динамики между секциями\n"
  166 [code      ]         "• нормальную развязку (fade вместо обрубания)",
  167 [code      ]         "action": "Проверь вокал на AI-признаки.",
  168 [code      ]         "tab": "⑨ Humanization",
  169 [code      ]     },
  170 [code      ]     {
  171 [code      ]         "id": "mix",
  172 [code      ]         "title": "⑩ Финальный микс",
  173 [code      ]         "text": "Склеивает бит + вокал, добавляет sidechain-компрессию, "
  174 [code      ]         "эквалайзер. Matchering подгоняет мастеринг под ЛЮБОЙ "
  175 [code      ]         "выбранный референс (не только один трек). "
  176 [code      ]         "Ты сегодня ориентируешься на один трек, завтра на другой — "
  177 [code      ]         "движок универсальный.",
  178 [code      ]         "action": "Загрузи beat, vocal и reference — нажми 'Собрать'.",
  179 [code      ]         "tab": "⑩ Микс",
  180 [code      ]     },
  181 [code      ]     {
  182 [code      ]         "id": "release",
  183 [code      ]         "title": "⑪ Релиз-пакет",
  184 [code      ]         "text": "Создаёт полный пакет для публикации:\n"
  185 [code      ]         "• WAV 24-bit master\n"
  186 [code      ]         "• MP3 320\n"
  187 [code      ]         "• FLAC\n"
  188 [code      ]         "• instrumental\n"
  189 [code      ]         "• acapella\n"
  190 [code      ]         "• TikTok edit (30 сек)\n"
  191 [code      ]         "• lyrics.txt\n"
  192 [code      ]         "• recipe.json (как сделано)\n"
  193 [code      ]         "• sample_manifest.json (лицензии)\n"
  194 [code      ]         "• release_notes.txt\n"
  195 [code      ]         "• metadata.json (для дистрибуции)",
  196 [code      ]         "action": "Собери релиз-пакет из готового трека.",
  197 [code      ]         "tab": "⑪ Релиз",
  198 [code      ]     },
  199 [code      ]     {
  200 [code      ]         "id": "autopilot",
  201 [code      ]         "title": "🚀 Полный автопилот",
  202 [code      ]         "text": "Один клик — весь пайплайн: референсы → анализ → groove → "
  203 [code      ]         "сэмплы → бит → текст → вокал → RVC → humanization → микс → "
  204 [code      ]         "релиз. Для ленивых дней. "
  205 [code      ]         "Программа становится умнее с каждым использованием: "
  206 [code      ]         "Voice Vault копится, Lyric Vault пополняется, "
  207 [code      ]         "анализы кэшируются.",
  208 [code      ]         "action": "Попробуй автопилот!",
  209 [code      ]         "tab": "🚀 Автопилот",
  210 [code      ]     },
  211 [code      ]     {
  212 [code      ]         "id": "done",
  213 [code      ]         "title": "🎉 Туториал завершён!",
  214 [code      ]         "text": "Теперь ты знаешь весь функционал. "
  215 [code      ]         "Начни с записи голоса (вкладка ⑧) — это самое важное для "
  216 [code      ]         "анти-палева. Потом анализируй референсы и собирай биты. "
  217 [code      ]         "Удачи в создании хитов! 🎧🔥",
  218 [code      ]         "action": "Туториал можно пройти заново в любое время.",
  219 [code      ]         "tab": None,
  220 [code      ]     },
  221 [code      ] ]
  222 [blank     ] 
  223 [blank     ] 
  224 [def       ] def get_tutorial_settings() -> dict:
  225 [branch    ]     if os.path.exists(SETTINGS_FILE):
  226 [try_block ]         try:
  227 [return    ]             return json.load(open(SETTINGS_FILE, encoding="utf-8"))
  228 [try_block ]         except Exception:
  229 [return    ]             return {}
  230 [return    ]     return {"enabled": True, "current_step": 0, "completed": False}
  231 [blank     ] 
  232 [blank     ] 
  233 [def       ] def save_tutorial_settings(settings: dict):
  234 [code      ]     json.dump(
  235 [code      ]         settings,
  236 [code      ]         open(SETTINGS_FILE, "w", encoding="utf-8"),
  237 [code      ]         ensure_ascii=False,
  238 [code      ]         indent=2,
  239 [code      ]     )
  240 [blank     ] 
  241 [blank     ] 
  242 [def       ] def get_step(index: int) -> dict:
  243 [branch    ]     if 0 <= index < len(STEPS):
  244 [return    ]         return STEPS[index]
  245 [return    ]     return None
  246 [blank     ] 
  247 [blank     ] 
  248 [def       ] def next_step() -> dict:
  249 [code      ]     settings = get_tutorial_settings()
  250 [code      ]     idx = settings.get("current_step", 0)
  251 [branch    ]     if idx < len(STEPS) - 1:
  252 [code      ]         settings["current_step"] = idx + 1
  253 [code      ]         save_tutorial_settings(settings)
  254 [return    ]         return get_step(idx + 1)
  255 [code      ]     settings["completed"] = True
  256 [code      ]     save_tutorial_settings(settings)
  257 [return    ]     return {
  258 [code      ]         "id": "done",
  259 [code      ]         "title": "Завершено",
  260 [code      ]         "text": "Туториал пройден!",
  261 [code      ]         "action": "",
  262 [code      ]     }
  263 [blank     ] 
  264 [blank     ] 
  265 [def       ] def prev_step() -> dict:
  266 [code      ]     settings = get_tutorial_settings()
  267 [code      ]     idx = settings.get("current_step", 0)
  268 [branch    ]     if idx > 0:
  269 [code      ]         settings["current_step"] = idx - 1
  270 [code      ]         save_tutorial_settings(settings)
  271 [return    ]         return get_step(idx - 1)
  272 [return    ]     return get_step(0)
  273 [blank     ] 
  274 [blank     ] 
  275 [def       ] def skip_tutorial():
  276 [code      ]     settings = get_tutorial_settings()
  277 [code      ]     settings["enabled"] = False
  278 [code      ]     settings["completed"] = True
  279 [code      ]     save_tutorial_settings(settings)
  280 [blank     ] 
  281 [blank     ] 
  282 [def       ] def reset_tutorial():
  283 [code      ]     settings = {"enabled": True, "current_step": 0, "completed": False}
  284 [code      ]     save_tutorial_settings(settings)
  285 [blank     ] 
  286 [blank     ] 
  287 [def       ] def get_total_steps() -> int:
  288 [return    ]     return len(STEPS)
  289 [blank     ] 
  290 [blank     ] 
  291 [branch    ] if __name__ == "__main__":
  292 [loop      ]     for i, s in enumerate(STEPS):
  293 [code      ]         print(f"{i+1}. {s['title']}")
```