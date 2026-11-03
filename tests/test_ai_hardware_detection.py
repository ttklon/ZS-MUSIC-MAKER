"""Hardware budgets must be detected, not presented as the developer's GPU."""
from app.ai.hardware import detect_budget
from app.ai.registry import HardwareBudget


def test_detect_budget_returns_nonnegative_measurements():
    found = detect_budget()
    assert found["ram_gb"] >= 0 and found["vram_gb"] >= 0
    assert found["cpu_threads"] >= 1 and found["cpu_cores"] >= 1
    assert found["cpu_cores"] <= found["cpu_threads"]


def test_explicit_hardware_overrides_take_precedence(monkeypatch):
    monkeypatch.setenv("ZSMM_RAM_GB", "7")
    monkeypatch.setenv("ZSMM_VRAM_GB", "0")
    monkeypatch.setenv("ZSMM_CPU_THREADS", "2")
    monkeypatch.setenv("ZSMM_CPU_CORES", "1")
    budget = HardwareBudget.from_env()
    assert (budget.ram_gb, budget.vram_gb, budget.cpu_threads, budget.cpu_cores) == (7, 0, 2, 1)


def test_whisper_requires_all_weight_assets(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace
    from app.ai.hardware import whisper_weights_available

    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(try_to_load_from_cache=lambda *args: None))
    (tmp_path / "model.bin").write_bytes(b"not a real model")
    assert whisper_weights_available(tmp_path, False) is False
    for name in ("config.json", "tokenizer.json", "preprocessor_config.json"):
        (tmp_path / name).write_text("{}")
    assert whisper_weights_available(tmp_path, False) is True  # presence, not inference


def test_registry_asr_does_not_confuse_runtime_with_weights(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace
    import importlib
    registry_module = importlib.import_module("app.ai.registry")

    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=object))
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(try_to_load_from_cache=lambda *args: None))
    monkeypatch.setattr(registry_module, "MODELS_DIR", tmp_path)
    model_registry = registry_module.ModelRegistry()
    assert model_registry.is_available("asr") is False
    folder = tmp_path / "asr"
    folder.mkdir()
    for name in ("model.bin", "config.json", "tokenizer.json", "preprocessor_config.json"):
        (folder / name).write_bytes(b"test only")
    assert model_registry.is_available("asr") is True
