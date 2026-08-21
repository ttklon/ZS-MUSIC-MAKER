# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/ai/prompts.py`

**Всего строк:** 94

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 34 | 36.2 |
| docstring | 23 | 24.5 |
| blank | 16 | 17.0 |
| branch | 7 | 7.4 |
| def | 6 | 6.4 |
| return | 6 | 6.4 |
| comment | 1 | 1.1 |
| import | 1 | 1.1 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - app/ai/prompts.py (v38): промпты для локальных LLM."""
    3 [import    ] from __future__ import annotations
    4 [blank     ] 
    5 [docstring ] SYSTEM_LYRICS = """Ты - русскоязычный автор-хитмейкер (рэп/трэп/фонк/поп-рэп/шансон). Правила:
    6 [docstring ] 1. Каждая строчка двигает историю, даёт punchline или усиливает эмоцию. Никаких пустых нейро-наборов.
    7 [docstring ] 2. Живой язык: сленг, конкретика, детали - не абстракции.
    8 [docstring ] 3. 6-10 слогов в строке под BPM. Схема AABB или ABAB, внутренние рифмы приветствуются.
    9 [docstring ] 4. Куплет = развитие мысли, не 4 несвязанных афоризма.
   10 [docstring ] 5. Хук = короткая цепляющая фраза, повтор 2-4 раза.
   11 [docstring ] 6. Референс-артиста соблюдать по лексике/флоу, но НЕ копировать его строки.
   12 [docstring ] 7. Только чистый текст с метками [Куплет 1]/[Припев]/[Bridge]. Без комментариев."""
   13 [blank     ] 
   14 [docstring ] SYSTEM_ANALYSIS = """Ты - музыкальный аналитик. Строишь досье артиста на русском в JSON:
   15 [docstring ] {"core_themes": [...], "lexicon": [...], "flow": "...", "rhyme_style": "...",
   16 [docstring ] "emotional_range": [...], "signature_tricks": [...], "audience": "...",
   17 [docstring ] "story_arcs": [...], "avoid": [...]}
   18 [docstring ] Только валидный JSON без комментариев."""
   19 [blank     ] 
   20 [docstring ] SYSTEM_TRACK_ANALYSIS = """Ты - аналитик отдельного трека. Выдай JSON:
   21 [docstring ] {"title_meaning": "...", "storyline": "...",
   22 [docstring ] "line_breakdown": [{"line": "...", "meaning": "...", "device": "..."}],
   23 [docstring ] "hook": "...", "hook_repetitions": N, "energy_curve": "...",
   24 [docstring ] "reusable_elements": [...]}
   25 [docstring ] Только валидный JSON. line_breakdown обязателен для каждой строки."""
   26 [blank     ] 
   27 [docstring ] SYSTEM_METADATA = """Ты - маркетолог инди-музыки. Выдай JSON:
   28 [docstring ] {title, spotify_desc, youtube_desc, tags_tiktok (15), tags_instagram (10)}.
   29 [docstring ] Только валидный JSON, без комментариев."""
   30 [blank     ] 
   31 [blank     ] 
   32 [def       ] def build_lyrics_prompt(theme, genre, bpm, n_verses, bilingual,
   33 [code      ]                         user_lines=None, artist_dossier=None, track_reference=None):
   34 [code      ]     parts = [f"Тема: {theme}", f"Жанр: {genre}", f"BPM: {bpm}",
   35 [code      ]              f"Куплетов: {n_verses}",
   36 [code      ]              f"Билингвал (RU куплеты + EN хук): {'да' if bilingual else 'нет'}"]
   37 [branch    ]     if user_lines:
   38 [code      ]         parts.append("ОБЯЗАТЕЛЬНЫЕ строки (впитать дословно):")
   39 [code      ]         parts += [f"  - {l}" for l in user_lines]
   40 [branch    ]     if artist_dossier:
   41 [code      ]         parts.append("Стиль референс-артиста (досье):")
   42 [code      ]         parts.append(f"  темы: {', '.join(artist_dossier.get('core_themes', [])[:8])}")
   43 [code      ]         parts.append(f"  лексика: {', '.join(artist_dossier.get('lexicon', [])[:15])}")
   44 [code      ]         parts.append(f"  флоу: {artist_dossier.get('flow', '-')}")
   45 [code      ]         parts.append(f"  фишки: {', '.join(artist_dossier.get('signature_tricks', [])[:5])}")
   46 [code      ]         parts.append(f"  избегает: {', '.join(artist_dossier.get('avoid', [])[:5])}")
   47 [branch    ]     if track_reference:
   48 [code      ]         parts.append("Референс-трек (в его духе, не копия):")
   49 [code      ]         parts.append(f"  сюжет: {track_reference.get('storyline', '-')}")
   50 [code      ]         parts.append(f"  hook: {track_reference.get('hook', '-')}")
   51 [code      ]         parts.append(f"  энергия: {track_reference.get('energy_curve', '-')}")
   52 [code      ]     parts.append("")
   53 [code      ]     parts.append("Пиши текст трека сейчас. Без комментариев.")
   54 [return    ]     return "\n".join(parts)
   55 [blank     ] 
   56 [blank     ] 
   57 [def       ] def build_dossier_prompt(artist, tracks_text):
   58 [return    ]     return (f"Артист: {artist}\n\nВсе известные тексты:\n=====\n"
   59 [code      ]             f"{tracks_text[:20000]}\n=====\n\nПострой досье JSON строго по schema.")
   60 [blank     ] 
   61 [blank     ] 
   62 [def       ] def build_track_dossier_prompt(title, lyrics, features):
   63 [return    ]     return (f"Трек: {title}\nBPM: {features.get('bpm', '?')}\n"
   64 [code      ]             f"Тональность: {features.get('key', '?')}\n"
   65 [code      ]             f"Теги (авто): {', '.join(features.get('tags', []))}\n"
   66 [code      ]             f"Длительность: {features.get('duration_sec', '?')} сек\n\n"
   67 [code      ]             f"Текст:\n=====\n{lyrics}\n=====\n\nВерни JSON по schema.")
   68 [blank     ] 
   69 [blank     ] 
   70 [def       ] def build_metadata_prompt(theme, style, snippet):
   71 [return    ]     return (f"Тема: {theme}\nСтиль: {style}\n\nКусок лирики:\n{snippet[:1200]}\n\n"
   72 [code      ]             "Выдай JSON {title, spotify_desc, youtube_desc, tags_tiktok, tags_instagram}.")
   73 [blank     ] 
   74 [blank     ] 
   75 [def       ] def build_music_prompt(genre, bpm, key, mood, reference_artist=None,
   76 [code      ]                        reference_track_features=None):
   77 [code      ]     parts = [f"{genre}", f"{bpm} BPM", f"{key} key", f"mood: {mood}"]
   78 [branch    ]     if reference_artist:
   79 [code      ]         parts.append(f"in the style of {reference_artist}")
   80 [branch    ]     if reference_track_features:
   81 [code      ]         instr = reference_track_features.get("instruments", [])
   82 [branch    ]         if instr:
   83 [code      ]             parts.append("instruments: " + ", ".join(instr[:6]))
   84 [code      ]         atmo = reference_track_features.get("atmosphere")
   85 [branch    ]         if atmo:
   86 [code      ]             parts.append(atmo)
   87 [code      ]     parts.append("professional mix, punchy drums, clean stereo image")
   88 [return    ]     return ", ".join(parts)
   89 [blank     ] 
   90 [blank     ] 
   91 [def       ] def build_cover_prompt(title, artist, genre, mood):
   92 [return    ]     return (f"Album cover for song '{title}' by {artist}. Genre: {genre}. "
   93 [code      ]             f"Mood: {mood}. Cinematic, high contrast, bold typography, square 1400x1400, "
   94 [code      ]             f"no watermark, professional music release cover.")
```