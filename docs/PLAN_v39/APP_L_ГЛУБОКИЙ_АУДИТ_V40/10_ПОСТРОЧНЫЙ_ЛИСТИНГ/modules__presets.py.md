# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/presets.py`

**Всего строк:** 170

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 126 | 74.1 |
| blank | 15 | 8.8 |
| return | 7 | 4.1 |
| branch | 6 | 3.5 |
| def | 5 | 2.9 |
| docstring | 4 | 2.4 |
| try_block | 4 | 2.4 |
| import | 2 | 1.2 |
| loop | 1 | 0.6 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [12] presets.py — Библиотека готовых пресетов (v5)
    3 [docstring ] Готовые «стили» для быстрого старта, если пользователь не хочет анализировать референс.
    4 [docstring ] """
    5 [blank     ] 
    6 [import    ] import json
    7 [import    ] import os
    8 [blank     ] 
    9 [code      ] PRESETS_FILE = os.path.join(os.path.dirname(__file__), "..", "presets.json")
   10 [blank     ] 
   11 [code      ] BUILTIN_PRESETS = {
   12 [code      ]     "tamam_like": {
   13 [code      ]         "name": "TAMAM-like (ethnic phonk drift)",
   14 [code      ]         "description": "Тёмный этник-фонк, дрифт, восточные лады, тяжёлый 808 — как TAMAM",
   15 [code      ]         "target_bpm": 129,
   16 [code      ]         "target_mode": "minor",
   17 [code      ]         "vibe_tags": ["phonk/drift", "bass-heavy", "dark", "aggressive", "underground"],
   18 [code      ]         "groove": {
   19 [code      ]             "kick_pattern": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
   20 [code      ]             "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
   21 [code      ]             "hihat_density": 0.55,
   22 [code      ]             "swing": 0.12,
   23 [code      ]         },
   24 [code      ]         "sample_query": "phonk 808 memphis cowbell oriental saz",
   25 [code      ]         "prompt_hint": "dark ethnic drift phonk, distorted 808, memphis cowbell, oriental saz, aggressive",
   26 [code      ]         "themes": ["лето", "движ", "тачки", "деньги", "Стамбул", "чёрный мерс"],
   27 [code      ]     },
   28 [code      ]     "brazilian_phonk": {
   29 [code      ]         "name": "Brazilian phonk / funk",
   30 [code      ]         "description": "Быстрый бразильский фонк, кач как ХЛ, минорные атмосферы",
   31 [code      ]         "target_bpm": 140,
   32 [code      ]         "target_mode": "minor",
   33 [code      ]         "vibe_tags": ["trap/hype", "bass-heavy", "dark"],
   34 [code      ]         "groove": {
   35 [code      ]             "kick_pattern": [1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0],
   36 [code      ]             "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
   37 [code      ]             "hihat_density": 0.75,
   38 [code      ]             "swing": 0.05,
   39 [code      ]         },
   40 [code      ]         "sample_query": "brazilian phonk funk 140 bpm",
   41 [code      ]         "prompt_hint": "brazilian phonk, funk carioca, distorted kick, tuim",
   42 [code      ]         "themes": ["ночь", "движ", "клуб", "разрыв"],
   43 [code      ]     },
   44 [code      ]     "hyperpop_edit": {
   45 [code      ]         "name": "TikTok hyperpop / edit",
   46 [code      ]         "description": "Быстрый хайп для эдитов и коротких видео",
   47 [code      ]         "target_bpm": 160,
   48 [code      ]         "target_mode": "minor",
   49 [code      ]         "vibe_tags": ["hyper/hardstyle", "bright"],
   50 [code      ]         "groove": {
   51 [code      ]             "kick_pattern": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
   52 [code      ]             "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
   53 [code      ]             "hihat_density": 0.85,
   54 [code      ]             "swing": 0.02,
   55 [code      ]         },
   56 [code      ]         "sample_query": "hyperpop tiktok edit anime",
   57 [code      ]         "prompt_hint": "hyperpop, fast edit, pitched vocals, anime aesthetic",
   58 [code      ]         "themes": ["движ", "разрыв", "эдит", "хайп"],
   59 [code      ]     },
   60 [code      ]     "lofi_drift": {
   61 [code      ]         "name": "Lo-Fi drift / chill",
   62 [code      ]         "description": "Медленный ночной драйв, приглушённые барабаны",
   63 [code      ]         "target_bpm": 88,
   64 [code      ]         "target_mode": "minor",
   65 [code      ]         "vibe_tags": ["slow", "dark", "underground"],
   66 [code      ]         "groove": {
   67 [code      ]             "kick_pattern": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
   68 [code      ]             "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
   69 [code      ]             "hihat_density": 0.4,
   70 [code      ]             "swing": 0.2,
   71 [code      ]         },
   72 [code      ]         "sample_query": "lo-fi drift chill night rain vinyl",
   73 [code      ]         "prompt_hint": "lo-fi, night drive, vinyl crackle, muted drums, jazzy chords",
   74 [code      ]         "themes": ["ночь", "тачка", "дождь", "мысли"],
   75 [code      ]     },
   76 [code      ]     "trap_ru": {
   77 [code      ]         "name": "Russian trap / уличка",
   78 [code      ]         "description": "Русский трэп, тяжёлый 808, читка",
   79 [code      ]         "target_bpm": 140,
   80 [code      ]         "target_mode": "minor",
   81 [code      ]         "vibe_tags": ["trap/hype", "bass-heavy", "aggressive", "underground"],
   82 [code      ]         "groove": {
   83 [code      ]             "kick_pattern": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
   84 [code      ]             "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
   85 [code      ]             "hihat_density": 0.7,
   86 [code      ]             "swing": 0.08,
   87 [code      ]         },
   88 [code      ]         "sample_query": "trap 808 dark russian street",
   89 [code      ]         "prompt_hint": "russian street trap, dark 808, syncopated hats, minor keys",
   90 [code      ]         "themes": ["район", "движ", "бабки", "улица"],
   91 [code      ]     },
   92 [code      ] }
   93 [blank     ] 
   94 [blank     ] 
   95 [def       ] def _load_all() -> dict:
   96 [branch    ]     if os.path.exists(PRESETS_FILE):
   97 [try_block ]         try:
   98 [code      ]             user = json.load(open(PRESETS_FILE, encoding="utf-8"))
   99 [try_block ]         except Exception:
  100 [code      ]             user = {}
  101 [branch    ]     else:
  102 [code      ]         user = {}
  103 [code      ]     merged = dict(BUILTIN_PRESETS)
  104 [code      ]     merged.update(user)
  105 [return    ]     return merged
  106 [blank     ] 
  107 [blank     ] 
  108 [def       ] def list_presets() -> list:
  109 [return    ]     return [
  110 [code      ]         {
  111 [code      ]             "key": k,
  112 [code      ]             "name": v["name"],
  113 [code      ]             "description": v["description"],
  114 [code      ]             "bpm": v["target_bpm"],
  115 [code      ]             "tags": v["vibe_tags"],
  116 [code      ]         }
  117 [loop      ]         for k, v in _load_all().items()
  118 [code      ]     ]
  119 [blank     ] 
  120 [blank     ] 
  121 [def       ] def get_preset(key: str) -> dict:
  122 [code      ]     p = _load_all().get(key)
  123 [branch    ]     if not p:
  124 [return    ]         return {"error": f"пресет '{key}' не найден"}
  125 [return    ]     return p
  126 [blank     ] 
  127 [blank     ] 
  128 [def       ] def save_user_preset(key: str, preset: dict) -> dict:
  129 [code      ]     user = {}
  130 [branch    ]     if os.path.exists(PRESETS_FILE):
  131 [try_block ]         try:
  132 [code      ]             user = json.load(open(PRESETS_FILE, encoding="utf-8"))
  133 [try_block ]         except Exception:
  134 [code      ]             user = {}
  135 [code      ]     user[key] = preset
  136 [code      ]     json.dump(
  137 [code      ]         user, open(PRESETS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2
  138 [code      ]     )
  139 [return    ]     return {"ok": True, "key": key, "saved_to": PRESETS_FILE}
  140 [blank     ] 
  141 [blank     ] 
  142 [def       ] def preset_to_style_vector(key: str) -> dict:
  143 [code      ]     p = get_preset(key)
  144 [branch    ]     if "error" in p:
  145 [return    ]         return p
  146 [return    ]     return {
  147 [code      ]         "sources": [f"preset:{key}"],
  148 [code      ]         "target_bpm": p["target_bpm"],
  149 [code      ]         "target_mode": p["target_mode"],
  150 [code      ]         "vibe_tags": p["vibe_tags"],
  151 [code      ]         "target_bass_ratio": 1.5,
  152 [code      ]         "target_centroid": 1500.0,
  153 [code      ]         "bpm_range": {
  154 [code      ]             "center": p["target_bpm"],
  155 [code      ]             "range_low": p["target_bpm"] - 6,
  156 [code      ]             "range_high": p["target_bpm"] + 8,
  157 [code      ]             "modes": {"keep_groove": p["target_bpm"]},
  158 [code      ]         },
  159 [code      ]         "individual": [
  160 [code      ]             {"key_root": "A", "bpm": p["target_bpm"], "vibe_tags": p["vibe_tags"]}
  161 [code      ]         ],
  162 [code      ]         "preset_key": key,
  163 [code      ]         "themes_hint": p.get("themes", []),
  164 [code      ]         "sample_query_hint": p.get("sample_query", ""),
  165 [code      ]         "prompt_hint": p.get("prompt_hint", ""),
  166 [code      ]     }
  167 [blank     ] 
  168 [blank     ] 
  169 [branch    ] if __name__ == "__main__":
  170 [code      ]     print(json.dumps(list_presets(), ensure_ascii=False, indent=2))
```