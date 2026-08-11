"""
[v9] orchestrator_v9_patch.py — накладываемый патч на v8 Orchestrator.

НИЧЕГО не удаляет из v7/v8. Только оборачивает.

Порядок цепочки в run_pipeline_v9(orch, recipe, hook):
   0. reference_ingest.build_style_vector(refs, weights)          — style vector
   1. arrangement_engine.build_arrangement(sv, sec, seed, variant) — план
   2. sample_hunter_v9.unified_search(sv)                         — сэмплы+манифест
   3. v8 run_pipeline_v8(orch, recipe, hook)                      — core (v7 core)
   4. voice_vault_v9.maybe_trigger_retrain()                      — RVC дотрейн (async)
   5. anti_ai_polish.polish_track(master_wav, ...)                — устранение нейроношности
   6. mastering_v9.render_all_stands(polished, stands_dir)        — 3 стенда
   7. hit_scorer.score_track(streaming_master)                    — HIT score
   8. tiktok_edit_v9.make_all_cuts(streaming_master, ...)         — TikTok cuts
   9. release_pack_v9.build_release_v9(release_dir, ...)          — full pack

apply(orch) монки-патчит метод run_pipeline. При отсутствии зависимостей —
gracefully проваливается на v8 (v7 fallback).
"""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path


def _stage(hook, name: str, progress: float):
    try:
        if callable(hook):
            hook(name, progress)
    except Exception:
        pass


def run_pipeline_v9(orch, recipe: dict, stage_hook=None):
    log = getattr(orch, "log", lambda *a, **k: None)
    project_id = recipe.get("track_id") or f"track_{int(time.time())}"
    project_dir = Path(recipe.get("project_dir") or f"output/projects/{project_id}")
    project_dir.mkdir(parents=True, exist_ok=True)

    # 0. reference ingest
    _stage(stage_hook, "reference_ingest", 0.03)
    style_fp = None
    try:
        from modules.reference_ingest import build_style_vector

        refs = recipe.get("references") or []
        weights = recipe.get("reference_weights") or [1.0] * len(refs)
        if refs:
            style_fp = build_style_vector(refs, weights=weights)
            recipe["_style_fp"] = style_fp
            log(
                f"[v9] style_vector: bpm={style_fp['consensus']['bpm']}, "
                f"genre={style_fp['consensus']['genre_hint']}"
            )
    except Exception as e:
        log(f"[v9] reference_ingest failed: {e}")

    # 1. arrangement plan
    _stage(stage_hook, "arrangement", 0.08)
    plan = None
    try:
        from modules.arrangement_engine import build_arrangement

        sv = (style_fp or {}).get("style_vector") or {"bpm": recipe.get("bpm", 130.0)}
        plan = build_arrangement(
            sv,
            total_seconds=recipe.get("duration_sec", 150.0),
            seed=recipe.get("seed"),
            variant=recipe.get("variant", 0),
        )
        recipe["_arrangement_plan"] = plan
        log(
            f"[v9] arrangement: {len(plan['sections'])} sections, "
            f"{plan['total_sec']}s"
        )
    except Exception as e:
        log(f"[v9] arrangement failed: {e}")

    # 2. sample hunter
    _stage(stage_hook, "sample_hunter_v9", 0.12)
    sample_manifest = None
    try:
        from agents.sample_hunter_v9 import save_manifest, unified_search

        sv = (style_fp or {}).get("style_vector") or {}
        u = unified_search(sv, include_online=recipe.get("online_samples", False))
        sample_manifest_path = save_manifest(
            (u.get("local", []) + u.get("online", [])), project_id
        )
        sample_manifest = json.loads(
            Path(sample_manifest_path).read_text(encoding="utf-8")
        )
        log(f"[v9] samples: {u['total']} candidates ({len(u['local'])} local)")
    except Exception as e:
        log(f"[v9] sample_hunter_v9 failed: {e}")

    # 3. v8 core pipeline
    _stage(stage_hook, "v8_core", 0.20)
    result = {}
    try:
        from app.core.orchestrator_v8_patch import run_pipeline_v8

        result = run_pipeline_v8(orch, recipe, stage_hook=stage_hook) or {}
    except Exception as e:
        log(f"[v9] v8 core failed: {e}\n{traceback.format_exc()}")
        result = {"error": str(e)}

    master_wav = result.get("master_wav") or recipe.get("master_wav")

    # 4. voice_vault → возможно триггерим RVC дотрейн (не блокируем pipeline)
    _stage(stage_hook, "voice_vault_check", 0.75)
    try:
        from modules.voice_vault_v9 import maybe_trigger_retrain

        rv = maybe_trigger_retrain()
        result["voice_vault_retrain"] = rv
        if rv.get("triggered"):
            log("[v9] RVC retrain triggered (background)")
    except Exception as e:
        log(f"[v9] voice_vault_v9 check failed: {e}")

    # 5. anti-ai polish
    polished_wav = None
    if master_wav and Path(master_wav).exists():
        _stage(stage_hook, "anti_ai_polish", 0.80)
        try:
            from modules.anti_ai_polish import polish_track

            polished_wav = str(project_dir / "master_polished.wav")
            preset = recipe.get("polish_preset", "standard")
            polish_r = polish_track(
                master_wav,
                polished_wav,
                arrangement_plan=plan,
                preset=preset,
                seed=recipe.get("seed"),
            )
            if not polish_r.get("ok"):
                polished_wav = master_wav
            log(f"[v9] anti_ai_polish: {polish_r.get('stages_applied')}")
        except Exception as e:
            log(f"[v9] anti_ai_polish failed: {e}")
            polished_wav = master_wav
    else:
        polished_wav = master_wav

    # 6. mastering stands
    _stage(stage_hook, "mastering_v9", 0.87)
    stand_wavs = {}
    try:
        from modules.mastering_v9 import render_all_stands

        if polished_wav and Path(polished_wav).exists():
            stands_dir = project_dir / "stands"
            mres = render_all_stands(
                polished_wav, str(stands_dir), artist=recipe.get("artist_name", "")
            )
            for name in ("car", "club", "streaming"):
                r = mres.get("results", {}).get(name, {})
                if r.get("ok"):
                    stand_wavs[name] = r.get("output")
            log(f"[v9] mastering stands: {list(stand_wavs.keys())}")
    except Exception as e:
        log(f"[v9] mastering_v9 failed: {e}")

    # 7. hit_scorer на streaming-мастере (или polished если нет)
    hit_report = None
    _stage(stage_hook, "hit_scorer", 0.92)
    try:
        from modules.hit_scorer import score_track

        target_for_score = stand_wavs.get("streaming") or polished_wav or master_wav
        if target_for_score and Path(target_for_score).exists():
            hit_report = score_track(
                target_for_score, out_json=str(project_dir / "hit_score.json")
            )
            log(
                f"[v9] hit_score={hit_report.get('hit_score')} "
                f"verdict={hit_report.get('verdict')}"
            )
    except Exception as e:
        log(f"[v9] hit_scorer failed: {e}")

    # 8. tiktok cuts
    _stage(stage_hook, "tiktok_edit", 0.95)
    tiktok_wavs = {}
    try:
        from modules.tiktok_edit_v9 import make_all_cuts

        src = stand_wavs.get("streaming") or polished_wav or master_wav
        if src and Path(src).exists():
            tt_dir = project_dir / "tiktok"
            tres = make_all_cuts(
                src, str(tt_dir), hit_report=hit_report, arrangement_plan=plan
            )
            for name, r in tres.get("results", {}).items():
                if r.get("ok"):
                    tiktok_wavs[name] = r.get("output")
            log(f"[v9] tiktok cuts: {list(tiktok_wavs.keys())}")
    except Exception as e:
        log(f"[v9] tiktok_edit failed: {e}")

    # 9. release pack v9
    _stage(stage_hook, "release_pack_v9", 0.98)
    try:
        from modules.release_pack_v9 import build_release_v9

        release_dir = str(project_dir / "release")
        # voice manifest (best-effort)
        voice_manifest = None
        try:
            from modules.voice_vault_v9 import export_manifest_for_rvc

            vm_path = export_manifest_for_rvc(
                out_path=str(project_dir / "voice_manifest.json")
            )
            voice_manifest = json.loads(Path(vm_path).read_text(encoding="utf-8"))
        except Exception:
            pass

        meta = {
            "artist": recipe.get("artist_name", ""),
            "title": recipe.get("title") or recipe.get("theme", ""),
            "bpm": (plan or {}).get("bpm"),
            "key": (plan or {}).get("key"),
            "mode": (plan or {}).get("mode"),
            "genre": (plan or {}).get("genre"),
            "mood": (plan or {}).get("mood"),
            "duration_s": (plan or {}).get("total_sec"),
        }
        pack_r = build_release_v9(
            release_dir=release_dir,
            project_meta=meta,
            master_wav=polished_wav or master_wav or "",
            hit_report=hit_report,
            arrangement_plan=plan,
            style_fingerprint=style_fp,
            sample_manifest=sample_manifest,
            voice_manifest=voice_manifest,
            stand_wavs=stand_wavs,
            tiktok_wavs=tiktok_wavs,
        )
        result["release_v9"] = pack_r
        log(f"[v9] release: {pack_r.get('n_files_added')} files")
    except Exception as e:
        log(f"[v9] release_pack_v9 failed: {e}")

    _stage(stage_hook, "done_v9", 1.0)

    # Собираем итог
    result.update(
        {
            "v9_ok": True,
            "master_wav": master_wav,
            "polished_wav": polished_wav,
            "stand_wavs": stand_wavs,
            "tiktok_wavs": tiktok_wavs,
            "hit_report": hit_report,
            "arrangement_plan_file": (
                str(project_dir / "arrangement_plan.json") if plan else None
            ),
            "project_id": project_id,
            "project_dir": str(project_dir),
        }
    )
    return result


def apply(orch) -> None:
    """Монки-патч. Оборачивает orch.run_pipeline в v9-версию."""
    if not hasattr(orch, "_run_pipeline_v8"):
        original = getattr(orch, "run_pipeline", None)
        if original:
            orch._run_pipeline_v8 = original

    def _wrapper(recipe, stage_hook=None):
        return run_pipeline_v9(orch, recipe, stage_hook=stage_hook)

    orch.run_pipeline = _wrapper
    orch._v9_applied = True
