# АУДИТ ФАЙЛА: `modules/beat_gen.py`

**LOC:** 153  |  **Размер:** 4772 байт  |  **Проблем:** 5  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 11 | `math` | import |
| 12 | `os` | import |
| 36 | `audiocraft.models.MusicGen` | from |
| 71 | `audiocraft.data.audio.audio_write` | from |
| 95 | `torch` | import |
| 96 | `torchaudio` | import |
| 97 | `audiocraft.data.audio.audio_write` | from |
| 20 | `torch` | import |
| 25 | `torch_directml` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 18 | `_pick_device` | 14 | 3 | ❌ |
| 35 | `_load_model` | 12 | 0 | ❌ |
| 50 | `build_prompt` | 11 | 2 | ❌ |
| 64 | `generate_texture` | 20 | 0 | ✅ |
| 87 | `generate_beat` | 42 | 3 | ✅ |
| 132 | `generate_from_samples` | 12 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 50** — public function 'build_prompt' без docstring

  ```
         48 | 
         49 | 
  >>>    50 | def build_prompt(
         51 |     style_vector: dict, user_extra: str = "", samples_desc: str = ""
         52 | ) -> str:
  ```

- **строка 132** — public function 'generate_from_samples' без docstring

  ```
        130 | 
        131 | 
  >>>   132 | def generate_from_samples(
        133 |     sample_paths: list, style_vector: dict, duration_sec: int = 90
        134 | ) -> str:
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 25** — import 'torch_directml' не используется в теле файла

  ```
         23 |             return "cuda"
         24 |         try:
  >>>    25 |             import torch_directml  # noqa
         26 | 
         27 |             return "dml"
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 28** — except: pass — тихое подавление ошибок

  ```
         26 | 
         27 |             return "dml"
  >>>    28 |         except ImportError:
         29 |             pass
         30 |         return "cpu"
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 153** — print() вместо logger

  ```
        151 |         "vibe_tags": ["phonk/drift", "bass-heavy", "dark", "aggressive"],
        152 |     }
  >>>   153 |     print(build_prompt(demo_style, user_extra="summer, cars, istanbul"))
  ```
