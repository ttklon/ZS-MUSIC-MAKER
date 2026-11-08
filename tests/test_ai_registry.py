# -*- coding: utf-8 -*-
"""app/ai/registry.py: реестр моделей — аренда, выгрузка, выбор устройства.

Ни одна модель не загружается по-настоящему: загрузчики подменены. Проверяется
то, что можно проверить честно: взаимное исключение моделей, запрет выгрузки
во время инференса, бюджет VRAM, отказ вместо молчаливой подмены устройства.
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

from app.ai import llm_service
from app.ai.model_catalog import MODEL_REGISTRY
from app.ai.registry import HardwareBudget, LoadedModel, ModelRegistry

# `from app.ai import registry` отдаёт объект-синглтон, а не модуль: нужен
# именно модуль, чтобы подменять MODELS_DIR и ensure_local_weights.
reg_mod = importlib.import_module("app.ai.registry")


@pytest.fixture
def registry(monkeypatch):
    """Реестр с фиктивным бюджетом и подменёнными загрузчиками.

    Загрузчики подменяются после конструирования: `_register_default_loaders`
    при создании объекта трогает веса и железо, а здесь проверяется логика
    аренды, а не загрузка моделей.
    """
    reg = ModelRegistry(HardwareBudget(vram_gb=8.0, ram_gb=16.0, cpu_threads=4, cpu_cores=4))
    reg._loaders = {key: (lambda k=key: ({"handle": k}, "cpu")) for key in MODEL_REGISTRY}
    return reg


class TestStatus:
    def test_empty_registry_reports_nothing_loaded(self, registry) -> None:
        status = registry.status()

        assert status["current"] is None
        assert status["engine"] is None
        assert status["budget"]["vram_gb"] == 8.0
        assert set(status["registry"]) == set(MODEL_REGISTRY)

    def test_unknown_role_is_not_available(self, registry) -> None:
        assert registry.is_available("нет-такой-роли") is False

    def test_role_without_engine_is_not_available(self, registry, monkeypatch) -> None:
        monkeypatch.setitem(MODEL_REGISTRY, "fake_role", {"engine": "нет-движка", "file": ""})

        assert registry.is_available("fake_role") is False

    def test_essentia_role_follows_librosa(self, registry) -> None:
        # `essentia_or_librosa` доступна, если есть librosa (она есть в окружении)
        assert registry.is_available("essentia") is True

    def test_missing_dependency_means_unavailable(self, registry, monkeypatch) -> None:
        monkeypatch.setitem(MODEL_REGISTRY, "fake_demucs", {"engine": "demucs", "file": ""})
        monkeypatch.setitem(sys.modules, "demucs", None)

        assert registry.is_available("fake_demucs") is False


class TestLoadUnload:
    def test_load_registers_current_model(self, registry) -> None:
        loaded = registry.load("essentia")

        assert isinstance(loaded, LoadedModel)
        assert loaded.key == "essentia"
        assert registry.status()["current"] == "essentia"

    def test_second_load_replaces_first(self, registry) -> None:
        registry.load("essentia")
        first = registry._current

        registry.load("music_generation")

        assert first is not registry._current
        assert registry._current.key == "music_generation"

    def test_same_key_is_not_reloaded(self, registry) -> None:
        first = registry.load("essentia")
        second = registry.load("essentia")

        assert first is second

    def test_unknown_role_raises(self, registry) -> None:
        with pytest.raises(KeyError, match="Unknown model role"):
            registry.load("нет-роли")

    def test_role_without_loader_raises(self, registry) -> None:
        registry._loaders.pop("essentia")

        with pytest.raises(RuntimeError, match="No loader registered"):
            registry.load("essentia")

    def test_unload_clears_current(self, registry) -> None:
        registry.load("essentia")

        registry.unload()

        assert registry._current is None
        assert registry.status()["current"] is None

    def test_unload_with_nothing_loaded_is_noop(self, registry) -> None:
        registry.unload()

        assert registry._current is None

    def test_busy_handle_is_not_unloaded(self, registry) -> None:
        registry.load("essentia")
        busy = registry._current

        # занятость handle — реальный механизм llm_service, не заглушка
        llm_service._BUSY_HANDLES.add(id(busy.handle))
        try:
            registry.unload()
            assert registry._current is busy
        finally:
            llm_service._BUSY_HANDLES.discard(id(busy.handle))


class TestUse:
    def test_use_yields_loaded_model_and_releases(self, registry) -> None:
        with registry.use("essentia") as model:
            assert model.key == "essentia"
            assert registry._current is model

        assert registry._current is None

    def test_use_can_keep_model_loaded(self, registry) -> None:
        with registry.use("essentia", unload_after=False) as model:
            assert model.key == "essentia"

        assert registry._current is not None

    def test_use_of_unknown_role_releases_lock(self, registry) -> None:
        with pytest.raises(KeyError):
            with registry.use("нет-роли"):
                pass

        # после исключения блокировка не должна остаться захваченной
        assert registry._lock.acquire(blocking=False) is True
        registry._lock.release()

    def test_use_unloads_after_exception_inside_block(self, registry) -> None:
        with pytest.raises(ValueError):
            with registry.use("essentia"):
                raise ValueError("сбой внутри инференса")

        assert registry._current is None


class TestDeviceSelection:
    def test_cpu_preference_wins(self, registry) -> None:
        assert registry.pick_device({"device_pref": "cpu", "vram_est_gb": 0.1}) == "cpu"

    def test_no_gpu_preference_wins(self, registry) -> None:
        registry.hw.prefer_gpu = False

        assert registry.pick_device({"device_pref": "auto", "vram_est_gb": 0.1}) == "cpu"

    def test_without_torch_cuda_it_is_cpu(self, registry) -> None:
        assert registry.pick_device({"device_pref": "cuda", "vram_est_gb": 0.1}) == "cpu"

    def test_cuda_reserve_is_respected(self, registry, monkeypatch) -> None:
        fake_torch = types.ModuleType("torch")
        fake_cuda = types.SimpleNamespace(
            is_available=lambda: True,
            # свободно 1.2 ГБ, модели нужно 0.5 → резерв 1 ГБ не оставляет места
            mem_get_info=lambda: (int(1.2 * 1024 ** 3), int(8 * 1024 ** 3)),
        )
        fake_torch.cuda = fake_cuda
        monkeypatch.setitem(sys.modules, "torch", fake_torch)

        assert registry.pick_device({"device_pref": "cuda", "vram_est_gb": 0.5}) == "cpu"

    def test_cuda_is_used_when_memory_fits(self, registry, monkeypatch) -> None:
        fake_torch = types.ModuleType("torch")
        fake_torch.cuda = types.SimpleNamespace(
            is_available=lambda: True,
            mem_get_info=lambda: (int(6 * 1024 ** 3), int(8 * 1024 ** 3)),
        )
        monkeypatch.setitem(sys.modules, "torch", fake_torch)

        assert registry.pick_device({"device_pref": "auto", "vram_est_gb": 2.0}) == "cuda"

    def test_whisper_stays_on_cpu_without_cuda(self, registry) -> None:
        assert registry._whisper_device() == "cpu"


class TestLoaders:
    def test_default_loaders_cover_every_catalogue_role(self) -> None:
        real = ModelRegistry(HardwareBudget(vram_gb=0.0, ram_gb=8.0, cpu_threads=2, cpu_cores=2))

        missing = [key for key in MODEL_REGISTRY if key not in real._loaders]

        assert missing == [], f"роли без загрузчика: {missing}"

    def test_essentia_loader_is_a_pure_dsp_marker(self) -> None:
        real = ModelRegistry(HardwareBudget(vram_gb=0.0, ram_gb=8.0, cpu_threads=2, cpu_cores=2))

        handle, device = real._loaders["essentia"]()

        assert handle == "librosa_dsp" and device == "cpu"

    def test_musicgen_refuses_without_local_weights(self, tmp_path, monkeypatch) -> None:
        real = ModelRegistry(HardwareBudget(vram_gb=0.0, ram_gb=8.0, cpu_threads=2, cpu_cores=2))
        monkeypatch.setattr(reg_mod, "MODELS_DIR", tmp_path / "models")
        monkeypatch.setattr(reg_mod, "ensure_local_weights", _refuse_weights)

        with pytest.raises(FileNotFoundError, match="весов нет"):
            real._loaders["music_generation"]()

    def test_xtts_refuses_without_local_weights(self, tmp_path, monkeypatch) -> None:
        real = ModelRegistry(HardwareBudget(vram_gb=0.0, ram_gb=8.0, cpu_threads=2, cpu_cores=2))
        monkeypatch.setattr(reg_mod, "ensure_local_weights", _refuse_weights)

        with pytest.raises(FileNotFoundError, match="весов нет"):
            real._loaders["tts_vocal"]()

    def test_demucs_refuses_without_local_weights(self, monkeypatch) -> None:
        real = ModelRegistry(HardwareBudget(vram_gb=0.0, ram_gb=8.0, cpu_threads=2, cpu_cores=2))
        monkeypatch.setattr(reg_mod, "ensure_local_weights", _refuse_weights)

        with pytest.raises(FileNotFoundError, match="весов нет"):
            real._loaders["stem_splitter"]()

    def test_clap_refuses_without_local_weights(self, monkeypatch) -> None:
        real = ModelRegistry(HardwareBudget(vram_gb=0.0, ram_gb=8.0, cpu_threads=2, cpu_cores=2))
        monkeypatch.setattr(reg_mod, "ensure_local_weights", _refuse_weights)

        with pytest.raises(FileNotFoundError, match="весов нет"):
            real._loaders["audio_tagger"]()

    def test_llama_reports_missing_weight_file_with_hint(self, tmp_path, monkeypatch) -> None:
        real = ModelRegistry(HardwareBudget(vram_gb=0.0, ram_gb=8.0, cpu_threads=2, cpu_cores=2))
        monkeypatch.setattr(reg_mod, "MODELS_DIR", tmp_path)
        fake = types.ModuleType("llama_cpp")
        fake.Llama = object
        fake.llama_supports_gpu_offload = lambda: False
        monkeypatch.setitem(sys.modules, "llama_cpp", fake)

        with pytest.raises(FileNotFoundError, match="pull_ai_models"):
            real._loaders["analysis_llm"]()

    def test_hardware_budget_reads_environment(self, monkeypatch) -> None:
        monkeypatch.setenv("ZSMM_VRAM_GB", "12")
        monkeypatch.setenv("ZSMM_RAM_GB", "32")
        monkeypatch.setenv("ZSMM_CPU_THREADS", "8")
        monkeypatch.setenv("ZSMM_CPU_CORES", "8")
        monkeypatch.setenv("ZSMM_PREFER_GPU", "0")

        budget = HardwareBudget.from_env()

        assert (budget.vram_gb, budget.ram_gb) == (12.0, 32.0)
        assert (budget.cpu_threads, budget.cpu_cores) == (8, 8)
        assert budget.prefer_gpu is False


def _refuse_weights(role, models_dir):
    raise FileNotFoundError(f"весов нет для {role}")
