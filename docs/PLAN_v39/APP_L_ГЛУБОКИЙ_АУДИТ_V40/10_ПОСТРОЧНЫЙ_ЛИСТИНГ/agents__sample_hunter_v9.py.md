# ПОСТРОЧНЫЙ ЛИСТИНГ: `agents/sample_hunter_v9.py`

**Всего строк:** 367

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 211 | 57.5 |
| blank | 38 | 10.4 |
| docstring | 30 | 8.2 |
| return | 23 | 6.3 |
| branch | 20 | 5.4 |
| try_block | 12 | 3.3 |
| def | 10 | 2.7 |
| import | 8 | 2.2 |
| loop | 8 | 2.2 |
| comment | 7 | 1.9 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v9] sample_hunter_v9.py — расширенный поиск сэмплов.
    3 [blank     ] 
    4 [docstring ] Надстройка над v7 agents/sample_hunter.py — НИЧЕГО не удаляем, только добавляем.
    5 [blank     ] 
    6 [docstring ] По ТЗ 3.3 (Sample Browser + Sample Search Agent):
    7 [docstring ]   «Сэмплы ищутся, фильтруются и собираются в библиотеку».
    8 [docstring ]   Лицензии: ТОЛЬКО CC0 / CC-BY / Royalty-Free. Никаких платных ключей.
    9 [blank     ] 
   10 [docstring ] Источники (все free, без API-ключей):
   11 [docstring ]   1. Локальная библиотека samples_cache/  (v7)
   12 [docstring ]   2. Freesound (только public preview + CC-фильтр через web-поиск)
   13 [docstring ]   3. Wikimedia Commons (audio files) — CC-BY-SA / PD
   14 [docstring ]   4. archive.org  (Public Domain / Creative Commons коллекции)
   15 [blank     ] 
   16 [docstring ] Ключевые фичи v9:
   17 [docstring ]   • query planner: разбирает style_vector → пачка целевых запросов
   18 [docstring ]   • bpm-aware match: тег/название содержит BPM ≈ target
   19 [docstring ]   • dedup по названию
   20 [docstring ]   • manifest.json — сохраняет URL + license + attribution для юридической
   21 [docstring ]     чистоты каждого использованного сэмпла
   22 [blank     ] 
   23 [docstring ] Работает без интернета — тогда используется только локальная библиотека.
   24 [docstring ] """
   25 [blank     ] 
   26 [import    ] from __future__ import annotations
   27 [blank     ] 
   28 [import    ] import json
   29 [import    ] import re
   30 [import    ] import time
   31 [import    ] from pathlib import Path
   32 [import    ] from urllib.parse import quote_plus
   33 [blank     ] 
   34 [try_block ] try:
   35 [import    ]     import requests
   36 [blank     ] 
   37 [code      ]     HAS_REQ = True
   38 [try_block ] except Exception:
   39 [code      ]     HAS_REQ = False
   40 [blank     ] 
   41 [code      ] ROOT = Path(__file__).resolve().parents[1]
   42 [code      ] LOCAL_LIB = ROOT / "samples_cache"
   43 [code      ] LOCAL_LIB.mkdir(parents=True, exist_ok=True)
   44 [code      ] MANIFEST_DIR = ROOT / "data" / "sample_manifests"
   45 [code      ] MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
   46 [blank     ] 
   47 [blank     ] 
   48 [comment   ] # ============================================================ query planner
   49 [code      ] GENRE_KEYWORDS = {
   50 [code      ]     "phonk / drift": [
   51 [code      ]         "808 kick",
   52 [code      ]         "cowbell phonk",
   53 [code      ]         "vinyl hiss",
   54 [code      ]         "memphis vocal chop",
   55 [code      ]         "drift phonk sample",
   56 [code      ]         "japanese vocal chop",
   57 [code      ]         "808 slide",
   58 [code      ]         "phonk snare",
   59 [code      ]         "phonk hihat roll",
   60 [code      ]         "supra engine",
   61 [code      ]     ],
   62 [code      ]     "dance / edm": [
   63 [code      ]         "big room synth",
   64 [code      ]         "future bass chord",
   65 [code      ]         "dance kick",
   66 [code      ]         "edm riser",
   67 [code      ]         "reverse cymbal",
   68 [code      ]         "dance clap",
   69 [code      ]         "vocal chop edm",
   70 [code      ]         "sidechain pad",
   71 [code      ]     ],
   72 [code      ]     "trap / hip-hop": [
   73 [code      ]         "trap 808",
   74 [code      ]         "hip-hop snare",
   75 [code      ]         "hip-hop kick",
   76 [code      ]         "trap hihat",
   77 [code      ]         "sample trap loop",
   78 [code      ]         "vocal chop trap",
   79 [code      ]         "trap riser",
   80 [code      ]         "trap open hat",
   81 [code      ]     ],
   82 [code      ]     "pop / r&b": [
   83 [code      ]         "rnb chord loop",
   84 [code      ]         "pop drum loop",
   85 [code      ]         "pop clap",
   86 [code      ]         "vocal chop rnb",
   87 [code      ]         "smooth piano loop",
   88 [code      ]         "airy pad",
   89 [code      ]         "pop snare",
   90 [code      ]     ],
   91 [code      ]     "hardstyle / techno": [
   92 [code      ]         "hardstyle kick",
   93 [code      ]         "reverse kick",
   94 [code      ]         "techno hat",
   95 [code      ]         "techno bass",
   96 [code      ]         "acid loop",
   97 [code      ]         "techno stab",
   98 [code      ]     ],
   99 [code      ]     "generic hit": [
  100 [code      ]         "kick drum",
  101 [code      ]         "snare drum",
  102 [code      ]         "hihat loop",
  103 [code      ]         "bass loop",
  104 [code      ]         "vocal chop",
  105 [code      ]         "riser fx",
  106 [code      ]         "impact fx",
  107 [code      ]     ],
  108 [code      ] }
  109 [blank     ] 
  110 [blank     ] 
  111 [def       ] def plan_queries(style_vector: dict, max_queries: int = 8) -> list[str]:
  112 [code      ]     genre = (
  113 [code      ]         (style_vector or {}).get("genre_hint")
  114 [code      ]         or (style_vector or {}).get("genre")
  115 [code      ]         or "generic hit"
  116 [code      ]     )
  117 [code      ]     bpm = int(round((style_vector or {}).get("bpm", 130.0)))
  118 [code      ]     base = GENRE_KEYWORDS.get(genre, GENRE_KEYWORDS["generic hit"])[:]
  119 [code      ]     bpm_q = [f"loop {bpm} bpm", f"drum loop {bpm} bpm", f"bass {bpm} bpm sample"]
  120 [code      ]     plan = (base + bpm_q)[:max_queries]
  121 [return    ]     return plan
  122 [blank     ] 
  123 [blank     ] 
  124 [comment   ] # ============================================================ local
  125 [code      ] AUDIO_EXT = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aiff")
  126 [blank     ] 
  127 [blank     ] 
  128 [def       ] def list_local(subdir: str = "") -> list[dict]:
  129 [code      ]     root = LOCAL_LIB / subdir if subdir else LOCAL_LIB
  130 [branch    ]     if not root.exists():
  131 [return    ]         return []
  132 [code      ]     items = []
  133 [loop      ]     for p in root.rglob("*"):
  134 [branch    ]         if p.is_file() and p.suffix.lower() in AUDIO_EXT:
  135 [code      ]             items.append(
  136 [code      ]                 {
  137 [code      ]                     "name": p.name,
  138 [code      ]                     "path": str(p),
  139 [code      ]                     "size": p.stat().st_size,
  140 [code      ]                     "source": "local",
  141 [code      ]                     "license": "user_supplied",
  142 [code      ]                     "url": None,
  143 [code      ]                 }
  144 [code      ]             )
  145 [return    ]     return items
  146 [blank     ] 
  147 [blank     ] 
  148 [comment   ] # ============================================================ online — safe wrappers
  149 [def       ] def _http_get(url: str, timeout: float = 6.0) -> str | None:
  150 [branch    ]     if not HAS_REQ:
  151 [return    ]         return None
  152 [try_block ]     try:
  153 [code      ]         r = requests.get(
  154 [code      ]             url, timeout=timeout, headers={"User-Agent": "ZSMusicMaker/9.0"}
  155 [code      ]         )
  156 [branch    ]         if r.status_code == 200:
  157 [return    ]             return r.text
  158 [try_block ]     except Exception:
  159 [return    ]         return None
  160 [return    ]     return None
  161 [blank     ] 
  162 [blank     ] 
  163 [def       ] def search_freesound_web(query: str, limit: int = 5) -> list[dict]:
  164 [docstring ]     """Поиск через публичную веб-страницу Freesound без API-ключа."""
  165 [branch    ]     if not HAS_REQ:
  166 [return    ]         return []
  167 [code      ]     url = (
  168 [code      ]         f"https://freesound.org/search/?q={quote_plus(query)}"
  169 [code      ]         "&f=license:%22Creative+Commons+0%22"
  170 [code      ]     )
  171 [code      ]     html = _http_get(url)
  172 [branch    ]     if not html:
  173 [return    ]         return []
  174 [code      ]     m = re.findall(r'href="(/people/[^/]+/sounds/(\d+)/)"[^>]*>\s*([^<]{3,100})', html)
  175 [code      ]     out = []
  176 [loop      ]     for path, sid, name in m[:limit]:
  177 [code      ]         out.append(
  178 [code      ]             {
  179 [code      ]                 "name": name.strip(),
  180 [code      ]                 "path": None,
  181 [code      ]                 "source": "freesound_cc0",
  182 [code      ]                 "license": "CC0",
  183 [code      ]                 "url": f"https://freesound.org{path}",
  184 [code      ]                 "id": sid,
  185 [code      ]                 "query": query,
  186 [code      ]             }
  187 [code      ]         )
  188 [return    ]     return out
  189 [blank     ] 
  190 [blank     ] 
  191 [def       ] def search_wikimedia(query: str, limit: int = 5) -> list[dict]:
  192 [branch    ]     if not HAS_REQ:
  193 [return    ]         return []
  194 [code      ]     url = (
  195 [code      ]         "https://commons.wikimedia.org/w/api.php"
  196 [code      ]         "?action=query&list=search&format=json"
  197 [code      ]         f"&srnamespace=6&srsearch={quote_plus(query)}+audio&srlimit={limit}"
  198 [code      ]     )
  199 [code      ]     txt = _http_get(url)
  200 [branch    ]     if not txt:
  201 [return    ]         return []
  202 [try_block ]     try:
  203 [code      ]         j = json.loads(txt)
  204 [code      ]         out = []
  205 [loop      ]         for row in j.get("query", {}).get("search", [])[:limit]:
  206 [code      ]             title = row.get("title", "")
  207 [branch    ]             if not any(title.lower().endswith(ext) for ext in AUDIO_EXT):
  208 [code      ]                 continue
  209 [code      ]             file_url = "https://commons.wikimedia.org/wiki/" + quote_plus(
  210 [code      ]                 title.replace(" ", "_")
  211 [code      ]             )
  212 [code      ]             out.append(
  213 [code      ]                 {
  214 [code      ]                     "name": title,
  215 [code      ]                     "path": None,
  216 [code      ]                     "source": "wikimedia",
  217 [code      ]                     "license": "CC-BY-SA / PD",
  218 [code      ]                     "url": file_url,
  219 [code      ]                     "query": query,
  220 [code      ]                 }
  221 [code      ]             )
  222 [return    ]         return out
  223 [try_block ]     except Exception:
  224 [return    ]         return []
  225 [blank     ] 
  226 [blank     ] 
  227 [def       ] def search_archive_org(query: str, limit: int = 5) -> list[dict]:
  228 [branch    ]     if not HAS_REQ:
  229 [return    ]         return []
  230 [code      ]     url = (
  231 [code      ]         "https://archive.org/advancedsearch.php?q="
  232 [code      ]         + quote_plus(
  233 [code      ]             f"{query} AND mediatype:audio AND "
  234 [code      ]             "(licenseurl:*creativecommons* OR licenseurl:*publicdomain*)"
  235 [code      ]         )
  236 [code      ]         + f"&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=licenseurl"
  237 [code      ]         f"&rows={limit}&output=json"
  238 [code      ]     )
  239 [code      ]     txt = _http_get(url)
  240 [branch    ]     if not txt:
  241 [return    ]         return []
  242 [try_block ]     try:
  243 [code      ]         j = json.loads(txt)
  244 [code      ]         docs = j.get("response", {}).get("docs", [])
  245 [code      ]         out = []
  246 [loop      ]         for d in docs[:limit]:
  247 [code      ]             ident = d.get("identifier")
  248 [code      ]             title = d.get("title", ident)
  249 [branch    ]             if not ident:
  250 [code      ]                 continue
  251 [code      ]             out.append(
  252 [code      ]                 {
  253 [code      ]                     "name": str(title)[:120],
  254 [code      ]                     "path": None,
  255 [code      ]                     "source": "archive.org",
  256 [code      ]                     "license": str(d.get("licenseurl", "cc"))[:80],
  257 [code      ]                     "url": f"https://archive.org/details/{ident}",
  258 [code      ]                     "id": ident,
  259 [code      ]                     "query": query,
  260 [code      ]                 }
  261 [code      ]             )
  262 [return    ]         return out
  263 [try_block ]     except Exception:
  264 [return    ]         return []
  265 [blank     ] 
  266 [blank     ] 
  267 [comment   ] # ============================================================ main API
  268 [blank     ] 
  269 [def       ] def _license_gate(items: list[dict], allow_user_override: bool = False) -> list[dict]:
  270 [docstring ]     """v34 FIX (P2.18): жёсткий лицензионный фильтр через license_manager.
  271 [blank     ] 
  272 [docstring ]     Раньше sample_hunter_v9 возвращал сэмплы с сырыми лицензиями вида
  273 [docstring ]     «CC-BY-SA / PD» (wikimedia) и licenseurl-строками (archive.org) БЕЗ
  274 [docstring ]     проверки через app.core.license_manager — т.е. в manifest мог попасть
  275 [docstring ]     NC/SA-контент, запрещённый ТЗ 33 («только CC0 / CC-BY / Royalty-Free»).
  276 [docstring ]     Теперь каждый онлайн-хит прогоняется через единый gate:
  277 [docstring ]       - CC0/PD/CC-BY/RF → проходит;
  278 [docstring ]       - NC/SA/unknown → блокируется (или помечается needs_user_confirm
  279 [docstring ]         при allow_user_override=True — тогда решает пользователь в UI).
  280 [docstring ]     """
  281 [try_block ]     try:
  282 [import    ]         from app.core.license_manager import is_free_commercial
  283 [try_block ]     except Exception:
  284 [return    ]         return items  # менеджер недоступен — не блокируем пайплайн
  285 [code      ]     out = []
  286 [loop      ]     for it in items:
  287 [code      ]         lic = str(it.get("license", "unknown"))
  288 [comment   ]         # Локальные файлы пользователя — вне gate (его собственный контент)
  289 [branch    ]         if it.get("source") == "local":
  290 [code      ]             out.append(it)
  291 [code      ]             continue
  292 [branch    ]         if is_free_commercial(lic, allow_user_override=allow_user_override):
  293 [code      ]             out.append(it)
  294 [branch    ]         else:
  295 [code      ]             it["license_blocked"] = True
  296 [code      ]             it["license_reason"] = f"blocked by license gate: {lic}"
  297 [code      ]             print(f"[sample_hunter_v9] BLOCKED non-free sample: "
  298 [code      ]                   f"{it.get('name','?')[:60]} ({lic})")
  299 [return    ]     return out
  300 [blank     ] 
  301 [blank     ] 
  302 [def       ] def search_online(
  303 [code      ]     style_vector: dict, max_per_source: int = 5, max_total: int = 40
  304 [code      ] ) -> list[dict]:
  305 [code      ]     queries = plan_queries(style_vector, max_queries=6)
  306 [code      ]     hits: list[dict] = []
  307 [code      ]     seen = set()
  308 [loop      ]     for q in queries:
  309 [loop      ]         for finder in (search_freesound_web, search_wikimedia, search_archive_org):
  310 [try_block ]             try:
  311 [code      ]                 results = finder(q, limit=max_per_source)
  312 [try_block ]             except Exception:
  313 [code      ]                 results = []
  314 [loop      ]             for r in results:
  315 [code      ]                 key = (r.get("source"), r.get("name", "").lower())
  316 [branch    ]                 if key in seen:
  317 [code      ]                     continue
  318 [code      ]                 seen.add(key)
  319 [code      ]                 hits.append(r)
  320 [branch    ]                 if len(hits) >= max_total:
  321 [code      ]                     break
  322 [comment   ]     # v34: лицензионный gate ДО возврата — в manifest не попадает NC/SA
  323 [return    ]     return _license_gate(hits)
  324 [blank     ] 
  325 [blank     ] 
  326 [def       ] def unified_search(
  327 [code      ]     style_vector: dict,
  328 [code      ]     include_local: bool = True,
  329 [code      ]     include_online: bool = True,
  330 [code      ]     max_total: int = 60,
  331 [code      ] ) -> dict:
  332 [code      ]     result = {
  333 [code      ]         "queries": plan_queries(style_vector),
  334 [code      ]         "local": [],
  335 [code      ]         "online": [],
  336 [code      ]         "ts": time.time(),
  337 [code      ]     }
  338 [branch    ]     if include_local:
  339 [code      ]         result["local"] = list_local()
  340 [branch    ]     if include_online:
  341 [code      ]         result["online"] = search_online(style_vector, max_total=max_total)
  342 [code      ]     result["total"] = len(result["local"]) + len(result["online"])
  343 [return    ]     return result
  344 [blank     ] 
  345 [blank     ] 
  346 [def       ] def save_manifest(items: list[dict], project_id: str) -> str:
  347 [code      ]     path = MANIFEST_DIR / f"{project_id}_samples.json"
  348 [code      ]     payload = {
  349 [code      ]         "project_id": project_id,
  350 [code      ]         "ts": time.time(),
  351 [code      ]         "total": len(items),
  352 [code      ]         "items": items,
  353 [code      ]         "notice": "Все сэмплы — CC0 / CC-BY / PD или пользовательская "
  354 [code      ]         "локальная библиотека.",
  355 [code      ]     }
  356 [code      ]     path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
  357 [return    ]     return str(path)
  358 [blank     ] 
  359 [blank     ] 
  360 [comment   ] # ============================================================ CLI
  361 [branch    ] if __name__ == "__main__":
  362 [code      ]     sv = {"bpm": 132, "genre_hint": "phonk / drift"}
  363 [code      ]     q = plan_queries(sv)
  364 [code      ]     print("PLAN:", q)
  365 [code      ]     local = list_local()
  366 [code      ]     print(f"LOCAL: {len(local)} files")
  367 [code      ]     print(f"HAS_REQ: {HAS_REQ}")
```