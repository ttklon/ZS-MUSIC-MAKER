# -*- coding: utf-8 -*-
"""
modules.hit_factory.autotune — автотюнинг весов жанров/BPM по hits_kpi.

Читает output/hits/hits_kpi.json, предлагает новые HIT_GENRE_WEIGHTS
и BPM_MAP корректировки на основе реальных hit_score.

Ничего не переписывает без --apply, только рекомендации + diff.

Использование:
    python -m modules.hit_factory.autotune
    python -m modules.hit_factory.autotune --apply  # перезапишет config.py (бекап .bak)
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from modules.hit_factory.config import BPM_MAP, HIT_GENRE_WEIGHTS
from modules.hit_factory.kpi import collect_hits

def analyze(output_root: str | Path = "output/hits") -> dict[str, Any]:
    hits = collect_hits(output_root)
    if not hits:
        return {"ok": False, "reason": "no hits yet — run hitmaker first"}
    # группируем по жанру
    by_genre: dict[str, list[float]] = {}
    by_bpm: dict[str, list[float]] = {}
    for h in hits:
        by_genre.setdefault(h["genre"], []).append(h["hit_score"])
        # bpm из report
        try:
            rep = json.loads(Path(h["path"]).read_text(encoding="utf-8"))
            bpm = rep.get("desktop_recipe_snapshot", {}).get("recipe", {}).get("bpm_override") or rep.get("recipe", {}).get("bpm_override") or 0
            if bpm:
                # bucket BPM
                bucket = f"{int(bpm//10*10)}-{int(bpm//10*10+10)}"
                by_bpm.setdefault(bucket, []).append(h["hit_score"])
        except Exception:
            pass

    genre_avg = {g: round(sum(v)/len(v),2) for g,v in by_genre.items()}
    bpm_avg = {b: round(sum(v)/len(v),2) for b,v in by_bpm.items()}

    # рекомендации по весам: жанры с avg >=68 +0.1, <=50 -0.1 (клип 0.2..1.2)
    weight_deltas = {}
    for genre, avg in genre_avg.items():
        cur = HIT_GENRE_WEIGHTS.get(genre)
        if cur is None:
            continue
        if avg >= 68:
            delta = 0.1
        elif avg >= 60:
            delta = 0.05
        elif avg <= 50:
            delta = -0.1
        elif avg <= 55:
            delta = -0.05
        else:
            delta = 0.0
        if delta:
            new_w = round(max(0.2, min(1.2, cur + delta)), 2)
            weight_deltas[genre] = {"cur": cur, "avg": avg, "delta": delta, "new": new_w}

    # BPM рекомендации: просто отчёт, не трогаем BPM_MAP автоматом (требует ручной проверки sweet spot)
    bpm_recs = []
    for bucket, avg in sorted(bpm_avg.items(), key=lambda x: -x[1])[:5]:
        bpm_recs.append(f"BPM {bucket}: avg {avg}")

    return {
        "ok": True,
        "total": len(hits),
        "genre_avg": genre_avg,
        "bpm_avg": bpm_avg,
        "weight_deltas": weight_deltas,
        "top_bpm": bpm_recs,
        "hits": hits[-5:],
    }

def apply_weights(weight_deltas: dict[str, dict], config_path: str | Path = "modules/hit_factory/config.py") -> dict[str, Any]:
    cfg = Path(config_path)
    if not cfg.exists():
        return {"ok": False, "reason": f"config not found: {cfg}"}
    text = cfg.read_text(encoding="utf-8")
    # бекап
    bak = cfg.with_suffix(".py.bak")
    shutil.copyfile(cfg, bak)
    # патчим веса построчно
    new_lines = []
    for line in text.splitlines():
        patched = False
        for genre, info in weight_deltas.items():
            # ищем строку "genre": вес
            if f'"{genre}"' in line and ":" in line and "HIT_GENRE_WEIGHTS" not in line:
                # заменяем вес на new
                # простая эвристика: ищем число после :
                import re
                m = re.search(r'("'+genre+r'"\s*:\s*)([0-9.]+)', line)
                if m:
                    line = line[:m.start(2)] + str(info["new"]) + line[m.end(2):]
                    patched = True
                    break
        new_lines.append(line)
    cfg.write_text("\n".join(new_lines), encoding="utf-8")
    return {"ok": True, "bak": str(bak), "patched": len(weight_deltas)}

def _cli() -> int:
    import argparse, json as js
    p = argparse.ArgumentParser(description="HIT FACTORY autotune — рекомендации по весам")
    p.add_argument("--output", type=str, default="output/hits", help="корень хитов")
    p.add_argument("--apply", action="store_true", help="применить новые веса в config.py")
    p.add_argument("--json", action="store_true", help="json в stdout")
    args = p.parse_args()
    res = analyze(args.output)
    if args.json:
        print(js.dumps(res, ensure_ascii=False, indent=2))
    else:
        if not res.get("ok"):
            print(f"[!] {res.get('reason')}")
            return 1
        print("=== HIT FACTORY AUTOTUNE ===")
        print(f"Всего хитов: {res['total']}")
        print("Жанр → avg:")
        for g,a in sorted(res["genre_avg"].items(), key=lambda x: -x[1]):
            print(f"  {g:20s} {a:5.1f}")
        if res["weight_deltas"]:
            print("\nРекомендуемые правки HIT_GENRE_WEIGHTS:")
            for g,inf in sorted(res["weight_deltas"].items(), key=lambda x: -x[1]["delta"]):
                print(f"  {g:20s} {inf['cur']} → {inf['new']} (avg {inf['avg']}, delta {inf['delta']:+.2f})")
            if args.apply:
                ap = apply_weights(res["weight_deltas"])
                print(f"\n[applied] бекап {ap.get('bak')}, патчей {ap.get('patched')}")
            else:
                print("\n[сухой прогон] добавь --apply чтобы переписать config.py")
        else:
            print("\nВеса в норме, правок не нужно.")
        if res["top_bpm"]:
            print("\nТоп BPM-бакеты:")
            for b in res["top_bpm"]:
                print(f"  {b}")
    return 0

if __name__ == "__main__":
    raise SystemExit(_cli())
