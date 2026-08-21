# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/genre_engine.py`

**Всего строк:** 127

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 60 | 47.2 |
| blank | 18 | 14.2 |
| def | 8 | 6.3 |
| comment | 7 | 5.5 |
| branch | 7 | 5.5 |
| docstring | 6 | 4.7 |
| import | 6 | 4.7 |
| return | 5 | 3.9 |
| class | 3 | 2.4 |
| try_block | 2 | 1.6 |
| loop | 2 | 1.6 |
| decorator | 1 | 0.8 |
| stmt | 1 | 0.8 |
| raise | 1 | 0.8 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — genre_engine.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Масштабируемая система управления жанрами (100+ жанров).
    6 [docstring ] Использует реестр стилей и фабрику для генерации параметров трека.
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] import json
   10 [import    ] import os
   11 [import    ] from typing import Dict, List
   12 [import    ] from dataclasses import dataclass, field
   13 [blank     ] 
   14 [decorator ] @dataclass
   15 [class     ] class GenreProfile:
   16 [code      ]     name: str
   17 [code      ]     bpm_range: tuple = (120, 140)
   18 [code      ]     preferred_keys: List[str] = field(default_factory=lambda: ["A minor", "E minor", "C major"])
   19 [code      ]     energy: float = 0.7
   20 [code      ]     swing: float = 0.0
   21 [code      ]     elements: List[str] = field(default_factory=lambda: ["drums", "bass", "melody"])
   22 [code      ]     tags: List[str] = field(default_factory=list)
   23 [blank     ] 
   24 [class     ] class StyleRegistry:
   25 [code      ]     _instance = None
   26 [blank     ] 
   27 [def       ]     def __new__(cls, *args, **kwargs):
   28 [branch    ]         if not cls._instance:
   29 [code      ]             cls._instance = super(StyleRegistry, cls).__new__(cls)
   30 [code      ]             cls._instance._initialized = False
   31 [return    ]         return cls._instance
   32 [blank     ] 
   33 [def       ]     def __init__(self):
   34 [branch    ]         if self._initialized:
   35 [return    ]             return
   36 [code      ]         self.genres: Dict[str, GenreProfile] = {}
   37 [code      ]         self._load_defaults()
   38 [code      ]         self._initialized = True
   39 [blank     ] 
   40 [def       ]     def _load_defaults(self):
   41 [comment   ]         # Базовые жанры
   42 [code      ]         self.register(GenreProfile(
   43 [code      ]             name="drift_phonk", 
   44 [code      ]             bpm_range=(120, 160), 
   45 [code      ]             preferred_keys=["A minor", "G# minor"], 
   46 [code      ]             energy=0.9, 
   47 [code      ]             tags=["aggressive", "distorted", "cowbell"]
   48 [code      ]         ))
   49 [blank     ]         
   50 [comment   ]         # Загрузка 100+ жанров из конфига
   51 [code      ]         config_path = os.path.join(os.path.dirname(__file__), "..", "config", "genres_100.json")
   52 [branch    ]         if os.path.exists(config_path):
   53 [try_block ]             try:
   54 [stmt      ]                 with open(config_path, "r", encoding="utf-8") as f:
   55 [code      ]                     data = json.load(f)
   56 [comment   ]                     # v26: Валидация структуры конфига
   57 [branch    ]                     if not isinstance(data, dict):
   58 [raise     ]                         raise ValueError("Genre config must be a JSON object")
   59 [blank     ]                     
   60 [loop      ]                     for category, genre_list in data.items():
   61 [branch    ]                         if not isinstance(genre_list, list):
   62 [code      ]                             continue
   63 [loop      ]                         for g_name in genre_list:
   64 [code      ]                             safe_name = g_name.lower().replace(" ", "_")
   65 [comment   ]                             # Динамическая настройка параметров в зависимости от категории
   66 [code      ]                             bpm_map = {
   67 [code      ]                                 "electronic": (124, 145),
   68 [code      ]                                 "hiphop_rnb": (85, 105),
   69 [code      ]                                 "jazz_blues": (90, 120),
   70 [code      ]                                 "rock_metal": (110, 160),
   71 [code      ]                                 "classical_cinematic": (60, 140),
   72 [code      ]                                 "folk_world": (80, 130)
   73 [code      ]                             }
   74 [code      ]                             self.register(GenreProfile(
   75 [code      ]                                 name=safe_name,
   76 [code      ]                                 bpm_range=bpm_map.get(category, (100, 130)),
   77 [code      ]                                 energy=0.8 if "metal" in category else 0.6,
   78 [code      ]                                 tags=[category, safe_name]
   79 [code      ]                             ))
   80 [try_block ]             except Exception as e:
   81 [import    ]                 from app.core.logger import app_logger
   82 [code      ]                 app_logger.error(f"Error loading genre config: {e}")
   83 [blank     ] 
   84 [def       ]     def register(self, profile: GenreProfile):
   85 [code      ]         self.genres[profile.name] = profile
   86 [blank     ] 
   87 [def       ]     def get_profile(self, name: str) -> GenreProfile:
   88 [comment   ]         # Пытаемся найти по точному имени, затем по нормализованному
   89 [code      ]         safe_name = name.lower().replace(" ", "_")
   90 [return    ]         return self.genres.get(name, self.genres.get(safe_name, self.genres.get("drift_phonk")))
   91 [blank     ] 
   92 [def       ]     def list_genres(self) -> List[str]:
   93 [return    ]         return list(self.genres.keys())
   94 [blank     ] 
   95 [class     ] class GenreFactory:
   96 [def       ]     def __init__(self, registry: StyleRegistry):
   97 [code      ]         self.registry = registry
   98 [blank     ] 
   99 [def       ]     def create_wizard_state(self, genre_name: str, override: dict = None) -> dict:
  100 [code      ]         profile = self.registry.get_profile(genre_name)
  101 [import    ]         import random
  102 [blank     ]         
  103 [code      ]         bpm = random.randint(profile.bpm_range[0], profile.bpm_range[1])
  104 [code      ]         key = random.choice(profile.preferred_keys)
  105 [blank     ]         
  106 [code      ]         state = {
  107 [code      ]             "genre": profile.name,
  108 [code      ]             "bpm_override": bpm,
  109 [code      ]             "key_override": key,
  110 [code      ]             "energy": profile.energy,
  111 [code      ]             "swing": profile.swing,
  112 [code      ]             "elements": profile.elements,
  113 [code      ]             "tags": profile.tags
  114 [code      ]         }
  115 [blank     ]         
  116 [branch    ]         if override:
  117 [code      ]             state.update(override)
  118 [blank     ]             
  119 [return    ]         return state
  120 [blank     ] 
  121 [branch    ] if __name__ == "__main__":
  122 [code      ]     reg = StyleRegistry()
  123 [code      ]     factory = GenreFactory(reg)
  124 [code      ]     print(f"Available genres: {len(reg.list_genres())}")
  125 [comment   ]     # Тест на конкретный жанр из 100+
  126 [code      ]     print(f"Generated Lo-Fi state: {factory.create_wizard_state('lo-fi_hip_hop')}")
  127 [code      ]     print(f"Generated Techno state: {factory.create_wizard_state('techno')}")
```