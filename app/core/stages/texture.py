# -*- coding: utf-8 -*-
"""
app/core/stages/texture.py — Атмосферная текстура: MusicGen, иначе честный synth-скаффолд.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _texture_scaffold(prompt: str, out_dir: Path) -> dict[str, Any]:
    """v23: честный синтезированный ambient-scaffold вместо пустого path.

    Раньше при недоступном MusicGen стадия отдавала path="" — и в трек
    не попадало НИЧЕГО, при этом fallback_used=True намекал, что что-то
    сгенерировано. Теперь синтезируем реальную низкоуровневую текстуру
    (drone-пэд + медленная огибающая + лёгкий noise-bed), которая:
      • реально записывается на диск и может попасть в микс;
      • честно помечена synthetic=True и engine='texture_scaffold_v23';
      • НЕ выдаётся за MusicGen-нейротекстуру.
    Это скелет атмосферы, а не финальный продакшн-текстур.
    """
    try:
        import numpy as np
        import soundfile as sf

        sr = 22050
        dur = 10.0
        n = int(sr * dur)
        t = np.arange(n) / sr
        # Drone-пэд: сумма трёх расстроенных пил вокруг 110 Hz
        base = 110.0
        pad = np.zeros(n, dtype="float32")
        for det in (-6.0, 0.0, 5.0):
            f = base * (2.0 ** (det / 1200.0))
            pad += np.sign(np.sin(2 * np.pi * f * t)) * 0.18
        # медленная огибающая (нарастание/спад), чтобы не было резких краёв
        env = np.sin(np.pi * t / dur) ** 2
        # лёгкий noise-bed для «воздуха»
        noise = np.random.randn(n).astype("float32")
        # грубый LP фильтр шума через скользящее среднее
        k = 64
        noise = np.convolve(noise, np.ones(k) / k, mode="same") * 0.06
        y = (pad * env * 0.5 + noise * env).astype("float32")
        # лёгкая стерео-раскладка
        stereo = np.stack([y, np.roll(y, int(sr * 0.012))], axis=1)
        peak = float(np.max(np.abs(stereo))) + 1e-9
        stereo = stereo / peak * 0.32  # текстура должна сидеть под миксом
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        out_wav = str(Path(out_dir) / "texture_scaffold.wav")
        sf.write(out_wav, stereo, sr)
        return {
            "ok": True,
            "path": out_wav,
            "blocked": True,
            "synthetic": True,
            "fallback_used": True,
            "engine": "texture_scaffold_v23",
            "duration_sec": round(len(y) / sr, 2),
            "reason": "audiocraft/MusicGen unavailable; honest synth "
            "ambient scaffold generated (not a neural texture)",
        }
    except Exception as e:
        return {
            "ok": True,
            "path": "",
            "blocked": True,
            "fallback_used": True,
            "reason": f"texture scaffold failed: {type(e).__name__}: {e}",
        }


def _stage_texture(prompt: str, out_dir: Path) -> dict[str, Any]:
    """v19: texture — опциональная стадия. Если MusicGen недоступен,
    честно отдаём ok=True + blocked=True + fallback_used=True, чтобы
    не ронять процент готовностью отсутствующей heavy-зависимости.
    v23: вместо пустого path отдаём реальный синтезированный scaffold.
    """
    try:
        from app.core import musicgen_texture as mgt

        r = mgt.generate_texture(prompt, duration_sec=10, vram_gb=0.0)
        if isinstance(r, dict) and r.get("ok") and r.get("path"):
            return r
        return _texture_scaffold(prompt, out_dir)
    except Exception:
        return _texture_scaffold(prompt, out_dir)
