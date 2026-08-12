# -*- coding: utf-8 -*-
"""
ZS Music Maker — smoke_v24
====================================================================

Проверяет главный фикс v24 (P0): рецепт GUI-визарда (preset, artist_name,
bpm_override, aggression, duration_sec, user_lyrics_lines) реально доезжает
до пайплайна run_full_pipeline, а не теряется молча.

Проверки:
  1. preset 'brazilian_phonk' применяется (analyze genre_default + mode).
  2. bpm_override=150 пробивает и пресет, и analysis → beat.bpm == 150.
  3. user_lyrics_lines → _stage_lyrics provider='user_lyrics' (без LLM/template).
  4. artist_name → попадает в metadata.json релиз-пакета.
  5. duration_sec из рецепта → доезжает до beat.
  6. Регрессия: пустой рецепт по-прежнему даёт дефолты (bpm=130, lyrics ok).

Запуск:  python3 tools/smoke_v24.py     (из корня проекта)
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESULTS = []


def check(name: str, ok: bool, detail: str = ""):
    RESULTS.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name:44s} {detail}")


def _run(project_id: str, recipe: dict) -> dict:
    from app.core.orchestrator import run_full_pipeline
    out_root = ROOT / "output" / "smoke_v24" / project_id
    if out_root.exists():
        shutil.rmtree(out_root, ignore_errors=True)
    return run_full_pipeline(project_id, recipe, dry_run=False, out_root=out_root)


def _stage(res: dict, name: str) -> dict:
    for s in res.get("stages", []):
        if s.get("name") == name:
            return s
    return {}


def main() -> int:
    print("=" * 64)
    print("ZS Music Maker v24 — smoke_v24 (wizard recipe -> pipeline mapping)")
    print("=" * 64)

    # ---- прогон 1: полный рецепт визарда -------------------------------
    recipe = {
        "references": [],
        "theme": "ночной город",
        "preset": "brazilian_phonk",
        "artist_name": "Smoke Artist v24",
        "bpm_override": 150,
        "aggression": 0.9,
        "duration_sec": 12,
        "user_lyrics_lines": ["ночь город дым фонари", "дрифт по спящим дворам"],
    }
    res = None
    try:
        res = _run("recipe_full", recipe)
    except Exception as e:
        for n in ("preset_applied", "bpm_override_wins", "user_lyrics_priority",
                  "artist_in_metadata", "duration_applied"):
            check("v24." + n, False, f"pipeline crashed: {e}")

    if res is not None:
        s_an = _stage(res, "_stage_analyze")
        an = (s_an.get("output") or {}).get("analysis") or {}
        check("v24.preset_applied", an.get("source") == "genre_default"
              and an.get("mode") == "minor",
              f"analysis source={an.get('source')} mode={an.get('mode')}")

        s_beat = _stage(res, "_stage_beat")
        beat_out = s_beat.get("output") or {}
        check("v24.bpm_override_wins",
              beat_out.get("bpm") == 150 and an.get("bpm") == 150,
              f"beat.bpm={beat_out.get('bpm')} analysis.bpm={an.get('bpm')}")

        s_lyr = _stage(res, "_stage_lyrics")
        lyr_out = s_lyr.get("output") or {}
        check("v24.user_lyrics_priority",
              lyr_out.get("provider") == "user_lyrics"
              and "ночь город дым фонари" in (lyr_out.get("text") or ""),
              f"provider={lyr_out.get('provider')}")

        meta_ok = False
        meta_detail = "metadata.json not found"
        rp = _stage(res, "_stage_release_pack").get("output") or {}
        rp_path = rp.get("path")
        if rp_path:
            mj = Path(rp_path) / "metadata.json"
            if mj.exists():
                meta = json.loads(mj.read_text(encoding="utf-8"))
                meta_ok = meta.get("artist") == "Smoke Artist v24"
                meta_detail = f"artist={meta.get('artist')!r}"
        check("v24.artist_in_metadata", meta_ok, meta_detail)

        check("v24.duration_applied",
              abs(float(beat_out.get("duration_sec") or 0) - 12.0) < 2.5,
              f"beat.duration_sec={beat_out.get('duration_sec')}")

    # ---- прогон 2: регрессия на пустом рецепте -------------------------
    try:
        res2 = _run("recipe_empty", {"references": []})
        an2 = ((_stage(res2, "_stage_analyze").get("output") or {})
               .get("analysis") or {})
        lyr2 = (_stage(res2, "_stage_lyrics").get("output") or {})
        check("v24.empty_recipe_regression",
              an2.get("bpm") == 130
              and res2.get("verdict") not in (None, "FAILED")
              and lyr2.get("ok") is True,
              f"bpm={an2.get('bpm')} verdict={res2.get('verdict')} "
              f"lyrics_provider={lyr2.get('provider')}")
    except Exception as e:
        check("v24.empty_recipe_regression", False, f"crashed: {e}")

    # ---- версия ----------------------------------------------------------
    try:
        v = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
        # v25: версия поднялась до 25.x — проверяем major >= 24, не точное равенство
        _maj = int(str(v.get("version", "0")).split(".")[0] or 0)
        check("v24.version_v24", _maj >= 24,
              f"version={v.get('version')}")
    except Exception as e:
        check("v24.version_v24", False, str(e))

    n_pass = sum(1 for _, ok, _ in RESULTS if ok)
    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    print("-" * 64)
    print(f"RESULT: {n_pass} PASS / {n_fail} FAIL / {len(RESULTS)} total")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
