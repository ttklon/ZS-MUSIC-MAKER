# АУДИТ ФАЙЛА: `modules/lyrics_gen_v8.py`

**LOC:** 196  |  **Размер:** 7699 байт  |  **Проблем:** 4  |  **Risk score:** 7

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 19 | `__future__.annotations` | from |
| 21 | `random` | import |
| 22 | `re` | import |
| 24 | `modules.author_ref_lyrics` | from |
| 24 | `modules.lyrics_gen` | from |
| 92 | `agents.trend_scout_v3.actual_slang_for_prompt` | from |
| 157 | `agents.trend_scout_v3.scout` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 30 | `_split_blocks` | 31 | 16 | ✅ |
| 64 | `_validate_rhythm` | 10 | 4 | ✅ |
| 77 | `generate_lyrics_v8` | 119 | 27 | ✅ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### HIGH_COMPLEXITY — 2 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 30** — _split_blocks: сложность ≈ 16 (>15)

  ```
         28 | 
         29 | 
  >>>    30 | def _split_blocks(text: str) -> dict[str, list[str]]:
         31 |     """Парсим блоки [Куплет 1] / [Припев] / [Куплет 2] / [Аутро]."""
         32 |     blocks = {
  ```

- **строка 77** — generate_lyrics_v8: сложность ≈ 27 (>15)

  ```
         75 | 
         76 | 
  >>>    77 | def generate_lyrics_v8(
         78 |     theme: str,
         79 |     user_words: list[str] | None = None,
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 19** — import 'annotations' не используется в теле файла

  ```
         17 | """
         18 | 
  >>>    19 | from __future__ import annotations
         20 | 
         21 | import random
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 77** — generate_lyrics_v8: 119 LOC (>100) — декомпозиция

  ```
         75 | 
         76 | 
  >>>    77 | def generate_lyrics_v8(
         78 |     theme: str,
         79 |     user_words: list[str] | None = None,
  ```
