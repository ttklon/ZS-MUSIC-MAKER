# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/arrangement_engine.py`

**Всего строк:** 325

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 210 | 64.6 |
| blank | 34 | 10.5 |
| docstring | 23 | 7.1 |
| branch | 18 | 5.5 |
| comment | 15 | 4.6 |
| return | 12 | 3.7 |
| def | 6 | 1.8 |
| import | 5 | 1.5 |
| loop | 2 | 0.6 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v9] arrangement_engine.py — планировщик аранжировки 1:30-3:30+.
    3 [blank     ] 
    4 [docstring ] По ТЗ 3.5 (Beat Constructor / Arrangement Engine):
    5 [docstring ]   «Ритм и аранжировка строятся ЗАНОВО, а не копируются».
    6 [blank     ] 
    7 [docstring ] Модуль НЕ генерирует аудио — он создаёт ARRANGEMENT PLAN (JSON), который
    8 [docstring ] скармливается beat_constructor.py и mixdown.py. Планов может быть несколько
    9 [docstring ] на трек (варианты).
   10 [blank     ] 
   11 [docstring ] План описывает:
   12 [docstring ]   • Общую длину и BPM.
   13 [docstring ]   • Список секций: intro, verse1, prechorus, chorus1, verse2, prechorus, chorus2,
   14 [docstring ]     bridge, chorus3, outro. Каждая секция — n bars, energy 0..1, elements.
   15 [docstring ]   • Элементы: kick_pattern, snare_pattern, hihat_pattern, 808_note,
   16 [docstring ]     lead_texture, pad_texture, fx, vocal_role.
   17 [docstring ]   • Переходы: fill_before, silence_before_ms, riser, downlifter.
   18 [docstring ]   • TikTok-hook window (25 sec) с моментальным входом.
   19 [blank     ] 
   20 [docstring ] Учитывает style_vector из reference_ingest.py и hit_scorer targets.
   21 [docstring ] """
   22 [blank     ] 
   23 [import    ] from __future__ import annotations
   24 [blank     ] 
   25 [import    ] import json
   26 [import    ] import random
   27 [import    ] import time
   28 [import    ] from pathlib import Path
   29 [blank     ] 
   30 [comment   ] # ---------------------------------------------------------- templates
   31 [comment   ] # Каждый шаблон — базовая структура для жанра.
   32 [comment   ] # Секции: (name, bars_default, energy, vocal_role)
   33 [code      ] GENRE_TEMPLATES = {
   34 [code      ]     "phonk / drift": [
   35 [code      ]         ("intro", 4, 0.35, "silence"),
   36 [code      ]         ("verse1", 8, 0.55, "rap"),
   37 [code      ]         ("prechorus", 4, 0.65, "rap"),
   38 [code      ]         ("chorus1", 8, 0.90, "hook_ru_en"),
   39 [code      ]         ("verse2", 8, 0.60, "rap"),
   40 [code      ]         ("prechorus", 4, 0.70, "rap"),
   41 [code      ]         ("chorus2", 8, 0.95, "hook_ru_en"),
   42 [code      ]         ("bridge", 4, 0.50, "adlib"),
   43 [code      ]         ("chorus3", 8, 1.00, "hook_ru_en_female"),
   44 [code      ]         ("outro", 4, 0.30, "adlib"),
   45 [code      ]     ],
   46 [code      ]     "dance / edm": [
   47 [code      ]         ("intro", 8, 0.30, "silence"),
   48 [code      ]         ("build1", 8, 0.55, "adlib"),
   49 [code      ]         ("drop1", 16, 0.95, "hook_en"),
   50 [code      ]         ("break", 8, 0.45, "sing"),
   51 [code      ]         ("build2", 8, 0.60, "adlib"),
   52 [code      ]         ("drop2", 16, 1.00, "hook_en"),
   53 [code      ]         ("outro", 8, 0.30, "silence"),
   54 [code      ]     ],
   55 [code      ]     "trap / hip-hop": [
   56 [code      ]         ("intro", 4, 0.40, "silence"),
   57 [code      ]         ("verse1", 16, 0.55, "rap"),
   58 [code      ]         ("chorus1", 8, 0.85, "hook_ru"),
   59 [code      ]         ("verse2", 16, 0.60, "rap"),
   60 [code      ]         ("chorus2", 8, 0.95, "hook_ru_en"),
   61 [code      ]         ("bridge", 8, 0.50, "adlib"),
   62 [code      ]         ("chorus3", 8, 1.00, "hook_ru_en_female"),
   63 [code      ]         ("outro", 4, 0.30, "silence"),
   64 [code      ]     ],
   65 [code      ]     "pop / r&b": [
   66 [code      ]         ("intro", 4, 0.35, "silence"),
   67 [code      ]         ("verse1", 8, 0.55, "sing"),
   68 [code      ]         ("prechorus", 4, 0.65, "sing"),
   69 [code      ]         ("chorus1", 8, 0.90, "hook_ru_en_female"),
   70 [code      ]         ("verse2", 8, 0.60, "sing"),
   71 [code      ]         ("prechorus", 4, 0.70, "sing"),
   72 [code      ]         ("chorus2", 8, 0.95, "hook_ru_en_female"),
   73 [code      ]         ("bridge", 8, 0.50, "sing"),
   74 [code      ]         ("chorus3", 8, 1.00, "hook_ru_en_female"),
   75 [code      ]         ("outro", 4, 0.30, "silence"),
   76 [code      ]     ],
   77 [code      ]     "hardstyle / techno": [
   78 [code      ]         ("intro", 16, 0.30, "silence"),
   79 [code      ]         ("build1", 8, 0.55, "adlib"),
   80 [code      ]         ("drop1", 16, 1.00, "shout"),
   81 [code      ]         ("break", 8, 0.40, "silence"),
   82 [code      ]         ("build2", 8, 0.60, "adlib"),
   83 [code      ]         ("drop2", 16, 1.00, "shout"),
   84 [code      ]         ("outro", 8, 0.30, "silence"),
   85 [code      ]     ],
   86 [code      ]     "generic hit": [
   87 [code      ]         ("intro", 4, 0.35, "silence"),
   88 [code      ]         ("verse1", 8, 0.55, "rap"),
   89 [code      ]         ("chorus1", 8, 0.90, "hook_ru_en"),
   90 [code      ]         ("verse2", 8, 0.60, "rap"),
   91 [code      ]         ("chorus2", 8, 0.95, "hook_ru_en"),
   92 [code      ]         ("bridge", 4, 0.50, "adlib"),
   93 [code      ]         ("chorus3", 8, 1.00, "hook_ru_en_female"),
   94 [code      ]         ("outro", 4, 0.30, "silence"),
   95 [code      ]     ],
   96 [code      ] }
   97 [blank     ] 
   98 [comment   ] # Паттерны ударных для разных energy-уровней (16 ступеней = 1 bar в 16-х)
   99 [code      ] KICK_PATTERNS = {
  100 [code      ]     "sparse": [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
  101 [code      ]     "trap": [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
  102 [code      ]     "four_floor": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
  103 [code      ]     "phonk": [1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1],
  104 [code      ]     "hard": [1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1],
  105 [code      ] }
  106 [code      ] SNARE_PATTERNS = {
  107 [code      ]     "backbeat": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
  108 [code      ]     "trap": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
  109 [code      ]     "clap": [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0],
  110 [code      ] }
  111 [code      ] HIHAT_PATTERNS = {
  112 [code      ]     "eighth": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
  113 [code      ]     "sixteenth": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
  114 [code      ]     "trap": [1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1],
  115 [code      ]     "phonk": [1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1],
  116 [code      ] }
  117 [blank     ] 
  118 [blank     ] 
  119 [comment   ] # ============================================================ helpers
  120 [def       ] def _pick(rng, patterns_dict, keys):
  121 [loop      ]     for k in keys:
  122 [branch    ]         if k in patterns_dict:
  123 [return    ]             return k, patterns_dict[k]
  124 [code      ]     k = rng.choice(list(patterns_dict.keys()))
  125 [return    ]     return k, patterns_dict[k]
  126 [blank     ] 
  127 [blank     ] 
  128 [def       ] def _bars_to_seconds(bars: int, bpm: float, beats_per_bar: int = 4) -> float:
  129 [return    ]     return bars * beats_per_bar * (60.0 / max(bpm, 1e-3))
  130 [blank     ] 
  131 [blank     ] 
  132 [def       ] def _clamp(x, lo, hi):
  133 [return    ]     return max(lo, min(hi, x))
  134 [blank     ] 
  135 [blank     ] 
  136 [comment   ] # ============================================================ main API
  137 [def       ] def build_arrangement(
  138 [code      ]     style_vector: dict,
  139 [code      ]     total_seconds: float = 150.0,
  140 [code      ]     seed: int | None = None,
  141 [code      ]     genre_override: str | None = None,
  142 [code      ]     hit_targets: dict | None = None,
  143 [code      ]     variant: int = 0,
  144 [code      ] ) -> dict:
  145 [docstring ]     """
  146 [docstring ]     Основной API. Строит план аранжировки под style_vector.
  147 [docstring ]       total_seconds: 90..300, default 150 (2:30)
  148 [docstring ]       variant: 0 — safe, 1 — bolder, 2 — experimental
  149 [docstring ]     Возвращает dict с ключом 'sections' (list) и 'meta'.
  150 [docstring ]     """
  151 [code      ]     rng = random.Random(seed or int(time.time()))
  152 [code      ]     sv = style_vector or {}
  153 [code      ]     bpm = float(sv.get("bpm", 130.0))
  154 [code      ]     key = sv.get("key", "C")
  155 [code      ]     mode = sv.get("mode", "minor")
  156 [code      ]     genre = genre_override or sv.get("genre_hint") or _guess_genre(sv)
  157 [code      ]     mood = sv.get("mood", "energetic / driving")
  158 [blank     ] 
  159 [code      ]     template = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["generic hit"])
  160 [blank     ] 
  161 [comment   ]     # Подгоняем общую длину под total_seconds — масштабируем bars
  162 [code      ]     default_seconds = sum(_bars_to_seconds(b, bpm) for _, b, _, _ in template)
  163 [code      ]     scale = _clamp(total_seconds / max(default_seconds, 1e-3), 0.5, 2.0)
  164 [blank     ] 
  165 [comment   ]     # Выбор паттернов по жанру
  166 [branch    ]     if "phonk" in genre:
  167 [code      ]         kick_key, kick = _pick(rng, KICK_PATTERNS, ["phonk", "trap"])
  168 [code      ]         snare_key, snare = _pick(rng, SNARE_PATTERNS, ["backbeat", "clap"])
  169 [code      ]         hh_key, hh = _pick(rng, HIHAT_PATTERNS, ["phonk", "trap"])
  170 [branch    ]     elif "dance" in genre or "techno" in genre or "hard" in genre:
  171 [code      ]         kick_key, kick = _pick(rng, KICK_PATTERNS, ["four_floor", "hard"])
  172 [code      ]         snare_key, snare = _pick(rng, SNARE_PATTERNS, ["clap", "backbeat"])
  173 [code      ]         hh_key, hh = _pick(rng, HIHAT_PATTERNS, ["eighth", "sixteenth"])
  174 [branch    ]     elif "trap" in genre or "hip-hop" in genre:
  175 [code      ]         kick_key, kick = _pick(rng, KICK_PATTERNS, ["trap", "sparse"])
  176 [code      ]         snare_key, snare = _pick(rng, SNARE_PATTERNS, ["trap", "clap"])
  177 [code      ]         hh_key, hh = _pick(rng, HIHAT_PATTERNS, ["trap", "sixteenth"])
  178 [branch    ]     elif "pop" in genre or "r&b" in genre:
  179 [code      ]         kick_key, kick = _pick(rng, KICK_PATTERNS, ["sparse", "four_floor"])
  180 [code      ]         snare_key, snare = _pick(rng, SNARE_PATTERNS, ["backbeat", "clap"])
  181 [code      ]         hh_key, hh = _pick(rng, HIHAT_PATTERNS, ["eighth"])
  182 [branch    ]     else:
  183 [code      ]         kick_key, kick = _pick(rng, KICK_PATTERNS, ["trap"])
  184 [code      ]         snare_key, snare = _pick(rng, SNARE_PATTERNS, ["backbeat"])
  185 [code      ]         hh_key, hh = _pick(rng, HIHAT_PATTERNS, ["eighth"])
  186 [blank     ] 
  187 [code      ]     sections = []
  188 [code      ]     t_cursor = 0.0
  189 [loop      ]     for i, (name, bars_def, energy, vrole) in enumerate(template):
  190 [code      ]         bars = max(2, int(round(bars_def * scale)))
  191 [code      ]         dur = _bars_to_seconds(bars, bpm)
  192 [blank     ] 
  193 [comment   ]         # Модификации по variant
  194 [branch    ]         if variant >= 1 and "chorus" in name:
  195 [code      ]             energy = min(1.0, energy + 0.03)
  196 [branch    ]         if variant >= 2 and name in ("verse1", "verse2"):
  197 [code      ]             energy = _clamp(energy + rng.uniform(-0.08, 0.08), 0.3, 0.85)
  198 [blank     ] 
  199 [comment   ]         # Элементы: chorus3 — female backing on top
  200 [code      ]         has_female = ("chorus3" in name) or (vrole.endswith("female"))
  201 [code      ]         has_808 = energy > 0.5 and (
  202 [code      ]             "phonk" in genre or "trap" in genre or "hip-hop" in genre
  203 [code      ]         )
  204 [code      ]         has_lead = energy > 0.5
  205 [blank     ] 
  206 [comment   ]         # FX
  207 [code      ]         fx = []
  208 [code      ]         prev_name = sections[-1]["name"] if sections else None
  209 [branch    ]         if name.startswith(("chorus", "drop")) and (prev_name or "").startswith(
  210 [code      ]             ("prechorus", "build", "bridge", "verse")
  211 [code      ]         ):
  212 [code      ]             fx.append("riser")
  213 [code      ]             fx.append("silence_50ms_before_drop")
  214 [branch    ]         if name.startswith(("outro", "break")):
  215 [code      ]             fx.append("downlifter")
  216 [blank     ] 
  217 [comment   ]         # Fill перед chorus/drop
  218 [code      ]         fill_before = name.startswith(("chorus", "drop"))
  219 [blank     ] 
  220 [comment   ]         # Плотность hi-hat
  221 [code      ]         hh_density_mul = 1.0 if energy > 0.7 else (0.6 if energy > 0.4 else 0.3)
  222 [blank     ] 
  223 [code      ]         sections.append(
  224 [code      ]             {
  225 [code      ]                 "index": i,
  226 [code      ]                 "name": name,
  227 [code      ]                 "bars": bars,
  228 [code      ]                 "start_sec": round(t_cursor, 2),
  229 [code      ]                 "end_sec": round(t_cursor + dur, 2),
  230 [code      ]                 "duration_sec": round(dur, 2),
  231 [code      ]                 "energy": round(float(energy), 3),
  232 [code      ]                 "vocal_role": vrole,
  233 [code      ]                 "kick_pattern": kick_key,
  234 [code      ]                 "snare_pattern": snare_key,
  235 [code      ]                 "hihat_pattern": hh_key,
  236 [code      ]                 "hihat_density": round(hh_density_mul, 2),
  237 [code      ]                 "has_808": has_808,
  238 [code      ]                 "has_lead": has_lead,
  239 [code      ]                 "has_pad": energy < 0.6,
  240 [code      ]                 "has_female_backing": has_female,
  241 [code      ]                 "fill_before": fill_before,
  242 [code      ]                 "fx": fx,
  243 [code      ]             }
  244 [code      ]         )
  245 [code      ]         t_cursor += dur
  246 [blank     ] 
  247 [comment   ]     # TikTok hook = самая громкая chorus секция + 25 сек оттуда
  248 [code      ]     hot_sections = sorted(
  249 [code      ]         [s for s in sections if s["name"].startswith(("chorus", "drop"))],
  250 [code      ]         key=lambda s: s["energy"],
  251 [code      ]         reverse=True,
  252 [code      ]     )
  253 [branch    ]     if hot_sections:
  254 [code      ]         target = hot_sections[0]
  255 [code      ]         tt_start = target["start_sec"]
  256 [code      ]         tt_end = min(t_cursor, tt_start + 25.0)
  257 [branch    ]     else:
  258 [code      ]         tt_start, tt_end = 0.0, min(25.0, t_cursor)
  259 [blank     ] 
  260 [code      ]     plan = {
  261 [code      ]         "ok": True,
  262 [code      ]         "bpm": round(bpm, 2),
  263 [code      ]         "key": key,
  264 [code      ]         "mode": mode,
  265 [code      ]         "genre": genre,
  266 [code      ]         "mood": mood,
  267 [code      ]         "total_sec": round(t_cursor, 2),
  268 [code      ]         "requested_sec": round(total_seconds, 2),
  269 [code      ]         "variant": variant,
  270 [code      ]         "sections": sections,
  271 [code      ]         "tiktok_hook": {
  272 [code      ]             "start_sec": round(tt_start, 2),
  273 [code      ]             "end_sec": round(tt_end, 2),
  274 [code      ]         },
  275 [code      ]         "drums": {
  276 [code      ]             "kick": {"pattern_key": kick_key, "steps": kick},
  277 [code      ]             "snare": {"pattern_key": snare_key, "steps": snare},
  278 [code      ]             "hihat": {"pattern_key": hh_key, "steps": hh},
  279 [code      ]         },
  280 [code      ]         "hit_targets": hit_targets
  281 [code      ]         or {
  282 [code      ]             "lufs": -9.0,
  283 [code      ]             "chorus_gain_db_over_verse": 3.0,
  284 [code      ]             "stereo_corr": 0.75,
  285 [code      ]         },
  286 [code      ]         "seed": seed,
  287 [code      ]         "ts": time.time(),
  288 [code      ]     }
  289 [return    ]     return plan
  290 [blank     ] 
  291 [blank     ] 
  292 [def       ] def _guess_genre(sv: dict) -> str:
  293 [code      ]     bpm = sv.get("bpm", 130.0)
  294 [branch    ]     if 130 <= bpm <= 145:
  295 [return    ]         return "phonk / drift"
  296 [branch    ]     if 120 <= bpm < 130:
  297 [return    ]         return "dance / edm"
  298 [branch    ]     if 70 <= bpm <= 100:
  299 [return    ]         return "trap / hip-hop"
  300 [branch    ]     if 95 <= bpm < 120:
  301 [return    ]         return "pop / r&b"
  302 [branch    ]     if bpm > 150:
  303 [return    ]         return "hardstyle / techno"
  304 [return    ]     return "generic hit"
  305 [blank     ] 
  306 [blank     ] 
  307 [def       ] def save_plan(plan: dict, out_path: str) -> str:
  308 [code      ]     Path(out_path).parent.mkdir(parents=True, exist_ok=True)
  309 [code      ]     Path(out_path).write_text(
  310 [code      ]         json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
  311 [code      ]     )
  312 [return    ]     return out_path
  313 [blank     ] 
  314 [blank     ] 
  315 [comment   ] # ============================================================ CLI
  316 [branch    ] if __name__ == "__main__":
  317 [code      ]     sv = {
  318 [code      ]         "bpm": 132,
  319 [code      ]         "key": "F",
  320 [code      ]         "mode": "minor",
  321 [code      ]         "genre_hint": "phonk / drift",
  322 [code      ]         "mood": "energetic / driving",
  323 [code      ]     }
  324 [code      ]     p = build_arrangement(sv, total_seconds=180, seed=42, variant=1)
  325 [code      ]     print(json.dumps(p, ensure_ascii=False, indent=2)[:3000])
```