"""Real isolated Python process with a fake RVC backend, not neural inference."""
import importlib
import json
import os
import subprocess
import sys
import venv
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf


@pytest.fixture
def fake_rvc_env(tmp_path):
    root = tmp_path / "env with spaces"
    venv.create(root, with_pip=False)
    python = root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    site = Path(subprocess.check_output([str(python), "-I", "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"], text=True).strip())
    package = site / "rvc_python"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "infer.py").write_text('''import json, os, wave, struct
class RVCInference:
    def __init__(self, **kwargs):
        self.values = dict(kwargs, numba_cache_dir=os.environ.get("NUMBA_CACHE_DIR"))
    def set_params(self, **kwargs):
        self.values.update(kwargs)
    def infer_file(self, source, target):
        with open(os.environ["FAKE_RVC_LOG"], "w") as f: json.dump(self.values, f)
        with wave.open(source, "rb") as src:
            params, frames = src.getparams(), src.readframes(src.getnframes())
        data = struct.unpack("<" + "h" * (len(frames) // 2), frames)
        with wave.open(target, "wb") as dst:
            dst.setparams(params)
            dst.writeframes(struct.pack("<" + "h" * len(data), *(int(x * .8) for x in data)))
    def unload_model(self): pass
''', encoding="utf-8")
    info = site / "rvc_python-0.1.5.dist-info"
    info.mkdir()
    (info / "METADATA").write_text("Metadata-Version: 2.1\nName: rvc-python\nVersion: 0.1.5\n", encoding="utf-8")
    base = package / "base_model"
    base.mkdir()
    for name in ("hubert_base.pt", "rmvpe.pt", "rmvpe.onnx"):
        (base / name).write_bytes(b"test-only fake asset")
    return python, base


def _paths(tmp_path):
    voice = tmp_path / "input.wav"
    sf.write(voice, .2 * np.sin(np.arange(8000) * .1), 8000)
    weights = tmp_path / "my voice.pth"
    weights.write_bytes(b"fake weights")
    index = tmp_path / "my voice.index"
    index.write_bytes(b"fake index")
    return voice, weights, index


def test_actual_isolated_process_routes_files_and_validates_output(tmp_path, monkeypatch, fake_rvc_env):
    python, _ = fake_rvc_env
    module = importlib.import_module("modules.rvc_manager.infer")
    voice, weights, index = _paths(tmp_path)
    log = tmp_path / "fake.json"
    monkeypatch.setenv("FAKE_RVC_LOG", str(log))
    monkeypatch.setenv("ZSMM_RVC_PYTHON", str(python))
    cache_base = tmp_path / 'shared numba base'
    cache_base.mkdir()
    sentinel = cache_base / 'preserve.txt'
    sentinel.write_text('keep')
    monkeypatch.setenv('NUMBA_CACHE_DIR', str(cache_base))
    monkeypatch.delenv('ZSMM_NUMBA_CACHE_ISOLATED', raising=False)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "detect_backend", lambda: pytest.fail("main torch must not be loaded"))
    monkeypatch.setattr("app.ai.hardware.available_memory_gib", lambda: 10.0)
    before = voice.read_bytes()
    output = Path(module.infer(str(voice), model_path=str(weights), index_path=str(index), pitch_shift=3))
    calls = json.loads(log.read_text(encoding="utf-8"))
    assert calls["device"] == "cpu:0" and calls["model_path"] == str(weights.resolve())
    assert calls["index_path"] == str(index.resolve()) and calls["f0up_key"] == 3
    assert Path(calls['numba_cache_dir']).parent == cache_base
    assert not Path(calls['numba_cache_dir']).exists() and sentinel.read_text() == 'keep'
    assert sf.info(output).frames == 8000 and voice.read_bytes() == before


def test_missing_auxiliary_weights_fail_before_model_is_loaded(tmp_path, monkeypatch, fake_rvc_env):
    python, base = fake_rvc_env
    (base / "rmvpe.pt").unlink()
    module = importlib.import_module("modules.rvc_manager.infer")
    voice, weights, index = _paths(tmp_path)
    old = tmp_path / "old.wav"
    old.write_bytes(b"existing result")
    log = tmp_path / "fake.json"
    monkeypatch.setenv("FAKE_RVC_LOG", str(log))
    monkeypatch.setenv("ZSMM_RVC_PYTHON", str(python))
    monkeypatch.setattr("app.ai.hardware.available_memory_gib", lambda: 10.0)
    with pytest.raises(RuntimeError, match="auxiliary weights missing"):
        module.infer(str(voice), model_path=str(weights), index_path=str(index), out_name=str(old))
    assert not log.exists() and old.read_bytes() == b"existing result"


def test_worker_timeout_is_observable_and_preserves_existing_output(tmp_path, monkeypatch):
    module = importlib.import_module("modules.rvc_manager.infer")
    voice, weights, index = _paths(tmp_path)
    old = tmp_path / "old.wav"
    old.write_bytes(b"existing result")
    monkeypatch.setenv("ZSMM_RVC_PYTHON", sys.executable)
    monkeypatch.setattr("app.ai.hardware.available_memory_gib", lambda: 10.0)
    monkeypatch.setattr(module.subprocess, "run", lambda args, **kw: (_ for _ in ()).throw(subprocess.TimeoutExpired(args, 30)))
    with pytest.raises(RuntimeError, match="timed out"):
        module.infer(str(voice), model_path=str(weights), index_path=str(index), out_name=str(old))
    assert old.read_bytes() == b"existing result" and sf.info(voice).frames == 8000


def test_invalid_explicit_interpreter_never_falls_back_in_process(tmp_path, monkeypatch):
    module = importlib.import_module("modules.rvc_manager.infer")
    voice, weights, index = _paths(tmp_path)
    monkeypatch.setenv("ZSMM_RVC_PYTHON", "relative-python")
    monkeypatch.setattr("app.ai.hardware.available_memory_gib", lambda: 10.0)
    monkeypatch.setattr(module, "require_base_assets", lambda: pytest.fail("should not fall back in process"))
    with pytest.raises(RuntimeError, match="absolute path"):
        module.infer(str(voice), model_path=str(weights), index_path=str(index))


def test_pipeline_uses_isolated_worker_and_keeps_failure_honest(tmp_path, monkeypatch, fake_rvc_env):
    from app.core.orchestrator import run_full_pipeline
    python, base = fake_rvc_env
    voice, weights, index = _paths(tmp_path)
    beat = tmp_path / "backing.wav"
    sf.write(beat, .2 * np.sin(np.arange(8000) * .07), 8000)
    monkeypatch.setenv("FAKE_RVC_LOG", str(tmp_path / "fake.json"))
    monkeypatch.setenv("ZSMM_RVC_PYTHON", str(python))
    monkeypatch.setattr("app.ai.hardware.available_memory_gib", lambda: 10.0)
    state = {"beat_engine": "user_audio", "beat_input_path": str(beat), "own_vocal_wav": str(voice),
             "use_rvc": True, "rvc_model_path": str(weights), "rvc_index_path": str(index), "use_vocal_fx": False}
    before = voice.read_bytes()
    result = run_full_pipeline("fake-rvc", state, out_root=tmp_path / "good", only={"beat", "vocal", "mix"})
    stages = {s["name"]: s for s in result["stages"]}
    assert stages["_stage_rvc"]["status"] == "OK"
    assert stages["_stage_rvc"]["output"]["execution"] == "isolated_python"
    assert stages["_stage_mix_and_sidechain"]["output"]["vocal_used"] and voice.read_bytes() == before
    (base / "hubert_base.pt").unlink()
    failed = run_full_pipeline("missing-rvc", state, out_root=tmp_path / "bad", only={"beat", "vocal", "mix"})
    stages = {s["name"]: s for s in failed["stages"]}
    assert stages["_stage_rvc"]["status"] == "BLOCKED" and "auxiliary weights missing" in stages["_stage_rvc"]["reason"]
    assert stages["_stage_mix_and_sidechain"]["output"]["vocal_used"] and voice.read_bytes() == before


def test_device_selection_uses_worker_memory_and_respects_explicit_cpu(monkeypatch):
    from types import SimpleNamespace
    from modules.rvc_manager import rvc_worker
    gpu = SimpleNamespace(is_available=lambda: True, mem_get_info=lambda _: (6 * 1024**3, 8 * 1024**3))
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=gpu))
    monkeypatch.setenv("ZSMM_RVC_DEVICE", "auto")
    assert rvc_worker.select_device() == "cuda:0"
    gpu.mem_get_info = lambda _: (3 * 1024**3, 8 * 1024**3)
    assert rvc_worker.select_device() == "cpu:0"
    gpu.mem_get_info = lambda _: (6 * 1024**3, 8 * 1024**3)
    monkeypatch.setenv("ZSMM_RVC_DEVICE", "cpu")
    assert rvc_worker.select_device() == "cpu:0"
    monkeypatch.setenv("ZSMM_RVC_DEVICE", "directml")
    with pytest.raises(RuntimeError, match="auto or cpu"):
        rvc_worker.select_device()


def test_rvc_registry_does_not_call_model_file_alone_ready(tmp_path, monkeypatch):
    from app.ai.registry import ModelRegistry
    from modules import rvc_manager
    monkeypatch.setattr(rvc_manager, "is_trained", lambda name: True)
    monkeypatch.delenv("ZSMM_RVC_PYTHON", raising=False)
    monkeypatch.setattr("modules.rvc_manager.rvc_worker.require_base_assets", lambda: (_ for _ in ()).throw(RuntimeError("missing weights")))
    registry = ModelRegistry()
    assert not registry.is_available("vocal_rvc")
    monkeypatch.setenv("ZSMM_RVC_PYTHON", "relative-python")
    assert not registry.is_available("vocal_rvc")
    monkeypatch.setenv("ZSMM_RVC_PYTHON", sys.executable)
    # Only model and interpreter file presence: never proof of dependencies/inference.
    assert registry.is_available("vocal_rvc")


def test_worker_passthrough_cannot_overwrite_previous_result(tmp_path, monkeypatch, fake_rvc_env):
    python, base = fake_rvc_env
    module = importlib.import_module("modules.rvc_manager.infer")
    voice, weights, index = _paths(tmp_path)
    (base.parent / "infer.py").write_text('''import shutil
class RVCInference:
    def __init__(self, **kwargs): pass
    def set_params(self, **kwargs): pass
    def infer_file(self, source, target): shutil.copyfile(source, target)
    def unload_model(self): pass
''', encoding="utf-8")
    old = tmp_path / "old.wav"
    old.write_bytes(b"existing result")
    monkeypatch.setenv("ZSMM_RVC_PYTHON", str(python))
    monkeypatch.setattr("app.ai.hardware.available_memory_gib", lambda: 10.0)
    with pytest.raises(RuntimeError, match="identical to input"):
        module.infer(str(voice), model_path=str(weights), index_path=str(index), out_name=str(old))
    assert old.read_bytes() == b"existing result"
