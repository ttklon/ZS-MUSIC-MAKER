# -*- coding: utf-8 -*-
"""`app/hw_probe.py`: что GUI показывает про железо.

Модуль был не покрыт ни одним тестом, хотя это лицо программы: первое окно и
вкладка диагностики показывают именно эти числа. Проверяется отображение, а не
измерение: реальное железо подменяется профилем, чтобы тест не зависел от
машины.

Правило, которое здесь держится: отсутствующее измерение остаётся `None`, а не
превращается в ноль. Ноль читается как «памяти нет», `None` — как «не измерили».
"""

from __future__ import annotations

import json
import sys
import types

import pytest

from app import hw_probe


def _profile(**overrides) -> dict:
    system = {
        "os": "Linux",
        "os_version": "6.1",
        "architecture": "x86_64",
        "cpu_name": "Test CPU",
        "cpu_threads": 16,
        "cpu_cores": 8,
        "ram_total_gib": 32.0,
        "ram_available_gib": 12.5,
        "disk_free_gib": 100.0,
        "gpus": [
            {"name": "NVIDIA RTX 4070", "vendor": "nvidia", "total_vram_gib": 12.0,
             "free_vram_gib": 10.0, "source": "torch"},
        ],
        "pytorch_device": {
            "name": "NVIDIA RTX 4070", "vendor": "nvidia", "backend": "cuda",
            "total_vram_gib": 12.0, "free_vram_gib": 10.0,
        },
        "directml_devices": [],
        "default_backend": "cuda",
        "notice": "Hardware detection does not verify model weights, compatibility or inference.",
    }
    profile = {"system": system, "gpu": {
        "kind": system["default_backend"],
        "name": system["pytorch_device"]["name"],
        "vendor": "nvidia",
        "vram_gb": 12.0,
        "vram_free_gb": 10.0,
        "ok": True,
    }, "mode": "full"}
    profile.update(overrides)
    return profile


@pytest.fixture
def fake_detect(monkeypatch):
    holder = {"profile": _profile()}

    def detect(force: bool = False):
        assert force in (False, True)
        return holder["profile"]

    module = types.SimpleNamespace(detect=detect)
    monkeypatch.setitem(sys.modules, "app.core.hw_autodetect", module)
    monkeypatch.setattr("app.core.hw_autodetect", module, raising=False)
    return holder


def test_probe_maps_detected_profile(fake_detect) -> None:
    hw = hw_probe.probe()

    assert hw.gpu_name == "NVIDIA RTX 4070"
    assert hw.backend == "cuda"
    assert hw.vram_gb == 12.0
    assert hw.vram_free_gb == 10.0
    assert hw.ram_gb == 32.0
    assert hw.ram_available_gb == 12.5
    assert hw.disk_free_gb == 100.0
    assert hw.cpu_name == "Test CPU"
    assert hw.os_name == "Linux 6.1"
    assert hw.mode == "full"


def test_missing_measurements_stay_none(fake_detect) -> None:
    """`None` — «не измерено»; ноль читался бы как «памяти нет»."""
    profile = _profile()
    profile["system"]["ram_available_gib"] = None
    profile["system"]["disk_free_gib"] = None
    profile["gpu"]["vram_free_gb"] = None
    fake_detect["profile"] = profile

    hw = hw_probe.probe()

    assert hw.ram_available_gb is None
    assert hw.disk_free_gb is None
    assert hw.vram_free_gb is None


def test_probe_reports_cpu_only_machine(fake_detect) -> None:
    profile = _profile()
    profile["system"]["pytorch_device"] = None
    profile["system"]["gpus"] = []
    profile["system"]["default_backend"] = "cpu"
    profile["gpu"] = {"kind": "cpu", "name": "unknown", "vendor": "unknown",
                      "vram_gb": 0.0, "vram_free_gb": None, "ok": False}
    profile["mode"] = "lite"
    fake_detect["profile"] = profile

    hw = hw_probe.probe()

    assert hw.backend == "cpu"
    assert hw.vram_gb == 0.0
    assert hw.mode == "lite"
    assert hw.ram_gb == 32.0, "CPU-профиль не повод терять RAM"


def test_hw_is_serialisable_for_gui_and_diagnostics(fake_detect) -> None:
    from dataclasses import asdict

    payload = asdict(hw_probe.probe())

    assert json.loads(json.dumps(payload, ensure_ascii=False))["mode"] == "full"
    assert set(payload) == {
        "gpu_name", "vram_gb", "backend", "ram_gb", "cpu_name", "os_name", "mode",
        "ram_available_gb", "disk_free_gb", "vram_free_gb",
    }


def test_unknown_os_string_is_not_left_empty(fake_detect) -> None:
    profile = _profile()
    profile["system"]["os"] = ""
    profile["system"]["os_version"] = ""
    fake_detect["profile"] = profile

    hw = hw_probe.probe()

    assert hw.os_name == " ", "пустая ОС даёт пробел, а не пустую строку"


def test_main_prints_json(fake_detect, capsys) -> None:
    hw_probe.main()

    payload = json.loads(capsys.readouterr().out)

    assert payload["backend"] == "cuda"
    assert payload["ram_gb"] == 32.0


def test_real_detector_returns_plausible_values() -> None:
    """Один честный вызов настоящего детектора: типы и границы, не конкретика."""
    hw = hw_probe.probe()

    assert isinstance(hw.mode, str) and hw.mode in {"lite", "mid", "full"}
    assert isinstance(hw.backend, str) and hw.backend
    assert hw.ram_gb >= 0.0
    assert hw.vram_gb >= 0.0
    assert hw.disk_free_gb is None or hw.disk_free_gb >= 0.0
    assert isinstance(hw.os_name, str) and hw.os_name.strip()


def test_module_entrypoint_prints_json(fake_detect, monkeypatch, capsys) -> None:
    """`python -m app.hw_probe` — документированный способ диагностики."""
    import runpy

    # runpy предупреждает, что модуль уже импортирован тестами; это ожидаемо
    monkeypatch.delitem(sys.modules, "app.hw_probe", raising=False)
    namespace = runpy.run_module("app.hw_probe", run_name="__main__")
    assert json.loads(capsys.readouterr().out)["mode"] == "full"

    assert namespace["__name__"] == "__main__"
    assert "main" in namespace
