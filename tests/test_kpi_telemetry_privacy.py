from __future__ import annotations

import json
from pathlib import Path

from modules.hit_kpi_monitor_v11 import KpiSession, finalize_session
from modules.kpi_dashboard_v12 import _latest_telemetry, _telemetry_section


def test_kpi_history_persists_only_allowlisted_non_pii_stage_metrics(tmp_path: Path) -> None:
    secret_project = "/home/alice/Private Artist/lyrics secret"
    secret_note = "full song lyrics: never store these words"
    session = KpiSession(project_id=secret_project, hw_mode="fallback_hw")
    safe = session.start_stage("mix")
    session.end_stage(safe, ok=True, note=secret_note, vram_gb=7.5, score=82.0)
    unsafe = session.start_stage("/home/alice/output/lyrics.txt")
    session.end_stage(unsafe, ok=False, note=secret_note, vram_gb=8.0, score=11.0)

    finalized = finalize_session(session, save_dir=str(tmp_path))
    history = tmp_path / "kpi_history.jsonl"
    raw = history.read_text(encoding="utf-8")
    payload = json.loads(raw)

    assert finalized.verdict == "PASS"
    assert secret_project not in raw
    assert secret_note not in raw
    assert "/home/alice" not in raw
    assert payload == {
        "schema": "zsmm.kpi-telemetry.v1",
        "pipeline_duration_sec": payload["pipeline_duration_sec"],
        "ai_detector_percent": None,
        "verdict": "PASS",
        "stages": [
            {"stage": "mix", "duration_sec": payload["stages"][0]["duration_sec"], "vram_gb": 7.5, "score": 82.0, "status": "ok"},
            {"stage": "redacted", "duration_sec": payload["stages"][1]["duration_sec"], "vram_gb": 8.0, "score": 11.0, "status": "failed"},
        ],
    }


def test_dashboard_reads_sanitized_telemetry_only(tmp_path: Path) -> None:
    telemetry_path = tmp_path / "kpi_history.jsonl"
    telemetry_path.write_text(
        '{"project_id":"should_be_ignored"}\n'
        '{"schema":"zsmm.kpi-telemetry.v1","pipeline_duration_sec":12.5,"ai_detector_percent":22.0,"verdict":"PASS","stages":[{"stage":"master","duration_sec":3.2,"vram_gb":6.0,"score":91.0,"status":"ok"}]}\n',
        encoding="utf-8",
    )

    telemetry = _latest_telemetry(telemetry_path)
    section = _telemetry_section(telemetry)
    rendered = "\n".join(section.lines)

    assert telemetry["schema"] == "zsmm.kpi-telemetry.v1"
    assert section.ok is True
    assert "master" in rendered and "VRAM 6.00GB" in rendered and "score 91.00" in rendered
    assert "should_be_ignored" not in rendered
