# grep-таблицы `tests/test_genre_and_audit.py`

## `import` — 4 совпадений
```
    5 | import sys
    6 | import os
   10 | from modules.genre_expansion_100 import get_genre_profile, list_all_supported_genres
   11 | from modules.global_audit_fixer import audit_system_integrity
```

## `print` — 3 совпадений
```
   22 |     print("Genre expansion tests passed successfully.")
   28 |     print("Global audit fixer tests passed successfully.")
   33 |     print("ALL TESTS PASSED.")
```

## `def` — 2 совпадений
```
   13 | def test_genre_expansion():
   24 | def test_audit_fixer():
```

## `if` — 1 совпадений
```
   30 | if __name__ == "__main__":
```

## `assert` — 5 совпадений
```
   15 |     assert len(genres) >= 50, "Should support at least 50+ genres"
   18 |     assert profile_phonk["bpm"] == 135
   21 |     assert profile_unknown["bpm"] == 120
   26 |     assert report["status"] == "PASSED_WITH_SELF_HEALING"
   27 |     assert report["critical_issues_resolved"] == 10
```
