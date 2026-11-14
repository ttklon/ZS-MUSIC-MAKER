# -*- coding: utf-8 -*-
"""
modules.hit_factory.benchmark — A/B бенчмарк жанров/BPM/aggression.

Генерит N треков по матрице жанров, меряет hit_score, выводит таблицу
и рекомендации для тюнинга HIT_GENRE_WEIGHTS и BPM_MAP.
Полностью бесплатно (DSP only).

Использование:
    python -m modules.hit_factory.benchmark --count 2 --duration 30
    # count = треков на каждый жанр
"""
from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any

from modules.hit_factory.config import HIT_GENRE_WEIGHTS, TOP_GENRES_FOR_HELP
from modules.hit_factory.generator import HitFactory


def benchmark(
    genres: list[str] | None = None,
    per_genre: int = 2,
    duration: int = 30,
    seed: int = 42,
    output_root: str = "output/hits",
    evolve: bool = False,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Прогоняет per_genre треков каждого жанра, возвращает сводку.
    """
    if genres is None:
        # топ-10 хитовых для бенчмарка по умолчанию
        genres = TOP_GENRES_FOR_HELP
    # фильтруем только известные веса
    genres = [g for g in genres if g in HIT_GENRE_WEIGHTS] or list(HIT_GENRE_WEIGHTS.keys())[:6]

    factory = HitFactory(output_root=output_root, evolve=evolve, verbose=verbose, duration_sec=duration)
    rng = random.Random(seed)
    results: dict[str, list[dict]] = {g: [] for g in genres}
    all_hits: list[dict] = []

    start_ts = time.time()
    for genre in genres:
        for i in range(per_genre):
            cur_seed = rng.randint(1, 1_000_000)
            hit = factory.make_one(genre=genre, seed=cur_seed, duration_sec=duration, evolve=evolve)
            entry = {
                "genre": genre,
                "seed": cur_seed,
                "hit_score": float(hit.get("hit_score") or 0),
                "verdict": hit.get("verdict"),
                "master_path": hit.get("master_path"),
                "project_id": hit.get("project_id"),
                "bpm": hit.get("wizard_state", {}).get("bpm_override"),
                "aggression": hit.get("wizard_state", {}).get("aggression"),
            }
            results[genre].append(entry)
            all_hits.append(entry)

    # сводка по жанрам
    summary = {}
    for g, lst in results.items():
        scores = [x["hit_score"] for x in lst]
        avg = sum(scores) / max(1, len(scores))
        mx = max(scores) if scores else 0
        mn = min(scores) if scores else 0
        solid_cnt = sum(1 for s in scores if s >= 68)
        chart_cnt = sum(1 for s in scores if s >= 82)
        summary[g] = {
            "avg": round(avg, 2),
            "max": round(mx, 2),
            "min": round(mn, 2),
            "solid_rate": round(solid_cnt / max(1, len(lst)) * 100, 1),
            "chart_rate": round(chart_cnt / max(1, len(lst)) * 100, 1),
            "samples": len(lst),
        }

    # общий топ
    sorted_all = sorted(all_hits, key=lambda x: x["hit_score"], reverse=True)
    top3 = sorted_all[:3]
    global_avg = round(sum(x["hit_score"] for x in all_hits) / max(1, len(all_hits)), 2)

    report = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "duration_sec": round(time.time() - start_ts, 1),
        "params": {"genres": genres, "per_genre": per_genre, "duration": duration, "seed": seed, "evolve": evolve},
        "summary_by_genre": summary,
        "global_avg": global_avg,
        "top3": top3,
        "all": all_hits,
    }

    # рекомендации
    recs = []
    # жанры с avg < 55 — кандидаты на понижение веса или BPM-фикс
    weak = [g for g, s in summary.items() if s["avg"] < 55]
    strong = [g for g, s in summary.items() if s["avg"] >= 68]
    if weak:
        recs.append(f"Слабые жанры (avg<55): {', '.join(weak)} — проверь BPM sweet spot или понизь вес в HIT_GENRE_WEIGHTS")
    if strong:
        recs.append(f"Сильные жанры (avg≥68 solid): {', '.join(strong)} — повысь вес/часто используй в фабрике")
    # BPM advice
    low_bpm = [x for x in all_hits if x["hit_score"] < 50 and x.get("bpm", 120) < 100]
    if len(low_bpm) >= 2:
        recs.append("Треки с BPM вне dance sweet spot чаще flop — держи trap 70-95 или dance 120-144")
    report["recommendations"] = recs

    # сохраняем
    out_path = Path(output_root) / f"benchmark_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["saved_to"] = str(out_path)

    if verbose:
        print("\n=== HIT FACTORY BENCHMARK ===")
        for g, s in sorted(summary.items(), key=lambda kv: kv[1]["avg"], reverse=True):
            print(f"  {g:20s} avg {s['avg']:5.1f}  max {s['max']:5.1f}  solid {s['solid_rate']:4.1f}% ({s['samples']} треков)")
        print(f"  GLOBAL AVG: {global_avg:.1f}")
        print("  TOP3:")
        for t in top3:
            print(f"    {t['genre']:15s} score {t['hit_score']:5.1f} {t['verdict']:10s} BPM {t['bpm']} seed {t['seed']}")
        if recs:
            print("  RECOMMENDATIONS:")
            for r in recs:
                print(f"    - {r}")
        print(f"  Saved: {out_path}")

    return report


def _cli() -> int:
    import argparse

    p = argparse.ArgumentParser(description="HIT FACTORY benchmark — A/B по жанрам (бесплатно)")
    p.add_argument("--genres", type=str, default="", help="через запятую жанры (пусто=топ-10)")
    p.add_argument("--count", type=int, default=2, help="треков на жанр")
    p.add_argument("--duration", type=int, default=30, help="длительность трека сек")
    p.add_argument("--seed", type=int, default=42, help="базовый seed")
    p.add_argument("--output", type=str, default="output/hits", help="куда")
    p.add_argument("--evolve", action="store_true", help="включить эволюцию в бенчмарке")
    args = p.parse_args()

    genres = [g.strip() for g in args.genres.split(",") if g.strip()] if args.genres else None
    benchmark(genres=genres, per_genre=args.count, duration=args.duration, seed=args.seed, output_root=args.output, evolve=args.evolve, verbose=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
