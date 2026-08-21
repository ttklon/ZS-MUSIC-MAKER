# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/phoneme_coverage.py`

**Всего строк:** 137

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 65 | 47.4 |
| blank | 21 | 15.3 |
| docstring | 19 | 13.9 |
| branch | 12 | 8.8 |
| import | 5 | 3.6 |
| try_block | 4 | 2.9 |
| def | 3 | 2.2 |
| loop | 3 | 2.2 |
| return | 3 | 2.2 |
| comment | 2 | 1.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v10 — Phoneme Coverage Analyzer
    3 [docstring ] ================================================
    4 [docstring ] Voice Vault: покрытие фонем/сочетаний (ТЗ 3.8).
    5 [blank     ] 
    6 [docstring ] Считает какие фонемы/дифоны русского и английского уже записаны
    7 [docstring ] пользователем в Voice Vault, и рекомендует какие короткие фразы
    8 [docstring ] записать чтобы покрыть недостающие.
    9 [blank     ] 
   10 [docstring ] Не требует нейросети — работает на транскрипте (Whisper выход
   11 [docstring ] или ручной ввод текста) через словарь звуков.
   12 [docstring ] """
   13 [blank     ] 
   14 [import    ] from __future__ import annotations
   15 [blank     ] 
   16 [import    ] import json
   17 [import    ] from collections import Counter
   18 [import    ] from pathlib import Path
   19 [import    ] from typing import Any
   20 [blank     ] 
   21 [comment   ] # Русские фонемы (упрощённо, IPA-подобно)
   22 [code      ] RU_PHONEMES = list("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
   23 [comment   ] # Англ фонемы (по буквенным группам)
   24 [code      ] EN_PHONEMES = list("abcdefghijklmnopqrstuvwxyz")
   25 [code      ] DIPHTHONGS = [
   26 [code      ]     "ая",
   27 [code      ]     "ое",
   28 [code      ]     "ый",
   29 [code      ]     "уй",
   30 [code      ]     "ай",
   31 [code      ]     "ой",
   32 [code      ]     "ei",
   33 [code      ]     "ai",
   34 [code      ]     "ou",
   35 [code      ]     "au",
   36 [code      ]     "th",
   37 [code      ]     "sh",
   38 [code      ]     "ch",
   39 [code      ] ]
   40 [blank     ] 
   41 [code      ] VAULT_DIR = Path("voice_vault")
   42 [code      ] COVERAGE_FILE = VAULT_DIR / "phoneme_coverage.json"
   43 [blank     ] 
   44 [blank     ] 
   45 [def       ] def _collect_transcripts() -> list[str]:
   46 [docstring ]     """
   47 [docstring ]     Собирает все транскрипты из Voice Vault.
   48 [docstring ]     """
   49 [code      ]     texts = []
   50 [loop      ]     for p in VAULT_DIR.rglob("*.txt"):
   51 [try_block ]         try:
   52 [code      ]             texts.append(p.read_text(encoding="utf-8"))
   53 [try_block ]         except Exception:
   54 [code      ]             pass
   55 [loop      ]     for p in VAULT_DIR.rglob("*.json"):
   56 [try_block ]         try:
   57 [code      ]             data = json.loads(p.read_text(encoding="utf-8"))
   58 [branch    ]             if isinstance(data, dict) and "transcript" in data:
   59 [code      ]                 texts.append(str(data["transcript"]))
   60 [branch    ]             elif isinstance(data, list):
   61 [loop      ]                 for item in data:
   62 [branch    ]                     if isinstance(item, dict) and "transcript" in item:
   63 [code      ]                         texts.append(str(item["transcript"]))
   64 [try_block ]         except Exception:
   65 [code      ]             pass
   66 [return    ]     return texts
   67 [blank     ] 
   68 [blank     ] 
   69 [def       ] def compute_coverage() -> dict[str, Any]:
   70 [docstring ]     """
   71 [docstring ]     Пересчитывает покрытие. Возвращает и сохраняет в JSON.
   72 [docstring ]     """
   73 [code      ]     texts = _collect_transcripts()
   74 [code      ]     joined = " ".join(texts).lower()
   75 [blank     ] 
   76 [code      ]     ru_c = Counter(ch for ch in joined if ch in RU_PHONEMES)
   77 [code      ]     en_c = Counter(ch for ch in joined if ch in EN_PHONEMES)
   78 [code      ]     di_c = Counter(d for d in DIPHTHONGS if d in joined)
   79 [blank     ] 
   80 [code      ]     ru_missing = [p for p in RU_PHONEMES if ru_c[p] < 3]
   81 [code      ]     en_missing = [p for p in EN_PHONEMES if en_c[p] < 3]
   82 [code      ]     di_missing = [d for d in DIPHTHONGS if di_c[d] < 1]
   83 [blank     ] 
   84 [code      ]     total_ru = sum(ru_c.values())
   85 [code      ]     total_en = sum(en_c.values())
   86 [blank     ] 
   87 [code      ]     ru_cov_pct = round((len(RU_PHONEMES) - len(ru_missing)) / len(RU_PHONEMES) * 100, 1)
   88 [code      ]     en_cov_pct = round((len(EN_PHONEMES) - len(en_missing)) / len(EN_PHONEMES) * 100, 1)
   89 [blank     ] 
   90 [code      ]     suggestions = _make_suggestions(ru_missing, en_missing, di_missing)
   91 [blank     ] 
   92 [code      ]     report = {
   93 [code      ]         "ru_coverage_pct": ru_cov_pct,
   94 [code      ]         "en_coverage_pct": en_cov_pct,
   95 [code      ]         "ru_missing": ru_missing,
   96 [code      ]         "en_missing": en_missing,
   97 [code      ]         "diphthongs_missing": di_missing,
   98 [code      ]         "total_ru_chars": total_ru,
   99 [code      ]         "total_en_chars": total_en,
  100 [code      ]         "suggested_phrases": suggestions,
  101 [code      ]         "transcript_count": len(texts),
  102 [code      ]     }
  103 [blank     ] 
  104 [code      ]     VAULT_DIR.mkdir(parents=True, exist_ok=True)
  105 [code      ]     COVERAGE_FILE.write_text(
  106 [code      ]         json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
  107 [code      ]     )
  108 [return    ]     return report
  109 [blank     ] 
  110 [blank     ] 
  111 [def       ] def _make_suggestions(ru_missing, en_missing, di_missing) -> list[str]:
  112 [docstring ]     """
  113 [docstring ]     Простые пангаммы под недостающие звуки.
  114 [docstring ]     """
  115 [code      ]     pool = []
  116 [branch    ]     if "ъ" in ru_missing or "ы" in ru_missing:
  117 [code      ]         pool.append("Съешь ещё этих мягких французских булок, да выпей чаю")
  118 [branch    ]     if "ж" in ru_missing or "щ" in ru_missing:
  119 [code      ]         pool.append("Широкая электрификация южных губерний даст мощный толчок подъёму")
  120 [branch    ]     if "х" in ru_missing:
  121 [code      ]         pool.append("В чащах юга жил бы цитрус? Да, но фальшивый экземпляр!")
  122 [branch    ]     if "ц" in ru_missing:
  123 [code      ]         pool.append("Цапля целый день сидела на цветущем цветке")
  124 [branch    ]     if any(x in en_missing for x in "xzqj"):
  125 [code      ]         pool.append("The quick brown fox jumps over the lazy dog")
  126 [branch    ]     if "th" in di_missing:
  127 [code      ]         pool.append("Three thin thieves thought a thousand thoughts")
  128 [branch    ]     if "sh" in di_missing:
  129 [code      ]         pool.append("She sells seashells by the sea shore")
  130 [branch    ]     if not pool:
  131 [code      ]         pool = ["Запись выглядит достаточной. Можно двигаться к RVC-тренингу."]
  132 [return    ]     return pool[:5]
  133 [blank     ] 
  134 [blank     ] 
  135 [branch    ] if __name__ == "__main__":
  136 [code      ]     r = compute_coverage()
  137 [code      ]     print(json.dumps(r, ensure_ascii=False, indent=2))
```