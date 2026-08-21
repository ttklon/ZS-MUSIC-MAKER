# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/lyric_vault_v10.py`

**Всего строк:** 252

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 118 | 46.8 |
| docstring | 35 | 13.9 |
| blank | 29 | 11.5 |
| branch | 20 | 7.9 |
| return | 11 | 4.4 |
| def | 10 | 4.0 |
| loop | 10 | 4.0 |
| import | 8 | 3.2 |
| try_block | 4 | 1.6 |
| comment | 4 | 1.6 |
| stmt | 3 | 1.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v10 — Lyric Vault v10
    3 [docstring ] ======================================
    4 [docstring ] Расширенное хранилище лирики (ТЗ 3.7).
    5 [blank     ] 
    6 [docstring ] Возможности v10 (сверх lyrics_memory.jsonl v9):
    7 [docstring ]   - индекс по BPM / слоговой плотности / эмоции / темам
    8 [docstring ]   - кросс-жанровое смешение хуков
    9 [docstring ]   - поиск подходящих панчей под текущий BPM
   10 [docstring ]   - экспорт в LRC с тайм-кодами
   11 [docstring ]   - импорт из чужих транскриптов с автопомечанием
   12 [docstring ]   - анти-повтор: чтобы одни и те же строки не всплывали 5 треков подряд
   13 [docstring ] """
   14 [blank     ] 
   15 [import    ] from __future__ import annotations
   16 [blank     ] 
   17 [import    ] import hashlib
   18 [import    ] import json
   19 [import    ] import logging
   20 [import    ] import time
   21 [import    ] from collections import Counter
   22 [import    ] from pathlib import Path
   23 [import    ] from typing import Any
   24 [blank     ] 
   25 [code      ] log = logging.getLogger("zsmm.lyric_vault_v10")
   26 [blank     ] 
   27 [code      ] VAULT = Path("lyric_vault")
   28 [code      ] MEMORY_JSONL = VAULT / "lyrics_memory.jsonl"
   29 [code      ] INDEX_JSON = VAULT / "vault_index_v10.json"
   30 [code      ] USAGE_LOG = VAULT / "line_usage_log.json"
   31 [blank     ] 
   32 [blank     ] 
   33 [def       ] def _syllable_count(line: str) -> int:
   34 [docstring ]     """
   35 [docstring ]     Приблизительный подсчёт слогов (RU/EN).
   36 [docstring ]     Для RU считаем гласные, для EN — группы гласных.
   37 [docstring ]     """
   38 [code      ]     line = line.lower()
   39 [code      ]     ru_vowels = set("аеёиоуыэюяaeiouy")
   40 [code      ]     n = 0
   41 [code      ]     prev_vowel = False
   42 [loop      ]     for ch in line:
   43 [code      ]         is_v = ch in ru_vowels
   44 [branch    ]         if is_v and not prev_vowel:
   45 [code      ]             n += 1
   46 [code      ]         prev_vowel = is_v
   47 [return    ]     return max(1, n)
   48 [blank     ] 
   49 [blank     ] 
   50 [def       ] def add_line(
   51 [code      ]     text: str,
   52 [code      ]     bpm: int | None = None,
   53 [code      ]     emotion: str = "neutral",
   54 [code      ]     topic: str = "generic",
   55 [code      ]     lang: str = "ru",
   56 [code      ]     source: str = "user",
   57 [code      ] ) -> dict[str, Any]:
   58 [docstring ]     """
   59 [docstring ]     Добавляет строку в vault.
   60 [docstring ]     """
   61 [code      ]     VAULT.mkdir(parents=True, exist_ok=True)
   62 [code      ]     entry = {
   63 [code      ]         "id": hashlib.md5(f"{text}{time.time()}".encode()).hexdigest()[:10],
   64 [code      ]         "text": text.strip(),
   65 [code      ]         "syllables": _syllable_count(text),
   66 [code      ]         "bpm": bpm,
   67 [code      ]         "emotion": emotion,
   68 [code      ]         "topic": topic,
   69 [code      ]         "lang": lang,
   70 [code      ]         "source": source,
   71 [code      ]         "created_at": int(time.time()),
   72 [code      ]         "use_count": 0,
   73 [code      ]     }
   74 [stmt      ]     with open(MEMORY_JSONL, "a", encoding="utf-8") as f:
   75 [code      ]         f.write(json.dumps(entry, ensure_ascii=False) + "\n")
   76 [return    ]     return entry
   77 [blank     ] 
   78 [blank     ] 
   79 [def       ] def load_all() -> list[dict[str, Any]]:
   80 [docstring ]     """
   81 [docstring ]     Загружает все записи из lyrics_memory.jsonl.
   82 [docstring ]     Совместимость: v9-записи (поле 'lyrics' вместо 'text', без 'id')
   83 [docstring ]     нормализуются в v10-схему на лету, без перезаписи файла.
   84 [docstring ]     """
   85 [branch    ]     if not MEMORY_JSONL.exists():
   86 [return    ]         return []
   87 [code      ]     out = []
   88 [stmt      ]     with open(MEMORY_JSONL, "r", encoding="utf-8") as f:
   89 [loop      ]         for i, line in enumerate(f):
   90 [code      ]             line = line.strip()
   91 [branch    ]             if not line:
   92 [code      ]                 continue
   93 [try_block ]             try:
   94 [code      ]                 entry = json.loads(line)
   95 [try_block ]             except Exception:
   96 [code      ]                 continue
   97 [comment   ]             # v9 -> v10 нормализация
   98 [branch    ]             if "id" not in entry:
   99 [code      ]                 base = str(entry.get("text") or entry.get("lyrics") or i)
  100 [code      ]                 entry["id"] = hashlib.md5(base.encode()).hexdigest()[:10]
  101 [branch    ]             if "text" not in entry:
  102 [code      ]                 entry["text"] = entry.get("lyrics", "")
  103 [branch    ]             if "syllables" not in entry:
  104 [code      ]                 entry["syllables"] = _syllable_count(str(entry.get("text", "")))
  105 [code      ]             out.append(entry)
  106 [return    ]     return out
  107 [blank     ] 
  108 [blank     ] 
  109 [def       ] def find_lines(
  110 [code      ]     bpm: int | None = None,
  111 [code      ]     emotion: str | None = None,
  112 [code      ]     topic: str | None = None,
  113 [code      ]     lang: str | None = None,
  114 [code      ]     syllable_min: int | None = None,
  115 [code      ]     syllable_max: int | None = None,
  116 [code      ]     limit: int = 20,
  117 [code      ]     anti_repeat: bool = True,
  118 [code      ] ) -> list[dict[str, Any]]:
  119 [docstring ]     """
  120 [docstring ]     Ищет подходящие строки. Anti-repeat: строки использованные
  121 [docstring ]     за последние 5 треков — отфильтровываются.
  122 [docstring ]     """
  123 [code      ]     all_lines = load_all()
  124 [code      ]     recently_used = _recently_used_ids(last_n_tracks=5) if anti_repeat else set()
  125 [blank     ] 
  126 [code      ]     matched = []
  127 [loop      ]     for e in all_lines:
  128 [branch    ]         if e["id"] in recently_used:
  129 [code      ]             continue
  130 [branch    ]         if bpm and e.get("bpm") and abs(e["bpm"] - bpm) > 15:
  131 [code      ]             continue
  132 [branch    ]         if emotion and e.get("emotion") != emotion:
  133 [code      ]             continue
  134 [branch    ]         if topic and e.get("topic") != topic:
  135 [code      ]             continue
  136 [branch    ]         if lang and e.get("lang") != lang:
  137 [code      ]             continue
  138 [code      ]         syl = e.get("syllables", 0)
  139 [branch    ]         if syllable_min and syl < syllable_min:
  140 [code      ]             continue
  141 [branch    ]         if syllable_max and syl > syllable_max:
  142 [code      ]             continue
  143 [code      ]         matched.append(e)
  144 [blank     ] 
  145 [comment   ]     # сортируем по use_count (свежее сначала)
  146 [code      ]     matched.sort(key=lambda x: (x.get("use_count", 0), -x.get("created_at", 0)))
  147 [return    ]     return matched[:limit]
  148 [blank     ] 
  149 [blank     ] 
  150 [def       ] def mark_used(line_ids: list[str], track_id: str) -> None:
  151 [docstring ]     """
  152 [docstring ]     Отмечает строки как использованные в треке (для anti-repeat).
  153 [docstring ]     """
  154 [code      ]     usage = _load_usage()
  155 [code      ]     ts = int(time.time())
  156 [loop      ]     for lid in line_ids:
  157 [code      ]         usage.setdefault(lid, []).append({"track": track_id, "at": ts})
  158 [code      ]     _save_usage(usage)
  159 [blank     ] 
  160 [blank     ] 
  161 [def       ] def rebuild_index() -> dict[str, Any]:
  162 [code      ]     all_lines = load_all()
  163 [code      ]     idx = {
  164 [code      ]         "total_lines": len(all_lines),
  165 [code      ]         "by_lang": dict(Counter(e.get("lang", "?") for e in all_lines)),
  166 [code      ]         "by_emotion": dict(Counter(e.get("emotion", "?") for e in all_lines)),
  167 [code      ]         "by_topic": dict(Counter(e.get("topic", "?") for e in all_lines)),
  168 [code      ]         "bpm_range": {
  169 [code      ]             "min": min((e["bpm"] for e in all_lines if e.get("bpm")), default=None),
  170 [code      ]             "max": max((e["bpm"] for e in all_lines if e.get("bpm")), default=None),
  171 [code      ]         },
  172 [code      ]         "syllable_hist": dict(Counter(e.get("syllables", 0) for e in all_lines)),
  173 [code      ]         "rebuilt_at": int(time.time()),
  174 [code      ]     }
  175 [code      ]     VAULT.mkdir(parents=True, exist_ok=True)
  176 [code      ]     INDEX_JSON.write_text(
  177 [code      ]         json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8"
  178 [code      ]     )
  179 [return    ]     return idx
  180 [blank     ] 
  181 [blank     ] 
  182 [def       ] def export_lrc(
  183 [code      ]     lines: list[dict[str, Any]],
  184 [code      ]     out_lrc: str,
  185 [code      ]     bpm: int = 120,
  186 [code      ]     start_offset_ms: int = 4000,
  187 [code      ] ) -> str:
  188 [docstring ]     """
  189 [docstring ]     Экспорт в LRC с тайм-кодами (для караоке).
  190 [docstring ]     Устойчив к разным shape'ам входа — если нет 'text', используется str(item).
  191 [docstring ]     """
  192 [code      ]     beat_ms = int(60000 / bpm)
  193 [code      ]     bar_ms = beat_ms * 4
  194 [code      ]     Path(out_lrc).parent.mkdir(parents=True, exist_ok=True)
  195 [stmt      ]     with open(out_lrc, "w", encoding="utf-8") as f:
  196 [code      ]         f.write("[ti:Track]\n[ar:ZS]\n[al:MM ZS Vault Export]\n\n")
  197 [code      ]         t = start_offset_ms
  198 [loop      ]         for e in lines:
  199 [branch    ]             if isinstance(e, dict):
  200 [code      ]                 text = e.get("text") or e.get("line") or ""
  201 [code      ]                 syl = e.get("syllables", _syllable_count(text) if text else 4)
  202 [branch    ]             else:
  203 [code      ]                 text = str(e)
  204 [code      ]                 syl = _syllable_count(text)
  205 [code      ]             mm = t // 60000
  206 [code      ]             ss = (t % 60000) / 1000.0
  207 [code      ]             f.write(f"[{mm:02d}:{ss:05.2f}]{text}\n")
  208 [code      ]             t += max(bar_ms, syl * (beat_ms // 2))
  209 [return    ]     return out_lrc
  210 [blank     ] 
  211 [blank     ] 
  212 [def       ] def _recently_used_ids(last_n_tracks: int = 5) -> set:
  213 [code      ]     usage = _load_usage()
  214 [comment   ]     # собираем все track_id и берём последние N
  215 [code      ]     all_tracks = []
  216 [loop      ]     for lid, entries in usage.items():
  217 [loop      ]         for e in entries:
  218 [code      ]             all_tracks.append((e["at"], e["track"]))
  219 [code      ]     all_tracks.sort(reverse=True)
  220 [comment   ]     # уникальные track_id, сохраняем порядок
  221 [code      ]     seen = []
  222 [loop      ]     for _, t in all_tracks:
  223 [branch    ]         if t not in seen:
  224 [code      ]             seen.append(t)
  225 [branch    ]         if len(seen) >= last_n_tracks:
  226 [code      ]             break
  227 [code      ]     recent_tracks = set(seen)
  228 [code      ]     used = set()
  229 [loop      ]     for lid, entries in usage.items():
  230 [loop      ]         for e in entries:
  231 [branch    ]             if e["track"] in recent_tracks:
  232 [code      ]                 used.add(lid)
  233 [return    ]     return used
  234 [blank     ] 
  235 [blank     ] 
  236 [def       ] def _load_usage() -> dict[str, list]:
  237 [branch    ]     if USAGE_LOG.exists():
  238 [try_block ]         try:
  239 [return    ]             return json.loads(USAGE_LOG.read_text(encoding="utf-8"))
  240 [try_block ]         except Exception:
  241 [return    ]             return {}
  242 [return    ]     return {}
  243 [blank     ] 
  244 [blank     ] 
  245 [def       ] def _save_usage(u: dict[str, list]) -> None:
  246 [code      ]     VAULT.mkdir(parents=True, exist_ok=True)
  247 [code      ]     USAGE_LOG.write_text(json.dumps(u, ensure_ascii=False, indent=2), encoding="utf-8")
  248 [blank     ] 
  249 [blank     ] 
  250 [branch    ] if __name__ == "__main__":
  251 [code      ]     r = rebuild_index()
  252 [code      ]     print(json.dumps(r, ensure_ascii=False, indent=2))
```