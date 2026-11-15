# -*- coding: utf-8 -*-
"""
app/cli/hitfactory.py — CLI обработчик для --hit-factory + прорыв
"""
from __future__ import annotations

from app.cli.env import safe_print


def _parse_refs(s: str) -> list[str]:
    if not s:
        return []
    return [p.strip() for p in s.split(",") if p.strip()]


def _run_breakthrough_cli(args, refs: list[str], artist: str | None, voice: str | None, theme: str | None, duration) -> int | None:
    try:
        from modules.hit_factory.breakthrough import full_orchestrate
        effective_theme = theme
        effective_artist = artist or "ICEGERGERT"
        dur = int(duration) if duration else 90
        count = int(getattr(args, "hit_count", 1) or 1)
        seed = getattr(args, "hit_seed", None)
        if count <= 1:
            res = full_orchestrate(artist=effective_artist, theme=effective_theme, reference_paths=refs or None,
                                   raw_voice_path=voice, duration_sec=dur, seed=seed, breakthrough=True)
            hit = res.get("hit") or {}
            safe_print(f"[hit-factory breakthrough] artist={effective_artist} theme={effective_theme} refs={len(refs)} voice={'yes' if voice else 'no'}")
            safe_print(f"[hit-factory] done: {hit.get('project_id')} score={hit.get('hit_score')} verdict={hit.get('verdict')} elapsed={res.get('elapsed_s')}s")
            return 0 if hit.get("master_path") else 1
        ok = 0
        for i in range(count):
            cur_seed = (int(seed) + i) if seed is not None else None
            res = full_orchestrate(artist=effective_artist, theme=effective_theme, reference_paths=refs or None,
                                   raw_voice_path=voice, duration_sec=dur, seed=cur_seed, breakthrough=True)
            hit = res.get("hit") or {}
            if hit.get("master_path"):
                ok += 1
            safe_print(f"[hit-factory breakthrough] {i+1}/{count} -> {hit.get('project_id')} score={hit.get('hit_score')}")
        safe_print(f"[hit-factory breakthrough] batch done: {ok}/{count} masters")
        return 0 if ok else 1
    except Exception as exc:  # noqa: BLE001
        safe_print(f"[hit-factory breakthrough] failed: {type(exc).__name__}: {exc} — fallback to standard")
        return None


def _run_standard_cli(args) -> int:
    from modules.hit_factory.generator import HitFactory
    count = int(getattr(args, "hit_count", 1) or 1)
    genre = getattr(args, "hit_genre", "") or None
    theme = getattr(args, "hit_theme", "") or None
    seed = getattr(args, "hit_seed", None)
    duration = getattr(args, "hit_duration", None)
    min_score = float(getattr(args, "hit_min_score", 68.0) or 68.0)
    evolve = not bool(getattr(args, "hit_no_evolve", False))
    breakthrough_flag = bool(getattr(args, "hit_breakthrough", False))
    if genre == "":
        genre = None
    if theme == "":
        theme = None
    factory = HitFactory(min_score=min_score, evolve=evolve, verbose=True)
    if breakthrough_flag:
        try:
            from modules.hit_factory.adaptive import get_adaptive_config
            factory.adaptive_cfg = get_adaptive_config(overrides={"breakthrough": True})
            safe_print(f"[hit-factory] forced breakthrough adaptive: {factory.adaptive_cfg.get('level_name')}")
        except Exception as _exc:
            print(f"[hit_factory] ignored: {_exc}")
    if count <= 1:
        hit = factory.make_one(genre=genre, theme=theme, seed=seed, duration_sec=duration)
        safe_print(f"[hit-factory] done: {hit.get('project_id')} score={hit.get('hit_score')} verdict={hit.get('verdict')}")
        return 0 if hit.get("master_path") else 1
    batch = factory.make_batch(count=count, genre=genre, theme=theme, seed=seed, duration_sec=duration)
    ok = sum(1 for r in batch if r.get("master_path"))
    safe_print(f"[hit-factory] batch done: {ok}/{len(batch)} masters")
    return 0 if ok else 1


def run_hit_factory(args) -> int:
    try:
        from modules.hit_factory.generator import HitFactory  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        safe_print(f"[hit-factory] import failed: {exc}")
        return 2
    breakthrough_flag = bool(getattr(args, "hit_breakthrough", False))
    artist = getattr(args, "hit_artist", "") or None
    refs_raw = getattr(args, "hit_refs", "") or ""
    voice = getattr(args, "hit_voice", "") or None
    theme = getattr(args, "hit_theme", "") or None
    refs = _parse_refs(refs_raw)
    use_breakthrough = breakthrough_flag or bool(artist) or bool(refs) or bool(voice)
    if use_breakthrough:
        dur = getattr(args, "hit_duration", None)
        rc = _run_breakthrough_cli(args, refs, artist, voice, theme, dur)
        if rc is not None:
            return rc
    try:
        return _run_standard_cli(args)
    except Exception as exc:  # noqa: BLE001
        safe_print(f"[hit-factory] failed: {type(exc).__name__}: {exc}")
        return 2
