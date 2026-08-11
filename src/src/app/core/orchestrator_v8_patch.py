# -*- coding: utf-8 -*-
"""
[v8] orchestrator_v8_patch.py — накладываемый патч на v7 Orchestrator.

Не переписываем orchestrator.py v7 (сохраняем как есть). Вместо этого:
  • Обёртка `run_pipeline_v8(orch, recipe, stage_hook)` вызывает v7 pipeline,
    а сверху добавляет:
      1. lyrics_gen_v8 (автор-референс + trend_scout_v3 + слэнг сегодня);
      2. female_backing (женский бэк на припеве, если включён);
      3. auto_qa (аудит финального master.wav);
      4. авто-рестарт нужных узлов при verdict="rebuild"/"patch".

Экспорт для orchestrator.py: apply(orch) — монки-патчит метод run_pipeline
на v8-версию.
"""
from __future__ import annotations
import time, traceback
from pathlib import Path


def _stage(hook, name: str, progress: float):
    try:
        if callable(hook):
            hook(name, progress)
    except Exception:
        pass


def run_pipeline_v8(orch, recipe: dict, stage_hook=None):
    """
    Полный v8 pipeline. `orch` — экземпляр v7 Orchestrator.
    Возвращает dict с результатами (пути к файлам).
    """
    from pathlib import Path
    log = getattr(orch, "log", lambda *a, **k: None)

    # ---------- 0) v8 lyrics с автором-референсом ------------------
    _stage(stage_hook, "lyrics_v8", 0.10)
    try:
        from modules.lyrics_gen_v8 import generate_lyrics_v8
        lyrics_res = generate_lyrics_v8(
            theme=recipe.get("theme", "лето тачки"),
            user_words=recipe.get("user_lyrics_lines", []),
            bpm=int(recipe.get("bpm", 130)),
            author=recipe.get("author_ref", None),
            target_lines=recipe.get("target_lines", 16),
            want_female_backing=recipe.get("female_backing", False),
            lang_mix=recipe.get("lang_mix", "ru+en"),
        )
        recipe["lyrics_text"]   = lyrics_res["text"]
        recipe["chorus_lines"]  = lyrics_res["chorus_lines"]
        recipe["used_slang"]    = lyrics_res["used_slang"]
        log(f"[v8] lyrics: author_style={lyrics_res['author_style_used']}, "
            f"slang={len(lyrics_res['used_slang'])}")
    except Exception as e:
        log(f"[v8] lyrics_v8 FAILED, use v7 default: {e}")

    # ---------- 1) v7 core pipeline (analyze → beat → voice → mix) ---
    _stage(stage_hook, "v7_core", 0.20)
    result = {}
    if hasattr(orch, "_run_pipeline_v7"):
        result = orch._run_pipeline_v7(recipe, stage_hook=stage_hook) or {}
    else:
        # v7 exposes run_pipeline directly
        try:
            result = orch.run_pipeline(recipe, stage_hook=stage_hook) or {}
        except Exception as e:
            log(f"[v8] v7 pipeline failed: {e}\n{traceback.format_exc()}")
            result = {"error": str(e)}

    # ---------- 2) female backing (после сборки основного вокала) ----
    if recipe.get("female_backing") and result.get("vocal_wav"):
        _stage(stage_hook, "female_backing", 0.78)
        try:
            from modules.female_backing import make_chorus_backing, mix_backing_into_vocal
            chorus_lines = recipe.get("chorus_lines", []) or \
                           ["night ride, we don't stop"]
            backing = make_chorus_backing(chorus_lines)
            new_vocal = mix_backing_into_vocal(result["vocal_wav"],
                                               backing,
                                               backing_gain_db=-9.0)
            result["vocal_wav"]  = str(new_vocal)
            result["backing_wav"] = str(backing)
            log(f"[v8] female_backing mixed: {backing}")
        except Exception as e:
            log(f"[v8] female_backing failed: {e}")

    # ---------- 3) Auto QA ------------------------------------------
    master_path = result.get("master_wav") or result.get("master") or ""
    if master_path and Path(master_path).exists():
        _stage(stage_hook, "auto_qa", 0.92)
        try:
            from modules.auto_qa import audit_track, should_retry
            report = audit_track(master_path)
            result["auto_qa"] = report
            log(f"[v8] auto_qa verdict: {report.get('verdict_text')}")

            # автоматическая пересборка узлов при verdict != release
            if recipe.get("auto_qa_loop", False):
                retry, targets = should_retry(
                    report, max_iterations=recipe.get("max_qa_iters", 2),
                    current_iter=recipe.get("_qa_iter", 0))
                if retry:
                    recipe["_qa_iter"] = recipe.get("_qa_iter", 0) + 1
                    recipe["rebuild_targets"] = targets
                    log(f"[v8] auto_qa retry #{recipe['_qa_iter']} → {targets}")
                    # рекурсивно повторяем только нужные узлы
                    return run_pipeline_v8(orch, recipe, stage_hook)
        except Exception as e:
            log(f"[v8] auto_qa failed: {e}")

    _stage(stage_hook, "done_v8", 1.0)
    return result


def apply(orch):
    """Монки-патчим экземпляр orchestrator: run_pipeline → v8-версия."""
    if hasattr(orch, "_v8_applied"):
        return
    if hasattr(orch, "run_pipeline"):
        orch._run_pipeline_v7 = orch.run_pipeline
        orch.run_pipeline = lambda recipe, stage_hook=None: \
            run_pipeline_v8(orch, recipe, stage_hook)
    orch._v8_applied = True
