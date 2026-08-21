# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/user_profile.py`

**Всего строк:** 157

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 55 | 35.0 |
| blank | 37 | 23.6 |
| return | 17 | 10.8 |
| def | 15 | 9.6 |
| docstring | 14 | 8.9 |
| branch | 7 | 4.5 |
| import | 4 | 2.5 |
| try_block | 4 | 2.5 |
| comment | 2 | 1.3 |
| loop | 2 | 1.3 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] user_profile.py — профиль пользователя.
    3 [blank     ] 
    4 [docstring ] Хранит:
    5 [docstring ]   • artist_name — обязательно запрашивается при первом запуске (для ID3-тегов)
    6 [docstring ]   • first_run — маркер первого запуска (для onboarding)
    7 [docstring ]   • quality_mode — Быстрый / Качественный / Максимальный
    8 [docstring ]   • last_settings — последние настройки Wizard
    9 [docstring ]   • favorite_themes, favorite_presets
   10 [docstring ]   • history — последние 100 треков
   11 [docstring ]   • voice_training_hours — сколько всего часов обучения RVC
   12 [docstring ] """
   13 [blank     ] 
   14 [import    ] import json
   15 [import    ] import time
   16 [import    ] from pathlib import Path
   17 [blank     ] 
   18 [code      ] ROOT = Path(__file__).resolve().parents[1]
   19 [code      ] PROFILE_FILE = ROOT / "data" / "user_profile.json"
   20 [comment   ] # v22: ленивое создание (не при импорте)
   21 [blank     ] 
   22 [code      ] DEFAULT_PROFILE = {
   23 [code      ]     "artist_name": "",
   24 [code      ]     "first_run": True,
   25 [code      ]     "quality_mode": "quality",  # fast | quality | max
   26 [code      ]     "last_settings": {},
   27 [code      ]     "favorite_themes": ["лето", "тачки", "деньги", "движ"],
   28 [code      ]     "favorite_presets": ["tamam_like", "brazilian_phonk"],
   29 [code      ]     "history": [],
   30 [code      ]     "voice_training_hours": 0.0,
   31 [code      ]     "voice_training_completed": False,
   32 [code      ]     "created_at": None,
   33 [code      ]     "updated_at": None,
   34 [code      ] }
   35 [blank     ] 
   36 [blank     ] 
   37 [def       ] def get_profile() -> dict:
   38 [branch    ]     if not PROFILE_FILE.exists():
   39 [code      ]         p = dict(DEFAULT_PROFILE)
   40 [code      ]         p["created_at"] = time.time()
   41 [code      ]         p["updated_at"] = p["created_at"]
   42 [code      ]         save_profile(p)
   43 [return    ]         return p
   44 [try_block ]     try:
   45 [code      ]         p = json.load(open(PROFILE_FILE, "r", encoding="utf-8"))
   46 [comment   ]         # Мигрируем недостающие поля
   47 [loop      ]         for k, v in DEFAULT_PROFILE.items():
   48 [code      ]             p.setdefault(k, v)
   49 [return    ]         return p
   50 [try_block ]     except Exception:
   51 [return    ]         return dict(DEFAULT_PROFILE)
   52 [blank     ] 
   53 [blank     ] 
   54 [def       ] def save_profile(p: dict) -> None:
   55 [code      ]     p["updated_at"] = time.time()
   56 [code      ]     PROFILE_FILE.write_text(
   57 [code      ]         json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8"
   58 [code      ]     )
   59 [blank     ] 
   60 [blank     ] 
   61 [def       ] def update(**kwargs) -> dict:
   62 [code      ]     p = get_profile()
   63 [loop      ]     for k, v in kwargs.items():
   64 [code      ]         p[k] = v
   65 [code      ]     save_profile(p)
   66 [return    ]     return p
   67 [blank     ] 
   68 [blank     ] 
   69 [def       ] def is_first_run() -> bool:
   70 [return    ]     return get_profile().get("first_run", True)
   71 [blank     ] 
   72 [blank     ] 
   73 [def       ] def mark_onboarded() -> dict:
   74 [return    ]     return update(first_run=False)
   75 [blank     ] 
   76 [blank     ] 
   77 [def       ] def set_artist_name(name: str) -> dict:
   78 [docstring ]     """Устанавливает имя артиста — пишется в ID3-теги всех треков."""
   79 [code      ]     name = (name or "").strip() or "ZSMM Artist"
   80 [return    ]     return update(artist_name=name)
   81 [blank     ] 
   82 [blank     ] 
   83 [def       ] def get_artist_name() -> str:
   84 [return    ]     return get_profile().get("artist_name") or "ZSMM Artist"
   85 [blank     ] 
   86 [blank     ] 
   87 [def       ] def set_quality_mode(mode: str) -> dict:
   88 [docstring ]     """mode: fast | quality | max"""
   89 [branch    ]     if mode not in ("fast", "quality", "max"):
   90 [code      ]         mode = "quality"
   91 [return    ]     return update(quality_mode=mode)
   92 [blank     ] 
   93 [blank     ] 
   94 [def       ] def add_to_history(entry: dict) -> None:
   95 [code      ]     p = get_profile()
   96 [code      ]     entry.setdefault("timestamp", time.time())
   97 [code      ]     p["history"].append(entry)
   98 [code      ]     p["history"] = p["history"][-100:]  # держим только последние 100
   99 [code      ]     save_profile(p)
  100 [blank     ] 
  101 [blank     ] 
  102 [def       ] def get_history(limit: int = 20) -> list:
  103 [return    ]     return list(reversed(get_profile().get("history", [])))[:limit]
  104 [blank     ] 
  105 [blank     ] 
  106 [def       ] def add_favorite_theme(theme: str) -> dict:
  107 [branch    ]     if not theme:
  108 [return    ]         return {"error": "пусто"}
  109 [code      ]     p = get_profile()
  110 [branch    ]     if theme not in p["favorite_themes"]:
  111 [code      ]         p["favorite_themes"].append(theme)
  112 [code      ]         p["favorite_themes"] = p["favorite_themes"][-30:]
  113 [code      ]         save_profile(p)
  114 [return    ]     return {"ok": True, "themes": p["favorite_themes"]}
  115 [blank     ] 
  116 [blank     ] 
  117 [def       ] def add_favorite_preset(preset_key: str) -> dict:
  118 [branch    ]     if not preset_key:
  119 [return    ]         return {"error": "пусто"}
  120 [code      ]     p = get_profile()
  121 [branch    ]     if preset_key not in p["favorite_presets"]:
  122 [code      ]         p["favorite_presets"].append(preset_key)
  123 [code      ]         p["favorite_presets"] = p["favorite_presets"][-20:]
  124 [code      ]         save_profile(p)
  125 [return    ]     return {"ok": True, "presets": p["favorite_presets"]}
  126 [blank     ] 
  127 [blank     ] 
  128 [def       ] def sync_voice_progress() -> dict:
  129 [docstring ]     """Обновляет прогресс обучения голоса из voice_convert.vault_summary()."""
  130 [try_block ]     try:
  131 [import    ]         from modules.voice_convert import vault_summary
  132 [blank     ] 
  133 [code      ]         v = vault_summary()
  134 [code      ]         p = get_profile()
  135 [code      ]         p["voice_training_hours"] = round(v.get("total_minutes", 0) / 60, 2)
  136 [code      ]         p["voice_training_completed"] = v.get("ready_for_training", False)
  137 [code      ]         save_profile(p)
  138 [return    ]         return {
  139 [code      ]             "ok": True,
  140 [code      ]             "hours": p["voice_training_hours"],
  141 [code      ]             "ready": p["voice_training_completed"],
  142 [code      ]             "detail": v,
  143 [code      ]         }
  144 [try_block ]     except Exception as e:
  145 [return    ]         return {"error": str(e)}
  146 [blank     ] 
  147 [blank     ] 
  148 [def       ] def save_last_settings(settings: dict) -> None:
  149 [code      ]     update(last_settings=settings)
  150 [blank     ] 
  151 [blank     ] 
  152 [def       ] def get_last_settings() -> dict:
  153 [return    ]     return get_profile().get("last_settings", {})
  154 [blank     ] 
  155 [blank     ] 
  156 [branch    ] if __name__ == "__main__":
  157 [code      ]     print(json.dumps(get_profile(), indent=2, ensure_ascii=False))
```