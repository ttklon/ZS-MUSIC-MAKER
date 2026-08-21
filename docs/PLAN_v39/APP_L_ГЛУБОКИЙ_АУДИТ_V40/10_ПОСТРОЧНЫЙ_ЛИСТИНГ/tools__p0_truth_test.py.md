# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/p0_truth_test.py`

**Всего строк:** 43

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 18 | 41.9 |
| import | 8 | 18.6 |
| blank | 8 | 18.6 |
| comment | 3 | 7.0 |
| stmt | 2 | 4.7 |
| try_block | 2 | 4.7 |
| branch | 1 | 2.3 |
| def | 1 | 2.3 |

## Полный листинг с классификацией
```
    1 [import    ] import struct
    2 [import    ] import sys
    3 [import    ] import tempfile
    4 [import    ] import wave
    5 [import    ] from pathlib import Path
    6 [blank     ] 
    7 [comment   ] # FIX v16 (P0): при запуске «python3 tools/p0_truth_test.py» корень проекта
    8 [comment   ] # не попадает в sys.path — «from modules import ...» падал с
    9 [comment   ] # ModuleNotFoundError без PYTHONPATH. Гарантируем доступность корня.
   10 [code      ] _ROOT = Path(__file__).resolve().parents[1]
   11 [branch    ] if str(_ROOT) not in sys.path:
   12 [code      ]     sys.path.insert(0, str(_ROOT))
   13 [blank     ] 
   14 [blank     ] 
   15 [def       ] def wav(path):
   16 [stmt      ]     with wave.open(str(path), "wb") as w:
   17 [code      ]         w.setnchannels(1)
   18 [code      ]         w.setsampwidth(2)
   19 [code      ]         w.setframerate(8000)
   20 [code      ]         w.writeframes(struct.pack("<8000h", *([0] * 8000)))
   21 [blank     ] 
   22 [blank     ] 
   23 [stmt      ] with tempfile.TemporaryDirectory() as d:
   24 [code      ]     src = Path(d) / "in.wav"
   25 [code      ]     wav(src)
   26 [import    ]     from modules import matchering_master, rvc_manager
   27 [blank     ] 
   28 [try_block ]     try:
   29 [code      ]         rvc_manager.infer(str(src), voice_name="definitely_missing")
   30 [code      ]         print("RVC_FAIL: fallback still active")
   31 [try_block ]     except RuntimeError as e:
   32 [code      ]         print("RVC_HONEST_FAIL_PASS:", e)
   33 [code      ]     out = Path(d) / "master.wav"
   34 [code      ]     r = matchering_master.master_to_stand(str(src), str(out), "streaming")
   35 [code      ]     print("MASTER_RESULT:", r)
   36 [import    ]     from app.core import musicgen_texture
   37 [blank     ] 
   38 [code      ]     m = musicgen_texture.generate_texture("test", duration_sec=1, vram_gb=0.0)
   39 [code      ]     print("MUSICGEN_RESULT:", m)
   40 [import    ]     from modules import master_pipeline_v12
   41 [blank     ] 
   42 [code      ]     x = master_pipeline_v12.run("api_test", {"references": []}, dry_run=True)
   43 [code      ]     print("PIPELINE_API:", x.get("verdict"), x.get("percent_ready"))
```