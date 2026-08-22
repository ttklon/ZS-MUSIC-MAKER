from __future__ import annotations

import logging

from app.runtime_orchestrator import RuntimeOrchestrator, _summarize_pipeline_result


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


class _BrokenDiagnosticSink:
    def info(self, _message: str) -> None:
        raise RuntimeError("sink offline")


def test_runtime_log_reports_broken_optional_sink(caplog) -> None:
    runtime = RuntimeOrchestrator(log=_BrokenDiagnosticSink())
    try:
        with caplog.at_level(logging.WARNING, logger="app.runtime_orchestrator"):
            runtime._log("pipeline diagnostic")
        assert "runtime diagnostic sink failed: sink offline" in caplog.text
    finally:
        runtime.stop(join_timeout=0.5)
