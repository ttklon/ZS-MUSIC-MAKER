# -*- coding: utf-8 -*-
"""ZS Music Maker - app/ai/registry.py (v38)
Реестр локальных AI-моделей. Одна тяжёлая модель в VRAM за раз.
Бюджет: VRAM<=12GB, RAM<=32GB, CPU 2xXeon(40 threads). Только серьёзные модели (>=8B)."""
from __future__ import annotations
import gc, os, time, threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class HardwareBudget:
    vram_gb: float = 12.0
    ram_gb: float = 32.0
    cpu_threads: int = 40
    cpu_cores: int = 20
    prefer_gpu: bool = True

    @classmethod
    def from_env(cls) -> "HardwareBudget":
        return cls(
            vram_gb=float(os.environ.get("ZSMM_VRAM_GB", "12")),
            ram_gb=float(os.environ.get("ZSMM_RAM_GB", "32")),
            cpu_threads=int(os.environ.get("ZSMM_CPU_THREADS", "40")),
            cpu_cores=int(os.environ.get("ZSMM_CPU_CORES", "20")),
            prefer_gpu=os.environ.get("ZSMM_PREFER_GPU", "1") == "1",
        )


MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "lyrics_llm": {
        "role": "Генерация текстов (сильная RU/EN LLM, никаких 1B-игрушек)",
        "engine": "llama_cpp",
        "hf_repo": "bartowski/Qwen2.5-14B-Instruct-GGUF",
        "file": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "context": 8192, "vram_est_gb": 9.5, "ram_est_gb": 12.0, "device_pref": "auto"},
    "analysis_llm": {
        "role": "Досье на артистов/треки (длинный контекст 32k)",
        "engine": "llama_cpp",
        "hf_repo": "bartowski/Qwen2.5-14B-Instruct-GGUF",
        "file": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "context": 32768, "vram_est_gb": 9.5, "ram_est_gb": 14.0, "device_pref": "auto"},
    "metadata_llm": {
        "role": "Названия/описания/хэштеги (Llama-3.1-8B)",
        "engine": "llama_cpp",
        "hf_repo": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "file": "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf",
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
        "engine": "rvc", "hf_repo": "user_supplied", "file": "models/rvc/*.pth",
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
                return (MODELS_DIR / "llm" / spec["file"]).exists()
            if eng == "audiocraft_musicgen":
                import audiocraft  # noqa
                return True
            if eng == "xtts_v2":
                from TTS.api import TTS  # noqa
                return True
            if eng == "rvc":
                d = ROOT / "models" / "rvc"
                return d.exists() and any(d.glob("*.pth"))
            if eng == "demucs":
                import demucs  # noqa
                return True
            if eng == "faster_whisper":
                from faster_whisper import WhisperModel  # noqa
                return True
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
            try:
                del self._current.handle
            except Exception:
                pass
            self._current = None
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
            except Exception:
                pass

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
        pref = spec.get("device_pref", "auto")
        need = float(spec.get("vram_est_gb", 0.0))
        if pref == "cpu":
            return "cpu"
        try:
            import torch
            if pref in ("cuda", "auto") and torch.cuda.is_available():
                if need <= self.hw.vram_gb:
                    return "cuda"
        except Exception:
            pass
        try:
            import torch_directml  # noqa
            if pref in ("dml", "auto") and need <= self.hw.vram_gb:
                return "dml"
        except Exception:
            pass
        return "cpu"

    def _register_default_loaders(self) -> None:
        def _llama(key):
            def _do():
                from llama_cpp import Llama
                spec = MODEL_REGISTRY[key]
                mp = MODELS_DIR / "llm" / spec["file"]
                mp.parent.mkdir(parents=True, exist_ok=True)
                if not mp.exists():
                    raise FileNotFoundError(
                        f"[{key}] not found at {mp}. "
                        f"Run: python tools/pull_ai_models.py --model {key}")
                device = self.pick_device(spec)
                llm = Llama(model_path=str(mp),
                            n_ctx=spec.get("context", 4096),
                            n_threads=min(self.hw.cpu_threads, 20),
                            n_gpu_layers=999 if device in ("cuda", "dml") else 0,
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
                    pass
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
                    pass
            return m, device
        self._loaders["stem_splitter"] = _demucs

        def _wh():
            from faster_whisper import WhisperModel
            spec = MODEL_REGISTRY["asr"]
            device = self.pick_device(spec)
            size = "large-v3" if device != "cpu" else "medium"
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
                    pass
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
                    pass
            return pipe, device
        self._loaders["cover_art"] = _sdxl

        def _match():
            import matchering  # noqa
            return matchering, "cpu"
        self._loaders["mastering_ai"] = _match


registry = ModelRegistry()
