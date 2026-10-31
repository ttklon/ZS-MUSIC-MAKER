from __future__ import annotations

import ast
from pathlib import Path


def test_gradio_expert_launch_schedules_browser_without_ui_sleep() -> None:
    source_path = Path(__file__).resolve().parents[1] / "app/gui/wizard" / "window.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    method = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "launch_gradio_expert"
    )
    calls = [node for node in ast.walk(method) if isinstance(node, ast.Call)]

    assert any(
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "threading"
        and call.func.attr == "Timer"
        for call in calls
    )
    assert not any(
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "time"
        and call.func.attr == "sleep"
        for call in calls
    )
