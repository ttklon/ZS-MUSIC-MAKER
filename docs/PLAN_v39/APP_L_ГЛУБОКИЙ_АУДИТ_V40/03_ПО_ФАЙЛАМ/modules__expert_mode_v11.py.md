# АУДИТ ФАЙЛА: `modules/expert_mode_v11.py`

**LOC:** 324  |  **Размер:** 9966 байт  |  **Проблем:** 15  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 8 | `__future__.annotations` | from |
| 10 | `json` | import |
| 11 | `os` | import |
| 12 | `sys` | import |
| 13 | `dataclasses.asdict` | from |
| 13 | `dataclasses.dataclass` | from |
| 13 | `dataclasses.field` | from |
| 13 | `dataclasses.fields` | from |
| 14 | `typing.Any` | from |
| 290 | `tempfile` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 17 | `_safe_print` | 4 | 1 | ❌ |
| 196 | `validate` | 27 | 13 | ❌ |
| 226 | `preset_default` | 1 | 0 | ❌ |
| 230 | `preset_phonk_car` | 10 | 0 | ❌ |
| 243 | `preset_hyperpop_tiktok` | 10 | 0 | ❌ |
| 256 | `preset_trap_summer` | 8 | 0 | ❌ |
| 275 | `apply_preset` | 2 | 0 | ❌ |
| 280 | `merge_with_wizard_state` | 6 | 1 | ❌ |
| 289 | `_self_test` | 31 | 1 | ❌ |
| 138 | `to_flat_dict` | 17 | 2 | ❌ |
| 157 | `to_dict` | 1 | 0 | ❌ |
| 160 | `save` | 4 | 2 | ❌ |
| 167 | `load` | 2 | 1 | ❌ |
| 172 | `from_dict` | 21 | 3 | ❌ |
| 173 | `_build` | 7 | 3 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 25 | `ExpertBeat` | ❌ |
| 37 | `ExpertLyrics` | ❌ |
| 53 | `ExpertVoice` | ❌ |
| 68 | `ExpertMix` | ❌ |
| 80 | `ExpertMaster` | ❌ |
| 91 | `ExpertMusicGen` | ❌ |
| 102 | `ExpertAntiNeuro` | ❌ |
| 112 | `ExpertRender` | ❌ |
| 126 | `ExpertConfig` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 9 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 25** — public class 'ExpertBeat' без docstring

  ```
         23 | 
         24 | @dataclass
  >>>    25 | class ExpertBeat:
         26 |     bpm_override: float | None = None
         27 |     swing_percent: float = 15.0
  ```

- **строка 37** — public class 'ExpertLyrics' без docstring

  ```
         35 | 
         36 | @dataclass
  >>>    37 | class ExpertLyrics:
         38 |     llm_temperature: float = 0.85
         39 |     llm_top_p: float = 0.92
  ```

- **строка 53** — public class 'ExpertVoice' без docstring

  ```
         51 | 
         52 | @dataclass
  >>>    53 | class ExpertVoice:
         54 |     mode: str = "rap"
         55 |     tts_engine: str = "silero"
  ```

- **строка 68** — public class 'ExpertMix' без docstring

  ```
         66 | 
         67 | @dataclass
  >>>    68 | class ExpertMix:
         69 |     eq_low_db: float = 0.0
         70 |     eq_mid_db: float = 0.0
  ```

- **строка 80** — public class 'ExpertMaster' без docstring

  ```
         78 | 
         79 | @dataclass
  >>>    80 | class ExpertMaster:
         81 |     target_lufs: float = -9.0
         82 |     stand_car_lufs: float = -8.5
  ```

- **строка 91** — public class 'ExpertMusicGen' без docstring

  ```
         89 | 
         90 | @dataclass
  >>>    91 | class ExpertMusicGen:
         92 |     variant: str = "auto"
         93 |     duration_sec: float = 8.0
  ```

- **строка 102** — public class 'ExpertAntiNeuro' без docstring

  ```
        100 | 
        101 | @dataclass
  >>>   102 | class ExpertAntiNeuro:
        103 |     preset: str = "standard"
        104 |     timing_jitter_ms: int = 10
  ```

- **строка 112** — public class 'ExpertRender' без docstring

  ```
        110 | 
        111 | @dataclass
  >>>   112 | class ExpertRender:
        113 |     length_sec: int = 150
        114 |     quality_mode: str = "quality"
  ```

- **строка 126** — public class 'ExpertConfig' без docstring

  ```
        124 | 
        125 | @dataclass
  >>>   126 | class ExpertConfig:
        127 |     enabled: bool = False
        128 |     version: str = "v11"
  ```

### MISSING_DOCSTRING — 3 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 196** — public function 'validate' без docstring

  ```
        194 | 
        195 | 
  >>>   196 | def validate(cfg):
        197 |     errors, warnings = [], []
        198 |     if cfg.render.length_sec < 60:
  ```

- **строка 138** — public function 'to_flat_dict' без docstring

  ```
        136 |     render: ExpertRender = field(default_factory=ExpertRender)
        137 | 
  >>>   138 |     def to_flat_dict(self) -> dict[str, Any]:
        139 |         out: dict[str, Any] = {
        140 |             "expert_mode_enabled": self.enabled,
  ```

- **строка 172** — public function 'from_dict' без docstring

  ```
        170 | 
        171 |     @classmethod
  >>>   172 |     def from_dict(cls, raw):
        173 |         def _build(dc_cls, data):
        174 |             if not isinstance(data, dict):
  ```

### BARE_PRINT — 2 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 19** — print() вместо logger

  ```
         17 | def _safe_print(msg):
         18 |     try:
  >>>    19 |         print(msg)
         20 |     except UnicodeEncodeError:
         21 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
  ```

- **строка 324** — print() вместо logger

  ```
        322 | 
        323 | if __name__ == "__main__":
  >>>   324 |     print("expert_mode_v11 self-test:", "OK" if _self_test() else "FAIL")
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 8** — import 'annotations' не используется в теле файла

  ```
          6 | """
          7 | 
  >>>     8 | from __future__ import annotations
          9 | 
         10 | import json
  ```
