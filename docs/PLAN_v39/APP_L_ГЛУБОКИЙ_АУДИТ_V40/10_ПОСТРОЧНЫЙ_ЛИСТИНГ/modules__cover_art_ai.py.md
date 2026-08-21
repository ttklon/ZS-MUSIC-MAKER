# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/cover_art_ai.py`

**Всего строк:** 32

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 11 | 34.4 |
| import | 6 | 18.8 |
| try_block | 4 | 12.5 |
| return | 4 | 12.5 |
| blank | 2 | 6.2 |
| comment | 1 | 3.1 |
| docstring | 1 | 3.1 |
| def | 1 | 3.1 |
| branch | 1 | 3.1 |
| stmt | 1 | 3.1 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - modules/cover_art_ai.py (v38, SDXL Base 1.0 fp16)."""
    3 [import    ] from __future__ import annotations
    4 [import    ] from pathlib import Path
    5 [import    ] from typing import Any, Dict
    6 [import    ] from app.ai.registry import registry
    7 [import    ] from app.ai import prompts as P
    8 [blank     ] 
    9 [blank     ] 
   10 [def       ] def render_cover_ai(title: str, artist: str, genre: str, mood: str,
   11 [code      ]                     out_path: str, size: int = 1024) -> Dict[str, Any]:
   12 [code      ]     prompt = P.build_cover_prompt(title, artist, genre, mood)
   13 [code      ]     Path(out_path).parent.mkdir(parents=True, exist_ok=True)
   14 [branch    ]     if not registry.is_available("cover_art"):
   15 [try_block ]         try:
   16 [import    ]             from modules import cover_art_gen
   17 [code      ]             res = cover_art_gen.generate(title=title, artist=artist,
   18 [code      ]                                          out_path=out_path, style="gradient")
   19 [code      ]             res["engine"] = "PIL_fallback"
   20 [return    ]             return res
   21 [try_block ]         except Exception as e:
   22 [return    ]             return {"ok": False, "reason": f"no cover engine: {e}"}
   23 [stmt      ]     with registry.use("cover_art") as m:
   24 [code      ]         pipe = m.handle
   25 [try_block ]         try:
   26 [code      ]             image = pipe(prompt=prompt, num_inference_steps=30,
   27 [code      ]                          guidance_scale=7.0, width=size, height=size).images[0]
   28 [code      ]             image.save(out_path)
   29 [return    ]             return {"ok": True, "engine": "sdxl-base-1.0", "path": out_path,
   30 [code      ]                     "prompt": prompt}
   31 [try_block ]         except Exception as e:
   32 [return    ]             return {"ok": False, "reason": str(e), "engine": "sdxl-base-1.0"}
```