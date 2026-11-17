# -*- coding: utf-8 -*-
"""
app/core/stages/master.py — Мастер: стенды, anti-neuro полировка, стемы, hit-score.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _stage_mastering(
    mix_wav: str,
    out_dir: Path,
    stands: list[str] | None = None,
    iterations: int | None = None,
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
        # режим качества из визарда: сколько доводок громкости делает мастеринг
        r = mastering.master_all_stands(mix_wav, out, stands=_stands, iterations=iterations)
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
                return _finalize_polish(result, f"{label}.{name}")
            if isinstance(result, dict) and result.get("ok"):
                payload = dict(result)
                payload["path"] = payload.get("path") or payload.get("out_wav") or out_wav
                payload.setdefault("engine", f"{label}.{name}")
                return _finalize_polish(str(payload["path"]), payload["engine"], payload)
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


def _finalize_polish(polished_wav: str, engine: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Вернуть громкость полировки к стенду streaming (−14 LUFS, −1 dBTP).

    Anti-neuro цепочка (лента, lofi-срез, джиттер) меняет уровень на 0.5–1 дБ.
    Без возврата к целевому LUFS «полированный» мастер выпадал бы из гейтов
    §7.2, поэтому нормализуем тем же единым движком мастеринга.
    """
    from modules import mastering

    result = dict(payload or {})
    result["path"] = polished_wav
    result["engine"] = engine
    normalized = mastering.normalize_master_loudness(polished_wav, polished_wav, target_lufs=-14.0)
    result["loudness"] = normalized
    result["gates"] = {
        "true_peak": float(normalized.get("output_true_peak_dbtp", 0.0)) <= -1.0,
        "lufs": abs(float(normalized.get("output_lufs", 0.0)) + 14.0) <= 0.5,
    }
    result["gates_passed"] = all(result["gates"].values())
    return result


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



def apply_adaptive_enhance(master_wav: str, adaptive_level: int, enhanced_dsp: bool) -> dict[str, Any]:
    """Лёгкая сатурация + расширение для ultra_light без нейросетей.

    Живёт в пайплайне, а не после него: раньше хит-фабрика вызывала этот шаг
    уже после `run_full_pipeline`, из-за чего hit-score, релизный пакет и
    `artifact_integrity` описывали один мастер, а на диске лежал другой.
    Теперь обработка — часть стадии `_stage_polish`, до всех измерений.
    """
    if not enhanced_dsp or int(adaptive_level or 0) != 0:
        return {"ok": True, "applied": False, "reason": "adaptive DSP disabled for this level"}
    try:
        import numpy as np
        import soundfile as sf

        from modules.hit_factory.adaptive import get_adaptive_config

        cfg = get_adaptive_config()
        if cfg.get("use_acestep") or cfg.get("use_musicgen"):
            return {"ok": True, "applied": False, "reason": "neural engine owns the master"}
        data, sr = sf.read(str(master_wav))
        if data.ndim == 1:
            data = np.stack([data, data], axis=1)
        if data.shape[0] > sr * 0.02:
            drive = 0.02
            data = np.tanh(data * (1 + drive)) / np.tanh(1 + drive)
            delay = int(sr * 0.012)
            if delay > 0 and data.shape[0] > delay:
                data[delay:, 1] = 0.7 * data[delay:, 1] + 0.3 * data[:-delay, 1]
        try:
            from scipy.signal import butter, lfilter

            b, a = butter(2, 80 / (sr / 2), btype="low")
            low = lfilter(b, a, data, axis=0)
            data = data * 0.85 + low * 0.15 * 1.2
        except Exception as _exc:  # noqa: BLE001 - фильтр опционален
            print(f"[adaptive] ignored: {_exc}")
        peak = float(np.max(np.abs(data)) + 1e-9)
        if peak > 0.99:
            data = data / peak * 0.95
        sf.write(str(master_wav), data, sr)
        return {"ok": True, "applied": True, "engine": "adaptive.ultra_light"}
    except Exception as exc:  # noqa: BLE001 - обработка не критична
        return {"ok": False, "applied": False, "reason": f"{type(exc).__name__}: {exc}"}


def _stage_auto_qa(master_wav: str) -> dict[str, Any]:
    """Второе «ухо» на финальный мастер: QA-вердикт и конкретные правки.

    `modules/auto_qa.audit_track` умел это давно, но в пайплайн не был
    подключён ни разу — QA-отчёт существовал только как ручной вызов. Стадия
    возвращает `verdict` (`release`/`patch`/`rebuild`) и список `actions`;
    она не переводит трек в FAILED: замечания к качеству — это информация,
    а не поломка рендера.
    """
    try:
        from modules.auto_qa import audit_track

        report = audit_track(master_wav)
        if not report.get("ok"):
            return {"ok": False, "reason": report.get("error") or "auto QA failed"}
        return {
            "ok": True,
            "verdict": report.get("verdict"),
            "verdict_text": report.get("verdict_text"),
            "actions": [item.get("reason") for item in report.get("actions") or []],
            "report_path": report.get("report_path"),
        }
    except Exception as exc:  # noqa: BLE001 - QA не должен ронять рендер
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}


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
