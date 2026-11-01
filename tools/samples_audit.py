# -*- coding: utf-8 -*-
"""
tools/samples_audit.py — аудит сэмплового банка перед релизом.

Проверяет: лицензия у каждого файла (CC0/CC-BY/public domain), наличие
`source`, совпадение SHA-256, покрытие инструментов и наличие ≥3 velocity-слоёв
и ≥2 round-robin вариантов на инструмент. Пишет отчёт и, если попросить,
`licenses.txt` для релизного пакета.

    python tools/samples_audit.py
    python tools/samples_audit.py --json
    python tools/samples_audit.py --licenses-output output/licenses.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.audio.samples import INSTRUMENTS, capability, iter_entries, load_bank  # noqa: E402

REPORT_PATH = ROOT / "output" / "samples_audit.json"


def audit(min_layers: int = 3, min_variants: int = 2) -> dict[str, object]:
    bank = load_bank(verify_hash=True)
    entries = list(iter_entries(bank))

    rejected = [
        {"file": str(entry.path.relative_to(ROOT)) if entry.path.is_relative_to(ROOT) else str(entry.path),
         "instrument": entry.instrument,
         "license": entry.license,
         "problems": entry.problems}
        for entry in entries
        if not entry.allowed
    ]

    coverage: dict[str, dict[str, int]] = {}
    for instrument in INSTRUMENTS:
        usable = bank.usable(instrument)
        layers = len({round(entry.velocity, 3) for entry in usable})
        variants = len({entry.round_robin for entry in usable})
        coverage[instrument] = {"samples": len(usable), "velocity_layers": layers, "variants": variants}

    thin = [
        name
        for name, stats in coverage.items()
        if stats["samples"] and (stats["velocity_layers"] < min_layers or stats["variants"] < min_variants)
    ]
    missing = [name for name, stats in coverage.items() if not stats["samples"]]

    report = {
        "capability": capability(bank),
        "n_samples": len(entries),
        "rejected": rejected,
        "coverage": coverage,
        "instruments_missing": missing,
        "instruments_thin": thin,
        "warnings": list(bank.warnings),
        "ok": not rejected and not missing and not thin,
    }
    return report


def licenses_text(report: dict[str, object]) -> str:
    bank = load_bank()
    lines = [
        "# Сторонние сэмплы в релизе",
        "",
        f"Всего сэмплов: {report['n_samples']}",
        "",
    ]
    any_entry = False
    for instrument in INSTRUMENTS:
        usable = bank.usable(instrument)
        if not usable:
            continue
        any_entry = True
        lines.append(f"## {instrument}")
        for entry in usable:
            lines.append(f"- `{entry.path.name}` — {entry.license}, {entry.source}")
        lines.append("")
    if not any_entry:
        lines.append("Банк пуст: сторонних сэмплов нет, весь звук синтезирован процедурно.")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit the ZS Music Maker sample bank")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--licenses-output", default="", help="write licenses.txt to this path")
    parser.add_argument("--min-layers", type=int, default=3, help="minimum velocity layers per instrument")
    parser.add_argument("--min-variants", type=int, default=2, help="minimum round-robin variants per instrument")
    args = parser.parse_args(argv)

    report = audit(min_layers=args.min_layers, min_variants=args.min_variants)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.licenses_output:
        target = Path(args.licenses_output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(licenses_text(report), encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 1

    print(f"samples_audit: {report['n_samples']} сэмплов, отчёт → {REPORT_PATH.relative_to(ROOT)}")
    for name, stats in report["coverage"].items():
        mark = "ok" if stats["samples"] else "—"
        print(
            f"  {name:10s} {stats['samples']:3d} файлов · {stats['velocity_layers']} слоёв · "
            f"{stats['variants']} вариантов  [{mark}]"
        )
    if report["rejected"]:
        print("  отвергнуто:")
        for row in report["rejected"]:
            print(f"    {row['file']}: {', '.join(row['problems'])}")
    for warning in report["warnings"]:
        print(f"  ! {warning}")
    print("результат:", "OK" if report["ok"] else "есть замечания (см. отчёт)")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
