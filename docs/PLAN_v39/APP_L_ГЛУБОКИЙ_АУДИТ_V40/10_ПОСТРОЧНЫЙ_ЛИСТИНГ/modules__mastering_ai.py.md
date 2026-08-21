# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/mastering_ai.py`

**Всего строк:** 34

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 14 | 41.2 |
| import | 5 | 14.7 |
| try_block | 4 | 11.8 |
| return | 3 | 8.8 |
| blank | 2 | 5.9 |
| branch | 2 | 5.9 |
| comment | 1 | 2.9 |
| docstring | 1 | 2.9 |
| def | 1 | 2.9 |
| stmt | 1 | 2.9 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - modules/mastering_ai.py (v38): matchering -> mastering_pro."""
    3 [import    ] from __future__ import annotations
    4 [import    ] from pathlib import Path
    5 [import    ] from typing import Any, Dict, Optional
    6 [import    ] from app.ai.registry import registry
    7 [blank     ] 
    8 [blank     ] 
    9 [def       ] def master_ai(input_wav: str, out_wav: str, reference_wav: Optional[str] = None,
   10 [code      ]               target_lufs: float = -9.0) -> Dict[str, Any]:
   11 [code      ]     Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
   12 [code      ]     fallback_reason = ""
   13 [branch    ]     if reference_wav and registry.is_available("mastering_ai"):
   14 [try_block ]         try:
   15 [stmt      ]             with registry.use("mastering_ai") as m:
   16 [code      ]                 mg = m.handle
   17 [code      ]                 mg.process(target=input_wav, reference=reference_wav,
   18 [code      ]                            results=[mg.pcm16(out_wav)])
   19 [return    ]             return {"ok": True, "engine": "matchering",
   20 [code      ]                     "reference": reference_wav, "path": out_wav}
   21 [try_block ]         except Exception as e:
   22 [code      ]             fallback_reason = str(e)
   23 [branch    ]     else:
   24 [code      ]         fallback_reason = "no reference" if not reference_wav else "matchering unavailable"
   25 [try_block ]     try:
   26 [import    ]         from modules import mastering_pro
   27 [code      ]         res = mastering_pro.process_mastering(input_wav, out_wav,
   28 [code      ]                                               vocal_path=None, target_lufs=target_lufs)
   29 [code      ]         res = res if isinstance(res, dict) else {"ok": True, "path": out_wav}
   30 [code      ]         res["engine"] = "mastering_pro"
   31 [code      ]         res["fallback_reason"] = fallback_reason
   32 [return    ]         return res
   33 [try_block ]     except Exception as e:
   34 [return    ]         return {"ok": False, "reason": f"mastering failed: {e}"}
```