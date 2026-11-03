import json
import os
from modules.kpi_dashboard.sources import _latest_pipeline, _pipeline_section


def test_current_report_is_used_and_failed_gates_are_visible(tmp_path):
    old = tmp_path / "old" / "report.json"
    old.parent.mkdir()
    old.write_text(json.dumps({"project_id": "song", "verdict": "PARTIAL", "percent": 70,
                               "stages": [{"name": "_stage_mix_and_sidechain", "status": "FALLBACK"}],
                               "quality_gate_failures": ["mix: correlation"]}), encoding="utf-8")
    newer = tmp_path / "new" / "report.json"
    newer.parent.mkdir()
    newer.write_text('{"unrelated": true}', encoding="utf-8")
    os.utime(old, (1, 1))
    report = _latest_pipeline(tmp_path)
    assert report["project_id"] == "song"
    section = _pipeline_section(report)
    assert not section.ok and section.percent == 70
    assert any("FALLBACK" in line for line in section.lines)
    assert any("mix: correlation" in line for line in section.lines)


def test_dry_run_and_partial_runs_do_not_claim_full_success():
    for extra in ({"dry_run": True}, {"only": ["beat"]}, {"verdict": "PASS_BLOCKED"}, {"quality_gate_failures": ["mix: failed"]}):
        assert not _pipeline_section({"verdict": "PASS", "stages": [], **extra}).ok


def test_dashboard_explains_checklist_is_not_ai_readiness():
    from modules.kpi_dashboard.models import Dashboard
    from modules.kpi_dashboard.report import render_markdown, render_text
    for rendered in (render_markdown(Dashboard()), render_text(Dashboard())):
        assert "Не подтверждает" in rendered or "не подтверждает" in rendered
        assert "модел" in rendered
