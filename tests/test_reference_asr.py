"""Contract checks use fakes; they do not claim real Whisper inference."""
from contextlib import contextmanager
import json
import sys
import threading
from types import SimpleNamespace

import numpy as np
import pytest

from app.ai import hardware
from app.core import reference_asr
from app.core.lyric_context import MAX_REFERENCE_CHARS
from app.core.recipe import build_recipe
from app.core.stages import lyrics


class FakeRegistry:
    def __init__(self, model=None, available=True, load_error=None):
        self.model = model
        self.available = available
        self.load_error = load_error
        self.loads = 0
        self.unloads = 0

    def is_available(self, key):
        assert key == "asr"
        return self.available

    @contextmanager
    def use(self, key, unload_after=True):
        assert key == "asr" and unload_after
        self.loads += 1
        if self.load_error:
            raise RuntimeError(self.load_error)
        try:
            yield SimpleNamespace(handle=self.model, engine="test_fake", device="cpu")
        finally:
            self.unloads += 1


class FakeModel:
    def __init__(self, texts):
        self.texts = iter(texts)
        self.calls = []

    def transcribe(self, audio, **kwargs):
        self.calls.append((audio, kwargs))
        result = next(self.texts)
        if isinstance(result, Exception):
            raise result
        return iter([SimpleNamespace(text=result)]), SimpleNamespace(language="ru", language_probability=0.97)


def test_multiple_refs_are_summarized_only_and_model_unloaded(tmp_path, monkeypatch):
    files = [tmp_path / "one.wav", tmp_path / "two.wav"]
    for path in files:
        path.touch()
    monkeypatch.setattr(reference_asr, "_decode_bounded", lambda _: (np.ones(32000, dtype="float32"), False))
    sentences = ["Неповторимая длинная строка про весеннюю погоду", "Другой референс рассказывает про море и маяки"]
    model = FakeModel(sentences)
    registry = FakeRegistry(model)
    text, report = reference_asr.transcribe_references([str(p) for p in files], model_registry=registry)
    assert text == "\n".join(sentences)
    assert report["status"] == "INFERRED_UNVERIFIED" and report["accuracy_verified"] is False
    assert report["engine"] == "test_fake" and report["transcript_saved"] is False
    assert len(report["items"]) == 2 and registry.loads == registry.unloads == 1
    assert all(call[1]["language"] is None and call[1]["vad_filter"] is True for call in model.calls)
    assert all(s not in json.dumps(report, ensure_ascii=False) for s in sentences)


def test_failures_limits_and_truncated_are_observable(tmp_path, monkeypatch):
    files = [tmp_path / f"{i}.wav" for i in range(4)]
    for path in files:
        path.touch()
    monkeypatch.setattr(reference_asr, "MAX_REFERENCES", 3)
    monkeypatch.setattr(reference_asr, "_decode_bounded", lambda _: (np.ones(16000), True))
    model = FakeModel(["Яркий луч проходит через ночные окна", RuntimeError("bad decode"), "ok ok ok ok ok ok ok ok ok"])
    text, report = reference_asr.transcribe_references([str(p) for p in files], model_registry=FakeRegistry(model))
    assert text == "Яркий луч проходит через ночные окна"
    assert report["status"] == "PARTIAL"
    assert [i["status"] for i in report["items"]] == ["INFERRED_UNVERIFIED", "FAILED", "NO_USABLE_TEXT", "SKIPPED"]
    assert report["items"][0]["audio_truncated"] and report["items"][3]["reason"] == "reference limit"


def test_absent_model_low_memory_and_invalid_input_do_not_claim_success(tmp_path, monkeypatch):
    assert reference_asr.transcribe_references([], model_registry=FakeRegistry())[1]["status"] == "BLOCKED"
    unavailable = FakeRegistry(available=False)
    text, report = reference_asr.transcribe_references(["a.wav"], model_registry=unavailable)
    assert not text and report["status"] == "BLOCKED" and unavailable.loads == 0
    text, report = reference_asr.transcribe_references(["a.wav"], model_registry=FakeRegistry(load_error="RAM"))
    assert not text and report["status"] == "BLOCKED" and "RuntimeError" in report["reason"]
    text, report = reference_asr.transcribe_references([str(tmp_path / "missing.wav")], model_registry=FakeRegistry())
    assert not text and report["status"] == "NO_USABLE_TEXT" and report["items"][0]["status"] == "FAILED"
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: 8.0)
    with pytest.raises(RuntimeError, match="Insufficient"):
        hardware.assert_whisper_memory({"ram_est_gb": 8}, "cpu")
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: None)
    with pytest.raises(RuntimeError, match="unknown"):
        hardware.assert_whisper_memory({}, "cuda")
    big = tmp_path / "model.bin"
    with big.open("wb") as out:
        out.truncate(10 * 1024**3)  # sparse; budget guard considers file size
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: 10.0)
    with pytest.raises(RuntimeError):
        hardware.assert_whisper_memory({}, "cpu", big)


def test_bounded_real_pyav_decoding(tmp_path, monkeypatch):
    pytest.importorskip("av")
    import soundfile as sf
    monkeypatch.setattr(reference_asr, "MAX_SECONDS", 1)
    path = tmp_path / "test.wav"
    data = np.sin(np.arange(48000 * 3) * 0.01).astype("float32")
    sf.write(path, np.column_stack([data, data]), 48000)
    decoded, truncated = reference_asr._decode_bounded(path)
    assert truncated and decoded.shape == (16000,) and decoded.dtype == np.float32
    assert np.isfinite(decoded).all() and np.max(np.abs(decoded)) > 0.1
    path.write_bytes(b"not audio")
    with pytest.raises(Exception):
        reference_asr._decode_bounded(path)


def test_recipe_manual_text_priority_privacy_and_fallback(monkeypatch):
    source_text = "За горизонтом удивительная история про далёкое море"
    asr_calls = []
    def transcribe(paths):
        asr_calls.append(paths)
        return source_text, {"requested": True, "status": "INFERRED_UNVERIFIED"}
    monkeypatch.setattr(reference_asr, "transcribe_references", transcribe)
    prompts = []
    def generate(*args, **kwargs):
        prompts.append(kwargs["creative_context"])
        return {"ok": True, "text": "Мой новый текст", "provider": "fake_llm"}
    monkeypatch.setattr(lyrics, "_stage_lyrics", generate)
    recipe = build_recipe({"references": ["a.wav", "b.wav"], "transcribe_references": True,
                           "reference_lyrics": "Луна светит над крышами города", "trend_notes": "чай"})
    stage, _, _ = lyrics._run_lyrics_stage(recipe)
    context = stage.output["creative_context"]
    assert asr_calls == [["a.wav", "b.wav"]] and context["reference_source"] == "mixed"
    assert context["reference_asr"]["provided_to_generator"]
    assert source_text not in prompts[0] and "Луна светит над крышами города" not in prompts[0]
    assert "непроверенной" in prompts[0] and "чай" in prompts[0]
    assert source_text not in json.dumps(stage.to_dict(), ensure_ascii=False)
    recipe["user_lyrics_lines"] = ["Мой собственный текст"]
    stage, _, text = lyrics._run_lyrics_stage(recipe)
    assert text == "Мой собственный текст" and len(asr_calls) == 1
    assert stage.output["creative_context"]["reference_asr"]["status"] == "SKIPPED"
    recipe["user_lyrics_lines"] = []
    recipe["dry_run"] = True
    stage, _, _ = lyrics._run_lyrics_stage(recipe)
    assert len(asr_calls) == 1 and stage.output["creative_context"]["reference_asr"]["reason"] == "dry run"
    recipe["dry_run"] = False
    recipe["reference_lyrics"] = "а" * MAX_REFERENCE_CHARS
    stage, _, _ = lyrics._run_lyrics_stage(recipe)
    asr = stage.output["creative_context"]["reference_asr"]
    assert asr["context_truncated"] and not asr["provided_to_generator"] and stage.status.value == "FALLBACK"
    monkeypatch.setattr(reference_asr, "transcribe_references", lambda paths: ("", {"requested": True, "status": "BLOCKED"}))
    stage, _, _ = lyrics._run_lyrics_stage(recipe)
    assert stage.status.value == "FALLBACK" and stage.output["creative_context"]["reference_asr"]["status"] == "BLOCKED"


def test_rocm_never_assumed_to_be_ctranslate_cuda(monkeypatch):
    from app.ai.registry import ModelRegistry
    reg = ModelRegistry()
    monkeypatch.setattr(reg, "pick_device", lambda spec: "cuda")
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(version=SimpleNamespace(hip="6.0")))
    monkeypatch.setitem(sys.modules, "ctranslate2", SimpleNamespace(get_supported_compute_types=lambda device: {"float16"}))
    assert reg._whisper_device() == "cpu"
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(version=SimpleNamespace(hip=None)))
    assert reg._whisper_device() == "cuda"
    monkeypatch.setitem(sys.modules, "ctranslate2", SimpleNamespace(get_supported_compute_types=lambda device: set()))
    assert reg._whisper_device() == "cpu"


def test_local_whisper_loader_cannot_download_and_respects_ram(tmp_path, monkeypatch):
    import importlib
    registry_module = importlib.import_module("app.ai.registry")
    reg = registry_module.ModelRegistry()
    local = tmp_path / "asr"
    local.mkdir()
    for name in ("model.bin", "config.json", "tokenizer.json", "preprocessor_config.json"):
        (local / name).write_bytes(b"x")
    monkeypatch.setattr(registry_module, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(reg, "_whisper_device", lambda: "cpu")
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: 12)
    calls = []
    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=lambda *a, **kw: calls.append((a, kw)) or object()))
    with reg.use("asr") as loaded:
        assert loaded.device == "cpu"
    assert calls[0][0] == (str(local),) and calls[0][1]["local_files_only"] is True
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: 2)
    with pytest.raises(RuntimeError, match="Insufficient"):
        with reg.use("asr"):
            pytest.fail("must not load")
    assert len(calls) == 1


def test_registry_lease_serializes_model_use():
    from app.ai.registry import HardwareBudget, ModelRegistry
    reg = ModelRegistry(HardwareBudget(16, 0, 2, 2))
    reg._loaders["asr"] = lambda: (object(), "cpu")
    reg._loaders["lyrics_llm"] = lambda: (object(), "cpu")
    first_entered = threading.Event()
    release = threading.Event()
    second_entered = threading.Event()
    def first():
        with reg.use("asr"):
            first_entered.set()
            assert release.wait(3)
    def second():
        with reg.use("lyrics_llm"):
            second_entered.set()
    one, two = threading.Thread(target=first), threading.Thread(target=second)
    one.start()
    assert first_entered.wait(3)
    two.start()
    assert not second_entered.wait(0.1)
    release.set()
    one.join(3)
    two.join(3)
    assert not one.is_alive() and not two.is_alive() and second_entered.is_set()


def test_cache_fallback_uses_complete_other_size_and_not_partial_local_dir(tmp_path, monkeypatch):
    from pathlib import Path
    (tmp_path / "model.bin").write_bytes(b"partial local installation")
    cache = tmp_path / "cached"
    cache.mkdir()
    for name in ("model.bin", "config.json", "tokenizer.json", "preprocessor_config.json"):
        (cache / name).write_bytes(b"fake")
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(
        try_to_load_from_cache=lambda repo, name: str(cache / name) if repo.endswith("large-v3") else None))
    size, model = hardware.whisper_model_source(tmp_path, use_gpu=False)
    assert size == "large-v3" and model == Path(cache / "model.bin")
    assert hardware.whisper_weights_available(tmp_path, use_gpu=False)


def test_failed_text_generation_still_reports_asr_problem(monkeypatch):
    monkeypatch.setattr(reference_asr, "transcribe_references", lambda _: ("", {
        "requested": True, "status": "BLOCKED", "reason": "missing weights"}))
    def fail(*args, **kwargs):
        raise ValueError("generator broke")
    monkeypatch.setattr(lyrics, "_stage_lyrics", fail)
    stage, _, _ = lyrics._run_lyrics_stage(build_recipe({"transcribe_references": True}))
    assert stage.status.value == "FAILED"
    assert stage.output["creative_context"]["reference_asr"]["status"] == "BLOCKED"


def test_backend_exception_does_not_leak_transcript(tmp_path, monkeypatch):
    path = tmp_path / "a.wav"
    path.touch()
    monkeypatch.setattr(reference_asr, "_decode_bounded", lambda _: (np.ones(16000), False))
    secret = "private transcript contents"
    model = FakeModel([RuntimeError(secret)])
    _, report = reference_asr.transcribe_references([str(path)], model_registry=FakeRegistry(model))
    assert report["items"][0]["error_type"] == "RuntimeError"
    assert secret not in json.dumps(report)


def test_whitespace_reference_cannot_hide_asr_context(monkeypatch):
    monkeypatch.setattr(reference_asr, "transcribe_references", lambda _: (
        "Различные красивые слова из песни", {"requested": True, "status": "INFERRED_UNVERIFIED"}))
    monkeypatch.setattr(lyrics, "_stage_lyrics", lambda *a, **k: {"ok": True, "text": "new", "provider": "fake"})
    stage, _, _ = lyrics._run_lyrics_stage(build_recipe({"reference_lyrics": " " * MAX_REFERENCE_CHARS,
                                                           "transcribe_references": True}))
    context = stage.output["creative_context"]
    assert context["reference_source"] == "audio_asr" and context["reference_asr"]["provided_to_generator"]


def test_oversized_gpu_model_falls_back_to_cpu_before_load(tmp_path, monkeypatch):
    import importlib
    registry_module = importlib.import_module("app.ai.registry")
    reg = registry_module.ModelRegistry()
    local = tmp_path / "asr"
    local.mkdir()
    for name in ("model.bin", "config.json", "tokenizer.json", "preprocessor_config.json"):
        (local / name).write_bytes(b"x")
    with (local / "model.bin").open("wb") as out:
        out.truncate(5 * 1024**3)
    monkeypatch.setattr(registry_module, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(reg, "_whisper_device", lambda: "cuda")
    monkeypatch.setattr(reg, "pick_device", lambda spec: "cpu" if spec["vram_est_gb"] > 6 else "cuda")
    monkeypatch.setattr(hardware, "available_memory_gib", lambda: 20)
    calls = []
    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=lambda *a, **kw: calls.append(kw) or object()))
    with reg.use("asr") as model:
        assert model.device == "cpu"
    assert calls[0]["compute_type"] == "int8" and calls[0]["local_files_only"] is True
