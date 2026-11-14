# -*- coding: utf-8 -*-
"""`app/cli/commands.py`: коды возврата и честные сообщения команд CLI.

Файл был покрыт на 24 %: проверялся разбор флагов, но не сами обработчики.
Здесь держится контракт из docstring модуля — 0 успех, 1 провал проверки,
2 ошибка окружения — и правило «отказ называется, а не молчит».

Тяжёлые подсистемы подменяются: реальные smoke/e2e-прогоны занимают минуты и
проверяются отдельно (`tools/smoke_audio.py`, `tools/smoke_god.py`,
`main.py --e2e`). Ничего о качестве звука эти тесты не утверждают.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

from app.cli import commands


@pytest.fixture
def said(monkeypatch) -> list[str]:
    """Перехват вывода команд: печать — часть контракта, её и проверяем."""
    lines: list[str] = []
    monkeypatch.setattr(commands, "safe_print", lines.append)
    return lines


def _stub(monkeypatch, name: str, **attrs):
    module = types.SimpleNamespace(**attrs)
    monkeypatch.setitem(sys.modules, name, module)
    parent, _, leaf = name.rpartition(".")
    if parent:
        pkg = sys.modules.get(parent)
        if pkg is not None:
            monkeypatch.setattr(pkg, leaf, module, raising=False)
    return module


# --------------------------------------------------------------------------- #
#  version / list-genres
# --------------------------------------------------------------------------- #

def test_version_reports_build_and_config(said, monkeypatch) -> None:
    config = types.SimpleNamespace(config_path=Path("/tmp/zsmm/settings.json"))
    _stub(monkeypatch, "config.settings",
          get_settings=lambda: types.SimpleNamespace(config_path="/tmp/zsmm/settings.json"))
    monkeypatch.setitem(sys.modules, "config", types.SimpleNamespace(settings=sys.modules["config.settings"]))

    code = commands.run_version()

    payload = json.loads(said[0])
    assert code == 0
    assert payload["config"] == "/tmp/zsmm/settings.json"
    assert payload["version"] == commands.VERSION
    assert "__" not in payload["config"] or payload["config"] == "unavailable"


def test_version_survives_broken_config(said, monkeypatch) -> None:
    class Boom:
        def get_settings(self):
            raise RuntimeError("нет config/settings.py")

    _stub(monkeypatch, "config.settings", get_settings=Boom().get_settings)
    monkeypatch.setitem(sys.modules, "config", types.SimpleNamespace(settings=sys.modules["config.settings"]))

    assert commands.run_version() == 0
    assert json.loads(said[0])["config"] == "unavailable"


def test_list_genres_prints_sorted_names(said, monkeypatch) -> None:
    class Registry:
        def list_genres(self):
            return ["zeta", "alpha"]

    _stub(monkeypatch, "modules.genre_engine", StyleRegistry=Registry)

    assert commands.run_list_genres() == 0
    assert said[1:] == ["  - alpha", "  - zeta"]


def test_list_genres_failure_is_code_2_with_reason(said, monkeypatch) -> None:
    _stub(monkeypatch, "modules.genre_engine", StyleRegistry=None)

    assert commands.run_list_genres() == 2
    assert "failed" in said[0]


# --------------------------------------------------------------------------- #
#  Проверки: smoke / dry-run / health / score / update
# --------------------------------------------------------------------------- #

def test_smoke_returns_worst_code(said, monkeypatch) -> None:
    _stub(monkeypatch, "tools.smoke_god", main=lambda: 0)
    _stub(monkeypatch, "tools.smoke_audio", main=lambda: 1)

    assert commands.run_smoke() == 1


def test_smoke_exception_becomes_environment_error(said, monkeypatch) -> None:
    _stub(monkeypatch, "tools.smoke_god", main=lambda: None)
    _stub(monkeypatch, "tools.smoke_audio", main=lambda: (_ for _ in ()).throw(RuntimeError("нет numpy")))

    assert commands.run_smoke() == 2
    assert "smoke_audio failed" in said[0]


def test_dry_run_pass_and_partial(said, monkeypatch) -> None:
    verdicts = {"value": "PASS"}
    _stub(monkeypatch, "app.core.orchestrator", run_full_pipeline=lambda *a, **k: {
        "verdict": verdicts["value"], "duration_sec": 0.5})

    assert commands.run_dry_run() == 0

    verdicts["value"] = "PARTIAL"
    assert commands.run_dry_run() == 1, "PARTIAL — не успех проверки"
    assert "verdict=PARTIAL" in said[-1]


def test_dry_run_crash_is_code_2(said, monkeypatch) -> None:
    _stub(monkeypatch, "app.core.orchestrator", run_full_pipeline=None)

    assert commands.run_dry_run() == 2


def test_health_codes(monkeypatch) -> None:
    for verdict, expected in (("GREEN", 0), ("YELLOW", 0), ("RED", 1), ("UNKNOWN", 1)):
        monkeypatch.setattr(commands, "health_snapshot", lambda v=verdict: {"verdict": v, "percent": 10})
        assert commands.run_health() == expected


def test_score_success_and_error(said, monkeypatch) -> None:
    _stub(monkeypatch, "modules.hit_scorer", score_track=lambda path: {"hit_score": 71.0})

    assert commands.run_score("master.wav") == 0
    assert json.loads(said[0])["hit_score"] == 71.0

    _stub(monkeypatch, "modules.hit_scorer", score_track=lambda path: {"error": "нет файла"})
    assert commands.run_score("master.wav") == 2


def test_update_ok_and_failure(said, monkeypatch) -> None:
    _stub(monkeypatch, "updater.updater", check_git_update_status=lambda root: {"ok": True, "behind": 0})

    assert commands.run_update() == 0

    _stub(monkeypatch, "updater.updater", check_git_update_status=lambda root: {"ok": False, "reason": "no git"})
    assert commands.run_update() == 2, "непроверяемое обновление не выдаётся за успех"


def test_readiness_returns_json_with_percent(said, monkeypatch) -> None:
    _stub(monkeypatch, "tools.readiness", compute=lambda: (65, {"cap": "no microphone"}))

    assert commands.run_readiness() == 0
    payload = json.loads("\n".join(said))
    assert payload["percent"] == 65


def test_readiness_failure_is_code_2(said, monkeypatch) -> None:
    _stub(monkeypatch, "tools.readiness", compute=None)

    assert commands.run_readiness() == 2


# --------------------------------------------------------------------------- #
#  AI-команды
# --------------------------------------------------------------------------- #

def test_ai_status_lists_roles_without_promising_weights(said, monkeypatch) -> None:
    registry = types.SimpleNamespace(
        hw={"ram_gb": 32.0},
        is_available=lambda key: key == "vocal_rvc",
    )
    models = {
        "vocal_rvc": {"engine": "rvc", "role": "voice"},
        "llm": {"engine": "gguf", "role": "lyrics", "vram_est_gb": 8},
    }
    _stub(monkeypatch, "app.ai.registry", MODEL_REGISTRY=models, registry=registry)
    _stub(monkeypatch, "app.core.hw_autodetect", detect=lambda: {"x": 1}, human_summary=lambda p: "CPU: test")

    assert commands.run_ai_status() == 0
    text = "\n".join(said)
    assert "FILES vocal_rvc" in text
    assert "-- llm" in text.replace("  --", "--", 1) or "--" in text
    assert "do not prove weights or inference" in text


def test_ai_pull_all_reports_failure(said, monkeypatch) -> None:
    _stub(monkeypatch, "app.ai.registry", MODEL_REGISTRY={"a": {}, "b": {}})
    pulled: list[str] = []
    _stub(monkeypatch, "tools.pull_ai_models", pull=lambda role: pulled.append(role) or role == "a")

    assert commands.run_ai_pull("ALL") == 2
    assert pulled == ["a", "b"]


def test_ai_pull_single_success(said, monkeypatch) -> None:
    _stub(monkeypatch, "tools.pull_ai_models", pull=lambda role: True)

    assert commands.run_ai_pull("llm") == 0


# --------------------------------------------------------------------------- #
#  Консольный REPL
# --------------------------------------------------------------------------- #

def _feed(monkeypatch, lines: list[str]) -> None:
    iterator = iter(lines)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(iterator))


def test_console_runs_known_command_then_exits(said, monkeypatch) -> None:
    called: list[str] = []
    monkeypatch.setattr(commands, "run_version", lambda: called.append("version") or 0)
    _feed(monkeypatch, ["version", "exit"])

    assert commands.run_console() == 0
    assert called == ["version"]


def test_console_reports_unknown_command(said, monkeypatch) -> None:
    _feed(monkeypatch, ["что-то", "quit"])

    assert commands.run_console() == 0
    assert any("unknown" in line for line in said)


def test_console_exits_on_eof(said, monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": (_ for _ in ()).throw(EOFError()))

    assert commands.run_console() == 0


def test_console_q_exits(said, monkeypatch) -> None:
    _feed(monkeypatch, ["q"])

    assert commands.run_console() == 0


# --------------------------------------------------------------------------- #
#  Обёртки над внешними entrypoint'ами
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "func,module,attr,expected",
    [
        (commands.run_dashboard, "modules.kpi_dashboard", "main", 0),
        (commands.run_self_diag, "modules.self_diag", "main_entry", 0),
        (commands.run_e2e, "tools.e2e", "main", 0),
        (commands.run_onboarding, "modules.voice_onboarding", "run_cli", 0),
    ],
)
def test_entrypoint_wrappers_pass_through_code(said, monkeypatch, func, module, attr, expected) -> None:
    _stub(monkeypatch, module, **{attr: lambda: 0})

    assert func() == expected


@pytest.mark.parametrize(
    "func,module,attr",
    [
        (commands.run_dashboard, "modules.kpi_dashboard", "main"),
        (commands.run_self_diag, "modules.self_diag", "main_entry"),
        (commands.run_e2e, "tools.e2e", "main"),
        (commands.run_onboarding, "modules.voice_onboarding", "run_cli"),
    ],
)
def test_entrypoint_wrappers_turn_crash_into_code_2(said, monkeypatch, func, module, attr) -> None:
    def boom():
        raise ImportError("модуль недоступен")

    _stub(monkeypatch, module, **{attr: boom})

    assert func() == 2
    assert "failed" in said[0]


def test_ai_status_failure_is_code_2(said, monkeypatch) -> None:
    _stub(monkeypatch, "app.ai.registry", MODEL_REGISTRY=None, registry=None)

    assert commands.run_ai_status() == 2
    # профиль железа печатается до проверки реестра — отказ ищем в выводе целиком
    assert any("ai-status" in line for line in said)
    assert any("failed" in line for line in said)


def test_ai_pull_failure_is_code_2(said, monkeypatch) -> None:
    _stub(monkeypatch, "tools.pull_ai_models", pull=None)

    assert commands.run_ai_pull("llm") == 2


def test_update_crash_is_code_2(said, monkeypatch) -> None:
    _stub(monkeypatch, "updater.updater", check_git_update_status=None)

    assert commands.run_update() == 2
    assert "update" in said[0]


def test_score_crash_is_code_2(said, monkeypatch) -> None:
    _stub(monkeypatch, "modules.hit_scorer", score_track=None)

    assert commands.run_score("master.wav") == 2
    assert "score" in said[0]
