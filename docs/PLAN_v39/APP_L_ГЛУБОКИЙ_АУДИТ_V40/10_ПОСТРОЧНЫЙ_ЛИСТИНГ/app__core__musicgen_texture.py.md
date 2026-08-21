# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/core/musicgen_texture.py`

**Всего строк:** 261

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 113 | 43.3 |
| docstring | 40 | 15.3 |
| blank | 37 | 14.2 |
| return | 17 | 6.5 |
| comment | 14 | 5.4 |
| def | 11 | 4.2 |
| try_block | 10 | 3.8 |
| import | 9 | 3.4 |
| branch | 7 | 2.7 |
| loop | 2 | 0.8 |
| raise | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] MusicGen Texture Engine — полноценный хайпер-инструмент.
    3 [blank     ] 
    4 [docstring ] По разделу 20.1 ТЗ:
    5 [docstring ]   • VRAM-aware routing: CPU-only → small; DirectML 6-8 GB → medium;
    6 [docstring ]     CUDA 12 GB+ → large / large-stereo.
    7 [docstring ]   • Генерирует атмосферы, FX, альтернативные хуки, пэды, мелодические затравки.
    8 [docstring ]   • Батч-режим: несколько окон по 20-30 сек с разными промтами.
    9 [docstring ]   • Ленивая загрузка модели, unload после использования (освобождение VRAM).
   10 [docstring ]   • Кэширование результатов по (prompt+size+duration).
   11 [docstring ]   • v35: НИКАКОГО pink-noise fallback (запрещено TZ 33.5). Если audiocraft
   12 [docstring ]     не установлен — честный BLOCKED через get_status() + detect_availability()
   13 [docstring ]     на старте приложения, а НЕ молчаливый выброс в лог.
   14 [docstring ] """
   15 [blank     ] 
   16 [import    ] from __future__ import annotations
   17 [blank     ] 
   18 [import    ] import hashlib
   19 [import    ] from pathlib import Path
   20 [import    ] from typing import Any
   21 [blank     ] 
   22 [code      ] ROOT = Path(__file__).resolve().parents[2]
   23 [code      ] OUT_DIR = ROOT / "output" / "textures"
   24 [code      ] CACHE = ROOT / "models" / "musicgen_cache"
   25 [loop      ] for d in (OUT_DIR, CACHE):
   26 [code      ]     d.mkdir(parents=True, exist_ok=True)
   27 [blank     ] 
   28 [blank     ] 
   29 [comment   ] # --------------------------------------------------------------- model routing
   30 [def       ] def choose_size(vram_gb: float, quality_mode: str = "quality") -> str:
   31 [docstring ]     """
   32 [docstring ]     Выбираем размер модели в зависимости от VRAM и режима качества.
   33 [docstring ]       quality_mode: "fast" | "quality" | "max"
   34 [docstring ]     """
   35 [branch    ]     if vram_gb >= 12:
   36 [comment   ]         # 12+ GB — можем large или large-stereo
   37 [return    ]         return "large" if quality_mode != "fast" else "medium"
   38 [branch    ]     if vram_gb >= 6:
   39 [comment   ]         # 6-11 GB — medium сбалансированно
   40 [return    ]         return "medium" if quality_mode != "fast" else "small"
   41 [comment   ]     # ≤ 4 GB / CPU — только small
   42 [return    ]     return "small"
   43 [blank     ] 
   44 [blank     ] 
   45 [comment   ] # --------------------------------------------------------------- model cache
   46 [code      ] _MODEL_CACHE: dict[str, Any] = {}
   47 [blank     ] 
   48 [blank     ] 
   49 [def       ] def _load_musicgen(size: str):
   50 [docstring ]     """Ленивая загрузка модели MusicGen. Кэшируется в памяти."""
   51 [branch    ]     if size in _MODEL_CACHE:
   52 [return    ]         return _MODEL_CACHE[size]
   53 [try_block ]     try:
   54 [import    ]         from audiocraft.models import MusicGen
   55 [blank     ] 
   56 [code      ]         model = MusicGen.get_pretrained(f"facebook/musicgen-{size}")
   57 [code      ]         _MODEL_CACHE[size] = model
   58 [return    ]         return model
   59 [try_block ]     except Exception as e:
   60 [code      ]         print(f"[musicgen_texture] audiocraft недоступен: {e}")
   61 [return    ]         return None
   62 [blank     ] 
   63 [blank     ] 
   64 [def       ] def unload_all() -> None:
   65 [docstring ]     """Освобождаем VRAM (после генерации, перед RVC-инференсом)."""
   66 [code      ]     _MODEL_CACHE.clear()
   67 [try_block ]     try:
   68 [import    ]         import torch
   69 [blank     ] 
   70 [code      ]         torch.cuda.empty_cache()
   71 [try_block ]     except Exception:
   72 [code      ]         pass
   73 [blank     ] 
   74 [blank     ] 
   75 [comment   ] # --------------------------------------------------------------- v35: honest status
   76 [def       ] def detect_availability() -> dict:
   77 [docstring ]     """v35 (SESSION_LOG P1): честная проверка доступности MusicGen БЕЗ загрузки
   78 [docstring ]     весов. Раньше модуль «молча падал в лог» — пайплайн узнавал о проблеме
   79 [docstring ]     только по ok=False глубоко в прогоне. Теперь стартап/health может вызвать
   80 [docstring ]     detect_availability() и заранее показать пользователю честный статус.
   81 [blank     ] 
   82 [docstring ]     Возвращает dict:
   83 [docstring ]       available  — True только если audiocraft+torch реально импортируются
   84 [docstring ]       status     — REAL_PASS | BLOCKED
   85 [docstring ]       reason     — человекочитаемая причина (для UI/health)
   86 [docstring ]       install_hint — как включить (для INSTALL/health)
   87 [docstring ]     """
   88 [try_block ]     try:
   89 [import    ]         import torch  # noqa: F401
   90 [try_block ]     except Exception as e:
   91 [return    ]         return {
   92 [code      ]             "available": False,
   93 [code      ]             "status": "BLOCKED",
   94 [code      ]             "reason": f"torch не установлен ({type(e).__name__})",
   95 [code      ]             "install_hint": "pip install torch  (CPU-сборка достаточна для musicgen-small)",
   96 [code      ]         }
   97 [try_block ]     try:
   98 [import    ]         import audiocraft  # noqa: F401
   99 [try_block ]     except Exception:
  100 [return    ]         return {
  101 [code      ]             "available": False,
  102 [code      ]             "status": "BLOCKED",
  103 [code      ]             "reason": "audiocraft не установлен — MusicGen-текстуры отключены (это опциональная фича, ядро не ломается)",
  104 [code      ]             "install_hint": "pip install audiocraft  # ~тяжёлая зависимость, тянет torch+audio-стек",
  105 [code      ]         }
  106 [return    ]     return {
  107 [code      ]         "available": True,
  108 [code      ]         "status": "REAL_PASS",
  109 [code      ]         "reason": "audiocraft + torch доступны",
  110 [code      ]         "install_hint": "",
  111 [code      ]     }
  112 [blank     ] 
  113 [blank     ] 
  114 [def       ] def get_status() -> dict:
  115 [docstring ]     """v35: сводный статус для health/dashboard (как get_status() у midi_generator)."""
  116 [code      ]     a = detect_availability()
  117 [return    ]     return {
  118 [code      ]         "module": "musicgen_texture",
  119 [code      ]         "status": a["status"],
  120 [code      ]         "available": a["available"],
  121 [code      ]         "reason": a["reason"],
  122 [code      ]         "install_hint": a["install_hint"],
  123 [code      ]         "cached_models": list(_MODEL_CACHE.keys()),
  124 [code      ]         "cache_dir": str(CACHE),
  125 [code      ]     }
  126 [blank     ] 
  127 [blank     ] 
  128 [comment   ] # --------------------------------------------------------------- cache key
  129 [def       ] def _cache_key(prompt: str, size: str, duration: int) -> str:
  130 [code      ]     h = hashlib.md5(f"{prompt}|{size}|{duration}".encode()).hexdigest()[:12]
  131 [return    ]     return h
  132 [blank     ] 
  133 [blank     ] 
  134 [comment   ] # --------------------------------------------------------------- main API
  135 [def       ] def generate_texture(
  136 [code      ]     prompt: str,
  137 [code      ]     duration_sec: int = 20,
  138 [code      ]     vram_gb: float = 4.0,
  139 [code      ]     quality_mode: str = "quality",
  140 [code      ]     out_name: str | None = None,
  141 [code      ] ) -> dict:
  142 [docstring ]     """
  143 [docstring ]     Генерирует одну текстуру (атмосфера/FX/пэд/хук).
  144 [docstring ]     Возвращает dict с путём к WAV.
  145 [docstring ]     """
  146 [code      ]     size = choose_size(vram_gb, quality_mode)
  147 [code      ]     key = _cache_key(prompt, size, duration_sec)
  148 [code      ]     cached = CACHE / f"tex_{key}.wav"
  149 [blank     ] 
  150 [comment   ]     # 1) Кэш — вернуть если уже генерили
  151 [branch    ]     if cached.exists() and cached.stat().st_size > 1000:
  152 [return    ]         return {
  153 [code      ]             "ok": True,
  154 [code      ]             "path": str(cached),
  155 [code      ]             "cached": True,
  156 [code      ]             "size": size,
  157 [code      ]             "duration": duration_sec,
  158 [code      ]         }
  159 [blank     ] 
  160 [comment   ]     # 2) Реальная генерация через audiocraft
  161 [code      ]     model = _load_musicgen(size)
  162 [branch    ]     if model is None:
  163 [comment   ]         # v35: честный лог причины один раз на вызов (не молчаливо)
  164 [code      ]         avail = detect_availability()
  165 [code      ]         print(f"[musicgen_texture] BLOCKED: {avail['reason']} | {avail['install_hint']}")
  166 [branch    ]     if model is not None:
  167 [try_block ]         try:
  168 [code      ]             model.set_generation_params(
  169 [code      ]                 duration=duration_sec,
  170 [code      ]                 use_sampling=True,
  171 [code      ]                 top_k=250,
  172 [code      ]                 top_p=0.0,
  173 [code      ]                 temperature=1.0,
  174 [code      ]             )
  175 [code      ]             wav = model.generate([prompt])  # tensor [B, C, T]
  176 [import    ]             import torchaudio
  177 [blank     ] 
  178 [code      ]             torchaudio.save(str(cached), wav[0].cpu(), sample_rate=32000)
  179 [return    ]             return {
  180 [code      ]                 "ok": True,
  181 [code      ]                 "path": str(cached),
  182 [code      ]                 "cached": False,
  183 [code      ]                 "size": size,
  184 [code      ]                 "duration": duration_sec,
  185 [code      ]             }
  186 [try_block ]         except Exception as e:
  187 [code      ]             print(f"[musicgen_texture] generation failed: {e}")
  188 [blank     ] 
  189 [comment   ]     # 3) Honest failure: pink noise is not MusicGen and must not be presented as it.
  190 [return    ]     return {
  191 [code      ]         "ok": False,
  192 [code      ]         "path": "",
  193 [code      ]         "cached": False,
  194 [code      ]         "size": "unavailable",
  195 [code      ]         "duration": duration_sec,
  196 [code      ]         "warning": "audiocraft/MusicGen unavailable; no synthetic fallback used",
  197 [code      ]     }
  198 [blank     ] 
  199 [blank     ] 
  200 [def       ] def generate_batch(
  201 [code      ]     prompts: list[str],
  202 [code      ]     duration_sec: int = 20,
  203 [code      ]     vram_gb: float = 4.0,
  204 [code      ]     quality_mode: str = "quality",
  205 [code      ] ) -> list[dict]:
  206 [docstring ]     """Батч-генерация — несколько промтов сразу для аранжировки."""
  207 [code      ]     results = []
  208 [loop      ]     for p in prompts:
  209 [code      ]         results.append(generate_texture(p, duration_sec, vram_gb, quality_mode))
  210 [return    ]     return results
  211 [blank     ] 
  212 [blank     ] 
  213 [comment   ] # --------------------------------------------------------------- fallback
  214 [def       ] def _pink_noise_fallback(prompt: str, duration_sec: int, out_path: str) -> str:
  215 [docstring ]     """DEPRECATED v14 (TZ P0.06): pink-noise as MusicGen is FORBIDDEN.
  216 [docstring ]     This function is kept only as a hard refusal marker. It is NOT
  217 [docstring ]     called anywhere in the pipeline. Raise RuntimeError if invoked."""
  218 [raise     ]     raise RuntimeError(
  219 [code      ]         "P0.06: pink-noise as MusicGen is FORBIDDEN by TZ 33.5. "
  220 [code      ]         "Install audiocraft for real MusicGen generation."
  221 [code      ]     )
  222 [blank     ] 
  223 [blank     ] 
  224 [comment   ] # --------------------------------------------------------------- convenience
  225 [def       ] def generate_atmosphere(vibe: str, duration_sec: int = 30, vram_gb: float = 4.0) -> str:
  226 [docstring ]     """Атмосферная подложка под вайб."""
  227 [code      ]     prompts = {
  228 [code      ]         "phonk": "dark cinematic phonk atmosphere with sub bass drones and distant chimes",
  229 [code      ]         "drift": "night city drift atmosphere with rain and neon hum",
  230 [code      ]         "hyperpop": "glitchy hyperpop atmosphere with pitched vocal chops",
  231 [code      ]         "lofi": "warm lofi tape atmosphere with vinyl crackle and soft pads",
  232 [code      ]         "trap": "dark trap atmosphere with 808 sub and hi-hat rolls",
  233 [code      ]         "summer": "warm summer atmosphere with soft synths and beach sounds",
  234 [code      ]     }
  235 [code      ]     prompt = prompts.get(vibe.lower(), f"cinematic {vibe} atmosphere with sub bass")
  236 [code      ]     r = generate_texture(
  237 [code      ]         prompt,
  238 [code      ]         duration_sec,
  239 [code      ]         vram_gb,
  240 [code      ]         quality_mode="quality",
  241 [code      ]         out_name=f"atmo_{vibe}.wav",
  242 [code      ]     )
  243 [return    ]     return r.get("path", "")
  244 [blank     ] 
  245 [blank     ] 
  246 [def       ] def generate_fx_hits(count: int = 5, vram_gb: float = 4.0) -> list[str]:
  247 [docstring ]     """Набор коротких FX-хитов (риверсы/удары/переходы)."""
  248 [code      ]     prompts = [
  249 [code      ]         "reverse cinematic riser build-up 4 seconds",
  250 [code      ]         "impact bass hit with sub tail",
  251 [code      ]         "hi-hat roll fill 2 seconds",
  252 [code      ]         "vinyl scratch transition",
  253 [code      ]         "808 sub drop with distortion",
  254 [code      ]     ][:count]
  255 [code      ]     results = generate_batch(prompts, duration_sec=4, vram_gb=vram_gb)
  256 [return    ]     return [r["path"] for r in results if r.get("ok")]
  257 [blank     ] 
  258 [blank     ] 
  259 [branch    ] if __name__ == "__main__":
  260 [code      ]     r = generate_texture("dark phonk atmosphere", duration_sec=10, vram_gb=4.0)
  261 [code      ]     print(r)
```