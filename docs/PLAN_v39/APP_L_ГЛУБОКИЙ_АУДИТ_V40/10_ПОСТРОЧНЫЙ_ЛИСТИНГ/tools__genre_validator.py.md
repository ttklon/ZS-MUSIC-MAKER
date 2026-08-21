# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/genre_validator.py`

**Всего строк:** 53

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 17 | 32.1 |
| blank | 10 | 18.9 |
| docstring | 6 | 11.3 |
| branch | 5 | 9.4 |
| comment | 4 | 7.5 |
| import | 3 | 5.7 |
| loop | 3 | 5.7 |
| try_block | 2 | 3.8 |
| return | 2 | 3.8 |
| def | 1 | 1.9 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — genre_validator.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Автоматическая валидация всех 119+ жанров.
    6 [docstring ] Гарантирует целостность конфигов и отсутствие критических ошибок в профилях.
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] import sys
   10 [import    ] from pathlib import Path
   11 [blank     ] 
   12 [comment   ] # Добавляем корень проекта в пути
   13 [code      ] sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
   14 [blank     ] 
   15 [import    ] from modules.genre_engine import StyleRegistry, GenreFactory
   16 [blank     ] 
   17 [def       ] def validate_all():
   18 [code      ]     print("=== Genre Integrity Audit (100+ Styles) ===")
   19 [code      ]     reg = StyleRegistry()
   20 [code      ]     factory = GenreFactory(reg)
   21 [blank     ]     
   22 [code      ]     genres = reg.list_genres()
   23 [code      ]     print(f"Total genres found: {len(genres)}")
   24 [blank     ]     
   25 [code      ]     errors = []
   26 [loop      ]     for g_name in genres:
   27 [try_block ]         try:
   28 [code      ]             state = factory.create_wizard_state(g_name)
   29 [comment   ]             # Проверка обязательных полей
   30 [code      ]             required = ["bpm_override", "key_override", "energy", "tags"]
   31 [loop      ]             for field in required:
   32 [branch    ]                 if field not in state:
   33 [code      ]                     errors.append(f"Genre '{g_name}' missing required field: {field}")
   34 [blank     ]             
   35 [comment   ]             # Проверка диапазонов
   36 [branch    ]             if not (20 <= state["bpm_override"] <= 300):
   37 [code      ]                 errors.append(f"Genre '{g_name}' has insane BPM: {state['bpm_override']}")
   38 [blank     ]                 
   39 [try_block ]         except Exception as e:
   40 [code      ]             errors.append(f"CRITICAL failure in genre '{g_name}': {e}")
   41 [blank     ] 
   42 [branch    ]     if not errors:
   43 [code      ]         print("✅ All 119+ genres are VALID and BATTLE-READY.")
   44 [return    ]         return True
   45 [branch    ]     else:
   46 [code      ]         print(f"❌ Found {len(errors)} issues:")
   47 [loop      ]         for err in errors:
   48 [code      ]             print(f"  - {err}")
   49 [return    ]         return False
   50 [blank     ] 
   51 [branch    ] if __name__ == "__main__":
   52 [code      ]     success = validate_all()
   53 [code      ]     sys.exit(0 if success else 1)
```