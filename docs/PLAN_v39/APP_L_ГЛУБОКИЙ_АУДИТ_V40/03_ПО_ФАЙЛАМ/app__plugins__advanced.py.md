# АУДИТ ФАЙЛА: `app/plugins/advanced.py`

**LOC:** 86  |  **Размер:** 3317 байт  |  **Проблем:** 5  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 8 | `numpy` | import |
| 9 | `app.plugins.base.AudioPlugin` | from |
| 14 | `pedalboard.Pedalboard` | from |
| 14 | `pedalboard.Distortion` | from |
| 14 | `pedalboard.Reverb` | from |
| 14 | `pedalboard.Compressor` | from |
| 14 | `pedalboard.HighpassFilter` | from |
| 33 | `audiomentations.Compose` | from |
| 33 | `audiomentations.PitchShift` | from |
| 33 | `audiomentations.TimeStretch` | from |
| 33 | `audiomentations.AddGaussianNoise` | from |
| 33 | `audiomentations.RoomSimulator` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 48 | `__init__` | 2 | 0 | ❌ |
| 52 | `process` | 7 | 1 | ❌ |
| 62 | `__init__` | 5 | 0 | ❌ |
| 70 | `__init__` | 7 | 0 | ❌ |
| 79 | `process` | 7 | 1 | ❌ |
| 20 | `__init__` | 1 | 0 | ❌ |
| 24 | `__init__` | 1 | 1 | ❌ |
| 27 | `__call__` | 1 | 0 | ❌ |
| 39 | `__init__` | 1 | 1 | ❌ |
| 42 | `__call__` | 1 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 47 | `PedalboardPlugin` | ❌ |
| 61 | `PhonkDistortion` | ❌ |
| 69 | `AntiAINeuroObfuscator` | ❌ |
| 19 | `_NoopFx` | ❌ |
| 23 | `Pedalboard` | ❌ |
| 38 | `Compose` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 5 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 47** — public class 'PedalboardPlugin' без docstring

  ```
         45 |     PitchShift = TimeStretch = AddGaussianNoise = RoomSimulator = object  # type: ignore
         46 | 
  >>>    47 | class PedalboardPlugin(AudioPlugin):
         48 |     def __init__(self, name: str, effects: list):
         49 |         super().__init__(name)
  ```

- **строка 61** — public class 'PhonkDistortion' без docstring

  ```
         59 |             return self.board(audio, sr)
         60 | 
  >>>    61 | class PhonkDistortion(PedalboardPlugin):
         62 |     def __init__(self, drive_db: float = 20.0):
         63 |         super().__init__("PhonkDistortion", [
  ```

- **строка 69** — public class 'AntiAINeuroObfuscator' без docstring

  ```
         67 |         ])
         68 | 
  >>>    69 | class AntiAINeuroObfuscator(AudioPlugin):
         70 |     def __init__(self, intensity: float = 0.5):
         71 |         super().__init__("AntiAINeuroObfuscator")
  ```

- **строка 23** — public class 'Pedalboard' без docstring

  ```
         21 |             pass
         22 | 
  >>>    23 |     class Pedalboard:  # type: ignore
         24 |         def __init__(self, effects=None):
         25 |             self.effects = effects or []
  ```

- **строка 38** — public class 'Compose' без docstring

  ```
         36 |     _HAS_AUG = False
         37 | 
  >>>    38 |     class Compose:  # type: ignore
         39 |         def __init__(self, transforms=None):
         40 |             self.transforms = transforms or []
  ```
