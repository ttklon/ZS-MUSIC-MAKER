# grep-таблицы `app/hw_probe.py`

## `import` — 7 совпадений
```
    3 | from __future__ import annotations
    5 | import json
    6 | import platform
    7 | from dataclasses import asdict, dataclass
   23 |         import psutil
   32 |         import torch
   46 |             import torch_directml as dml
```

## `print` — 1 совпадений
```
   61 |     print(json.dumps(asdict(probe()), ensure_ascii=False, indent=2))
```

## `except` — 3 совпадений
```
   26 |     except Exception:
   40 |     except Exception:
   53 |         except Exception:
```

## `try` — 3 совпадений
```
   22 |     try:
   31 |     try:
   45 |         try:
```

## `def` — 2 совпадений
```
   21 | def probe() -> HW:
   60 | def main():
```

## `class` — 1 совпадений
```
   11 | class HW:
```

## `return` — 1 совпадений
```
   57 |     return hw
```

## `if` — 3 совпадений
```
   34 |         if torch.cuda.is_available():
   44 |     if hw.backend == "cpu":
   64 | if __name__ == "__main__":
```
