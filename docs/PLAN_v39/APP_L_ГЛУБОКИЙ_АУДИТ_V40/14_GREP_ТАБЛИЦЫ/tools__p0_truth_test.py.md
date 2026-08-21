# grep-таблицы `tools/p0_truth_test.py`

## `import` — 8 совпадений
```
    1 | import struct
    2 | import sys
    3 | import tempfile
    4 | import wave
    5 | from pathlib import Path
   26 |     from modules import matchering_master, rvc_manager
   36 |     from app.core import musicgen_texture
   40 |     from modules import master_pipeline_v12
```

## `print` — 5 совпадений
```
   30 |         print("RVC_FAIL: fallback still active")
   32 |         print("RVC_HONEST_FAIL_PASS:", e)
   35 |     print("MASTER_RESULT:", r)
   39 |     print("MUSICGEN_RESULT:", m)
   43 |     print("PIPELINE_API:", x.get("verdict"), x.get("percent_ready"))
```

## `except` — 1 совпадений
```
   31 |     except RuntimeError as e:
```

## `try` — 1 совпадений
```
   28 |     try:
```

## `def` — 1 совпадений
```
   15 | def wav(path):
```

## `if` — 1 совпадений
```
   11 | if str(_ROOT) not in sys.path:
```

## `with` — 2 совпадений
```
   16 |     with wave.open(str(path), "wb") as w:
   23 | with tempfile.TemporaryDirectory() as d:
```

## `open` — 1 совпадений
```
   16 |     with wave.open(str(path), "wb") as w:
```
