from __future__ import annotations

from io import StringIO
from pathlib import Path

from app.ai.sequential_runner import AIStage, SequentialAIRunner
from app.core.logger import TerminalStageProgress
from app.core.orchestrator_ai import run_ai_pipeline


def test_terminal_progress_uses_real_stage_reports_and_vram_values() -> None:
    stream = StringIO()
    progress = TerminalStageProgress(total_stages=2, stream=stream)
    runner = SequentialAIRunner(vram_budget_gb=4.0, vram_probe=lambda: 1.25)
    runner.add(AIStage("prepare", None, lambda _handle, _ctx: {"ok": True}))

    def failing_stage(_handle, _ctx):
        raise RuntimeError("expected stage failure")

    runner.add(AIStage("render", None, failing_stage))
    report = runner.run(progress=progress)
    lines = stream.getvalue().splitlines()

    assert len(report.stages) == 2
    assert lines[0] == "[AI] [------------] 1/2 START prepare | VRAM 1.250 GB"
    assert "1/2 OK prepare" in lines[1] and "VRAM 1.250->1.250 GB" in lines[1]
    assert "2/2 START render" in lines[2]
    assert "2/2 FAILED render" in lines[3]


def test_dry_ai_pipeline_renders_all_configured_stage_progress(tmp_path: Path, capsys) -> None:
    result = run_ai_pipeline(
        "terminal_progress", out_root=tmp_path, dry_run=True, terminal_progress=True
    )
    terminal_lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith("[AI]")]

    assert len(result["report"]["stages"]) == 12
    assert len(terminal_lines) == 24
    assert terminal_lines[0].startswith("[AI] [------------] 1/12 START hw_check")
    assert "12/12" in terminal_lines[-1]
    assert all("VRAM" in line for line in terminal_lines)
