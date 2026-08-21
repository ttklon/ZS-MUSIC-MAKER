# АУДИТ ФАЙЛА: `agents/sample_hunter_v9.py`

**LOC:** 367  |  **Размер:** 12146 байт  |  **Проблем:** 11  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 26 | `__future__.annotations` | from |
| 28 | `json` | import |
| 29 | `re` | import |
| 30 | `time` | import |
| 31 | `pathlib.Path` | from |
| 32 | `urllib.parse.quote_plus` | from |
| 35 | `requests` | import |
| 282 | `app.core.license_manager.is_free_commercial` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 111 | `plan_queries` | 10 | 4 | ❌ |
| 128 | `list_local` | 17 | 4 | ❌ |
| 149 | `_http_get` | 11 | 3 | ❌ |
| 163 | `search_freesound_web` | 25 | 3 | ✅ |
| 191 | `search_wikimedia` | 33 | 5 | ❌ |
| 227 | `search_archive_org` | 37 | 5 | ❌ |
| 269 | `_license_gate` | 30 | 4 | ✅ |
| 302 | `search_online` | 21 | 6 | ❌ |
| 326 | `unified_search` | 17 | 2 | ❌ |
| 346 | `save_manifest` | 11 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 6 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 128** — public function 'list_local' без docstring

  ```
        126 | 
        127 | 
  >>>   128 | def list_local(subdir: str = "") -> list[dict]:
        129 |     root = LOCAL_LIB / subdir if subdir else LOCAL_LIB
        130 |     if not root.exists():
  ```

- **строка 191** — public function 'search_wikimedia' без docstring

  ```
        189 | 
        190 | 
  >>>   191 | def search_wikimedia(query: str, limit: int = 5) -> list[dict]:
        192 |     if not HAS_REQ:
        193 |         return []
  ```

- **строка 227** — public function 'search_archive_org' без docstring

  ```
        225 | 
        226 | 
  >>>   227 | def search_archive_org(query: str, limit: int = 5) -> list[dict]:
        228 |     if not HAS_REQ:
        229 |         return []
  ```

- **строка 302** — public function 'search_online' без docstring

  ```
        300 | 
        301 | 
  >>>   302 | def search_online(
        303 |     style_vector: dict, max_per_source: int = 5, max_total: int = 40
        304 | ) -> list[dict]:
  ```

- **строка 326** — public function 'unified_search' без docstring

  ```
        324 | 
        325 | 
  >>>   326 | def unified_search(
        327 |     style_vector: dict,
        328 |     include_local: bool = True,
  ```

- **строка 346** — public function 'save_manifest' без docstring

  ```
        344 | 
        345 | 
  >>>   346 | def save_manifest(items: list[dict], project_id: str) -> str:
        347 |     path = MANIFEST_DIR / f"{project_id}_samples.json"
        348 |     payload = {
  ```

### BARE_PRINT — 4 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 297** — print() вместо logger

  ```
        295 |             it["license_blocked"] = True
        296 |             it["license_reason"] = f"blocked by license gate: {lic}"
  >>>   297 |             print(f"[sample_hunter_v9] BLOCKED non-free sample: "
        298 |                   f"{it.get('name','?')[:60]} ({lic})")
        299 |     return out
  ```

- **строка 364** — print() вместо logger

  ```
        362 |     sv = {"bpm": 132, "genre_hint": "phonk / drift"}
        363 |     q = plan_queries(sv)
  >>>   364 |     print("PLAN:", q)
        365 |     local = list_local()
        366 |     print(f"LOCAL: {len(local)} files")
  ```

- **строка 366** — print() вместо logger

  ```
        364 |     print("PLAN:", q)
        365 |     local = list_local()
  >>>   366 |     print(f"LOCAL: {len(local)} files")
        367 |     print(f"HAS_REQ: {HAS_REQ}")
  ```

- **строка 367** — print() вместо logger

  ```
        365 |     local = list_local()
        366 |     print(f"LOCAL: {len(local)} files")
  >>>   367 |     print(f"HAS_REQ: {HAS_REQ}")
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 26** — import 'annotations' не используется в теле файла

  ```
         24 | """
         25 | 
  >>>    26 | from __future__ import annotations
         27 | 
         28 | import json
  ```
