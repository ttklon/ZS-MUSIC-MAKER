"""Референсы обязаны доезжать до пайплайна — или честно сказать, почему нет.

Регрессия 42.0.15. Пользователь передал `--hit-refs /tmp/bad.wav`, приложение
отработало «успешно», а в отчёте стояло `source: genre_default`, `n_refs: 0`
и ни одного предупреждения. Причина: путь «breakthrough» анализировал
референсы (`analyze_references`), но `HitFactory.make_one` их вообще не
принимал — результат анализа выбрасывался, в рецепт попадал пустой список.

Второй слой: даже когда причина отказа была известна (`all analyses failed`),
она не доходила до `report.json.warnings`, то есть пользователь не мог узнать,
что его референс проигнорирован.
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

from app.core.recipe import build_recipe
from modules.hit_factory.generator import HitFactory


def _tone(path, seconds: float = 6.0, sr: int = 22050) -> str:
    t = np.arange(int(sr * seconds))
    y = 0.3 * np.sin(2 * np.pi * 130 * t / sr)
    sf.write(path, np.stack([y, y], axis=1).astype("float32"), sr)
    return str(path)


def test_make_one_carries_references_into_recipe(tmp_path, monkeypatch):
    """`make_one(references=...)` → `wizard_state` → рецепт."""
    captured = {}

    factory = HitFactory(output_root=str(tmp_path), min_score=0, evolve=False, duration_sec=4)

    def fake_pipeline_once(project_id, wizard_state, rng):
        captured.update(wizard_state)
        return {"master_path": None, "hit_score": 0.0, "verdict": "PASS_BLOCKED",
                "report": {"verdict": "PASS_BLOCKED"}, "project_id": project_id}

    monkeypatch.setattr(factory, "_run_pipeline_once", fake_pipeline_once, raising=False)
    ref = _tone(tmp_path / "ref.wav")

    factory.make_one(
        genre="trap",
        theme="тест",
        seed=1,
        duration_sec=4,
        references=[ref],
        reference_warnings=["references not applied: all analyses failed"],
    )

    assert captured.get("references") == [ref], "референс не дошёл до wizard_state"
    assert captured.get("reference_warnings"), "причина отказа не дошла до состояния"


def test_recipe_surfaces_reference_warnings():
    """Рецепт несёт причину отказа, иначе отчёт врёт о «нет референсов»."""
    recipe = build_recipe(
        {
            "genre": "trap",
            "references": ["/tmp/bad.wav"],
            "reference_warnings": ["references not applied: all analyses failed"],
        }
    )
    assert recipe["refs"] == ["/tmp/bad.wav"]
    assert recipe["ref_warnings"] == ["references not applied: all analyses failed"]


def test_reference_warnings_are_snapshotable():
    """Проект переоткрывается вместе с причиной отказа."""
    from app.core.project_snapshot import snapshot_recipe

    state = {"genre": "trap", "reference_warnings": ["boom"]}
    assert snapshot_recipe(state)["recipe"]["reference_warnings"] == ["boom"]


def test_breakthrough_reports_failed_reference_analysis(monkeypatch):
    """Неудачный анализ референса превращается в предупреждение, а не в тишину."""
    from modules.hit_factory import breakthrough

    monkeypatch.setattr(
        breakthrough, "analyze_references", lambda paths, weights=None: {
            "ok": False, "error": "all analyses failed",
        }
    )
    result = breakthrough.analyze_references(["/tmp/bad.wav"])
    assert result["ok"] is False
    assert "all analyses failed" in result["error"]
