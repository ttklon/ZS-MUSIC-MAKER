# АУДИТ ФАЙЛА: `modules/anti_neuro_v10.py`

**LOC:** 401  |  **Размер:** 14498 байт  |  **Проблем:** 6  |  **Risk score:** 9

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 17 | `__future__.annotations` | from |
| 19 | `json` | import |
| 20 | `logging` | import |
| 21 | `random` | import |
| 22 | `pathlib.Path` | from |
| 23 | `typing.Any` | from |
| 28 | `pydub.AudioSegment` | from |
| 29 | `pydub.generators.WhiteNoise` | from |
| 38 | `numpy` | import |
| 39 | `soundfile` | import |
| 134 | `shutil` | import |
| 304 | `numpy` | import |
| 308 | `scipy.signal.butter` | from |
| 308 | `scipy.signal.sosfilt` | from |
| 346 | `librosa` | import |
| 347 | `numpy` | import |
| 204 | `scipy.signal.butter` | from |
| 204 | `scipy.signal.sosfilt` | from |
| 217 | `scipy.signal.butter` | from |
| 217 | `scipy.signal.sosfilt` | from |
| 246 | `scipy.signal.butter` | from |
| 246 | `scipy.signal.sosfilt` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 48 | `polish_vocal` | 56 | 4 | ✅ |
| 107 | `apply_polish` | 18 | 4 | ✅ |
| 128 | `_polish_numpy` | 152 | 21 | ✅ |
| 283 | `_apply_stage` | 105 | 16 | ❌ |
| 391 | `capability_report` | 6 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### LONG_FUNCTION — 2 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 128** — _polish_numpy: 152 LOC (>100) — декомпозиция

  ```
        126 | 
        127 | 
  >>>   128 | def _polish_numpy(
        129 |     vocal_wav: str, out_wav: str, preset: str = "standard", seed: int | None = None
        130 | ) -> dict[str, Any]:
  ```

- **строка 283** — _apply_stage: 105 LOC (>100) — декомпозиция

  ```
        281 | 
        282 | 
  >>>   283 | def _apply_stage(seg, name: str, rng: random.Random):
        284 |     if name == "breath":
        285 |         breath = WhiteNoise().to_audio_segment(duration=180).apply_gain(-32)
  ```

### HIGH_COMPLEXITY — 2 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 128** — _polish_numpy: сложность ≈ 21 (>15)

  ```
        126 | 
        127 | 
  >>>   128 | def _polish_numpy(
        129 |     vocal_wav: str, out_wav: str, preset: str = "standard", seed: int | None = None
        130 | ) -> dict[str, Any]:
  ```

- **строка 283** — _apply_stage: сложность ≈ 16 (>15)

  ```
        281 | 
        282 | 
  >>>   283 | def _apply_stage(seg, name: str, rng: random.Random):
        284 |     if name == "breath":
        285 |         breath = WhiteNoise().to_audio_segment(duration=180).apply_gain(-32)
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 17** — import 'annotations' не используется в теле файла

  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | import json
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 401** — print() вместо logger

  ```
        399 | 
        400 | if __name__ == "__main__":
  >>>   401 |     print(json.dumps(capability_report(), ensure_ascii=False, indent=2))
  ```
