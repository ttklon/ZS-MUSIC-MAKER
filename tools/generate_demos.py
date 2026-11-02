# -*- coding: utf-8 -*-
"""tools/generate_demos.py — пять демо в пяти жанрах + отчёт прогона (план 4.8).

Запускает полный конвейер на CPU (без тяжёлых ИИ-моделей), складывает готовые
мастера и сводный отчёт:

    python tools/generate_demos.py                 # 5 жанров по умолчанию, 75 с
    python tools/generate_demos.py --duration 60 --out output/demos

Что проверяется по каждому демо (и попадает в `demos_report.json`):
* статусы стадий (нет FAILED; BLOCKED — только отсутствующие зависимости);
* гейты микса (§7.2) и мастеринга по 8 стендам;
* громкость, true peak, crest, корреляция, hit-score (если посчитан).

Скрипт ничего не «округляет в пользу результата»: все цифры — из отчётов
стадий, поэтому его вывод можно показывать как есть.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_DEMOS = (
    ("drift_phonk", "ночь, дрифт, огни города"),
    ("trap", "деньги, скорость, ледяной блеск"),
    ("house", "клуб, рассвет, мокрый асфальт"),
    ("hard_rock", "рёв мотора, ярость, пыль"),
    ("dark_ambient", "пустой терминал, туман, ожидание"),
)


def _demo_one(genre: str, theme: str, seed: int, duration: int, out_root: Path) -> dict:
    from app.core.orchestrator import run_full_pipeline

    project = f"demo_{genre}"
    started = time.time()
    result = run_full_pipeline(
        project,
        {"genre": genre, "theme": theme, "seed": seed, "duration_sec": duration},
        out_root=out_root / project,
    )
    stages = {stage.get("name"): stage for stage in result.get("stages", [])}
    master_stage = stages.get("_stage_mastering", {})
    master_out = master_stage.get("output") or {}
    mix_stage = stages.get("_stage_mix_and_sidechain", {})
    mix_out = mix_stage.get("output") or {}
    score_stage = stages.get("_stage_hit_score", {})
    score_out = score_stage.get("output") or {}

    masters = (master_out.get("masters") or {})
    streaming = Path(masters.get("streaming", "")) if masters.get("streaming") else None
    demo_wav = out_root / "demos" / f"{genre}_streaming.wav"
    if streaming and streaming.exists():
        demo_wav.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(streaming, demo_wav)

    return {
        "genre": genre,
        "theme": theme,
        "seed": seed,
        "project_dir": str(out_root / project),
        "wav": str(demo_wav) if demo_wav.exists() else None,
        "elapsed_sec": round(time.time() - started, 1),
        "status_summary": result.get("status_summary", {}),
        "warnings": result.get("warnings", []),
        "mix": {
            "gates": mix_out.get("gates", {}),
            "gates_passed": mix_out.get("gates_passed"),
            "metrics": mix_out.get("metrics", {}),
        },
        "mastering": master_out.get("summary", {}),
        "mastering_gates": master_out.get("failed_gates", {}),
        "master_streaming": (master_out.get("reports") or {}).get("streaming", {}),
        "master_stands": {
            stand: {
                key: report.get(key)
                for key in ("lufs", "true_peak_dbtp", "crest_db", "stereo_correlation")
            }
            for stand, report in (master_out.get("reports") or {}).items()
        },
        "hit_score": {
            "score": score_out.get("hit_score"),
            "verdict": score_out.get("verdict"),
            "metrics": {
                name: value.get("score")
                for name, value in (score_out.get("metrics") or {}).items()
                if isinstance(value, dict)
            },
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Сгенерировать 5 демо в 5 жанрах")
    parser.add_argument("--duration", type=int, default=75, help="длительность каждого демо, с")
    parser.add_argument("--seed", type=int, default=101, help="базовый seed (жанр получает seed+индекс)")
    parser.add_argument("--out", default="output/demos_run", help="каталог прогонов")
    parser.add_argument("--json", action="store_true", help="напечатать только JSON")
    args = parser.parse_args(argv)

    out_root = Path(args.out)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    demos_dir = out_root / "demos"
    demos_dir.mkdir(parents=True, exist_ok=True)

    reports = []
    for index, (genre, theme) in enumerate(DEFAULT_DEMOS):
        seed = args.seed + index
        if not args.json:
            print(f"[{index + 1}/{len(DEFAULT_DEMOS)}] {genre} (seed={seed})…", flush=True)
        report = _demo_one(genre, theme, seed, args.duration, out_root)
        reports.append(report)
        if not args.json:
            mix_ok = report["mix"]["gates_passed"]
            master_ok = (report["mastering"] or {}).get("gates_passed")
            print(
                f"    микс §7.2: {'OK' if mix_ok else 'FAIL'} | "
                f"мастеринг 8 стендов: {'OK' if master_ok else 'FAIL'} | "
                f"{report['elapsed_sec']} с",
                flush=True,
            )

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration_sec": args.duration,
        "demos": reports,
        "all_mix_gates_passed": all(item["mix"]["gates_passed"] for item in reports),
        "all_mastering_gates_passed": all(
            (item["mastering"] or {}).get("gates_passed") for item in reports
        ),
    }
    report_path = demos_dir / "demos_report.json"
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"\nОтчёт: {report_path}")
        for item in reports:
            master = item.get("master_streaming") or {}
            print(
                f"  {item['genre']:14s} {str(item['wav']).split('/')[-1]:28s} "
                f"микс {item['mix']['metrics'].get('lufs')} LUFS · мастер "
                f"{master.get('lufs')} LUFS / {master.get('true_peak_dbtp')} dBTP / "
                f"crest {master.get('crest_db')} дБ"
            )
        print(
            "Итог: микс "
            + ("OK" if payload["all_mix_gates_passed"] else "FAIL")
            + ", мастеринг "
            + ("OK" if payload["all_mastering_gates_passed"] else "FAIL")
        )
    return 0 if payload["all_mix_gates_passed"] and payload["all_mastering_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
