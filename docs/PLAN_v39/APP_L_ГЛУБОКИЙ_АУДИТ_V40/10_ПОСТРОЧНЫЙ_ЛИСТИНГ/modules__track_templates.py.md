# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/track_templates.py`

**Всего строк:** 99

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 30 | 30.3 |
| blank | 24 | 24.2 |
| return | 11 | 11.1 |
| def | 9 | 9.1 |
| docstring | 6 | 6.1 |
| try_block | 6 | 6.1 |
| import | 5 | 5.1 |
| comment | 4 | 4.0 |
| branch | 3 | 3.0 |
| loop | 1 | 1.0 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v8] track_templates.py — сохранение и запуск «Шаблонов трека».
    3 [blank     ] 
    4 [docstring ] ТЗ 20.3: «Мастер должен позволять сохранить Шаблон трека (пресет + тема + длина)
    5 [docstring ] и быстро его запускать повторно. История — последние 100 треков.»
    6 [blank     ] 
    7 [docstring ] Работает поверх recipe.json. Хранит в data/templates/*.json.
    8 [docstring ] """
    9 [blank     ] 
   10 [import    ] from __future__ import annotations
   11 [blank     ] 
   12 [import    ] import json
   13 [import    ] import time
   14 [import    ] import uuid
   15 [import    ] from pathlib import Path
   16 [blank     ] 
   17 [code      ] ROOT = Path(__file__).resolve().parents[1]
   18 [code      ] TPL_DIR = ROOT / "data" / "templates"
   19 [code      ] HIST_FILE = ROOT / "data" / "history.json"
   20 [comment   ] # v22: ленивое создание (не при импорте)
   21 [blank     ] 
   22 [comment   ] # v22: ленивое создание (не при импорте)
   23 [blank     ] 
   24 [blank     ] 
   25 [def       ] def _load_history() -> list[dict]:
   26 [branch    ]     if HIST_FILE.exists():
   27 [try_block ]         try:
   28 [return    ]             return json.loads(HIST_FILE.read_text(encoding="utf-8"))
   29 [try_block ]         except Exception:
   30 [return    ]             return []
   31 [return    ]     return []
   32 [blank     ] 
   33 [blank     ] 
   34 [def       ] def _save_history(items: list[dict]) -> None:
   35 [code      ]     HIST_FILE.write_text(
   36 [code      ]         json.dumps(items[-100:], ensure_ascii=False, indent=2), encoding="utf-8"
   37 [code      ]     )
   38 [blank     ] 
   39 [blank     ] 
   40 [comment   ] # ------------------------------------------------------- templates
   41 [def       ] def save_template(name: str, recipe: dict) -> str:
   42 [code      ]     tid = uuid.uuid4().hex[:10]
   43 [code      ]     data = {
   44 [code      ]         "id": tid,
   45 [code      ]         "name": name,
   46 [code      ]         "created_at": time.time(),
   47 [code      ]         "recipe": recipe,
   48 [code      ]     }
   49 [code      ]     (TPL_DIR / f"{tid}.json").write_text(
   50 [code      ]         json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
   51 [code      ]     )
   52 [return    ]     return tid
   53 [blank     ] 
   54 [blank     ] 
   55 [def       ] def list_templates() -> list[dict]:
   56 [code      ]     out = []
   57 [loop      ]     for f in TPL_DIR.glob("*.json"):
   58 [try_block ]         try:
   59 [code      ]             out.append(json.loads(f.read_text(encoding="utf-8")))
   60 [try_block ]         except Exception:
   61 [code      ]             continue
   62 [code      ]     out.sort(key=lambda d: d.get("created_at", 0), reverse=True)
   63 [return    ]     return out
   64 [blank     ] 
   65 [blank     ] 
   66 [def       ] def load_template(tid: str) -> dict | None:
   67 [code      ]     f = TPL_DIR / f"{tid}.json"
   68 [branch    ]     if not f.exists():
   69 [return    ]         return None
   70 [try_block ]     try:
   71 [return    ]         return json.loads(f.read_text(encoding="utf-8"))
   72 [try_block ]     except Exception:
   73 [return    ]         return None
   74 [blank     ] 
   75 [blank     ] 
   76 [def       ] def delete_template(tid: str) -> bool:
   77 [code      ]     f = TPL_DIR / f"{tid}.json"
   78 [branch    ]     if f.exists():
   79 [code      ]         f.unlink()
   80 [return    ]         return True
   81 [return    ]     return False
   82 [blank     ] 
   83 [blank     ] 
   84 [comment   ] # ------------------------------------------------------- history
   85 [def       ] def push_history(track_meta: dict) -> None:
   86 [code      ]     hist = _load_history()
   87 [code      ]     entry = dict(track_meta)
   88 [code      ]     entry.setdefault("ts", time.time())
   89 [code      ]     entry.setdefault("id", uuid.uuid4().hex[:10])
   90 [code      ]     hist.append(entry)
   91 [code      ]     _save_history(hist)
   92 [blank     ] 
   93 [blank     ] 
   94 [def       ] def get_history(limit: int = 100) -> list[dict]:
   95 [return    ]     return _load_history()[-limit:]
   96 [blank     ] 
   97 [blank     ] 
   98 [def       ] def clear_history() -> None:
   99 [code      ]     _save_history([])
```