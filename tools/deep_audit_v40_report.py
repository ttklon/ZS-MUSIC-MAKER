#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/deep_audit_v40_report.py — детальный отчёт из AUDIT_RAW.json."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "PLAN_v39" / "APP_L_ГЛУБОКИЙ_АУДИТ_V40"
RAW = OUT / "AUDIT_RAW.json"

ISSUE_HUMAN = {
    "PARSE_ERROR": "Файл не парсится (SyntaxError) — блокер",
    "DEAD_IMPORT": "Мёртвый импорт (не используется в файле)",
    "STAR_IMPORT": "'from X import *' — ломает статический анализ",
    "BARE_EXCEPT": "'except:' без типа — ловит KeyboardInterrupt/SystemExit",
    "SILENT_EXCEPT_PASS": "'except ...: pass' — тихое поглощение ошибок",
    "LONG_FUNCTION": "Функция > 100 LOC — сложно тестировать/поддерживать",
    "HIGH_COMPLEXITY": "Цикломатическая сложность > 15",
    "MISSING_DOCSTRING": "Public-функция без docstring",
    "MISSING_CLASS_DOCSTRING": "Public-класс без docstring",
    "HARDCODED_WIN_PATH": "Захардкоженный Windows-путь (C:\\...)",
    "HARDCODED_POSIX_PATH": "Захардкоженный POSIX-путь (/home/... /Users/...)",
    "BARE_PRINT": "print() вместо logger",
    "BLOCKING_SLEEP": "time.sleep() без комментария/аргументации",
    "GLOBAL_STATEMENT": "global — обычно антипаттерн",
    "ASSERT_IN_PROD": "assert в production — -O его выкинет",
    "SECURITY_EVAL": "eval()/exec() — вектор RCE",
    "SECURITY_OS_SYSTEM": "os.system() — заменить на subprocess.run(shell=False)",
    "SECURITY_SHELL_TRUE": "subprocess(..., shell=True) — shell-injection",
    "NO_HTTP_TIMEOUT": "HTTP-запрос без timeout — риск hang",
    "MARKER_TODO": "TODO в коде — незакрытая задача",
    "MARKER_FIXME": "FIXME в коде — известная ошибка",
    "MARKER_HACK": "HACK в коде — временное решение",
    "MARKER_XXX": "XXX в коде — требуется внимание",
    "MARKER_BUG": "BUG-маркер в коде",
}
ISSUE_FIX = {
    "PARSE_ERROR": "Открыть файл, найти строку из msg, исправить синтаксис.",
    "DEAD_IMPORT": "Удалить строку `import X`. Убедиться, что X не используется (grep -R).",
    "STAR_IMPORT": "Заменить на явный список имён.",
    "BARE_EXCEPT": "`except:` → `except Exception:`. logger.exception(...).",
    "SILENT_EXCEPT_PASS": "`pass` → `logger.debug('reason=..., exc=%r', exc)`.",
    "LONG_FUNCTION": "Декомпозировать: приватные `_helper()`, тестировать по частям.",
    "HIGH_COMPLEXITY": "Разбить на подфункции; if-цепочки → dict-диспатчер.",
    "MISSING_DOCSTRING": "Добавить \"\"\"что делает, args, returns\"\"\" 3-5 строк.",
    "MISSING_CLASS_DOCSTRING": "Добавить \"\"\"назначение класса, публичные методы\"\"\".",
    "HARDCODED_WIN_PATH": "Заменить на Path из config.settings или env-переменную.",
    "HARDCODED_POSIX_PATH": "Path из config.settings/tempfile.gettempdir().",
    "BARE_PRINT": "`print(x)` → `logger.info(x)`.",
    "BLOCKING_SLEEP": "Комментарий или await asyncio.sleep().",
    "GLOBAL_STATEMENT": "Инкапсулировать в класс или get_*().",
    "ASSERT_IN_PROD": "`if not cond: raise ValueError('...')`. assert только в тестах.",
    "SECURITY_EVAL": "Убрать. ast.literal_eval или явный парсер.",
    "SECURITY_OS_SYSTEM": "`subprocess.run([...], check=True, shell=False, timeout=N)`.",
    "SECURITY_SHELL_TRUE": "Убрать shell=True; передавать список аргументов.",
    "NO_HTTP_TIMEOUT": "Добавить `timeout=(5, 30)`.",
    "MARKER_TODO": "Закрыть отдельным шагом.",
    "MARKER_FIXME": "Закрыть отдельным шагом.",
    "MARKER_HACK": "Закрыть отдельным шагом.",
    "MARKER_XXX": "Закрыть отдельным шагом.",
    "MARKER_BUG": "Закрыть отдельным шагом.",
}
ISSUE_SEVERITY = {
    "PARSE_ERROR": "🔴 BLOCKER", "SECURITY_EVAL": "🔴 CRITICAL",
    "SECURITY_OS_SYSTEM": "🔴 CRITICAL", "SECURITY_SHELL_TRUE": "🔴 CRITICAL",
    "BARE_EXCEPT": "🟠 HIGH", "HARDCODED_WIN_PATH": "🟠 HIGH",
    "HARDCODED_POSIX_PATH": "🟠 HIGH", "SILENT_EXCEPT_PASS": "🟡 MEDIUM",
    "STAR_IMPORT": "🟡 MEDIUM", "DEAD_IMPORT": "🟡 MEDIUM",
    "LONG_FUNCTION": "🟡 MEDIUM", "HIGH_COMPLEXITY": "🟡 MEDIUM",
    "GLOBAL_STATEMENT": "🟡 MEDIUM", "ASSERT_IN_PROD": "🟡 MEDIUM",
    "NO_HTTP_TIMEOUT": "🟡 MEDIUM", "BLOCKING_SLEEP": "🟢 LOW",
    "BARE_PRINT": "🟢 LOW", "MISSING_DOCSTRING": "🟢 LOW",
    "MISSING_CLASS_DOCSTRING": "🟢 LOW", "MARKER_TODO": "🟢 LOW",
    "MARKER_FIXME": "🟠 HIGH", "MARKER_HACK": "🟡 MEDIUM",
    "MARKER_XXX": "🟡 MEDIUM", "MARKER_BUG": "🔴 CRITICAL",
}


def get_line(path: Path, lineno: int, ctx: int = 2) -> list[str]:
    try:
        with open(path, encoding="utf-8") as f:
            all_lines = f.readlines()
    except Exception:
        try:
            with open(path, encoding="cp1251") as f:
                all_lines = f.readlines()
        except Exception:
            return []
    if lineno <= 0 or lineno > len(all_lines):
        return []
    start = max(0, lineno - 1 - ctx)
    end = min(len(all_lines), lineno + ctx)
    out = []
    for i in range(start, end):
        marker = ">>>" if (i + 1) == lineno else "   "
        out.append(f"{marker} {i+1:5d} | {all_lines[i].rstrip()}")
    return out


def main():
    reports = json.loads(RAW.read_text(encoding="utf-8"))

    idx = ["# ГЛУБОКИЙ АУДИТ v40 — ИНДЕКС ОТЧЁТА", "",
           f"Дата: 2026-08-21  |  Файлов: {len(reports)}  |  Всего проблем: {sum(len(r['issues']) for r in reports)}",
           "", "## Карта отчёта", "",
           "| # | Раздел | Файл | Описание |",
           "|---|--------|------|----------|",
           "| 1 | Статистика | 01_СТАТИСТИКА.md | Счётчики по типам проблем |",
           "| 2 | Критические | 02_КРИТ_БАГИ.md | Только SECURITY/BLOCKER |",
           "| 3 | По файлам | 03_ПО_ФАЙЛАМ/*.md | Отчёт по каждому .py |",
           "| 4 | По типам | 04_ПО_ТИПАМ_ПРОБЛЕМ/*.md | Каждый тип — свой файл |",
           "| 5 | План фикса | 05_ПЛАН_ИСПРАВЛЕНИЙ.md | Пошаговый план |",
           "| 6 | Построчно | 06_ПОСТРОЧНО.md | Все проблемы с цитатой кода ±2 |",
           "| 7 | Функции/классы | 07_ФУНКЦИИ_И_КЛАССЫ.md | Карточка каждой |",
           "| 8 | Импорты | 08_ИМПОРТЫ.md | Граф и мёртвые |",
           "| 9 | Матрица | 09_МАТРИЦА.md | Файл × тип проблемы |",
           "| 10 | Построчный листинг | 10_ПОСТРОЧНЫЙ_ЛИСТИНГ/*.md | Весь код с классификацией |",
           "| 11 | AST-дамп | 11_AST_ДАМП/*.md | Полный ast.dump() |",
           "| 12 | Идентификаторы | 12_ИДЕНТИФИКАТОРЫ/*.md | Все имена/литералы |",
           "| 13 | Git-история | 13_ИСТОРИЯ_КОММИТОВ/*.md | git log по файлу |",
           "| 14 | grep-таблицы | 14_GREP_ТАБЛИЦЫ/*.md | pattern-hits |",
           ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "00_INDEX.md").write_text("\n".join(idx), encoding="utf-8")

    stats = Counter()
    per_file_count = {}
    reports_by_file = {}
    for r in reports:
        reports_by_file[r["file"]] = r
        cnt = 0
        for it in r["issues"]:
            stats[it["kind"]] += 1
            cnt += 1
        per_file_count[r["file"]] = cnt

    # 01_СТАТИСТИКА
    lines = ["# СТАТИСТИКА (все типы проблем)", ""]
    lines.append("## По типам")
    lines.append("| Тип | Кол-во | Severity | Human | Fix |")
    lines.append("|-----|-------:|----------|-------|-----|")
    for k, v in stats.most_common():
        lines.append(f"| {k} | {v} | {ISSUE_SEVERITY.get(k,'?')} | {ISSUE_HUMAN.get(k, '')} | {ISSUE_FIX.get(k, '')[:100]} |")
    lines.append("")
    lines.append(f"**ИТОГО файлов:** {len(reports)}")
    lines.append(f"**ИТОГО проблем:** {sum(stats.values())}")
    lines.append("")
    lines.append("## ТОП-40 файлов по числу проблем")
    lines.append("| Файл | Проблем | LOC |")
    lines.append("|------|--------:|----:|")
    top = sorted(per_file_count.items(), key=lambda x: -x[1])[:40]
    for f, c in top:
        lines.append(f"| `{f}` | {c} | {reports_by_file[f]['loc']} |")
    (OUT / "01_СТАТИСТИКА.md").write_text("\n".join(lines), encoding="utf-8")

    # 02_КРИТ_БАГИ
    crit_types = {"PARSE_ERROR", "SECURITY_EVAL", "SECURITY_OS_SYSTEM",
                  "SECURITY_SHELL_TRUE", "MARKER_BUG", "MARKER_FIXME"}
    crit = []
    for r in reports:
        for it in r["issues"]:
            if it["kind"] in crit_types:
                crit.append((r["file"], it))
    L = ["# КРИТИЧЕСКИЕ БАГИ (BLOCKER / CRITICAL / SECURITY)", "",
         f"Всего: **{len(crit)}**", ""]
    for f, it in crit:
        p = ROOT / f
        L.append(f"### {f}:{it['line']} — {it['kind']}")
        L.append(f"**Severity:** {ISSUE_SEVERITY.get(it['kind'],'?')}")
        L.append(f"**Что нашли:** {it['msg']}")
        L.append(f"**Человеческий смысл:** {ISSUE_HUMAN.get(it['kind'],'')}")
        L.append(f"**Как чинить:** {ISSUE_FIX.get(it['kind'],'')}")
        ctx = get_line(p, it["line"], ctx=3)
        if ctx:
            L.append("")
            L.append("```")
            L.extend(ctx)
            L.append("```")
        L.append("")
    (OUT / "02_КРИТ_БАГИ.md").write_text("\n".join(L), encoding="utf-8")

    # 03_ПО_ФАЙЛАМ
    per_dir = OUT / "03_ПО_ФАЙЛАМ"
    per_dir.mkdir(exist_ok=True)
    for r in reports:
        rel = r["file"]
        safe = rel.replace("/", "__").replace("\\", "__")
        p = ROOT / rel
        L = [f"# АУДИТ ФАЙЛА: `{rel}`", "",
             f"**LOC:** {r['loc']}  |  **Размер:** {r['size_bytes']} байт  |  **Проблем:** {len(r['issues'])}  |  **Risk score:** {r['risk_score']}",
             "", "## Импорты", ""]
        if r["imports"]:
            L.append("| Строка | Имя | Вид |")
            L.append("|-------:|-----|-----|")
            for imp in r["imports"]:
                L.append(f"| {imp['line']} | `{imp['name']}` | {imp['kind']} |")
        else:
            L.append("_импортов нет_")
        L.append("")
        L.append("## Функции")
        L.append("")
        if r["functions"]:
            L.append("| Строка | Имя | LOC | Complexity | Docstring |")
            L.append("|-------:|-----|----:|-----------:|-----------|")
            for fn in r["functions"]:
                L.append(f"| {fn['line']} | `{fn['name']}` | {fn['loc']} | {fn['complexity']} | {'✅' if fn['has_doc'] else '❌'} |")
        else:
            L.append("_функций нет_")
        L.append("")
        L.append("## Классы")
        L.append("")
        if r["classes"]:
            L.append("| Строка | Имя | Docstring |")
            L.append("|-------:|-----|-----------|")
            for cl in r["classes"]:
                L.append(f"| {cl['line']} | `{cl['name']}` | {'✅' if cl['has_doc'] else '❌'} |")
        else:
            L.append("_классов нет_")
        L.append("")
        L.append("## Проблемы (детально, с цитатой кода)")
        L.append("")
        by_kind = defaultdict(list)
        for it in r["issues"]:
            by_kind[it["kind"]].append(it)
        for kind, items in sorted(by_kind.items(), key=lambda x: -len(x[1])):
            L.append(f"### {kind} — {len(items)} шт. — {ISSUE_SEVERITY.get(kind,'?')}")
            L.append(f"**Смысл:** {ISSUE_HUMAN.get(kind,'')}")
            L.append(f"**Fix:** {ISSUE_FIX.get(kind,'')}")
            L.append("")
            for it in items:
                L.append(f"- **строка {it['line']}** — {it['msg']}")
                ctx = get_line(p, it["line"], ctx=2)
                if ctx:
                    L.append("")
                    L.append("  ```")
                    for c in ctx:
                        L.append(f"  {c}")
                    L.append("  ```")
                L.append("")
        (per_dir / (safe + ".md")).write_text("\n".join(L), encoding="utf-8")

    # 04_ПО_ТИПАМ
    kind_dir = OUT / "04_ПО_ТИПАМ_ПРОБЛЕМ"
    kind_dir.mkdir(exist_ok=True)
    for kind in stats:
        L = [f"# {kind} — {ISSUE_HUMAN.get(kind, '')}", "",
             f"**Severity:** {ISSUE_SEVERITY.get(kind,'?')}",
             f"**Всего:** {stats[kind]}",
             f"**Как чинить:** {ISSUE_FIX.get(kind,'')}",
             "", "## Все вхождения", ""]
        for r in reports:
            hits = [it for it in r["issues"] if it["kind"] == kind]
            if not hits:
                continue
            p = ROOT / r["file"]
            L.append(f"### `{r['file']}` — {len(hits)} шт.")
            for it in hits:
                L.append(f"- **строка {it['line']}** — {it['msg']}")
                ctx = get_line(p, it["line"], ctx=2)
                if ctx:
                    L.append("  ```")
                    for c in ctx:
                        L.append(f"  {c}")
                    L.append("  ```")
            L.append("")
        (kind_dir / f"{kind}.md").write_text("\n".join(L), encoding="utf-8")

    # 05_ПЛАН_ИСПРАВЛЕНИЙ
    L = ["# ПЛАН ИСПРАВЛЕНИЙ v40 — пошаговый", "",
         "Порядок: BLOCKER → CRITICAL → HIGH → MEDIUM → LOW.",
         "После каждого блока — pytest -x, py_compile, commit в main.", ""]
    order = ["PARSE_ERROR", "SECURITY_EVAL", "SECURITY_OS_SYSTEM",
             "SECURITY_SHELL_TRUE", "MARKER_BUG", "MARKER_FIXME",
             "BARE_EXCEPT", "HARDCODED_WIN_PATH", "HARDCODED_POSIX_PATH",
             "STAR_IMPORT", "DEAD_IMPORT", "SILENT_EXCEPT_PASS",
             "LONG_FUNCTION", "HIGH_COMPLEXITY", "GLOBAL_STATEMENT",
             "ASSERT_IN_PROD", "NO_HTTP_TIMEOUT", "MARKER_HACK", "MARKER_XXX",
             "BLOCKING_SLEEP", "BARE_PRINT", "MISSING_DOCSTRING",
             "MISSING_CLASS_DOCSTRING", "MARKER_TODO"]
    step_no = 1
    for kind in order:
        if kind not in stats:
            continue
        L.append(f"## Блок {kind} ({stats[kind]} шт.) — {ISSUE_SEVERITY.get(kind,'?')}")
        L.append(f"**Что делать:** {ISSUE_FIX.get(kind,'')}")
        L.append("")
        for r in reports:
            hits = [it for it in r["issues"] if it["kind"] == kind]
            for it in hits:
                L.append(f"- [ ] ШАГ {step_no:04d}: `{r['file']}:{it['line']}` — {it['msg']}")
                step_no += 1
        L.append("")
    (OUT / "05_ПЛАН_ИСПРАВЛЕНИЙ.md").write_text("\n".join(L), encoding="utf-8")

    # 06_ПОСТРОЧНО
    L = ["# ПОСТРОЧНЫЙ ДАМП (с цитатой ±2 строки)", ""]
    for r in reports:
        if not r["issues"]:
            continue
        p = ROOT / r["file"]
        L.append(f"## `{r['file']}` — {len(r['issues'])} шт.")
        for it in sorted(r["issues"], key=lambda x: x.get("line", 0)):
            L.append(f"### line {it['line']} — {it['kind']} — {ISSUE_SEVERITY.get(it['kind'],'?')}")
            L.append(f"- **msg:** {it['msg']}")
            L.append(f"- **human:** {ISSUE_HUMAN.get(it['kind'],'')}")
            L.append(f"- **fix:** {ISSUE_FIX.get(it['kind'],'')}")
            ctx = get_line(p, it["line"], ctx=2)
            if ctx:
                L.append("```")
                L.extend(ctx)
                L.append("```")
            L.append("")
    (OUT / "06_ПОСТРОЧНО.md").write_text("\n".join(L), encoding="utf-8")

    # 07_ФУНКЦИИ_И_КЛАССЫ
    L = ["# ВСЕ ФУНКЦИИ И КЛАССЫ ПРОЕКТА", ""]
    tot_fn = sum(len(r["functions"]) for r in reports)
    tot_cl = sum(len(r["classes"]) for r in reports)
    L.append(f"Всего функций: **{tot_fn}**, классов: **{tot_cl}**.")
    L.append("")
    for r in reports:
        if not r["functions"] and not r["classes"]:
            continue
        L.append(f"## `{r['file']}`")
        if r["classes"]:
            L.append("### Классы")
            for cl in r["classes"]:
                L.append(f"- **`{cl['name']}`** (строка {cl['line']}, docstring: {'да' if cl['has_doc'] else 'НЕТ'})")
        if r["functions"]:
            L.append("### Функции")
            for fn in r["functions"]:
                doc = "да" if fn["has_doc"] else "НЕТ"
                warn = ""
                if fn["loc"] > 100:
                    warn += " ⚠️ длинная"
                if fn["complexity"] > 15:
                    warn += " ⚠️ сложная"
                L.append(f"- **`{fn['name']}`** — строка {fn['line']}, LOC={fn['loc']}, cyclo≈{fn['complexity']}, doc={doc}{warn}")
        L.append("")
    (OUT / "07_ФУНКЦИИ_И_КЛАССЫ.md").write_text("\n".join(L), encoding="utf-8")

    # 08_ИМПОРТЫ
    L = ["# ИМПОРТЫ ВО ВСЁМ ПРОЕКТЕ", ""]
    dead = sum(1 for r in reports for it in r["issues"] if it["kind"] == "DEAD_IMPORT")
    live = sum(len(r["imports"]) for r in reports)
    L.append(f"Всего импортов: **{live}**, мёртвых: **{dead}** ({100*dead/max(live,1):.1f}%).")
    L.append("")
    for r in reports:
        if not r["imports"]:
            continue
        L.append(f"## `{r['file']}`")
        L.append("| Строка | Имя | Вид | Мёртв |")
        L.append("|-------:|-----|-----|:----:|")
        dead_lines = {it["line"] for it in r["issues"] if it["kind"] == "DEAD_IMPORT"}
        for imp in r["imports"]:
            mark = "❌" if imp["line"] in dead_lines else "✅"
            L.append(f"| {imp['line']} | `{imp['name']}` | {imp['kind']} | {mark} |")
        L.append("")
    (OUT / "08_ИМПОРТЫ.md").write_text("\n".join(L), encoding="utf-8")

    # 09_МАТРИЦА
    all_kinds = sorted(stats.keys())
    L = ["# МАТРИЦА: файл × тип проблемы", "",
         "| Файл | " + " | ".join(all_kinds) + " | Σ |",
         "|------|" + "|".join([":-:"] * len(all_kinds)) + "|--:|"]
    for r in sorted(reports, key=lambda x: -len(x["issues"])):
        row = [f"`{r['file']}`"]
        by = Counter(it["kind"] for it in r["issues"])
        for k in all_kinds:
            row.append(str(by.get(k, "")))
        row.append(str(len(r["issues"])))
        L.append("| " + " | ".join(row) + " |")
    (OUT / "09_МАТРИЦА.md").write_text("\n".join(L), encoding="utf-8")

    print("Reports written to", OUT)


if __name__ == "__main__":
    from cli_contract import help_or_error

    if help_or_error(__doc__ or "ZS Music Maker tool"):
        raise SystemExit(0)
    main()
