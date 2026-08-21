# grep-таблицы `tools/deep_audit_v40.py`

## `import` — 6 совпадений
```
   22 | from __future__ import annotations
   24 | import ast
   25 | import json
   26 | import re
   27 | from collections import Counter
   28 | from pathlib import Path
```

## `print` — 5 совпадений
```
  244 |                  "msg": "print() вместо logger"}
  273 |     print("=== AUDIT STATS ===")
  275 |         print(f"  {k:32s}  {v}")
  276 |     print(f"Total files: {len(reports)}")
  277 |     print(f"Total issues: {sum(stats.values())}")
```

## `except` — 3 совпадений
```
   47 |     except Exception:
   50 |         except Exception:
   70 |     except Exception as e:
```

## `try` — 3 совпадений
```
   45 |     try:
   48 |         try:
   68 |     try:
```

## `def` — 4 совпадений
```
   33 | def all_py_files() -> list[Path]:
   44 | def read_src(p: Path) -> str:
   54 | def audit_file(p: Path) -> dict:
  259 | def main():
```

## `return` — 6 совпадений
```
   41 |     return sorted(out)
   46 |         return p.read_text(encoding="utf-8")
   49 |             return p.read_text(encoding="cp1251")
   51 |             return ""
   73 |         return report
  256 |     return report
```

## `if` — 34 совпадений
```
   36 |         if ".git" in p.parts:
   38 |         if "__pycache__" in p.parts:
   77 |         if isinstance(node, ast.Import):
   86 |                 if nm == "*":
  100 |         if nm.startswith("_"):
  104 |         if len(hits) < 2:
  112 |         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
  120 |                 if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.BoolOp))
  126 |             if body_len > 100 and not node.name.startswith("_test"):
  132 |             if complexity > 15:
  138 |             if not has_doc and not node.name.startswith("_") and body_len > 10:
  146 |             if not has_doc and not node.name.startswith("_"):
  153 |         if isinstance(node, ast.ExceptHandler):
  154 |             if node.type is None:
  160 |             if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
  168 |         if isinstance(node, ast.Call):
  171 |             if isinstance(fn, ast.Name):
  175 |             if fname in ("eval", "exec"):
  181 |             if fname == "system":
  182 |                 if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "os":
  189 |                 if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
  195 |             if isinstance(fn, ast.Attribute) and fn.attr in ("get", "post", "put", "delete", "head", "patch"):
  200 |                 if base_name in ("requests", "session", "urlopen"):
  202 |                     if not has_timeout:
  209 |     if "/tests/" not in rel and not rel.startswith("tests/"):
  211 |             if isinstance(node, ast.Assert):
  220 |         if not low or low.startswith("#"):
  222 |                 if marker in low.upper():
  230 |         if m:
  236 |         if m:
  241 |         if re.search(r"^\s*print\(", line):
  246 |         if re.search(r"\btime\.sleep\(", line) and "#" not in line:
  251 |         if re.match(r"^\s*global\s+\w", line):
  280 | if __name__ == "__main__":
```

## `for` — 17 совпадений
```
   35 |     for p in ROOT.rglob("*.py"):
   76 |     for node in ast.walk(tree):
   78 |             for n in node.names:
   84 |             for n in node.names:
   99 |     for nm, ln in import_names:
  111 |     for node in ast.walk(tree):
  119 |                 for n in ast.walk(node)
  152 |     for node in ast.walk(tree):
  167 |     for node in ast.walk(tree):
  188 |             for kw in node.keywords or []:
  210 |         for node in ast.walk(tree):
  218 |     for i, line in enumerate(lines, 1):
  221 |             for marker in ("TODO", "FIXME", "HACK", "XXX", "BUG"):
  262 |     for p in files:
  270 |     for r in reports:
  271 |         for it in r["issues"]:
  274 |     for k, v in stats.most_common():
```

## `todo` — 2 совпадений
```
   11 |   • TODO/FIXME/HACK/XXX
  221 |             for marker in ("TODO", "FIXME", "HACK", "XXX", "BUG"):
```

## `path_C` — 1 совпадений
```
   10 |   • hardcoded C:\\ / /home/ / /Users/
```

## `path_home` — 1 совпадений
```
   10 |   • hardcoded C:\\ / /home/ / /Users/
```

## `sleep` — 2 совпадений
```
   17 |   • голые time.sleep() без комментария
  249 |                  "msg": "time.sleep(...) без пояснения"}
```

## `subprocess` — 2 совпадений
```
   19 |   • риски безопасности: eval/exec/os.system/subprocess.shell=True
  185 |                          "msg": "os.system() — заменить на subprocess.run(shell=False)"}
```

## `os_system` — 1 совпадений
```
  185 |                          "msg": "os.system() — заменить на subprocess.run(shell=False)"}
```
