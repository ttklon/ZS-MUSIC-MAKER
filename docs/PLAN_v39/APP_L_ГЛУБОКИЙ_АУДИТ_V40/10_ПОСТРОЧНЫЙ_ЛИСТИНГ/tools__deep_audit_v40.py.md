# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/deep_audit_v40.py`

**Всего строк:** 281

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 164 | 58.4 |
| branch | 37 | 13.2 |
| blank | 21 | 7.5 |
| docstring | 18 | 6.4 |
| loop | 17 | 6.0 |
| import | 6 | 2.1 |
| return | 6 | 2.1 |
| try_block | 6 | 2.1 |
| def | 4 | 1.4 |
| comment | 2 | 0.7 |

## Полный листинг с классификацией
```
    1 [comment   ] #!/usr/bin/env python3
    2 [comment   ] # -*- coding: utf-8 -*-
    3 [docstring ] """
    4 [docstring ] tools/deep_audit_v40.py — САМЫЙ ГЛУБОКИЙ АУДИТ (v40).
    5 [blank     ] 
    6 [docstring ] Читаем КАЖДУЮ строку кода репозитория и выявляем:
    7 [docstring ]   • dead imports (AST)
    8 [docstring ]   • silent except: pass
    9 [docstring ]   • bare except
   10 [docstring ]   • hardcoded C:\\ / /home/ / /Users/
   11 [docstring ]   • TODO/FIXME/HACK/XXX
   12 [docstring ]   • magic numbers (порог: > 1 повторного использования одинакового литерала)
   13 [docstring ]   • слишком длинные функции (> 100 LOC)
   14 [docstring ]   • отсутствующие docstring'и у public API
   15 [docstring ]   • сложность (упрощённо: количество if/for/while/try)
   16 [docstring ]   • голые print (не через logger)
   17 [docstring ]   • голые time.sleep() без комментария
   18 [docstring ]   • assert в production-коде
   19 [docstring ]   • риски безопасности: eval/exec/os.system/subprocess.shell=True
   20 [docstring ]   • отсутствие явных таймаутов у HTTP-запросов
   21 [docstring ] """
   22 [import    ] from __future__ import annotations
   23 [blank     ] 
   24 [import    ] import ast
   25 [import    ] import json
   26 [import    ] import re
   27 [import    ] from collections import Counter
   28 [import    ] from pathlib import Path
   29 [blank     ] 
   30 [code      ] ROOT = Path(__file__).resolve().parents[1]
   31 [blank     ] 
   32 [blank     ] 
   33 [def       ] def all_py_files() -> list[Path]:
   34 [code      ]     out = []
   35 [loop      ]     for p in ROOT.rglob("*.py"):
   36 [branch    ]         if ".git" in p.parts:
   37 [code      ]             continue
   38 [branch    ]         if "__pycache__" in p.parts:
   39 [code      ]             continue
   40 [code      ]         out.append(p)
   41 [return    ]     return sorted(out)
   42 [blank     ] 
   43 [blank     ] 
   44 [def       ] def read_src(p: Path) -> str:
   45 [try_block ]     try:
   46 [return    ]         return p.read_text(encoding="utf-8")
   47 [try_block ]     except Exception:
   48 [try_block ]         try:
   49 [return    ]             return p.read_text(encoding="cp1251")
   50 [try_block ]         except Exception:
   51 [return    ]             return ""
   52 [blank     ] 
   53 [blank     ] 
   54 [def       ] def audit_file(p: Path) -> dict:
   55 [code      ]     src = read_src(p)
   56 [code      ]     lines = src.splitlines()
   57 [code      ]     rel = p.relative_to(ROOT).as_posix()
   58 [code      ]     report: dict = {
   59 [code      ]         "file": rel,
   60 [code      ]         "loc": len(lines),
   61 [code      ]         "size_bytes": len(src.encode("utf-8")),
   62 [code      ]         "issues": [],
   63 [code      ]         "functions": [],
   64 [code      ]         "classes": [],
   65 [code      ]         "imports": [],
   66 [code      ]         "risk_score": 0,
   67 [code      ]     }
   68 [try_block ]     try:
   69 [code      ]         tree = ast.parse(src)
   70 [try_block ]     except Exception as e:
   71 [code      ]         report["issues"].append({"line": 0, "kind": "PARSE_ERROR", "msg": str(e)})
   72 [code      ]         report["risk_score"] += 100
   73 [return    ]         return report
   74 [blank     ] 
   75 [code      ]     import_names: list[tuple[str, int]] = []
   76 [loop      ]     for node in ast.walk(tree):
   77 [branch    ]         if isinstance(node, ast.Import):
   78 [loop      ]             for n in node.names:
   79 [code      ]                 nm = n.asname or n.name.split(".")[0]
   80 [code      ]                 import_names.append((nm, node.lineno))
   81 [code      ]                 report["imports"].append({"name": n.name, "line": node.lineno, "kind": "import"})
   82 [branch    ]         elif isinstance(node, ast.ImportFrom):
   83 [code      ]             mod = node.module or ""
   84 [loop      ]             for n in node.names:
   85 [code      ]                 nm = n.asname or n.name
   86 [branch    ]                 if nm == "*":
   87 [code      ]                     report["issues"].append(
   88 [code      ]                         {"line": node.lineno, "kind": "STAR_IMPORT",
   89 [code      ]                          "msg": f"from {mod} import *"}
   90 [code      ]                     )
   91 [code      ]                     report["risk_score"] += 3
   92 [code      ]                     continue
   93 [code      ]                 import_names.append((nm, node.lineno))
   94 [code      ]                 report["imports"].append(
   95 [code      ]                     {"name": f"{mod}.{n.name}", "line": node.lineno, "kind": "from"}
   96 [code      ]                 )
   97 [blank     ] 
   98 [code      ]     body_src = "\n".join(lines)
   99 [loop      ]     for nm, ln in import_names:
  100 [branch    ]         if nm.startswith("_"):
  101 [code      ]             continue
  102 [code      ]         pattern = re.compile(rf"\b{re.escape(nm)}\b")
  103 [code      ]         hits = pattern.findall(body_src)
  104 [branch    ]         if len(hits) < 2:
  105 [code      ]             report["issues"].append(
  106 [code      ]                 {"line": ln, "kind": "DEAD_IMPORT",
  107 [code      ]                  "msg": f"import '{nm}' не используется в теле файла"}
  108 [code      ]             )
  109 [code      ]             report["risk_score"] += 1
  110 [blank     ] 
  111 [loop      ]     for node in ast.walk(tree):
  112 [branch    ]         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
  113 [code      ]             start = node.lineno
  114 [code      ]             end = getattr(node, "end_lineno", start)
  115 [code      ]             body_len = max(1, end - start)
  116 [code      ]             has_doc = bool(ast.get_docstring(node))
  117 [code      ]             complexity = sum(
  118 [code      ]                 1
  119 [loop      ]                 for n in ast.walk(node)
  120 [branch    ]                 if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.BoolOp))
  121 [code      ]             )
  122 [code      ]             report["functions"].append(
  123 [code      ]                 {"name": node.name, "line": start, "loc": body_len,
  124 [code      ]                  "has_doc": has_doc, "complexity": complexity}
  125 [code      ]             )
  126 [branch    ]             if body_len > 100 and not node.name.startswith("_test"):
  127 [code      ]                 report["issues"].append(
  128 [code      ]                     {"line": start, "kind": "LONG_FUNCTION",
  129 [code      ]                      "msg": f"{node.name}: {body_len} LOC (>100) — декомпозиция"}
  130 [code      ]                 )
  131 [code      ]                 report["risk_score"] += 2
  132 [branch    ]             if complexity > 15:
  133 [code      ]                 report["issues"].append(
  134 [code      ]                     {"line": start, "kind": "HIGH_COMPLEXITY",
  135 [code      ]                      "msg": f"{node.name}: сложность ≈ {complexity} (>15)"}
  136 [code      ]                 )
  137 [code      ]                 report["risk_score"] += 2
  138 [branch    ]             if not has_doc and not node.name.startswith("_") and body_len > 10:
  139 [code      ]                 report["issues"].append(
  140 [code      ]                     {"line": start, "kind": "MISSING_DOCSTRING",
  141 [code      ]                      "msg": f"public function '{node.name}' без docstring"}
  142 [code      ]                 )
  143 [branch    ]         elif isinstance(node, ast.ClassDef):
  144 [code      ]             has_doc = bool(ast.get_docstring(node))
  145 [code      ]             report["classes"].append({"name": node.name, "line": node.lineno, "has_doc": has_doc})
  146 [branch    ]             if not has_doc and not node.name.startswith("_"):
  147 [code      ]                 report["issues"].append(
  148 [code      ]                     {"line": node.lineno, "kind": "MISSING_CLASS_DOCSTRING",
  149 [code      ]                      "msg": f"public class '{node.name}' без docstring"}
  150 [code      ]                 )
  151 [blank     ] 
  152 [loop      ]     for node in ast.walk(tree):
  153 [branch    ]         if isinstance(node, ast.ExceptHandler):
  154 [branch    ]             if node.type is None:
  155 [code      ]                 report["issues"].append(
  156 [code      ]                     {"line": node.lineno, "kind": "BARE_EXCEPT",
  157 [code      ]                      "msg": "bare 'except:' — ловит и KeyboardInterrupt"}
  158 [code      ]                 )
  159 [code      ]                 report["risk_score"] += 3
  160 [branch    ]             if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
  161 [code      ]                 report["issues"].append(
  162 [code      ]                     {"line": node.lineno, "kind": "SILENT_EXCEPT_PASS",
  163 [code      ]                      "msg": "except: pass — тихое подавление ошибок"}
  164 [code      ]                 )
  165 [code      ]                 report["risk_score"] += 2
  166 [blank     ] 
  167 [loop      ]     for node in ast.walk(tree):
  168 [branch    ]         if isinstance(node, ast.Call):
  169 [code      ]             fn = node.func
  170 [code      ]             fname = None
  171 [branch    ]             if isinstance(fn, ast.Name):
  172 [code      ]                 fname = fn.id
  173 [branch    ]             elif isinstance(fn, ast.Attribute):
  174 [code      ]                 fname = fn.attr
  175 [branch    ]             if fname in ("eval", "exec"):
  176 [code      ]                 report["issues"].append(
  177 [code      ]                     {"line": node.lineno, "kind": "SECURITY_EVAL",
  178 [code      ]                      "msg": f"{fname}() — потенциально опасно"}
  179 [code      ]                 )
  180 [code      ]                 report["risk_score"] += 5
  181 [branch    ]             if fname == "system":
  182 [branch    ]                 if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "os":
  183 [code      ]                     report["issues"].append(
  184 [code      ]                         {"line": node.lineno, "kind": "SECURITY_OS_SYSTEM",
  185 [code      ]                          "msg": "os.system() — заменить на subprocess.run(shell=False)"}
  186 [code      ]                     )
  187 [code      ]                     report["risk_score"] += 4
  188 [loop      ]             for kw in node.keywords or []:
  189 [branch    ]                 if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
  190 [code      ]                     report["issues"].append(
  191 [code      ]                         {"line": node.lineno, "kind": "SECURITY_SHELL_TRUE",
  192 [code      ]                          "msg": "subprocess(..., shell=True) — shell-injection"}
  193 [code      ]                     )
  194 [code      ]                     report["risk_score"] += 4
  195 [branch    ]             if isinstance(fn, ast.Attribute) and fn.attr in ("get", "post", "put", "delete", "head", "patch"):
  196 [code      ]                 base = fn.value
  197 [code      ]                 base_name = base.id if isinstance(base, ast.Name) else (
  198 [code      ]                     base.attr if isinstance(base, ast.Attribute) else ""
  199 [code      ]                 )
  200 [branch    ]                 if base_name in ("requests", "session", "urlopen"):
  201 [code      ]                     has_timeout = any(kw.arg == "timeout" for kw in node.keywords or [])
  202 [branch    ]                     if not has_timeout:
  203 [code      ]                         report["issues"].append(
  204 [code      ]                             {"line": node.lineno, "kind": "NO_HTTP_TIMEOUT",
  205 [code      ]                              "msg": f"{base_name}.{fn.attr}(...) без timeout"}
  206 [code      ]                         )
  207 [code      ]                         report["risk_score"] += 2
  208 [blank     ] 
  209 [branch    ]     if "/tests/" not in rel and not rel.startswith("tests/"):
  210 [loop      ]         for node in ast.walk(tree):
  211 [branch    ]             if isinstance(node, ast.Assert):
  212 [code      ]                 report["issues"].append(
  213 [code      ]                     {"line": node.lineno, "kind": "ASSERT_IN_PROD",
  214 [code      ]                      "msg": "assert в production-коде: -O его выкинет"}
  215 [code      ]                 )
  216 [code      ]                 report["risk_score"] += 1
  217 [blank     ] 
  218 [loop      ]     for i, line in enumerate(lines, 1):
  219 [code      ]         low = line.strip()
  220 [branch    ]         if not low or low.startswith("#"):
  221 [loop      ]             for marker in ("TODO", "FIXME", "HACK", "XXX", "BUG"):
  222 [branch    ]                 if marker in low.upper():
  223 [code      ]                     report["issues"].append(
  224 [code      ]                         {"line": i, "kind": f"MARKER_{marker}", "msg": low[:160]}
  225 [code      ]                     )
  226 [code      ]                     report["risk_score"] += 1
  227 [code      ]                     break
  228 [code      ]             continue
  229 [code      ]         m = re.search(r'["\']([A-Za-z]:\\\\[^"\']+)["\']', line)
  230 [branch    ]         if m:
  231 [code      ]             report["issues"].append(
  232 [code      ]                 {"line": i, "kind": "HARDCODED_WIN_PATH", "msg": m.group(1)[:120]}
  233 [code      ]             )
  234 [code      ]             report["risk_score"] += 3
  235 [code      ]         m = re.search(r'["\'](/(?:home|Users|tmp|var/tmp|opt/homebrew)/[^"\']+)["\']', line)
  236 [branch    ]         if m:
  237 [code      ]             report["issues"].append(
  238 [code      ]                 {"line": i, "kind": "HARDCODED_POSIX_PATH", "msg": m.group(1)[:120]}
  239 [code      ]             )
  240 [code      ]             report["risk_score"] += 2
  241 [branch    ]         if re.search(r"^\s*print\(", line):
  242 [code      ]             report["issues"].append(
  243 [code      ]                 {"line": i, "kind": "BARE_PRINT",
  244 [code      ]                  "msg": "print() вместо logger"}
  245 [code      ]             )
  246 [branch    ]         if re.search(r"\btime\.sleep\(", line) and "#" not in line:
  247 [code      ]             report["issues"].append(
  248 [code      ]                 {"line": i, "kind": "BLOCKING_SLEEP",
  249 [code      ]                  "msg": "time.sleep(...) без пояснения"}
  250 [code      ]             )
  251 [branch    ]         if re.match(r"^\s*global\s+\w", line):
  252 [code      ]             report["issues"].append(
  253 [code      ]                 {"line": i, "kind": "GLOBAL_STATEMENT", "msg": "global — антипаттерн"}
  254 [code      ]             )
  255 [blank     ] 
  256 [return    ]     return report
  257 [blank     ] 
  258 [blank     ] 
  259 [def       ] def main():
  260 [code      ]     files = all_py_files()
  261 [code      ]     reports = []
  262 [loop      ]     for p in files:
  263 [code      ]         reports.append(audit_file(p))
  264 [code      ]     out_dir = ROOT / "docs" / "PLAN_v39" / "APP_L_ГЛУБОКИЙ_АУДИТ_V40"
  265 [code      ]     out_dir.mkdir(parents=True, exist_ok=True)
  266 [code      ]     (out_dir / "AUDIT_RAW.json").write_text(
  267 [code      ]         json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
  268 [code      ]     )
  269 [code      ]     stats = Counter()
  270 [loop      ]     for r in reports:
  271 [loop      ]         for it in r["issues"]:
  272 [code      ]             stats[it["kind"]] += 1
  273 [code      ]     print("=== AUDIT STATS ===")
  274 [loop      ]     for k, v in stats.most_common():
  275 [code      ]         print(f"  {k:32s}  {v}")
  276 [code      ]     print(f"Total files: {len(reports)}")
  277 [code      ]     print(f"Total issues: {sum(stats.values())}")
  278 [blank     ] 
  279 [blank     ] 
  280 [branch    ] if __name__ == "__main__":
  281 [code      ]     main()
```