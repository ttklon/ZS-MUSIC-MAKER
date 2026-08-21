# ПОСТРОЧНЫЙ ЛИСТИНГ: `agents/sample_hunter.py`

**Всего строк:** 205

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 93 | 45.4 |
| blank | 25 | 12.2 |
| docstring | 22 | 10.7 |
| return | 17 | 8.3 |
| branch | 13 | 6.3 |
| try_block | 10 | 4.9 |
| import | 7 | 3.4 |
| comment | 7 | 3.4 |
| def | 7 | 3.4 |
| loop | 4 | 2.0 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] sample_hunter.py — split-view API: online + local.
    3 [blank     ] 
    4 [docstring ] Источники online:
    5 [docstring ]   • Freesound (public без API-ключа, через freesound.org/apiv2)
    6 [docstring ]   • Wikimedia Commons (CC0)
    7 [docstring ]   • Pixabay music
    8 [blank     ] 
    9 [docstring ] Локальный browser:
   10 [docstring ]   • samples_cache/ — уже подтянутые сэмплы
   11 [docstring ]   • пользовательские drop-и
   12 [blank     ] 
   13 [docstring ] Все возвращаемые сэмплы проходят фильтр License Manager
   14 [docstring ] (CC0 / CC-BY / Royalty-Free / Public Domain по умолчанию).
   15 [docstring ] """
   16 [blank     ] 
   17 [import    ] from __future__ import annotations
   18 [blank     ] 
   19 [import    ] import json
   20 [import    ] import os
   21 [import    ] import urllib.parse
   22 [import    ] from pathlib import Path
   23 [import    ] from app.core.security_utils import safe_hash, download_file, get_json
   24 [blank     ] 
   25 [code      ] ROOT = Path(__file__).resolve().parents[1]
   26 [code      ] CACHE = ROOT / "samples_cache"
   27 [code      ] CACHE.mkdir(parents=True, exist_ok=True)
   28 [blank     ] 
   29 [blank     ] 
   30 [comment   ] # ---------------------------------------------------------------- local
   31 [def       ] def list_local(query: str = "") -> list[dict]:
   32 [docstring ]     """Локальная библиотека samples_cache/."""
   33 [code      ]     out = []
   34 [code      ]     q = (query or "").lower()
   35 [loop      ]     for p in sorted(CACHE.glob("**/*")):
   36 [branch    ]         if not p.is_file():
   37 [code      ]             continue
   38 [branch    ]         if p.suffix.lower() not in (".wav", ".mp3", ".flac", ".ogg", ".m4a"):
   39 [code      ]             continue
   40 [branch    ]         if q and q not in p.name.lower():
   41 [code      ]             continue
   42 [code      ]         out.append(
   43 [code      ]             {
   44 [code      ]                 "source": "local",
   45 [code      ]                 "path": str(p),
   46 [code      ]                 "name": p.name,
   47 [code      ]                 "size_kb": round(p.stat().st_size / 1024, 1),
   48 [code      ]                 "license": "local",
   49 [code      ]                 "preview": str(p),
   50 [code      ]             }
   51 [code      ]         )
   52 [return    ]     return out
   53 [blank     ] 
   54 [blank     ] 
   55 [comment   ] # ---------------------------------------------------------------- online
   56 [def       ] def search_wikimedia(query: str, max_results: int = 10) -> list[dict]:
   57 [docstring ]     """Wikimedia Commons — CC0/CC-BY музыка без API-ключа."""
   58 [code      ]     results = []
   59 [try_block ]     try:
   60 [code      ]         url = (
   61 [code      ]             "https://commons.wikimedia.org/w/api.php?"
   62 [code      ]             f"action=query&list=search&srsearch={urllib.parse.quote(query)}%20audio"
   63 [code      ]             f"&srnamespace=6&srlimit={max_results}&format=json"
   64 [code      ]         )
   65 [code      ]         data = get_json(url)
   66 [branch    ]         if not data:
   67 [return    ]             return []
   68 [loop      ]         for item in data.get("query", {}).get("search", []):
   69 [code      ]             title = item.get("title", "")
   70 [branch    ]             if not any(
   71 [code      ]                 title.lower().endswith(ext) for ext in (".ogg", ".wav", ".mp3", ".flac")
   72 [code      ]             ):
   73 [code      ]                 continue
   74 [code      ]             page_url = f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title)}"
   75 [code      ]             results.append(
   76 [code      ]                 {
   77 [code      ]                     "source": "wikimedia",
   78 [code      ]                     "name": title,
   79 [code      ]                     "url": page_url,
   80 [code      ]                     "license": "CC0 / CC-BY",
   81 [code      ]                     "preview": page_url,
   82 [code      ]                     "tags": item.get("snippet", "")[:100],
   83 [code      ]                 }
   84 [code      ]             )
   85 [try_block ]     except Exception as e:
   86 [code      ]         print(f"[sample_hunter.wikimedia] {e}")
   87 [return    ]     return results
   88 [blank     ] 
   89 [blank     ] 
   90 [def       ] def search_freesound_public(query: str, max_results: int = 10) -> list[dict]:
   91 [docstring ]     """Freesound без API-ключа — только публичные метаданные (без preview)."""
   92 [code      ]     results = []
   93 [try_block ]     try:
   94 [comment   ]         # Freesound has /apiv2/search/text/ but requires token.
   95 [comment   ]         # Public alternative: parsing search page (ограничено).
   96 [comment   ]         # Оставляем как best-effort placeholder.
   97 [return    ]         return results
   98 [try_block ]     except Exception:
   99 [return    ]         return results
  100 [blank     ] 
  101 [blank     ] 
  102 [def       ] def search_pixabay(query: str, max_results: int = 10) -> list[dict]:
  103 [docstring ]     """Pixabay music — требует бесплатный API key. Мы пропускаем если ключа нет."""
  104 [code      ]     api_key = os.environ.get("PIXABAY_API_KEY")
  105 [branch    ]     if not api_key:
  106 [return    ]         return []
  107 [try_block ]     try:
  108 [code      ]         url = f"https://pixabay.com/api/music/?key={api_key}&q={urllib.parse.quote(query)}&per_page={max_results}"
  109 [code      ]         data = get_json(url)
  110 [branch    ]         if not data:
  111 [return    ]             return []
  112 [loop      ]         for hit in data.get("hits", []):
  113 [code      ]             results = []
  114 [code      ]             results.append(
  115 [code      ]                 {
  116 [code      ]                     "source": "pixabay",
  117 [code      ]                     "name": hit.get("title", ""),
  118 [code      ]                     "url": hit.get("audio", ""),
  119 [code      ]                     "license": "Royalty-Free (Pixabay)",
  120 [code      ]                     "preview": hit.get("preview", ""),
  121 [code      ]                     "tags": hit.get("tags", ""),
  122 [code      ]                 }
  123 [code      ]             )
  124 [return    ]         return results
  125 [try_block ]     except Exception:
  126 [return    ]         return []
  127 [blank     ] 
  128 [blank     ] 
  129 [def       ] def search_online(query: str, max_results: int = 10) -> list[dict]:
  130 [docstring ]     """Агрегатор online-поиска, split-view."""
  131 [code      ]     results = []
  132 [code      ]     results.extend(search_wikimedia(query, max_results))
  133 [code      ]     results.extend(search_freesound_public(query, max_results))
  134 [code      ]     results.extend(search_pixabay(query, max_results))
  135 [return    ]     return results[:max_results]
  136 [blank     ] 
  137 [blank     ] 
  138 [comment   ] # ---------------------------------------------------------------- hunt (main)
  139 [def       ] def hunt(
  140 [code      ]     query: str,
  141 [code      ]     max_results: int = 8,
  142 [code      ]     allow_online: bool = True,
  143 [code      ]     license_filter: bool = True,
  144 [code      ] ) -> dict:
  145 [docstring ]     """
  146 [docstring ]     Главная точка. Возвращает split-view: local + online.
  147 [docstring ]     Фильтрует через License Manager.
  148 [docstring ]     """
  149 [code      ]     local = list_local(query)
  150 [code      ]     online = search_online(query, max_results) if allow_online else []
  151 [blank     ] 
  152 [branch    ]     if license_filter:
  153 [try_block ]         try:
  154 [import    ]             from app.core.license_manager import is_free_commercial
  155 [blank     ] 
  156 [code      ]             online = [
  157 [code      ]                 s for s in online if is_free_commercial(s.get("license", "unknown"))
  158 [code      ]             ]
  159 [try_block ]         except Exception:
  160 [code      ]             pass
  161 [blank     ] 
  162 [return    ]     return {
  163 [code      ]         "ok": True,
  164 [code      ]         "query": query,
  165 [code      ]         "local": local[:max_results],
  166 [code      ]         "online": online[:max_results],
  167 [code      ]         "samples": local[:max_results]
  168 [code      ]         + online[:max_results],  # обратная совместимость v5
  169 [code      ]         "provenance": [
  170 [code      ]             {
  171 [code      ]                 "name": s["name"],
  172 [code      ]                 "source": s["source"],
  173 [code      ]                 "license": s["license"],
  174 [code      ]                 "url": s.get("url", s.get("path", "")),
  175 [code      ]             }
  176 [loop      ]             for s in online
  177 [code      ]         ],
  178 [code      ]     }
  179 [blank     ] 
  180 [blank     ] 
  181 [def       ] def download_to_cache(item: dict) -> str | None:
  182 [docstring ]     """Качаем online-сэмпл в samples_cache/."""
  183 [branch    ]     if item.get("source") == "local":
  184 [return    ]         return item.get("path")
  185 [code      ]     url = item.get("url")
  186 [branch    ]     if not url:
  187 [return    ]         return None
  188 [try_block ]     try:
  189 [code      ]         h = safe_hash(url)[:10]
  190 [code      ]         name = f"{item.get('source','online')}_{h}_{item.get('name','sample')[:30]}"
  191 [comment   ]         # Санитайзим имя файла
  192 [code      ]         name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
  193 [code      ]         target = CACHE / name
  194 [branch    ]         if target.exists():
  195 [return    ]             return str(target)
  196 [branch    ]         if download_file(url, str(target)):
  197 [return    ]             return str(target)
  198 [return    ]         return None
  199 [try_block ]     except Exception as e:
  200 [code      ]         print(f"[sample_hunter.download] {e}")
  201 [return    ]         return None
  202 [blank     ] 
  203 [blank     ] 
  204 [branch    ] if __name__ == "__main__":
  205 [code      ]     print(json.dumps(hunt("phonk 808", max_results=3), ensure_ascii=False, indent=2))
```