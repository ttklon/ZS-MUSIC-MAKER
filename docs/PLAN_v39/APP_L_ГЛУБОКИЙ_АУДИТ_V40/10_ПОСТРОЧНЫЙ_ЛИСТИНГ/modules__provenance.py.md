# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/provenance.py`

**Всего строк:** 142

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 94 | 66.2 |
| blank | 17 | 12.0 |
| docstring | 8 | 5.6 |
| return | 7 | 4.9 |
| def | 6 | 4.2 |
| import | 3 | 2.1 |
| branch | 3 | 2.1 |
| try_block | 2 | 1.4 |
| comment | 1 | 0.7 |
| loop | 1 | 0.7 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [10] provenance.py — License / Provenance Manager v2 (НОВЫЙ)
    3 [docstring ] Отслеживает происхождение каждого сэмпла, условия использования и предупреждения.
    4 [docstring ] Важно для Freesound (разные CC-лицензии) и MusicRadar (royalty-free, но не redistribute).
    5 [docstring ] """
    6 [blank     ] 
    7 [import    ] import json
    8 [import    ] import os
    9 [import    ] import time
   10 [blank     ] 
   11 [code      ] VAULT = os.path.join(
   12 [code      ]     os.path.dirname(__file__), "..", "samples_cache", "provenance.json"
   13 [code      ] )
   14 [comment   ] # v22: ленивое создание (не при импорте)
   15 [blank     ] 
   16 [code      ] LICENSES = {
   17 [code      ]     "cc0": {
   18 [code      ]         "name": "CC0 — Public Domain",
   19 [code      ]         "commercial": True,
   20 [code      ]         "attribution": False,
   21 [code      ]         "note": "Свободное использование без ограничений",
   22 [code      ]     },
   23 [code      ]     "cc-by": {
   24 [code      ]         "name": "CC-BY — Attribution",
   25 [code      ]         "commercial": True,
   26 [code      ]         "attribution": True,
   27 [code      ]         "note": "Нужно указать автора",
   28 [code      ]     },
   29 [code      ]     "cc-by-nc": {
   30 [code      ]         "name": "CC-BY-NC — NonCommercial",
   31 [code      ]         "commercial": False,
   32 [code      ]         "attribution": True,
   33 [code      ]         "note": "Только некоммерческое использование. Указать автора.",
   34 [code      ]     },
   35 [code      ]     "cc-by-sa": {
   36 [code      ]         "name": "CC-BY-SA — ShareAlike",
   37 [code      ]         "commercial": True,
   38 [code      ]         "attribution": True,
   39 [code      ]         "note": "Указать автора. Производные — на той же лицензии.",
   40 [code      ]     },
   41 [code      ]     "cc-by-nc-sa": {
   42 [code      ]         "name": "CC-BY-NC-SA",
   43 [code      ]         "commercial": False,
   44 [code      ]         "attribution": True,
   45 [code      ]         "note": "Некоммерческое. Указать автора. ShareAlike.",
   46 [code      ]     },
   47 [code      ]     "royalty_free": {
   48 [code      ]         "name": "Royalty-Free",
   49 [code      ]         "commercial": True,
   50 [code      ]         "attribution": False,
   51 [code      ]         "note": "Свободное использование в музыке. Не перераспространять как пак.",
   52 [code      ]     },
   53 [code      ]     "unknown": {
   54 [code      ]         "name": "Unknown — проверить вручную",
   55 [code      ]         "commercial": False,
   56 [code      ]         "attribution": True,
   57 [code      ]         "note": "Лицензия не определена. Проверьте перед использованием.",
   58 [code      ]     },
   59 [code      ] }
   60 [blank     ] 
   61 [blank     ] 
   62 [def       ] def _load():
   63 [branch    ]     if os.path.exists(VAULT):
   64 [try_block ]         try:
   65 [return    ]             return json.load(open(VAULT, encoding="utf-8"))
   66 [try_block ]         except Exception:
   67 [return    ]             return []
   68 [return    ]     return []
   69 [blank     ] 
   70 [blank     ] 
   71 [def       ] def _save(data):
   72 [code      ]     json.dump(data, open(VAULT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
   73 [blank     ] 
   74 [blank     ] 
   75 [def       ] def add_sample(
   76 [code      ]     name: str,
   77 [code      ]     path: str,
   78 [code      ]     source_url: str = "",
   79 [code      ]     license_key: str = "unknown",
   80 [code      ]     author: str = "",
   81 [code      ]     tags: list = None,
   82 [code      ]     bpm: float = None,
   83 [code      ]     key: str = "",
   84 [code      ] ) -> dict:
   85 [docstring ]     """Регистрирует сэмпл в provenance базе."""
   86 [code      ]     entry = {
   87 [code      ]         "name": name,
   88 [code      ]         "path": path,
   89 [code      ]         "source": source_url,
   90 [code      ]         "license": license_key,
   91 [code      ]         "license_info": LICENSES.get(license_key, LICENSES["unknown"]),
   92 [code      ]         "author": author,
   93 [code      ]         "tags": tags or [],
   94 [code      ]         "bpm": bpm,
   95 [code      ]         "key": key,
   96 [code      ]         "added": time.time(),
   97 [code      ]     }
   98 [code      ]     data = _load()
   99 [code      ]     data.append(entry)
  100 [code      ]     _save(data)
  101 [return    ]     return entry
  102 [blank     ] 
  103 [blank     ] 
  104 [def       ] def list_samples() -> list:
  105 [return    ]     return _load()
  106 [blank     ] 
  107 [blank     ] 
  108 [def       ] def check_commercial_safe() -> dict:
  109 [docstring ]     """Проверяет все сэмплы на возможность коммерческого использования."""
  110 [code      ]     data = _load()
  111 [code      ]     safe = [s for s in data if s.get("license_info", {}).get("commercial", False)]
  112 [code      ]     unsafe = [s for s in data if not s.get("license_info", {}).get("commercial", False)]
  113 [code      ]     needs_attribution = [
  114 [code      ]         s for s in data if s.get("license_info", {}).get("attribution", False)
  115 [code      ]     ]
  116 [return    ]     return {
  117 [code      ]         "total": len(data),
  118 [code      ]         "commercial_safe": len(safe),
  119 [code      ]         "non_commercial": len(unsafe),
  120 [code      ]         "needs_attribution": len(needs_attribution),
  121 [code      ]         "safe_samples": [s["name"] for s in safe],
  122 [code      ]         "unsafe_samples": [
  123 [code      ]             {"name": s["name"], "license": s.get("license")} for s in unsafe
  124 [code      ]         ],
  125 [code      ]     }
  126 [blank     ] 
  127 [blank     ] 
  128 [def       ] def generate_attribution_text() -> str:
  129 [docstring ]     """Генерирует текст атрибуции для всех сэмплов требующих указания автора."""
  130 [code      ]     data = _load()
  131 [code      ]     lines = ["=== Атрибуция сэмплов ===\n"]
  132 [loop      ]     for s in data:
  133 [code      ]         info = s.get("license_info", {})
  134 [branch    ]         if info.get("attribution"):
  135 [code      ]             lines.append(
  136 [code      ]                 f"• {s['name']} — {s.get('author', 'unknown')} — {info['name']} — {s.get('source', '')}"
  137 [code      ]             )
  138 [return    ]     return "\n".join(lines) if len(lines) > 1 else "Атрибуция не требуется."
  139 [blank     ] 
  140 [blank     ] 
  141 [branch    ] if __name__ == "__main__":
  142 [code      ]     print(json.dumps(check_commercial_safe(), ensure_ascii=False, indent=2))
```