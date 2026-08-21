# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/deep_audit_v40_report.py`

**Всего строк:** 382

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 280 | 73.3 |
| loop | 32 | 8.4 |
| branch | 22 | 5.8 |
| blank | 21 | 5.5 |
| comment | 11 | 2.9 |
| import | 4 | 1.0 |
| try_block | 4 | 1.0 |
| return | 3 | 0.8 |
| def | 2 | 0.5 |
| stmt | 2 | 0.5 |
| docstring | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [comment   ] #!/usr/bin/env python3
    2 [comment   ] # -*- coding: utf-8 -*-
    3 [docstring ] """tools/deep_audit_v40_report.py — детальный отчёт из AUDIT_RAW.json."""
    4 [import    ] from __future__ import annotations
    5 [blank     ] 
    6 [import    ] import json
    7 [import    ] from collections import Counter, defaultdict
    8 [import    ] from pathlib import Path
    9 [blank     ] 
   10 [code      ] ROOT = Path(__file__).resolve().parents[1]
   11 [code      ] OUT = ROOT / "docs" / "PLAN_v39" / "APP_L_ГЛУБОКИЙ_АУДИТ_V40"
   12 [code      ] RAW = OUT / "AUDIT_RAW.json"
   13 [blank     ] 
   14 [code      ] ISSUE_HUMAN = {
   15 [code      ]     "PARSE_ERROR": "Файл не парсится (SyntaxError) — блокер",
   16 [code      ]     "DEAD_IMPORT": "Мёртвый импорт (не используется в файле)",
   17 [code      ]     "STAR_IMPORT": "'from X import *' — ломает статический анализ",
   18 [code      ]     "BARE_EXCEPT": "'except:' без типа — ловит KeyboardInterrupt/SystemExit",
   19 [code      ]     "SILENT_EXCEPT_PASS": "'except ...: pass' — тихое поглощение ошибок",
   20 [code      ]     "LONG_FUNCTION": "Функция > 100 LOC — сложно тестировать/поддерживать",
   21 [code      ]     "HIGH_COMPLEXITY": "Цикломатическая сложность > 15",
   22 [code      ]     "MISSING_DOCSTRING": "Public-функция без docstring",
   23 [code      ]     "MISSING_CLASS_DOCSTRING": "Public-класс без docstring",
   24 [code      ]     "HARDCODED_WIN_PATH": "Захардкоженный Windows-путь (C:\\...)",
   25 [code      ]     "HARDCODED_POSIX_PATH": "Захардкоженный POSIX-путь (/home/... /Users/...)",
   26 [code      ]     "BARE_PRINT": "print() вместо logger",
   27 [code      ]     "BLOCKING_SLEEP": "time.sleep() без комментария/аргументации",
   28 [code      ]     "GLOBAL_STATEMENT": "global — обычно антипаттерн",
   29 [code      ]     "ASSERT_IN_PROD": "assert в production — -O его выкинет",
   30 [code      ]     "SECURITY_EVAL": "eval()/exec() — вектор RCE",
   31 [code      ]     "SECURITY_OS_SYSTEM": "os.system() — заменить на subprocess.run(shell=False)",
   32 [code      ]     "SECURITY_SHELL_TRUE": "subprocess(..., shell=True) — shell-injection",
   33 [code      ]     "NO_HTTP_TIMEOUT": "HTTP-запрос без timeout — риск hang",
   34 [code      ]     "MARKER_TODO": "TODO в коде — незакрытая задача",
   35 [code      ]     "MARKER_FIXME": "FIXME в коде — известная ошибка",
   36 [code      ]     "MARKER_HACK": "HACK в коде — временное решение",
   37 [code      ]     "MARKER_XXX": "XXX в коде — требуется внимание",
   38 [code      ]     "MARKER_BUG": "BUG-маркер в коде",
   39 [code      ] }
   40 [code      ] ISSUE_FIX = {
   41 [code      ]     "PARSE_ERROR": "Открыть файл, найти строку из msg, исправить синтаксис.",
   42 [code      ]     "DEAD_IMPORT": "Удалить строку `import X`. Убедиться, что X не используется (grep -R).",
   43 [code      ]     "STAR_IMPORT": "Заменить на явный список имён.",
   44 [code      ]     "BARE_EXCEPT": "`except:` → `except Exception:`. logger.exception(...).",
   45 [code      ]     "SILENT_EXCEPT_PASS": "`pass` → `logger.debug('reason=..., exc=%r', exc)`.",
   46 [code      ]     "LONG_FUNCTION": "Декомпозировать: приватные `_helper()`, тестировать по частям.",
   47 [code      ]     "HIGH_COMPLEXITY": "Разбить на подфункции; if-цепочки → dict-диспатчер.",
   48 [code      ]     "MISSING_DOCSTRING": "Добавить \"\"\"что делает, args, returns\"\"\" 3-5 строк.",
   49 [code      ]     "MISSING_CLASS_DOCSTRING": "Добавить \"\"\"назначение класса, публичные методы\"\"\".",
   50 [code      ]     "HARDCODED_WIN_PATH": "Заменить на Path из config.settings или env-переменную.",
   51 [code      ]     "HARDCODED_POSIX_PATH": "Path из config.settings/tempfile.gettempdir().",
   52 [code      ]     "BARE_PRINT": "`print(x)` → `logger.info(x)`.",
   53 [code      ]     "BLOCKING_SLEEP": "Комментарий или await asyncio.sleep().",
   54 [code      ]     "GLOBAL_STATEMENT": "Инкапсулировать в класс или get_*().",
   55 [code      ]     "ASSERT_IN_PROD": "`if not cond: raise ValueError('...')`. assert только в тестах.",
   56 [code      ]     "SECURITY_EVAL": "Убрать. ast.literal_eval или явный парсер.",
   57 [code      ]     "SECURITY_OS_SYSTEM": "`subprocess.run([...], check=True, shell=False, timeout=N)`.",
   58 [code      ]     "SECURITY_SHELL_TRUE": "Убрать shell=True; передавать список аргументов.",
   59 [code      ]     "NO_HTTP_TIMEOUT": "Добавить `timeout=(5, 30)`.",
   60 [code      ]     "MARKER_TODO": "Закрыть отдельным шагом.",
   61 [code      ]     "MARKER_FIXME": "Закрыть отдельным шагом.",
   62 [code      ]     "MARKER_HACK": "Закрыть отдельным шагом.",
   63 [code      ]     "MARKER_XXX": "Закрыть отдельным шагом.",
   64 [code      ]     "MARKER_BUG": "Закрыть отдельным шагом.",
   65 [code      ] }
   66 [code      ] ISSUE_SEVERITY = {
   67 [code      ]     "PARSE_ERROR": "🔴 BLOCKER", "SECURITY_EVAL": "🔴 CRITICAL",
   68 [code      ]     "SECURITY_OS_SYSTEM": "🔴 CRITICAL", "SECURITY_SHELL_TRUE": "🔴 CRITICAL",
   69 [code      ]     "BARE_EXCEPT": "🟠 HIGH", "HARDCODED_WIN_PATH": "🟠 HIGH",
   70 [code      ]     "HARDCODED_POSIX_PATH": "🟠 HIGH", "SILENT_EXCEPT_PASS": "🟡 MEDIUM",
   71 [code      ]     "STAR_IMPORT": "🟡 MEDIUM", "DEAD_IMPORT": "🟡 MEDIUM",
   72 [code      ]     "LONG_FUNCTION": "🟡 MEDIUM", "HIGH_COMPLEXITY": "🟡 MEDIUM",
   73 [code      ]     "GLOBAL_STATEMENT": "🟡 MEDIUM", "ASSERT_IN_PROD": "🟡 MEDIUM",
   74 [code      ]     "NO_HTTP_TIMEOUT": "🟡 MEDIUM", "BLOCKING_SLEEP": "🟢 LOW",
   75 [code      ]     "BARE_PRINT": "🟢 LOW", "MISSING_DOCSTRING": "🟢 LOW",
   76 [code      ]     "MISSING_CLASS_DOCSTRING": "🟢 LOW", "MARKER_TODO": "🟢 LOW",
   77 [code      ]     "MARKER_FIXME": "🟠 HIGH", "MARKER_HACK": "🟡 MEDIUM",
   78 [code      ]     "MARKER_XXX": "🟡 MEDIUM", "MARKER_BUG": "🔴 CRITICAL",
   79 [code      ] }
   80 [blank     ] 
   81 [blank     ] 
   82 [def       ] def get_line(path: Path, lineno: int, ctx: int = 2) -> list[str]:
   83 [try_block ]     try:
   84 [stmt      ]         with open(path, encoding="utf-8") as f:
   85 [code      ]             all_lines = f.readlines()
   86 [try_block ]     except Exception:
   87 [try_block ]         try:
   88 [stmt      ]             with open(path, encoding="cp1251") as f:
   89 [code      ]                 all_lines = f.readlines()
   90 [try_block ]         except Exception:
   91 [return    ]             return []
   92 [branch    ]     if lineno <= 0 or lineno > len(all_lines):
   93 [return    ]         return []
   94 [code      ]     start = max(0, lineno - 1 - ctx)
   95 [code      ]     end = min(len(all_lines), lineno + ctx)
   96 [code      ]     out = []
   97 [loop      ]     for i in range(start, end):
   98 [code      ]         marker = ">>>" if (i + 1) == lineno else "   "
   99 [code      ]         out.append(f"{marker} {i+1:5d} | {all_lines[i].rstrip()}")
  100 [return    ]     return out
  101 [blank     ] 
  102 [blank     ] 
  103 [def       ] def main():
  104 [code      ]     reports = json.loads(RAW.read_text(encoding="utf-8"))
  105 [blank     ] 
  106 [code      ]     idx = ["# ГЛУБОКИЙ АУДИТ v40 — ИНДЕКС ОТЧЁТА", "",
  107 [code      ]            f"Дата: 2026-08-21  |  Файлов: {len(reports)}  |  Всего проблем: {sum(len(r['issues']) for r in reports)}",
  108 [code      ]            "", "## Карта отчёта", "",
  109 [code      ]            "| # | Раздел | Файл | Описание |",
  110 [code      ]            "|---|--------|------|----------|",
  111 [code      ]            "| 1 | Статистика | 01_СТАТИСТИКА.md | Счётчики по типам проблем |",
  112 [code      ]            "| 2 | Критические | 02_КРИТ_БАГИ.md | Только SECURITY/BLOCKER |",
  113 [code      ]            "| 3 | По файлам | 03_ПО_ФАЙЛАМ/*.md | Отчёт по каждому .py |",
  114 [code      ]            "| 4 | По типам | 04_ПО_ТИПАМ_ПРОБЛЕМ/*.md | Каждый тип — свой файл |",
  115 [code      ]            "| 5 | План фикса | 05_ПЛАН_ИСПРАВЛЕНИЙ.md | Пошаговый план |",
  116 [code      ]            "| 6 | Построчно | 06_ПОСТРОЧНО.md | Все проблемы с цитатой кода ±2 |",
  117 [code      ]            "| 7 | Функции/классы | 07_ФУНКЦИИ_И_КЛАССЫ.md | Карточка каждой |",
  118 [code      ]            "| 8 | Импорты | 08_ИМПОРТЫ.md | Граф и мёртвые |",
  119 [code      ]            "| 9 | Матрица | 09_МАТРИЦА.md | Файл × тип проблемы |",
  120 [code      ]            "| 10 | Построчный листинг | 10_ПОСТРОЧНЫЙ_ЛИСТИНГ/*.md | Весь код с классификацией |",
  121 [code      ]            "| 11 | AST-дамп | 11_AST_ДАМП/*.md | Полный ast.dump() |",
  122 [code      ]            "| 12 | Идентификаторы | 12_ИДЕНТИФИКАТОРЫ/*.md | Все имена/литералы |",
  123 [code      ]            "| 13 | Git-история | 13_ИСТОРИЯ_КОММИТОВ/*.md | git log по файлу |",
  124 [code      ]            "| 14 | grep-таблицы | 14_GREP_ТАБЛИЦЫ/*.md | pattern-hits |",
  125 [code      ]            ""]
  126 [code      ]     OUT.mkdir(parents=True, exist_ok=True)
  127 [code      ]     (OUT / "00_INDEX.md").write_text("\n".join(idx), encoding="utf-8")
  128 [blank     ] 
  129 [code      ]     stats = Counter()
  130 [code      ]     per_file_count = {}
  131 [code      ]     reports_by_file = {}
  132 [loop      ]     for r in reports:
  133 [code      ]         reports_by_file[r["file"]] = r
  134 [code      ]         cnt = 0
  135 [loop      ]         for it in r["issues"]:
  136 [code      ]             stats[it["kind"]] += 1
  137 [code      ]             cnt += 1
  138 [code      ]         per_file_count[r["file"]] = cnt
  139 [blank     ] 
  140 [comment   ]     # 01_СТАТИСТИКА
  141 [code      ]     lines = ["# СТАТИСТИКА (все типы проблем)", ""]
  142 [code      ]     lines.append("## По типам")
  143 [code      ]     lines.append("| Тип | Кол-во | Severity | Human | Fix |")
  144 [code      ]     lines.append("|-----|-------:|----------|-------|-----|")
  145 [loop      ]     for k, v in stats.most_common():
  146 [code      ]         lines.append(f"| {k} | {v} | {ISSUE_SEVERITY.get(k,'?')} | {ISSUE_HUMAN.get(k, '')} | {ISSUE_FIX.get(k, '')[:100]} |")
  147 [code      ]     lines.append("")
  148 [code      ]     lines.append(f"**ИТОГО файлов:** {len(reports)}")
  149 [code      ]     lines.append(f"**ИТОГО проблем:** {sum(stats.values())}")
  150 [code      ]     lines.append("")
  151 [code      ]     lines.append("## ТОП-40 файлов по числу проблем")
  152 [code      ]     lines.append("| Файл | Проблем | LOC |")
  153 [code      ]     lines.append("|------|--------:|----:|")
  154 [code      ]     top = sorted(per_file_count.items(), key=lambda x: -x[1])[:40]
  155 [loop      ]     for f, c in top:
  156 [code      ]         lines.append(f"| `{f}` | {c} | {reports_by_file[f]['loc']} |")
  157 [code      ]     (OUT / "01_СТАТИСТИКА.md").write_text("\n".join(lines), encoding="utf-8")
  158 [blank     ] 
  159 [comment   ]     # 02_КРИТ_БАГИ
  160 [code      ]     crit_types = {"PARSE_ERROR", "SECURITY_EVAL", "SECURITY_OS_SYSTEM",
  161 [code      ]                   "SECURITY_SHELL_TRUE", "MARKER_BUG", "MARKER_FIXME"}
  162 [code      ]     crit = []
  163 [loop      ]     for r in reports:
  164 [loop      ]         for it in r["issues"]:
  165 [branch    ]             if it["kind"] in crit_types:
  166 [code      ]                 crit.append((r["file"], it))
  167 [code      ]     L = ["# КРИТИЧЕСКИЕ БАГИ (BLOCKER / CRITICAL / SECURITY)", "",
  168 [code      ]          f"Всего: **{len(crit)}**", ""]
  169 [loop      ]     for f, it in crit:
  170 [code      ]         p = ROOT / f
  171 [code      ]         L.append(f"### {f}:{it['line']} — {it['kind']}")
  172 [code      ]         L.append(f"**Severity:** {ISSUE_SEVERITY.get(it['kind'],'?')}")
  173 [code      ]         L.append(f"**Что нашли:** {it['msg']}")
  174 [code      ]         L.append(f"**Человеческий смысл:** {ISSUE_HUMAN.get(it['kind'],'')}")
  175 [code      ]         L.append(f"**Как чинить:** {ISSUE_FIX.get(it['kind'],'')}")
  176 [code      ]         ctx = get_line(p, it["line"], ctx=3)
  177 [branch    ]         if ctx:
  178 [code      ]             L.append("")
  179 [code      ]             L.append("```")
  180 [code      ]             L.extend(ctx)
  181 [code      ]             L.append("```")
  182 [code      ]         L.append("")
  183 [code      ]     (OUT / "02_КРИТ_БАГИ.md").write_text("\n".join(L), encoding="utf-8")
  184 [blank     ] 
  185 [comment   ]     # 03_ПО_ФАЙЛАМ
  186 [code      ]     per_dir = OUT / "03_ПО_ФАЙЛАМ"
  187 [code      ]     per_dir.mkdir(exist_ok=True)
  188 [loop      ]     for r in reports:
  189 [code      ]         rel = r["file"]
  190 [code      ]         safe = rel.replace("/", "__").replace("\\", "__")
  191 [code      ]         p = ROOT / rel
  192 [code      ]         L = [f"# АУДИТ ФАЙЛА: `{rel}`", "",
  193 [code      ]              f"**LOC:** {r['loc']}  |  **Размер:** {r['size_bytes']} байт  |  **Проблем:** {len(r['issues'])}  |  **Risk score:** {r['risk_score']}",
  194 [code      ]              "", "## Импорты", ""]
  195 [branch    ]         if r["imports"]:
  196 [code      ]             L.append("| Строка | Имя | Вид |")
  197 [code      ]             L.append("|-------:|-----|-----|")
  198 [loop      ]             for imp in r["imports"]:
  199 [code      ]                 L.append(f"| {imp['line']} | `{imp['name']}` | {imp['kind']} |")
  200 [branch    ]         else:
  201 [code      ]             L.append("_импортов нет_")
  202 [code      ]         L.append("")
  203 [code      ]         L.append("## Функции")
  204 [code      ]         L.append("")
  205 [branch    ]         if r["functions"]:
  206 [code      ]             L.append("| Строка | Имя | LOC | Complexity | Docstring |")
  207 [code      ]             L.append("|-------:|-----|----:|-----------:|-----------|")
  208 [loop      ]             for fn in r["functions"]:
  209 [code      ]                 L.append(f"| {fn['line']} | `{fn['name']}` | {fn['loc']} | {fn['complexity']} | {'✅' if fn['has_doc'] else '❌'} |")
  210 [branch    ]         else:
  211 [code      ]             L.append("_функций нет_")
  212 [code      ]         L.append("")
  213 [code      ]         L.append("## Классы")
  214 [code      ]         L.append("")
  215 [branch    ]         if r["classes"]:
  216 [code      ]             L.append("| Строка | Имя | Docstring |")
  217 [code      ]             L.append("|-------:|-----|-----------|")
  218 [loop      ]             for cl in r["classes"]:
  219 [code      ]                 L.append(f"| {cl['line']} | `{cl['name']}` | {'✅' if cl['has_doc'] else '❌'} |")
  220 [branch    ]         else:
  221 [code      ]             L.append("_классов нет_")
  222 [code      ]         L.append("")
  223 [code      ]         L.append("## Проблемы (детально, с цитатой кода)")
  224 [code      ]         L.append("")
  225 [code      ]         by_kind = defaultdict(list)
  226 [loop      ]         for it in r["issues"]:
  227 [code      ]             by_kind[it["kind"]].append(it)
  228 [loop      ]         for kind, items in sorted(by_kind.items(), key=lambda x: -len(x[1])):
  229 [code      ]             L.append(f"### {kind} — {len(items)} шт. — {ISSUE_SEVERITY.get(kind,'?')}")
  230 [code      ]             L.append(f"**Смысл:** {ISSUE_HUMAN.get(kind,'')}")
  231 [code      ]             L.append(f"**Fix:** {ISSUE_FIX.get(kind,'')}")
  232 [code      ]             L.append("")
  233 [loop      ]             for it in items:
  234 [code      ]                 L.append(f"- **строка {it['line']}** — {it['msg']}")
  235 [code      ]                 ctx = get_line(p, it["line"], ctx=2)
  236 [branch    ]                 if ctx:
  237 [code      ]                     L.append("")
  238 [code      ]                     L.append("  ```")
  239 [loop      ]                     for c in ctx:
  240 [code      ]                         L.append(f"  {c}")
  241 [code      ]                     L.append("  ```")
  242 [code      ]                 L.append("")
  243 [code      ]         (per_dir / (safe + ".md")).write_text("\n".join(L), encoding="utf-8")
  244 [blank     ] 
  245 [comment   ]     # 04_ПО_ТИПАМ
  246 [code      ]     kind_dir = OUT / "04_ПО_ТИПАМ_ПРОБЛЕМ"
  247 [code      ]     kind_dir.mkdir(exist_ok=True)
  248 [loop      ]     for kind in stats:
  249 [code      ]         L = [f"# {kind} — {ISSUE_HUMAN.get(kind, '')}", "",
  250 [code      ]              f"**Severity:** {ISSUE_SEVERITY.get(kind,'?')}",
  251 [code      ]              f"**Всего:** {stats[kind]}",
  252 [code      ]              f"**Как чинить:** {ISSUE_FIX.get(kind,'')}",
  253 [code      ]              "", "## Все вхождения", ""]
  254 [loop      ]         for r in reports:
  255 [code      ]             hits = [it for it in r["issues"] if it["kind"] == kind]
  256 [branch    ]             if not hits:
  257 [code      ]                 continue
  258 [code      ]             p = ROOT / r["file"]
  259 [code      ]             L.append(f"### `{r['file']}` — {len(hits)} шт.")
  260 [loop      ]             for it in hits:
  261 [code      ]                 L.append(f"- **строка {it['line']}** — {it['msg']}")
  262 [code      ]                 ctx = get_line(p, it["line"], ctx=2)
  263 [branch    ]                 if ctx:
  264 [code      ]                     L.append("  ```")
  265 [loop      ]                     for c in ctx:
  266 [code      ]                         L.append(f"  {c}")
  267 [code      ]                     L.append("  ```")
  268 [code      ]             L.append("")
  269 [code      ]         (kind_dir / f"{kind}.md").write_text("\n".join(L), encoding="utf-8")
  270 [blank     ] 
  271 [comment   ]     # 05_ПЛАН_ИСПРАВЛЕНИЙ
  272 [code      ]     L = ["# ПЛАН ИСПРАВЛЕНИЙ v40 — пошаговый", "",
  273 [code      ]          "Порядок: BLOCKER → CRITICAL → HIGH → MEDIUM → LOW.",
  274 [code      ]          "После каждого блока — pytest -x, py_compile, commit в main.", ""]
  275 [code      ]     order = ["PARSE_ERROR", "SECURITY_EVAL", "SECURITY_OS_SYSTEM",
  276 [code      ]              "SECURITY_SHELL_TRUE", "MARKER_BUG", "MARKER_FIXME",
  277 [code      ]              "BARE_EXCEPT", "HARDCODED_WIN_PATH", "HARDCODED_POSIX_PATH",
  278 [code      ]              "STAR_IMPORT", "DEAD_IMPORT", "SILENT_EXCEPT_PASS",
  279 [code      ]              "LONG_FUNCTION", "HIGH_COMPLEXITY", "GLOBAL_STATEMENT",
  280 [code      ]              "ASSERT_IN_PROD", "NO_HTTP_TIMEOUT", "MARKER_HACK", "MARKER_XXX",
  281 [code      ]              "BLOCKING_SLEEP", "BARE_PRINT", "MISSING_DOCSTRING",
  282 [code      ]              "MISSING_CLASS_DOCSTRING", "MARKER_TODO"]
  283 [code      ]     step_no = 1
  284 [loop      ]     for kind in order:
  285 [branch    ]         if kind not in stats:
  286 [code      ]             continue
  287 [code      ]         L.append(f"## Блок {kind} ({stats[kind]} шт.) — {ISSUE_SEVERITY.get(kind,'?')}")
  288 [code      ]         L.append(f"**Что делать:** {ISSUE_FIX.get(kind,'')}")
  289 [code      ]         L.append("")
  290 [loop      ]         for r in reports:
  291 [code      ]             hits = [it for it in r["issues"] if it["kind"] == kind]
  292 [loop      ]             for it in hits:
  293 [code      ]                 L.append(f"- [ ] ШАГ {step_no:04d}: `{r['file']}:{it['line']}` — {it['msg']}")
  294 [code      ]                 step_no += 1
  295 [code      ]         L.append("")
  296 [code      ]     (OUT / "05_ПЛАН_ИСПРАВЛЕНИЙ.md").write_text("\n".join(L), encoding="utf-8")
  297 [blank     ] 
  298 [comment   ]     # 06_ПОСТРОЧНО
  299 [code      ]     L = ["# ПОСТРОЧНЫЙ ДАМП (с цитатой ±2 строки)", ""]
  300 [loop      ]     for r in reports:
  301 [branch    ]         if not r["issues"]:
  302 [code      ]             continue
  303 [code      ]         p = ROOT / r["file"]
  304 [code      ]         L.append(f"## `{r['file']}` — {len(r['issues'])} шт.")
  305 [loop      ]         for it in sorted(r["issues"], key=lambda x: x.get("line", 0)):
  306 [code      ]             L.append(f"### line {it['line']} — {it['kind']} — {ISSUE_SEVERITY.get(it['kind'],'?')}")
  307 [code      ]             L.append(f"- **msg:** {it['msg']}")
  308 [code      ]             L.append(f"- **human:** {ISSUE_HUMAN.get(it['kind'],'')}")
  309 [code      ]             L.append(f"- **fix:** {ISSUE_FIX.get(it['kind'],'')}")
  310 [code      ]             ctx = get_line(p, it["line"], ctx=2)
  311 [branch    ]             if ctx:
  312 [code      ]                 L.append("```")
  313 [code      ]                 L.extend(ctx)
  314 [code      ]                 L.append("```")
  315 [code      ]             L.append("")
  316 [code      ]     (OUT / "06_ПОСТРОЧНО.md").write_text("\n".join(L), encoding="utf-8")
  317 [blank     ] 
  318 [comment   ]     # 07_ФУНКЦИИ_И_КЛАССЫ
  319 [code      ]     L = ["# ВСЕ ФУНКЦИИ И КЛАССЫ ПРОЕКТА", ""]
  320 [code      ]     tot_fn = sum(len(r["functions"]) for r in reports)
  321 [code      ]     tot_cl = sum(len(r["classes"]) for r in reports)
  322 [code      ]     L.append(f"Всего функций: **{tot_fn}**, классов: **{tot_cl}**.")
  323 [code      ]     L.append("")
  324 [loop      ]     for r in reports:
  325 [branch    ]         if not r["functions"] and not r["classes"]:
  326 [code      ]             continue
  327 [code      ]         L.append(f"## `{r['file']}`")
  328 [branch    ]         if r["classes"]:
  329 [code      ]             L.append("### Классы")
  330 [loop      ]             for cl in r["classes"]:
  331 [code      ]                 L.append(f"- **`{cl['name']}`** (строка {cl['line']}, docstring: {'да' if cl['has_doc'] else 'НЕТ'})")
  332 [branch    ]         if r["functions"]:
  333 [code      ]             L.append("### Функции")
  334 [loop      ]             for fn in r["functions"]:
  335 [code      ]                 doc = "да" if fn["has_doc"] else "НЕТ"
  336 [code      ]                 warn = ""
  337 [branch    ]                 if fn["loc"] > 100:
  338 [code      ]                     warn += " ⚠️ длинная"
  339 [branch    ]                 if fn["complexity"] > 15:
  340 [code      ]                     warn += " ⚠️ сложная"
  341 [code      ]                 L.append(f"- **`{fn['name']}`** — строка {fn['line']}, LOC={fn['loc']}, cyclo≈{fn['complexity']}, doc={doc}{warn}")
  342 [code      ]         L.append("")
  343 [code      ]     (OUT / "07_ФУНКЦИИ_И_КЛАССЫ.md").write_text("\n".join(L), encoding="utf-8")
  344 [blank     ] 
  345 [comment   ]     # 08_ИМПОРТЫ
  346 [code      ]     L = ["# ИМПОРТЫ ВО ВСЁМ ПРОЕКТЕ", ""]
  347 [code      ]     dead = sum(1 for r in reports for it in r["issues"] if it["kind"] == "DEAD_IMPORT")
  348 [code      ]     live = sum(len(r["imports"]) for r in reports)
  349 [code      ]     L.append(f"Всего импортов: **{live}**, мёртвых: **{dead}** ({100*dead/max(live,1):.1f}%).")
  350 [code      ]     L.append("")
  351 [loop      ]     for r in reports:
  352 [branch    ]         if not r["imports"]:
  353 [code      ]             continue
  354 [code      ]         L.append(f"## `{r['file']}`")
  355 [code      ]         L.append("| Строка | Имя | Вид | Мёртв |")
  356 [code      ]         L.append("|-------:|-----|-----|:----:|")
  357 [code      ]         dead_lines = {it["line"] for it in r["issues"] if it["kind"] == "DEAD_IMPORT"}
  358 [loop      ]         for imp in r["imports"]:
  359 [code      ]             mark = "❌" if imp["line"] in dead_lines else "✅"
  360 [code      ]             L.append(f"| {imp['line']} | `{imp['name']}` | {imp['kind']} | {mark} |")
  361 [code      ]         L.append("")
  362 [code      ]     (OUT / "08_ИМПОРТЫ.md").write_text("\n".join(L), encoding="utf-8")
  363 [blank     ] 
  364 [comment   ]     # 09_МАТРИЦА
  365 [code      ]     all_kinds = sorted(stats.keys())
  366 [code      ]     L = ["# МАТРИЦА: файл × тип проблемы", "",
  367 [code      ]          "| Файл | " + " | ".join(all_kinds) + " | Σ |",
  368 [code      ]          "|------|" + "|".join([":-:"] * len(all_kinds)) + "|--:|"]
  369 [loop      ]     for r in sorted(reports, key=lambda x: -len(x["issues"])):
  370 [code      ]         row = [f"`{r['file']}`"]
  371 [code      ]         by = Counter(it["kind"] for it in r["issues"])
  372 [loop      ]         for k in all_kinds:
  373 [code      ]             row.append(str(by.get(k, "")))
  374 [code      ]         row.append(str(len(r["issues"])))
  375 [code      ]         L.append("| " + " | ".join(row) + " |")
  376 [code      ]     (OUT / "09_МАТРИЦА.md").write_text("\n".join(L), encoding="utf-8")
  377 [blank     ] 
  378 [code      ]     print("Reports written to", OUT)
  379 [blank     ] 
  380 [blank     ] 
  381 [branch    ] if __name__ == "__main__":
  382 [code      ]     main()
```