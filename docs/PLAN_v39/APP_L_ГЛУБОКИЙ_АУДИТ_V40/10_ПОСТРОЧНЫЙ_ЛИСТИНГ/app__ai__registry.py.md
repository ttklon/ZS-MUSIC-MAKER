# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/ai/registry.py`

**Всего строк:** 365

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 184 | 50.4 |
| return | 36 | 9.9 |
| blank | 31 | 8.5 |
| branch | 29 | 7.9 |
| import | 27 | 7.4 |
| def | 23 | 6.3 |
| try_block | 18 | 4.9 |
| class | 4 | 1.1 |
| docstring | 3 | 0.8 |
| decorator | 3 | 0.8 |
| raise | 3 | 0.8 |
| stmt | 2 | 0.5 |
| comment | 1 | 0.3 |
| loop | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - app/ai/registry.py (v38)
    3 [docstring ] Реестр локальных AI-моделей. Одна тяжёлая модель в VRAM за раз.
    4 [docstring ] Бюджет: VRAM<=12GB, RAM<=32GB, CPU 2xXeon(40 threads). Только серьёзные модели (>=8B)."""
    5 [import    ] from __future__ import annotations
    6 [import    ] import gc, os, time, threading
    7 [import    ] from dataclasses import dataclass
    8 [import    ] from pathlib import Path
    9 [import    ] from typing import Any, Callable, Dict, Optional
   10 [blank     ] 
   11 [code      ] ROOT = Path(__file__).resolve().parents[2]
   12 [code      ] MODELS_DIR = ROOT / "models"
   13 [code      ] MODELS_DIR.mkdir(parents=True, exist_ok=True)
   14 [blank     ] 
   15 [blank     ] 
   16 [decorator ] @dataclass
   17 [class     ] class HardwareBudget:
   18 [code      ]     vram_gb: float = 12.0
   19 [code      ]     ram_gb: float = 32.0
   20 [code      ]     cpu_threads: int = 40
   21 [code      ]     cpu_cores: int = 20
   22 [code      ]     prefer_gpu: bool = True
   23 [blank     ] 
   24 [decorator ]     @classmethod
   25 [def       ]     def from_env(cls) -> "HardwareBudget":
   26 [return    ]         return cls(
   27 [code      ]             vram_gb=float(os.environ.get("ZSMM_VRAM_GB", "12")),
   28 [code      ]             ram_gb=float(os.environ.get("ZSMM_RAM_GB", "32")),
   29 [code      ]             cpu_threads=int(os.environ.get("ZSMM_CPU_THREADS", "40")),
   30 [code      ]             cpu_cores=int(os.environ.get("ZSMM_CPU_CORES", "20")),
   31 [code      ]             prefer_gpu=os.environ.get("ZSMM_PREFER_GPU", "1") == "1",
   32 [code      ]         )
   33 [blank     ] 
   34 [blank     ] 
   35 [code      ] MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
   36 [code      ]     "lyrics_llm": {
   37 [code      ]         "role": "Генерация текстов (сильная RU/EN LLM, никаких 1B-игрушек)",
   38 [code      ]         "engine": "llama_cpp",
   39 [code      ]         "hf_repo": "bartowski/Qwen2.5-14B-Instruct-GGUF",
   40 [code      ]         "file": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
   41 [code      ]         "context": 8192, "vram_est_gb": 9.5, "ram_est_gb": 12.0, "device_pref": "auto"},
   42 [code      ]     "analysis_llm": {
   43 [code      ]         "role": "Досье на артистов/треки (длинный контекст 32k)",
   44 [code      ]         "engine": "llama_cpp",
   45 [code      ]         "hf_repo": "bartowski/Qwen2.5-14B-Instruct-GGUF",
   46 [code      ]         "file": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
   47 [code      ]         "context": 32768, "vram_est_gb": 9.5, "ram_est_gb": 14.0, "device_pref": "auto"},
   48 [code      ]     "metadata_llm": {
   49 [code      ]         "role": "Названия/описания/хэштеги (Llama-3.1-8B)",
   50 [code      ]         "engine": "llama_cpp",
   51 [code      ]         "hf_repo": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
   52 [code      ]         "file": "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf",
   53 [code      ]         "context": 8192, "vram_est_gb": 7.0, "ram_est_gb": 10.0, "device_pref": "auto"},
   54 [code      ]     "music_generation": {
   55 [code      ]         "role": "Генерация бита (MusicGen-large 3.3B)",
   56 [code      ]         "engine": "audiocraft_musicgen", "hf_repo": "facebook/musicgen-large",
   57 [code      ]         "file": "musicgen-large", "vram_est_gb": 11.0, "ram_est_gb": 14.0,
   58 [code      ]         "device_pref": "cuda", "cpu_fallback": "facebook/musicgen-medium"},
   59 [code      ]     "music_stereo": {
   60 [code      ]         "role": "Стерео-текстуры (переходы, интро, пэды)",
   61 [code      ]         "engine": "audiocraft_musicgen", "hf_repo": "facebook/musicgen-stereo-medium",
   62 [code      ]         "file": "musicgen-stereo-medium", "vram_est_gb": 8.0, "ram_est_gb": 10.0,
   63 [code      ]         "device_pref": "auto"},
   64 [code      ]     "tts_vocal": {
   65 [code      ]         "role": "Основной вокал (XTTS-v2, клонирование голоса)",
   66 [code      ]         "engine": "xtts_v2", "hf_repo": "coqui/XTTS-v2", "file": "XTTS-v2",
   67 [code      ]         "vram_est_gb": 4.0, "ram_est_gb": 6.0, "device_pref": "cuda"},
   68 [code      ]     "vocal_rvc": {
   69 [code      ]         "role": "Voice-conversion под голос артиста (.pth кладёт юзер)",
   70 [code      ]         "engine": "rvc", "hf_repo": "user_supplied", "file": "models/rvc/*.pth",
   71 [code      ]         "vram_est_gb": 3.0, "ram_est_gb": 4.0, "device_pref": "cuda"},
   72 [code      ]     "stem_splitter": {
   73 [code      ]         "role": "Демиксинг референса (Demucs htdemucs)",
   74 [code      ]         "engine": "demucs", "hf_repo": "facebook/demucs-htdemucs",
   75 [code      ]         "file": "htdemucs.th", "vram_est_gb": 6.0, "ram_est_gb": 10.0,
   76 [code      ]         "device_pref": "cuda"},
   77 [code      ]     "asr": {
   78 [code      ]         "role": "Распознавание речи референса (faster-whisper large-v3)",
   79 [code      ]         "engine": "faster_whisper", "hf_repo": "Systran/faster-whisper-large-v3",
   80 [code      ]         "file": "faster-whisper-large-v3", "vram_est_gb": 6.0, "ram_est_gb": 8.0,
   81 [code      ]         "device_pref": "cuda", "cpu_fallback": "Systran/faster-whisper-medium"},
   82 [code      ]     "audio_tagger": {
   83 [code      ]         "role": "Автотегирование (CLAP HTSAT-fused)",
   84 [code      ]         "engine": "clap", "hf_repo": "laion/clap-htsat-fused",
   85 [code      ]         "file": "clap-htsat-fused", "vram_est_gb": 2.5, "ram_est_gb": 4.0,
   86 [code      ]         "device_pref": "auto"},
   87 [code      ]     "essentia": {
   88 [code      ]         "role": "BPM/key/loudness (librosa DSP)",
   89 [code      ]         "engine": "essentia_or_librosa", "hf_repo": "", "file": "",
   90 [code      ]         "vram_est_gb": 0.0, "ram_est_gb": 2.0, "device_pref": "cpu"},
   91 [code      ]     "cover_art": {
   92 [code      ]         "role": "Обложка (SDXL Base 1.0 fp16)",
   93 [code      ]         "engine": "diffusers", "hf_repo": "stabilityai/stable-diffusion-xl-base-1.0",
   94 [code      ]         "file": "sdxl-base-1.0", "vram_est_gb": 10.0, "ram_est_gb": 8.0,
   95 [code      ]         "device_pref": "cuda", "cpu_fallback": "stabilityai/sd-turbo"},
   96 [code      ]     "mastering_ai": {
   97 [code      ]         "role": "AI-мастеринг (matchering под референс)",
   98 [code      ]         "engine": "matchering_plus", "hf_repo": "", "file": "",
   99 [code      ]         "vram_est_gb": 0.0, "ram_est_gb": 4.0, "device_pref": "cpu"},
  100 [code      ] }
  101 [blank     ] 
  102 [blank     ] 
  103 [decorator ] @dataclass
  104 [class     ] class LoadedModel:
  105 [code      ]     key: str
  106 [code      ]     handle: Any
  107 [code      ]     engine: str
  108 [code      ]     loaded_at: float
  109 [code      ]     device: str
  110 [code      ]     vram_est_gb: float
  111 [blank     ] 
  112 [blank     ] 
  113 [class     ] class ModelRegistry:
  114 [def       ]     def __init__(self, hw: Optional[HardwareBudget] = None):
  115 [code      ]         self.hw = hw or HardwareBudget.from_env()
  116 [code      ]         self._current: Optional[LoadedModel] = None
  117 [code      ]         self._loaders: Dict[str, Callable[[], Any]] = {}
  118 [code      ]         self._lock = threading.RLock()
  119 [code      ]         self._register_default_loaders()
  120 [blank     ] 
  121 [def       ]     def status(self) -> Dict[str, Any]:
  122 [code      ]         cur = self._current
  123 [return    ]         return {"current": cur.key if cur else None,
  124 [code      ]                 "engine": cur.engine if cur else None,
  125 [code      ]                 "device": cur.device if cur else None,
  126 [code      ]                 "vram_est_gb": cur.vram_est_gb if cur else 0.0,
  127 [code      ]                 "budget": {"vram_gb": self.hw.vram_gb, "ram_gb": self.hw.ram_gb,
  128 [code      ]                            "cpu_threads": self.hw.cpu_threads},
  129 [code      ]                 "registry": list(MODEL_REGISTRY.keys())}
  130 [blank     ] 
  131 [def       ]     def is_available(self, key: str) -> bool:
  132 [code      ]         spec = MODEL_REGISTRY.get(key)
  133 [branch    ]         if not spec:
  134 [return    ]             return False
  135 [code      ]         eng = spec["engine"]
  136 [try_block ]         try:
  137 [branch    ]             if eng == "llama_cpp":
  138 [import    ]                 import llama_cpp  # noqa
  139 [return    ]                 return (MODELS_DIR / "llm" / spec["file"]).exists()
  140 [branch    ]             if eng == "audiocraft_musicgen":
  141 [import    ]                 import audiocraft  # noqa
  142 [return    ]                 return True
  143 [branch    ]             if eng == "xtts_v2":
  144 [import    ]                 from TTS.api import TTS  # noqa
  145 [return    ]                 return True
  146 [branch    ]             if eng == "rvc":
  147 [code      ]                 d = ROOT / "models" / "rvc"
  148 [return    ]                 return d.exists() and any(d.glob("*.pth"))
  149 [branch    ]             if eng == "demucs":
  150 [import    ]                 import demucs  # noqa
  151 [return    ]                 return True
  152 [branch    ]             if eng == "faster_whisper":
  153 [import    ]                 from faster_whisper import WhisperModel  # noqa
  154 [return    ]                 return True
  155 [branch    ]             if eng == "clap":
  156 [import    ]                 import transformers  # noqa
  157 [return    ]                 return True
  158 [branch    ]             if eng == "essentia_or_librosa":
  159 [import    ]                 import librosa  # noqa
  160 [return    ]                 return True
  161 [branch    ]             if eng == "diffusers":
  162 [import    ]                 import diffusers  # noqa
  163 [return    ]                 return True
  164 [branch    ]             if eng == "matchering_plus":
  165 [import    ]                 import matchering  # noqa
  166 [return    ]                 return True
  167 [try_block ]         except Exception:
  168 [return    ]             return False
  169 [return    ]         return False
  170 [blank     ] 
  171 [def       ]     def load(self, key: str) -> LoadedModel:
  172 [stmt      ]         with self._lock:
  173 [branch    ]             if self._current and self._current.key == key:
  174 [return    ]                 return self._current
  175 [branch    ]             if self._current is not None:
  176 [code      ]                 self.unload()
  177 [code      ]             spec = MODEL_REGISTRY.get(key)
  178 [branch    ]             if not spec:
  179 [raise     ]                 raise KeyError(f"Unknown model role: {key}")
  180 [code      ]             loader = self._loaders.get(key)
  181 [branch    ]             if not loader:
  182 [raise     ]                 raise RuntimeError(f"No loader registered for {key}")
  183 [code      ]             handle, device = loader()
  184 [code      ]             self._current = LoadedModel(key=key, handle=handle,
  185 [code      ]                                         engine=spec["engine"],
  186 [code      ]                                         loaded_at=time.time(), device=device,
  187 [code      ]                                         vram_est_gb=float(spec.get("vram_est_gb", 0.0)))
  188 [return    ]             return self._current
  189 [blank     ] 
  190 [def       ]     def unload(self) -> None:
  191 [stmt      ]         with self._lock:
  192 [branch    ]             if self._current is None:
  193 [return    ]                 return
  194 [try_block ]             try:
  195 [code      ]                 del self._current.handle
  196 [try_block ]             except Exception:
  197 [code      ]                 pass
  198 [code      ]             self._current = None
  199 [code      ]             gc.collect()
  200 [try_block ]             try:
  201 [import    ]                 import torch
  202 [branch    ]                 if torch.cuda.is_available():
  203 [code      ]                     torch.cuda.empty_cache()
  204 [code      ]                     torch.cuda.ipc_collect()
  205 [try_block ]             except Exception:
  206 [code      ]                 pass
  207 [blank     ] 
  208 [class     ]     class _UseCtx:
  209 [def       ]         def __init__(self, reg, key, unload_after):
  210 [code      ]             self.reg = reg; self.key = key
  211 [code      ]             self.unload_after = unload_after; self.model = None
  212 [blank     ] 
  213 [def       ]         def __enter__(self):
  214 [code      ]             self.model = self.reg.load(self.key)
  215 [return    ]             return self.model
  216 [blank     ] 
  217 [def       ]         def __exit__(self, et, ex, tb):
  218 [branch    ]             if self.unload_after:
  219 [code      ]                 self.reg.unload()
  220 [return    ]             return False
  221 [blank     ] 
  222 [def       ]     def use(self, key: str, unload_after: bool = True):
  223 [return    ]         return ModelRegistry._UseCtx(self, key, unload_after)
  224 [blank     ] 
  225 [def       ]     def pick_device(self, spec: Dict[str, Any]) -> str:
  226 [code      ]         pref = spec.get("device_pref", "auto")
  227 [code      ]         need = float(spec.get("vram_est_gb", 0.0))
  228 [branch    ]         if pref == "cpu":
  229 [return    ]             return "cpu"
  230 [try_block ]         try:
  231 [import    ]             import torch
  232 [branch    ]             if pref in ("cuda", "auto") and torch.cuda.is_available():
  233 [branch    ]                 if need <= self.hw.vram_gb:
  234 [return    ]                     return "cuda"
  235 [try_block ]         except Exception:
  236 [code      ]             pass
  237 [try_block ]         try:
  238 [import    ]             import torch_directml  # noqa
  239 [branch    ]             if pref in ("dml", "auto") and need <= self.hw.vram_gb:
  240 [return    ]                 return "dml"
  241 [try_block ]         except Exception:
  242 [code      ]             pass
  243 [return    ]         return "cpu"
  244 [blank     ] 
  245 [def       ]     def _register_default_loaders(self) -> None:
  246 [def       ]         def _llama(key):
  247 [def       ]             def _do():
  248 [import    ]                 from llama_cpp import Llama
  249 [code      ]                 spec = MODEL_REGISTRY[key]
  250 [code      ]                 mp = MODELS_DIR / "llm" / spec["file"]
  251 [code      ]                 mp.parent.mkdir(parents=True, exist_ok=True)
  252 [branch    ]                 if not mp.exists():
  253 [raise     ]                     raise FileNotFoundError(
  254 [code      ]                         f"[{key}] not found at {mp}. "
  255 [code      ]                         f"Run: python tools/pull_ai_models.py --model {key}")
  256 [code      ]                 device = self.pick_device(spec)
  257 [code      ]                 llm = Llama(model_path=str(mp),
  258 [code      ]                             n_ctx=spec.get("context", 4096),
  259 [code      ]                             n_threads=min(self.hw.cpu_threads, 20),
  260 [code      ]                             n_gpu_layers=999 if device in ("cuda", "dml") else 0,
  261 [code      ]                             verbose=False)
  262 [return    ]                 return llm, device
  263 [return    ]             return _do
  264 [loop      ]         for k in ("lyrics_llm", "analysis_llm", "metadata_llm"):
  265 [code      ]             self._loaders[k] = _llama(k)
  266 [blank     ] 
  267 [def       ]         def _musicgen(key):
  268 [def       ]             def _do():
  269 [import    ]                 from audiocraft.models import MusicGen
  270 [code      ]                 spec = MODEL_REGISTRY[key]
  271 [code      ]                 device = self.pick_device(spec)
  272 [code      ]                 repo = spec["hf_repo"]
  273 [branch    ]                 if device == "cpu" and spec.get("cpu_fallback"):
  274 [code      ]                     repo = spec["cpu_fallback"]
  275 [return    ]                 return (MusicGen.get_pretrained(repo, device=device if device != "dml" else "cpu"), device)
  276 [return    ]             return _do
  277 [code      ]         self._loaders["music_generation"] = _musicgen("music_generation")
  278 [code      ]         self._loaders["music_stereo"] = _musicgen("music_stereo")
  279 [blank     ] 
  280 [def       ]         def _xtts():
  281 [import    ]             from TTS.api import TTS
  282 [code      ]             spec = MODEL_REGISTRY["tts_vocal"]
  283 [code      ]             device = self.pick_device(spec)
  284 [code      ]             t = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
  285 [branch    ]             if device == "cuda":
  286 [try_block ]                 try:
  287 [code      ]                     t.to("cuda")
  288 [try_block ]                 except Exception:
  289 [code      ]                     pass
  290 [return    ]             return t, device
  291 [code      ]         self._loaders["tts_vocal"] = _xtts
  292 [blank     ] 
  293 [def       ]         def _rvc():
  294 [import    ]             from modules import rvc_manager
  295 [code      ]             spec = MODEL_REGISTRY["vocal_rvc"]
  296 [return    ]             return rvc_manager, self.pick_device(spec)
  297 [code      ]         self._loaders["vocal_rvc"] = _rvc
  298 [blank     ] 
  299 [def       ]         def _demucs():
  300 [import    ]             from demucs.pretrained import get_model
  301 [code      ]             spec = MODEL_REGISTRY["stem_splitter"]
  302 [code      ]             device = self.pick_device(spec)
  303 [code      ]             m = get_model("htdemucs")
  304 [branch    ]             if device == "cuda":
  305 [try_block ]                 try:
  306 [code      ]                     m.to("cuda")
  307 [try_block ]                 except Exception:
  308 [code      ]                     pass
  309 [return    ]             return m, device
  310 [code      ]         self._loaders["stem_splitter"] = _demucs
  311 [blank     ] 
  312 [def       ]         def _wh():
  313 [import    ]             from faster_whisper import WhisperModel
  314 [code      ]             spec = MODEL_REGISTRY["asr"]
  315 [code      ]             device = self.pick_device(spec)
  316 [code      ]             size = "large-v3" if device != "cpu" else "medium"
  317 [code      ]             compute = "float16" if device == "cuda" else "int8"
  318 [return    ]             return WhisperModel(size, device=device if device != "dml" else "cpu",
  319 [code      ]                                 compute_type=compute), device
  320 [code      ]         self._loaders["asr"] = _wh
  321 [blank     ] 
  322 [def       ]         def _clap():
  323 [import    ]             from transformers import ClapModel, ClapProcessor
  324 [code      ]             spec = MODEL_REGISTRY["audio_tagger"]
  325 [code      ]             device = self.pick_device(spec)
  326 [code      ]             m = ClapModel.from_pretrained(spec["hf_repo"])
  327 [code      ]             p = ClapProcessor.from_pretrained(spec["hf_repo"])
  328 [branch    ]             if device == "cuda":
  329 [try_block ]                 try:
  330 [code      ]                     m = m.to("cuda")
  331 [try_block ]                 except Exception:
  332 [code      ]                     pass
  333 [return    ]             return (m, p), device
  334 [code      ]         self._loaders["audio_tagger"] = _clap
  335 [blank     ] 
  336 [code      ]         self._loaders["essentia"] = lambda: ("librosa_dsp", "cpu")
  337 [blank     ] 
  338 [def       ]         def _sdxl():
  339 [import    ]             from diffusers import DiffusionPipeline
  340 [import    ]             import torch
  341 [code      ]             spec = MODEL_REGISTRY["cover_art"]
  342 [code      ]             device = self.pick_device(spec)
  343 [code      ]             repo = spec["hf_repo"]
  344 [branch    ]             if device == "cpu" and spec.get("cpu_fallback"):
  345 [code      ]                 repo = spec["cpu_fallback"]
  346 [code      ]             pipe = DiffusionPipeline.from_pretrained(
  347 [code      ]                 repo, torch_dtype=torch.float16 if device == "cuda" else torch.float32,
  348 [code      ]                 variant="fp16" if device == "cuda" else None, use_safetensors=True)
  349 [branch    ]             if device == "cuda":
  350 [try_block ]                 try:
  351 [code      ]                     pipe.to("cuda")
  352 [code      ]                     pipe.enable_attention_slicing()
  353 [code      ]                     pipe.enable_vae_tiling()
  354 [try_block ]                 except Exception:
  355 [code      ]                     pass
  356 [return    ]             return pipe, device
  357 [code      ]         self._loaders["cover_art"] = _sdxl
  358 [blank     ] 
  359 [def       ]         def _match():
  360 [import    ]             import matchering  # noqa
  361 [return    ]             return matchering, "cpu"
  362 [code      ]         self._loaders["mastering_ai"] = _match
  363 [blank     ] 
  364 [blank     ] 
  365 [code      ] registry = ModelRegistry()
```