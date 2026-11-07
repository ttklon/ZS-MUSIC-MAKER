# -*- coding: utf-8 -*-
"""
app/core/stages/beat.py — Бит: вызов `beat_constructor` и честный процедурный синтез-фоллбек.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# `_arrangement_drives_beat` реэкспортируется: его проверяют тесты и отчёты
# через этот модуль, а живёт он рядом с разбором плана.
from app.core.stages.beat_arrangement import (  # noqa: F401
    _arrangement_drives_beat,
    _arrangement_sections,
)

def _stage_ai_beat(recipe: dict[str, Any], plan: Any, out_dir: Path,
                   style: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    """Explicit external model: no substitution if it is missing or fails."""
    expected = recipe.get("recorded_backing_sha256", "")
    if expected and recipe.get("beat_engine") != "user_audio":
        return {"ok": False, "engine": "user_instrumental", "reason": "recorded backing required; select the original or record again"}
    if recipe.get("beat_engine") == "user_audio":
        try:
            from app.core.stages.imported_beat import import_instrumental
            return import_instrumental(recipe.get("beat_input_path", ""), out_dir / "beat.wav", expected_sha256=expected)
        except Exception as exc:
            prefix = "recorded backing: " if expected else ""
            return {"ok": False, "engine": "user_instrumental", "reason": f"{prefix}{type(exc).__name__}: {exc}"}
    if recipe.get("beat_engine") != "ace_step":
        return {"ok": False, "reason": f"unknown beat engine: {recipe.get('beat_engine')}"}
    if dry_run:
        return {"ok": True, "blocked": True, "reason": "ACE-Step skipped in dry run"}
    try:
        import os
        from app.ai.acestep import generate_instrumental

        prompt = f"Instrumental {recipe['genre']}, {recipe['theme']}; no vocals"
        return generate_instrumental(
            prompt, out_dir / "beat.wav", duration_sec=float((plan or {}).get("duration_sec") or 90),
            bpm=int(style.get("target_bpm") or 128), key=recipe_key(style), seed=recipe.get("seed"),
            base_url=os.getenv("ZSMM_ACESTEP_URL", "http://127.0.0.1:8001"),
            timeout_sec=float(os.getenv("ZSMM_ACESTEP_TIMEOUT", "7200")),
        )
    except Exception as exc:
        return {"ok": False, "engine": "ace_step_1_5_api", "reason": f"{type(exc).__name__}: {exc}"}


def _stage_beat(
    plan: Any,
    out_dir: Path,
    groove: Any = None,
    style_vector: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """v17 FIX (P0): construct_beat вместо несуществующего build_beat."""
    beat_wav = str(out_dir / "beat.wav")
    try:
        from modules import beat_constructor as bc

        style = style_vector or {"target_bpm": 128, "target_mode": "minor"}
        sections, arrangement_note = _arrangement_sections(plan)
        if hasattr(bc, "construct_beat"):
            r = bc.construct_beat(
                groove or {},
                [],
                style,
                duration_sec=int((plan or {}).get("duration_sec", 90)),
                n_verses=int((plan or {}).get("n_verses", 2)),
                aggression=float((plan or {}).get("aggression", 0.7)),
                out_name=Path(beat_wav).name,
                sections=sections,
            )
            if isinstance(r, dict) and r.get("beat_path"):
                src = Path(r["beat_path"])
                dst = Path(beat_wav)
                if src.exists() and src.resolve() != dst.resolve():
                    try:
                        import shutil

                        shutil.copy(src, dst)
                    except Exception:
                        dst = src
                return {
                    "ok": True,
                    "path": str(dst),
                    "bpm": r.get("bpm"),
                    "key": r.get("key"),
                    "sections": r.get("sections"),
                    "duration_sec": r.get("duration_sec"),
                    "engine": "beat_constructor.construct_beat",
                    "arrangement_driven": bool(sections),
                    **({"arrangement_note": arrangement_note} if arrangement_note else {}),
                }
        # v22: fallback — полный structured synth beat, не 8с тупые kicks
        _bpm = int(style.get("target_bpm", 128) or 128)
        _dur = int((plan or {}).get("duration_sec", 90) or 90)
        _key = recipe_key(style)
        return _synth_beat(
            beat_wav, duration=_dur, bpm=_bpm, key_root=_key.split()[0], key_name=_key
        )
    except Exception as e:
        try:
            _bpm = int((style_vector or {}).get("target_bpm", 128))
            _dur = int((plan or {}).get("duration_sec", 90))
            _key = recipe_key(style_vector)
            return _synth_beat(
                beat_wav, duration=_dur, bpm=_bpm, key_root=_key.split()[0], key_name=_key
            )
        except Exception:
            return {"ok": False, "reason": str(e)}


def recipe_key(style: dict[str, Any] | None) -> str:
    """Тональность из style_vector («A minor»), по умолчанию A minor."""
    style = style or {}
    root = str(style.get("key_root") or "A").upper()
    mode = str(style.get("target_mode") or "minor").lower()
    if mode not in ("major", "minor"):
        mode = "minor"
    return f"{root} {mode}"


def _render_beat_buffer(duration: int, bpm: int, key_root: str):
    """Готовый стерео-буфер и карта секций: шаги синтеза — в beat_synth."""
    import numpy as np

    from app.core.stages import beat_synth

    sr = 44100
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4
    step_sec = bar_sec / 16.0
    root_hz = beat_synth.KEY_HZ.get(key_root.upper(), 440.0) / 4.0
    sections = beat_synth.scale_sections(duration, bar_sec)
    total_samples = int(sum(nb * bar_sec for _, nb in sections) * sr)
    y = np.zeros(total_samples, dtype="float32")
    section_info = beat_synth.render_drum_lane(
        y, np, sr, sections, bar_sec, step_sec, beat_sec, root_hz
    )
    stereo = beat_synth.stereoize(y, np, sr)
    peak = float(np.max(np.abs(stereo)) + 1e-9)
    if peak > 0.98:
        stereo = stereo / peak * 0.95
    return stereo, section_info, sr, len(y)


def _synth_beat(
    out_wav: str,
    duration: int = 90,
    bpm: int = 128,
    key_root: str = "A",
    key_name: str | None = None,
) -> dict[str, Any]:
    """v22: полноценный structured synth-бит (не 8 сек тупых киков).

    Многосекционная структура (intro/verse/pre/chorus/verse/pre/chorus/outro),
    808 sub-bass по ключу, hi-hat roll перед drop, snare с air-tail,
    open-hat на offbeat, stop-time перед хуком, white+sub ризеры.
    Честно помечаем fallback_used=True — не выдаём за real beat_constructor.

    Порядок шагов — в `app/core/stages/beat_synth.py`: здесь только сборка
    результата и запись файла.
    """
    try:
        import soundfile as sf

        stereo, section_info, sr, length = _render_beat_buffer(duration, bpm, key_root)
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_wav, stereo, sr)
        return {
            "ok": True,
            "path": out_wav,
            "bpm": bpm,
            "key": key_name or f"{key_root} minor",
            "duration_sec": round(length / sr, 2),
            "sections": section_info,
            "engine": "synth_beat_v22",
            "fallback_used": True,
            "reason": "synthesized structured beat (beat_constructor unavailable)",
        }
    except Exception as e:
        return {"ok": False, "reason": str(e)}


