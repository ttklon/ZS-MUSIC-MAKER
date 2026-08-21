# grep-таблицы `tests/test_font_utils.py`

## `import` — 2 совпадений
```
    3 | from __future__ import annotations
    5 | from app.core import font_utils as F
```

## `def` — 4 совпадений
```
    8 | def test_candidates_non_empty():
   16 | def test_candidates_regular_variant():
   21 | def test_env_override(monkeypatch):
   27 | def test_load_pil_font_returns_something():
```

## `assert` — 6 совпадений
```
   10 |     assert isinstance(cands, list)
   11 |     assert cands  # хотя бы 1
   13 |     assert len(cands) == len(set(cands))
   18 |     assert cands
   24 |     assert cands[0] == "/custom/font.ttf"
   29 |     assert f is not None
```
