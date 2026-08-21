# grep-таблицы `app/core/font_utils.py`

## `import` — 6 совпадений
```
   13 | from __future__ import annotations
   15 | import os
   16 | import sys
   17 | from pathlib import Path
   18 | from typing import Iterable, Optional
   98 |         from PIL import ImageFont
```

## `print` — 2 совпадений
```
   35 |         print(f"[font_utils] cannot read {cfg}: {e}", file=sys.stderr)
  107 |             print(f"[font_utils] TTF load error {cand}: {e}", file=sys.stderr)
```

## `except` — 5 совпадений
```
   34 |     except OSError as e:  # noqa: BLE001 — сообщаем причину и работаем без конфига
   99 |     except ImportError as e:
  104 |         except OSError:
  106 |         except Exception as e:  # noqa: BLE001
  118 |         except OSError:
```

## `try` — 4 совпадений
```
   28 |     try:
   97 |     try:
  102 |         try:
  115 |         try:
```

## `def` — 4 совпадений
```
   23 | def _config_font_candidates() -> Iterable[str]:
   39 | def font_candidates(bold: bool = True) -> list[str]:
   91 | def load_pil_font(size: int, bold: bool = True):
  112 | def first_available_font_path(bold: bool = True) -> Optional[str]:
```

## `raise` — 1 совпадений
```
  100 |         raise RuntimeError(f"Pillow (PIL) не установлен: {e}") from e
```

## `return` — 8 совпадений
```
   27 |         return []
   29 |         return [
   36 |         return []
   88 |     return uniq
  103 |             return ImageFont.truetype(cand, size)
  109 |     return ImageFont.load_default()
  117 |                 return cand
  120 |     return None
```

## `if` — 7 совпадений
```
   26 |     if not cfg.exists():
   32 |             if line.strip() and not line.strip().startswith("#")
   47 |     if env:
   67 |     if windir:
   75 |     if bold:
   85 |         if p and p not in seen:
  116 |             if cand and os.path.exists(cand):
```

## `for` — 4 совпадений
```
   31 |             for line in cfg.read_text(encoding="utf-8").splitlines()
   84 |     for p in result:
  101 |     for cand in font_candidates(bold=bold):
  114 |     for cand in font_candidates(bold=bold):
```

## `path_C` — 2 совпадений
```
    7 | C:\\Windows\\Fonts\\arialbd.ttf — на Linux всё падало на fallback default.
   11 | C:\\ и /home/ubuntu в production-коде.
```

## `path_home` — 1 совпадений
```
   11 | C:\\ и /home/ubuntu в production-коде.
```
