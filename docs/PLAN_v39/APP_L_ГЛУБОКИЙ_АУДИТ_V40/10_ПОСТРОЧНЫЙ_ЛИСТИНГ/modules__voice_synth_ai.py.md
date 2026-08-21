# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/voice_synth_ai.py`

**Всего строк:** 40

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 17 | 42.5 |
| branch | 5 | 12.5 |
| import | 4 | 10.0 |
| try_block | 4 | 10.0 |
| return | 3 | 7.5 |
| blank | 2 | 5.0 |
| stmt | 2 | 5.0 |
| comment | 1 | 2.5 |
| docstring | 1 | 2.5 |
| def | 1 | 2.5 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - modules/voice_synth_ai.py (v38): XTTS-v2 -> RVC."""
    3 [import    ] from __future__ import annotations
    4 [import    ] from pathlib import Path
    5 [import    ] from typing import Any, Dict, Optional
    6 [import    ] from app.ai.registry import registry
    7 [blank     ] 
    8 [blank     ] 
    9 [def       ] def synth_vocal_ai(text: str, out_path: str, speaker_wav: Optional[str] = None,
   10 [code      ]                    language: str = "ru", rvc_model: Optional[str] = None) -> Dict[str, Any]:
   11 [branch    ]     if not text or not text.strip():
   12 [return    ]         return {"ok": False, "reason": "empty text"}
   13 [code      ]     Path(out_path).parent.mkdir(parents=True, exist_ok=True)
   14 [branch    ]     if not registry.is_available("tts_vocal"):
   15 [return    ]         return {"ok": False, "reason": "tts_vocal unavailable - install TTS (Coqui)"}
   16 [stmt      ]     with registry.use("tts_vocal") as m:
   17 [code      ]         tts = m.handle
   18 [code      ]         kwargs = dict(text=text, file_path=out_path, language=language)
   19 [branch    ]         if speaker_wav and Path(speaker_wav).exists():
   20 [code      ]             kwargs["speaker_wav"] = speaker_wav
   21 [code      ]         tts.tts_to_file(**kwargs)
   22 [code      ]     result = {"ok": True, "engine": "xtts_v2", "vocal_path": out_path,
   23 [code      ]               "sample_rate": 24000, "rvc_applied": False}
   24 [branch    ]     if rvc_model and registry.is_available("vocal_rvc"):
   25 [try_block ]         try:
   26 [stmt      ]             with registry.use("vocal_rvc") as m:
   27 [code      ]                 conv = out_path.replace(".wav", f"_rvc_{Path(rvc_model).stem}.wav")
   28 [code      ]                 ok = False
   29 [try_block ]                 try:
   30 [code      ]                     ok = m.handle.convert(input_path=out_path, output_path=conv,
   31 [code      ]                                           model_path=rvc_model)
   32 [try_block ]                 except Exception:
   33 [code      ]                     ok = False
   34 [branch    ]                 if ok and Path(conv).exists():
   35 [code      ]                     result["vocal_path"] = conv
   36 [code      ]                     result["rvc_applied"] = True
   37 [code      ]                     result["rvc_model"] = rvc_model
   38 [try_block ]         except Exception as e:
   39 [code      ]             result["rvc_error"] = str(e)
   40 [return    ]     return result
```