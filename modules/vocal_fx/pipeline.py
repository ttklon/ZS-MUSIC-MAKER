# -*- coding: utf-8 -*-
"""
modules/vocal_fx/pipeline.py — единая цепочка обработки вокала.

Порядок: clean (опционально) → double → throw. Throw не критичен: если он не
сработал, остаётся double; если не сработало ничего — честный отказ, а не
скрытая копия «как будто обработали».
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from modules.vocal_fx.double import apply_vocal_double
from modules.vocal_fx.dsp import _OK
from modules.vocal_fx.throw import apply_delay_throw


def process_vocal(
    vocal_wav: str,
    out_wav: str,
    use_double: bool = True,
    use_throw: bool = True,
    double_level_db: float = -10.0,
    throw_level_db: float = -9.0,
    delay_ms: float = 320.0,
    clean_before_fx: bool = True,
    genre: str | None = None,
    use_tune: bool = True,
    use_deess: bool = True,
    use_prosody: bool = True,
    bpm: float | None = None,
    tonic: str = "A",
    scale: str = "minor",
    tune_strength: float = 0.7,
) -> dict[str, Any]:
    """Единая точка: clean -> double -> throw -> out. Возвращает dict-результат."""
    if not _OK:
        return {"ok": False, "engine": "none", "reason": "numpy/soundfile unavailable"}

    cur = vocal_wav
    stages: list[str] = []
    throws = 0
    tmp_clean = str(Path(out_wav).with_name("_vocal_clean_tmp.wav"))
    tmp_tune = str(Path(out_wav).with_name("_vocal_tune_tmp.wav"))
    tmp_double = str(Path(out_wav).with_name("_fx_double_tmp.wav"))
    cleaner = None
    tune_report: dict[str, Any] | None = None
    deess_report: dict[str, Any] | None = None
    prosody_report: dict[str, Any] | None = None
    skipped: list[dict[str, str]] = []

    if clean_before_fx:
        try:
            from modules.voice_cleaner import clean_vocal_chain

            cleaner = clean_vocal_chain(cur, tmp_clean, genre=genre)
            if cleaner.get("ok"):
                cur = str(cleaner["path"])
                stages.append("clean")
        except Exception as exc:
            cleaner = {"ok": False, "reason": str(exc)}

    if use_tune or use_deess:
        cur, tune_report, deess_report = _shape_vocal(
            cur,
            tmp_tune,
            use_tune=use_tune,
            use_deess=use_deess,
            tonic=tonic,
            scale=scale,
            tune_strength=tune_strength,
            stages=stages,
            skipped=skipped,
        )

    if use_prosody:
        cur, prosody_report = _prosody_vocal(cur, out_wav, bpm=bpm, stages=stages, skipped=skipped)

    if use_double:
        r = apply_vocal_double(cur, tmp_double, double_level_db=double_level_db)
        if r.ok:
            cur = tmp_double
            stages.append("double")

    if use_throw:
        r = apply_delay_throw(
            cur, out_wav, delay_ms=delay_ms, throw_level_db=throw_level_db
        )
        if r.ok:
            cur = out_wav
            stages.append("throw")
            throws = r.throws_applied
        else:
            # throw не критичен — остаёмся на double
            try:
                shutil.copy(cur, out_wav)
                cur = out_wav
            except (OSError, shutil.Error) as error:
                return {
                    "ok": False,
                    "engine": "none",
                    "reason": f"throw failed and fallback copy could not be written: {error}",
                    "cleaner": cleaner,
                }

    if not stages:
        # оба не сработали — честно сообщаем, не делаем скрытый copy
        return {"ok": False, "engine": "none", "reason": "clean, double and throw all failed"}

    if str(cur) != str(out_wav):
        # финал не совпал с целевым путём (например, без double/throw) — копируем
        try:
            shutil.copy(cur, out_wav)
            cur = out_wav
        except (OSError, shutil.Error) as error:
            return {
                "ok": False,
                "engine": "none",
                "reason": f"clean vocal could not be finalized: {error}",
                "cleaner": cleaner,
            }

    # подчистить временные файлы, не удаляя текущий итог
    cleanup_warnings: list[str] = []
    for temporary in (tmp_clean, tmp_tune, tmp_double, _prosody_temp(out_wav)):
        path = Path(temporary)
        try:
            if path.exists() and str(path) != str(cur):
                path.unlink()
        except OSError as error:
            cleanup_warnings.append(f"{path.name}: {type(error).__name__}: {error}")

    return {
        "ok": True,
        "engine": "numpy_vocal_fx",
        "path": cur,
        "out_wav": cur,
        "stages": stages,
        "throws_applied": throws,
        "double_used": "double" in stages,
        "throw_used": "throw" in stages,
        "clean_used": "clean" in stages,
        "cleaner": cleaner,
        "tune": tune_report,
        "deess": deess_report,
        "prosody": prosody_report,
        "skipped": skipped,
        "cleanup_warnings": cleanup_warnings,
    }


def _prosody_temp(out_wav: str) -> str:
    return str(Path(out_wav).with_name("_vocal_prosody_tmp.wav"))


def _shape_vocal(
    path: str,
    out_path: str,
    *,
    use_tune: bool,
    use_deess: bool,
    tonic: str,
    scale: str,
    tune_strength: float,
    stages: list[str],
    skipped: list[dict[str, str]],
) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    """Тюн и де-эссер: один проход чтения/записи, отчёты наружу."""
    import numpy as np
    import soundfile as sf

    try:
        data, sample_rate = sf.read(path, always_2d=True)
    except Exception as exc:  # noqa: BLE001 - отказ честно попадает в skipped
        skipped.append({"stage": "tune", "reason": f"{type(exc).__name__}: {exc}"})
        return path, None, None

    audio = np.asarray(data, dtype=np.float64)
    tune_report: dict[str, Any] | None = None
    deess_report: dict[str, Any] | None = None
    if use_tune:
        try:
            from modules.vocal_fx.pitch import correct_pitch

            audio, tune_report = correct_pitch(
                audio, sample_rate, tonic=tonic, scale=scale, strength=tune_strength
            )
            stages.append("tune")
        except Exception as exc:  # noqa: BLE001
            skipped.append({"stage": "tune", "reason": f"{type(exc).__name__}: {exc}"})

    if use_deess:
        try:
            from modules.vocal_fx.desser import dynamic_deess

            audio, deess_report = dynamic_deess(audio, sample_rate)
            stages.append("deess")
        except Exception as exc:  # noqa: BLE001
            skipped.append({"stage": "deess", "reason": f"{type(exc).__name__}: {exc}"})

    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0.999:
        audio = audio / peak * 0.999
    try:
        sf.write(out_path, audio.astype(np.float32), sample_rate)
        return out_path, tune_report, deess_report
    except Exception as exc:  # noqa: BLE001
        skipped.append({"stage": "tune", "reason": f"write failed: {exc}"})
        return path, tune_report, deess_report


def _prosody_vocal(
    path: str,
    out_wav: str,
    *,
    bpm: float | None,
    stages: list[str],
    skipped: list[dict[str, str]],
) -> tuple[str, dict[str, Any] | None]:
    import numpy as np
    import soundfile as sf

    temp = _prosody_temp(out_wav)
    try:
        data, sample_rate = sf.read(path, always_2d=True)
        from modules.vocal_fx.prosody import process_prosody

        audio, report = process_prosody(
            np.asarray(data, dtype=np.float64), sample_rate, bpm=bpm
        )
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > 0.999:
            audio = audio / peak * 0.999
        sf.write(temp, audio.astype(np.float32), sample_rate)
        stages.append("prosody")
        return temp, report
    except Exception as exc:  # noqa: BLE001
        skipped.append({"stage": "prosody", "reason": f"{type(exc).__name__}: {exc}"})
        return path, None


def capability_report() -> dict[str, Any]:
    return {
        "numpy_soundfile": _OK,
        "real_double_possible": _OK,
        "real_throw_possible": _OK,
    }


if __name__ == "__main__":
    print(json.dumps(capability_report(), indent=2))
