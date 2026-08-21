# АУДИТ ФАЙЛА: `tools/readiness.py`

**LOC:** 283  |  **Размер:** 9449 байт  |  **Проблем:** 9  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 7 | `__future__.annotations` | from |
| 9 | `json` | import |
| 10 | `math` | import |
| 11 | `sys` | import |
| 12 | `pathlib.Path` | from |
| 13 | `typing.Any` | from |
| 165 | `modules.voice_recording` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 46 | `_module_exists` | 5 | 1 | ❌ |
| 54 | `_file_exists` | 1 | 0 | ❌ |
| 58 | `probe_architecture` | 20 | 1 | ❌ |
| 81 | `probe_core_modules` | 28 | 0 | ❌ |
| 112 | `probe_audio_pipeline` | 36 | 8 | ❌ |
| 151 | `probe_voice_rvc` | 22 | 1 | ❌ |
| 176 | `probe_release` | 13 | 1 | ❌ |
| 192 | `probe_installer` | 8 | 0 | ❌ |
| 203 | `probe_testing` | 12 | 0 | ❌ |
| 218 | `_block_percent` | 5 | 1 | ❌ |
| 226 | `compute` | 47 | 7 | ❌ |
| 276 | `main` | 3 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 7 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 58** — public function 'probe_architecture' без docstring

  ```
         56 | 
         57 | 
  >>>    58 | def probe_architecture() -> dict[str, str]:
         59 |     p: dict[str, str] = {}
         60 |     stray = list((ROOT).glob("main_v*.py"))
  ```

- **строка 81** — public function 'probe_core_modules' без docstring

  ```
         79 | 
         80 | 
  >>>    81 | def probe_core_modules() -> dict[str, str]:
         82 |     p: dict[str, str] = {}
         83 |     p["analyzer"] = "REAL_PASS" if _module_exists("modules.analyzer") else "MISSING"
  ```

- **строка 112** — public function 'probe_audio_pipeline' без docstring

  ```
        110 | 
        111 | 
  >>>   112 | def probe_audio_pipeline() -> dict[str, str]:
        113 |     p: dict[str, str] = {}
        114 |     try:
  ```

- **строка 151** — public function 'probe_voice_rvc' без docstring

  ```
        149 | 
        150 | 
  >>>   151 | def probe_voice_rvc() -> dict[str, str]:
        152 |     p: dict[str, str] = {}
        153 |     p["voice_recording"] = (
  ```

- **строка 176** — public function 'probe_release' без docstring

  ```
        174 | 
        175 | 
  >>>   176 | def probe_release() -> dict[str, str]:
        177 |     p: dict[str, str] = {}
        178 |     p["release_pack_module"] = (
  ```

- **строка 203** — public function 'probe_testing' без docstring

  ```
        201 | 
        202 | 
  >>>   203 | def probe_testing() -> dict[str, str]:
        204 |     p: dict[str, str] = {}
        205 |     p["smoke_v14"] = "REAL_PASS" if _file_exists("tools/smoke_v14.py") else "MISSING"
  ```

- **строка 226** — public function 'compute' без docstring

  ```
        224 | 
        225 | 
  >>>   226 | def compute() -> tuple[float, dict[str, Any]]:
        227 |     blocks_raw = {
        228 |         "architecture": probe_architecture(),
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 7** — import 'annotations' не используется в теле файла

  ```
          5 | """
          6 | 
  >>>     7 | from __future__ import annotations
          8 | 
          9 | import json
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 278** — print() вместо logger

  ```
        276 | def main() -> int:
        277 |     pct, blocks = compute()
  >>>   278 |     print(json.dumps({"percent": pct, "blocks": blocks}, ensure_ascii=False, indent=2))
        279 |     return 0
        280 | 
  ```
