# АУДИТ ФАЙЛА: `modules/sidechain.py`

**LOC:** 290  |  **Размер:** 8866 байт  |  **Проблем:** 5  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 16 | `__future__.annotations` | from |
| 18 | `json` | import |
| 19 | `math` | import |
| 20 | `dataclasses.dataclass` | from |
| 21 | `pathlib.Path` | from |
| 22 | `typing.Any` | from |
| 25 | `pedalboard` | import |
| 33 | `numpy` | import |
| 34 | `soundfile` | import |
| 44 | `scipy.signal.butter` | from |
| 45 | `scipy.signal.sosfilt` | from |
| 162 | `scipy.signal` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 67 | `_envelope_from_kick` | 20 | 4 | ❌ |
| 90 | `_bandpass_numpy` | 14 | 1 | ✅ |
| 107 | `_detect_kick_onsets` | 27 | 8 | ❌ |
| 137 | `_numpy_dsp` | 94 | 6 | ❌ |
| 234 | `measure_ducking_effect` | 21 | 5 | ❌ |
| 258 | `apply_sidechain` | 18 | 0 | ❌ |
| 279 | `capability_report` | 7 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 55 | `SidechainResult` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 234** — public function 'measure_ducking_effect' без docstring

  ```
        232 | 
        233 | 
  >>>   234 | def measure_ducking_effect(bus_before, bus_after, kick, sr: int) -> float:
        235 |     if _np is None:
        236 |         return 0.0
  ```

- **строка 258** — public function 'apply_sidechain' без docstring

  ```
        256 | 
        257 | 
  >>>   258 | def apply_sidechain(
        259 |     bus_wav: str,
        260 |     kick_wav: str,
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 16** — import 'annotations' не используется в теле файла

  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import json
  ```

### MISSING_CLASS_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 55** — public class 'SidechainResult' без docstring

  ```
         53 | 
         54 | @dataclass
  >>>    55 | class SidechainResult:
         56 |     ok: bool
         57 |     engine: str
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 290** — print() вместо logger

  ```
        288 | 
        289 | if __name__ == "__main__":
  >>>   290 |     print(json.dumps(capability_report(), indent=2))
  ```
