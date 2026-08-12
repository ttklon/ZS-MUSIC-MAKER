"""
ZS Music Maker — modules/mastering.py (v27 P0 FIX — unified mastering entry)
============================================================================

Что чинит эта версия
--------------------
До v27 `app/core/orchestrator._stage_mastering` вызывал:

    from modules import mastering
    mastering.master_all_stands(mix_wav, out_dir, stands=stands)

Но модуля `modules/mastering.py` в проекте НЕ БЫЛО.
Существовали только:
  * `modules/matchering_master.py` — `master_all_stands(target, out_dir)`
     (без `stands=`, только 4 стенда, gain-only fallback без реальной EQ);
  * `modules/mastering_pro.py`     — `process_mastering(in, out, target_lufs)`;
  * `app/core/mastering_stands.py` — простая FFT-EQ по стендам.

Из-за отсутствия `modules.mastering` стадия мастеринга падала с
ImportError, оркестратор оставлял только `mix_ducked.wav`, а
`master_streaming.wav`, `hit_score`, `release/*` НИКОГДА не создавались.
Все три FAIL в smoke_v26 (master_stereo_preserved, master_loudness_target,
hit_score_improved) — прямые следствия этого одного отсутствующего файла.

Что делает `master_all_stands` теперь
-------------------------------------
1) Санитизирует список `stands` из recipe и всегда включает `streaming`
   (стадии polish / stems / hit / release читают именно его).
2) На каждый стенд:
   * применяет стенд-специфичную EQ (car/club/tiktok/airpods/bluetooth/
     headphones/monitors/streaming) в СТЕРЕО, без mono-downmix (было
     монофоличение → corr=1.0 весь мастер);
   * прогоняет `mastering_pro.process_mastering` (pedalboard chain +
     pyloudnorm с честным LUFS-таргетом на стенд, fallback → RMS);
   * пишет `masters/master_<stand>.wav` (плюс дубликат `<stand>_master.wav`
     для обратной совместимости со старыми утилитами).
3) Возвращает `{ok, engine, stands: {name: {ok, out_wav, target_lufs,
   engine, ...}}, summary: {ok, fallback}}` — формат, который ожидает
   `_stage_mastering` (там читается `r["summary"]["fallback"]`).

Fallback / BLOCKED-политика
---------------------------
* Если ни pedalboard, ни pyloudnorm недоступны — работает RMS-фоллбек
  (честно, помечен `fallback_used=True`, без вранья).
* Если сам input mix отсутствует — стадия возвращает `ok=False` без
  создания синтетических «мастеров».
* НЕ используем pydub gain-only «мастеринг» — он объявлен запрещённым
  в общих правилах проекта.

Baseline-железо (Xeon v2 / RX580 / 16GB RAM)
--------------------------------------------
Работает на CPU, никаких GPU-зависимостей. Основной cost — pedalboard
+ pyloudnorm, оба лёгкие. При отказе — RMS.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

# ---------------------------------------------------------------------------
# Целевые LUFS на стенд (сдвиг +0.5 dB унаследован из v26 после калибровки
# hit_scorer — не трогать без пересчёта регрессионных smoke).
# ---------------------------------------------------------------------------
STAND_LUFS: dict[str, float] = {
    "streaming":  -13.5,   # DSP/YouTube/Spotify sweet-spot после калибровки
    "car":         -8.5,   # громко, для машин / TikTok car edits
    "club":        -6.5,   # максимальная плотность, клубный дроп
    "tiktok":     -12.5,   # TikTok / Reels — чуть громче streaming
    "airpods":    -13.0,   # true-wireless — компенсация bass roll-off
    "bluetooth":  -12.5,   # общий bluetooth (colonки, наушники)
    "headphones": -14.0,   # проводные, HD580-style — самый нейтральный
    "monitors":   -13.5,   # студийные мониторы, near-field
}

VALID_STANDS: set[str] = set(STAND_LUFS.keys())


# ---------------------------------------------------------------------------
# Стенд-специфичная стерео-EQ через FFT. Работает раздельно по L/R,
# что сохраняет реальный stereo image (в отличие от старого
# app/core/mastering_stands.py, который делал mono-downmix и разрушал
# stereo_width, полученный beat_constructor.v26).
# ---------------------------------------------------------------------------

def _stand_gain_curve(freqs: np.ndarray, stand: str) -> np.ndarray:
    """Возвращает мультипликативную gain-кривую по спектру для стенда."""
    g = np.ones_like(freqs, dtype=np.float32)
    if stand == "car":
        g[(freqs >= 30) & (freqs <= 80)]   *= 1.60
        g[(freqs >= 80) & (freqs <= 200)]  *= 1.20
        g[freqs > 10_000]                  *= 0.85
    elif stand == "club":
        g[(freqs >= 40)  & (freqs <= 120)] *= 1.80
        g[(freqs >= 2000) & (freqs <= 5000)] *= 1.15
        g[freqs > 12_000]                  *= 0.90
    elif stand == "streaming":
        g[(freqs >= 60)  & (freqs <= 100)] *= 1.05
        g[(freqs >= 5000) & (freqs <= 10000)] *= 0.90
    elif stand == "tiktok":
        g[freqs < 40]                      *= 0.50
        g[(freqs >= 200) & (freqs <= 500)] *= 1.15
        g[(freqs >= 3000) & (freqs <= 6000)] *= 1.20
    elif stand == "airpods":
        g[(freqs >= 50)  & (freqs <= 120)] *= 1.25
        g[(freqs >= 8000) & (freqs <= 12000)] *= 0.90
    elif stand == "bluetooth":
        g[(freqs >= 100) & (freqs <= 300)] *= 1.10
        g[(freqs >= 6000) & (freqs <= 9000)] *= 0.92
    elif stand == "headphones":
        g[(freqs >= 8000) & (freqs <= 14000)] *= 1.05
    elif stand == "monitors":
        g[freqs < 25]                      *= 0.30
    return g


def _apply_stand_eq_stereo(y: np.ndarray, sr: int, stand: str) -> np.ndarray:
    """FFT-EQ на СТЕРЕО (per-channel), сохраняя stereo image."""
    if y.ndim == 1:
        y = np.stack([y, y], axis=1)
    out = np.empty_like(y, dtype=np.float32)
    for ch in range(y.shape[1]):
        x = y[:, ch].astype(np.float32)
        Y = np.fft.rfft(x)
        freqs = np.fft.rfftfreq(len(x), 1.0 / sr)
        curve = _stand_gain_curve(freqs, stand)
        y2 = np.fft.irfft(Y * curve, n=len(x)).astype(np.float32)
        out[:, ch] = y2
    # v27.1: headroom -6 dBFS перед mastering_pro — иначе limiter упирается
    # раньше pyloudnorm и оставляет LUFS ниже таргета (v27.0 давал -16 при
    # target -13.5). Пик ставим 0.5 → +6 dB запаса.
    peak = float(np.max(np.abs(out))) + 1e-9
    if peak > 0.5:
        out = out * (0.5 / peak)
    return out


# ---------------------------------------------------------------------------
# Основная точка входа — вызывается из
# app/core/orchestrator._stage_mastering
# ---------------------------------------------------------------------------

def master_all_stands(
    mix_wav: str,
    out_dir: str,
    stands: list[str] | None = None,
) -> dict[str, Any]:
    """Мастеринг микса под все выбранные стенды.

    Args:
        mix_wav: путь к финальному миксу (mix_ducked.wav из
                 _stage_mix_and_sidechain).
        out_dir: куда писать `masters/master_<stand>.wav`.
        stands:  список стендов из recipe / wizard; None = все восемь.
                 `streaming` включается автоматически (нужен для
                 polish/stems/hit/release).

    Returns:
        dict совместимый с ожиданиями _stage_mastering:
        {
          "ok": bool,
          "engine": "unified-v27",
          "stands": { name: {ok, out_wav, target_lufs, engine, ...} },
          "summary": {"ok": int, "fallback": int, "failed": int},
        }
    """
    if not mix_wav or not os.path.exists(mix_wav):
        return {
            "ok": False,
            "engine": "unified-v27",
            "reason": f"input mix not found: {mix_wav}",
            "stands": {},
            "summary": {"ok": 0, "fallback": 0, "failed": 1},
        }

    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    # -- Санитизация списка стендов ------------------------------------------------
    if stands:
        chosen = [s for s in stands if s in VALID_STANDS]
    else:
        chosen = list(VALID_STANDS)
    if "streaming" not in chosen:
        chosen.insert(0, "streaming")

    try:
        y_mix, sr = sf.read(mix_wav, always_2d=True)
    except Exception as e:
        return {
            "ok": False,
            "engine": "unified-v27",
            "reason": f"failed to read mix: {e}",
            "stands": {},
            "summary": {"ok": 0, "fallback": 0, "failed": 1},
        }

    if y_mix.dtype != np.float32:
        y_mix = y_mix.astype(np.float32) / (
            np.iinfo(y_mix.dtype).max if np.issubdtype(y_mix.dtype, np.integer) else 1.0
        )

    # -- Отложенный импорт mastering_pro --------------------------------------
    try:
        from modules import mastering_pro
        _has_pro = True
    except Exception as e:
        mastering_pro = None  # type: ignore[assignment]
        _has_pro = False
        _pro_reason = str(e)
    else:
        _pro_reason = ""

    results: dict[str, dict[str, Any]] = {}
    stats = {"ok": 0, "fallback": 0, "failed": 0}

    for stand in chosen:
        target_lufs = STAND_LUFS.get(stand, -14.0)
        # 1) стенд-специфичная EQ (in-memory, стерео сохраняется)
        try:
            y_eq = _apply_stand_eq_stereo(y_mix, sr, stand)
        except Exception as e:
            results[stand] = {
                "ok": False,
                "stand": stand,
                "reason": f"EQ failed: {e}",
                "target_lufs": target_lufs,
            }
            stats["failed"] += 1
            continue

        stand_out = str(out_root / f"master_{stand}.wav")
        tmp_eq = str(out_root / f"_tmp_eq_{stand}.wav")
        try:
            sf.write(tmp_eq, y_eq, sr, subtype="FLOAT")
        except Exception as e:
            results[stand] = {
                "ok": False,
                "stand": stand,
                "reason": f"tmp EQ write failed: {e}",
                "target_lufs": target_lufs,
            }
            stats["failed"] += 1
            continue

        # 2) mastering_pro на выходе EQ, либо RMS-фоллбек.
        stand_res: dict[str, Any]
        if _has_pro:
            try:
                r = mastering_pro.process_mastering(
                    tmp_eq, stand_out, target_lufs=target_lufs
                )
                if not isinstance(r, dict) or not r.get("ok"):
                    raise RuntimeError(
                        f"mastering_pro returned non-ok: {r!r}"
                    )
                stand_res = {
                    "ok": True,
                    "stand": stand,
                    "out_wav": stand_out,
                    "target_lufs": target_lufs,
                    "engine": r.get("engine", "mastering_pro"),
                    "input_lufs": r.get("input_lufs"),
                    "fallback_used": "rms" in str(r.get("engine", "")),
                }
                if stand_res["fallback_used"]:
                    stats["fallback"] += 1
                stats["ok"] += 1
            except Exception as e:
                stand_res = _rms_fallback(y_eq, sr, stand_out, target_lufs, stand, str(e))
                if stand_res.get("ok"):
                    stats["ok"] += 1
                    stats["fallback"] += 1
                else:
                    stats["failed"] += 1
        else:
            stand_res = _rms_fallback(
                y_eq, sr, stand_out, target_lufs, stand,
                f"mastering_pro import failed: {_pro_reason}",
            )
            if stand_res.get("ok"):
                stats["ok"] += 1
                stats["fallback"] += 1
            else:
                stats["failed"] += 1

        # Backward-compat alias — старые утилиты читают `<stand>_master.wav`.
        try:
            legacy = out_root / f"{stand}_master.wav"
            if not legacy.exists() and Path(stand_out).exists():
                import shutil
                shutil.copyfile(stand_out, legacy)
        except Exception:
            pass

        # hit_score / release читают `master_streaming.wav`.
        if stand == "streaming":
            try:
                import shutil
                shutil.copyfile(stand_out, str(out_root / "master.wav"))
            except Exception:
                pass

        try:
            os.remove(tmp_eq)
        except Exception:
            pass

        results[stand] = stand_res

    overall_ok = stats["ok"] > 0
    return {
        "ok": overall_ok,
        "engine": "unified-v27",
        "stands": results,
        "summary": stats,
        "streaming_master": str(out_root / "master_streaming.wav"),
    }


def _rms_fallback(
    y_eq: np.ndarray,
    sr: int,
    stand_out: str,
    target_lufs: float,
    stand: str,
    reason: str,
) -> dict[str, Any]:
    """Честный RMS-фоллбек без pedalboard/pyloudnorm.

    Никакого «pydub gain-only мастеринга» — там нет ни EQ, ни лимитера,
    и правила проекта явно запрещают выдавать его за mastering.
    Здесь: RMS-нормализация к target_lufs (грубая аппроксимация LUFS =
    RMS_dBFS - 3) + soft tanh-limiter, стерео сохраняется.
    """
    try:
        y = y_eq.copy().astype(np.float32)
        rms = float(np.sqrt(np.mean(y * y))) + 1e-12
        current_dbfs = 20.0 * np.log10(rms)
        approx_lufs = current_dbfs - 3.0
        gain_db = target_lufs - approx_lufs
        gain_db = max(-24.0, min(18.0, gain_db))
        gain = 10.0 ** (gain_db / 20.0)
        y = y * gain
        y = np.tanh(y * 1.5) / 1.5
        peak = float(np.max(np.abs(y))) + 1e-9
        if peak > 0.94:
            y = y * (0.94 / peak)
        Path(stand_out).parent.mkdir(parents=True, exist_ok=True)
        sf.write(stand_out, y, sr, subtype="PCM_16")
        return {
            "ok": True,
            "stand": stand,
            "out_wav": stand_out,
            "target_lufs": target_lufs,
            "gain_db": round(gain_db, 2),
            "engine": "rms_tanh_fallback",
            "fallback_used": True,
            "reason": reason,
        }
    except Exception as e:
        return {
            "ok": False,
            "stand": stand,
            "target_lufs": target_lufs,
            "reason": f"rms fallback failed: {e} (root: {reason})",
        }


# ---------------------------------------------------------------------------
# CLI-only smoke: `python3 -m modules.mastering path/to/mix.wav`
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python3 -m modules.mastering <mix.wav> [out_dir]")
        sys.exit(2)
    mix = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) >= 3 else "output/mastering_smoke"
    r = master_all_stands(mix, out)
    print("ok:", r.get("ok"))
    print("summary:", r.get("summary"))
    for k, v in r.get("stands", {}).items():
        print(
            f"  {k:10s} ok={v.get('ok')} engine={v.get('engine')} "
            f"target={v.get('target_lufs')} → {v.get('out_wav')}"
        )
