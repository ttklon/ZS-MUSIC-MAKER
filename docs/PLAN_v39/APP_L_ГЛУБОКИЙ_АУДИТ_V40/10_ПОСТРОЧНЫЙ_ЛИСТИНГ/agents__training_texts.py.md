# ПОСТРОЧНЫЙ ЛИСТИНГ: `agents/training_texts.py`

**Всего строк:** 140

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 97 | 69.3 |
| blank | 20 | 14.3 |
| docstring | 8 | 5.7 |
| def | 5 | 3.6 |
| return | 5 | 3.6 |
| import | 2 | 1.4 |
| branch | 2 | 1.4 |
| loop | 1 | 0.7 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] Agent: TrainingTexts v2
    3 [docstring ] Банк текстов в 8 стилях + отслеживание прогресса + phoneme coverage.
    4 [docstring ] Стили: slow_clear, fast_loud, fast_quiet, conversational, aggressive,
    5 [docstring ]        whisper, singing, phonetics_panagrams.
    6 [docstring ] """
    7 [blank     ] 
    8 [import    ] import json
    9 [import    ] import os
   10 [blank     ] 
   11 [code      ] TEXTS_DIR = os.path.join(os.path.dirname(__file__), "..", "training_texts")
   12 [code      ] os.makedirs(TEXTS_DIR, exist_ok=True)
   13 [blank     ] 
   14 [blank     ] 
   15 [code      ] BANK = {
   16 [code      ]     "slow_clear": [
   17 [code      ]         "На заре туманной юности всей душой любил я милую. Речь моя течёт спокойно, каждый звук произношу отчётливо и ясно.",
   18 [code      ]         "Широкая электрификация южных губерний даст мощный толчок подъёму сельского хозяйства. Читаю ровно, без спешки, каждый слог.",
   19 [code      ]         "В чащах юга жил бы цитрус? Да, но фальшивый экземпляр! Прогоняю панграмму медленно, чётко, без запинки.",
   20 [code      ]         "Корабли лавировали, лавировали, да не вылавировали. Тренирую дикцию, каждый согласный звучит чисто.",
   21 [code      ]         "Река течёт, ветер дует, солнце светит. Простые слова, медленный темп, полная концентрация на артикуляции.",
   22 [code      ]     ],
   23 [code      ]     "fast_loud": [
   24 [code      ]         "Погнали, качает лето, тачка чёрный мерс, бабки в руках, стайл на максимум, движ по району, флоу как надо!",
   25 [code      ]         "Всё горит, всё летит, всё качает, я на волне, я в движе, я поднимаю чек, слышишь как басит!",
   26 [code      ]         "Дави на газ, врубай на полную, район наш, ночь наша, тачка ревёт, движ поднимает волну!",
   27 [code      ]         "Бам, бам, качает, раз, два, три, четыре, флоу летит, не догонишь, стиль мой, вайб мой, двигаю дальше!",
   28 [code      ]         "Погнали, погнали, всё летит, всё качает, мы на вершине, мы поднимаем, мы не тормозим, полный газ!",
   29 [code      ]     ],
   30 [code      ]     "fast_quiet": [
   31 [code      ]         "Тихо шепчу быстро-быстро, но каждый звук слышно, каждый слог на месте, движ идёт под покровом ночи.",
   32 [code      ]         "Быстрый шёпот сквозь зубы, слова летят потоком, но громкость на минимуме, атмосфера напряжённая.",
   33 [code      ]         "Слышь, тихо, быстро, двигаем, тёмная ночь, тихий шёпот, слова как тени, но всё понятно без слов.",
   34 [code      ]     ],
   35 [code      ]     "conversational": [
   36 [code      ]         "Ну слушай, короче, вчера был движ, приехали пацаны, музыка качала, тачки стояли красивые, вайб был огонь.",
   37 [code      ]         "Да ладно, ты серьёзно? Ну вообще норм получилось, я думал будет хуже, а вышло прям в тему.",
   38 [code      ]         "Знаешь что, я тебе так скажу — если делать, то делать нормально, иначе вообще не стоит начинать.",
   39 [code      ]         "Слушай, я тут подумал, может замутим что-нибудь этакое? Чтоб прям качало, чтоб все услышали и зашли.",
   40 [code      ]         "Ну ты понимаешь, да? Когда всё сходится — бит, голос, текст — вот тогда оно летит. А так — пустое.",
   41 [code      ]     ],
   42 [code      ]     "aggressive": [
   43 [code      ]         "Отойди с дороги, я иду по своему пути, никто меня не остановит, я поднимаю всё что вижу!",
   44 [code      ]         "Слышишь как рычит мотор, слышишь как басит колонка, я на своей волне, я не тормозю никогда!",
   45 [code      ]         "Рвём, метём, не остановимся, полный газ, полный огонь, мы здесь чтобы забрать всё!",
   46 [code      ]         "Кто тут? Я тут! Кто движет? Я движу! Кто поднимает? Я поднимаю! Слышишь меня? Я не шепчу!",
   47 [code      ]     ],
   48 [code      ]     "whisper": [
   49 [code      ]         "Тише-тише, никому не говори, это только между нами, шёпотом на ухо, ночь скрывает секреты.",
   50 [code      ]         "Дыхание сдержано, голос почти не слышен, слова растворяются в темноте, но смысл кристально ясен.",
   51 [code      ]         "Шшш... тихо... они не должны знать... только мы... только сейчас... шёпотом...",
   52 [code      ]     ],
   53 [code      ]     "singing": [
   54 [code      ]         "Ля-ля-ля, а-а-а-а, о-о-о-о, у-у-у, распеваю гласные, тяну ноты, держу тональность стабильно.",
   55 [code      ]         "Мммм-аааа, ммммм-эээ, ммммм-иии — вокализ по нотам от низа к верху и обратно, плавно.",
   56 [code      ]         "О-о-о, лето-о-о, дви-и-иж, тач-ки, баб-ки — пою слоги ритмично, тяну гласные, чёткие согласные.",
   57 [code      ]         "А-а-а, мотив простой, повторяю, вариирую, от тихого к громкому, от низа к верху, пою свободно.",
   58 [code      ]     ],
   59 [code      ]     "phonetics_panagrams": [
   60 [code      ]         "Съешь же ещё этих мягких французских булок, да выпей чаю. Панграмма покрывает все буквы алфавита.",
   61 [code      ]         "В чащах юга жил бы цитрус? Да, но фальшивый экземпляр! Все 33 буквы русского языка присутствуют.",
   62 [code      ]         "Шёл флегматичный дядя Фёдор через мост, шурша листвой и жуя щавель, экзотично щурясь.",
   63 [code      ]         "Эй, ёж, притащи мне кукурузу, шишку, жёлудь и чашку чаю! Все гласные и согласные на месте.",
   64 [code      ]         "Дробясь, дробясь, дробясь — жуём щёчкой, жуём щёчкой. Тренируем щелевые и аффрикаты.",
   65 [code      ]     ],
   66 [code      ] }
   67 [blank     ] 
   68 [blank     ] 
   69 [def       ] def get_next_text(style: str = None) -> dict:
   70 [docstring ]     """Возвращает следующий текст для записи. Балансирует по стилям."""
   71 [code      ]     idx_file = os.path.join(TEXTS_DIR, "progress.json")
   72 [code      ]     progress = (
   73 [code      ]         json.load(open(idx_file, encoding="utf-8")) if os.path.exists(idx_file) else {}
   74 [code      ]     )
   75 [blank     ] 
   76 [branch    ]     if style is None:
   77 [code      ]         counts = {s: progress.get(s, 0) for s in BANK}
   78 [code      ]         style = min(counts, key=counts.get)
   79 [blank     ] 
   80 [code      ]     variants = BANK.get(style, BANK["slow_clear"])
   81 [code      ]     used = progress.get(style, 0)
   82 [code      ]     text = variants[used % len(variants)]
   83 [blank     ] 
   84 [code      ]     progress[style] = used + 1
   85 [code      ]     json.dump(
   86 [code      ]         progress, open(idx_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2
   87 [code      ]     )
   88 [blank     ] 
   89 [return    ]     return {
   90 [code      ]         "style": style,
   91 [code      ]         "text": text,
   92 [code      ]         "instruction": _instruction(style),
   93 [code      ]         "min_duration_sec": 8,
   94 [code      ]         "progress": progress,
   95 [code      ]         "styles_remaining": _styles_remaining(progress),
   96 [code      ]     }
   97 [blank     ] 
   98 [blank     ] 
   99 [def       ] def _styles_remaining(progress: dict) -> list:
  100 [return    ]     return [s for s in BANK if progress.get(s, 0) < len(BANK[s])]
  101 [blank     ] 
  102 [blank     ] 
  103 [def       ] def _instruction(style: str) -> str:
  104 [return    ]     return {
  105 [code      ]         "slow_clear": "Читай МЕДЛЕННО и ЧЁТКО. Каждый слог отдельно. Громкость средняя.",
  106 [code      ]         "fast_loud": "Читай БЫСТРО и ГРОМКО. Эмоционально, с напором. Не тормози!",
  107 [code      ]         "fast_quiet": "Читай БЫСТРО, но ТИХО. Шёпот на скорости. Слова всё равно чёткие.",
  108 [code      ]         "conversational": "Читай как в обычном разговоре с другом. Расслабленно, естественно.",
  109 [code      ]         "aggressive": "Читай АГРЕССИВНО, зло, с рычанием. Дави на согласные!",
  110 [code      ]         "whisper": "Читай ШЁПОТОМ, очень тихо. Дыхание слышно, слова шёлковые.",
  111 [code      ]         "singing": "ПОЙ, тяни ноты. Не читай — пой. Гласные длинные, согласные короткие.",
  112 [code      ]         "phonetics_panagrams": "Читай выразительно, все звуки чётко. Каждая буква алфавита должна прозвучать.",
  113 [code      ]     }.get(style, "Читай как удобно.")
  114 [blank     ] 
  115 [blank     ] 
  116 [def       ] def all_styles() -> list:
  117 [return    ]     return list(BANK.keys())
  118 [blank     ] 
  119 [blank     ] 
  120 [def       ] def progress_summary() -> dict:
  121 [docstring ]     """Сводка прогресса по всем стилям."""
  122 [code      ]     idx_file = os.path.join(TEXTS_DIR, "progress.json")
  123 [code      ]     progress = (
  124 [code      ]         json.load(open(idx_file, encoding="utf-8")) if os.path.exists(idx_file) else {}
  125 [code      ]     )
  126 [code      ]     summary = {}
  127 [loop      ]     for style in BANK:
  128 [code      ]         done = progress.get(style, 0)
  129 [code      ]         total = len(BANK[style])
  130 [code      ]         summary[style] = {
  131 [code      ]             "recorded": done,
  132 [code      ]             "available": total,
  133 [code      ]             "complete": done >= total,
  134 [code      ]             "pct": round(done / total * 100, 1) if total > 0 else 0,
  135 [code      ]         }
  136 [return    ]     return summary
  137 [blank     ] 
  138 [blank     ] 
  139 [branch    ] if __name__ == "__main__":
  140 [code      ]     print(json.dumps(get_next_text(), ensure_ascii=False, indent=2))
```