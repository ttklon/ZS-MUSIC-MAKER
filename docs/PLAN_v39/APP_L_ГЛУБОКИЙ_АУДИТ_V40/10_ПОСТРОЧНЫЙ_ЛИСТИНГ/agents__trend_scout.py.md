# ПОСТРОЧНЫЙ ЛИСТИНГ: `agents/trend_scout.py`

**Всего строк:** 156

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 67 | 42.9 |
| blank | 29 | 18.6 |
| docstring | 13 | 8.3 |
| comment | 9 | 5.8 |
| return | 9 | 5.8 |
| branch | 8 | 5.1 |
| try_block | 8 | 5.1 |
| import | 6 | 3.8 |
| def | 6 | 3.8 |
| loop | 1 | 0.6 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] Agent: TrendScout v2 (НОВЫЙ)
    3 [docstring ] Ищет в интернете тренды, сленг, мемы, популярные выражения.
    4 [docstring ] Источники: DuckDuckGo, Google Trends (опционально), Reddit.
    5 [docstring ] Работает опционально — если интернета нет, возвращает локальный кэш.
    6 [docstring ] """
    7 [blank     ] 
    8 [import    ] import json
    9 [import    ] import os
   10 [import    ] import re
   11 [import    ] import time
   12 [blank     ] 
   13 [import    ] import requests
   14 [blank     ] 
   15 [code      ] CACHE_FILE = os.path.join(
   16 [code      ]     os.path.dirname(__file__), "..", "lyric_vault", "trends_cache.json"
   17 [code      ] )
   18 [code      ] os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
   19 [blank     ] 
   20 [blank     ] 
   21 [def       ] def scout_trends(query: str, max_results: int = 10) -> list:
   22 [docstring ]     """
   23 [docstring ]     Ищет актуальные тренды и сленг по теме.
   24 [docstring ]     Возвращает список выражений/фраз.
   25 [docstring ]     """
   26 [code      ]     cache = _load_cache()
   27 [code      ]     cache_key = query.lower().strip()
   28 [blank     ] 
   29 [comment   ]     # Проверяем кэш (не старше 24 часов)
   30 [branch    ]     if cache_key in cache:
   31 [code      ]         entry = cache[cache_key]
   32 [branch    ]         if time.time() - entry.get("ts", 0) < 86400:
   33 [return    ]             return entry.get("trends", [])
   34 [blank     ] 
   35 [code      ]     trends = []
   36 [blank     ] 
   37 [comment   ]     # 1. DuckDuckGo (простой HTML-парсинг)
   38 [try_block ]     try:
   39 [code      ]         trends.extend(_duckduckgo_search(f"{query} тренд сленг 2026"))
   40 [try_block ]     except Exception:
   41 [code      ]         pass
   42 [blank     ] 
   43 [comment   ]     # 2. Дополняем локальным словарём
   44 [try_block ]     try:
   45 [import    ]         from modules.lyrics_gen import load_slang_dictionary
   46 [blank     ] 
   47 [code      ]         trends.extend(load_slang_dictionary()[:10])
   48 [try_block ]     except Exception:
   49 [code      ]         pass
   50 [blank     ] 
   51 [comment   ]     # 3. Стандартные хайповые фразы (fallback)
   52 [branch    ]     if not trends:
   53 [code      ]         trends = _fallback_trends(query)
   54 [blank     ] 
   55 [comment   ]     # Дедупликация
   56 [code      ]     trends = list(dict.fromkeys(trends))[:max_results]
   57 [blank     ] 
   58 [comment   ]     # Кэшируем
   59 [code      ]     cache[cache_key] = {"trends": trends, "ts": time.time()}
   60 [code      ]     _save_cache(cache)
   61 [blank     ] 
   62 [return    ]     return trends
   63 [blank     ] 
   64 [blank     ] 
   65 [def       ] def _duckduckgo_search(query: str) -> list:
   66 [docstring ]     """Простой парсинг DuckDuckGo HTML."""
   67 [code      ]     url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
   68 [code      ]     headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
   69 [code      ]     r = requests.get(url, headers=headers, timeout=10)
   70 [comment   ]     # Извлекаем текст из результатов
   71 [code      ]     snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
   72 [comment   ]     # Очищаем от HTML
   73 [code      ]     clean = []
   74 [loop      ]     for s in snippets:
   75 [code      ]         text = re.sub(r"<[^>]+>", "", s).strip()
   76 [branch    ]         if text and len(text) > 10:
   77 [code      ]             clean.append(text)
   78 [return    ]     return clean[:5]
   79 [blank     ] 
   80 [blank     ] 
   81 [def       ] def _fallback_trends(query: str) -> list:
   82 [docstring ]     """Локальный fallback если интернет недоступен."""
   83 [return    ]     return [
   84 [code      ]         "движ",
   85 [code      ]         "качает",
   86 [code      ]         "поднимает",
   87 [code      ]         "тачка",
   88 [code      ]         "бабки",
   89 [code      ]         "лям",
   90 [code      ]         "движуха",
   91 [code      ]         "залетело",
   92 [code      ]         "чек",
   93 [code      ]         "стайл",
   94 [code      ]         "флоу",
   95 [code      ]         "вайб",
   96 [code      ]         "огонь",
   97 [code      ]         "краш",
   98 [code      ]         "флекс",
   99 [code      ]         "хайп",
  100 [code      ]         "имба",
  101 [code      ]         "база",
  102 [code      ]         "на волне",
  103 [code      ]         "в теме",
  104 [code      ]         "по кайфу",
  105 [code      ]         "разрыв",
  106 [code      ]         "убойный",
  107 [code      ]     ]
  108 [blank     ] 
  109 [blank     ] 
  110 [def       ] def _load_cache() -> dict:
  111 [branch    ]     if os.path.exists(CACHE_FILE):
  112 [try_block ]         try:
  113 [return    ]             return json.load(open(CACHE_FILE, encoding="utf-8"))
  114 [try_block ]         except Exception:
  115 [return    ]             return {}
  116 [return    ]     return {}
  117 [blank     ] 
  118 [blank     ] 
  119 [def       ] def _save_cache(data: dict):
  120 [code      ]     json.dump(
  121 [code      ]         data, open(CACHE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2
  122 [code      ]     )
  123 [blank     ] 
  124 [blank     ] 
  125 [def       ] def get_hot_topics() -> list:
  126 [docstring ]     """Возвращает актуальные горячие темы для треков."""
  127 [code      ]     cache = _load_cache()
  128 [branch    ]     if "hot_topics" in cache and time.time() - cache["hot_topics"].get("ts", 0) < 86400:
  129 [return    ]         return cache["hot_topics"].get("topics", [])
  130 [blank     ] 
  131 [code      ]     topics = [
  132 [code      ]         "лето, море, тачки, движение",
  133 [code      ]         "ночной город, неон, флекс",
  134 [code      ]         "деньги, успех, подъём",
  135 [code      ]         "Турция, Стамбул, отдых",
  136 [code      ]         "район, пацаны, верность",
  137 [code      ]         "любовь, краш, чувства",
  138 [code      ]         "трэп, тёмный вайб, 808",
  139 [code      ]         "TikTok тренд, залетевший хук",
  140 [code      ]     ]
  141 [blank     ] 
  142 [comment   ]     # Пробуем найти актуальные тренды в интернете
  143 [try_block ]     try:
  144 [code      ]         online = _duckduckgo_search("тrend music tiktok 2026")
  145 [branch    ]         if online:
  146 [code      ]             topics = online[:4] + topics
  147 [try_block ]     except Exception:
  148 [code      ]         pass
  149 [blank     ] 
  150 [code      ]     cache["hot_topics"] = {"topics": topics, "ts": time.time()}
  151 [code      ]     _save_cache(cache)
  152 [return    ]     return topics
  153 [blank     ] 
  154 [blank     ] 
  155 [branch    ] if __name__ == "__main__":
  156 [code      ]     print(json.dumps(scout_trends("phonk drift"), ensure_ascii=False, indent=2))
```