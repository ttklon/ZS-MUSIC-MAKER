# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/license_manager.py`

**Всего строк:** 66

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 17 | 25.8 |
| return | 13 | 19.7 |
| blank | 11 | 16.7 |
| branch | 10 | 15.2 |
| docstring | 5 | 7.6 |
| def | 3 | 4.5 |
| comment | 3 | 4.5 |
| import | 2 | 3.0 |
| decorator | 1 | 1.5 |
| class | 1 | 1.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] License / Provenance Manager v6.
    3 [docstring ] Жёсткий фильтр CC0 / Royalty-Free / CC-BY по умолчанию.
    4 [docstring ] Всё остальное блокируется до подтверждения пользователем.
    5 [docstring ] """
    6 [blank     ] 
    7 [import    ] from __future__ import annotations
    8 [blank     ] 
    9 [import    ] from dataclasses import dataclass
   10 [blank     ] 
   11 [code      ] ALLOW_DEFAULT = {
   12 [code      ]     "cc0",
   13 [code      ]     "public domain",
   14 [code      ]     "royalty-free",
   15 [code      ]     "royalty free",
   16 [code      ]     "cc-by",
   17 [code      ]     "cc by",
   18 [code      ]     "creative commons 0",
   19 [code      ] }
   20 [code      ] NEEDS_ATTRIBUTION = {"cc-by", "cc by"}
   21 [code      ] BLOCK_UNLESS_CONFIRMED = {"cc-by-nc", "cc by-nc", "cc-by-sa", "unknown"}
   22 [blank     ] 
   23 [blank     ] 
   24 [decorator ] @dataclass
   25 [class     ] class LicenseCheck:
   26 [code      ]     ok: bool
   27 [code      ]     needs_attribution: bool
   28 [code      ]     reason: str
   29 [blank     ] 
   30 [blank     ] 
   31 [def       ] def normalize(lic: str) -> str:
   32 [code      ]     n = (lic or "").strip().lower().replace("_", " ")
   33 [comment   ]     # v34 FIX: лицензии часто приходят как URL (archive.org licenseurl,
   34 [comment   ]     # freesound API). Нормализуем URL → каноническое имя, иначе
   35 [comment   ]     # publicdomain-URL ошибочно попадал в «unknown» и блокировался.
   36 [branch    ]     if "/" in n or "creativecommons.org" in n or "licenses" in n:
   37 [branch    ]         if "publicdomain" in n or "public-domain" in n:
   38 [return    ]             return "public domain"
   39 [branch    ]         if "by-nc-sa" in n or "by-nc-nd" in n or "by-nc" in n:
   40 [return    ]             return "cc-by-nc"
   41 [branch    ]         if "by-sa" in n:
   42 [return    ]             return "cc-by-sa"
   43 [branch    ]         if n.rstrip("/").endswith("/by") or "/by/" in n:
   44 [return    ]             return "cc-by"
   45 [branch    ]         if "zero" in n or "cc0" in n:
   46 [return    ]             return "cc0"
   47 [return    ]         return "unknown"
   48 [return    ]     return n
   49 [blank     ] 
   50 [blank     ] 
   51 [def       ] def is_free_commercial(lic: str, allow_user_override: bool = False) -> bool:
   52 [code      ]     n = normalize(lic)
   53 [branch    ]     if n in ALLOW_DEFAULT:
   54 [return    ]         return True
   55 [branch    ]     if allow_user_override:
   56 [return    ]         return True
   57 [return    ]     return False
   58 [blank     ] 
   59 [blank     ] 
   60 [def       ] def check(lic: str, allow_user_override: bool = False) -> LicenseCheck:
   61 [code      ]     n = normalize(lic)
   62 [branch    ]     if n in ALLOW_DEFAULT:
   63 [return    ]         return LicenseCheck(True, n in NEEDS_ATTRIBUTION, "allowed")
   64 [branch    ]     if n in BLOCK_UNLESS_CONFIRMED:
   65 [return    ]         return LicenseCheck(allow_user_override, False, "requires user confirmation")
   66 [return    ]     return LicenseCheck(allow_user_override, False, f"unknown license: {lic}")
```