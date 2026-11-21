"""Setup must neither report failed downloads as success nor break the main venv."""
import sys
from types import SimpleNamespace

import pytest

from app.core import bootstrap
from app.core.bootstrap_report import summarize_setup


def ready():
    return {"heavy": {}, "models": {}, "ollama": {"ok": True},
            "rvc": {"present": True}, "rvc_env": {"ok": True},
            "rvc_trainer": {"present": True}, "readiness_after": 65}


def test_setup_success_is_not_inference_proof():
    report = summarize_setup(ready())
    assert report == {"ok": True, "blockers": [], "inference_verified": False}


@pytest.mark.parametrize("stage,flag", [("rvc", "present"), ("rvc_trainer", "present"),
                                         ("rvc_env", "ok"), ("ollama", "ok")])
def test_readiness_percentage_cannot_hide_missing_engine(stage, flag):
    result = ready()
    result["readiness_after"] = 100
    result[stage] = {flag: False, "reason": "network disabled"}
    report = summarize_setup(result)
    assert report["ok"] is False
    assert any(stage in b and "network disabled" in b for b in report["blockers"])


@pytest.mark.parametrize("status", ["failed", "skipped"])
def test_failed_or_skipped_packages_block_setup(status):
    result = ready()
    result["heavy"] = {status: ["torch"]}
    assert summarize_setup(result)["ok"] is False


def test_rvc_is_not_installed_into_main_numpy_environment():
    assert "rvc_python" not in bootstrap.HEAVY_PIP
    assert "rvc_python" not in bootstrap.PIP_TO_IMPORT


def test_pip_exit_zero_requires_successful_import(monkeypatch):
    monkeypatch.setattr(bootstrap, "missing_heavy", lambda: ["torch"])
    monkeypatch.setattr(bootstrap, "silent_hardware_budget", lambda: {})
    monkeypatch.setattr(bootstrap, "_pip_install", lambda *a, **kw: True)
    monkeypatch.setattr(bootstrap, "_module_exists", lambda name: False)
    assert bootstrap.ensure_heavy_engines(allow_download=True) == {
        "installed": [], "failed": ["torch"], "skipped": []}


def test_false_model_download_is_recorded_as_failure(monkeypatch):
    monkeypatch.setitem(sys.modules, "tools.pull_ai_models", SimpleNamespace(pull=lambda role: False))
    monkeypatch.setattr("app.ai.model_catalog.MODEL_REGISTRY", {"test_role": {"engine": "test"}})
    from app.ai.registry import registry
    monkeypatch.setattr(registry, "is_available", lambda role: False)
    assert bootstrap._pull_missing_roles() == ([], ["test_role"])


def test_offline_never_calls_pip(monkeypatch):
    monkeypatch.setattr(bootstrap, "missing_heavy", lambda: ["torch"])
    monkeypatch.setattr(bootstrap, "_pip_install", lambda *a, **kw: pytest.fail("offline pip"))
    assert bootstrap.ensure_heavy_engines(allow_download=False)["skipped"] == ["torch"]


def test_bootstrap_command_returns_failure_even_at_high_score(monkeypatch):
    from app.cli.commands import run_bootstrap
    monkeypatch.setattr(bootstrap, "wire_full_agents", lambda: None)
    monkeypatch.setattr(bootstrap, "auto_bootstrap", lambda **kw: {
        "ok": False, "readiness_after": 100, "blockers": ["torch import failed"]})
    assert run_bootstrap() == 1


def test_audiocraft_cannot_downgrade_main_torch(monkeypatch, caplog):
    monkeypatch.setattr(bootstrap, "missing_heavy", lambda: ["audiocraft"])
    monkeypatch.setattr(bootstrap, "silent_hardware_budget", lambda: {})
    monkeypatch.setattr(bootstrap, "_pip_install", lambda *a, **kw: pytest.fail("incompatible shared install"))
    result = bootstrap.ensure_heavy_engines(allow_download=True)
    assert result["failed"] == ["audiocraft"]
    assert result["installed"] == []
    assert "isolated environment" in caplog.text
