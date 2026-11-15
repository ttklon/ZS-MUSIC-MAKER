#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hitmaker.py — Однострочный лаунчер фабрики хитов + ПРОРЫВ.

Полностью бесплатно, нероншно, как человек.
От референсов (любой артист) до хита — 1 вызов.

Примеры:
    python hitmaker.py                          # 1 случайный хит
    python hitmaker.py --count 5                # 5 хитов батчем
    python hitmaker.py --genre trap --theme "ночь, деньги, движ" --count 3
    python hitmaker.py --count 10 --evolve --min-score 68 --duration 90
    python hitmaker.py --seed 42 --genre drift_phonk
    # ПРОРЫВ: от референсов ICEGERGERT до хита с RVC и MusicGen CPU чанками (медленно но не фризит)
    python hitmaker.py --breakthrough --artist ICEGERGERT --refs ref1.mp3,ref2.mp3 --theme "ночь, движ" --count 1
    python hitmaker.py --breakthrough --voice raw.wav --duration 90
    ZSMM_BREAKTHROUGH=1 python hitmaker.py --count 5 --evolve  # тоже прорыв через env

Результат: output/hits/<project_id>/master.wav + hit_report.json
Документация: docs/HIT_FACTORY_PLAN.md, HIT_QUICKSTART.md
"""
from __future__ import annotations

import argparse
import json
import os


def _parse_refs(s: str) -> list[str]:
    return [p.strip() for p in s.split(",") if p.strip()] if s else []


def _run_standard(args) -> int:
    from modules.hit_factory.generator import HitFactory
    factory = HitFactory(output_root=args.output, min_score=args.min_score, evolve=args.evolve, verbose=True,
                         duration_sec=args.duration)
    # форсим breakthrough адаптив если флаг/ENV
    if args.breakthrough or os.getenv("ZSMM_BREAKTHROUGH", "").strip() in ("1", "true", "yes"):
        try:
            from modules.hit_factory.adaptive import get_adaptive_config
            factory.adaptive_cfg = get_adaptive_config(overrides={"breakthrough": True})
            print(f"[hitmaker breakthrough] {factory.adaptive_cfg.get('level_name')} | {factory.adaptive_cfg.get('note')}")
        except Exception as _exc:
            print(f"[hitmaker] ignored: {_exc}")
    if args.count <= 1:
        hit = factory.make_one(genre=args.genre or None, theme=args.theme or None, seed=args.seed, duration_sec=args.duration)
        print(json.dumps(hit, ensure_ascii=False, indent=2, default=str))
        return 0 if hit.get("master_path") else 1
    batch = factory.make_batch(count=args.count, genre=args.genre or None, theme=args.theme or None, seed=args.seed, duration_sec=args.duration)
    print(json.dumps(batch, ensure_ascii=False, indent=2, default=str))
    return 0


def _run_breakthrough(args) -> int:
    from modules.hit_factory.breakthrough import full_orchestrate
    refs = _parse_refs(args.refs or "")
    artist = args.artist or "ICEGERGERT"
    theme = args.theme or None
    # genre not separate in breakthrough — genre infer from refs/dossier; but allow genre→theme hint
    if args.genre and not theme:
        theme = args.genre
    dur = int(args.duration) if args.duration else 90
    if args.count <= 1:
        res = full_orchestrate(artist=artist, theme=theme, reference_paths=refs or None,
                               raw_voice_path=args.voice or None, duration_sec=dur, seed=args.seed, breakthrough=True, output_root=args.output)
        print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
        hit = res.get("hit") or {}
        return 0 if hit.get("master_path") else 1
    # batch: sequential full_orchestrate
    results = []
    for i in range(args.count):
        cur_seed = (int(args.seed) + i) if args.seed is not None else None
        res = full_orchestrate(artist=artist, theme=theme, reference_paths=refs or None,
                               raw_voice_path=args.voice or None, duration_sec=dur, seed=cur_seed, breakthrough=True, output_root=args.output)
        results.append(res)
        hit = res.get("hit") or {}
        print(f"[hitmaker breakthrough] {i+1}/{args.count} -> {hit.get('project_id')} score={hit.get('hit_score')}")
    print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    ok = sum(1 for r in results if (r.get("hit") or {}).get("master_path"))
    return 0 if ok else 1


def _cli() -> int:
    p = argparse.ArgumentParser(description="ZS HIT FACTORY — автономная фабрика хитов (бесплатно) + ПРОРЫВ")
    p.add_argument("--count", type=int, default=1, help="сколько треков генерить")
    p.add_argument("--genre", type=str, default="", help="фиксированный жанр (пусто = рандом хитовый)")
    p.add_argument("--theme", type=str, default="", help="тема (пусто = авто из трендов 2026)")
    p.add_argument("--seed", type=int, default=None, help="базовый seed (детерминизм)")
    p.add_argument("--duration", type=int, default=None, help="длительность сек (65/90/120)")
    p.add_argument("--min-score", type=float, default=68.0, help="порог hit_score для эволюции")
    p.add_argument("--evolve", action="store_true", help="включает эволюцию (≤3 попытки на трек)")
    p.add_argument("--no-evolve", dest="evolve", action="store_false", help="выключает эволюцию")
    p.set_defaults(evolve=True)
    p.add_argument("--output", type=str, default="output/hits", help="куда складывать хиты")
    p.add_argument("--breakthrough", action="store_true", help="ПРОРЫВ: медленный CPU offload ротатор 1× — работает даже на 3.85GB RAM (интернет, не фризит)")
    p.add_argument("--artist", type=str, default="", help="артист-референс для прорыва (напр. ICEGERGERT)")
    p.add_argument("--refs", type=str, default="", help="референс-треки/ссылки через запятую (1-7 wav/mp3/http)")
    p.add_argument("--voice", type=str, default="", help="сырая запись голоса wav для RVC (10 мин)")
    args = p.parse_args()
    # прорыв если явно указан флаг/env/артист/refs/voice
    env_break = os.getenv("ZSMM_BREAKTHROUGH", "").strip() in ("1", "true", "yes")
    if args.breakthrough or env_break or args.artist or args.refs or args.voice:
        return _run_breakthrough(args)
    return _run_standard(args)


if __name__ == "__main__":
    raise SystemExit(_cli())
