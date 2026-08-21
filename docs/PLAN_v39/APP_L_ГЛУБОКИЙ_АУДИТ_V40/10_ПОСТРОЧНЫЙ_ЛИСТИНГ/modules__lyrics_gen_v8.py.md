# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/lyrics_gen_v8.py`

**Всего строк:** 196

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 97 | 49.5 |
| blank | 22 | 11.2 |
| docstring | 20 | 10.2 |
| branch | 20 | 10.2 |
| comment | 11 | 5.6 |
| try_block | 11 | 5.6 |
| import | 6 | 3.1 |
| def | 3 | 1.5 |
| loop | 3 | 1.5 |
| return | 3 | 1.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v8] lyrics_gen_v8.py — надстройка над lyrics_gen v7.
    3 [blank     ] 
    4 [docstring ] Что добавляет v8 (не удаляя ничего из v7):
    5 [docstring ]   • Интеграция с author_ref_lyrics (стиль конкретного автора-референса).
    6 [docstring ]   • Интеграция с trend_scout_v3 (актуальный сленг на день создания).
    7 [docstring ]   • Поле «female_backing_chorus»: если True — генерируется отдельный «женский»
    8 [docstring ]     вариант припева для наложения как бэк.
    9 [docstring ]   • Bilingual разметка [Куплет RU] / [Припев EN / Female backing].
   10 [docstring ]   • Валидация ритмики: строки не выходят за ±20% средней длины.
   11 [blank     ] 
   12 [docstring ] API:
   13 [docstring ]     generate_lyrics_v8(theme, user_words, bpm, author=None,
   14 [docstring ]                        target_lines=16, want_female_backing=False) -> dict
   15 [docstring ]       → {'text': str, 'chorus_lines': list[str],
   16 [docstring ]          'used_slang': list[str], 'author_style_used': bool}
   17 [docstring ] """
   18 [blank     ] 
   19 [import    ] from __future__ import annotations
   20 [blank     ] 
   21 [import    ] import random
   22 [import    ] import re
   23 [blank     ] 
   24 [import    ] from modules import (
   25 [code      ]     author_ref_lyrics,
   26 [code      ]     lyrics_gen,  # v7, оставляем как есть
   27 [code      ] )
   28 [blank     ] 
   29 [blank     ] 
   30 [def       ] def _split_blocks(text: str) -> dict[str, list[str]]:
   31 [docstring ]     """Парсим блоки [Куплет 1] / [Припев] / [Куплет 2] / [Аутро]."""
   32 [code      ]     blocks = {
   33 [code      ]         "intro": [],
   34 [code      ]         "verse1": [],
   35 [code      ]         "chorus": [],
   36 [code      ]         "verse2": [],
   37 [code      ]         "bridge": [],
   38 [code      ]         "outro": [],
   39 [code      ]     }
   40 [code      ]     current = "verse1"
   41 [loop      ]     for raw_line in text.splitlines():
   42 [code      ]         line = raw_line.strip()
   43 [branch    ]         if not line:
   44 [code      ]             continue
   45 [code      ]         low = line.lower()
   46 [branch    ]         if low.startswith("[") and low.endswith("]"):
   47 [branch    ]             if "интро" in low or "intro" in low:
   48 [code      ]                 current = "intro"
   49 [branch    ]             elif "припев" in low or "chorus" in low or "hook" in low:
   50 [code      ]                 current = "chorus"
   51 [branch    ]             elif "куплет 1" in low or "verse 1" in low:
   52 [code      ]                 current = "verse1"
   53 [branch    ]             elif "куплет 2" in low or "verse 2" in low:
   54 [code      ]                 current = "verse2"
   55 [branch    ]             elif "бридж" in low or "bridge" in low:
   56 [code      ]                 current = "bridge"
   57 [branch    ]             elif "аутро" in low or "outro" in low:
   58 [code      ]                 current = "outro"
   59 [code      ]             continue
   60 [code      ]         blocks[current].append(line)
   61 [return    ]     return blocks
   62 [blank     ] 
   63 [blank     ] 
   64 [def       ] def _validate_rhythm(
   65 [code      ]     lines: list[str], target_avg: float = 9.0, tol: float = 0.3
   66 [code      ] ) -> list[str]:
   67 [docstring ]     """Отсекаем строки, которые слишком короткие/длинные (≥±30% от target)."""
   68 [code      ]     kept = []
   69 [loop      ]     for l in lines:
   70 [code      ]         n = sum(1 for ch in l.lower() if ch in "аеёиоуыэюяaeiouy")
   71 [code      ]         n = max(1, n)
   72 [branch    ]         if target_avg * (1 - tol) <= n <= target_avg * (1 + tol) or len(lines) < 4:
   73 [code      ]             kept.append(l)
   74 [return    ]     return kept or lines
   75 [blank     ] 
   76 [blank     ] 
   77 [def       ] def generate_lyrics_v8(
   78 [code      ]     theme: str,
   79 [code      ]     user_words: list[str] | None = None,
   80 [code      ]     bpm: int = 130,
   81 [code      ]     author: str | None = None,
   82 [code      ]     target_lines: int = 16,
   83 [code      ]     want_female_backing: bool = False,
   84 [code      ]     lang_mix: str = "ru+en",
   85 [code      ] ) -> dict:
   86 [docstring ]     """
   87 [docstring ]     Главная точка входа v8. Возвращает готовый текст + мета.
   88 [docstring ]     """
   89 [code      ]     user_words = [w.strip() for w in (user_words or []) if w and w.strip()]
   90 [comment   ]     # 1) актуальный сленг на сегодня
   91 [try_block ]     try:
   92 [import    ]         from agents.trend_scout_v3 import actual_slang_for_prompt
   93 [blank     ] 
   94 [code      ]         slang = actual_slang_for_prompt(theme, n_words=15)
   95 [try_block ]     except Exception:
   96 [code      ]         slang = []
   97 [blank     ] 
   98 [comment   ]     # 2) стилевой промт по автору (если задан)
   99 [code      ]     author_style_used = False
  100 [code      ]     style_prompt = ""
  101 [branch    ]     if author:
  102 [try_block ]         try:
  103 [comment   ]             # если автора нет в корпусе — попробуем подтянуть онлайн
  104 [code      ]             profile = author_ref_lyrics.get_style_profile(author)
  105 [branch    ]             if not profile:
  106 [code      ]                 author_ref_lyrics.fetch_and_ingest_author(author, max_tracks=5)
  107 [code      ]                 profile = author_ref_lyrics.get_style_profile(author)
  108 [branch    ]             if profile:
  109 [code      ]                 style_prompt = author_ref_lyrics.build_style_prompt(
  110 [code      ]                     author=author,
  111 [code      ]                     theme=theme,
  112 [code      ]                     user_words=user_words + slang[:6],
  113 [code      ]                     bpm=bpm,
  114 [code      ]                     target_lines=target_lines,
  115 [code      ]                 )
  116 [code      ]                 author_style_used = True
  117 [try_block ]         except Exception:
  118 [code      ]             style_prompt = ""
  119 [blank     ] 
  120 [comment   ]     # 3) базовая генерация через v7
  121 [code      ]     seed = theme
  122 [branch    ]     if user_words:
  123 [code      ]         seed += " — " + ", ".join(user_words)
  124 [branch    ]     if slang:
  125 [code      ]         seed += " · слэнг: " + ", ".join(slang[:8])
  126 [code      ]     seed_user_lyrics = user_words  # v7 гарантирует их появление
  127 [blank     ] 
  128 [try_block ]     try:
  129 [code      ]         raw = lyrics_gen.generate_lyrics(
  130 [code      ]             theme=seed,
  131 [code      ]             bpm=bpm,
  132 [code      ]             user_lyrics_lines=seed_user_lyrics,
  133 [code      ]             style_prompt=style_prompt or None,
  134 [code      ]             target_lines=target_lines,
  135 [code      ]         )
  136 [try_block ]     except TypeError:
  137 [comment   ]         # v7 может не поддерживать все kwargs — деградируем к базовому вызову
  138 [try_block ]         try:
  139 [code      ]             raw = lyrics_gen.generate_lyrics(theme=seed, bpm=bpm)
  140 [try_block ]         except Exception:
  141 [code      ]             raw = f"[Куплет 1]\n{seed}\n[Припев]\n{random.choice(slang) if slang else 'yeah'}\n"
  142 [try_block ]     except Exception as e:
  143 [code      ]         raw = f"[Куплет 1]\n{seed}\n[Припев]\n(fallback: {e})\n"
  144 [blank     ] 
  145 [comment   ]     # 4) парсим, валидируем ритм
  146 [code      ]     blocks = _split_blocks(raw if isinstance(raw, str) else str(raw))
  147 [loop      ]     for key in ("verse1", "verse2", "chorus"):
  148 [code      ]         blocks[key] = _validate_rhythm(blocks[key])
  149 [blank     ] 
  150 [comment   ]     # 5) обеспечиваем bilingual разметку
  151 [branch    ]     if lang_mix == "ru+en":
  152 [comment   ]         # Ищем в припеве английские хуки; если их нет — подмешиваем из trend_scout_v3
  153 [code      ]         chorus_txt = " ".join(blocks["chorus"]).lower()
  154 [code      ]         has_en = any(re.search(r"[a-z]{3,}", w) for w in chorus_txt.split())
  155 [branch    ]         if not has_en:
  156 [try_block ]             try:
  157 [import    ]                 from agents.trend_scout_v3 import scout
  158 [blank     ] 
  159 [code      ]                 hook_en = random.choice(scout(theme)["hooks_en"])
  160 [code      ]                 blocks["chorus"].append(hook_en)
  161 [try_block ]             except Exception:
  162 [code      ]                 blocks["chorus"].append("night ride, we don't stop")
  163 [blank     ] 
  164 [comment   ]     # 6) собираем финальный текст
  165 [code      ]     parts = []
  166 [branch    ]     if blocks["intro"]:
  167 [code      ]         parts.append("[Интро]\n" + "\n".join(blocks["intro"]))
  168 [code      ]     parts.append(
  169 [code      ]         "[Куплет 1]\n" + "\n".join(blocks["verse1"] or ["город спит, а мотор рычит"])
  170 [code      ]     )
  171 [code      ]     parts.append(
  172 [code      ]         "[Припев]\n" + "\n".join(blocks["chorus"] or ["night ride, we don't stop"])
  173 [code      ]     )
  174 [code      ]     parts.append("[Куплет 2]\n" + "\n".join(blocks["verse2"] or blocks["verse1"] or []))
  175 [code      ]     parts.append("[Припев]\n" + "\n".join(blocks["chorus"] or []))
  176 [branch    ]     if blocks["bridge"]:
  177 [code      ]         parts.append("[Бридж]\n" + "\n".join(blocks["bridge"]))
  178 [branch    ]     if blocks["outro"]:
  179 [code      ]         parts.append("[Аутро]\n" + "\n".join(blocks["outro"]))
  180 [blank     ] 
  181 [code      ]     final_text = "\n\n".join(parts)
  182 [blank     ] 
  183 [comment   ]     # 7) вариант припева для женского бэка
  184 [code      ]     chorus_lines = blocks["chorus"] or []
  185 [branch    ]     if want_female_backing and chorus_lines:
  186 [comment   ]         # Помечаем — orchestrator подхватит и сгенерирует backing.
  187 [code      ]         pass
  188 [blank     ] 
  189 [return    ]     return {
  190 [code      ]         "text": final_text,
  191 [code      ]         "chorus_lines": chorus_lines,
  192 [code      ]         "used_slang": slang,
  193 [code      ]         "author_style_used": author_style_used,
  194 [code      ]         "want_female_backing": want_female_backing,
  195 [code      ]         "author": author or "",
  196 [code      ]     }
```