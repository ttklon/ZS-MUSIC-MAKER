# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/ai_arranger.py`

**Всего строк:** 52

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 24 | 46.2 |
| docstring | 9 | 17.3 |
| blank | 7 | 13.5 |
| comment | 3 | 5.8 |
| def | 2 | 3.8 |
| loop | 2 | 3.8 |
| branch | 2 | 3.8 |
| import | 1 | 1.9 |
| class | 1 | 1.9 |
| return | 1 | 1.9 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — ai_arranger.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Интеллектуальная аранжировка трека.
    6 [docstring ] Определяет структуру (Intro, Verse, Hook, Drop, Outro) в зависимости от жанра.
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] from typing import List, Dict, Any
   10 [class     ] class AIArranger:
   11 [def       ]     def __init__(self):
   12 [comment   ]         # Шаблоны структур для разных типов жанров
   13 [code      ]         self.structures = {
   14 [code      ]             "electronic": ["intro", "buildup", "drop", "breakdown", "drop", "outro"],
   15 [code      ]             "hiphop": ["intro", "verse", "hook", "verse", "hook", "outro"],
   16 [code      ]             "rock": ["intro", "verse", "chorus", "verse", "chorus", "bridge", "chorus", "outro"],
   17 [code      ]             "ambient": ["intro", "texture_a", "texture_b", "texture_a", "outro"],
   18 [code      ]             "default": ["intro", "verse", "hook", "verse", "hook", "outro"]
   19 [code      ]         }
   20 [blank     ] 
   21 [def       ]     def get_structure(self, genre_tags: List[str]) -> List[Dict[str, Any]]:
   22 [docstring ]         """
   23 [docstring ]         Генерирует структуру трека с таймингами.
   24 [docstring ]         """
   25 [code      ]         category = "default"
   26 [loop      ]         for tag in genre_tags:
   27 [branch    ]             if tag in self.structures:
   28 [code      ]                 category = tag
   29 [code      ]                 break
   30 [blank     ]         
   31 [code      ]         base_struct = self.structures[category]
   32 [code      ]         full_struct = []
   33 [code      ]         current_sec = 0.0
   34 [blank     ]         
   35 [loop      ]         for section in base_struct:
   36 [comment   ]             # Длительность секции в тактах (обычно 4, 8 или 16)
   37 [code      ]             bars = 8 if section in ("verse", "drop", "chorus") else 4
   38 [code      ]             duration_sec = bars * (4 * (60.0 / 120.0)) # Упрощенно для 120 BPM
   39 [blank     ]             
   40 [code      ]             full_struct.append({
   41 [code      ]                 "name": section,
   42 [code      ]                 "bars": bars,
   43 [code      ]                 "start_sec": current_sec,
   44 [code      ]                 "duration_sec": round(duration_sec, 2)
   45 [code      ]             })
   46 [code      ]             current_sec += duration_sec
   47 [blank     ]             
   48 [return    ]         return full_struct
   49 [blank     ] 
   50 [branch    ] if __name__ == "__main__":
   51 [code      ]     arranger = AIArranger()
   52 [code      ]     print(arranger.get_structure(["electronic", "techno"]))
```