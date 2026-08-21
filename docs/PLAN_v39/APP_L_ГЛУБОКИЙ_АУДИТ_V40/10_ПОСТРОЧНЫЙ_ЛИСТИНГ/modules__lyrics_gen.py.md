# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/lyrics_gen.py`

**Всего строк:** 310

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 185 | 59.7 |
| blank | 40 | 12.9 |
| docstring | 20 | 6.5 |
| branch | 16 | 5.2 |
| return | 12 | 3.9 |
| comment | 9 | 2.9 |
| def | 9 | 2.9 |
| loop | 8 | 2.6 |
| import | 6 | 1.9 |
| try_block | 4 | 1.3 |
| stmt | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] lyrics_gen.py — генератор текстов с ОБЯЗАТЕЛЬНЫМ впитыванием
    3 [docstring ] пользовательских строк и bilingual структурой (RU куплеты + EN хуки).
    4 [blank     ] 
    5 [docstring ] Источники (по ТЗ 3.7):
    6 [docstring ]   1. Ollama (Llama 3) — если локально запущено
    7 [docstring ]   2. Trend-Scout — актуальные темы и сленг из интернета
    8 [docstring ]   3. Lyric Vault — локальное хранилище идей
    9 [docstring ]   4. Fallback — шаблонный генератор на встроенных панчах
   10 [blank     ] 
   11 [docstring ] Ключевое требование ТЗ 20.2 (вопрос 3): user_lyrics_lines — если
   12 [docstring ] пользователь указал свои строки, они ОБЯЗАНЫ попасть в трек, дословно.
   13 [docstring ] """
   14 [blank     ] 
   15 [import    ] from __future__ import annotations
   16 [blank     ] 
   17 [import    ] import json
   18 [import    ] import random
   19 [import    ] import time
   20 [import    ] from pathlib import Path
   21 [blank     ] 
   22 [code      ] ROOT = Path(__file__).resolve().parents[1]
   23 [code      ] VAULT_DIR = ROOT / "lyric_vault"
   24 [comment   ] # v22: ленивое создание (не при импорте)
   25 [blank     ] 
   26 [code      ] LYRIC_MEMORY = VAULT_DIR / "lyrics_memory.jsonl"
   27 [code      ] SLANG_FILE = VAULT_DIR / "slang.txt"
   28 [blank     ] 
   29 [comment   ] # Панчи по темам — используются как fallback и как затравка для Llama
   30 [code      ] PUNCHES_RU = {
   31 [code      ]     "лето": [
   32 [code      ]         "солнце жарит, плавит асфальт",
   33 [code      ]         "лето без страховки, полный газ вдаль",
   34 [code      ]         "тачка без крыши, ветер в лицо",
   35 [code      ]         "закат на Стамбул, золотое кольцо",
   36 [code      ]         "море, деньги, драйв — это наш финал",
   37 [code      ]         "жаркие ночи, танцпол закипал",
   38 [code      ]         "песок под ногами, ритм в груди",
   39 [code      ]         "лето не кончится, всё впереди",
   40 [code      ]     ],
   41 [code      ]     "тачки": [
   42 [code      ]         "Supra рвёт тишину, турбина свистит",
   43 [code      ]         "AMG в ночи, как чёрный магнит",
   44 [code      ]         "мотор кричит, просит ещё",
   45 [code      ]         "полёт по трассе, время течёт",
   46 [code      ]         "дрифт в тумане, жжёная резина",
   47 [code      ]         "скорость — мой яд, адреналин — бензин",
   48 [code      ]         "низкий клиренс, дерзкий обвес",
   49 [code      ]         "мы короли улиц, у нас есть вес",
   50 [code      ]     ],
   51 [code      ]     "деньги": [
   52 [code      ]         "кэш на кэше, стопки до небес",
   53 [code      ]         "чек за чеком, ловим интерес",
   54 [code      ]         "мани мани моуш, крутим дела",
   55 [code      ]         "деньги в кармане, удача пришла",
   56 [code      ]         "бриллианты блестят, как звёзды в ночи",
   57 [code      ]         "золотые цепи, от сейфа ключи",
   58 [code      ]         "успех — это труд, а не просто фарт",
   59 [code      ]         "мы строим империю, это наш старт",
   60 [code      ]     ],
   61 [code      ]     "движ": [
   62 [code      ]         "ночь моя, я в центре огней",
   63 [code      ]         "движ до утра, зови всех друзей",
   64 [code      ]         "клуб на пике, бас бьёт в висок",
   65 [code      ]         "звук качает, просыпайся, город-игрок",
   66 [code      ]         "лица в свете, тени в углах",
   67 [code      ]         "энергия прёт, забыли про страх",
   68 [code      ]         "мы здесь и сейчас, это наш момент",
   69 [code      ]         "музыка — жизнь, лучший элемент",
   70 [code      ]     ],
   71 [code      ]     "турция": [
   72 [code      ]         "Стамбул горит миллионами ламп",
   73 [code      ]         "Босфор шумит, проплывая сквозь храм",
   74 [code      ]         "чай крепче кофе, разговор до утра",
   75 [code      ]         "Турция как второй дом, родная земля",
   76 [code      ]         "Анталия ждёт, тёплый бриз у воды",
   77 [code      ]         "древние камни, наши следы",
   78 [code      ]         "восточная сказка в реальности дня",
   79 [code      ]         "здесь каждый закат — для тебя и меня",
   80 [code      ]     ],
   81 [code      ]     "агрессия": [
   82 [code      ]         "без тормозов, летим напролом",
   83 [code      ]         "рубим наотмашь, крушим этот дом",
   84 [code      ]         "молчание — предатель, кричи во весь голос",
   85 [code      ]         "рвём этот бит, как коса спелый колос",
   86 [code      ]         "ярость в глазах, сила в руках",
   87 [code      ]         "мы победим, оставив всех в дураках",
   88 [code      ]         "сталь в характере, лёд в словах",
   89 [code      ]         "путь к вершине — через боль и страх",
   90 [code      ]     ],
   91 [code      ] }
   92 [blank     ] 
   93 [code      ] HOOKS_EN = [
   94 [code      ]     "money over everything, we never look back",
   95 [code      ]     "night, drift, we ride, strictly on track",
   96 [code      ]     "summer, cars, get high, feel the heat",
   97 [code      ]     "no brakes, we win, victory is sweet",
   98 [code      ]     "vibe on repeat, loud in the street",
   99 [code      ]     "shining like a star, never accept defeat",
  100 [code      ]     "put your hands up, touch the sky",
  101 [code      ]     "let it burn tonight, let the sparks fly",
  102 [code      ]     "we don't stop, we own the game",
  103 [code      ]     "living on the edge, remember the name",
  104 [code      ]     "top down, cruising, feeling so free",
  105 [code      ]     "this is the life, how it's meant to be",
  106 [code      ] ]
  107 [blank     ] 
  108 [blank     ] 
  109 [def       ] def _load_lyric_memory() -> list:
  110 [branch    ]     if not LYRIC_MEMORY.exists():
  111 [return    ]         return []
  112 [code      ]     out = []
  113 [loop      ]     for line in LYRIC_MEMORY.read_text(encoding="utf-8").splitlines():
  114 [branch    ]         if line.strip():
  115 [try_block ]             try:
  116 [code      ]                 out.append(json.loads(line))
  117 [try_block ]             except Exception:
  118 [code      ]                 pass
  119 [return    ]     return out
  120 [blank     ] 
  121 [blank     ] 
  122 [def       ] def _save_lyric_memory(entry: dict) -> None:
  123 [code      ]     entry["timestamp"] = time.time()
  124 [stmt      ]     with open(LYRIC_MEMORY, "a", encoding="utf-8") as f:
  125 [code      ]         f.write(json.dumps(entry, ensure_ascii=False) + "\n")
  126 [blank     ] 
  127 [blank     ] 
  128 [def       ] def _pick_punches(theme: str, count: int = 4) -> list[str]:
  129 [docstring ]     """Собираем панчи по темам из строки-запроса."""
  130 [code      ]     theme_lower = (theme or "").lower()
  131 [code      ]     collected = []
  132 [blank     ]     
  133 [comment   ]     # Если это шансон или тюремная/жизненная лирика
  134 [branch    ]     if "шансон" in theme_lower or "централ" in theme_lower or "ветер" in theme_lower or "жиган" in theme_lower:
  135 [code      ]         collected.extend([
  136 [code      ]             "Владимирский централ, ветер северный,",
  137 [code      ]             "Этапный путь до тюрьмы, до каторги.",
  138 [code      ]             "Кольщик, наколо мне купола да кресты,",
  139 [code      ]             "Чтобы память жила до черты.",
  140 [code      ]             "А на воле весна, магаданский туман,",
  141 [code      ]             "Облака плывут в океан.",
  142 [code      ]             "Жиган-монпансье, воля вольная,",
  143 [code      ]             "Душа моя больная, доля горькая."
  144 [code      ]         ])
  145 [blank     ]         
  146 [loop      ]     for key, punches in PUNCHES_RU.items():
  147 [branch    ]         if key in theme_lower:
  148 [code      ]             collected.extend(punches)
  149 [blank     ]             
  150 [branch    ]     if not collected:
  151 [loop      ]         for punches in PUNCHES_RU.values():
  152 [code      ]             collected.extend(punches)
  153 [blank     ]             
  154 [code      ]     random.shuffle(collected)
  155 [return    ]     return collected[:count]
  156 [blank     ] 
  157 [blank     ] 
  158 [def       ] def _try_ollama(prompt: str, model: str = "llama3") -> str | None:
  159 [docstring ]     """Пробуем Ollama через локальный HTTP API."""
  160 [try_block ]     try:
  161 [import    ]         import requests
  162 [blank     ] 
  163 [code      ]         r = requests.post(
  164 [code      ]             "http://127.0.0.1:11434/api/generate",
  165 [code      ]             json={"model": model, "prompt": prompt, "stream": False},
  166 [code      ]             timeout=60,
  167 [code      ]         )
  168 [branch    ]         if r.status_code == 200:
  169 [return    ]             return r.json().get("response", "").strip()
  170 [try_block ]     except Exception:
  171 [code      ]         pass
  172 [return    ]     return None
  173 [blank     ] 
  174 [blank     ] 
  175 [def       ] def _template_verse(
  176 [code      ]     punches: list[str], user_lines: list[str], bpm: int, syllable_target: int
  177 [code      ] ) -> list[str]:
  178 [docstring ]     """Собираем куплет из панчей и пользовательских строк."""
  179 [code      ]     lines = []
  180 [code      ]     used_user = 0
  181 [loop      ]     for i in range(4):
  182 [branch    ]         if used_user < len(user_lines) and i in (0, 2):
  183 [code      ]             lines.append(user_lines[used_user])
  184 [code      ]             used_user += 1
  185 [branch    ]         else:
  186 [code      ]             base = random.choice(punches) if punches else "движ на движ"
  187 [code      ]             lines.append(base)
  188 [comment   ]     # Оставшиеся пользовательские — добавим в конец
  189 [loop      ]     for extra in user_lines[used_user:]:
  190 [code      ]         lines.append(extra)
  191 [return    ]     return lines
  192 [blank     ] 
  193 [blank     ] 
  194 [def       ] def _template_hook_en(user_hooks: list[str]) -> list[str]:
  195 [docstring ]     """English хук: сначала пользовательские EN-строки, потом из HOOKS_EN."""
  196 [code      ]     en_user = [l for l in user_hooks if _is_english(l)]
  197 [code      ]     hook = list(en_user)[:2]
  198 [loop      ]     while len(hook) < 2:
  199 [code      ]         cand = random.choice(HOOKS_EN)
  200 [branch    ]         if cand not in hook:
  201 [code      ]             hook.append(cand)
  202 [return    ]     return hook * 2  # 4 строки припева
  203 [blank     ] 
  204 [blank     ] 
  205 [def       ] def _is_english(s: str) -> bool:
  206 [docstring ]     """Груборечивая эвристика: строка содержит только ASCII/латиницу."""
  207 [branch    ]     if not s:
  208 [return    ]         return False
  209 [code      ]     letters = [c for c in s if c.isalpha()]
  210 [branch    ]     if not letters:
  211 [return    ]         return False
  212 [code      ]     ascii_letters = sum(1 for c in letters if ord(c) < 128)
  213 [return    ]     return ascii_letters / len(letters) > 0.8
  214 [blank     ] 
  215 [blank     ] 
  216 [def       ] def generate_lyrics(
  217 [code      ]     theme: str,
  218 [code      ]     style_vector: dict | None = None,
  219 [code      ]     n_verses: int = 2,
  220 [code      ]     user_lyrics_lines: list[str] | None = None,
  221 [code      ]     bilingual: bool = True,
  222 [code      ] ) -> dict:
  223 [docstring ]     """
  224 [docstring ]     Главный API. Всегда возвращает {'lyrics': str, 'structure': [...], ...}.
  225 [docstring ]     """
  226 [code      ]     user_lyrics_lines = user_lyrics_lines or []
  227 [code      ]     style_vector = style_vector or {}
  228 [code      ]     bpm = int(style_vector.get("target_bpm") or 140)
  229 [blank     ] 
  230 [comment   ]     # Разделяем пользовательские строки на русские и английские
  231 [code      ]     user_ru = [l.strip() for l in user_lyrics_lines if l.strip() and not _is_english(l)]
  232 [code      ]     user_en = [l.strip() for l in user_lyrics_lines if l.strip() and _is_english(l)]
  233 [blank     ] 
  234 [comment   ]     # Слоговая цель — 6-9 при бампирующем BPM
  235 [code      ]     syllable_target = 6 if bpm > 150 else 8
  236 [blank     ] 
  237 [comment   ]     # Попробуем Ollama если запущен
  238 [code      ]     ollama_prompt = (
  239 [code      ]         f"Напиши текст трека в стиле phonk/trap/hyperpop, BPM={bpm}, "
  240 [code      ]         f"тема: {theme}. Куплеты — по-русски, короткие рэп-строчки, "
  241 [code      ]         f"хук — по-английски, {2 if bilingual else 0} английских строк. "
  242 [code      ]         f"Обязательные строки: {', '.join(user_lyrics_lines) if user_lyrics_lines else 'нет'}. "
  243 [code      ]         f"Не пиши комментарии, только текст трека."
  244 [code      ]     )
  245 [code      ]     ollama_out = _try_ollama(ollama_prompt)
  246 [blank     ] 
  247 [branch    ]     if ollama_out and len(ollama_out) > 50:
  248 [code      ]         lyrics_text = ollama_out
  249 [code      ]         source = "ollama"
  250 [branch    ]     else:
  251 [comment   ]         # Fallback: template
  252 [code      ]         punches = _pick_punches(theme, count=8)
  253 [code      ]         blocks = []
  254 [loop      ]         for i in range(n_verses):
  255 [code      ]             blocks.append(f"[Куплет {i+1}]")
  256 [code      ]             blocks.extend(
  257 [code      ]                 _template_verse(
  258 [code      ]                     punches, user_ru if i == 0 else [], bpm, syllable_target
  259 [code      ]                 )
  260 [code      ]             )
  261 [branch    ]             if bilingual:
  262 [code      ]                 blocks.append("[Hook]")
  263 [code      ]                 blocks.extend(_template_hook_en(user_en))
  264 [code      ]         lyrics_text = "\n".join(blocks)
  265 [code      ]         source = "template"
  266 [blank     ] 
  267 [comment   ]     # Гарантируем что все user_lyrics впитаны
  268 [loop      ]     for line in user_lyrics_lines:
  269 [branch    ]         if line.strip() and line.strip() not in lyrics_text:
  270 [code      ]             lyrics_text += f"\n[User]\n{line.strip()}"
  271 [blank     ] 
  272 [code      ]     _save_lyric_memory(
  273 [code      ]         {
  274 [code      ]             "theme": theme,
  275 [code      ]             "bpm": bpm,
  276 [code      ]             "lyrics": lyrics_text,
  277 [code      ]             "source": source,
  278 [code      ]             "user_lines": user_lyrics_lines,
  279 [code      ]         }
  280 [code      ]     )
  281 [blank     ] 
  282 [return    ]     return {
  283 [code      ]         "ok": True,
  284 [code      ]         "lyrics": lyrics_text,
  285 [code      ]         "source": source,
  286 [code      ]         "bilingual": bilingual,
  287 [code      ]         "n_verses": n_verses,
  288 [code      ]         "bpm": bpm,
  289 [code      ]         "user_lines_included": all(
  290 [code      ]             l.strip() in lyrics_text for l in user_lyrics_lines if l.strip()
  291 [code      ]         ),
  292 [code      ]     }
  293 [blank     ] 
  294 [blank     ] 
  295 [def       ] def get_lyric_memory(limit: int = 20) -> list:
  296 [docstring ]     """Вернуть последние строки из Lyric Vault."""
  297 [code      ]     mem = _load_lyric_memory()
  298 [return    ]     return list(reversed(mem))[:limit]
  299 [blank     ] 
  300 [blank     ] 
  301 [branch    ] if __name__ == "__main__":
  302 [code      ]     r = generate_lyrics(
  303 [code      ]         "лето, тачки, деньги",
  304 [code      ]         style_vector={"target_bpm": 140},
  305 [code      ]         user_lyrics_lines=["ночь горит, Supra летит", "money over everything"],
  306 [code      ]         bilingual=True,
  307 [code      ]     )
  308 [code      ]     print(r["lyrics"])
  309 [code      ]     print("---")
  310 [code      ]     print("user_included:", r["user_lines_included"])
```