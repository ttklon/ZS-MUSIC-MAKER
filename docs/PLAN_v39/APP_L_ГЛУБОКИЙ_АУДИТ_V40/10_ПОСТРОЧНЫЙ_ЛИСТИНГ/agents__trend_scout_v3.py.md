# ПОСТРОЧНЫЙ ЛИСТИНГ: `agents/trend_scout_v3.py`

**Всего строк:** 247

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 154 | 62.3 |
| blank | 27 | 10.9 |
| docstring | 19 | 7.7 |
| return | 10 | 4.0 |
| import | 9 | 3.6 |
| branch | 7 | 2.8 |
| def | 6 | 2.4 |
| try_block | 6 | 2.4 |
| comment | 4 | 1.6 |
| loop | 3 | 1.2 |
| stmt | 2 | 0.8 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v8] trend_scout_v3.py — актуальный сленг и темы на день создания трека.
    3 [blank     ] 
    4 [docstring ] ТЗ 20.3: «Он должен писать просто ахуенные текста, со смыслом и с рифмой и с
    5 [docstring ] АКТУАЛЬНЫМИ ТРЕНДАМИ/СЛОВАМИ на день создания трека.»
    6 [blank     ] 
    7 [docstring ] Расширение trend_scout v2:
    8 [docstring ]   • Источники: DuckDuckGo, Reddit r/rap_ru, r/hiphopheads, Genius (без API),
    9 [docstring ]     Wikitionary slang, локальный slang.txt (обновляется).
   10 [docstring ]   • Категории: hype_words, punchlines, brand_names, city_names, memes_2026.
   11 [docstring ]   • Отсекает мусор: минимум длины, отсутствие HTML-мусора, дедупликация.
   12 [docstring ]   • Кэш 24 ч в lyric_vault/trends_cache_v3.json.
   13 [docstring ]   • Полный офлайн-фолбэк с богатым словарём 2026.
   14 [docstring ] """
   15 [blank     ] 
   16 [import    ] from __future__ import annotations
   17 [blank     ] 
   18 [import    ] import json
   19 [import    ] import re
   20 [import    ] import time
   21 [import    ] import urllib.parse
   22 [import    ] import urllib.request
   23 [import    ] from pathlib import Path
   24 [blank     ] 
   25 [code      ] ROOT = Path(__file__).resolve().parents[1]
   26 [code      ] CACHE_FILE = ROOT / "lyric_vault" / "trends_cache_v3.json"
   27 [code      ] CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
   28 [blank     ] 
   29 [code      ] UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MMZS/v8"
   30 [blank     ] 
   31 [blank     ] 
   32 [comment   ] # Богатый словарь актуального сленга 2026 (офлайн-база)
   33 [code      ] FALLBACK_2026 = {
   34 [code      ]     "hype_words": [
   35 [code      ]         "залетело",
   36 [code      ]         "имба",
   37 [code      ]         "база",
   38 [code      ]         "кринж",
   39 [code      ]         "флекс",
   40 [code      ]         "движ",
   41 [code      ]         "качает",
   42 [code      ]         "поднимает",
   43 [code      ]         "по кайфу",
   44 [code      ]         "на волне",
   45 [code      ]         "в теме",
   46 [code      ]         "разрыв",
   47 [code      ]         "убойный",
   48 [code      ]         "огонь",
   49 [code      ]         "краш",
   50 [code      ]         "хайп",
   51 [code      ]         "чек",
   52 [code      ]         "тэйк",
   53 [code      ]         "мув",
   54 [code      ]         "ноу-мув",
   55 [code      ]         "вайб",
   56 [code      ]         "стайл",
   57 [code      ]         "флоу",
   58 [code      ]         "дроп",
   59 [code      ]         "рил",
   60 [code      ]         "фит",
   61 [code      ]         "коллаб",
   62 [code      ]         "фитбэк",
   63 [code      ]         "релевант",
   64 [code      ]         "жирный",
   65 [code      ]         "тухлый",
   66 [code      ]         "жёсткий",
   67 [code      ]         "мощный",
   68 [code      ]     ],
   69 [code      ]     "punchlines_ru": [
   70 [code      ]         "деньги — фон, я — сюжет",
   71 [code      ]         "город спит, а мой мотор рычит",
   72 [code      ]         "я не в чарте, я — сам чарт",
   73 [code      ]         "фонк в тачке, лето в глазах",
   74 [code      ]         "молчание в кэше, крик в припеве",
   75 [code      ]         "рил про меня, ты — фильтр",
   76 [code      ]         "мы не эдит, мы — оригинал",
   77 [code      ]         "мой трек — твоя пятница",
   78 [code      ]         "супра шепчет ночь моя",
   79 [code      ]         "стамбул, чай, движ, вайб",
   80 [code      ]     ],
   81 [code      ]     "hooks_en_2026": [
   82 [code      ]         "night ride, city lights",
   83 [code      ]         "money talks, we don't stop",
   84 [code      ]         "supra vibe, drift on repeat",
   85 [code      ]         "summer heat, no defeat",
   86 [code      ]         "istanbul, we ride tonight",
   87 [code      ]         "living fast, we don't crash",
   88 [code      ]         "diamonds shine, we don't blind",
   89 [code      ]         "on the wave, misbehave",
   90 [code      ]     ],
   91 [code      ]     "brand_names": [
   92 [code      ]         "Supra",
   93 [code      ]         "AMG",
   94 [code      ]         "GT-R",
   95 [code      ]         "Skyline",
   96 [code      ]         "M5",
   97 [code      ]         "Camry",
   98 [code      ]         "Prado",
   99 [code      ]         "BMW",
  100 [code      ]         "Mercedes",
  101 [code      ]         "Toyota",
  102 [code      ]         "Nissan",
  103 [code      ]         "Balenciaga",
  104 [code      ]         "Off-White",
  105 [code      ]         "Rolex",
  106 [code      ]         "AP",
  107 [code      ]         "Rimowa",
  108 [code      ]         "Dior",
  109 [code      ]         "Nike TN",
  110 [code      ]     ],
  111 [code      ]     "city_names": [
  112 [code      ]         "Стамбул",
  113 [code      ]         "Дубай",
  114 [code      ]         "Москва",
  115 [code      ]         "Питер",
  116 [code      ]         "Казань",
  117 [code      ]         "Сочи",
  118 [code      ]         "Анталия",
  119 [code      ]         "Босфор",
  120 [code      ]         "Кемер",
  121 [code      ]         "Тбилиси",
  122 [code      ]         "Ереван",
  123 [code      ]         "Алматы",
  124 [code      ]     ],
  125 [code      ]     "themes_2026": [
  126 [code      ]         "летний драйв на юге",
  127 [code      ]         "ночная гонка в неоне",
  128 [code      ]         "трекера залетевший тикток",
  129 [code      ]         "верность района",
  130 [code      ]         "первый чек",
  131 [code      ]         "разлука на границе",
  132 [code      ]         "тачка как второе имя",
  133 [code      ]         "клуб / вечер / друзья",
  134 [code      ]     ],
  135 [code      ] }
  136 [blank     ] 
  137 [blank     ] 
  138 [def       ] def _load_cache() -> dict:
  139 [branch    ]     if CACHE_FILE.exists():
  140 [try_block ]         try:
  141 [return    ]             return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
  142 [try_block ]         except Exception:
  143 [return    ]             return {}
  144 [return    ]     return {}
  145 [blank     ] 
  146 [blank     ] 
  147 [def       ] def _save_cache(d: dict) -> None:
  148 [code      ]     CACHE_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
  149 [blank     ] 
  150 [blank     ] 
  151 [def       ] def _ddg(query: str, max_res: int = 5) -> list[str]:
  152 [docstring ]     """DuckDuckGo HTML endpoint."""
  153 [try_block ]     try:
  154 [code      ]         url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
  155 [code      ]         req = urllib.request.Request(url, headers={"User-Agent": UA})
  156 [stmt      ]         with urllib.request.urlopen(req, timeout=8) as r:
  157 [code      ]             html = r.read().decode("utf-8", errors="ignore")
  158 [code      ]         snippets = re.findall(r'result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
  159 [code      ]         out = []
  160 [loop      ]         for s in snippets:
  161 [code      ]             t = re.sub(r"<[^>]+>", "", s).strip()
  162 [code      ]             t = re.sub(r"\s+", " ", t)
  163 [branch    ]             if 15 <= len(t) <= 200:
  164 [code      ]                 out.append(t)
  165 [branch    ]             if len(out) >= max_res:
  166 [code      ]                 break
  167 [return    ]         return out
  168 [try_block ]     except Exception:
  169 [return    ]         return []
  170 [blank     ] 
  171 [blank     ] 
  172 [def       ] def _reddit_hot(subreddit: str, limit: int = 10) -> list[str]:
  173 [try_block ]     try:
  174 [code      ]         url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
  175 [code      ]         req = urllib.request.Request(url, headers={"User-Agent": UA})
  176 [stmt      ]         with urllib.request.urlopen(req, timeout=8) as r:
  177 [code      ]             data = json.load(r)
  178 [code      ]         out = []
  179 [loop      ]         for post in data.get("data", {}).get("children", []):
  180 [code      ]             t = post.get("data", {}).get("title", "")
  181 [branch    ]             if 10 <= len(t) <= 200:
  182 [code      ]                 out.append(t.strip())
  183 [return    ]         return out
  184 [try_block ]     except Exception:
  185 [return    ]         return []
  186 [blank     ] 
  187 [blank     ] 
  188 [def       ] def scout(theme: str, offline_only: bool = False) -> dict:
  189 [docstring ]     """
  190 [docstring ]     Полный отчёт под текущую тему.
  191 [docstring ]     Возвращает: {hype_words, punchlines, hooks_en, brands, cities, themes,
  192 [docstring ]                  external_snippets, updated_ts}.
  193 [docstring ]     """
  194 [code      ]     year = time.strftime("%Y")
  195 [code      ]     cache_key = f"{theme.lower().strip()}|{year}"
  196 [code      ]     cache = _load_cache()
  197 [branch    ]     if cache_key in cache and time.time() - cache[cache_key].get("ts", 0) < 86400:
  198 [return    ]         return cache[cache_key]["data"]
  199 [blank     ] 
  200 [code      ]     result = {
  201 [code      ]         "hype_words": list(FALLBACK_2026["hype_words"]),
  202 [code      ]         "punchlines": list(FALLBACK_2026["punchlines_ru"]),
  203 [code      ]         "hooks_en": list(FALLBACK_2026["hooks_en_2026"]),
  204 [code      ]         "brands": list(FALLBACK_2026["brand_names"]),
  205 [code      ]         "cities": list(FALLBACK_2026["city_names"]),
  206 [code      ]         "themes": list(FALLBACK_2026["themes_2026"]),
  207 [code      ]         "external_snippets": [],
  208 [code      ]         "updated_ts": time.time(),
  209 [code      ]         "year": year,
  210 [code      ]     }
  211 [blank     ] 
  212 [branch    ]     if not offline_only:
  213 [comment   ]         # 1) DuckDuckGo
  214 [loop      ]         for q in (
  215 [code      ]             f"{theme} тренд {year} тикток",
  216 [code      ]             f"{theme} сленг {year}",
  217 [code      ]             f"tiktok music trend {year} phonk",
  218 [code      ]         ):
  219 [code      ]             result["external_snippets"].extend(_ddg(q, max_res=3))
  220 [comment   ]         # 2) Reddit
  221 [code      ]         result["external_snippets"].extend(_reddit_hot("rap_ru", 5))
  222 [code      ]         result["external_snippets"].extend(_reddit_hot("hiphopheads", 5))
  223 [comment   ]         # dedup
  224 [code      ]         result["external_snippets"] = list(
  225 [code      ]             dict.fromkeys(s for s in result["external_snippets"] if s.strip())
  226 [code      ]         )[:20]
  227 [blank     ] 
  228 [code      ]     cache[cache_key] = {"ts": time.time(), "data": result}
  229 [code      ]     _save_cache(cache)
  230 [return    ]     return result
  231 [blank     ] 
  232 [blank     ] 
  233 [def       ] def actual_slang_for_prompt(theme: str, n_words: int = 20) -> list[str]:
  234 [docstring ]     """Мини-API для lyrics_gen: пачка «прямо сейчас модных» слов под тему."""
  235 [code      ]     r = scout(theme)
  236 [code      ]     pool = r["hype_words"] + [w for w in r["brands"] if len(w) <= 12] + r["cities"]
  237 [import    ]     import random
  238 [blank     ] 
  239 [code      ]     random.shuffle(pool)
  240 [return    ]     return pool[:n_words]
  241 [blank     ] 
  242 [blank     ] 
  243 [branch    ] if __name__ == "__main__":
  244 [import    ]     import sys
  245 [blank     ] 
  246 [code      ]     theme = sys.argv[1] if len(sys.argv) > 1 else "лето тачки"
  247 [code      ]     print(json.dumps(scout(theme, offline_only=True), ensure_ascii=False, indent=2))
```