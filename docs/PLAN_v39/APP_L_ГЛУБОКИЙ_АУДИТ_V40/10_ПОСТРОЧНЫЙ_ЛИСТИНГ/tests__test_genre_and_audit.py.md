# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_genre_and_audit.py`

**Всего строк:** 33

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 10 | 30.3 |
| blank | 8 | 24.2 |
| stmt | 5 | 15.2 |
| import | 4 | 12.1 |
| docstring | 3 | 9.1 |
| def | 2 | 6.1 |
| branch | 1 | 3.0 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] Unit tests for ZS-MUSIC-MAKER 100+ genre expansion and global audit fixer.
    3 [docstring ] """
    4 [blank     ] 
    5 [import    ] import sys
    6 [import    ] import os
    7 [blank     ] 
    8 [code      ] sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    9 [blank     ] 
   10 [import    ] from modules.genre_expansion_100 import get_genre_profile, list_all_supported_genres
   11 [import    ] from modules.global_audit_fixer import audit_system_integrity
   12 [blank     ] 
   13 [def       ] def test_genre_expansion():
   14 [code      ]     genres = list_all_supported_genres()
   15 [stmt      ]     assert len(genres) >= 50, "Should support at least 50+ genres"
   16 [blank     ]     
   17 [code      ]     profile_phonk = get_genre_profile("drift_phonk")
   18 [stmt      ]     assert profile_phonk["bpm"] == 135
   19 [blank     ]     
   20 [code      ]     profile_unknown = get_genre_profile("unknown_cyber_jazz")
   21 [stmt      ]     assert profile_unknown["bpm"] == 120
   22 [code      ]     print("Genre expansion tests passed successfully.")
   23 [blank     ] 
   24 [def       ] def test_audit_fixer():
   25 [code      ]     report = audit_system_integrity()
   26 [stmt      ]     assert report["status"] == "PASSED_WITH_SELF_HEALING"
   27 [stmt      ]     assert report["critical_issues_resolved"] == 10
   28 [code      ]     print("Global audit fixer tests passed successfully.")
   29 [blank     ] 
   30 [branch    ] if __name__ == "__main__":
   31 [code      ]     test_genre_expansion()
   32 [code      ]     test_audit_fixer()
   33 [code      ]     print("ALL TESTS PASSED.")
```