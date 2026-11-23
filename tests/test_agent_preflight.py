"""Installed agent hardware preflight contracts; no model inference is claimed."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ai import profiles


MEASUREMENTS = {
    "cpu_threads": 8,
    "ram_total_gib": 16.0,
    "ram_available_gib": 8.0,
    "disk_free_gib": 24.0,
    "gpu": {"adapters": [], "pytorch_device": None, "directml_devices": [],
            "inference_verified": False},
}


def _inventory(*, system=None, measurements=None, errors=None, kind="inventory_only"):
    return {
        "schema": 1,
        "kind": kind,
        "os": "TestOS",
        "os_release": "1",
        "architecture": "x86_64",
        "measurements": dict(MEASUREMENTS if measurements is None else measurements),
        "errors": list(errors or []),
        "system": {"cpu_threads": 8, "ram_total_gib": 16.0, "ram_available_gib": 8.0,
                   "disk_free_gib": 24.0, "pytorch_device": None, "gpus": []}
                  if system is None else system,
        "inference_verified": False,
        "product_profile_accepted": False,
    }


def _safe_adaptive(**changes):
    config = {"level": 0, "use_acestep": False, "use_musicgen": False,
              "use_silero": False, "use_rvc": False, "gpu": {"backend": "cpu"}}
    config.update(changes)
    return config


def _install_measurements(monkeypatch, *, inventory=None, adaptive=None, observed=None):
    from modules.hit_factory import adaptive as adaptive_module

    inventory = inventory or _inventory()
    adaptive = adaptive or _safe_adaptive()
    monkeypatch.setattr(profiles, "measure_profile", lambda directory: inventory)

    def select(*, system):
        if observed is not None:
            observed.append(system)
        return dict(adaptive)

    monkeypatch.setattr(adaptive_module, "get_adaptive_config", select)
    return inventory


def test_preflight_uses_one_inventory_and_routes_same_snapshot(monkeypatch, tmp_path):
    from app.ai.agent_preflight import preflight_agent_hardware

    system = {"cpu_threads": 8, "ram_total_gib": 16.0, "ram_available_gib": 8.0,
              "disk_free_gib": 24.0, "pytorch_device": None, "gpus": []}
    inventory = _inventory(system=system)
    observed = []
    _install_measurements(monkeypatch, inventory=inventory, observed=observed)
    output_root = tmp_path / "not-created" / "hits"

    record, adaptive = preflight_agent_hardware({"use_texture": False}, output_root)

    assert observed == [system] and observed[0] is system
    assert not output_root.exists()
    assert record["status"] == "inventory_only"
    assert record["decision"] == "continue_unverified" and record["can_attempt"] is True
    assert record["selected_backend"] == "procedural_dsp"
    assert record["resource_budget_status"] == "not_established"
    assert record["texture_route"]["selected_backend"] == "disabled"
    assert record["inventory"]["measurements"] == MEASUREMENTS
    assert record["inference_verified"] is False and record["product_profile_accepted"] is False
    assert adaptive["use_musicgen"] is False and adaptive["use_texture"] is False


def test_measurement_uses_existing_target_volume_ancestor(monkeypatch, tmp_path):
    from app.ai.agent_preflight import preflight_agent_hardware

    seen = []
    monkeypatch.setattr(profiles, "measure_profile", lambda directory: seen.append(Path(directory)) or _inventory())
    from modules.hit_factory import adaptive as adaptive_module
    monkeypatch.setattr(adaptive_module, "get_adaptive_config", lambda **kwargs: _safe_adaptive())
    absent = tmp_path / "not-yet" / "nested" / "hits"

    preflight_agent_hardware({"use_texture": False}, absent)

    assert seen == [tmp_path.resolve()]
    assert not absent.exists()


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), -1, True, "8"])
def test_missing_or_invalid_required_measurement_refuses(value, monkeypatch, tmp_path):
    from app.ai.agent_preflight import preflight_agent_hardware

    measurements = dict(MEASUREMENTS)
    measurements["ram_available_gib"] = value
    _install_measurements(monkeypatch, inventory=_inventory(measurements=measurements))

    record, _ = preflight_agent_hardware({"use_texture": False}, tmp_path / "hits")

    assert record["decision"] == "refuse" and record["can_attempt"] is False
    assert any("ram_available_gib" in reason for reason in record["reasons"])
    assert record["inference_verified"] is False


@pytest.mark.parametrize(("name", "value", "reason"), [
    ("ram_available_gib", 1.99, "safety floor"),
    ("disk_free_gib", 0.99, "safety floor"),
])
def test_known_but_insufficient_resources_refuse_before_backend_selection(name, value, reason, monkeypatch, tmp_path):
    from app.ai.agent_preflight import preflight_agent_hardware
    from modules.hit_factory import adaptive as adaptive_module

    measurements = dict(MEASUREMENTS)
    measurements[name] = value
    system = {"cpu_threads": 8, "ram_total_gib": 16.0, "ram_available_gib": 8.0,
              "disk_free_gib": 24.0, "pytorch_device": None, "gpus": []}
    system[name] = value
    _install_measurements(monkeypatch, inventory=_inventory(system=system, measurements=measurements))
    monkeypatch.setattr(adaptive_module, "get_adaptive_config",
                        lambda **_kwargs: pytest.fail("insufficient base resources must refuse before backend selection"))

    record, adaptive = preflight_agent_hardware({"use_texture": False}, tmp_path / "hits")

    assert record["decision"] == "refuse" and record["can_attempt"] is False
    assert record["selected_backend"] == "not_selected"
    assert any(name in item and reason in item for item in record["reasons"])
    assert adaptive == {"use_acestep": False, "use_musicgen": False, "use_texture": False}
    assert not (tmp_path / "hits").exists()


def test_unknown_disk_refuses_before_backend_selection(monkeypatch, tmp_path):
    from app.ai.agent_preflight import preflight_agent_hardware
    from modules.hit_factory import adaptive as adaptive_module

    measurements = dict(MEASUREMENTS)
    measurements["disk_free_gib"] = None
    system = {"cpu_threads": 8, "ram_total_gib": 16.0, "ram_available_gib": 8.0,
              "disk_free_gib": None, "pytorch_device": None, "gpus": []}
    _install_measurements(monkeypatch, inventory=_inventory(system=system, measurements=measurements))
    monkeypatch.setattr(adaptive_module, "get_adaptive_config",
                        lambda **_kwargs: pytest.fail("unknown disk must refuse before backend selection"))

    record, _ = preflight_agent_hardware({"use_texture": False}, tmp_path / "hits")

    assert record["decision"] == "refuse" and record["can_attempt"] is False
    assert any("disk_free_gib" in item for item in record["reasons"])
    assert not (tmp_path / "hits").exists()


def test_malformed_inventory_is_fail_closed(monkeypatch, tmp_path):
    from app.ai.agent_preflight import preflight_agent_hardware

    _install_measurements(monkeypatch, inventory=None)
    monkeypatch.setattr(profiles, "measure_profile", lambda _directory: None)

    record, _ = preflight_agent_hardware({"use_texture": False}, tmp_path / "hits")

    assert record["decision"] == "refuse" and record["can_attempt"] is False
    assert any("inventory" in reason for reason in record["reasons"])


def test_runner_refuses_texture_record_that_claims_inference(monkeypatch):
    from modules.agent_guide.preflight_report import validate_preflight_result

    record = {"schema": 1, "status": "inventory_only", "decision": "continue_unverified",
              "can_attempt": True, "selected_backend": "procedural_dsp",
              "resource_budget_status": "not_established",
              "texture_route": {"selected_backend": "disabled", "inference_verified": True},
              "reasons": [], "inference_verified": False, "product_profile_accepted": False}

    checked, _adaptive, can_attempt = validate_preflight_result((record, _safe_adaptive()))

    assert can_attempt is False
    assert checked["status"] == "blocked" and checked["decision"] == "refuse"
    assert checked["inference_verified"] is False and checked["product_profile_accepted"] is False
    assert any("safe DSP" in reason for reason in checked["reasons"])


def test_unbudgeted_musicgen_and_ace_step_are_refused(monkeypatch, tmp_path):
    from app.ai.agent_preflight import preflight_agent_hardware

    for adaptive, expected in (({"use_musicgen": True}, "musicgen"),
                               ({"use_acestep": True, "use_musicgen": True}, "ace_step")):
        _install_measurements(monkeypatch, adaptive=_safe_adaptive(**adaptive))
        record, _ = preflight_agent_hardware({"use_texture": False}, tmp_path / expected)
        assert record["selected_backend"] == expected
        assert record["decision"] == "refuse"
        assert record["resource_budget_status"] == "missing_for_selected_backend"
        assert not record["inference_verified"] and not record["product_profile_accepted"]


def test_optional_musicgen_texture_must_be_disabled_until_budget_exists(monkeypatch, tmp_path):
    from app.ai.agent_preflight import preflight_agent_hardware

    _install_measurements(monkeypatch)

    record, adaptive = preflight_agent_hardware({"use_texture": True}, tmp_path / "hits")

    assert record["decision"] == "refuse"
    assert any("MusicGen texture" in reason for reason in record["reasons"])
    assert adaptive["use_texture"] is False


def test_requested_rvc_preflight_reuses_system_snapshot(monkeypatch, tmp_path):
    from app.ai.agent_preflight import preflight_agent_hardware
    from importlib import import_module

    infer = import_module("modules.rvc_manager.infer")
    voice = tmp_path / "take.wav"
    voice.write_bytes(b"test-only path")
    system = {"cpu_threads": 8, "ram_total_gib": 16.0, "ram_available_gib": 8.0,
              "disk_free_gib": 24.0, "pytorch_device": None, "gpus": []}
    _install_measurements(monkeypatch, inventory=_inventory(system=system))
    observed = {}

    def rvc_preflight(*, system):
        observed["system"] = system
        return {"schema": 1, "allowed": True, "backend": "cpu", "device": "cpu:0",
                "available_ram_gib": 8.0, "inference_verified": False, "reasons": []}

    monkeypatch.setattr(infer, "preflight_rvc_inference", rvc_preflight)
    record, _ = preflight_agent_hardware({"own_vocal_wav": str(voice), "use_rvc": True,
                                          "use_texture": False}, tmp_path / "hits")

    assert observed["system"] is system
    assert record["decision"] == "continue_unverified"
    assert record["rvc"]["inference_verified"] is False


@pytest.mark.parametrize(("free_vram", "expected"), [
    (None, "unknown or invalid"), (1.0, "below the 4 GiB safety floor"),
])
def test_requested_rvc_gpu_refuses_unknown_or_insufficient_vram(monkeypatch, tmp_path, free_vram, expected):
    from app.ai.agent_preflight import preflight_agent_hardware

    voice = tmp_path / "probe.wav"
    voice.write_bytes(b"preflight-only; inference must not run")
    system = {"cpu_threads": 8, "ram_total_gib": 16.0, "ram_available_gib": 8.0,
              "disk_free_gib": 24.0, "pytorch_device": {"backend": "cuda",
              "vendor": "nvidia", "total_vram_gib": 8.0, "free_vram_gib": free_vram},
              "gpus": []}
    _install_measurements(monkeypatch, inventory=_inventory(system=system))

    record, _ = preflight_agent_hardware({"own_vocal_wav": str(voice), "use_rvc": True,
                                          "use_texture": False}, tmp_path / "hits")

    assert record["decision"] == "refuse" and record["can_attempt"] is False
    assert record["rvc"]["allowed"] is False
    assert any(expected in reason for reason in record["reasons"])
    assert not (tmp_path / "hits").exists()


def test_requested_rvc_without_input_is_refused_before_work(monkeypatch, tmp_path):
    from app.ai.agent_preflight import preflight_agent_hardware

    _install_measurements(monkeypatch)
    record, _ = preflight_agent_hardware({"own_vocal_wav": "", "use_rvc": True}, tmp_path / "hits")

    assert record["decision"] == "refuse"
    assert any("without an input" in reason for reason in record["reasons"])


def test_installed_agent_cli_does_not_bootstrap_before_preflight(monkeypatch, tmp_path):
    from app.core import bootstrap
    from app.cli import agent_task
    from modules.agent_guide import runner

    calls = []
    monkeypatch.setattr(bootstrap, "auto_bootstrap", lambda **kwargs: calls.append(kwargs))
    refusal = {"schema": 1, "status": "blocked", "decision": "refuse", "can_attempt": False,
               "selected_backend": "procedural_dsp", "resource_budget_status": "not_established",
               "texture_route": {"selected_backend": "disabled", "inference_verified": False},
               "reasons": ["inventory unavailable"], "inference_verified": False,
               "product_profile_accepted": False}
    monkeypatch.setattr(runner, "_hardware_preflight", lambda *_args: (refusal, {}))
    monkeypatch.setattr(runner, "_trend", lambda *_args: pytest.fail("preflight refusal must stop stages"))
    args = SimpleNamespace(online=True, agent_output=str(tmp_path / "unused"))

    assert agent_task.run_agent_hit(args) == 1
    assert calls == []
    assert not (tmp_path / "unused").exists()


@pytest.mark.parametrize(("existing", "inside", "after"), [
    (None, "1", None), ("0", "0", "0"), ("1", "1", "1"),
])
def test_cli_online_consent_is_scoped_and_never_overrides_off(existing, inside, after, monkeypatch):
    import os
    from app.cli import agent_task
    import modules.agent_guide as guide

    if existing is None:
        monkeypatch.delenv("ZSMM_ONLINE", raising=False)
    else:
        monkeypatch.setenv("ZSMM_ONLINE", existing)
    observed = []
    monkeypatch.setattr(guide, "run_conversation_hit", lambda *a, **kw:
                        observed.append(os.environ.get("ZSMM_ONLINE")) or {"master_path": None})
    monkeypatch.setattr(guide, "narrate", lambda _report: "")

    assert agent_task.run_agent_hit(SimpleNamespace(online=True)) == 1

    assert observed == [inside]
    assert os.environ.get("ZSMM_ONLINE") == after
