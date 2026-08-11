# -*- coding: utf-8 -*-
"""
ZS Music Maker v14 — tools/fallback_audit.py (P0.15)

Сканирует modules/, app/, agents/, tools/, updater/ и ищет fallback-пути:
  — pitch_shift, apply_gain, silence_stub, pink_noise, sine_stub;
  — dry_run, placeholder, FALLBACK_USED, shutil.copy.

Формирует отчёт output/audit_v14/fallback_report.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]

SCAN_DIRS = ["modules", "app", "agents", "tools", "updater"]
BAD_PATTERNS = {
    "pitch_shift_as_rvc": r"librosa\.effects\.pitch_shift",
    "apply_gain_as_master": r"\.apply_gain\s*\(",
    "silence_stub":        r"silence_stub|_silence_stub",
    "pink_noise":          r"pink_noise|_pink_noise",
    "sine_stub":           r"synthesize_sine|_sine_stub",
    "dry_run":             r"dry_run\s*=\s*True|\"dry_run\":\s*True",
    "placeholder":         r"placeholder|style_vector_placeholder",
    "fallback_var":        r"FALLBACK_USED|fallback_used",
    "shutil_copy_master":  r"shutil\.copy.*master",
    # v18: регресс-страж бага v16, когда бит дакался сам собой
    # (apply_sidechain(beat, beat)) вместо bus по кику
    "sidechain_self_duck": r"apply_sidechain\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*\1\s*,",
}

# v18: сниппеты с этой меткой — осознанный, задокументированный DSP
# (например pitch-shift для бэкинг-гармонии), а НЕ подмена RVC.
LEGIT_MARKERS = ("ZSMM_NOT_RVC", "ZSMM_LEGIT", "noqa: ZSMM")


SELF_SKIP = {"tools/fallback_audit.py"}


def _is_hard_refusal(text: str, def_line: str) -> bool:
    """v18: deprecated-функция, которая сразу бросает RuntimeError
    и НЕ вызывается в пайплайне — честный отказ, а не скрытый fallback.
    Пример: _pink_noise_fallback в musicgen_texture (P0.06)."""
    name = def_line.split("def ", 1)[1].split("(", 1)[0].strip()
    # тело функции должно содержать raise RuntimeError
    m = re.search(r"def\s+" + re.escape(name) + r"\s*\(.*?\n(.*?)(?=\ndef\s|\Z)",
                  text, re.DOTALL)
    if not m:
        return False
    body = m.group(1)
    if "raise RuntimeError" not in body:
        return False
    # функция не должна вызываться нигде, кроме собственного объявления
    calls = re.findall(re.escape(name) + r"\s*\(", text)
    return len(calls) <= 1  # только само объявление


def scan_file(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    rel = str(path.relative_to(ROOT))
    if rel in SELF_SKIP:
        return {}
    hits: Dict[str, List[Dict[str, Any]]] = {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return hits
    for tag, pat in BAD_PATTERNS.items():
        for m in re.finditer(pat, text):
            line_no = text[:m.start()].count("\n") + 1
            snippet = text.splitlines()[line_no - 1].strip() \
                if line_no - 1 < len(text.splitlines()) else ""
            # v18: явно помеченные легитимные применения — не флаг
            if any(mk in snippet for mk in LEGIT_MARKERS):
                continue
            # v18: hard-refusal (raise RuntimeError / deprecated-stub,
            # который НЕ вызывается в пайплайне) — честный отказ, не флаг
            if snippet.startswith("def ") and _is_hard_refusal(text, snippet):
                continue
            hits.setdefault(tag, []).append({
                "file": str(path.relative_to(ROOT)),
                "line": line_no,
                "snippet": snippet[:140],
            })
    return hits


def scan_all() -> Dict[str, Any]:
    all_hits: Dict[str, List[Dict[str, Any]]] = {}
    files_scanned = 0
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if "__pycache__" in str(p):
                continue
            files_scanned += 1
            h = scan_file(p)
            for tag, entries in h.items():
                all_hits.setdefault(tag, []).extend(entries)

    summary = {tag: len(entries) for tag, entries in all_hits.items()}
    red_flags = {}
    for tag in ("pitch_shift_as_rvc", "pink_noise", "sine_stub",
                "silence_stub", "sidechain_self_duck"):
        if tag in all_hits:
            real = [e for e in all_hits[tag]
                    if "legacy/" not in e["file"]
                    and not e["snippet"].lstrip().startswith("#")]
            if real:
                red_flags[tag] = real

    return {
        "files_scanned": files_scanned,
        "summary": summary,
        "red_flags": red_flags,
        "all_hits": all_hits,
    }


def main() -> int:
    r = scan_all()
    out_dir = ROOT / "output" / "audit_v14"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "fallback_report.json"
    out.write_text(json.dumps(r, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(json.dumps({"files_scanned": r["files_scanned"],
                      "summary": r["summary"],
                      "red_flags_count": {k: len(v) for k, v in r["red_flags"].items()},
                      "report": str(out)},
                     ensure_ascii=False, indent=2))
    return 0 if not r["red_flags"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
