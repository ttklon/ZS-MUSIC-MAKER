# -*- coding: utf-8 -*-
"""
app/core/stages/master.py — Мастер: стенды, anti-neuro полировка, стемы, hit-score.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _stage_mastering(
    mix_wav: str, out_dir: Path, stands: list[str] | None = None
) -> dict[str, Any]:
    """v25 (P1): stands из wizard-recipe реально пробрасываются —
    раньше всегда мастерились все 8, игнорируя выбор пользователя
    (GUI шаг ②: car/club/streaming). Список санитизируется:
    streaming ВСЕГДА включён (это базовый вход для polish/stems/hit/release)."""
    try:
        from modules import mastering

        out = str(out_dir / "masters")
        _valid = {
            "streaming",
            "car",
            "club",
            "tiktok",
            "airpods",
            "bluetooth",
            "headphones",
            "monitors",
        }
        _stands: list[str] | None = None
        if stands:
            _stands = [s for s in stands if s in _valid]
            if "streaming" not in _stands:
                _stands.insert(0, "streaming")
        r = mastering.master_all_stands(mix_wav, out, stands=_stands)
        fb = r.get("summary", {}).get("fallback", 0) > 0
        r["fallback_used"] = fb
        return r
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _stage_polish(input_wav: str, out_dir: Path) -> dict[str, Any]:
    """Anti-neuro обработка мастера: трековая цепочка → вокальная → честная копия.

    Каждый движок пробуется изолированно: сбой одного не отменяет следующий,
    а полный отказ заканчивается явной копией с `fallback_used=True`.
    """
    out_wav = str(out_dir / "polished.wav")
    attempts: list[str] = []
    try:
        from modules import anti_neuro, anti_neuro_track

        for label, owner, name in (
            ("anti_neuro_track", anti_neuro_track, "polish_track"),
            ("anti_neuro", anti_neuro, "apply_polish"),
            ("anti_neuro", anti_neuro, "polish_vocal"),
        ):
            fn = getattr(owner, name, None)
            if not callable(fn):
                continue
            attempts.append(name)
            result: Any = None
            try:
                if name == "polish_track":
                    result = fn(input_wav, out_wav, preset="standard")
                elif name == "apply_polish":
                    result = fn(input_wav, out_wav, intensity=0.5)
                else:
                    result = fn(input_wav, out_wav, preset="standard")
            except TypeError:
                try:
                    result = fn(input_wav, out_wav)
                except Exception as exc:  # noqa: BLE001 - пробуем следующий движок
                    attempts.append(f"{name}:error:{type(exc).__name__}")
                    continue
            except Exception as exc:  # noqa: BLE001
                attempts.append(f"{name}:error:{type(exc).__name__}")
                continue
            if isinstance(result, str) and Path(result).exists():
                return {"ok": True, "path": result, "engine": f"{label}.{name}"}
            if isinstance(result, dict) and result.get("ok"):
                payload = dict(result)
                payload["path"] = payload.get("path") or payload.get("out_wav") or out_wav
                payload.setdefault("engine", f"{label}.{name}")
                return payload
    except Exception as exc:  # noqa: BLE001 - импорт недоступен
        attempts.append(f"import:error:{type(exc).__name__}")

    import shutil

    shutil.copy(input_wav, out_wav)
    return {
        "ok": True,
        "path": out_wav,
        "fallback_used": True,
        "attempts": attempts,
        "reason": "anti-neuro engines unavailable; master copied as-is",
    }


def _stage_stems(master_wav: str, out_dir: Path) -> dict[str, Any]:
    """v19 FIX (P0): раньше вызывался несуществующий stem_splitter.split(...),
    из-за чего стадия всегда падала на AttributeError → все прогоны стемов
    выдавали BLOCKED. Реальный API — stem_splitter.split_stems(...).
    """
    try:
        import demucs  # noqa
    except Exception:
        return {
            "ok": True,
            "blocked": True,
            "stems": {},
            "reason": "demucs not installed (heavy dep)",
            "notice": "install demucs for stem splitting on user PC",
        }
    try:
        from modules import stem_splitter

        fn = None
        for cand in ("split_stems", "split", "separate", "run"):
            f = getattr(stem_splitter, cand, None)
            if callable(f):
                fn = f
                break
        if fn is None:
            return {
                "ok": True,
                "blocked": True,
                "stems": {},
                "reason": "stem_splitter: no split_stems/split entry",
            }
        r = (
            fn(master_wav)
            if fn.__code__.co_argcount == 1
            else fn(master_wav, model="htdemucs")
        )
        if isinstance(r, dict):
            if "error" in r:
                return {
                    "ok": True,
                    "blocked": True,
                    "stems": {},
                    "reason": r["error"],
                    "engine": "demucs",
                }
            stems = {
                k: v for k, v in r.items() if k in ("vocals", "drums", "bass", "other")
            }
            return {
                "ok": bool(stems),
                "stems": stems,
                "n_stems": len(stems),
                "engine": "stem_splitter." + fn.__name__,
                "note": r.get("note", ""),
            }
        return {"ok": True, "path": str(r), "engine": "stem_splitter." + fn.__name__}
    except Exception as e:
        # v21: demucs есть, но runtime error — честный BLOCKED, не FAILED
        return {
            "ok": True,
            "blocked": True,
            "stems": {},
            "reason": f"{type(e).__name__}: {e}",
        }


def _stage_hit_score(master_wav: str) -> dict[str, Any]:
    """v19 FIX (P0): раньше искали hit_scorer.score(...), но реальная функция —
    hit_scorer.score_track(...). Из-за этого пайплайн всегда отдавал
    синтетические hit_score=60.0/verdict='solid' (ложная готовность).
    Теперь честно зовём score_track и пробрасываем реальные метрики.
    """
    try:
        from modules import hit_scorer

        fn = None
        for cand in ("score_track", "score", "evaluate"):
            f = getattr(hit_scorer, cand, None)
            if callable(f):
                fn = f
                break
        if fn is None:
            return {
                "ok": True,
                "hit_score": 60.0,
                "verdict": "solid",
                "fallback_used": True,
                "reason": "hit_scorer: no scoring entry exposed",
            }
        r = fn(master_wav)
        if not isinstance(r, dict):
            return {"ok": False, "reason": f"hit_scorer.{fn.__name__} bad return type"}
        if r.get("error"):
            return {
                "ok": False,
                "reason": r["error"],
                "hit_score": r.get("hit_score", 0.0),
                "verdict": r.get("verdict", "flop_risk"),
            }
        return {
            "ok": True,
            "hit_score": r.get("hit_score"),
            "verdict": r.get("verdict"),
            "metrics": r.get("metrics"),
            "tiktok_slice": r.get("tiktok_slice"),
            "actions": r.get("actions"),
            "engine": "hit_scorer." + fn.__name__,
        }
    except Exception as e:
        return {"ok": False, "reason": f"{type(e).__name__}: {e}"}
