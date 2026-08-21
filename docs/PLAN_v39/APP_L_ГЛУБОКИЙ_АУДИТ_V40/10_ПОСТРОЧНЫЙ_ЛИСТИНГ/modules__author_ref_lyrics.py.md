# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/author_ref_lyrics.py`

**Всего строк:** 369

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 178 | 48.2 |
| blank | 49 | 13.3 |
| docstring | 40 | 10.8 |
| return | 24 | 6.5 |
| branch | 23 | 6.2 |
| def | 14 | 3.8 |
| import | 11 | 3.0 |
| loop | 11 | 3.0 |
| comment | 10 | 2.7 |
| try_block | 8 | 2.2 |
| stmt | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v8] author_ref_lyrics.py — Author-Referenced Lyrics Engine.
    3 [blank     ] 
    4 [docstring ] Реализация ТЗ 20.3, пункт «Темы: тренды + пользователь»:
    5 [blank     ] 
    6 [docstring ]   «Возможность, чтобы все треки, которые я загрузил (в библиотеку) использовались
    7 [docstring ]    для написания новых текстов. Берётся 500 треков или все → на основе них + ИИ
    8 [docstring ]    + словарь + поисковик трендов составляются реально крутые тексты.
    9 [docstring ]    Я могу задать тему, слова, ВЫБРАТЬ АВТОРА ИЗ РЕФЕРЕНСОВ, чтобы именно в его
   10 [docstring ]    стиле всё писалось, или написать автора в поиске — программа сама найдёт
   11 [docstring ]    все треки автора для референса.»
   12 [blank     ] 
   13 [docstring ] Модуль:
   14 [docstring ]   • Индексирует всю библиотеку lyric_vault + references/*.mp3 (через whisper).
   15 [docstring ]   • Строит стилевой профиль автора: n-граммы, любимые слова, ритм слогов, темы.
   16 [docstring ]   • При запросе автора в интернете — ищет тексты через DuckDuckGo/Genius/Lyrics.fandom.
   17 [docstring ]   • Отдаёт «стилевой промт» для lyrics_gen (Ollama/fallback).
   18 [docstring ]   • Полностью офлайн-совместим: если интернета нет — работает по локальному корпусу.
   19 [docstring ] """
   20 [blank     ] 
   21 [import    ] from __future__ import annotations
   22 [blank     ] 
   23 [import    ] import hashlib
   24 [import    ] import json
   25 [import    ] import re
   26 [import    ] import time
   27 [import    ] from collections import Counter
   28 [import    ] from pathlib import Path
   29 [blank     ] 
   30 [code      ] ROOT = Path(__file__).resolve().parents[1]
   31 [code      ] CORPUS_DIR = ROOT / "lyric_vault" / "author_corpus"
   32 [code      ] STYLE_DIR = ROOT / "lyric_vault" / "author_styles"
   33 [code      ] CACHE_FILE = ROOT / "lyric_vault" / "author_index.json"
   34 [loop      ] for p in (CORPUS_DIR, STYLE_DIR):
   35 [code      ]     p.mkdir(parents=True, exist_ok=True)
   36 [blank     ] 
   37 [comment   ] # ------------------------------------------------------------- utils
   38 [code      ] _WORD_RE = re.compile(r"[а-яА-Яёa-zA-Z0-9']+")
   39 [code      ] _STOPWORDS = {
   40 [code      ]     "и",
   41 [code      ]     "а",
   42 [code      ]     "но",
   43 [code      ]     "или",
   44 [code      ]     "что",
   45 [code      ]     "как",
   46 [code      ]     "это",
   47 [code      ]     "то",
   48 [code      ]     "же",
   49 [code      ]     "бы",
   50 [code      ]     "не",
   51 [code      ]     "в",
   52 [code      ]     "на",
   53 [code      ]     "с",
   54 [code      ]     "по",
   55 [code      ]     "за",
   56 [code      ]     "из",
   57 [code      ]     "от",
   58 [code      ]     "до",
   59 [code      ]     "у",
   60 [code      ]     "к",
   61 [code      ]     "о",
   62 [code      ]     "об",
   63 [code      ]     "the",
   64 [code      ]     "a",
   65 [code      ]     "an",
   66 [code      ]     "of",
   67 [code      ]     "to",
   68 [code      ]     "and",
   69 [code      ]     "in",
   70 [code      ]     "is",
   71 [code      ]     "it",
   72 [code      ]     "on",
   73 [code      ]     "for",
   74 [code      ]     "my",
   75 [code      ]     "your",
   76 [code      ]     "we",
   77 [code      ]     "you",
   78 [code      ]     "i",
   79 [code      ] }
   80 [blank     ] 
   81 [blank     ] 
   82 [def       ] def _tokenize(text: str) -> list[str]:
   83 [return    ]     return [w.lower() for w in _WORD_RE.findall(text or "")]
   84 [blank     ] 
   85 [blank     ] 
   86 [def       ] def _syllables_ru(word: str) -> int:
   87 [return    ]     return max(1, sum(1 for ch in word.lower() if ch in "аеёиоуыэюяaeiouy"))
   88 [blank     ] 
   89 [blank     ] 
   90 [def       ] def _load_index() -> dict:
   91 [branch    ]     if CACHE_FILE.exists():
   92 [try_block ]         try:
   93 [return    ]             return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
   94 [try_block ]         except Exception:
   95 [return    ]             return {}
   96 [return    ]     return {}
   97 [blank     ] 
   98 [blank     ] 
   99 [def       ] def _save_index(idx: dict) -> None:
  100 [code      ]     CACHE_FILE.write_text(
  101 [code      ]         json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8"
  102 [code      ]     )
  103 [blank     ] 
  104 [blank     ] 
  105 [comment   ] # ------------------------------------------------------------- ingest
  106 [def       ] def ingest_lyrics_file(path: str | Path, author: str, title: str = "") -> dict:
  107 [docstring ]     """Кладём один текст в корпус автора. Возвращаем сводку."""
  108 [code      ]     path = Path(path)
  109 [branch    ]     if not path.exists():
  110 [return    ]         return {"ok": False, "error": f"file not found: {path}"}
  111 [code      ]     text = path.read_text(encoding="utf-8", errors="ignore")
  112 [return    ]     return ingest_lyrics_text(text, author=author, title=title or path.stem)
  113 [blank     ] 
  114 [blank     ] 
  115 [def       ] def ingest_lyrics_text(text: str, author: str, title: str = "") -> dict:
  116 [docstring ]     """Индексируем сырой текст."""
  117 [code      ]     author_slug = re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "_", (author or "unknown")).lower()
  118 [code      ]     fname = hashlib.md5(
  119 [code      ]         (author_slug + "|" + title + "|" + text[:60]).encode()
  120 [code      ]     ).hexdigest()[:12]
  121 [code      ]     dst = CORPUS_DIR / author_slug
  122 [code      ]     dst.mkdir(parents=True, exist_ok=True)
  123 [code      ]     (dst / f"{fname}.txt").write_text(text, encoding="utf-8")
  124 [blank     ] 
  125 [code      ]     idx = _load_index()
  126 [code      ]     idx.setdefault(author_slug, {"display_name": author, "files": []})
  127 [code      ]     idx[author_slug]["files"].append(
  128 [code      ]         {
  129 [code      ]             "id": fname,
  130 [code      ]             "title": title,
  131 [code      ]             "chars": len(text),
  132 [code      ]             "ts": time.time(),
  133 [code      ]         }
  134 [code      ]     )
  135 [code      ]     _save_index(idx)
  136 [return    ]     return {"ok": True, "author": author_slug, "id": fname}
  137 [blank     ] 
  138 [blank     ] 
  139 [def       ] def ingest_reference_audio(
  140 [code      ]     audio_path: str | Path, author: str = "unknown", title: str = ""
  141 [code      ] ) -> dict:
  142 [docstring ]     """Через Whisper вытаскиваем текст из аудио-референса и кладём в корпус."""
  143 [code      ]     audio_path = Path(audio_path)
  144 [branch    ]     if not audio_path.exists():
  145 [return    ]         return {"ok": False, "error": "no audio"}
  146 [try_block ]     try:
  147 [import    ]         import whisper
  148 [blank     ] 
  149 [code      ]         model = whisper.load_model("base")
  150 [code      ]         res = model.transcribe(str(audio_path), fp16=False)
  151 [code      ]         text = (res.get("text") or "").strip()
  152 [branch    ]         if not text:
  153 [return    ]             return {"ok": False, "error": "empty transcription"}
  154 [return    ]         return ingest_lyrics_text(text, author=author, title=title or audio_path.stem)
  155 [try_block ]     except Exception as e:
  156 [return    ]         return {"ok": False, "error": f"whisper failed: {e}"}
  157 [blank     ] 
  158 [blank     ] 
  159 [comment   ] # ------------------------------------------------------------- style profile
  160 [def       ] def build_style_profile(author: str) -> dict:
  161 [docstring ]     """
  162 [docstring ]     Строим стилевой профиль автора: словарь, ритм слогов, любимые темы, характерные
  163 [docstring ]     n-граммы. Сохраняем в STYLE_DIR/<author>.json.
  164 [docstring ]     """
  165 [code      ]     author_slug = re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "_", author).lower()
  166 [code      ]     author_dir = CORPUS_DIR / author_slug
  167 [branch    ]     if not author_dir.exists():
  168 [return    ]         return {"ok": False, "error": f"нет корпуса для {author}"}
  169 [blank     ] 
  170 [code      ]     all_text = ""
  171 [loop      ]     for f in author_dir.glob("*.txt"):
  172 [code      ]         all_text += "\n" + f.read_text(encoding="utf-8", errors="ignore")
  173 [blank     ] 
  174 [code      ]     tokens = _tokenize(all_text)
  175 [branch    ]     if len(tokens) < 5:
  176 [return    ]         return {"ok": False, "error": "слишком мало данных"}
  177 [blank     ] 
  178 [code      ]     counter = Counter(w for w in tokens if w not in _STOPWORDS and len(w) > 2)
  179 [code      ]     top_words = counter.most_common(80)
  180 [blank     ] 
  181 [comment   ]     # Биграммы (характерные обороты)
  182 [code      ]     bigrams = Counter()
  183 [loop      ]     for i in range(len(tokens) - 1):
  184 [code      ]         a, b = tokens[i], tokens[i + 1]
  185 [branch    ]         if a not in _STOPWORDS and b not in _STOPWORDS:
  186 [code      ]             bigrams[f"{a} {b}"] += 1
  187 [code      ]     top_bigrams = [bg for bg, c in bigrams.most_common(30) if c >= 2]
  188 [blank     ] 
  189 [comment   ]     # Средняя длина строки в слогах
  190 [code      ]     lines = [l for l in all_text.split("\n") if l.strip()]
  191 [code      ]     syll_per_line = []
  192 [loop      ]     for line in lines[:400]:
  193 [code      ]         ws = _tokenize(line)
  194 [branch    ]         if ws:
  195 [code      ]             syll_per_line.append(sum(_syllables_ru(w) for w in ws))
  196 [code      ]     avg_syll = round(sum(syll_per_line) / max(1, len(syll_per_line)), 1)
  197 [blank     ] 
  198 [comment   ]     # Rhyme skeleton: последние слоги последних слов строк
  199 [code      ]     rhymes = []
  200 [loop      ]     for line in lines[:200]:
  201 [code      ]         ws = _tokenize(line)
  202 [branch    ]         if ws:
  203 [code      ]             rhymes.append(ws[-1][-3:])
  204 [code      ]     rhyme_counter = Counter(rhymes)
  205 [blank     ] 
  206 [code      ]     profile = {
  207 [code      ]         "author": author,
  208 [code      ]         "author_slug": author_slug,
  209 [code      ]         "top_words": [{"w": w, "n": n} for w, n in top_words],
  210 [code      ]         "top_bigrams": top_bigrams,
  211 [code      ]         "avg_syll_per_line": avg_syll,
  212 [code      ]         "rhyme_endings": [r for r, _ in rhyme_counter.most_common(20)],
  213 [code      ]         "sample_lines": [l.strip() for l in lines if 6 <= len(_tokenize(l)) <= 14][:12],
  214 [code      ]         "corpus_size_chars": len(all_text),
  215 [code      ]         "built_at": time.time(),
  216 [code      ]     }
  217 [code      ]     (STYLE_DIR / f"{author_slug}.json").write_text(
  218 [code      ]         json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
  219 [code      ]     )
  220 [return    ]     return {"ok": True, "profile": profile}
  221 [blank     ] 
  222 [blank     ] 
  223 [def       ] def get_style_profile(author: str) -> dict | None:
  224 [code      ]     author_slug = re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "_", author).lower()
  225 [code      ]     f = STYLE_DIR / f"{author_slug}.json"
  226 [branch    ]     if f.exists():
  227 [try_block ]         try:
  228 [return    ]             return json.loads(f.read_text(encoding="utf-8"))
  229 [try_block ]         except Exception:
  230 [return    ]             return None
  231 [comment   ]     # Автосборка при первом обращении
  232 [code      ]     r = build_style_profile(author)
  233 [return    ]     return r.get("profile") if r.get("ok") else None
  234 [blank     ] 
  235 [blank     ] 
  236 [comment   ] # ------------------------------------------------------------- online search
  237 [def       ] def search_author_online(author: str, max_tracks: int = 20) -> list[dict]:
  238 [docstring ]     """
  239 [docstring ]     Пытаемся найти в интернете тексты треков автора.
  240 [docstring ]     Использует DuckDuckGo html endpoint (без API-ключа).
  241 [docstring ]     Возвращает список {title, url, snippet}.
  242 [docstring ]     """
  243 [import    ]     import urllib.parse
  244 [import    ]     import urllib.request
  245 [blank     ] 
  246 [code      ]     q = urllib.parse.quote(f"{author} lyrics текст песни")
  247 [code      ]     url = f"https://html.duckduckgo.com/html/?q={q}"
  248 [try_block ]     try:
  249 [code      ]         req = urllib.request.Request(
  250 [code      ]             url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
  251 [code      ]         )
  252 [stmt      ]         with urllib.request.urlopen(req, timeout=8) as r:
  253 [code      ]             html = r.read().decode("utf-8", errors="ignore")
  254 [try_block ]     except Exception as e:
  255 [return    ]         return [{"error": str(e)}]
  256 [blank     ] 
  257 [code      ]     results = []
  258 [loop      ]     for m in re.finditer(
  259 [code      ]         r'result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
  260 [code      ]         r'result__snippet"[^>]*>(.*?)</a>',
  261 [code      ]         html,
  262 [code      ]         re.DOTALL,
  263 [code      ]     ):
  264 [code      ]         u, t, s = m.groups()
  265 [code      ]         title = re.sub(r"<[^>]+>", "", t).strip()
  266 [code      ]         snip = re.sub(r"<[^>]+>", "", s).strip()
  267 [branch    ]         if title and snip:
  268 [code      ]             results.append({"title": title, "url": u, "snippet": snip})
  269 [branch    ]         if len(results) >= max_tracks:
  270 [code      ]             break
  271 [return    ]     return results
  272 [blank     ] 
  273 [blank     ] 
  274 [def       ] def fetch_and_ingest_author(author: str, max_tracks: int = 5) -> dict:
  275 [docstring ]     """
  276 [docstring ]     Ищет автора онлайн, тянет пары {title, snippet}, сохраняет как лирические
  277 [docstring ]     заготовки. Полноценные тексты нельзя тянуть без API — используем snippets
  278 [docstring ]     как стилевой намёк.
  279 [docstring ]     """
  280 [code      ]     hits = search_author_online(author, max_tracks=max_tracks * 3)
  281 [code      ]     kept = 0
  282 [loop      ]     for h in hits:
  283 [branch    ]         if "error" in h:
  284 [code      ]             continue
  285 [code      ]         text = h.get("snippet") or ""
  286 [branch    ]         if len(text) < 40:
  287 [code      ]             continue
  288 [code      ]         ingest_lyrics_text(text, author=author, title=h.get("title", ""))
  289 [code      ]         kept += 1
  290 [branch    ]         if kept >= max_tracks:
  291 [code      ]             break
  292 [branch    ]     if kept:
  293 [code      ]         build_style_profile(author)
  294 [return    ]     return {"ok": kept > 0, "ingested": kept, "author": author}
  295 [blank     ] 
  296 [blank     ] 
  297 [comment   ] # ------------------------------------------------------------- prompt builder
  298 [def       ] def build_style_prompt(
  299 [code      ]     author: str, theme: str, user_words: list[str], bpm: int, target_lines: int = 16
  300 [code      ] ) -> str:
  301 [docstring ]     """
  302 [docstring ]     Строим промт для Ollama/лирического движка с учётом стилевого профиля автора.
  303 [docstring ]     """
  304 [code      ]     profile = get_style_profile(author) or {}
  305 [code      ]     words = ", ".join(w["w"] for w in profile.get("top_words", [])[:20])
  306 [code      ]     bigs = ", ".join(profile.get("top_bigrams", [])[:10])
  307 [code      ]     samples = "\n".join(f"  • {s}" for s in profile.get("sample_lines", [])[:6])
  308 [code      ]     avg = profile.get("avg_syll_per_line", 9.0)
  309 [code      ]     user_line = ", ".join(user_words or []) or "(нет)"
  310 [code      ]     parts = [
  311 [code      ]         f"Пиши текст в стиле «{profile.get('author', author) or author}».",
  312 [code      ]         f"Тема: {theme}. Обязательно впиши слова пользователя: {user_line}.",
  313 [code      ]         f"BPM трека: {bpm}. Средняя длина строки — около {avg} слогов.",
  314 [code      ]         "Куплеты на русском, припев/хук может быть на английском.",
  315 [code      ]         f"Целевая длина: {target_lines} строк, без нейроношных повторов, "
  316 [code      ]         "с рифмой AABB или ABAB.",
  317 [code      ]         f"Характерные слова автора: {words}." if words else "",
  318 [code      ]         f"Характерные обороты: {bigs}." if bigs else "",
  319 [code      ]         f"Примеры строк автора:\n{samples}" if samples else "",
  320 [code      ]         "Выдай текст блоками [Куплет 1] / [Припев] / [Куплет 2] / [Аутро].",
  321 [code      ]     ]
  322 [return    ]     return "\n".join(p for p in parts if p)
  323 [blank     ] 
  324 [blank     ] 
  325 [comment   ] # ------------------------------------------------------------- library sweep
  326 [def       ] def scan_library(
  327 [code      ]     references_dir: str | Path = None, vault_dir: str | Path = None
  328 [code      ] ) -> dict:
  329 [docstring ]     """
  330 [docstring ]     Проход по всей библиотеке пользователя: references/*.mp3 → whisper →
  331 [docstring ]     ingest; lyric_vault/*.txt → ingest как unknown если автор неизвестен.
  332 [docstring ]     """
  333 [code      ]     references_dir = Path(references_dir or ROOT / "references")
  334 [code      ]     vault_dir = Path(vault_dir or ROOT / "lyric_vault")
  335 [code      ]     added_audio = added_text = 0
  336 [loop      ]     for ext in ("*.mp3", "*.wav", "*.flac", "*.m4a"):
  337 [loop      ]         for f in references_dir.rglob(ext):
  338 [code      ]             author = f.parent.name if f.parent != references_dir else "unknown"
  339 [code      ]             r = ingest_reference_audio(f, author=author, title=f.stem)
  340 [branch    ]             if r.get("ok"):
  341 [code      ]                 added_audio += 1
  342 [loop      ]     for f in vault_dir.rglob("*.txt"):
  343 [branch    ]         if "author_corpus" in str(f) or "slang" in f.name:
  344 [code      ]             continue
  345 [code      ]         r = ingest_lyrics_file(f, author=f.parent.name or "unknown", title=f.stem)
  346 [branch    ]         if r.get("ok"):
  347 [code      ]             added_text += 1
  348 [return    ]     return {"ok": True, "audio_ingested": added_audio, "text_ingested": added_text}
  349 [blank     ] 
  350 [blank     ] 
  351 [def       ] def list_authors() -> list[dict]:
  352 [code      ]     idx = _load_index()
  353 [return    ]     return [
  354 [code      ]         {"slug": s, "name": d.get("display_name", s), "files": len(d.get("files", []))}
  355 [loop      ]         for s, d in idx.items()
  356 [code      ]     ]
  357 [blank     ] 
  358 [blank     ] 
  359 [branch    ] if __name__ == "__main__":
  360 [import    ]     import sys
  361 [blank     ] 
  362 [branch    ]     if len(sys.argv) > 1 and sys.argv[1] == "scan":
  363 [code      ]         print(json.dumps(scan_library(), ensure_ascii=False, indent=2))
  364 [branch    ]     elif len(sys.argv) > 2 and sys.argv[1] == "profile":
  365 [code      ]         print(
  366 [code      ]             json.dumps(build_style_profile(sys.argv[2]), ensure_ascii=False, indent=2)
  367 [code      ]         )
  368 [branch    ]     else:
  369 [code      ]         print(json.dumps(list_authors(), ensure_ascii=False, indent=2))
```