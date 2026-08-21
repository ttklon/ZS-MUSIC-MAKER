# grep-таблицы `tests/test_isrc.py`

## `import` — 2 совпадений
```
    3 | from __future__ import annotations
    5 | from app.core import isrc as I
```

## `def` — 10 совпадений
```
    8 | def test_placeholder_detection():
   15 | def test_valid_isrc_positive():
   21 | def test_valid_isrc_negative():
   30 | def test_generate_deterministic():
   39 | def test_generate_custom_country_registrant():
   47 | def test_generate_from_seq_number():
   53 | def test_get_isrc_fallback_empty_when_bad_input():
   62 | def test_get_isrc_preserves_valid_input():
   68 | def test_generate_stable_across_years_field_types():
   75 | def test_get_isrc_fallback_string():
```

## `assert` — 25 совпадений
```
    9 |     assert I.is_placeholder_isrc("")
   10 |     assert I.is_placeholder_isrc("XX-XXX-00-00000")
   11 |     assert I.is_placeholder_isrc(None)
   12 |     assert not I.is_placeholder_isrc("RUZSM2600042")
   16 |     assert I.is_valid_isrc("RU-ZSM-26-00042")
   17 |     assert I.is_valid_isrc("RUZSM2600042")
   18 |     assert I.is_valid_isrc("us-abc-25-12345")
   22 |     assert not I.is_valid_isrc("XX-XXX-00-00000")
   23 |     assert not I.is_valid_isrc("RU-ZS-26-00042")  # 2 letters registrant, not 3
   24 |     assert not I.is_valid_isrc("R-ZSM-26-00042")
   25 |     assert not I.is_valid_isrc("")
   26 |     assert not I.is_valid_isrc(None)
   27 |     assert not I.is_valid_isrc("RUZSM26000")
   34 |     assert a == b
   35 |     assert I.is_valid_isrc(a)
   36 |     assert a.startswith("RU-ZSM-26-")
   43 |     assert r.startswith("US-ABC-25-")
   44 |     assert I.is_valid_isrc(r)
   50 |     assert r.endswith("-00042")
   57 |     assert r
   58 |     assert I.is_valid_isrc(r)
   59 |     assert not I.is_placeholder_isrc(r)
   65 |     assert I.is_valid_isrc(r)
   72 |     assert "-26-" in r
   78 |     assert I.is_valid_isrc(r) or r == "UNREGISTERED"
```

## `todo` — 3 совпадений
```
   10 |     assert I.is_placeholder_isrc("XX-XXX-00-00000")
   22 |     assert not I.is_valid_isrc("XX-XXX-00-00000")
   55 |     meta = {"isrc": "XX-XXX-00-00000", "title": "T", "artist": "A"}
```
