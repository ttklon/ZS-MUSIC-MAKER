# -*- coding: utf-8 -*-
"""`modules/llm/ollama_setup.py`: установка Ollama из приложения, честно.

До модуля единственным способом поставить Ollama и текстовую модель было
руками в консоли: bootstrap молча возвращал `[]`, если `ollama` нет в `PATH`,
и чистая машина получала `BLOCKED` без кнопки. Здесь проверяется то, что
важно для «работает на чистой Windows»: состояния различаются (`нет бинаря` ≠
`нет демона` ≠ `нет модели`), сеть не трогается без согласия, а установщик
не «запускается тихо» за спиной у человека.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modules.llm import ollama_setup


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Любой HTTP-запрос в этих тестах — ошибка, а не «повезло с сетью»."""
    monkeypatch.setenv("ZSMM_OLLAMA_URL", "http://127.0.0.1:11434")
    monkeypatch.delenv("ZSMM_OLLAMA_PULL_MODEL", raising=False)
    monkeypatch.setattr(ollama_setup, "_daemon_models", lambda *_a, **_k: None)
    monkeypatch.setattr(ollama_setup, "_ollama_bin", lambda: None)
    return monkeypatch


def test_report_without_ollama_has_reason_and_action() -> None:
    report = ollama_setup.install_report()

    assert report["ready"] is False
    assert report["daemon"] == "down"
    assert report["model"] == "qwen3:4b"
    assert report["reason"], "отказ без причины — это то же молчание"
    assert report["action"], "нужен следующий шаг, а не только статус"


def test_missing_daemon_and_missing_model_are_different_states(monkeypatch) -> None:
    monkeypatch.setattr(ollama_setup, "_ollama_bin", lambda: "/usr/bin/ollama")

    down = ollama_setup.install_report()
    monkeypatch.setattr(ollama_setup, "_daemon_models", lambda *_a, **_k: [])
    empty = ollama_setup.install_report()
    monkeypatch.setattr(ollama_setup, "_daemon_models", lambda *_a, **_k: ["llama3.2:1b"])

    other = ollama_setup.install_report()

    assert down["daemon"] == "down"
    assert empty["daemon"] == "up_no_models"
    assert other["daemon"] == "up"
    assert "демон" in down["reason"]
    assert "qwen3:4b" in other["reason"] and "ollama pull" in other["action"]


def test_ready_when_daemon_has_the_model(monkeypatch) -> None:
    monkeypatch.setattr(ollama_setup, "_daemon_models", lambda *_a, **_k: ["qwen3:4b"])

    report = ollama_setup.install_report()

    assert report["ready"] is True
    assert report["reason"] == "" and report["action"] == ""


def test_model_tag_matches_ignoring_tag_case(monkeypatch) -> None:
    """`qwen3:4b` и `qwen3:4b-instruct` — разные модели, а `QWEN3:4B` — та же."""
    monkeypatch.setattr(ollama_setup, "_daemon_models", lambda *_a, **_k: ["QWEN3:4B"])

    assert ollama_setup.install_report()["ready"] is True


def test_ensure_checks_network_before_any_download(monkeypatch) -> None:
    downloads: list = []
    monkeypatch.setattr(ollama_setup, "_download", lambda *a, **k: downloads.append(a))
    monkeypatch.setattr("app.core.net_policy.network_allowed",
                        lambda allow_online=False, settings_path=None: False)

    result = ollama_setup.ensure_ollama()

    assert result["ok"] is False
    assert downloads == [], "без согласия на сеть скачивания быть не должно"
    assert "network disabled" in result["reason"]
    assert "Диагностике" in result["action"]


def test_ensure_offline_when_daemon_already_has_model(monkeypatch) -> None:
    """Готовое состояние не требует сети: `pull` не зовётся зря."""
    monkeypatch.setattr(ollama_setup, "_daemon_models", lambda *_a, **_k: ["qwen3:4b"])
    monkeypatch.setattr(ollama_setup, "_pull_model",
                        lambda *a, **k: pytest.fail("pull не нужен: модель уже есть"))

    result = ollama_setup.ensure_ollama(allow_download=False)

    assert result["ok"] is True
    assert result["changed"] is False


def test_ensure_pulls_when_daemon_alive_and_model_missing(monkeypatch) -> None:
    state = {"models": ["llama3.2:1b"]}
    monkeypatch.setattr(ollama_setup, "_daemon_models", lambda *_a, **_k: list(state["models"]))

    def fake_pull(model, timeout=0):
        state["models"] = ["llama3.2:1b", model]
        return {"ok": True, "model": model}

    monkeypatch.setattr(ollama_setup, "_pull_model", fake_pull)

    result = ollama_setup.ensure_ollama(allow_download=True)

    assert result["ok"] is True
    assert result["changed"] is True
    assert result["ready"] is True


def test_pull_failure_keeps_honest_reason(monkeypatch) -> None:
    monkeypatch.setattr(ollama_setup, "_daemon_models", lambda *_a, **_k: [])
    monkeypatch.setattr(ollama_setup, "_pull_model",
                        lambda *a, **k: {"ok": False, "reason": "pull_failed: denied"})

    result = ollama_setup.ensure_ollama(allow_download=True)

    assert result["ok"] is False
    assert "pull_failed" in result["reason"]
    assert result["action"] == "ollama pull qwen3:4b"


def test_linux_install_is_a_hint_not_a_silent_curl_pipe(monkeypatch, tmp_path: Path) -> None:
    """`curl | sh` за спиной у пользователя — недопустимо: только подсказка."""
    monkeypatch.setattr(ollama_setup.platform, "system", lambda: "Linux")

    result = ollama_setup.ensure_ollama(allow_download=True)

    assert result["ok"] is False
    assert result["action"].startswith("curl -fsSL")
    assert (tmp_path / "installers").exists() is False
    assert "curl" in result["action"] and "sh" in result["action"]


def test_dry_run_changes_nothing(monkeypatch) -> None:
    monkeypatch.setattr(ollama_setup, "_download",
                        lambda *a, **k: pytest.fail("dry_run не качает"))
    monkeypatch.setattr(ollama_setup, "_pull_model",
                        lambda *a, **k: pytest.fail("dry_run не тянет модель"))

    result = ollama_setup.ensure_ollama(allow_download=True, dry_run=True)

    assert result["dry_run"] is True
    assert result["changed"] is False


def test_windows_download_returns_installer_and_asks_for_user_action(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ollama_setup.platform, "system", lambda: "Windows")
    monkeypatch.setattr(
        ollama_setup, "_download",
        lambda url, target, timeout=900.0: (
            target.parent.mkdir(parents=True, exist_ok=True),
            target.write_bytes(b"MZ"),
            {"ok": True, "path": str(target), "bytes": 2},
        )[-1],
    )

    result = ollama_setup.ensure_ollama(allow_download=True)

    assert result["needs_user_action"] is True, "MSI требует UAC — это шаг человека"
    assert result["installer"].endswith("OllamaSetup.exe")
    assert Path(result["installer"]).is_file()
    assert "UAC" in result["reason"]


def test_cli_module_prints_json(capsys, monkeypatch) -> None:
    code = ollama_setup.main([])
    payload = json.loads(capsys.readouterr().out)

    assert code == 1  # в песочнице Ollama нет — это честный отказ
    assert payload["ready"] is False


def test_readiness_probe_reports_blocked_without_ollama() -> None:
    from tools.readiness.probes import probe_audio_pipeline

    assert probe_audio_pipeline()["lyrics_llm"] == "BLOCKED"


def test_bootstrap_records_honest_ollama_state(monkeypatch) -> None:
    """`auto_bootstrap.ollama` должен объяснять отказ, а не молчать.

    Раньше `_ensure_ollama_qwen()` возвращал `[]` без следа в отчёте: окно
    показывало пустой текст и не могло сказать, чего не хватает.
    """
    from app.core import bootstrap

    bootstrap.auto_bootstrap_last.clear()
    monkeypatch.setattr(bootstrap, "_network_allowed", lambda: False)
    monkeypatch.setattr("modules.llm.ollama_setup._ollama_bin", lambda: None)

    pulled = bootstrap._ensure_ollama_qwen(allow_download=False)

    assert pulled == []
    state = bootstrap.auto_bootstrap_last["ollama"]
    assert state["ready"] is False
    assert "network disabled" in state["reason"]
    assert state["action"], "без следующего шага отказ бесполезен"
