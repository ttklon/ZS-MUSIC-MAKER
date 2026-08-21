# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/lyrics_gen_ai.py`

**Всего строк:** 57

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 34 | 59.6 |
| import | 8 | 14.0 |
| branch | 4 | 7.0 |
| blank | 3 | 5.3 |
| return | 3 | 5.3 |
| stmt | 2 | 3.5 |
| comment | 1 | 1.8 |
| docstring | 1 | 1.8 |
| def | 1 | 1.8 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - modules/lyrics_gen_ai.py (v38 AI-first)"""
    3 [import    ] from __future__ import annotations
    4 [import    ] import json, re, time
    5 [import    ] from pathlib import Path
    6 [import    ] from typing import Any, Dict
    7 [import    ] from app.ai.registry import registry
    8 [import    ] from app.ai import prompts as P
    9 [import    ] from app.ai import llm_service as LLM
   10 [import    ] from modules.artist_dossier import DossierManager
   11 [blank     ] 
   12 [code      ] ROOT = Path(__file__).resolve().parents[1]
   13 [code      ] VAULT = ROOT / "lyric_vault"
   14 [code      ] MEMORY = VAULT / "lyrics_memory.jsonl"
   15 [blank     ] 
   16 [blank     ] 
   17 [def       ] def generate_lyrics_ai(theme, style_vector=None, n_verses=2, user_lyrics_lines=None,
   18 [code      ]                        bilingual=True, artist_slug=None, track_id=None,
   19 [code      ]                        genre="phonk") -> Dict[str, Any]:
   20 [code      ]     style_vector = style_vector or {}
   21 [code      ]     user_lyrics_lines = [l.strip() for l in (user_lyrics_lines or []) if l.strip()]
   22 [code      ]     bpm = int(style_vector.get("target_bpm") or 140)
   23 [code      ]     art_dos = trk_dos = None
   24 [branch    ]     if artist_slug:
   25 [code      ]         mgr = DossierManager()
   26 [code      ]         art_dos = mgr.get_artist_dossier(artist_slug)
   27 [code      ]         trk_dos = mgr.get_track_dossier(artist_slug, track_id) if track_id else None
   28 [code      ]     prompt = P.build_lyrics_prompt(theme=theme, genre=genre, bpm=bpm,
   29 [code      ]                                    n_verses=n_verses, bilingual=bilingual,
   30 [code      ]                                    user_lines=user_lyrics_lines,
   31 [code      ]                                    artist_dossier=art_dos, track_reference=trk_dos)
   32 [branch    ]     if not registry.is_available("lyrics_llm"):
   33 [return    ]         return {"ok": False, "lyrics": "",
   34 [code      ]                 "reason": "lyrics_llm unavailable - run tools/pull_ai_models.py --model lyrics_llm",
   35 [code      ]                 "source": "BLOCKED"}
   36 [stmt      ]     with registry.use("lyrics_llm") as m:
   37 [code      ]         text = LLM.complete(m.handle, P.SYSTEM_LYRICS, prompt,
   38 [code      ]                             max_tokens=1400, temperature=0.9, top_p=0.95,
   39 [code      ]                             repeat_penalty=1.15)
   40 [branch    ]     if not text or len(text) < 60:
   41 [return    ]         return {"ok": False, "lyrics": text or "", "reason": "empty LLM output",
   42 [code      ]                 "source": "lyrics_llm"}
   43 [code      ]     text = re.sub(r"^```.*?$", "", text, flags=re.MULTILINE).strip()
   44 [code      ]     lo = text.lower()
   45 [code      ]     missing = [ln for ln in user_lyrics_lines if ln.lower() not in lo]
   46 [branch    ]     if missing:
   47 [code      ]         text = text.rstrip() + "\n\n[User]\n" + "\n".join(missing)
   48 [code      ]     VAULT.mkdir(parents=True, exist_ok=True)
   49 [stmt      ]     with open(MEMORY, "a", encoding="utf-8") as f:
   50 [code      ]         f.write(json.dumps({"theme": theme, "bpm": bpm, "lyrics": text,
   51 [code      ]                             "source": "lyrics_llm", "artist_slug": artist_slug,
   52 [code      ]                             "track_id": track_id, "timestamp": time.time()},
   53 [code      ]                            ensure_ascii=False) + "\n")
   54 [return    ]     return {"ok": True, "lyrics": text, "source": "lyrics_llm",
   55 [code      ]             "bilingual": bilingual, "n_verses": n_verses, "bpm": bpm,
   56 [code      ]             "artist_slug": artist_slug, "track_id": track_id,
   57 [code      ]             "user_lines_included": all(l.lower() in text.lower() for l in user_lyrics_lines)}
```