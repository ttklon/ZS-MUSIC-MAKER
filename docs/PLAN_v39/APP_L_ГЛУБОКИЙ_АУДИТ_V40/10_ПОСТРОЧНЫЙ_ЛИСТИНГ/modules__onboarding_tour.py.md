# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/onboarding_tour.py`

**Всего строк:** 213

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 139 | 65.3 |
| blank | 27 | 12.7 |
| docstring | 14 | 6.6 |
| def | 9 | 4.2 |
| return | 7 | 3.3 |
| branch | 6 | 2.8 |
| import | 5 | 2.3 |
| try_block | 4 | 1.9 |
| loop | 2 | 0.9 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v10 — Interactive Onboarding Tour
    3 [docstring ] ==================================================
    4 [docstring ] Пошаговый интерактивный тур (ТЗ 5, «ONBOARDING»).
    5 [blank     ] 
    6 [docstring ] Framework-agnostic — работает и с PySide6, и с Gradio, и в консоли.
    7 [docstring ] Данные тура: 15 шагов на русском, каждый привязан к элементу wizard'а.
    8 [docstring ] """
    9 [blank     ] 
   10 [import    ] from __future__ import annotations
   11 [blank     ] 
   12 [import    ] import json
   13 [import    ] import logging
   14 [import    ] from pathlib import Path
   15 [import    ] from typing import Any
   16 [blank     ] 
   17 [code      ] log = logging.getLogger("zsmm.tour")
   18 [blank     ] 
   19 [blank     ] 
   20 [def       ] def _tour_state_path() -> Path:
   21 [docstring ]     """v34 FIX (P3.26): раньше путь был относительным `Path("tutorial_settings.json")` —
   22 [docstring ]     т.е. зависел от CWD: при запуске из другой папки создавался дубль-файл,
   23 [docstring ]     а прогресс тура терялся. Теперь единый путь data/tutorial_settings.json
   24 [docstring ]     с миграцией старого файла из корня репозитория."""
   25 [code      ]     root = Path(__file__).resolve().parents[1]
   26 [code      ]     new = root / "data" / "tutorial_settings.json"
   27 [code      ]     old_root = root / "tutorial_settings.json"
   28 [code      ]     old_cwd = Path("tutorial_settings.json")
   29 [try_block ]     try:
   30 [code      ]         new.parent.mkdir(parents=True, exist_ok=True)
   31 [branch    ]         if not new.exists():
   32 [loop      ]             for cand in (old_root, old_cwd):
   33 [branch    ]                 if cand.exists() and cand.resolve() != new.resolve():
   34 [code      ]                     new.write_text(cand.read_text(encoding="utf-8"), encoding="utf-8")
   35 [code      ]                     break
   36 [try_block ]     except Exception as e:
   37 [code      ]         log.warning(f"tour state migration failed: {e}")
   38 [return    ]     return new
   39 [blank     ] 
   40 [blank     ] 
   41 [code      ] TOUR_STATE = _tour_state_path()
   42 [blank     ] 
   43 [code      ] TOUR_STEPS: list[dict[str, Any]] = [
   44 [code      ]     {
   45 [code      ]         "id": "welcome",
   46 [code      ]         "title": "Привет!",
   47 [code      ]         "text": "Это ZS Music Maker v10. Тур займёт 3 минуты. "
   48 [code      ]         "После него ты сможешь собрать свой первый трек за 10 минут.",
   49 [code      ]         "action": "next",
   50 [code      ]         "anchor": None,
   51 [code      ]     },
   52 [code      ]     {
   53 [code      ]         "id": "artist_name",
   54 [code      ]         "title": "Твоё имя",
   55 [code      ]         "text": "Введи артист-имя. Оно пойдёт в ID3-теги и на обложку.",
   56 [code      ]         "action": "input",
   57 [code      ]         "anchor": "artist_name_field",
   58 [code      ]     },
   59 [code      ]     {
   60 [code      ]         "id": "references",
   61 [code      ]         "title": "Референсы",
   62 [code      ]         "text": "Загрузи 1–7 треков, которые задают вайб. Можешь указать вес каждого.",
   63 [code      ]         "action": "highlight",
   64 [code      ]         "anchor": "step1_references",
   65 [code      ]     },
   66 [code      ]     {
   67 [code      ]         "id": "weights",
   68 [code      ]         "title": "Вес референсов",
   69 [code      ]         "text": "Слайдеры справа: например, 50% вайб первого + 30% ритм второго. "
   70 [code      ]         "Программа смешает.",
   71 [code      ]         "action": "highlight",
   72 [code      ]         "anchor": "weight_sliders",
   73 [code      ]     },
   74 [code      ]     {
   75 [code      ]         "id": "length",
   76 [code      ]         "title": "Длительность",
   77 [code      ]         "text": "Ползунок от 1:30 до 3:20+. Для TikTok-хита оптимум 2:00-2:30.",
   78 [code      ]         "action": "highlight",
   79 [code      ]         "anchor": "length_slider",
   80 [code      ]     },
   81 [code      ]     {
   82 [code      ]         "id": "style",
   83 [code      ]         "title": "Пресет стиля",
   84 [code      ]         "text": "Trap, Turkish-pop, phonk, hyperpop... Или свой микс.",
   85 [code      ]         "action": "highlight",
   86 [code      ]         "anchor": "style_preset",
   87 [code      ]     },
   88 [code      ]     {
   89 [code      ]         "id": "samples",
   90 [code      ]         "title": "Сэмплы",
   91 [code      ]         "text": "Split-view: локальные слева, Freesound/Wikimedia справа. "
   92 [code      ]         "Фильтр по CC0 включён по умолчанию.",
   93 [code      ]         "action": "highlight",
   94 [code      ]         "anchor": "sample_browser",
   95 [code      ]     },
   96 [code      ]     {
   97 [code      ]         "id": "lyrics",
   98 [code      ]         "title": "Текст",
   99 [code      ]         "text": "Три источника: твои строки, транскрипция референсов, Trend Scout. "
  100 [code      ]         "Все твои строки на 100% попадут в трек.",
  101 [code      ]         "action": "highlight",
  102 [code      ]         "anchor": "lyrics_editor",
  103 [code      ]     },
  104 [code      ]     {
  105 [code      ]         "id": "voice_vault",
  106 [code      ]         "title": "Voice Vault",
  107 [code      ]         "text": "Здесь копится твой голос. Записывай короткие фразы в разных стилях. "
  108 [code      ]         "Через 5-10 минут — RVC натренит модель.",
  109 [code      ]         "action": "highlight",
  110 [code      ]         "anchor": "voice_vault",
  111 [code      ]     },
  112 [code      ]     {
  113 [code      ]         "id": "karaoke",
  114 [code      ]         "title": "Караоке",
  115 [code      ]         "text": "В Pro-режиме открывается окно записи с подсветкой слов, "
  116 [code      ]         "метрономом и регулятором громкости эталона в ушах.",
  117 [code      ]         "action": "highlight",
  118 [code      ]         "anchor": "karaoke_button",
  119 [code      ]     },
  120 [code      ]     {
  121 [code      ]         "id": "polish",
  122 [code      ]         "title": "Anti-neuro polish",
  123 [code      ]         "text": "Экспертные опции: gentle / standard / aggressive. "
  124 [code      ]         "Устраняет «пластмассовый» вокал.",
  125 [code      ]         "action": "highlight",
  126 [code      ]         "anchor": "polish_dropdown",
  127 [code      ]     },
  128 [code      ]     {
  129 [code      ]         "id": "stands",
  130 [code      ]         "title": "Стенды",
  131 [code      ]         "text": "Каждый релиз даёт 3 мастера: car -8.5, club -6.5, streaming -14 LUFS. "
  132 [code      ]         "Проверь в машине!",
  133 [code      ]         "action": "highlight",
  134 [code      ]         "anchor": "stands_toggle",
  135 [code      ]     },
  136 [code      ]     {
  137 [code      ]         "id": "release_pack",
  138 [code      ]         "title": "Релиз-пакет",
  139 [code      ]         "text": "После рендера: WAV/MP3/FLAC + инструментал + акапелла + стемы + "
  140 [code      ]         "TikTok/Reels + обложка + LRC + метаданные.",
  141 [code      ]         "action": "highlight",
  142 [code      ]         "anchor": "release_folder",
  143 [code      ]     },
  144 [code      ]     {
  145 [code      ]         "id": "hit_score",
  146 [code      ]         "title": "HIT SCORE",
  147 [code      ]         "text": "12 метрик оценят чарт-потенциал. Вердикт + список конкретных доработок.",
  148 [code      ]         "action": "highlight",
  149 [code      ]         "anchor": "hit_score_widget",
  150 [code      ]     },
  151 [code      ]     {
  152 [code      ]         "id": "finish",
  153 [code      ]         "title": "Готово!",
  154 [code      ]         "text": "Тур завершён. Начни с загрузки одного референса — программа проведёт дальше. "
  155 [code      ]         "Тур можно перезапустить в меню Помощь.",
  156 [code      ]         "action": "finish",
  157 [code      ]         "anchor": None,
  158 [code      ]     },
  159 [code      ] ]
  160 [blank     ] 
  161 [blank     ] 
  162 [def       ] def load_state() -> dict[str, Any]:
  163 [branch    ]     if TOUR_STATE.exists():
  164 [try_block ]         try:
  165 [return    ]             return json.loads(TOUR_STATE.read_text(encoding="utf-8"))
  166 [try_block ]         except Exception:
  167 [code      ]             pass
  168 [return    ]     return {"tour_done": False, "last_step": 0}
  169 [blank     ] 
  170 [blank     ] 
  171 [def       ] def save_state(state: dict[str, Any]) -> None:
  172 [code      ]     TOUR_STATE.write_text(
  173 [code      ]         json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
  174 [code      ]     )
  175 [blank     ] 
  176 [blank     ] 
  177 [def       ] def should_show() -> bool:
  178 [return    ]     return not load_state().get("tour_done", False)
  179 [blank     ] 
  180 [blank     ] 
  181 [def       ] def steps() -> list[dict[str, Any]]:
  182 [return    ]     return list(TOUR_STEPS)
  183 [blank     ] 
  184 [blank     ] 
  185 [def       ] def get_step(idx: int) -> dict[str, Any] | None:
  186 [branch    ]     if 0 <= idx < len(TOUR_STEPS):
  187 [return    ]         return TOUR_STEPS[idx]
  188 [return    ]     return None
  189 [blank     ] 
  190 [blank     ] 
  191 [def       ] def mark_done() -> None:
  192 [code      ]     save_state({"tour_done": True, "last_step": len(TOUR_STEPS) - 1})
  193 [blank     ] 
  194 [blank     ] 
  195 [def       ] def reset() -> None:
  196 [code      ]     save_state({"tour_done": False, "last_step": 0})
  197 [blank     ] 
  198 [blank     ] 
  199 [def       ] def run_console_demo() -> None:
  200 [docstring ]     """
  201 [docstring ]     Демо-тур в консоли (для CI и slow-железа).
  202 [docstring ]     """
  203 [loop      ]     for i, step in enumerate(TOUR_STEPS):
  204 [code      ]         print(f"\n=== Шаг {i+1}/{len(TOUR_STEPS)}: {step['title']} ===")
  205 [code      ]         print(step["text"])
  206 [branch    ]         if step.get("anchor"):
  207 [code      ]             print(f"  → элемент интерфейса: {step['anchor']}")
  208 [code      ]     mark_done()
  209 [code      ]     print("\nТур завершён.")
  210 [blank     ] 
  211 [blank     ] 
  212 [branch    ] if __name__ == "__main__":
  213 [code      ]     run_console_demo()
```