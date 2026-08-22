from __future__ import annotations

from app.runtime_orchestrator import _summarize_pipeline_result


def test_pipeline_result_summary_preserves_desktop_job_contract() -> None:
    pipeline = {
        "warnings": ["  first warning  ", 12, "", "second warning"],
        "stages": [
            {
                "name": "_stage_mastering",
                "output": {"stands": {"streaming": {"out_wav": "mastered.wav"}}},
            },
            {"name": "_stage_polish", "output": {"out_wav": "polished.wav"}},
            {"name": "_stage_release_pack", "output": {"path": "release-dir"}},
            {
                "name": "_stage_hit_score",
                "output": {
                    "verdict": "PROMISING",
                    "hit_score": 87,
                    "actions": ["  tighten hook  ", 5, "", "check intro"],
                },
            },
        ],
    }

    summary = _summarize_pipeline_result(pipeline)

    assert summary["pipeline"] is pipeline
    assert summary["master"] == "polished.wav"
    assert summary["master_path"] == "polished.wav"
    assert summary["release"] == {"release_dir": "release-dir"}
    assert summary["ai_detector"] == {
        "ok": True,
        "verdict": "PROMISING",
        "score": 87,
        "flags": ["first warning", "second warning"],
        "advice": ["tighten hook", "check intro"],
    }
