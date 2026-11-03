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


MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "lyrics_llm": {
        "role": "Генерация текстов (Qwen2.5-14B GGUF; требуется достаточно памяти)",
        "engine": "llama_cpp",
        "hf_repo": "bartowski/Qwen2.5-14B-Instruct-GGUF",
        "file": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "sha256": "e47ad95dad6ff848b431053b375adb5d39321290ea2c638682577dafca87c008",
        "expected_size_bytes": 8988110976,
        "context": 8192, "vram_est_gb": 9.5, "ram_est_gb": 12.0, "device_pref": "auto"},
    "analysis_llm": {
        "role": "Досье на артистов/треки (длинный контекст 32k)",
        "engine": "llama_cpp",
        "hf_repo": "bartowski/Qwen2.5-14B-Instruct-GGUF",
        "file": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "sha256": "e47ad95dad6ff848b431053b375adb5d39321290ea2c638682577dafca87c008",
        "expected_size_bytes": 8988110976,
        "context": 32768, "vram_est_gb": 9.5, "ram_est_gb": 14.0, "device_pref": "auto"},
    "metadata_llm": {
        "role": "Названия/описания/хэштеги (Llama-3.1-8B)",
        "engine": "llama_cpp",
        "hf_repo": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "file": "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf",
        "sha256": "14e10feba0c82a55da198dcd69d137206ad22d116a809926d27fa5f2398c69c7",
        "expected_size_bytes": 5732992416,
        "context": 8192, "vram_est_gb": 7.0, "ram_est_gb": 10.0, "device_pref": "auto"},
    "music_generation": {
        "role": "Генерация бита (MusicGen-large 3.3B)",
        "engine": "audiocraft_musicgen", "hf_repo": "facebook/musicgen-large",
        "file": "musicgen-large", "vram_est_gb": 11.0, "ram_est_gb": 14.0,
        "device_pref": "cuda", "cpu_fallback": "facebook/musicgen-medium"},
    "music_stereo": {
        "role": "Стерео-текстуры (переходы, интро, пэды)",
        "engine": "audiocraft_musicgen", "hf_repo": "facebook/musicgen-stereo-medium",
        "file": "musicgen-stereo-medium", "vram_est_gb": 8.0, "ram_est_gb": 10.0,
        "device_pref": "auto"},
    "tts_vocal": {
        "role": "Основной вокал (XTTS-v2, клонирование голоса)",
        "engine": "xtts_v2", "hf_repo": "coqui/XTTS-v2", "file": "XTTS-v2",
        "vram_est_gb": 4.0, "ram_est_gb": 6.0, "device_pref": "cuda"},
    "vocal_rvc": {
        "role": "Voice-conversion под голос артиста (.pth кладёт юзер)",
        "engine": "rvc", "hf_repo": "user_supplied", "file": "data/ai_models/vocal_rvc/*.pth",
        "vram_est_gb": 3.0, "ram_est_gb": 4.0, "device_pref": "cuda"},
    "stem_splitter": {
        "role": "Демиксинг референса (Demucs htdemucs)",
        "engine": "demucs", "hf_repo": "facebook/demucs-htdemucs",
        "file": "htdemucs.th", "vram_est_gb": 6.0, "ram_est_gb": 10.0,
        "device_pref": "cuda"},
    "asr": {
        "role": "Распознавание речи референса (faster-whisper large-v3)",
        "engine": "faster_whisper", "hf_repo": "Systran/faster-whisper-large-v3",
        "file": "faster-whisper-large-v3", "vram_est_gb": 6.0, "ram_est_gb": 8.0,
        "device_pref": "cuda", "cpu_fallback": "Systran/faster-whisper-medium"},
    "audio_tagger": {
        "role": "Автотегирование (CLAP HTSAT-fused)",
        "engine": "clap", "hf_repo": "laion/clap-htsat-fused",
        "file": "clap-htsat-fused", "vram_est_gb": 2.5, "ram_est_gb": 4.0,
        "device_pref": "auto"},
    "essentia": {
        "role": "BPM/key/loudness (librosa DSP)",
        "engine": "essentia_or_librosa", "hf_repo": "", "file": "",
        "vram_est_gb": 0.0, "ram_est_gb": 2.0, "device_pref": "cpu"},
    "cover_art": {
        "role": "Обложка (SDXL Base 1.0 fp16)",
        "engine": "diffusers", "hf_repo": "stabilityai/stable-diffusion-xl-base-1.0",
        "file": "sdxl-base-1.0", "vram_est_gb": 10.0, "ram_est_gb": 8.0,
        "device_pref": "cuda", "cpu_fallback": "stabilityai/sd-turbo"},
    "mastering_ai": {
        "role": "AI-мастеринг (matchering под референс)",
        "engine": "matchering_plus", "hf_repo": "", "file": "",
        "vram_est_gb": 0.0, "ram_est_gb": 4.0, "device_pref": "cpu"},
}


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
                return is_trained("my_voice")
            if eng == "demucs":
                import demucs  # noqa
                return True
            if eng == "faster_whisper":
                from faster_whisper import WhisperModel  # noqa
                from app.ai.hardware import whisper_weights_available
                return whisper_weights_available(MODELS_DIR / key, self.pick_device(spec) != "cpu")
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
            self.model = self.reg.load(self.key)
            return self.model

        def __exit__(self, et, ex, tb):
            if self.unload_after:
                self.reg.unload()
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
            device = self.pick_device(spec)
            size = "large-v3" if device != "cpu" else "medium"
            local_dir = MODELS_DIR / "asr"
            if all((local_dir / name).is_file() for name in
                   ("model.bin", "config.json", "tokenizer.json", "preprocessor_config.json")):
                size = str(local_dir)
            compute = "float16" if device == "cuda" else "int8"
            return WhisperModel(size, device=device if device != "dml" else "cpu",
                                compute_type=compute), device
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
