# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/beat_gen_ai.py`

**Всего строк:** 52

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 26 | 50.0 |
| branch | 7 | 13.5 |
| import | 6 | 11.5 |
| try_block | 4 | 7.7 |
| blank | 2 | 3.8 |
| return | 2 | 3.8 |
| comment | 1 | 1.9 |
| docstring | 1 | 1.9 |
| def | 1 | 1.9 |
| stmt | 1 | 1.9 |
| loop | 1 | 1.9 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - modules/beat_gen_ai.py (v38, MusicGen-large, чанки 20с)."""
    3 [import    ] from __future__ import annotations
    4 [import    ] import math
    5 [import    ] from pathlib import Path
    6 [import    ] from typing import Any, Dict, Optional
    7 [import    ] from app.ai.registry import registry
    8 [blank     ] 
    9 [blank     ] 
   10 [def       ] def render_beat_ai(prompt: str, bpm: int = 140, duration_sec: int = 120,
   11 [code      ]                    out_path: str = "beat.wav", reference_wav: Optional[str] = None,
   12 [code      ]                    chunk_sec: int = 20) -> Dict[str, Any]:
   13 [branch    ]     if not registry.is_available("music_generation"):
   14 [return    ]         return {"ok": False, "reason": "music_generation unavailable - install audiocraft"}
   15 [import    ]     import numpy as np, soundfile as sf, torch
   16 [code      ]     Path(out_path).parent.mkdir(parents=True, exist_ok=True)
   17 [code      ]     n_chunks = max(1, math.ceil(duration_sec / chunk_sec))
   18 [stmt      ]     with registry.use("music_generation") as m:
   19 [code      ]         model = m.handle
   20 [try_block ]         try:
   21 [code      ]             model.set_generation_params(duration=min(chunk_sec, 30), top_k=250,
   22 [code      ]                                         top_p=0.0, temperature=1.0, cfg_coef=3.0)
   23 [try_block ]         except Exception:
   24 [code      ]             pass
   25 [code      ]         sr = getattr(model, "sample_rate", 32000)
   26 [code      ]         chunks = [model.generate([prompt], progress=False)[0].cpu().numpy()]
   27 [loop      ]         for i in range(1, n_chunks):
   28 [try_block ]             try:
   29 [code      ]                 prev_t = torch.from_numpy(chunks[-1]).unsqueeze(0)
   30 [branch    ]                 if any(p.is_cuda for p in model.lm.parameters()):
   31 [code      ]                     prev_t = prev_t.cuda()
   32 [code      ]                 cont = model.generate_continuation(prev_t, sr, [prompt], progress=False)[0]
   33 [code      ]                 chunks.append(cont.cpu().numpy())
   34 [try_block ]             except Exception:
   35 [code      ]                 chunks.append(model.generate([prompt], progress=False)[0].cpu().numpy())
   36 [code      ]     full = np.concatenate(chunks, axis=-1)
   37 [code      ]     total = int(duration_sec * sr)
   38 [branch    ]     if full.shape[-1] > total:
   39 [code      ]         full = full[..., :total]
   40 [branch    ]     if full.ndim == 1:
   41 [code      ]         full = np.stack([full, full], axis=-1)
   42 [branch    ]     else:
   43 [code      ]         full = full.T
   44 [branch    ]         if full.shape[1] == 1:
   45 [code      ]             full = np.concatenate([full, full], axis=1)
   46 [code      ]     peak = float(np.max(np.abs(full)) + 1e-9)
   47 [branch    ]     if peak > 0.99:
   48 [code      ]         full = full * (0.98 / peak)
   49 [code      ]     sf.write(out_path, full.astype("float32"), int(sr), subtype="PCM_16")
   50 [return    ]     return {"ok": True, "beat_path": out_path, "duration_sec": duration_sec,
   51 [code      ]             "sample_rate": int(sr), "bpm": bpm, "engine": "musicgen-large",
   52 [code      ]             "chunks": n_chunks}
```