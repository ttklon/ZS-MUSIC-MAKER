"""Отказ стадии обязан объясняться, даже если у исключения пустое сообщение.

Найдено в 42.0.17. `audioread.exceptions.NoBackendError` не несёт текста:
`str(e) == ""`. `_stage_analyze` и `_stage_groove` складывали причину как
`str(e)`, поэтому в `report.json` появлялось `reason: ""` — стадия падала
«молча». Пользователь видел, что референс не применился, но не мог понять,
что дело в формате файла и что именно за чтение упало.
"""

from __future__ import annotations

import pytest

from app.core.stages.prep import _stage_analyze, _stage_groove
from modules.errors import failure_reason


def _no_backend_error() -> Exception:
    """Настоящий класс из audioread: воспроизводим ровно его пустое сообщение."""
    audioread = pytest.importorskip("audioread")
    return audioread.exceptions.NoBackendError()


def test_failure_reason_never_empty():
    """Пустое сообщение — самый опасный случай: имя типа обязано остаться."""
    reason = failure_reason(_no_backend_error())
    assert reason
    assert "NoBackendError" in reason


def test_failure_reason_keeps_message_when_present():
    reason = failure_reason(ValueError("not found: /tmp/x.wav"))
    assert reason.startswith("ValueError")
    assert "not found: /tmp/x.wav" in reason


def test_analyze_stage_explains_unreadable_reference():
    """Битый референс → читаемая причина + честное число запрошенных файлов."""
    result = _stage_analyze(["/tmp/definitely-not-audio.wav"], dry_run=False, genre="trap")
    assert result["ok"] is False
    assert result["fallback_used"] is True
    assert result["reason"], "причина отказа не может быть пустой строкой"
    assert "references not applied (requested 1)" in result["reason"]


def test_analyze_stage_counts_every_requested_reference():
    result = _stage_analyze(["/tmp/a.wav", "/tmp/b.wav"], dry_run=False, genre="trap")
    assert result["ok"] is False
    assert "(requested 2)" in result["reason"]


def test_groove_stage_explains_unreadable_reference():
    result = _stage_groove(["/tmp/definitely-not-audio.wav"], genre="trap")
    assert result["ok"] is False
    assert result["reason"]


def test_analyze_stage_without_refs_is_not_an_error():
    """Нет референсов — это generate-from-scratch, а не сбой."""
    result = _stage_analyze([], dry_run=False, genre="trap")
    assert result["ok"] is True
    assert result["analysis"]["source"] == "genre_default"
    assert result["analysis"]["n_refs"] == 0


def test_no_module_reports_exception_text_as_reason():
    """Статический гейт: внутри `except` причина не собирается через `str(e)`.

    `str(e)` законен для обычных исключений, но не для беcтекстовых
    (`NoBackendError`): в поле причины он даёт пустую строку. Проверяем именно
    поля причины/ошибки внутри обработчиков исключений — там нужен
    `failure_reason`.
    """
    import ast
    import pathlib

    skip = {"tests", ".venv", "node_modules", "build", "dist", ".venv-rvc", ".git"}
    offenders: list[str] = []
    for path in pathlib.Path(".").rglob("*.py"):
        if skip & set(path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for handler in [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)]:
            for node in ast.walk(handler):
                if not isinstance(node, ast.Dict):
                    continue
                for key, value in zip(node.keys, node.values):
                    if not isinstance(key, ast.Constant) or key.value not in {"reason", "error"}:
                        continue
                    if (
                        isinstance(value, ast.Call)
                        and isinstance(value.func, ast.Name)
                        and value.func.id == "str"
                    ):
                        offenders.append(f"{path}:{node.lineno}")
    assert not offenders, f"причина отказа собирается через str(e): {offenders}"
