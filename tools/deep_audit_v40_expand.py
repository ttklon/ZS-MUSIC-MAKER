#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/deep_audit_v40_expand.py — раздувание отчёта РЕАЛЬНЫМИ данными."""
from __future__ import annotations

import ast
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "PLAN_v39" / "APP_L_ГЛУБОКИЙ_АУДИТ_V40"
DEEP = OUT / "10_ПОСТРОЧНЫЙ_ЛИСТИНГ"
DEEP.mkdir(exist_ok=True, parents=True)
AST_DIR = OUT / "11_AST_ДАМП"
AST_DIR.mkdir(exist_ok=True, parents=True)
IDENT_DIR = OUT / "12_ИДЕНТИФИКАТОРЫ"
IDENT_DIR.mkdir(exist_ok=True, parents=True)
GITLOG_DIR = OUT / "13_ИСТОРИЯ_КОММИТОВ"
GITLOG_DIR.mkdir(exist_ok=True, parents=True)
GREP_DIR = OUT / "14_GREP_ТАБЛИЦЫ"
GREP_DIR.mkdir(exist_ok=True, parents=True)


def all_py():
    out = []
    for p in ROOT.rglob("*.py"):
        if ".git" in p.parts or "__pycache__" in p.parts:
            continue
        out.append(p)
    return sorted(out)


def classify_line(line: str, in_docstring: bool) -> str:
    stripped = line.rstrip("\n").strip()
    if not stripped:
        return "blank"
    if in_docstring:
        return "docstring"
    if stripped.startswith("#"):
        return "comment"
    if stripped.startswith(("import ", "from ")):
        return "import"
    if stripped.startswith("def "):
        return "def"
    if stripped.startswith("async def "):
        return "async_def"
    if stripped.startswith("class "):
        return "class"
    if stripped.startswith("@"):
        return "decorator"
    if stripped.startswith(("return ", "return")):
        return "return"
    if stripped.startswith(("raise ", "raise")):
        return "raise"
    if stripped.startswith(("if ", "elif ", "else:")):
        return "branch"
    if stripped.startswith(("for ", "while ")):
        return "loop"
    if stripped.startswith(("try:", "except", "finally:")):
        return "try_block"
    if stripped.startswith(("with ", "assert ")):
        return "stmt"
    return "code"


def per_file_listing(p: Path) -> str:
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        try:
            text = p.read_text(encoding="cp1251")
        except Exception:
            return ""
    lines = text.splitlines()
    rel = p.relative_to(ROOT).as_posix()
    docs_ranges = set()
    in_doc = False
    doc_start_line = 0
    for i, ln in enumerate(lines, 1):
        n_triple = ln.count('"""') + ln.count("'''")
        if n_triple:
            if not in_doc:
                in_doc = True
                doc_start_line = i
                if n_triple >= 2:
                    docs_ranges.add(i)
                    in_doc = False
            else:
                for j in range(doc_start_line, i + 1):
                    docs_ranges.add(j)
                in_doc = False
        elif in_doc:
            docs_ranges.add(i)

    class_cnt = Counter()
    per_line_kind = []
    for i, ln in enumerate(lines, 1):
        kind = classify_line(ln, i in docs_ranges)
        class_cnt[kind] += 1
        per_line_kind.append(kind)

    out = [f"# ПОСТРОЧНЫЙ ЛИСТИНГ: `{rel}`", "",
           f"**Всего строк:** {len(lines)}", "", "## Классификация строк",
           "| Тип | Кол-во | % |", "|-----|-------:|--:|"]
    total = max(1, len(lines))
    for k, v in class_cnt.most_common():
        out.append(f"| {k} | {v} | {100*v/total:.1f} |")
    out.append("")
    out.append("## Полный листинг с классификацией")
    out.append("```")
    for i, (ln, kind) in enumerate(zip(lines, per_line_kind), 1):
        out.append(f"{i:5d} [{kind:10s}] {ln}")
    out.append("```")
    return "\n".join(out)


def per_file_ast(p: Path) -> str:
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return ""
    rel = p.relative_to(ROOT).as_posix()
    try:
        tree = ast.parse(text)
    except Exception as e:
        return f"# AST-дамп `{rel}`\n\nОШИБКА ПАРСИНГА: {e}\n"
    dump = ast.dump(tree, annotate_fields=True, include_attributes=True, indent=2)
    return f"# AST-дамп `{rel}`\n\n```\n{dump}\n```\n"


def per_file_identifiers(p: Path) -> str:
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return ""
    rel = p.relative_to(ROOT).as_posix()
    try:
        tree = ast.parse(text)
    except Exception:
        return f"# Идентификаторы `{rel}`\n\nОшибка парсинга.\n"
    names, calls, strings, numbers, attrs = (Counter() for _ in range(5))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names[node.id] += 1
        elif isinstance(node, ast.Attribute):
            attrs[node.attr] += 1
        elif isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                calls[fn.id] += 1
            elif isinstance(fn, ast.Attribute):
                calls[fn.attr] += 1
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                if len(node.value) <= 120:
                    strings[node.value] += 1
            elif isinstance(node.value, (int, float)):
                numbers[str(node.value)] += 1

    def dump_counter(title, c):
        L = [f"## {title} (уникальных: {len(c)})", "",
             "| Имя | Использований |", "|-----|--------------:|"]
        for k, v in c.most_common():
            safe = k.replace("|", "\\|").replace("\n", "\\n")
            L.append(f"| `{safe[:120]}` | {v} |")
        return "\n".join(L)

    out = [f"# Идентификаторы `{rel}`", ""]
    out.append(dump_counter("Имена (ast.Name)", names))
    out.append("")
    out.append(dump_counter("Вызванные функции/методы (ast.Call)", calls))
    out.append("")
    out.append(dump_counter("Обращения к атрибутам (.attr)", attrs))
    out.append("")
    out.append(dump_counter("Строковые литералы", strings))
    out.append("")
    out.append(dump_counter("Числовые литералы", numbers))
    return "\n".join(out)


def per_file_gitlog(p: Path) -> str:
    rel = p.relative_to(ROOT).as_posix()
    try:
        log = subprocess.check_output(
            ["git", "-C", str(ROOT), "log", "--follow",
             "--pretty=format:%h %ad %s", "--date=short", "--", rel],
            stderr=subprocess.DEVNULL, timeout=10,
        ).decode("utf-8", errors="replace")
    except Exception as e:
        log = f"(git log недоступен: {e})"
    return f"# История коммитов `{rel}`\n\n```\n{log}\n```\n"


def per_file_grep(p: Path) -> str:
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return ""
    rel = p.relative_to(ROOT).as_posix()
    lines = text.splitlines()
    patterns = {
        "import": re.compile(r"^\s*(import\s|from\s)"),
        "print": re.compile(r"\bprint\("),
        "except": re.compile(r"^\s*except\b"),
        "try": re.compile(r"^\s*try:"),
        "def": re.compile(r"^\s*(async\s+)?def\s"),
        "class": re.compile(r"^\s*class\s"),
        "raise": re.compile(r"\braise\b"),
        "return": re.compile(r"^\s*return\b"),
        "if": re.compile(r"^\s*if\b"),
        "for": re.compile(r"^\s*for\b"),
        "while": re.compile(r"^\s*while\b"),
        "with": re.compile(r"^\s*with\b"),
        "assert": re.compile(r"^\s*assert\b"),
        "todo": re.compile(r"TODO|FIXME|HACK|XXX|BUG", re.I),
        "path_C": re.compile(r"[A-Za-z]:\\\\"),
        "path_home": re.compile(r"/home/|/Users/|/tmp/"),
        "sleep": re.compile(r"\btime\.sleep\("),
        "requests": re.compile(r"\brequests\."),
        "subprocess": re.compile(r"\bsubprocess\."),
        "os_system": re.compile(r"\bos\.system\("),
        "eval": re.compile(r"\beval\("),
        "exec": re.compile(r"\bexec\("),
        "open": re.compile(r"\bopen\("),
        "np": re.compile(r"\bnp\."),
        "sf": re.compile(r"\bsf\."),
    }
    out = [f"# grep-таблицы `{rel}`", ""]
    for name, pat in patterns.items():
        matches = [(i, ln) for i, ln in enumerate(lines, 1) if pat.search(ln)]
        if not matches:
            continue
        out.append(f"## `{name}` — {len(matches)} совпадений")
        out.append("```")
        for i, ln in matches:
            out.append(f"{i:5d} | {ln.rstrip()}")
        out.append("```")
        out.append("")
    return "\n".join(out)


def main():
    files = all_py()
    print(f"Total files: {len(files)}")
    for i, p in enumerate(files, 1):
        rel = p.relative_to(ROOT).as_posix()
        safe = rel.replace("/", "__").replace("\\", "__")
        (DEEP / (safe + ".md")).write_text(per_file_listing(p), encoding="utf-8")
        (AST_DIR / (safe + ".md")).write_text(per_file_ast(p), encoding="utf-8")
        (IDENT_DIR / (safe + ".md")).write_text(per_file_identifiers(p), encoding="utf-8")
        (GITLOG_DIR / (safe + ".md")).write_text(per_file_gitlog(p), encoding="utf-8")
        (GREP_DIR / (safe + ".md")).write_text(per_file_grep(p), encoding="utf-8")
        if i % 30 == 0:
            print(f"  processed {i}/{len(files)}")
    print("Done.")


if __name__ == "__main__":
    from cli_contract import help_or_error

    if help_or_error(__doc__ or "ZS Music Maker tool"):
        raise SystemExit(0)
    main()
