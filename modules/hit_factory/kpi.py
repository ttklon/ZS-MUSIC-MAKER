# -*- coding: utf-8 -*-
"""
modules.hit_factory.kpi — агрегатор KPI для фабрики хитов.

Собирает сводку по всем хитам в output/hits/:
  - средний hit_score, распределение verdict, лучший/худший, динамика по времени
  - сохраняет output/hits/hits_kpi.json и output/hits/hits_kpi.md
  - интегрируется с modules.kpi_dashboard (читает hits_kpi как источник)
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def collect_hits(output_root: str | Path = "output/hits") -> list[dict[str, Any]]:
    root = Path(output_root)
    hits = []
    for p in root.glob("hit_*/report.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            # hit_score из hit_report или из stages
            hit_score = None
            verdict = data.get("verdict")
            # пробуем hit_report.json рядом
            hr = p.parent / "hit_report.json"
            if hr.exists():
                try:
                    h = json.loads(hr.read_text(encoding="utf-8"))
                    hit_score = h.get("hit_score")
                    verdict = h.get("verdict") or verdict
                except Exception:
                    pass
            if hit_score is None:
                # ищем в stages
                for st in data.get("stages", []):
                    if st.get("name") == "_stage_hit_score":
                        hit_score = (st.get("output") or {}).get("hit_score")
                        verdict = (st.get("output") or {}).get("verdict") or verdict
                        break
            hits.append({
                "project_id": data.get("project_id") or p.parent.name,
                "hit_score": float(hit_score) if hit_score is not None else 0.0,
                "verdict": verdict or "unknown",
                "genre": (data.get("recipe") or {}).get("genre") or data.get("desktop_recipe_snapshot", {}).get("recipe", {}).get("genre", "unknown"),
                "duration_sec": (data.get("desktop_recipe_snapshot", {}).get("recipe", {}).get("duration_sec") or 0),
                "master_path": data.get("master_path"),
                "finished_at": data.get("finished_at"),
                "path": str(p),
            })
        except Exception:
            continue
    # сортировка по времени
    hits.sort(key=lambda x: x.get("finished_at") or 0)
    return hits


def build_kpi(output_root: str | Path = "output/hits", save: bool = True) -> dict[str, Any]:
    hits = collect_hits(output_root)
    total = len(hits)
    if total == 0:
        kpi = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "total": 0,
            "avg_score": 0,
            "verdict_dist": {},
            "genre_avg": {},
            "best": None,
            "worst": None,
            "hits": [],
        }
    else:
        avg = sum(h["hit_score"] for h in hits) / total
        verdict_dist: dict[str, int] = {}
        genre_scores: dict[str, list[float]] = {}
        for h in hits:
            verdict_dist[h["verdict"]] = verdict_dist.get(h["verdict"], 0) + 1
            genre_scores.setdefault(h["genre"], []).append(h["hit_score"])
        genre_avg = {g: round(sum(v)/len(v), 2) for g, v in genre_scores.items()}
        best = max(hits, key=lambda x: x["hit_score"])
        worst = min(hits, key=lambda x: x["hit_score"])
        # динамика: последние 5 vs предыдущие 5
        last5 = hits[-5:]
        last5_avg = round(sum(x["hit_score"] for x in last5)/len(last5), 2) if last5 else 0
        kpi = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "total": total,
            "avg_score": round(avg, 2),
            "last5_avg": last5_avg,
            "verdict_dist": verdict_dist,
            "genre_avg": genre_avg,
            "best": best,
            "worst": worst,
            "hits": hits[-20:],  # последние 20 для отчёта
        }

    if save:
        root = Path(output_root)
        root.mkdir(parents=True, exist_ok=True)
        # json
        (root / "hits_kpi.json").write_text(json.dumps(kpi, ensure_ascii=False, indent=2), encoding="utf-8")
        # markdown
        md = _render_md(kpi)
        (root / "hits_kpi.md").write_text(md, encoding="utf-8")

    return kpi


def _render_md(kpi: dict[str, Any]) -> str:
    lines = [
        "# HIT FACTORY KPI",
        f"_Generated: {kpi['ts']}_",
        "",
        f"**Всего хитов: {kpi['total']}** | **Средний score: {kpi['avg_score']}** | **Последние 5 avg: {kpi.get('last5_avg',0)}**",
        "",
    ]
    if kpi["total"] == 0:
        lines.append("_Пока нет хитов — запусти `python hitmaker.py --count 5`_")
        return "\n".join(lines) + "\n"
    lines.append("## Распределение verdict")
    for v, cnt in sorted(kpi["verdict_dist"].items(), key=lambda x: -x[1]):
        lines.append(f"- **{v}**: {cnt}")
    lines.append("")
    lines.append("## Средний по жанрам")
    for g, avg in sorted(kpi["genre_avg"].items(), key=lambda x: -x[1]):
        lines.append(f"- `{g}`: {avg}")
    lines.append("")
    if kpi.get("best"):
        b = kpi["best"]
        lines.append(f"## Лучший: {b['project_id']} — {b['hit_score']} {b['verdict']} ({b['genre']})")
        lines.append(f"  `master: {b['master_path']}`")
        lines.append("")
    if kpi.get("worst"):
        w = kpi["worst"]
        lines.append(f"## Худший: {w['project_id']} — {w['hit_score']} {w['verdict']} ({w['genre']})")
        lines.append("")
    lines.append("## Последние хиты (до 20)")
    lines.append("| # | project_id | genre | score | verdict |")
    lines.append("|---|------------|-------|-------|---------|")
    for i, h in enumerate(reversed(kpi["hits"]), 1):
        lines.append(f"| {i} | {h['project_id']} | {h['genre']} | {h['hit_score']} | {h['verdict']} |")
    return "\n".join(lines) + "\n"


def _cli() -> int:
    import argparse

    p = argparse.ArgumentParser(description="HIT FACTORY KPI — агрегатор")
    p.add_argument("--output", type=str, default="output/hits", help="корень хитов")
    p.add_argument("--json", action="store_true", help="вывести json в stdout")
    args = p.parse_args()
    kpi = build_kpi(args.output, save=True)
    if args.json:
        print(json.dumps(kpi, ensure_ascii=False, indent=2))
    else:
        print(_render_md(kpi))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
