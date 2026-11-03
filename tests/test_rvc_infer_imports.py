"""Exercise rvc-python's public class contract with a fake backend, not AI inference."""
import importlib
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest
import soundfile as sf


def test_infer_uses_public_rvc_python_class_and_validates_output(tmp_path, monkeypatch):
    module = importlib.import_module("modules.rvc_manager.infer")
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
