"""
[v7] MusicGen Texture Engine — полноценный хайпер-инструмент.

При запуске из основного пайплайна выбирает CPU или PyTorch CUDA/ROCm
по измеренной свободной памяти; DirectML не является поддержкой MusicGen.
  • Генерирует атмосферы, FX, альтернативные хуки, пэды, мелодические затравки.
  • Батч-режим: несколько окон по 20-30 сек с разными промтами.
  • Ленивая загрузка модели, unload после использования (освобождение VRAM).
  • Кэширование результатов по (prompt+size+duration).
  • v35: НИКАКОГО pink-noise fallback (запрещено TZ 33.5). Если audiocraft
    не установлен — честный BLOCKED через get_status() + detect_availability()
    на старте приложения, а НЕ молчаливый выброс в лог.
"""

from __future__ import annotations

import logging

import hashlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "output" / "textures"
CACHE = ROOT / "models" / "musicgen_cache"
for d in (OUT_DIR, CACHE):
    d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------- model routing
def choose_size(vram_gb: float, quality_mode: str = "quality") -> str:
    """
    Выбираем размер модели в зависимости от VRAM и режима качества.
      quality_mode: "fast" | "quality" | "max"
    """
    if vram_gb >= 12:
        # 12+ GB — можем large или large-stereo
        return "large" if quality_mode != "fast" else "medium"
    if vram_gb >= 8:
        # 8-11 GiB доступного бюджета — оценка, не гарантия
        return "medium" if quality_mode != "fast" else "small"
    # ≤ 4 GB / CPU — только small
    return "small"


# --------------------------------------------------------------- model cache
_MODEL_CACHE: dict[str, Any] = {}


def _load_musicgen(size: str, device: str):
    """Ленивая загрузка модели MusicGen. Кэшируется в памяти."""
    cache_key = f"{size}:{device}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    try:
        from audiocraft.models import MusicGen

        model = MusicGen.get_pretrained(f"facebook/musicgen-{size}", device=device)
        _MODEL_CACHE[cache_key] = model
        return model
    except Exception as e:
        print(f"[musicgen_texture] audiocraft недоступен: {e}")
        return None


def unload_all() -> None:
    """Освобождаем VRAM (после генерации, перед RVC-инференсом)."""
    _MODEL_CACHE.clear()
    try:
        import torch

        torch.cuda.empty_cache()
    except Exception:
        logging.getLogger(__name__).debug("ignored exception", exc_info=True)


# --------------------------------------------------------------- v35: honest status
def detect_availability() -> dict:
    """v35 (SESSION_LOG P1): честная проверка доступности MusicGen БЕЗ загрузки
    весов. Раньше модуль «молча падал в лог» — пайплайн узнавал о проблеме
    только по ok=False глубоко в прогоне. Теперь стартап/health может вызвать
    detect_availability() и заранее показать пользователю честный статус.

    Возвращает dict:
      available  — True только если audiocraft+torch реально импортируются
      status     — PREFLIGHT | BLOCKED
      reason     — человекочитаемая причина (для UI/health)
      install_hint — как включить (для INSTALL/health)
    """
    try:
        import torch  # noqa: F401
    except Exception as e:
        return {
            "available": False,
            "status": "BLOCKED",
            "reason": f"torch не установлен ({type(e).__name__})",
            "install_hint": "pip install torch  (CPU-сборка достаточна для musicgen-small)",
        }
    try:
        import audiocraft  # noqa: F401
    except Exception:
        return {
            "available": False,
            "status": "BLOCKED",
            "reason": "audiocraft не установлен — MusicGen-текстуры отключены (это опциональная фича, ядро не ломается)",
            "install_hint": "pip install audiocraft  # ~тяжёлая зависимость, тянет torch+audio-стек",
        }
    return {
        "available": True,
        "status": "PREFLIGHT",
        "reason": "audiocraft + torch импортируются; веса и inference не проверены",
        "install_hint": "",
    }


def get_status() -> dict:
    """v35: сводный статус для health/dashboard (как get_status() у midi_generator)."""
    a = detect_availability()
    return {
        "module": "musicgen_texture",
        "status": a["status"],
        "available": a["available"],
        "reason": a["reason"],
        "install_hint": a["install_hint"],
        "cached_models": list(_MODEL_CACHE.keys()),
        "cache_dir": str(CACHE),
    }


# --------------------------------------------------------------- cache key
def _cache_key(prompt: str, size: str, duration: int) -> str:
    h = hashlib.md5(f"{prompt}|{size}|{duration}".encode()).hexdigest()[:12]
    return h


# --------------------------------------------------------------- main API
def generate_texture(
    prompt: str,
    duration_sec: int = 20,
    vram_gb: float = 4.0,
    quality_mode: str = "quality",
    out_name: str | None = None,
    device: str = "cpu",
) -> dict:
    """
    Генерирует одну текстуру (атмосфера/FX/пэд/хук).
    Возвращает dict с путём к WAV.
    """
    if device not in ("cpu", "cuda"):
        raise ValueError("MusicGen backend must be cpu or torch cuda/rocm")
    size = choose_size(vram_gb if device == "cuda" else 0.0, quality_mode)
    key = _cache_key(prompt, size, duration_sec)
    cached = CACHE / f"tex_{key}.wav"

    # 1) Кэш — вернуть если уже генерили
    if cached.exists() and cached.stat().st_size > 1000:
        return {
            "ok": True,
            "path": str(cached),
            "cached": True,
            "size": size,
            "duration": duration_sec,
        }

    # 2) Реальная генерация через audiocraft
    model = _load_musicgen(size, device)
    if model is None:
        # v35: честный лог причины один раз на вызов (не молчаливо)
        avail = detect_availability()
        print(f"[musicgen_texture] BLOCKED: {avail['reason']} | {avail['install_hint']}")
    if model is not None:
        try:
            model.set_generation_params(
                duration=duration_sec,
                use_sampling=True,
                top_k=250,
                top_p=0.0,
                temperature=1.0,
            )
            wav = model.generate([prompt])  # tensor [B, C, T]
            import torchaudio

            torchaudio.save(str(cached), wav[0].cpu(), sample_rate=32000)
            return {
                "ok": True,
                "path": str(cached),
                "cached": False,
                "size": size,
                "duration": duration_sec,
            }
        except Exception as e:
            print(f"[musicgen_texture] generation failed: {e}")

    # 3) Honest failure: pink noise is not MusicGen and must not be presented as it.
    return {
        "ok": False,
        "path": "",
        "cached": False,
        "size": "unavailable",
        "duration": duration_sec,
        "warning": "audiocraft/MusicGen unavailable; no synthetic fallback used",
    }


def generate_batch(
    prompts: list[str],
    duration_sec: int = 20,
    vram_gb: float = 4.0,
    quality_mode: str = "quality",
) -> list[dict]:
    """Батч-генерация — несколько промтов сразу для аранжировки."""
    results = []
    for p in prompts:
        results.append(generate_texture(p, duration_sec, vram_gb, quality_mode))
    return results


# --------------------------------------------------------------- fallback
def _pink_noise_fallback(prompt: str, duration_sec: int, out_path: str) -> str:
    """DEPRECATED v14 (TZ P0.06): pink-noise as MusicGen is FORBIDDEN.
    This function is kept only as a hard refusal marker. It is NOT
    called anywhere in the pipeline. Raise RuntimeError if invoked."""
    raise RuntimeError(
        "P0.06: pink-noise as MusicGen is FORBIDDEN by TZ 33.5. "
        "Install audiocraft for real MusicGen generation."
    )


# --------------------------------------------------------------- convenience
def generate_atmosphere(vibe: str, duration_sec: int = 30, vram_gb: float = 4.0) -> str:
    """Атмосферная подложка под вайб."""
    prompts = {
        "phonk": "dark cinematic phonk atmosphere with sub bass drones and distant chimes",
        "drift": "night city drift atmosphere with rain and neon hum",
        "hyperpop": "glitchy hyperpop atmosphere with pitched vocal chops",
        "lofi": "warm lofi tape atmosphere with vinyl crackle and soft pads",
        "trap": "dark trap atmosphere with 808 sub and hi-hat rolls",
        "summer": "warm summer atmosphere with soft synths and beach sounds",
    }
    prompt = prompts.get(vibe.lower(), f"cinematic {vibe} atmosphere with sub bass")
    r = generate_texture(
        prompt,
        duration_sec,
        vram_gb,
        quality_mode="quality",
        out_name=f"atmo_{vibe}.wav",
    )
    return r.get("path", "")


def generate_fx_hits(count: int = 5, vram_gb: float = 4.0) -> list[str]:
    """Набор коротких FX-хитов (риверсы/удары/переходы)."""
    prompts = [
        "reverse cinematic riser build-up 4 seconds",
        "impact bass hit with sub tail",
        "hi-hat roll fill 2 seconds",
        "vinyl scratch transition",
        "808 sub drop with distortion",
    ][:count]
    results = generate_batch(prompts, duration_sec=4, vram_gb=vram_gb)
    return [r["path"] for r in results if r.get("ok")]


if __name__ == "__main__":
    r = generate_texture("dark phonk atmosphere", duration_sec=10, vram_gb=4.0)
    print(r)
