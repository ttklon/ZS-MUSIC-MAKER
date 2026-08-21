# grep-таблицы `tools/deep_audit_v40_report.py`

## `import` — 4 совпадений
```
    4 | from __future__ import annotations
    6 | import json
    7 | from collections import Counter, defaultdict
    8 | from pathlib import Path
```

## `print` — 3 совпадений
```
   26 |     "BARE_PRINT": "print() вместо logger",
   52 |     "BARE_PRINT": "`print(x)` → `logger.info(x)`.",
  378 |     print("Reports written to", OUT)
```

## `except` — 2 совпадений
```
   86 |     except Exception:
   90 |         except Exception:
```

## `try` — 2 совпадений
```
   83 |     try:
   87 |         try:
```

## `def` — 2 совпадений
```
   82 | def get_line(path: Path, lineno: int, ctx: int = 2) -> list[str]:
  103 | def main():
```

## `raise` — 1 совпадений
```
   55 |     "ASSERT_IN_PROD": "`if not cond: raise ValueError('...')`. assert только в тестах.",
```

## `return` — 3 совпадений
```
   91 |             return []
   93 |         return []
  100 |     return out
```

## `if` — 19 совпадений
```
   92 |     if lineno <= 0 or lineno > len(all_lines):
  165 |             if it["kind"] in crit_types:
  177 |         if ctx:
  195 |         if r["imports"]:
  205 |         if r["functions"]:
  215 |         if r["classes"]:
  236 |                 if ctx:
  256 |             if not hits:
  263 |                 if ctx:
  285 |         if kind not in stats:
  301 |         if not r["issues"]:
  311 |             if ctx:
  325 |         if not r["functions"] and not r["classes"]:
  328 |         if r["classes"]:
  332 |         if r["functions"]:
  337 |                 if fn["loc"] > 100:
  339 |                 if fn["complexity"] > 15:
  352 |         if not r["imports"]:
  381 | if __name__ == "__main__":
```

## `for` — 32 совпадений
```
   97 |     for i in range(start, end):
  132 |     for r in reports:
  135 |         for it in r["issues"]:
  145 |     for k, v in stats.most_common():
  155 |     for f, c in top:
  163 |     for r in reports:
  164 |         for it in r["issues"]:
  169 |     for f, it in crit:
  188 |     for r in reports:
  198 |             for imp in r["imports"]:
  208 |             for fn in r["functions"]:
  218 |             for cl in r["classes"]:
  226 |         for it in r["issues"]:
  228 |         for kind, items in sorted(by_kind.items(), key=lambda x: -len(x[1])):
  233 |             for it in items:
  239 |                     for c in ctx:
  248 |     for kind in stats:
  254 |         for r in reports:
  260 |             for it in hits:
  265 |                     for c in ctx:
  284 |     for kind in order:
  290 |         for r in reports:
  292 |             for it in hits:
  300 |     for r in reports:
  305 |         for it in sorted(r["issues"], key=lambda x: x.get("line", 0)):
  324 |     for r in reports:
  330 |             for cl in r["classes"]:
  334 |             for fn in r["functions"]:
  351 |     for r in reports:
  358 |         for imp in r["imports"]:
  369 |     for r in sorted(reports, key=lambda x: -len(x["issues"])):
  372 |         for k in all_kinds:
```

## `with` — 2 совпадений
```
   84 |         with open(path, encoding="utf-8") as f:
   88 |             with open(path, encoding="cp1251") as f:
```

## `todo` — 18 совпадений
```
   34 |     "MARKER_TODO": "TODO в коде — незакрытая задача",
   35 |     "MARKER_FIXME": "FIXME в коде — известная ошибка",
   36 |     "MARKER_HACK": "HACK в коде — временное решение",
   37 |     "MARKER_XXX": "XXX в коде — требуется внимание",
   38 |     "MARKER_BUG": "BUG-маркер в коде",
   45 |     "SILENT_EXCEPT_PASS": "`pass` → `logger.debug('reason=..., exc=%r', exc)`.",
   60 |     "MARKER_TODO": "Закрыть отдельным шагом.",
   61 |     "MARKER_FIXME": "Закрыть отдельным шагом.",
   62 |     "MARKER_HACK": "Закрыть отдельным шагом.",
   63 |     "MARKER_XXX": "Закрыть отдельным шагом.",
   64 |     "MARKER_BUG": "Закрыть отдельным шагом.",
   76 |     "MISSING_CLASS_DOCSTRING": "🟢 LOW", "MARKER_TODO": "🟢 LOW",
   77 |     "MARKER_FIXME": "🟠 HIGH", "MARKER_HACK": "🟡 MEDIUM",
   78 |     "MARKER_XXX": "🟡 MEDIUM", "MARKER_BUG": "🔴 CRITICAL",
  161 |                   "SECURITY_SHELL_TRUE", "MARKER_BUG", "MARKER_FIXME"}
  276 |              "SECURITY_SHELL_TRUE", "MARKER_BUG", "MARKER_FIXME",
  280 |              "ASSERT_IN_PROD", "NO_HTTP_TIMEOUT", "MARKER_HACK", "MARKER_XXX",
  282 |              "MISSING_CLASS_DOCSTRING", "MARKER_TODO"]
```

## `path_C` — 1 совпадений
```
   24 |     "HARDCODED_WIN_PATH": "Захардкоженный Windows-путь (C:\\...)",
```

## `path_home` — 1 совпадений
```
   25 |     "HARDCODED_POSIX_PATH": "Захардкоженный POSIX-путь (/home/... /Users/...)",
```

## `sleep` — 1 совпадений
```
   27 |     "BLOCKING_SLEEP": "time.sleep() без комментария/аргументации",
```

## `subprocess` — 2 совпадений
```
   31 |     "SECURITY_OS_SYSTEM": "os.system() — заменить на subprocess.run(shell=False)",
   57 |     "SECURITY_OS_SYSTEM": "`subprocess.run([...], check=True, shell=False, timeout=N)`.",
```

## `os_system` — 1 совпадений
```
   31 |     "SECURITY_OS_SYSTEM": "os.system() — заменить на subprocess.run(shell=False)",
```

## `eval` — 1 совпадений
```
   30 |     "SECURITY_EVAL": "eval()/exec() — вектор RCE",
```

## `exec` — 1 совпадений
```
   30 |     "SECURITY_EVAL": "eval()/exec() — вектор RCE",
```

## `open` — 2 совпадений
```
   84 |         with open(path, encoding="utf-8") as f:
   88 |             with open(path, encoding="cp1251") as f:
```
