# -*- coding: utf-8 -*-
"""Бюджет длины функций: правило ≤ 60 строк стало мягким, но управляемым.

`docs/WORKFLOW.md` требует функции ≤ 60 строк, а в коде их 80 длиннее. Жёсткий
гейт означал бы переписать все 80 ради теста; поэтому база фиксируется явно:
новые длинные функции запрещены, существующие не имеют права расти. Когда
функцию разгружают, её строка удаляется из `LONG_FUNCTIONS` — база только
сжимается.

Крупные кандидаты, уже разобранные по плану (T20):
`orchestrator.run_full_pipeline`, `stages/beat._synth_beat`,
`beat/constructor.build_track` — блоки вынесены в отдельные модули.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_LINES = 60
# Допуск на один-два комментария при разборе: функция не «растёт», а уточняется.
SLACK = 3

# (файл, функция): зафиксированная длина на момент введения правила.
LONG_FUNCTIONS: dict[tuple[str, str], int] = {
    ("agents/sample_hunter/hunter.py", "hunt"): 62,
    ("app/ai/acestep.py", "generate_instrumental"): 79,
    ("app/ai/registry.py", "_register_default_loaders"): 143,
    ("app/ai/sequential_runner.py", "run"): 84,
    ("app/core/ai/render.py", "extend_beat_with_stereo_sections"): 61,
    ("app/core/musicgen_texture.py", "generate_texture"): 65,
    ("app/core/orchestrator.py", "_build_report"): 65,
    ("app/core/orchestrator.py", "run_full_pipeline"): 140,
    ("app/core/orchestrator_ai.py", "run_ai_pipeline"): 86,
    ("app/core/project_inputs.py", "apply_replacement_inputs"): 74,
    ("app/core/recipe.py", "build_recipe"): 83,
    ("app/core/stages/beat.py", "_stage_beat"): 61,
    ("app/core/stages/lyrics.py", "_run_lyrics_stage"): 72,
    ("app/core/stages/lyrics.py", "_stage_lyrics"): 103,
    ("app/core/stages/master.py", "_stage_stems"): 63,
    ("app/core/stages/mix.py", "_stage_mix_and_sidechain"): 138,
    ("app/core/stages/vocal.py", "_pyttsx3_speak"): 153,
    ("app/core/stages/vocal.py", "_stage_voice_synth"): 62,
    ("app/core/stages/vocal_chain.py", "_run_vocal_chain"): 100,
    ("app/gui/theme.py", "qss"): 189,
    ("app/gui/wizard/project_edit_dialog.py", "__init__"): 70,
    ("app/gui/wizard/record_dialog.py", "__init__"): 62,
    ("app/gui/wizard/steps_brief.py", "__init__"): 76,
    ("app/gui/wizard/steps_material.py", "__init__"): 72,
    ("app/gui/wizard/steps_run.py", "show_result"): 71,
    ("app/gui/wizard/steps_tuning.py", "__init__"): 63,
    ("app/gui/wizard/steps_voice.py", "__init__"): 91,
    ("app/pipeline/stage.py", "summarize"): 73,
    ("app/runtime_orchestrator.py", "_process"): 61,
    ("main.py", "main"): 85,
    ("modules/ai_detector_pro.py", "analyze_track"): 140,
    ("modules/analyzer.py", "analyze_multi"): 65,
    ("modules/analyzer.py", "analyze_single"): 77,
    ("modules/anti_neuro_track.py", "polish_track"): 68,
    ("modules/arrangement_engine.py", "build_arrangement"): 90,
    ("modules/artist_dossier/manager.py", "_analyze_single_track"): 156,
    ("modules/auto_qa.py", "audit_track"): 101,
    ("modules/beat/arrangement.py", "_build_section"): 170,
    ("modules/beat/constructor.py", "build_track"): 85,
    ("modules/beat/dramaturgy.py", "plan_sections"): 79,
    ("modules/beat_gen_ai.py", "_render_with_handle"): 65,
    ("modules/chanson_engine.py", "synthesize_chanson_track"): 87,
    ("modules/cover_art_gen.py", "generate"): 80,
    ("modules/groove_extractor.py", "extract_groove"): 73,
    ("modules/hit_scorer/scoring.py", "score_track"): 85,
    ("modules/kpi_monitor.py", "finalize_session"): 71,
    ("modules/llm/router.py", "complete"): 126,
    ("modules/lyrics/generate.py", "generate_lyrics"): 79,
    ("modules/mastering/chain.py", "_control_crest"): 70,
    ("modules/mastering/chain.py", "master_one"): 127,
    ("modules/mastering/loudness.py", "_converge_loudness"): 113,
    ("modules/mix/bus.py", "build_mix"): 129,
    ("modules/mix/ducking.py", "duck_low_band"): 65,
    ("modules/mix/reference.py", "match_to_reference"): 149,
    ("modules/mix/width.py", "match_width"): 68,
    ("modules/reference_ingest.py", "analyze_file"): 65,
    ("modules/reference_ingest.py", "build_style_vector"): 77,
    ("modules/release/export.py", "export_release"): 113,
    ("modules/release/export.py", "tag_release_master"): 69,
    ("modules/release/pack.py", "build_pack"): 113,
    ("modules/rvc_manager/infer.py", "infer"): 75,
    ("modules/sidechain.py", "_numpy_dsp"): 94,
    ("modules/tiktok_edit.py", "make_all_cuts"): 61,
    ("modules/tiktok_edit.py", "make_vertical_video"): 62,
    ("modules/video_edit/render.py", "_build_fallback"): 62,
    ("modules/video_edit/render.py", "_build_with_moviepy"): 76,
    ("modules/vocal_fx/desser.py", "dynamic_deess"): 67,
    ("modules/vocal_fx/pipeline.py", "process_vocal"): 131,
    ("modules/vocal_fx/pitch.py", "_pitch_shift"): 74,
    ("modules/vocal_fx/pitch.py", "correct_pitch"): 67,
    ("modules/vocal_fx/throw.py", "apply_delay_throw"): 76,
    ("modules/voice_cleaner.py", "_spectral_denoise"): 68,
    ("modules/voice_recording/takes.py", "split_wav_into_takes"): 63,
    ("modules/voice_vault.py", "add_recording"): 65,
    ("tests/test_project_edit_gui_contract.py", "fake_qt"): 89,
    ("tools/e2e.py", "main"): 100,
    ("tools/generate_demos.py", "main"): 61,
    ("tools/smoke_audio.py", "main"): 123,
    ("ui/karaoke_recorder.py", "record_with_backing"): 124,
    ("updater/install.py", "install_from_zip"): 113,
}


# Каталоги, где лежит не исходный код, а данные, сборки и кэши.
SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "output", "build", "dist",
    "node_modules", "models", "data", "assets", "logs", ".pytest_cache",
}


def _tracked() -> list[str]:
    """Все .py в репозитории, включая ещё не закоммиченные.

    Раньше список брался из `git ls-files`: новый файл до первого коммита
    выпадал из гейта — то есть ровно тогда, когда правило важнее всего.
    """
    files: list[str] = []
    for path in ROOT.rglob("*.py"):
        parts = set(path.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        files.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return sorted(files)


def _long_functions() -> dict[tuple[str, str], int]:
    found: dict[tuple[str, str], int] = {}
    for path in _tracked():
        file_path = ROOT / path
        if not file_path.is_file():
            continue
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:  # pragma: no cover - защищено другими тестами
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            length = (node.end_lineno or 0) - node.lineno
            if length > MAX_LINES:
                found[(path, node.name)] = length
    return found


def test_no_new_long_functions_appear() -> None:
    current = _long_functions()

    new_ones = sorted(key for key in current if key not in LONG_FUNCTIONS)
    assert not new_ones, (
        "новые функции длиннее {} строк: {}".format(
            MAX_LINES, ", ".join(f"{path}::{name}" for path, name in new_ones)
        )
    )


def test_known_long_functions_do_not_grow() -> None:
    current = _long_functions()

    grown = {
        key: (LONG_FUNCTIONS[key], current[key])
        for key in current
        if key in LONG_FUNCTIONS and current[key] > LONG_FUNCTIONS[key] + SLACK
    }
    assert not grown, f"функции выросли: {grown}"


def test_refactored_functions_left_the_budget_list() -> None:
    """Если функцию разгрузили, запись в базе должна исчезнуть, а не протухнуть."""
    current = _long_functions()

    stale = [key for key in LONG_FUNCTIONS if key not in current]
    assert not stale, (
        "эти функции уже уложились в бюджет — удали их из LONG_FUNCTIONS: "
        + ", ".join(f"{path}::{name}" for path, name in stale)
    )
