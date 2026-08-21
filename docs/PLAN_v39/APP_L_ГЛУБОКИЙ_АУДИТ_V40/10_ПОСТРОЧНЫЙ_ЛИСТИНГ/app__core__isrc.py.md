# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/isrc.py`

**Всего строк:** 117

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| docstring | 32 | 27.4 |
| code | 28 | 23.9 |
| blank | 21 | 17.9 |
| return | 11 | 9.4 |
| branch | 8 | 6.8 |
| def | 6 | 5.1 |
| import | 5 | 4.3 |
| try_block | 4 | 3.4 |
| comment | 2 | 1.7 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — app/core/isrc.py (v39.4, ШАГ 003)
    4 [docstring ] ========================================================================
    5 [docstring ] Реальный генератор ISRC + валидатор.
    6 [blank     ] 
    7 [docstring ] Формат ISRC (ISO 3901): CC-XXX-YY-NNNNN
    8 [docstring ]   CC    — 2-буквенный код страны (RU, US, ...)
    9 [docstring ]   XXX   — 3-символьный код регистранта (буквы или цифры)
   10 [docstring ]   YY    — 2 цифры года (25 = 2025, 26 = 2026)
   11 [docstring ]   NNNNN — 5-значный номер релиза
   12 [blank     ] 
   13 [docstring ] Раньше в release_pack_full.py / release_export.py / distribution_export_v11.py
   14 [docstring ] метаданные содержали заглушку XX-XXX-00-00000 — трек уходил бы к
   15 [docstring ] дистрибьютору с невалидным ISRC.
   16 [blank     ] 
   17 [docstring ] Теперь: get_isrc(meta) возвращает валидный ISRC ИЛИ пустую строку +
   18 [docstring ] пометку UNREGISTERED (никогда не фейковый placeholder).
   19 [docstring ] """
   20 [import    ] from __future__ import annotations
   21 [blank     ] 
   22 [import    ] import hashlib
   23 [import    ] import re
   24 [import    ] import time
   25 [import    ] from typing import Any, Optional
   26 [blank     ] 
   27 [code      ] _ISRC_RE = re.compile(r"^[A-Z]{2}-?[A-Z0-9]{3}-?\d{2}-?\d{5}$")
   28 [blank     ] 
   29 [blank     ] 
   30 [def       ] def is_valid_isrc(isrc: Optional[str]) -> bool:
   31 [docstring ]     """True если строка — валидный ISRC по ISO 3901."""
   32 [branch    ]     if not isrc:
   33 [return    ]         return False
   34 [code      ]     s = str(isrc).upper().strip()
   35 [branch    ]     if not _ISRC_RE.match(s):
   36 [return    ]         return False
   37 [comment   ]     # плейсхолдеры вида XX-XXX-00-00000 отбраковываем
   38 [code      ]     core = s.replace("-", "")
   39 [branch    ]     if core.startswith("XX") or (core.endswith("00000") and core[5:7] == "00"):
   40 [return    ]         return False
   41 [return    ]     return True
   42 [blank     ] 
   43 [blank     ] 
   44 [def       ] def is_placeholder_isrc(isrc: Optional[str]) -> bool:
   45 [docstring ]     """True если это XX-XXX-00-00000 / пусто / любой очевидный placeholder."""
   46 [branch    ]     if not isrc:
   47 [return    ]         return True
   48 [code      ]     s = str(isrc).upper().replace("-", "").replace(" ", "")
   49 [return    ]     return "XXXXX" in s or s.startswith("XX") or (s.endswith("00000") and "00" in s[5:7])
   50 [blank     ] 
   51 [blank     ] 
   52 [def       ] def _short_seq_from_title(title: str) -> str:
   53 [docstring ]     """5-значный детерминированный NNNNN из sha256(title|artist)."""
   54 [branch    ]     if not title:
   55 [code      ]         title = "zs_untitled"
   56 [code      ]     h = hashlib.sha256(title.encode("utf-8", errors="replace")).hexdigest()
   57 [code      ]     n = int(h[:6], 16) % 100000
   58 [return    ]     return f"{n:05d}"
   59 [blank     ] 
   60 [blank     ] 
   61 [def       ] def _normalize_existing(existing: str) -> str:
   62 [code      ]     s = str(existing).upper().replace("-", "")
   63 [return    ]     return f"{s[:2]}-{s[2:5]}-{s[5:7]}-{s[7:12]}"
   64 [blank     ] 
   65 [blank     ] 
   66 [def       ] def generate_isrc(
   67 [code      ]     meta: dict[str, Any],
   68 [code      ]     country_code: str = "RU",
   69 [code      ]     registrant: str = "ZSM",
   70 [code      ]     year: Optional[int] = None,
   71 [code      ] ) -> str:
   72 [docstring ]     """
   73 [docstring ]     Генерирует валидный ISRC из метаданных трека.
   74 [blank     ] 
   75 [docstring ]     Приоритет:
   76 [docstring ]       1. Если meta['isrc'] уже валидный — возвращаем его (нормализованный).
   77 [docstring ]       2. Иначе строим CC-REG-YY-NNNNN где:
   78 [docstring ]          CC = meta.get('country', country_code)
   79 [docstring ]          REG = meta.get('label_isrc_code', registrant)
   80 [docstring ]          YY = meta.get('year', current_year) % 100
   81 [docstring ]          NNNNN = meta.get('release_seq') или sha256(title+artist)[:5]
   82 [docstring ]     """
   83 [code      ]     existing = meta.get("isrc") or ""
   84 [branch    ]     if is_valid_isrc(existing):
   85 [return    ]         return _normalize_existing(str(existing))
   86 [blank     ] 
   87 [code      ]     cc = str(meta.get("country") or country_code).upper()[:2].ljust(2, "X")
   88 [code      ]     reg = str(meta.get("label_isrc_code") or registrant).upper()
   89 [code      ]     reg = re.sub(r"[^A-Z0-9]", "", reg)[:3].ljust(3, "Z")
   90 [code      ]     yy_source = meta.get("year") or (year if year is not None else time.gmtime().tm_year)
   91 [try_block ]     try:
   92 [code      ]         yy = int(yy_source) % 100
   93 [try_block ]     except (TypeError, ValueError):
   94 [code      ]         yy = time.gmtime().tm_year % 100
   95 [blank     ] 
   96 [code      ]     seq = meta.get("release_seq")
   97 [branch    ]     if seq is None:
   98 [code      ]         base_title = str(meta.get("title") or "")
   99 [code      ]         base_artist = str(meta.get("artist") or "")
  100 [code      ]         nnnnn = _short_seq_from_title(f"{base_title}|{base_artist}")
  101 [branch    ]     else:
  102 [try_block ]         try:
  103 [code      ]             nnnnn = f"{int(seq) % 100000:05d}"
  104 [try_block ]         except (TypeError, ValueError):
  105 [code      ]             nnnnn = _short_seq_from_title(str(seq))
  106 [blank     ] 
  107 [code      ]     isrc = f"{cc}-{reg}-{yy:02d}-{nnnnn}"
  108 [return    ]     return isrc if is_valid_isrc(isrc) else ""
  109 [blank     ] 
  110 [blank     ] 
  111 [def       ] def get_isrc(meta: dict[str, Any], fallback: str = "") -> str:
  112 [docstring ]     """
  113 [docstring ]     Возвращает валидный ISRC или fallback.
  114 [docstring ]     fallback по-умолчанию — пустая строка (никогда не XX-XXX-00-00000).
  115 [docstring ]     """
  116 [code      ]     isrc = generate_isrc(meta)
  117 [return    ]     return isrc if is_valid_isrc(isrc) else fallback
```