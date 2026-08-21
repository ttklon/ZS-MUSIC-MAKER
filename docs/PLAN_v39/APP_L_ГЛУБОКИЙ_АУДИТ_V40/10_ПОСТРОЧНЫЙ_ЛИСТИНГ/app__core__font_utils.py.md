# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/font_utils.py`

**Всего строк:** 120

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 39 | 32.5 |
| docstring | 22 | 18.3 |
| blank | 13 | 10.8 |
| try_block | 9 | 7.5 |
| branch | 8 | 6.7 |
| return | 8 | 6.7 |
| comment | 6 | 5.0 |
| import | 6 | 5.0 |
| def | 4 | 3.3 |
| loop | 4 | 3.3 |
| raise | 1 | 0.8 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — app/core/font_utils.py (v39.4, ШАГ 002)
    4 [docstring ] ========================================================================
    5 [docstring ] Единый источник TTF-fallback для PIL. Раньше пути к шрифтам были жёстко
    6 [docstring ] зашиты в трёх местах (cover_art_gen, video_edit_v11, cover_gen) с
    7 [docstring ] C:\\Windows\\Fonts\\arialbd.ttf — на Linux всё падало на fallback default.
    8 [blank     ] 
    9 [docstring ] Теперь: единый список кандидатов (Linux/macOS/Windows) + опциональный
   10 [docstring ] override через ZSMM_FONT_PATH / config/fonts.txt. Никаких hardcoded
   11 [docstring ] C:\\ и /home/ubuntu в production-коде.
   12 [docstring ] """
   13 [import    ] from __future__ import annotations
   14 [blank     ] 
   15 [import    ] import os
   16 [import    ] import sys
   17 [import    ] from pathlib import Path
   18 [import    ] from typing import Iterable, Optional
   19 [blank     ] 
   20 [code      ] _ROOT = Path(__file__).resolve().parents[2]
   21 [blank     ] 
   22 [blank     ] 
   23 [def       ] def _config_font_candidates() -> Iterable[str]:
   24 [docstring ]     """Читает config/fonts.txt если есть — по одному пути на строку."""
   25 [code      ]     cfg = _ROOT / "config" / "fonts.txt"
   26 [branch    ]     if not cfg.exists():
   27 [return    ]         return []
   28 [try_block ]     try:
   29 [return    ]         return [
   30 [code      ]             line.strip()
   31 [loop      ]             for line in cfg.read_text(encoding="utf-8").splitlines()
   32 [branch    ]             if line.strip() and not line.strip().startswith("#")
   33 [code      ]         ]
   34 [try_block ]     except OSError as e:  # noqa: BLE001 — сообщаем причину и работаем без конфига
   35 [code      ]         print(f"[font_utils] cannot read {cfg}: {e}", file=sys.stderr)
   36 [return    ]         return []
   37 [blank     ] 
   38 [blank     ] 
   39 [def       ] def font_candidates(bold: bool = True) -> list[str]:
   40 [docstring ]     """
   41 [docstring ]     Возвращает упорядоченный список кандидатов TTF: env → config → OS-defaults.
   42 [docstring ]     Пути к системным шрифтам — только через os.path.join / стандартные
   43 [docstring ]     OS-локации, ничего hardcoded под конкретную машину пользователя.
   44 [docstring ]     """
   45 [code      ]     env = os.environ.get("ZSMM_FONT_PATH", "").strip()
   46 [code      ]     result: list[str] = []
   47 [branch    ]     if env:
   48 [code      ]         result.append(env)
   49 [code      ]     result.extend(_config_font_candidates())
   50 [comment   ]     # Linux
   51 [code      ]     linux_bold = [
   52 [code      ]         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
   53 [code      ]         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
   54 [code      ]         "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
   55 [code      ]         "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
   56 [code      ]     ]
   57 [code      ]     linux_reg = [
   58 [code      ]         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
   59 [code      ]         "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
   60 [code      ]     ]
   61 [comment   ]     # macOS
   62 [code      ]     mac_bold = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial Bold.ttf"]
   63 [comment   ]     # Windows — вычисляем от %WINDIR% (не hardcoded в код)
   64 [code      ]     win_bold: list[str] = []
   65 [code      ]     win_reg: list[str] = []
   66 [code      ]     windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
   67 [branch    ]     if windir:
   68 [code      ]         fonts = os.path.join(windir, "Fonts")
   69 [code      ]         win_bold = [os.path.join(fonts, "arialbd.ttf"), os.path.join(fonts, "Arial Bold.ttf")]
   70 [code      ]         win_reg = [os.path.join(fonts, "arial.ttf")]
   71 [blank     ] 
   72 [comment   ]     # PIL / bundled name fallback (PIL сам ищет в системных путях)
   73 [code      ]     named = ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]
   74 [blank     ] 
   75 [branch    ]     if bold:
   76 [code      ]         result += linux_bold + mac_bold + win_bold + named
   77 [branch    ]     else:
   78 [code      ]         result += linux_reg + [
   79 [code      ]             "/System/Library/Fonts/Helvetica.ttc",
   80 [code      ]         ] + win_reg + ["arial.ttf", "DejaVuSans.ttf"]
   81 [comment   ]     # dedup preserve order
   82 [code      ]     seen: set[str] = set()
   83 [code      ]     uniq: list[str] = []
   84 [loop      ]     for p in result:
   85 [branch    ]         if p and p not in seen:
   86 [code      ]             seen.add(p)
   87 [code      ]             uniq.append(p)
   88 [return    ]     return uniq
   89 [blank     ] 
   90 [blank     ] 
   91 [def       ] def load_pil_font(size: int, bold: bool = True):
   92 [docstring ]     """
   93 [docstring ]     Возвращает PIL ImageFont: пробует all-candidates, честно логирует
   94 [docstring ]     неожиданные ошибки в stderr, штатное отсутствие шрифта — тихо.
   95 [docstring ]     Никогда не бросает — на самый крайний случай возвращает load_default().
   96 [docstring ]     """
   97 [try_block ]     try:
   98 [import    ]         from PIL import ImageFont
   99 [try_block ]     except ImportError as e:
  100 [raise     ]         raise RuntimeError(f"Pillow (PIL) не установлен: {e}") from e
  101 [loop      ]     for cand in font_candidates(bold=bold):
  102 [try_block ]         try:
  103 [return    ]             return ImageFont.truetype(cand, size)
  104 [try_block ]         except OSError:
  105 [code      ]             continue  # штатное отсутствие
  106 [try_block ]         except Exception as e:  # noqa: BLE001
  107 [code      ]             print(f"[font_utils] TTF load error {cand}: {e}", file=sys.stderr)
  108 [code      ]             continue
  109 [return    ]     return ImageFont.load_default()
  110 [blank     ] 
  111 [blank     ] 
  112 [def       ] def first_available_font_path(bold: bool = True) -> Optional[str]:
  113 [docstring ]     """Возвращает первый существующий путь из кандидатов или None."""
  114 [loop      ]     for cand in font_candidates(bold=bold):
  115 [try_block ]         try:
  116 [branch    ]             if cand and os.path.exists(cand):
  117 [return    ]                 return cand
  118 [try_block ]         except OSError:
  119 [code      ]             continue
  120 [return    ]     return None
```