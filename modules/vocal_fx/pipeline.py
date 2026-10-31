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
) -> dict[str, Any]:
    """Единая точка: clean -> double -> throw -> out. Возвращает dict-результат."""
    if not _OK:
        return {"ok": False, "engine": "none", "reason": "numpy/soundfile unavailable"}

    cur = vocal_wav
    stages: list[str] = []
    throws = 0
    tmp_clean = str(Path(out_wav).with_name("_vocal_clean_tmp.wav"))
    tmp_double = str(Path(out_wav).with_name("_fx_double_tmp.wav"))
    cleaner = None

    if clean_before_fx:
        try:
            from modules.voice_cleaner import clean_vocal_chain

            cleaner = clean_vocal_chain(cur, tmp_clean, genre=genre)
            if cleaner.get("ok"):
                cur = str(cleaner["path"])
                stages.append("clean")
        except Exception as exc:
            cleaner = {"ok": False, "reason": str(exc)}

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

    if stages == ["clean"]:
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
    for temporary in (tmp_clean, tmp_double):
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
        "cleanup_warnings": cleanup_warnings,
    }


def capability_report() -> dict[str, Any]:
    return {
        "numpy_soundfile": _OK,
        "real_double_possible": _OK,
        "real_throw_possible": _OK,
    }


if __name__ == "__main__":
    print(json.dumps(capability_report(), indent=2))
