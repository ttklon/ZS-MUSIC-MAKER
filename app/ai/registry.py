# -*- coding: utf-8 -*-
"""ZS Music Maker - app/ai/registry.py (v38)
Реестр локальных AI-моделей. Одна тяжёлая модель реестра за раз.
Аппаратные параметры определяются на текущем компьютере."""
from __future__ import annotations

import logging
import gc, os, time, threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from app.ai.model_catalog import MODEL_REGISTRY  # noqa: F401 - existing public registry contract

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "data" / "ai_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class HardwareBudget:
    vram_gb: float = 0.0
    ram_gb: float = 0.0
    cpu_threads: int = 1
    cpu_cores: int = 1
    prefer_gpu: bool = True

    @classmethod
    def from_env(cls) -> "HardwareBudget":
        from app.ai.hardware import detect_budget

        detected = detect_budget()
        return cls(
            vram_gb=float(os.environ.get("ZSMM_VRAM_GB", detected["vram_gb"])),
            ram_gb=float(os.environ.get("ZSMM_RAM_GB", detected["ram_gb"])),
            cpu_threads=int(os.environ.get("ZSMM_CPU_THREADS", detected["cpu_threads"])),
            cpu_cores=int(os.environ.get("ZSMM_CPU_CORES", detected["cpu_cores"])),
            prefer_gpu=os.environ.get("ZSMM_PREFER_GPU", "1") == "1",
        )


@dataclass
class LoadedModel:
    key: str
    handle: Any
    engine: str
    loaded_at: float
    device: str
    vram_est_gb: float


class ModelRegistry:
    def __init__(self, hw: Optional[HardwareBudget] = None):
        self.hw = hw or HardwareBudget.from_env()
        self._current: Optional[LoadedModel] = None
        self._loaders: Dict[str, Callable[[], Any]] = {}
        self._lock = threading.RLock()
        self._register_default_loaders()

    def status(self) -> Dict[str, Any]:
        cur = self._current
        return {"current": cur.key if cur else None,
                "engine": cur.engine if cur else None,
                "device": cur.device if cur else None,
                "vram_est_gb": cur.vram_est_gb if cur else 0.0,
                "budget": {"vram_gb": self.hw.vram_gb, "ram_gb": self.hw.ram_gb,
                           "cpu_threads": self.hw.cpu_threads},
                "registry": list(MODEL_REGISTRY.keys())}

    def is_available(self, key: str) -> bool:
        spec = MODEL_REGISTRY.get(key)
        if not spec:
            return False
        eng = spec["engine"]
        try:
            if eng == "llama_cpp":
                import llama_cpp  # noqa
                return (MODELS_DIR / key / spec["file"]).exists()
            if eng == "audiocraft_musicgen":
                import audiocraft  # noqa
                return True
            if eng == "xtts_v2":
                from TTS.api import TTS  # noqa
                return True
            if eng == "rvc":
                from modules.rvc_manager import is_trained
                from modules.rvc_manager.rvc_worker import require_base_assets
                if not is_trained("my_voice"):
                    return False
                external = os.environ.get("ZSMM_RVC_PYTHON", "").strip()
                if external:
                    interpreter = Path(external)
                    return interpreter.is_absolute() and interpreter.is_file()
                require_base_assets()
                return True
            if eng == "demucs":
                import demucs  # noqa
                return True
            if eng == "faster_whisper":
                from faster_whisper import WhisperModel  # noqa
                from app.ai.hardware import whisper_weights_available
                return whisper_weights_available(MODELS_DIR / key, self._whisper_device() == "cuda")
            if eng == "clap":
                import transformers  # noqa
                return True
            if eng == "essentia_or_librosa":
                import librosa  # noqa
                return True
            if eng == "diffusers":
                import diffusers  # noqa
                return True
            if eng == "matchering_plus":
                import matchering  # noqa
                return True
        except Exception:
            return False
        return False

    def load(self, key: str) -> LoadedModel:
        with self._lock:
            if self._current:
                from app.ai.llm_service import is_handle_busy
                if is_handle_busy(self._current.handle):
                    raise RuntimeError("Model inference is still running after timeout")
            if self._current and self._current.key == key:
                return self._current
            if self._current is not None:
                self.unload()
            spec = MODEL_REGISTRY.get(key)
            if not spec:
                raise KeyError(f"Unknown model role: {key}")
            loader = self._loaders.get(key)
            if not loader:
                raise RuntimeError(f"No loader registered for {key}")
            handle, device = loader()
            self._current = LoadedModel(key=key, handle=handle,
                                        engine=spec["engine"],
                                        loaded_at=time.time(), device=device,
                                        vram_est_gb=float(spec.get("vram_est_gb", 0.0)))
            return self._current

    def unload(self) -> None:
        with self._lock:
            if self._current is None:
                return
            from app.ai.llm_service import is_handle_busy
            if is_handle_busy(self._current.handle):
                logging.getLogger(__name__).warning("Deferring model unload: inference is still running")
                return
            try:
                del self._current.handle
            except Exception:
                logging.getLogger(__name__).debug("ignored exception", exc_info=True)
            self._current = None
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
            except Exception:
                logging.getLogger(__name__).debug("ignored exception", exc_info=True)

    class _UseCtx:
        def __init__(self, reg, key, unload_after):
            self.reg = reg; self.key = key
            self.unload_after = unload_after; self.model = None

        def __enter__(self):
            # Keep the registry lease for the whole inference, not just load().
            self.reg._lock.acquire()
            try:
                self.model = self.reg.load(self.key)
                return self.model
            except BaseException:
                self.reg._lock.release()
                raise

        def __exit__(self, et, ex, tb):
            try:
                if self.unload_after:
                    self.reg.unload()
            finally:
                self.reg._lock.release()
            return False

    def use(self, key: str, unload_after: bool = True):
        return ModelRegistry._UseCtx(self, key, unload_after)

    def pick_device(self, spec: Dict[str, Any]) -> str:
        """Use CUDA/ROCm only if measured *free* VRAM leaves a 1 GiB reserve."""
        pref = spec.get("device_pref", "auto")
        need = float(spec.get("vram_est_gb", 0.0))
        if pref == "cpu" or not self.hw.prefer_gpu:
            return "cpu"
        try:
            import torch
            if pref in ("cuda", "auto") and torch.cuda.is_available():
                free_bytes, _ = torch.cuda.mem_get_info()
                free_gb = min(self.hw.vram_gb, free_bytes / (1024 ** 3))
                if need <= max(0.0, free_gb - 1.0):
                    return "cuda"
        except Exception:
            logging.getLogger(__name__).debug("GPU free memory unavailable", exc_info=True)
        # Generic loaders cannot safely use torch-directml as a CUDA device.
        return "cpu"

    def _whisper_device(self) -> str:
        """CTranslate2 CUDA is not PyTorch ROCm or DirectML support."""
        if self.pick_device(MODEL_REGISTRY["asr"]) != "cuda":
            return "cpu"
        try:
            import torch
            import ctranslate2
            if getattr(getattr(torch, "version", None), "hip", None):
                return "cpu"
            return "cuda" if "float16" in ctranslate2.get_supported_compute_types("cuda") else "cpu"
        except Exception:
            logging.getLogger(__name__).debug("CTranslate2 CUDA unavailable", exc_info=True)
            return "cpu"

    def _register_default_loaders(self) -> None:
        def _llama(key):
            def _do():
                import llama_cpp
                from llama_cpp import Llama
                spec = MODEL_REGISTRY[key]
                mp = MODELS_DIR / key / spec["file"]
                mp.parent.mkdir(parents=True, exist_ok=True)
                if not mp.exists():
                    raise FileNotFoundError(
                        f"[{key}] not found at {mp}. "
                        f"Run: python tools/pull_ai_models.py --model {key}")
                device = self.pick_device(spec)
                supports_gpu = bool(getattr(llama_cpp, "llama_supports_gpu_offload", lambda: False)())
                override = os.environ.get("ZSMM_LLAMA_GPU_LAYERS")
                layers = int(override) if override is not None else (999 if device == "cuda" and supports_gpu else 0)
                if layers < -1:
                    raise ValueError("ZSMM_LLAMA_GPU_LAYERS must be -1, 0 or a positive integer")
                if layers and not supports_gpu:
                    raise RuntimeError("llama-cpp-python has no GPU offload backend; install a compatible build or use CPU")
                from app.ai.hardware import assert_llama_memory
                assert_llama_memory(key, spec, layers)
                device = "gpu_offload_requested" if layers else "cpu"
                llm = Llama(model_path=str(mp),
                            n_ctx=spec.get("context", 4096),
                            n_threads=min(self.hw.cpu_threads, 20),
                            n_gpu_layers=layers,
                            verbose=False)
                return llm, device
            return _do
        for k in ("lyrics_llm", "analysis_llm", "metadata_llm"):
            self._loaders[k] = _llama(k)

        def _musicgen(key):
            def _do():
                from audiocraft.models import MusicGen
                spec = MODEL_REGISTRY[key]
                device = self.pick_device(spec)
                repo = spec["hf_repo"]
                if device == "cpu" and spec.get("cpu_fallback"):
                    repo = spec["cpu_fallback"]
                return (MusicGen.get_pretrained(repo, device=device if device != "dml" else "cpu"), device)
            return _do
        self._loaders["music_generation"] = _musicgen("music_generation")
        self._loaders["music_stereo"] = _musicgen("music_stereo")

        def _xtts():
            from TTS.api import TTS
            spec = MODEL_REGISTRY["tts_vocal"]
            device = self.pick_device(spec)
            t = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
            if device == "cuda":
                try:
                    t.to("cuda")
                except Exception:
                    logging.getLogger(__name__).debug("ignored exception", exc_info=True)
            return t, device
        self._loaders["tts_vocal"] = _xtts

        def _rvc():
            from modules import rvc_manager
            spec = MODEL_REGISTRY["vocal_rvc"]
            return rvc_manager, self.pick_device(spec)
        self._loaders["vocal_rvc"] = _rvc

        def _demucs():
            from demucs.pretrained import get_model
            spec = MODEL_REGISTRY["stem_splitter"]
            device = self.pick_device(spec)
            m = get_model("htdemucs")
            if device == "cuda":
                try:
                    m.to("cuda")
                except Exception:
                    logging.getLogger(__name__).debug("ignored exception", exc_info=True)
            return m, device
        self._loaders["stem_splitter"] = _demucs

        def _wh():
            from faster_whisper import WhisperModel
            spec = MODEL_REGISTRY["asr"]
            device = self._whisper_device()
            from app.ai.hardware import assert_whisper_memory, whisper_model_source
            source = whisper_model_source(MODELS_DIR / "asr", device == "cuda")
            if source is None:
                raise FileNotFoundError("local Whisper weights not found")
            size, model_bin = source
            if device == "cuda" and model_bin.is_file():
                estimated_vram = max(float(spec.get("vram_est_gb", 6)), model_bin.stat().st_size / (1024 ** 3) * 1.5)
                if self.pick_device({**spec, "vram_est_gb": estimated_vram}) != "cuda":
                    device = "cpu"
            assert_whisper_memory(spec, device, model_bin)
            compute = "float16" if device == "cuda" else "int8"
            return WhisperModel(size, device=device, compute_type=compute,
                                local_files_only=True, cpu_threads=max(1, self.hw.cpu_threads)), device
        self._loaders["asr"] = _wh

        def _clap():
            from transformers import ClapModel, ClapProcessor
            spec = MODEL_REGISTRY["audio_tagger"]
            device = self.pick_device(spec)
            m = ClapModel.from_pretrained(spec["hf_repo"])
            p = ClapProcessor.from_pretrained(spec["hf_repo"])
            if device == "cuda":
                try:
                    m = m.to("cuda")
                except Exception:
                    logging.getLogger(__name__).debug("ignored exception", exc_info=True)
            return (m, p), device
        self._loaders["audio_tagger"] = _clap

        self._loaders["essentia"] = lambda: ("librosa_dsp", "cpu")

        def _sdxl():
            from diffusers import DiffusionPipeline
            import torch
            spec = MODEL_REGISTRY["cover_art"]
            device = self.pick_device(spec)
            repo = spec["hf_repo"]
            if device == "cpu" and spec.get("cpu_fallback"):
                repo = spec["cpu_fallback"]
            pipe = DiffusionPipeline.from_pretrained(
                repo, torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                variant="fp16" if device == "cuda" else None, use_safetensors=True)
            if device == "cuda":
                try:
                    pipe.to("cuda")
                    pipe.enable_attention_slicing()
                    pipe.enable_vae_tiling()
                except Exception:
                    logging.getLogger(__name__).debug("ignored exception", exc_info=True)
            return pipe, device
        self._loaders["cover_art"] = _sdxl

        def _match():
            import matchering  # noqa
            return matchering, "cpu"
        self._loaders["mastering_ai"] = _match


registry = ModelRegistry()
