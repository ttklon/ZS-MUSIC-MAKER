# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/deep_audit_v40_expand.py`

**Всего строк:** 261

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 131 | 50.2 |
| branch | 32 | 12.3 |
| return | 28 | 10.7 |
| blank | 24 | 9.2 |
| try_block | 16 | 6.1 |
| loop | 11 | 4.2 |
| def | 9 | 3.4 |
| import | 6 | 2.3 |
| comment | 2 | 0.8 |
| docstring | 2 | 0.8 |

## Полный листинг с классификацией
```
    1 [comment   ] #!/usr/bin/env python3
    2 [comment   ] # -*- coding: utf-8 -*-
    3 [docstring ] """tools/deep_audit_v40_expand.py — раздувание отчёта РЕАЛЬНЫМИ данными."""
    4 [import    ] from __future__ import annotations
    5 [blank     ] 
    6 [import    ] import ast
    7 [import    ] import re
    8 [import    ] import subprocess
    9 [import    ] from collections import Counter
   10 [import    ] from pathlib import Path
   11 [blank     ] 
   12 [code      ] ROOT = Path(__file__).resolve().parents[1]
   13 [code      ] OUT = ROOT / "docs" / "PLAN_v39" / "APP_L_ГЛУБОКИЙ_АУДИТ_V40"
   14 [code      ] DEEP = OUT / "10_ПОСТРОЧНЫЙ_ЛИСТИНГ"
   15 [code      ] DEEP.mkdir(exist_ok=True, parents=True)
   16 [code      ] AST_DIR = OUT / "11_AST_ДАМП"
   17 [code      ] AST_DIR.mkdir(exist_ok=True, parents=True)
   18 [code      ] IDENT_DIR = OUT / "12_ИДЕНТИФИКАТОРЫ"
   19 [code      ] IDENT_DIR.mkdir(exist_ok=True, parents=True)
   20 [code      ] GITLOG_DIR = OUT / "13_ИСТОРИЯ_КОММИТОВ"
   21 [code      ] GITLOG_DIR.mkdir(exist_ok=True, parents=True)
   22 [code      ] GREP_DIR = OUT / "14_GREP_ТАБЛИЦЫ"
   23 [code      ] GREP_DIR.mkdir(exist_ok=True, parents=True)
   24 [blank     ] 
   25 [blank     ] 
   26 [def       ] def all_py():
   27 [code      ]     out = []
   28 [loop      ]     for p in ROOT.rglob("*.py"):
   29 [branch    ]         if ".git" in p.parts or "__pycache__" in p.parts:
   30 [code      ]             continue
   31 [code      ]         out.append(p)
   32 [return    ]     return sorted(out)
   33 [blank     ] 
   34 [blank     ] 
   35 [def       ] def classify_line(line: str, in_docstring: bool) -> str:
   36 [code      ]     stripped = line.rstrip("\n").strip()
   37 [branch    ]     if not stripped:
   38 [return    ]         return "blank"
   39 [branch    ]     if in_docstring:
   40 [return    ]         return "docstring"
   41 [branch    ]     if stripped.startswith("#"):
   42 [return    ]         return "comment"
   43 [branch    ]     if stripped.startswith(("import ", "from ")):
   44 [return    ]         return "import"
   45 [branch    ]     if stripped.startswith("def "):
   46 [return    ]         return "def"
   47 [branch    ]     if stripped.startswith("async def "):
   48 [return    ]         return "async_def"
   49 [branch    ]     if stripped.startswith("class "):
   50 [return    ]         return "class"
   51 [branch    ]     if stripped.startswith("@"):
   52 [return    ]         return "decorator"
   53 [branch    ]     if stripped.startswith(("return ", "return")):
   54 [return    ]         return "return"
   55 [branch    ]     if stripped.startswith(("raise ", "raise")):
   56 [return    ]         return "raise"
   57 [branch    ]     if stripped.startswith(("if ", "elif ", "else:")):
   58 [return    ]         return "branch"
   59 [branch    ]     if stripped.startswith(("for ", "while ")):
   60 [return    ]         return "loop"
   61 [branch    ]     if stripped.startswith(("try:", "except", "finally:")):
   62 [return    ]         return "try_block"
   63 [branch    ]     if stripped.startswith(("with ", "assert ")):
   64 [return    ]         return "stmt"
   65 [return    ]     return "code"
   66 [blank     ] 
   67 [blank     ] 
   68 [def       ] def per_file_listing(p: Path) -> str:
   69 [try_block ]     try:
   70 [code      ]         text = p.read_text(encoding="utf-8")
   71 [try_block ]     except Exception:
   72 [try_block ]         try:
   73 [code      ]             text = p.read_text(encoding="cp1251")
   74 [try_block ]         except Exception:
   75 [return    ]             return ""
   76 [code      ]     lines = text.splitlines()
   77 [code      ]     rel = p.relative_to(ROOT).as_posix()
   78 [code      ]     docs_ranges = set()
   79 [code      ]     in_doc = False
   80 [code      ]     doc_start_line = 0
   81 [loop      ]     for i, ln in enumerate(lines, 1):
   82 [docstring ]         n_triple = ln.count('"""') + ln.count("'''")
   83 [branch    ]         if n_triple:
   84 [branch    ]             if not in_doc:
   85 [code      ]                 in_doc = True
   86 [code      ]                 doc_start_line = i
   87 [branch    ]                 if n_triple >= 2:
   88 [code      ]                     docs_ranges.add(i)
   89 [code      ]                     in_doc = False
   90 [branch    ]             else:
   91 [loop      ]                 for j in range(doc_start_line, i + 1):
   92 [code      ]                     docs_ranges.add(j)
   93 [code      ]                 in_doc = False
   94 [branch    ]         elif in_doc:
   95 [code      ]             docs_ranges.add(i)
   96 [blank     ] 
   97 [code      ]     class_cnt = Counter()
   98 [code      ]     per_line_kind = []
   99 [loop      ]     for i, ln in enumerate(lines, 1):
  100 [code      ]         kind = classify_line(ln, i in docs_ranges)
  101 [code      ]         class_cnt[kind] += 1
  102 [code      ]         per_line_kind.append(kind)
  103 [blank     ] 
  104 [code      ]     out = [f"# ПОСТРОЧНЫЙ ЛИСТИНГ: `{rel}`", "",
  105 [code      ]            f"**Всего строк:** {len(lines)}", "", "## Классификация строк",
  106 [code      ]            "| Тип | Кол-во | % |", "|-----|-------:|--:|"]
  107 [code      ]     total = max(1, len(lines))
  108 [loop      ]     for k, v in class_cnt.most_common():
  109 [code      ]         out.append(f"| {k} | {v} | {100*v/total:.1f} |")
  110 [code      ]     out.append("")
  111 [code      ]     out.append("## Полный листинг с классификацией")
  112 [code      ]     out.append("```")
  113 [loop      ]     for i, (ln, kind) in enumerate(zip(lines, per_line_kind), 1):
  114 [code      ]         out.append(f"{i:5d} [{kind:10s}] {ln}")
  115 [code      ]     out.append("```")
  116 [return    ]     return "\n".join(out)
  117 [blank     ] 
  118 [blank     ] 
  119 [def       ] def per_file_ast(p: Path) -> str:
  120 [try_block ]     try:
  121 [code      ]         text = p.read_text(encoding="utf-8")
  122 [try_block ]     except Exception:
  123 [return    ]         return ""
  124 [code      ]     rel = p.relative_to(ROOT).as_posix()
  125 [try_block ]     try:
  126 [code      ]         tree = ast.parse(text)
  127 [try_block ]     except Exception as e:
  128 [return    ]         return f"# AST-дамп `{rel}`\n\nОШИБКА ПАРСИНГА: {e}\n"
  129 [code      ]     dump = ast.dump(tree, annotate_fields=True, include_attributes=True, indent=2)
  130 [return    ]     return f"# AST-дамп `{rel}`\n\n```\n{dump}\n```\n"
  131 [blank     ] 
  132 [blank     ] 
  133 [def       ] def per_file_identifiers(p: Path) -> str:
  134 [try_block ]     try:
  135 [code      ]         text = p.read_text(encoding="utf-8")
  136 [try_block ]     except Exception:
  137 [return    ]         return ""
  138 [code      ]     rel = p.relative_to(ROOT).as_posix()
  139 [try_block ]     try:
  140 [code      ]         tree = ast.parse(text)
  141 [try_block ]     except Exception:
  142 [return    ]         return f"# Идентификаторы `{rel}`\n\nОшибка парсинга.\n"
  143 [code      ]     names, calls, strings, numbers, attrs = (Counter() for _ in range(5))
  144 [loop      ]     for node in ast.walk(tree):
  145 [branch    ]         if isinstance(node, ast.Name):
  146 [code      ]             names[node.id] += 1
  147 [branch    ]         elif isinstance(node, ast.Attribute):
  148 [code      ]             attrs[node.attr] += 1
  149 [branch    ]         elif isinstance(node, ast.Call):
  150 [code      ]             fn = node.func
  151 [branch    ]             if isinstance(fn, ast.Name):
  152 [code      ]                 calls[fn.id] += 1
  153 [branch    ]             elif isinstance(fn, ast.Attribute):
  154 [code      ]                 calls[fn.attr] += 1
  155 [branch    ]         elif isinstance(node, ast.Constant):
  156 [branch    ]             if isinstance(node.value, str):
  157 [branch    ]                 if len(node.value) <= 120:
  158 [code      ]                     strings[node.value] += 1
  159 [branch    ]             elif isinstance(node.value, (int, float)):
  160 [code      ]                 numbers[str(node.value)] += 1
  161 [blank     ] 
  162 [def       ]     def dump_counter(title, c):
  163 [code      ]         L = [f"## {title} (уникальных: {len(c)})", "",
  164 [code      ]              "| Имя | Использований |", "|-----|--------------:|"]
  165 [loop      ]         for k, v in c.most_common():
  166 [code      ]             safe = k.replace("|", "\\|").replace("\n", "\\n")
  167 [code      ]             L.append(f"| `{safe[:120]}` | {v} |")
  168 [return    ]         return "\n".join(L)
  169 [blank     ] 
  170 [code      ]     out = [f"# Идентификаторы `{rel}`", ""]
  171 [code      ]     out.append(dump_counter("Имена (ast.Name)", names))
  172 [code      ]     out.append("")
  173 [code      ]     out.append(dump_counter("Вызванные функции/методы (ast.Call)", calls))
  174 [code      ]     out.append("")
  175 [code      ]     out.append(dump_counter("Обращения к атрибутам (.attr)", attrs))
  176 [code      ]     out.append("")
  177 [code      ]     out.append(dump_counter("Строковые литералы", strings))
  178 [code      ]     out.append("")
  179 [code      ]     out.append(dump_counter("Числовые литералы", numbers))
  180 [return    ]     return "\n".join(out)
  181 [blank     ] 
  182 [blank     ] 
  183 [def       ] def per_file_gitlog(p: Path) -> str:
  184 [code      ]     rel = p.relative_to(ROOT).as_posix()
  185 [try_block ]     try:
  186 [code      ]         log = subprocess.check_output(
  187 [code      ]             ["git", "-C", str(ROOT), "log", "--follow",
  188 [code      ]              "--pretty=format:%h %ad %s", "--date=short", "--", rel],
  189 [code      ]             stderr=subprocess.DEVNULL, timeout=10,
  190 [code      ]         ).decode("utf-8", errors="replace")
  191 [try_block ]     except Exception as e:
  192 [code      ]         log = f"(git log недоступен: {e})"
  193 [return    ]     return f"# История коммитов `{rel}`\n\n```\n{log}\n```\n"
  194 [blank     ] 
  195 [blank     ] 
  196 [def       ] def per_file_grep(p: Path) -> str:
  197 [try_block ]     try:
  198 [code      ]         text = p.read_text(encoding="utf-8")
  199 [try_block ]     except Exception:
  200 [return    ]         return ""
  201 [code      ]     rel = p.relative_to(ROOT).as_posix()
  202 [code      ]     lines = text.splitlines()
  203 [code      ]     patterns = {
  204 [code      ]         "import": re.compile(r"^\s*(import\s|from\s)"),
  205 [code      ]         "print": re.compile(r"\bprint\("),
  206 [code      ]         "except": re.compile(r"^\s*except\b"),
  207 [code      ]         "try": re.compile(r"^\s*try:"),
  208 [code      ]         "def": re.compile(r"^\s*(async\s+)?def\s"),
  209 [code      ]         "class": re.compile(r"^\s*class\s"),
  210 [code      ]         "raise": re.compile(r"\braise\b"),
  211 [code      ]         "return": re.compile(r"^\s*return\b"),
  212 [code      ]         "if": re.compile(r"^\s*if\b"),
  213 [code      ]         "for": re.compile(r"^\s*for\b"),
  214 [code      ]         "while": re.compile(r"^\s*while\b"),
  215 [code      ]         "with": re.compile(r"^\s*with\b"),
  216 [code      ]         "assert": re.compile(r"^\s*assert\b"),
  217 [code      ]         "todo": re.compile(r"TODO|FIXME|HACK|XXX|BUG", re.I),
  218 [code      ]         "path_C": re.compile(r"[A-Za-z]:\\\\"),
  219 [code      ]         "path_home": re.compile(r"/home/|/Users/|/tmp/"),
  220 [code      ]         "sleep": re.compile(r"\btime\.sleep\("),
  221 [code      ]         "requests": re.compile(r"\brequests\."),
  222 [code      ]         "subprocess": re.compile(r"\bsubprocess\."),
  223 [code      ]         "os_system": re.compile(r"\bos\.system\("),
  224 [code      ]         "eval": re.compile(r"\beval\("),
  225 [code      ]         "exec": re.compile(r"\bexec\("),
  226 [code      ]         "open": re.compile(r"\bopen\("),
  227 [code      ]         "np": re.compile(r"\bnp\."),
  228 [code      ]         "sf": re.compile(r"\bsf\."),
  229 [code      ]     }
  230 [code      ]     out = [f"# grep-таблицы `{rel}`", ""]
  231 [loop      ]     for name, pat in patterns.items():
  232 [code      ]         matches = [(i, ln) for i, ln in enumerate(lines, 1) if pat.search(ln)]
  233 [branch    ]         if not matches:
  234 [code      ]             continue
  235 [code      ]         out.append(f"## `{name}` — {len(matches)} совпадений")
  236 [code      ]         out.append("```")
  237 [loop      ]         for i, ln in matches:
  238 [code      ]             out.append(f"{i:5d} | {ln.rstrip()}")
  239 [code      ]         out.append("```")
  240 [code      ]         out.append("")
  241 [return    ]     return "\n".join(out)
  242 [blank     ] 
  243 [blank     ] 
  244 [def       ] def main():
  245 [code      ]     files = all_py()
  246 [code      ]     print(f"Total files: {len(files)}")
  247 [loop      ]     for i, p in enumerate(files, 1):
  248 [code      ]         rel = p.relative_to(ROOT).as_posix()
  249 [code      ]         safe = rel.replace("/", "__").replace("\\", "__")
  250 [code      ]         (DEEP / (safe + ".md")).write_text(per_file_listing(p), encoding="utf-8")
  251 [code      ]         (AST_DIR / (safe + ".md")).write_text(per_file_ast(p), encoding="utf-8")
  252 [code      ]         (IDENT_DIR / (safe + ".md")).write_text(per_file_identifiers(p), encoding="utf-8")
  253 [code      ]         (GITLOG_DIR / (safe + ".md")).write_text(per_file_gitlog(p), encoding="utf-8")
  254 [code      ]         (GREP_DIR / (safe + ".md")).write_text(per_file_grep(p), encoding="utf-8")
  255 [branch    ]         if i % 30 == 0:
  256 [code      ]             print(f"  processed {i}/{len(files)}")
  257 [code      ]     print("Done.")
  258 [blank     ] 
  259 [blank     ] 
  260 [branch    ] if __name__ == "__main__":
  261 [code      ]     main()
```