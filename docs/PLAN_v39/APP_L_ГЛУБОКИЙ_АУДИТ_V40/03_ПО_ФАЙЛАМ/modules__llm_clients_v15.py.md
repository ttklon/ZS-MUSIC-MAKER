# АУДИТ ФАЙЛА: `modules/llm_clients_v15.py`

**LOC:** 580  |  **Размер:** 19040 байт  |  **Проблем:** 12  |  **Risk score:** 9

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 19 | `__future__.annotations` | from |
| 21 | `base64` | import |
| 22 | `json` | import |
| 23 | `os` | import |
| 24 | `time` | import |
| 25 | `pathlib.Path` | from |
| 26 | `typing.Any` | from |
| 29 | `requests` | import |
| 36 | `cryptography.fernet.Fernet` | from |
| 37 | `cryptography.hazmat.primitives.hashes` | from |
| 38 | `cryptography.hazmat.primitives.kdf.pbkdf2.PBKDF2HMAC` | from |
| 340 | `random` | import |
| 545 | `argparse` | import |
| 387 | `socket` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 52 | `_derive_key` | 6 | 1 | ❌ |
| 61 | `save_secrets` | 7 | 1 | ❌ |
| 71 | `load_secrets` | 9 | 3 | ❌ |
| 83 | `get_keys_from_env` | 13 | 2 | ✅ |
| 127 | `call_ollama` | 39 | 3 | ❌ |
| 169 | `call_openrouter` | 40 | 4 | ❌ |
| 212 | `call_grok` | 38 | 4 | ❌ |
| 253 | `call_gemini` | 46 | 5 | ❌ |
| 326 | `local_fallback_lyrics` | 31 | 4 | ✅ |
| 544 | `_cli` | 32 | 0 | ❌ |
| 105 | `__init__` | 9 | 0 | ❌ |
| 116 | `to_dict` | 8 | 0 | ❌ |
| 366 | `__init__` | 9 | 1 | ❌ |
| 383 | `_preflight` | 26 | 3 | ❌ |
| 411 | `_try_provider` | 12 | 0 | ❌ |
| 425 | `complete` | 113 | 14 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 102 | `ProviderResult` | ❌ |
| 363 | `LLMRouter` | ✅ |

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 5 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 127** — public function 'call_ollama' без docstring

  ```
        125 | 
        126 | 
  >>>   127 | def call_ollama(
        128 |     prompt: str,
        129 |     system: str = "",
  ```

- **строка 169** — public function 'call_openrouter' без docstring

  ```
        167 | 
        168 | 
  >>>   169 | def call_openrouter(
        170 |     prompt: str,
        171 |     system: str = "",
  ```

- **строка 212** — public function 'call_grok' без docstring

  ```
        210 | 
        211 | 
  >>>   212 | def call_grok(
        213 |     prompt: str,
        214 |     system: str = "",
  ```

- **строка 253** — public function 'call_gemini' без docstring

  ```
        251 | 
        252 | 
  >>>   253 | def call_gemini(
        254 |     prompt: str,
        255 |     system: str = "",
  ```

- **строка 425** — public function 'complete' без docstring

  ```
        423 |         return r
        424 | 
  >>>   425 |     def complete(
        426 |         self,
        427 |         prompt: str,
  ```

### SILENT_EXCEPT_PASS — 3 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 286** — except: pass — тихое подавление ошибок

  ```
        284 |         try:
        285 |             text = j["candidates"][0]["content"]["parts"][0]["text"]
  >>>   286 |         except Exception:
        287 |             pass
        288 |         return ProviderResult(
  ```

- **строка 395** — except: pass — тихое подавление ошибок

  ```
        393 |             s.close()
        394 |             out["internet"] = True
  >>>   395 |         except Exception:
        396 |             pass
        397 |         try:
  ```

- **строка 406** — except: pass — тихое подавление ошибок

  ```
        404 |             s.close()
        405 |             out["ollama"] = True
  >>>   406 |         except Exception:
        407 |             pass
        408 |         LLMRouter._preflight_cache = out
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
         21 | import base64
  ```

### MISSING_CLASS_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 102** — public class 'ProviderResult' без docstring

  ```
        100 | 
        101 | 
  >>>   102 | class ProviderResult:
        103 |     __slots__ = ("error", "model", "ok", "provider", "raw", "text", "tokens")
        104 | 
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 425** — complete: 113 LOC (>100) — декомпозиция

  ```
        423 |         return r
        424 | 
  >>>   425 |     def complete(
        426 |         self,
        427 |         prompt: str,
  ```

### BARE_PRINT — 1 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 563** — print() вместо logger

  ```
        561 |         a.prompt, a.system, theme=a.theme, genre=a.genre, language=a.language
        562 |     )
  >>>   563 |     print(
        564 |         json.dumps(
        565 |             {
  ```
