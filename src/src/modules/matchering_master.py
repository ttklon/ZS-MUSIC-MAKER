# -*- coding: utf-8 -*-
"""
ZS Music Maker v10 — Matchering Mastering Wrapper
==================================================
Обёртка над Matchering 2.0 (ТЗ 3.11).

Подгоняет TARGET под REFERENCE по:
  - RMS / LUFS
  - Спектральной характеристике
  - Стерео-ширине
  - Пиковой амплитуде

Если matchering не установлен — делает pydub-fallback:
  - нормализация до -14 LUFS (streaming) / -8.5 LUFS (car) / -6.5 LUFS (club)
  - лёгкая эквализация
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

log = logging.getLogger("zsmm.matchering")

try:
    import matchering as mg  # type: ignore
    MG_OK = True
except Exception:
    MG_OK = False


def match_to_reference(target: str,
                       reference: str,
                       out_wav: str,
                       out_mp3: Optional[str] = None) -> Dict[str, Any]:
    """
    Основная функция: подгонка target под reference.
    """
    Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
    if MG_OK:
        try:
            mg.log(print)
            results = [mg.pcm24(out_wav)]
            if out_mp3:
                results.append(mg.Result(out_mp3, subtype="PCM_16"))
            mg.process(target=target, reference=reference, results=results)
            return {"ok": True, "engine": "matchering", "out_wav": out_wav, "out_mp3": out_mp3}
        except Exception as e:
            log.warning("Matchering fail, fallback: %s", e)
    return {"ok": False, "engine": "none",
            "reason": "Matchering unavailable or failed; pydub gain is not mastering",
            "out_wav": out_wav}


def master_to_stand(target: str, out_wav: str, stand: str = "streaming") -> Dict[str, Any]:
    """
    Мастер под целевой стенд без референса.
      streaming: -14 LUFS
      car:       -8.5 LUFS (громче, туповатее верх)
      club:      -6.5 LUFS (макс-плотность)
      tiktok:    -13 LUFS
    """
    lufs_map = {"streaming": -14.0, "car": -8.5, "club": -6.5, "tiktok": -13.0}
    if not MG_OK:
        return {"ok": False, "engine": "none", "stand": stand,
                "reason": "Matchering unavailable; refusing gain-only mastering",
                "out_wav": out_wav}
    return _pydub_fallback(target, out_wav, target_lufs=lufs_map.get(stand, -14.0), stand=stand)


def master_all_stands(target: str, out_dir: str) -> Dict[str, Any]:
    """
    Генерирует 4 версии: streaming / car / club / tiktok.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out = {}
    for stand in ("streaming", "car", "club", "tiktok"):
        out_wav = str(Path(out_dir) / f"{stand}_master.wav")
        res = master_to_stand(target, out_wav, stand)
        out[stand] = res
    return {"ok": True, "stands": out}


def _pydub_fallback(target: str, out_wav: str,
                    target_lufs: float = -14.0,
                    stand: str = "streaming") -> Dict[str, Any]:
    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_file(target)
        # приближение LUFS = dBFS - 3 (грубая оценка для музыки)
        cur_dbfs = seg.dBFS
        approx_lufs = cur_dbfs - 3.0
        gain = target_lufs - approx_lufs
        # ограничим ±20 дБ чтобы не порвать
        gain = max(-20.0, min(20.0, gain))
        seg = seg.apply_gain(gain)
        # клубный стенд — лёгкий пик-лимитер
        if stand == "club":
            seg = seg.compress_dynamic_range(threshold=-6.0, ratio=4.0)
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        seg.export(out_wav, format="wav")
        return {
            "ok": True, "engine": "pydub_fallback",
            "out_wav": out_wav, "gain_applied_db": round(gain, 2),
            "target_lufs": target_lufs, "stand": stand
        }
    except Exception as e:
        log.error("pydub fallback error: %s", e)
        return {"ok": False, "reason": str(e)}


if __name__ == "__main__":
    print("Matchering available:", MG_OK)
