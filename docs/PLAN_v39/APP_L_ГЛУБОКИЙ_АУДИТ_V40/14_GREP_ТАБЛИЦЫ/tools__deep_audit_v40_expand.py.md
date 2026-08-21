# grep-таблицы `tools/deep_audit_v40_expand.py`

## `import` — 6 совпадений
```
    4 | from __future__ import annotations
    6 | import ast
    7 | import re
    8 | import subprocess
    9 | from collections import Counter
   10 | from pathlib import Path
```

## `print` — 3 совпадений
```
  246 |     print(f"Total files: {len(files)}")
  256 |             print(f"  processed {i}/{len(files)}")
  257 |     print("Done.")
```

## `except` — 8 совпадений
```
   71 |     except Exception:
   74 |         except Exception:
  122 |     except Exception:
  127 |     except Exception as e:
  136 |     except Exception:
  141 |     except Exception:
  191 |     except Exception as e:
  199 |     except Exception:
```

## `try` — 8 совпадений
```
   69 |     try:
   72 |         try:
  120 |     try:
  125 |     try:
  134 |     try:
  139 |     try:
  185 |     try:
  197 |     try:
```

## `def` — 9 совпадений
```
   26 | def all_py():
   35 | def classify_line(line: str, in_docstring: bool) -> str:
   68 | def per_file_listing(p: Path) -> str:
  119 | def per_file_ast(p: Path) -> str:
  133 | def per_file_identifiers(p: Path) -> str:
  162 |     def dump_counter(title, c):
  183 | def per_file_gitlog(p: Path) -> str:
  196 | def per_file_grep(p: Path) -> str:
  244 | def main():
```

## `raise` — 3 совпадений
```
   55 |     if stripped.startswith(("raise ", "raise")):
   56 |         return "raise"
  210 |         "raise": re.compile(r"\braise\b"),
```

## `return` — 28 совпадений
```
   32 |     return sorted(out)
   38 |         return "blank"
   40 |         return "docstring"
   42 |         return "comment"
   44 |         return "import"
   46 |         return "def"
   48 |         return "async_def"
   50 |         return "class"
   52 |         return "decorator"
   54 |         return "return"
   56 |         return "raise"
   58 |         return "branch"
   60 |         return "loop"
   62 |         return "try_block"
   64 |         return "stmt"
   65 |     return "code"
   75 |             return ""
  116 |     return "\n".join(out)
  123 |         return ""
  128 |         return f"# AST-дамп `{rel}`\n\nОШИБКА ПАРСИНГА: {e}\n"
  130 |     return f"# AST-дамп `{rel}`\n\n```\n{dump}\n```\n"
  137 |         return ""
  142 |         return f"# Идентификаторы `{rel}`\n\nОшибка парсинга.\n"
  168 |         return "\n".join(L)
  180 |     return "\n".join(out)
  193 |     return f"# История коммитов `{rel}`\n\n```\n{log}\n```\n"
  200 |         return ""
  241 |     return "\n".join(out)
```

## `if` — 25 совпадений
```
   29 |         if ".git" in p.parts or "__pycache__" in p.parts:
   37 |     if not stripped:
   39 |     if in_docstring:
   41 |     if stripped.startswith("#"):
   43 |     if stripped.startswith(("import ", "from ")):
   45 |     if stripped.startswith("def "):
   47 |     if stripped.startswith("async def "):
   49 |     if stripped.startswith("class "):
   51 |     if stripped.startswith("@"):
   53 |     if stripped.startswith(("return ", "return")):
   55 |     if stripped.startswith(("raise ", "raise")):
   57 |     if stripped.startswith(("if ", "elif ", "else:")):
   59 |     if stripped.startswith(("for ", "while ")):
   61 |     if stripped.startswith(("try:", "except", "finally:")):
   63 |     if stripped.startswith(("with ", "assert ")):
   83 |         if n_triple:
   84 |             if not in_doc:
   87 |                 if n_triple >= 2:
  145 |         if isinstance(node, ast.Name):
  151 |             if isinstance(fn, ast.Name):
  156 |             if isinstance(node.value, str):
  157 |                 if len(node.value) <= 120:
  233 |         if not matches:
  255 |         if i % 30 == 0:
  260 | if __name__ == "__main__":
```

## `for` — 11 совпадений
```
   28 |     for p in ROOT.rglob("*.py"):
   81 |     for i, ln in enumerate(lines, 1):
   91 |                 for j in range(doc_start_line, i + 1):
   99 |     for i, ln in enumerate(lines, 1):
  108 |     for k, v in class_cnt.most_common():
  113 |     for i, (ln, kind) in enumerate(zip(lines, per_line_kind), 1):
  144 |     for node in ast.walk(tree):
  165 |         for k, v in c.most_common():
  231 |     for name, pat in patterns.items():
  237 |         for i, ln in matches:
  247 |     for i, p in enumerate(files, 1):
```

## `todo` — 1 совпадений
```
  217 |         "todo": re.compile(r"TODO|FIXME|HACK|XXX|BUG", re.I),
```

## `path_home` — 1 совпадений
```
  219 |         "path_home": re.compile(r"/home/|/Users/|/tmp/"),
```

## `subprocess` — 2 совпадений
```
  186 |         log = subprocess.check_output(
  189 |             stderr=subprocess.DEVNULL, timeout=10,
```
