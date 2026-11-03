"""Hardware profiles and model selection are simulated, not GPU inference tests."""
import importlib
import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from app.ai import hardware
from modules.llm.ollama_adaptive import choose_installed_model


def _system(monkeypatch, adapters, torch_device=None, dml=None, ram=12):
    monkeypatch.setattr(hardware, "detect_budget", lambda: {
        "ram_gb": 16.0, "vram_gb": 0.0, "cpu_threads": 8, "cpu_cores": 4})
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: ram)
    monkeypatch.setattr(hardware, "_windows_adapters", lambda: adapters)
    monkeypatch.setattr(hardware, "_dxgi_adapters", lambda: [])
    monkeypatch.setattr(hardware, "_torch_device", lambda: torch_device or {})
    monkeypatch.setattr(hardware, "_directml_devices", lambda: dml or [])
    return hardware.detect_system()


def test_rx580_installed_is_not_misreported_as_available_rocm(monkeypatch):
    adapter = {"name": "Radeon RX 580 Series", "vendor": "amd", "source": "windows_cim"}
    system = _system(monkeypatch, [adapter])
    assert system["gpus"] == [adapter]
    assert system["default_backend"] == "cpu" and system["pytorch_device"] is None
    from app.core import hw_autodetect
    monkeypatch.setattr(hw_autodetect, "detect_system", lambda: system)
    profile = hw_autodetect.detect()
    assert profile["gpu"]["name"] == "Radeon RX 580 Series"
    assert profile["gpu"]["vram_gb"] == 0 and profile["gpu"]["vram_free_gb"] is None
    assert profile["gpu"]["kind"] == "cpu" and profile["mode"] == "lite"
    assert "обучение не подключено" in profile["recommendations"]["rvc"]


def test_cuda_and_rocm_backend_are_distinguished(monkeypatch):
    gib = 1024 ** 3
    cuda = SimpleNamespace(is_available=lambda: True, get_device_name=lambda index: "AMD Radeon RX",
                           get_device_properties=lambda index: SimpleNamespace(total_memory=8*gib),
                           mem_get_info=lambda index: (5*gib, 8*gib))
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda, version=SimpleNamespace(hip="7.2")))
    device = hardware._torch_device()
    assert device["vendor"] == "amd" and device["backend"] == "rocm"
    assert (device["total_vram_gib"], device["free_vram_gib"]) == (8, 5)
    cuda.get_device_name = lambda index: "NVIDIA RTX"
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda, version=SimpleNamespace(hip=None)))
    assert hardware._torch_device()["backend"] == "cuda"
    assert hardware._torch_device()["vendor"] == "nvidia"


def test_directml_device_is_not_claimed_as_pytorch_model_execution(monkeypatch):
    adapter = {"name": "RX 580", "vendor": "amd", "source": "torch_directml", "index": 0}
    system = _system(monkeypatch, [], dml=[adapter])
    assert system["gpus"][0]["name"] == "RX 580"
    assert system["directml_devices"] and system["default_backend"] == "cpu"


def test_windows_adapter_name_and_vendor_without_trusting_wmi_vram(monkeypatch):
    import platform
    import subprocess
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    payload = [{"Name": "Radeon RX 580 Series", "PNPDeviceID": r"PCI\VEN_1002", "AdapterRAM": 4294967295},
               {"Name": "GeForce RTX", "PNPDeviceID": r"PCI\VEN_10DE"}]
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout=json.dumps(payload).encode()))
    adapters = hardware._windows_adapters()
    assert [item["vendor"] for item in adapters] == ["amd", "nvidia"]
    assert all("vram" not in item for item in adapters)


def test_choose_only_installed_and_fit_known_text_models():
    gib = 1024**3
    models = [{"name": "qwen3.5:4b", "size": 3*gib, "details": {"parameter_size": "4B"}},
              {"name": "qwen3.5:9b", "size": 7*gib, "details": {"parameter_size": "9B"}},
              {"name": "qwen3-embedding:4b", "size": gib},
              {"name": "unknown:latest", "size": gib},
              {"name": "qwen3:8b", "size": 5*gib, "details": {"parameter_size": "8B"}}]
    assert choose_installed_model(models, 12)["model"] == "qwen3.5:9b"
    assert choose_installed_model(models, 8)["model"] == "qwen3.5:4b"
    assert choose_installed_model(models, 3)["model"] is None
    assert choose_installed_model(models, None)["model"] is None


def test_registry_gguf_refuses_to_load_when_ram_is_too_low(tmp_path, monkeypatch):
    registry = importlib.import_module("app.ai.registry")
    monkeypatch.setattr(registry, "MODELS_DIR", tmp_path)
    spec = registry.MODEL_REGISTRY["lyrics_llm"]
    model_file = tmp_path / "lyrics_llm" / spec["file"]
    model_file.parent.mkdir()
    model_file.write_bytes(b"fake weights")
    calls = []
    llama = ModuleType("llama_cpp")
    llama.llama_supports_gpu_offload = lambda: False
    llama.Llama = lambda **kwargs: calls.append(kwargs) or object()
    monkeypatch.setitem(sys.modules, "llama_cpp", llama)
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: 6.0)
    monkeypatch.delenv("ZSMM_LLAMA_GPU_LAYERS", raising=False)
    reg = registry.ModelRegistry(registry.HardwareBudget(ram_gb=16, cpu_threads=2))
    with pytest.raises(RuntimeError, match="Insufficient or unknown free RAM"):
        reg.load("lyrics_llm")
    assert calls == []
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: 20.0)
    result = reg.load("lyrics_llm")
    assert result.device == "cpu" and calls[0]["n_gpu_layers"] == 0


def test_ollama_router_autoselects_installed_model(monkeypatch):
    from modules.llm import ollama_adaptive, providers, router
    monkeypatch.delenv("ZSMM_OLLAMA_MODEL", raising=False)
    monkeypatch.setattr(router.LLMRouter, "_preflight", lambda self: {"internet": False, "ollama": True})
    monkeypatch.setattr(ollama_adaptive, "discover_ollama_model", lambda url: {
        "model": "qwen3.5:4b", "reason": "installed", "estimated_ram_gib": 6.25})
    calls = {}
    def generate(*args, **kwargs):
        calls.update(kwargs)
        return providers.ProviderResult(True, text="тест", provider="ollama", model=kwargs["model"])
    monkeypatch.setattr(router, "call_ollama", generate)
    result = router.LLMRouter().complete("тема")
    assert calls["model"] == "qwen3.5:4b"
    assert result["model_selection"]["estimated_ram_gib"] == 6.25
    assert result["provider"] == "ollama" and not result["fallback_used"]


def test_no_fitting_model_falls_back_without_generation(monkeypatch):
    from modules.llm import ollama_adaptive, router
    monkeypatch.delenv("ZSMM_OLLAMA_MODEL", raising=False)
    monkeypatch.setattr(router.LLMRouter, "_preflight", lambda self: {"internet": False, "ollama": True})
    monkeypatch.setattr(ollama_adaptive, "discover_ollama_model", lambda url: {
        "model": None, "reason": "no known installed text model fits estimated free RAM"})
    monkeypatch.setattr(router, "call_ollama", lambda *a, **kw: pytest.fail("must not load"))
    result = router.LLMRouter().complete("тема")
    assert result["fallback_used"] and result["provider"] == "local_template"
    assert "fits estimated free RAM" in result["error"]["ollama"]


def test_main_lyrics_prefers_installed_fitting_model_to_large_gguf(monkeypatch):
    from app.ai.registry import registry
    from app.core.stages import lyrics
    from modules.llm import ollama_adaptive
    from modules.lyrics import ai
    monkeypatch.delenv("ZSMM_OLLAMA_MODEL", raising=False)
    monkeypatch.setattr(registry, "is_available", lambda role: True)
    monkeypatch.setattr(ollama_adaptive, "discover_ollama_model", lambda url: {"model": "qwen3.5:4b"})
    monkeypatch.setattr(ai, "generate_lyrics_ai", lambda *a, **kw: pytest.fail("large GGUF must be skipped"))
    captured = {}
    class Router:
        def __init__(self, **kwargs): captured.update(kwargs)
        def complete(self, *args, **kwargs):
            return {"ok": True, "text": "текст", "provider": "ollama", "fallback_used": False}
    monkeypatch.setattr(lyrics, "LLMRouter", Router)
    result = lyrics._stage_lyrics("тема", "pop")
    assert captured["ollama_model"] == "qwen3.5:4b" and result["provider"] == "ollama"


def test_texture_adapts_backend_and_unloads_model(monkeypatch, tmp_path):
    from app.core.stages import texture
    from app.core import musicgen_texture
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: 12)
    monkeypatch.setattr(hardware, "_torch_device", lambda: {
        "backend": "cuda", "free_vram_gib": 7})
    calls = {}
    def fake_generate(prompt, **kwargs):
        calls.update(kwargs)
        return {"ok": True, "path": str(tmp_path / "fake.wav")}
    monkeypatch.setattr(musicgen_texture, "generate_texture", fake_generate)
    monkeypatch.setattr(musicgen_texture, "unload_all", lambda: calls.update(unloaded=True))
    result = texture._stage_texture("prompt", tmp_path)
    assert result["hardware_preflight"]["device"] == "cuda"
    assert calls["device"] == "cuda" and calls["vram_gb"] == 6 and calls["unloaded"]
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: 3)
    monkeypatch.setattr(texture, "_texture_scaffold", lambda *a: {"ok": True, "blocked": True})
    monkeypatch.setattr(musicgen_texture, "generate_texture", lambda *a, **kw: pytest.fail("must not load"))
    result = texture._stage_texture("prompt", tmp_path)
    assert result["blocked"] and "not enough" in result["reason"]


def test_musicgen_passes_device_explicitly_and_keys_cache_by_device(monkeypatch):
    from app.core import musicgen_texture
    calls = []
    fake = ModuleType("audiocraft.models")
    fake.MusicGen = SimpleNamespace(get_pretrained=lambda model, device: calls.append((model, device)) or object())
    monkeypatch.setitem(sys.modules, "audiocraft", ModuleType("audiocraft"))
    monkeypatch.setitem(sys.modules, "audiocraft.models", fake)
    musicgen_texture._MODEL_CACHE.clear()
    try:
        musicgen_texture._load_musicgen("small", "cpu")
        musicgen_texture._load_musicgen("small", "cuda")
        assert calls == [("facebook/musicgen-small", "cpu"), ("facebook/musicgen-small", "cuda")]
    finally:
        musicgen_texture._MODEL_CACHE.clear()


def test_dxgi_memory_identification_does_not_enable_gpu_backend(monkeypatch):
    adapter = {"name": "Radeon RX 580 Series", "vendor": "amd", "source": "dxgi", "total_vram_gib": 8.0}
    system = _system(monkeypatch, [adapter])
    assert system["gpus"][0]["total_vram_gib"] == 8.0
    assert system["default_backend"] == "cpu" and not system["pytorch_device"]
    from app.core import hw_autodetect
    monkeypatch.setattr(hw_autodetect, "detect_system", lambda: system)
    profile = hw_autodetect.detect()
    assert profile["gpu"]["vram_gb"] == 8.0 and profile["gpu"]["vram_free_gb"] is None
    assert profile["mode"] == "lite" and profile["gpu"]["kind"] == "cpu"


def test_ollama_discovery_calls_local_tags_without_downloading(monkeypatch):
    from modules.llm import ollama_adaptive
    import requests
    gib = 1024 ** 3
    calls = []
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {"models": [{"name": "qwen3.5:4b", "size": 3*gib,
                                "details": {"parameter_size": "4B"}}]}
    monkeypatch.setattr(requests, "get", lambda url, **kw: calls.append((url, kw)) or Response())
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: 10.0)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: pytest.fail("must not pull or generate"))
    result = ollama_adaptive.discover_ollama_model("http://127.0.0.1:11434")
    assert result["model"] == "qwen3.5:4b"
    assert calls == [("http://127.0.0.1:11434/api/tags", {"timeout": 2})]


def test_ram_detection_survives_cpu_affinity_failure(monkeypatch):
    class Process:
        def cpu_affinity(self): raise PermissionError("not permitted")
    psutil = SimpleNamespace(virtual_memory=lambda: SimpleNamespace(total=16 * 1024**3),
                             Process=Process, cpu_count=lambda logical=False: 4)
    monkeypatch.setitem(sys.modules, "psutil", psutil)
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False)))
    found = hardware.detect_budget()
    assert found["ram_gb"] == 16 and found["cpu_threads"] >= 1
