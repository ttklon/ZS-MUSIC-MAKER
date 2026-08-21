# grep-таблицы `tools/lazy_dirs_patch.py`

## `import` — 2 совпадений
```
   11 | import re
   12 | from pathlib import Path
```

## `print` — 4 совпадений
```
  157 |             print(f"  [SKIP] {fname} not found")
  166 |             print(f"  [OK] {fname}")
  168 |             print(f"  [NOOP] {fname}")
  169 |     print(f"\nTotal modified: {len(modified)}")
```

## `def` — 1 совпадений
```
  152 | def main():
```

## `raise` — 1 совпадений
```
  174 |     raise SystemExit(main())
```

## `return` — 1 совпадений
```
  170 |     return 0
```

## `if` — 3 совпадений
```
  156 |         if not p.exists():
  163 |         if src != orig:
  173 | if __name__ == "__main__":
```

## `for` — 2 совпадений
```
  154 |     for fname, rules in PATCHES.items():
  161 |         for pattern, replacement in rules:
```
