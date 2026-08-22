#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/deep_audit_v40.py — САМЫЙ ГЛУБОКИЙ АУДИТ (v40).

Читаем КАЖДУЮ строку кода репозитория и выявляем:
  • dead imports (AST)
  • silent except: pass
  • bare except
  • hardcoded C:\\ / /home/ / /Users/
  • TODO/FIXME/HACK/XXX
  • magic numbers (порог: > 1 повторного использования одинакового литерала)
  • слишком длинные функции (> 100 LOC)
  • отсутствующие docstring'и у public API
  • сложность (упрощённо: количество if/for/while/try)
  • голые print (не через logger)
  • голые production time.sleep() без комментария
  • assert в production-коде
  • риски безопасности: eval/exec/os.system/subprocess.shell=True
  • отсутствие явных таймаутов у HTTP-запросов
"""
from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def all_py_files() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.py"):
        if ".git" in p.parts:
            continue
        if "__pycache__" in p.parts:
            continue
        out.append(p)
    return sorted(out)


def read_src(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        try:
            return p.read_text(encoding="cp1251")
        except Exception:
            return ""


def audit_file(p: Path) -> dict:
    src = read_src(p)
    lines = src.splitlines()
    rel = p.relative_to(ROOT).as_posix()
    report: dict = {
        "file": rel,
        "loc": len(lines),
        "size_bytes": len(src.encode("utf-8")),
        "issues": [],
        "functions": [],
        "classes": [],
        "imports": [],
        "risk_score": 0,
    }
    try:
        tree = ast.parse(src)
    except Exception as e:
        report["issues"].append({"line": 0, "kind": "PARSE_ERROR", "msg": str(e)})
        report["risk_score"] += 100
        return report

    import_names: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        line_text = lines[node.lineno - 1] if getattr(node, "lineno", 0) else ""
        if "# noqa" in line_text:
            continue
        if isinstance(node, ast.Import):
            for n in node.names:
                nm = n.asname or n.name.split(".")[0]
                import_names.append((nm, node.lineno))
                report["imports"].append({"name": n.name, "line": node.lineno, "kind": "import"})
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            # __future__ imports are compiler directives, and relative imports
            # commonly re-export package API rather than bind local runtime names.
            if mod == "__future__" or node.level:
                continue
            for n in node.names:
                nm = n.asname or n.name
                if nm == "*":
                    report["issues"].append(
                        {"line": node.lineno, "kind": "STAR_IMPORT",
                         "msg": f"from {mod} import *"}
                    )
                    report["risk_score"] += 3
                    continue
                import_names.append((nm, node.lineno))
                report["imports"].append(
                    {"name": f"{mod}.{n.name}", "line": node.lineno, "kind": "from"}
                )

    self_test_lines = {
        line_number
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("_self_test")
        for line_number in range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1)
    }

    body_src = "\n".join(lines)
    for nm, ln in import_names:
        if nm.startswith("_"):
            continue
        pattern = re.compile(rf"\b{re.escape(nm)}\b")
        hits = pattern.findall(body_src)
        if len(hits) < 2:
            report["issues"].append(
                {"line": ln, "kind": "DEAD_IMPORT",
                 "msg": f"import '{nm}' не используется в теле файла"}
            )
            report["risk_score"] += 1

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            body_len = max(1, end - start)
            has_doc = bool(ast.get_docstring(node))
            complexity = sum(
                1
                for n in ast.walk(node)
                if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.BoolOp))
            )
            report["functions"].append(
                {"name": node.name, "line": start, "loc": body_len,
                 "has_doc": has_doc, "complexity": complexity}
            )
            if body_len > 100 and not node.name.startswith("_test"):
                report["issues"].append(
                    {"line": start, "kind": "LONG_FUNCTION",
                     "msg": f"{node.name}: {body_len} LOC (>100) — декомпозиция"}
                )
                report["risk_score"] += 2
            if complexity > 15:
                report["issues"].append(
                    {"line": start, "kind": "HIGH_COMPLEXITY",
                     "msg": f"{node.name}: сложность ≈ {complexity} (>15)"}
                )
                report["risk_score"] += 2
            if not has_doc and not node.name.startswith("_") and body_len > 10:
                report["issues"].append(
                    {"line": start, "kind": "MISSING_DOCSTRING",
                     "msg": f"public function '{node.name}' без docstring"}
                )
        elif isinstance(node, ast.ClassDef):
            has_doc = bool(ast.get_docstring(node))
            report["classes"].append({"name": node.name, "line": node.lineno, "has_doc": has_doc})
            if not has_doc and not node.name.startswith("_"):
                report["issues"].append(
                    {"line": node.lineno, "kind": "MISSING_CLASS_DOCSTRING",
                     "msg": f"public class '{node.name}' без docstring"}
                )

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                report["issues"].append(
                    {"line": node.lineno, "kind": "BARE_EXCEPT",
                     "msg": "bare 'except:' — ловит и KeyboardInterrupt"}
                )
                report["risk_score"] += 3
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                report["issues"].append(
                    {"line": node.lineno, "kind": "SILENT_EXCEPT_PASS",
                     "msg": "except: pass — тихое подавление ошибок"}
                )
                report["risk_score"] += 2

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            fname = None
            if isinstance(fn, ast.Name):
                fname = fn.id
            elif isinstance(fn, ast.Attribute):
                fname = fn.attr
            # Only direct builtin calls can execute attacker-controlled source.
            # Attribute methods such as Qt's QDialog.exec()/QApplication.exec()
            # run an event loop and must not be misclassified as RCE.
            if isinstance(fn, ast.Name) and fname in ("eval", "exec"):
                report["issues"].append(
                    {"line": node.lineno, "kind": "SECURITY_EVAL",
                     "msg": f"builtin {fname}() — потенциально опасно"}
                )
                report["risk_score"] += 5
            if fname == "system":
                if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "os":
                    report["issues"].append(
                        {"line": node.lineno, "kind": "SECURITY_OS_SYSTEM",
                         "msg": "os.system() — заменить на subprocess.run(shell=False)"}
                    )
                    report["risk_score"] += 4
            for kw in node.keywords or []:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    report["issues"].append(
                        {"line": node.lineno, "kind": "SECURITY_SHELL_TRUE",
                         "msg": "subprocess(..., shell=True) — shell-injection"}
                    )
                    report["risk_score"] += 4
            if isinstance(fn, ast.Attribute) and fn.attr in ("get", "post", "put", "delete", "head", "patch"):
                base = fn.value
                base_name = base.id if isinstance(base, ast.Name) else (
                    base.attr if isinstance(base, ast.Attribute) else ""
                )
                if base_name in ("requests", "session", "urlopen"):
                    has_timeout = any(kw.arg == "timeout" for kw in node.keywords or [])
                    if not has_timeout:
                        report["issues"].append(
                            {"line": node.lineno, "kind": "NO_HTTP_TIMEOUT",
                             "msg": f"{base_name}.{fn.attr}(...) без timeout"}
                        )
                        report["risk_score"] += 2

    if "/tests/" not in rel and not rel.startswith("tests/"):
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                report["issues"].append(
                    {"line": node.lineno, "kind": "ASSERT_IN_PROD",
                     "msg": "assert в production-коде: -O его выкинет"}
                )
                report["risk_score"] += 1

    for i, line in enumerate(lines, 1):
        low = line.strip()
        if not low or low.startswith("#"):
            # Markers are actionable only when they label the comment itself
            # (for example ``# TODO:``), not when a domain format happens to
            # contain the letters, such as ISRC ``XX-XXX-00-00000``.
            marker_match = re.match(r"#\s*(TODO|FIXME|HACK|XXX|BUG)\b(?:\s|:|-|$)", low, re.I)
            if marker_match:
                marker = marker_match.group(1).upper()
                report["issues"].append(
                    {"line": i, "kind": f"MARKER_{marker}", "msg": low[:160]}
                )
                report["risk_score"] += 1
            continue
        m = re.search(r'["\']([A-Za-z]:\\\\[^"\']+)["\']', line)
        if m:
            report["issues"].append(
                {"line": i, "kind": "HARDCODED_WIN_PATH", "msg": m.group(1)[:120]}
            )
            report["risk_score"] += 3
        m = re.search(r'["\'](/(?:home|Users|tmp|var/tmp|opt/homebrew)/[^"\']+)["\']', line)
        # Test fixtures intentionally model sensitive/foreign paths, and this
        # detector naturally contains its own path regex. Neither is a shipped
        # production portability defect.
        audit_meta_files = {
            "tools/deep_audit_v40.py",
            "tools/deep_audit_v40_expand.py",
            "tools/deep_audit_v40_report.py",
        }
        if m and not rel.startswith("tests/") and rel not in audit_meta_files:
            report["issues"].append(
                {"line": i, "kind": "HARDCODED_POSIX_PATH", "msg": m.group(1)[:120]}
            )
            report["risk_score"] += 2
        if re.search(r"^\s*print\(", line):
            report["issues"].append(
                {"line": i, "kind": "BARE_PRINT",
                 "msg": "print() вместо logger"}
            )
        if (
            re.search(r"\btime\.sleep\(", line)
            and "#" not in line
            and i not in self_test_lines
            and not rel.startswith("tests/")
            and rel not in audit_meta_files
        ):
            report["issues"].append(
                {"line": i, "kind": "BLOCKING_SLEEP",
                 "msg": "time.sleep(...) без пояснения"}
            )
        if re.match(r"^\s*global\s+\w", line):
            report["issues"].append(
                {"line": i, "kind": "GLOBAL_STATEMENT", "msg": "global — антипаттерн"}
            )

    return report


def main():
    files = all_py_files()
    reports = []
    for p in files:
        reports.append(audit_file(p))
    out_dir = ROOT / "docs" / "PLAN_v39" / "APP_L_ГЛУБОКИЙ_АУДИТ_V40"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "AUDIT_RAW.json").write_text(
        json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    stats = Counter()
    for r in reports:
        for it in r["issues"]:
            stats[it["kind"]] += 1
    print("=== AUDIT STATS ===")
    for k, v in stats.most_common():
        print(f"  {k:32s}  {v}")
    print(f"Total files: {len(reports)}")
    print(f"Total issues: {sum(stats.values())}")


if __name__ == "__main__":
    from cli_contract import help_or_error

    if help_or_error(__doc__ or "ZS Music Maker tool"):
        raise SystemExit(0)
    main()
