# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_isrc.py`

**Всего строк:** 78

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| stmt | 25 | 32.1 |
| blank | 21 | 26.9 |
| code | 16 | 20.5 |
| def | 10 | 12.8 |
| comment | 3 | 3.8 |
| import | 2 | 2.6 |
| docstring | 1 | 1.3 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker — tests for app/core/isrc (ШАГ 003)."""
    3 [import    ] from __future__ import annotations
    4 [blank     ] 
    5 [import    ] from app.core import isrc as I
    6 [blank     ] 
    7 [blank     ] 
    8 [def       ] def test_placeholder_detection():
    9 [stmt      ]     assert I.is_placeholder_isrc("")
   10 [stmt      ]     assert I.is_placeholder_isrc("XX-XXX-00-00000")
   11 [stmt      ]     assert I.is_placeholder_isrc(None)
   12 [stmt      ]     assert not I.is_placeholder_isrc("RUZSM2600042")
   13 [blank     ] 
   14 [blank     ] 
   15 [def       ] def test_valid_isrc_positive():
   16 [stmt      ]     assert I.is_valid_isrc("RU-ZSM-26-00042")
   17 [stmt      ]     assert I.is_valid_isrc("RUZSM2600042")
   18 [stmt      ]     assert I.is_valid_isrc("us-abc-25-12345")
   19 [blank     ] 
   20 [blank     ] 
   21 [def       ] def test_valid_isrc_negative():
   22 [stmt      ]     assert not I.is_valid_isrc("XX-XXX-00-00000")
   23 [stmt      ]     assert not I.is_valid_isrc("RU-ZS-26-00042")  # 2 letters registrant, not 3
   24 [stmt      ]     assert not I.is_valid_isrc("R-ZSM-26-00042")
   25 [stmt      ]     assert not I.is_valid_isrc("")
   26 [stmt      ]     assert not I.is_valid_isrc(None)
   27 [stmt      ]     assert not I.is_valid_isrc("RUZSM26000")
   28 [blank     ] 
   29 [blank     ] 
   30 [def       ] def test_generate_deterministic():
   31 [code      ]     meta = {"title": "Turkish Nights", "artist": "ZS", "year": 2026}
   32 [code      ]     a = I.generate_isrc(meta)
   33 [code      ]     b = I.generate_isrc(meta)
   34 [stmt      ]     assert a == b
   35 [stmt      ]     assert I.is_valid_isrc(a)
   36 [stmt      ]     assert a.startswith("RU-ZSM-26-")
   37 [blank     ] 
   38 [blank     ] 
   39 [def       ] def test_generate_custom_country_registrant():
   40 [code      ]     meta = {"title": "Beat X", "artist": "ZS", "year": 2025,
   41 [code      ]             "country": "US", "label_isrc_code": "ABC"}
   42 [code      ]     r = I.generate_isrc(meta)
   43 [stmt      ]     assert r.startswith("US-ABC-25-")
   44 [stmt      ]     assert I.is_valid_isrc(r)
   45 [blank     ] 
   46 [blank     ] 
   47 [def       ] def test_generate_from_seq_number():
   48 [code      ]     meta = {"title": "T", "artist": "A", "year": 2026, "release_seq": 42}
   49 [code      ]     r = I.generate_isrc(meta)
   50 [stmt      ]     assert r.endswith("-00042")
   51 [blank     ] 
   52 [blank     ] 
   53 [def       ] def test_get_isrc_fallback_empty_when_bad_input():
   54 [comment   ]     # placeholder на входе — не пропускаем, генерируем
   55 [code      ]     meta = {"isrc": "XX-XXX-00-00000", "title": "T", "artist": "A"}
   56 [code      ]     r = I.get_isrc(meta)
   57 [stmt      ]     assert r
   58 [stmt      ]     assert I.is_valid_isrc(r)
   59 [stmt      ]     assert not I.is_placeholder_isrc(r)
   60 [blank     ] 
   61 [blank     ] 
   62 [def       ] def test_get_isrc_preserves_valid_input():
   63 [code      ]     meta = {"isrc": "RU-ZSM-26-01234", "title": "T", "artist": "A"}
   64 [code      ]     r = I.get_isrc(meta)
   65 [stmt      ]     assert I.is_valid_isrc(r)
   66 [blank     ] 
   67 [blank     ] 
   68 [def       ] def test_generate_stable_across_years_field_types():
   69 [comment   ]     # year как строка
   70 [code      ]     meta = {"title": "T", "artist": "A", "year": "2026"}
   71 [code      ]     r = I.generate_isrc(meta)
   72 [stmt      ]     assert "-26-" in r
   73 [blank     ] 
   74 [blank     ] 
   75 [def       ] def test_get_isrc_fallback_string():
   76 [code      ]     meta = {"title": "", "artist": ""}
   77 [code      ]     r = I.get_isrc(meta, fallback="UNREGISTERED")
   78 [stmt      ]     assert I.is_valid_isrc(r) or r == "UNREGISTERED"
```