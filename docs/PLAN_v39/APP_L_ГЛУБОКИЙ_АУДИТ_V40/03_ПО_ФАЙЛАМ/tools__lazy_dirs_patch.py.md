# АУДИТ ФАЙЛА: `tools/lazy_dirs_patch.py`

**LOC:** 174  |  **Размер:** 5987 байт  |  **Проблем:** 5  |  **Risk score:** 0

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 11 | `re` | import |
| 12 | `pathlib.Path` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 152 | `main` | 18 | 4 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 4 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 157** — print() вместо logger

  ```
        155 |         p = MODS / fname
        156 |         if not p.exists():
  >>>   157 |             print(f"  [SKIP] {fname} not found")
        158 |             continue
        159 |         src = p.read_text(encoding="utf-8")
  ```

- **строка 166** — print() вместо logger

  ```
        164 |             p.write_text(src, encoding="utf-8")
        165 |             modified.append(fname)
  >>>   166 |             print(f"  [OK] {fname}")
        167 |         else:
        168 |             print(f"  [NOOP] {fname}")
  ```

- **строка 168** — print() вместо logger

  ```
        166 |             print(f"  [OK] {fname}")
        167 |         else:
  >>>   168 |             print(f"  [NOOP] {fname}")
        169 |     print(f"\nTotal modified: {len(modified)}")
        170 |     return 0
  ```

- **строка 169** — print() вместо logger

  ```
        167 |         else:
        168 |             print(f"  [NOOP] {fname}")
  >>>   169 |     print(f"\nTotal modified: {len(modified)}")
        170 |     return 0
        171 | 
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 152** — public function 'main' без docstring

  ```
        150 | 
        151 | 
  >>>   152 | def main():
        153 |     modified = []
        154 |     for fname, rules in PATCHES.items():
  ```
