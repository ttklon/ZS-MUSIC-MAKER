"""Exercise rvc-python's public class contract with a fake backend, not AI inference."""
import importlib
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest
import soundfile as sf


def test_infer_uses_public_rvc_python_class_and_validates_output(tmp_path, monkeypatch):
    module = importlib.import_module("modules.rvc_manager.infer")
    monkeypatch.setattr("app.ai.hardware.available_memory_gib", lambda: 12.0)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(module, "detect_backend", lambda: SimpleNamespace(kind="directml", fork="applio"))
    weights = tmp_path / "models" / "my_voice" / "my_voice.pth"
    weights.parent.mkdir(parents=True)
    weights.write_bytes(b"fake test weights")
    source = tmp_path / "voice.wav"
    waveform = 0.2 * np.sin(np.arange(8000, dtype=np.float32) * 0.1)
    sf.write(source, waveform, 8000)
    fake = ModuleType("rvc_python.infer")
    calls = {}
    class RVCInference:
        def __init__(self, **kwargs): calls.update(kwargs)
        def set_params(self, **kwargs): calls.update(kwargs)
        def infer_file(self, input_path, output_path): sf.write(output_path, waveform, 8000)
        def unload_model(self): calls["unloaded"] = True
    fake.RVCInference = RVCInference
    monkeypatch.setitem(sys.modules, "rvc_python", ModuleType("rvc_python"))
    monkeypatch.setitem(sys.modules, "rvc_python.infer", fake)
    output = module.infer(str(source), pitch_shift=2)
    assert output.endswith("converted.wav") and sf.info(output).duration == 1
    assert calls["model_path"] == str(weights) and calls["device"] == "cpu:0"
    assert calls["f0up_key"] == 2 and calls["unloaded"] is True

    class Broken(RVCInference):
        def infer_file(self, input_path, output_path): pass
    fake.RVCInference = Broken
    with pytest.raises(RuntimeError, match="validation failed"):
        module.infer(str(source), out_name="converted.wav")
    assert sf.info(output).duration == 1  # old file was not mistaken for a new result


def test_training_not_claimed_without_verified_backend():
    from modules.voice_convert import train_rvc_model
    result = train_rvc_model()
    assert result["ok"] is False and result["job_started"] is False
    assert "не подключено" in result["reason"]


def test_rocm_detected_as_rocm_not_nvidia(monkeypatch):
    import sys
    from types import SimpleNamespace
    from modules.rvc_manager.backend import detect_backend
    cuda = SimpleNamespace(is_available=lambda: True, get_device_name=lambda _: "AMD Radeon",
                           get_device_properties=lambda _: SimpleNamespace(total_memory=8 * 1024**3))
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda, version=SimpleNamespace(hip="7.2")))
    result = detect_backend()
    assert result.kind == "rocm" and result.vram_gb == 8.0 and result.fork == "rvc-python"


def test_explicit_model_and_index_are_used_and_missing_index_is_not_ignored(tmp_path, monkeypatch):
    module = importlib.import_module("modules.rvc_manager.infer")
    monkeypatch.setattr("app.ai.hardware.available_memory_gib", lambda: 12.0)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "detect_backend", lambda: SimpleNamespace(kind="cpu"))
    source = tmp_path / "recording.wav"
    waveform = 0.2 * np.sin(np.arange(8000, dtype=np.float32) * 0.1)
    sf.write(source, waveform, 8000)
    model = tmp_path / "voice.pth"
    model.write_bytes(b"test weights")
    index = tmp_path / "voice.index"
    index.write_bytes(b"test index")
    fake = ModuleType("rvc_python.infer")
    calls = {}
    class RVCInference:
        def __init__(self, **kwargs): calls.update(kwargs)
        def set_params(self, **kwargs): pass
        def infer_file(self, input_path, output_path): sf.write(output_path, waveform, 8000)
        def unload_model(self): pass
    fake.RVCInference = RVCInference
    monkeypatch.setitem(sys.modules, "rvc_python", ModuleType("rvc_python"))
    monkeypatch.setitem(sys.modules, "rvc_python.infer", fake)
    result = module.infer(str(source), model_path=str(model), index_path=str(index))
    assert calls["model_path"] == str(model) and calls["index_path"] == str(index)
    assert sf.info(result).frames == len(waveform)
    index.unlink()
    with pytest.raises(RuntimeError, match=r"\.index is not available"):
        module.infer(str(source), model_path=str(model), index_path=str(index))
    with pytest.raises(ValueError, match="must not overwrite"):
        module.infer(str(source), model_path=str(model), out_name=str(source))
    assert sf.info(source).frames == len(waveform)


def test_explicit_model_and_index_reach_vocal_chain(tmp_path, monkeypatch):
    from app.core.recipe import build_recipe
    from app.core.stages import vocal_chain
    from modules import rvc_manager
    voice = tmp_path / "recording.wav"
    sf.write(voice, np.sin(np.arange(8000) * .1) * .2, 8000)
    model = tmp_path / "custom.pth"
    model.write_bytes(b"fake")
    index = tmp_path / "custom.index"
    index.write_bytes(b"fake")
    captured = {}
    def infer(*args, **kwargs):
        captured.update(kwargs)
        return str(voice)
    monkeypatch.setattr(rvc_manager, "infer", infer)
    monkeypatch.setattr(vocal_chain, "_stage_vocal_fx", lambda path, *a, **kw: {"ok": True, "path": path})
    recipe = build_recipe({"own_vocal_wav": str(voice), "use_rvc": True, "rvc_model_path": str(model),
                           "rvc_index_path": str(index), "rvc_pitch_shift": 4})
    stages, result, _ = vocal_chain._run_vocal_chain(recipe, "слова", tmp_path)
    assert stages[1].status.value == "OK" and result == str(voice)
    assert captured["model_path"] == str(model) and captured["index_path"] == str(index)
    assert captured["pitch_shift"] == 4


def test_missing_explicit_index_reports_blocked_and_preserves_recording(tmp_path, monkeypatch):
    from app.core.recipe import build_recipe
    from app.core.stages import vocal_chain
    module = importlib.import_module("modules.rvc_manager.infer")
    monkeypatch.setattr("app.ai.hardware.available_memory_gib", lambda: 12.0)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    voice = tmp_path / "recording.wav"
    sf.write(voice, np.sin(np.arange(8000) * .1) * .2, 8000)
    model = tmp_path / "custom.pth"
    model.write_bytes(b"fake")
    monkeypatch.setattr(vocal_chain, "_stage_vocal_fx", lambda path, *a, **kw: {"ok": True, "path": path})
    recipe = build_recipe({"own_vocal_wav": str(voice), "use_rvc": True, "rvc_model_path": str(model),
                           "rvc_index_path": str(tmp_path / "missing.index")})
    stages, output, _ = vocal_chain._run_vocal_chain(recipe, "слова", tmp_path)
    assert stages[1].status.value == "BLOCKED"
    assert ".index is not available" in stages[1].reason
    assert output == str(voice)


def test_rvc_selects_gpu_only_with_measured_headroom(tmp_path, monkeypatch):
    module = importlib.import_module("modules.rvc_manager.infer")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr("app.ai.hardware.available_memory_gib", lambda: 8.0)
    model = tmp_path / "voice.pth"
    model.write_bytes(b"test")
    source = tmp_path / "source.wav"
    waveform = 0.2 * np.sin(np.arange(8000, dtype=np.float32) * .1)
    sf.write(source, waveform, 8000)
    calls = []
    fake = ModuleType("rvc_python.infer")
    class RVCInference:
        def __init__(self, **kwargs): calls.append(kwargs["device"])
        def set_params(self, **kwargs): pass
        def infer_file(self, input_path, output_path): sf.write(output_path, waveform, 8000)
        def unload_model(self): pass
    fake.RVCInference = RVCInference
    monkeypatch.setitem(sys.modules, "rvc_python", ModuleType("rvc_python"))
    monkeypatch.setitem(sys.modules, "rvc_python.infer", fake)
    monkeypatch.setattr(module, "detect_backend", lambda: SimpleNamespace(kind="cuda", vram_free_gb=5))
    module.infer(str(source), model_path=str(model))
    monkeypatch.setattr(module, "detect_backend", lambda: SimpleNamespace(kind="cuda", vram_free_gb=2))
    module.infer(str(source), model_path=str(model))
    assert calls == ["cuda:0", "cpu:0"]
    monkeypatch.setattr("app.ai.hardware.available_memory_gib", lambda: 3.0)
    with pytest.raises(RuntimeError, match="free RAM"):
        module.infer(str(source), model_path=str(model))
    assert calls == ["cuda:0", "cpu:0"]
