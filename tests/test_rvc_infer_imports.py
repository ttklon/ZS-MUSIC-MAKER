"""RVC inference can reach the backend when a user's model is present."""
import importlib
import sys
from types import ModuleType, SimpleNamespace


def test_infer_resolves_backend_and_paths(tmp_path, monkeypatch):
    module = importlib.import_module("modules.rvc_manager.infer")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(module, "detect_backend", lambda: SimpleNamespace(kind="cpu", fork="rvc-python"))
    weights = tmp_path / "models" / "my_voice" / "my_voice.pth"
    weights.parent.mkdir(parents=True)
    weights.write_bytes(b"fake test weights")
    fake = ModuleType("rvc_python.infer")
    def infer_file(**kwargs):
        from pathlib import Path
        Path(kwargs["output_path"]).write_bytes(b"fake output" * 110)
    fake.infer_file = infer_file
    monkeypatch.setitem(sys.modules, "rvc_python", ModuleType("rvc_python"))
    monkeypatch.setitem(sys.modules, "rvc_python.infer", fake)
    output = module.infer("input.wav")
    assert output.endswith("converted.wav")
