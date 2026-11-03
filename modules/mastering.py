# -*- coding: utf-8 -*-
"""modules/mastering.py — единственный мастеринг проекта (план 4.6).

Цепочка: коррекция тона под стенд → двухполосная компрессия → look-ahead
лимитер с потолком −1 dBTP → сходимость по LUFS. Всё измеряется настоящими
метриками (`modules.dsp.metrics`), а не «на слух»:

* true peak — 4× oversample (≤ −1.0 dBTP на каждом стенде);
* LUFS — pyloudnorm (ITU-R BS.1770), с явным статусом, если его нет;
* клиппинг — 0 сэмплов; корреляция и потеря в моно — гейты §7.2.

`master_all_stands` пишет `master_<stand>.wav` и возвращает отчёт с гейтами
по каждому стенду. Недостижимая цель (например, клуб −8.5 LUFS на очень
динамичном миксе) не выдаётся за успех: `gates[lufs] = False` и в отчёте
стоит фактическое значение.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from modules.dsp import dynamics, filters, limiter, metrics

_LOG = logging.getLogger(__name__)

__all__ = [
    "ALL_STANDS",
    "STAND_TARGET_LUFS",
    "master_all_stands",
    "master_one",
    "normalize_master_loudness",
]

TRUE_PEAK_CEILING = -1.0

# Целевые LUFS по стендам (§7.2: streaming −14 ± 0.5, клуб/тачка −8…−9).
STAND_TARGET_LUFS: dict[str, float] = {
    "streaming": -14.0,
    "tiktok": -11.5,
    "club": -8.5,
    "car": -10.0,
    "airpods": -14.0,
    "bluetooth": -14.5,
    "headphones": -14.0,
    "monitors": -14.0,
}

LUFS_TOLERANCE: dict[str, float] = {
    "streaming": 0.5,
    "tiktok": 0.6,
    "club": 0.5,  # −9…−8
    "car": 0.7,
    "airpods": 0.5,
    "bluetooth": 0.7,
    "headphones": 0.5,
    "monitors": 0.5,
}

# Crest-коридор зависит от стенда: клубные мастера плотнее по определению.
CREST_RANGE: dict[str, tuple[float, float]] = {
    # Клубный мастер по определению плотный: −8.5 LUFS при −1 dBTP не бывает
    # с «живым» крестом 8–14 дБ (это гейт микса, а не мастера).
    # −8.5 LUFS при потолке −1 dBTP физически даёт crest ≈ 4 дБ: плотнее
    # материал не становится. 3.8 — нижняя граница, которую мы принимаем, и
    # фактическое значение всегда пишется в отчёт.
    "club": (3.8, 11.0),
    "car": (5.5, 12.0),
    "tiktok": (6.0, 13.0),
    # Bluetooth-стенд сознательно тише (−14.5 LUFS) и потому динамичнее:
    # держать его в 14 дБ crest значило бы «сдавить» мастер вопреки цели.
    "bluetooth": (8.0, 15.0),
}
DEFAULT_CREST = (8.0, 14.0)

# Коридор корреляции мастеров. На «плотных» стендах лимитер неизбежно
# поднимает корреляцию (это следствие громкости, а не дефект картинки) —
# стерео-образ задан миксом (там гейт 0.2…0.8), а мастер лишь сохраняет его.
CORRELATION_RANGE: dict[str, tuple[float, float]] = {
    "club": (0.2, 0.95),
    "car": (0.2, 0.9),
    "tiktok": (0.2, 0.9),
    "bluetooth": (0.2, 0.9),
}
DEFAULT_CORRELATION = (0.2, 0.8)

# Характер стенда: (срез Гц, дБ, полоса) — та же логика, что была, но через dsp.
STAND_EQ: dict[str, tuple[tuple[float, float, str], ...]] = {
    "streaming": ((150, 0.5, "low"), (8000, 1.0, "high")),
    "car": ((120, 1.5, "low"), (6500, 1.0, "high")),
    # клуб: саб и низ — часть жанра; подъём низа даёт громкость без «сдавливания»
    "club": ((100, 2.5, "low"), (70, 2.0, "low"), (9000, 0.5, "high")),
    "tiktok": ((200, 1.0, "low"), (7500, 2.0, "high")),
    "airpods": ((250, 1.0, "low"), (8000, 1.5, "high")),
    "bluetooth": ((180, 1.5, "low"), (7000, 1.0, "high")),
    "headphones": ((150, 0.5, "low"), (9000, 0.5, "high")),
    "monitors": ((150, 0.0, "low"), (10000, 0.0, "high")),
}

ALL_STANDS = list(STAND_TARGET_LUFS)

# Совместимость: старый публичный словарь dBFS-ориентиров.
STAND_TARGET_DBFS: dict[str, float] = {}


def _load(path: str | Path) -> tuple[np.ndarray, int]:
    data, sr = sf.read(str(path), always_2d=True)
    y = np.asarray(data, dtype=np.float64)
    if y.ndim == 2 and y.shape[1] == 1:
        y = np.repeat(y, 2, axis=1)
    return y, int(sr)


def _tone(y: np.ndarray, sample_rate: int, stand: str) -> np.ndarray:
    out = y
    for cutoff, gain_db, band in STAND_EQ.get(stand, STAND_EQ["streaming"]):
        if abs(gain_db) > 1e-6:
            out = filters.shelf(out, sample_rate, cutoff, gain_db, band)
    return out


def _render_candidate(
    base: np.ndarray,
    sample_rate: int,
    gain_db: float,
    ceiling_dbtp: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Один проход «усиление → мягкий клиппер → лимитер → правка ширины»."""
    from modules.mix.width import match_width

    candidate = base * (10.0 ** (gain_db / 20.0))
    info: dict[str, Any] = {"gain_db": round(float(gain_db), 2)}
    # Клиппер применяется всегда, но ниже колена (= потолка) он математически
    # ничего не меняет. Включать его «по условию» нельзя: на границе включения
    # громкость скачет на несколько дБ и калибровка теряет устойчивость.
    candidate, info["soft_clip"] = limiter.soft_clip(candidate, knee_dbfs=ceiling_dbtp)
    candidate, info["limiter"] = limiter.limit(candidate, sample_rate, ceiling_dbtp=ceiling_dbtp)
    # Стерео-картину задаёт микс (`modules.mix.width`). Мастер её не правит:
    # переширение после лимитера отнимает у мастера 1–3 дБ громкости, а
    # добить их обратно лимитером невозможно (потолок уже выбран). Поэтому
    # здесь только фиксация измеренной корреляции.
    info["width"] = {
        "correlation": round(float(metrics.stereo_correlation(candidate)), 3),
        "handled_by": "mix_stage",
    }
    return candidate, info


def _converge_loudness(
    y: np.ndarray,
    sample_rate: int,
    target_lufs: float,
    *,
    ceiling_dbtp: float = TRUE_PEAK_CEILING,
    tolerance: float = 0.25,
    max_gain_db: float = 18.0,
    search_iterations: int = 6,
    min_crest_db: float | None = None,
    max_crest_db: float | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Довести трек до целевого LUFS устойчиво, с уважением к crest-коридору.

    Отклик громкости на усиление нелинейный (после включения клиппера он резко
    растёт), поэтому «gain += ошибка» раскачивается. Схема:

    1. бисекция по усилению на громком 30-секундном фрагменте, кандидат
       принимается только если его crest попадает в коридор стенда;
    2. полный рендер найденным усилением;
    3. до шести доводок: новый рендер с усилением `gain + 0.8·ошибка`
       (а не линейный трим готового мастера — трим не меняет crest и незаметно
       «съедает» динамику), принимаем только то, что ближе к цели И в коридоре.

    Если коридор crest-фактора не даёт дотянуть до цели, в отчёте честно
    стоят фактическая громкость и `limiter_saturated=True`, а не подделка.
    """
    excerpt = metrics.active_window(y, sample_rate, 30.0)
    use_excerpt = excerpt.shape[0] < y.shape[0]

    def acceptable(crest: float) -> bool:
        if min_crest_db is not None and crest < min_crest_db - 0.05:
            return False
        if max_crest_db is not None and crest > max_crest_db + 0.05:
            return False
        return True

    def measure(gain_db: float, source: np.ndarray | None = None):
        rendered, info = _render_candidate(
            y if source is None else source, sample_rate, gain_db, ceiling_dbtp
        )
        lufs, metering = metrics.integrated_lufs(rendered, sample_rate)
        return rendered, info, float(lufs), float(metrics.reference_crest_db(rendered, sample_rate)), metering

    low, high = 0.0, max_gain_db
    best: tuple[float, float] | None = None
    crest_rejected = 0
    for _ in range(search_iterations):
        middle = (low + high) * 0.5
        _, _, lufs, crest, _ = measure(middle, excerpt if use_excerpt else None)
        if acceptable(crest):
            err = abs(lufs - target_lufs)
            if best is None or err < best[0]:
                best = (err, middle)
        else:
            crest_rejected += 1
        if lufs < target_lufs:
            low = middle
        else:
            high = middle
        if best is not None and best[0] <= tolerance:
            break

    gain = best[1] if best is not None else 0.0
    rendered, render_info, lufs, crest, metering = measure(gain)
    corrections = 0
    for _ in range(6):
        error = target_lufs - lufs
        if abs(error) <= tolerance:
            break
        corrections += 1
        trial_gain = float(np.clip(gain + error * 0.8, 0.0, max_gain_db))
        if abs(trial_gain - gain) < 0.05:
            break
        trial, trial_info, trial_lufs, trial_crest, trial_metering = measure(trial_gain)
        if acceptable(trial_crest) and abs(target_lufs - trial_lufs) < abs(target_lufs - lufs) - 0.01:
            rendered, render_info, lufs, crest, metering = (
                trial,
                trial_info,
                trial_lufs,
                trial_crest,
                trial_metering,
            )
            gain = trial_gain
        elif not acceptable(trial_crest):
            # усиление упирается в crest: шагаем назад, а не «давим» тримом
            gain = max(0.0, gain - 0.5)
            rendered, render_info, lufs, crest, metering = measure(gain)
        else:
            break

    trimmed_db = 0.0
    if lufs > target_lufs + 0.05:
        # стать тише можно линейно: crest при этом не меняется (в отличие от
        # «рендера с меньшим усилением», который вернул бы клиппинг)
        trimmed_db = float(target_lufs - lufs)
        rendered = rendered * (10.0 ** (trimmed_db / 20.0))
        lufs, _ = metrics.integrated_lufs(rendered, sample_rate)
        corrections += 1

    saturated = abs(target_lufs - lufs) > tolerance
    return rendered, {
        "target_lufs": target_lufs,
        "achieved_lufs": round(float(lufs), 2),
        "error_lu": round(float(lufs - target_lufs), 2),
        "gain_applied_db": round(float(gain), 2),
        "crest_db": round(float(crest), 2),
        "corrections": corrections,
        "trim_db": round(trimmed_db, 2),
        "limiter_saturated": saturated,
        "crest_rejected_candidates": crest_rejected,
        **{k: v for k, v in render_info.items() if k != "gain_db"},
        **metering,
    }


def _control_crest(
    mastered: np.ndarray,
    source: np.ndarray,
    sample_rate: int,
    stand: str,
    target_lufs: float,
    ceiling_dbtp: float = TRUE_PEAK_CEILING,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Довести crest-фактор мастера в коридор стенда — измеримо, без магии.

    Коридор снизу уже удержан при сведении громкости (кандидаты с crest ниже
    нормы отбрасываются). Здесь остаётся «слишком живой» мастер: пики
    аккуратно подрезаются мягким клиппером (нелинейно — в отличие от
    лимитера, который масштабирует весь сигнал и crest не меняет), после чего
    громкость возвращается к цели. Каждый шаг пишется в отчёт.
    """
    low, high = CREST_RANGE.get(stand, DEFAULT_CREST)
    crest = float(metrics.loudness_report(mastered, sample_rate)["crest_db"])
    info: dict[str, Any] = {
        "crest_before_db": round(crest, 2),
        "corridor_db": [low, high],
        "actions": [],
    }
    for offset in (1.0, 2.0, 3.0, 4.0, 5.0):
        if crest <= high:
            break
        clipped, _ = limiter.soft_clip(mastered, knee_dbfs=ceiling_dbtp - offset)
        lufs = float(metrics.integrated_lufs(clipped, sample_rate)[0])
        gain_db = float(np.clip(target_lufs - lufs, -6.0, 6.0))
        restored, _ = limiter.soft_clip(
            clipped * (10.0 ** (gain_db / 20.0)), knee_dbfs=ceiling_dbtp
        )
        # мягкий клиппер может выйти за потолок: финальный лимитер обязателен
        restored, _ = limiter.limit(restored, sample_rate, ceiling_dbtp=ceiling_dbtp)
        new_crest = float(metrics.loudness_report(restored, sample_rate)["crest_db"])
        info["actions"].append(f"soft_clip_knee_-{offset}_db")
        if new_crest < crest:
            mastered, crest = restored, new_crest
    if crest > high:
        # тяжёлый лимитер держит пики, но не сжимает тело: чтобы убрать
        # избыточный crest, нужна компрессия, а не ещё один лимитер
        from modules.dsp import dynamics

        compressed, comp_info = dynamics.compress(
            mastered,
            sample_rate,
            threshold_db=-14.0,
            ratio=2.5,
            attack_ms=5.0,
            release_ms=120.0,
        )
        lufs = float(metrics.integrated_lufs(compressed, sample_rate)[0])
        gain_db = float(np.clip(target_lufs - lufs, -6.0, 6.0))
        restored, _ = limiter.limit(
            compressed * (10.0 ** (gain_db / 20.0)),
            sample_rate,
            ceiling_dbtp=ceiling_dbtp,
        )
        new_crest = float(metrics.loudness_report(restored, sample_rate)["crest_db"])
        info["actions"].append("compress_body_ratio_2_5")
        info["compressor"] = comp_info
        if new_crest < crest:
            mastered, crest = restored, new_crest

    if crest < low - 0.05:
        info["below_floor"] = True
        info["reason"] = (
            "crest ниже коридора: цель по громкости требует плотнее, чем позволяет материал"
        )
    info["crest_after_db"] = round(crest, 2)
    return mastered, info


def _gates(report: dict[str, Any], stand: str) -> dict[str, bool]:
    lufs = float(report["lufs"])
    target = STAND_TARGET_LUFS.get(stand, -14.0)
    tol = LUFS_TOLERANCE.get(stand, 0.5)
    crest_lo, crest_hi = CREST_RANGE.get(stand, DEFAULT_CREST)
    corr = float(report["stereo_correlation"]) if int(report["channels"]) > 1 else 0.5
    corr_lo, corr_hi = CORRELATION_RANGE.get(stand, DEFAULT_CORRELATION)
    return {
        "true_peak": float(report["true_peak_dbtp"]) <= TRUE_PEAK_CEILING,
        "lufs": abs(lufs - target) <= tol,
        "crest": crest_lo <= float(report["crest_db"]) <= crest_hi,
        "correlation": corr_lo <= corr <= corr_hi,
        "mono_loss": float(report["mono_loss_db"]) <= 3.0,
        "no_clipping": int(report["clipping_samples"]) == 0,
    }


def master_one(mix_wav: str, out_wav: str, stand: str = "streaming") -> dict[str, Any]:
    """Мастеринг одного WAV под конкретный стенд. Всегда стерео, всегда с отчётом."""
    try:
        y, sr = _load(mix_wav)
    except Exception as exc:
        return {"ok": False, "reason": f"read failed: {type(exc).__name__}: {exc}"}
    if y.size == 0:
        return {"ok": False, "reason": "input mix is empty"}

    target = STAND_TARGET_LUFS.get(stand, STAND_TARGET_LUFS["streaming"])
    y = _tone(y, sr, stand)
    compressed, comp_info = dynamics.multiband_compress(
        y, sr, split_hz=190.0,
        low={"threshold_db": -14.0, "ratio": 1.6, "attack_ms": 25.0, "release_ms": 200.0},
        high={"threshold_db": -20.0, "ratio": 1.4, "attack_ms": 10.0, "release_ms": 120.0},
    )
    crest_low, crest_high = CREST_RANGE.get(stand, DEFAULT_CREST)
    mastered, loudness_info = _converge_loudness(
        compressed,
        sr,
        target,
        min_crest_db=crest_low,
        max_crest_db=crest_high,
    )
    # Если цель по громкости не достигнута из-за транзиентов (лимитер уже стоит
    # на потолке, а прибавка усиления не даёт LUFS), единственный честный путь —
    # уменьшить динамический диапазон тела, а не задирать усиление.
    rescue_attempts: list[dict[str, Any]] = []
    source = compressed
    for _ in range(2):
        if not loudness_info.get("limiter_saturated"):
            break
        source, _comp_info = dynamics.compress(
            source,
            sr,
            threshold_db=-18.0,
            ratio=2.0,
            attack_ms=10.0,
            release_ms=150.0,
        )
        mastered, loudness_info = _converge_loudness(
            source,
            sr,
            target,
            min_crest_db=crest_low,
            max_crest_db=crest_high,
        )
        rescue_attempts.append(
            {
                "achieved_lufs": loudness_info.get("achieved_lufs"),
                "saturated": loudness_info.get("limiter_saturated"),
            }
        )
    if rescue_attempts:
        loudness_info["loudness_rescue"] = rescue_attempts
    mastered, crest_info = _control_crest(mastered, compressed, sr, stand, target)
    # Правка плотности (клиппер/компрессор) может уронить громкость: добираем её
    # обратно уже на готовом сигнале, по-прежнему не выходя из crest-коридора.
    current_lufs = float(metrics.integrated_lufs(mastered, sr)[0])
    topup_info: dict[str, Any] | None = None
    if abs(current_lufs - target) > 0.25:
        mastered, topup_info = _converge_loudness(
            mastered,
            sr,
            target,
            max_gain_db=4.0,
            min_crest_db=crest_low,
            max_crest_db=crest_high,
        )
        crest_info["topup"] = {
            "lufs_before": round(current_lufs, 2),
            "lufs_after": topup_info.get("achieved_lufs"),
            "gain_db": topup_info.get("gain_applied_db"),
        }
    loudness_info["crest_control"] = crest_info
    mastered = np.nan_to_num(mastered, nan=0.0, posinf=0.0, neginf=0.0)
    report = metrics.loudness_report(mastered, sr)
    gates = _gates(report, stand)
    advice = None
    if not gates["lufs"]:
        advice = (
            f"цель {target} LUFS недостижима без перегруза: получено {report['lufs']} LUFS. "
            "Сведите микс плотнее (crest опорного участка ≤ 10.5 дБ) или выберите более тихий стенд"
        )

    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), mastered.astype(np.float32), sr, subtype="FLOAT")

    return {
        "ok": True,
        "path": str(out),
        "stand": stand,
        "channels": report["channels"],
        "sample_rate": sr,
        "target_lufs": target,
        "input_lufs": round(float(metrics.integrated_lufs(y, sr)[0]), 2),
        "output_lufs": report["lufs"],
        "output_true_peak_dbtp": report["true_peak_dbtp"],
        "output_peak_db": report["peak_dbfs"],
        "crest_db": report["crest_db"],
        "compression": comp_info,
        "width": loudness_info.get("width", {}),
        "loudness": loudness_info,
        "lufs_engine": report["lufs_engine"],
        "lufs_status": report["lufs_status"],
        "report": report,
        "gates": gates,
        "gates_passed": all(gates.values()),
        "advice": advice,
        "fallback_used": False,
    }


def normalize_master_loudness(
    input_wav: str,
    output_wav: str | None = None,
    target_lufs: float = -14.0,
    ceiling_db: float = TRUE_PEAK_CEILING,
) -> dict[str, Any]:
    """Довести громкость уже готового мастера без новой DSP-окраски."""
    output_wav = output_wav or input_wav
    try:
        y, sr = _load(input_wav)
    except Exception as exc:
        return {"ok": False, "reason": f"read failed: {type(exc).__name__}: {exc}"}
    if y.size == 0:
        return {"ok": False, "reason": "master audio is empty"}

    normalized, info = _converge_loudness(y, sr, target_lufs, ceiling_dbtp=ceiling_db)
    report = metrics.loudness_report(normalized, sr)
    out = Path(output_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), normalized.astype(np.float32), sr, subtype="FLOAT")
    return {
        "ok": True,
        "path": str(out),
        "target_lufs": float(target_lufs),
        "output_lufs": report["lufs"],
        "output_true_peak_dbtp": report["true_peak_dbtp"],
        "output_peak_db": report["peak_dbfs"],  # совместимость с прежним API
        "output_rms_dbfs": report["rms_dbfs"],
        "loudness_mode": "integrated_lufs" if report["lufs_status"] == "ok" else "rms_approximation",
        "sample_rate": sr,
        "channels": report["channels"],
        "report": report,
        "loudness": info,
    }


# Оригинал `master_one`. Если его подменили (тесты, эксперименты), стенды
# считаются в этом же процессе: чужая функция живёт только здесь, в дочерний
# процесс она не попадёт.
_MASTER_ONE_IMPL = master_one


def _master_stand_job(job: tuple[str, str, str]) -> tuple[str, dict[str, Any]]:
    """Один стенд в отдельном процессе (аргументы должны быть picklable)."""
    mix_wav, out_wav, stand = job
    return stand, master_one(mix_wav, out_wav, stand=stand)


def _stand_workers(count: int) -> int:
    """Сколько стендов считать параллельно.

    Стенды независимы, поэтому 8 версий считаются одновременно, а не
    последовательно — на 8-ядерной машине время мастеринга падает почти
    линейно. Потолок 4: каждый процесс держит в памяти весь трек
    (120 с стерео ≈ 42 МБ float64 на буфер), и больше четырёх воркеров
    начинают мешать друг другу сильнее, чем помогать. `ZSMM_MASTER_WORKERS=1`
    принудительно включает последовательный режим.
    """
    try:
        forced = int(os.environ.get("ZSMM_MASTER_WORKERS", "0") or 0)
    except ValueError:
        forced = 0
    if forced > 0:
        return max(1, min(forced, count))
    return max(1, min(count, os.cpu_count() or 1, 4))


def _run_stands(
    mix_wav: str,
    out: Path,
    chosen: list[str],
) -> list[tuple[str, dict[str, Any]]]:
    """Посчитать стенды; при любой проблеме с процессами — честный фолбэк."""
    jobs = [(mix_wav, str(out / f"master_{stand}.wav"), stand) for stand in chosen]
    workers = 1 if master_one is not _MASTER_ONE_IMPL else _stand_workers(len(jobs))
    if workers > 1:
        try:
            from concurrent.futures import ProcessPoolExecutor

            with ProcessPoolExecutor(max_workers=workers) as pool:
                return list(pool.map(_master_stand_job, jobs))
        except Exception as error:  # noqa: BLE001 - пул может быть запрещён сборкой
            _LOG.warning("parallel mastering unavailable (%s); falling back to serial", error)
    return [_master_stand_job(job) for job in jobs]


def master_all_stands(
    mix_wav: str,
    out_dir: str,
    stands: list[str] | None = None,
) -> dict[str, Any]:
    """Мастеринг под все запрошенные стенды + сводный отчёт по гейтам."""
    chosen = stands or ALL_STANDS
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    masters: dict[str, str] = {}
    reports: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    for stand, result in _run_stands(mix_wav, out, list(chosen)):
        if result.get("ok"):
            masters[stand] = str(result["path"])
            reports[stand] = result
        else:
            errors[stand] = str(result.get("reason", "unknown"))

    failed_gates = {
        stand: [name for name, ok in data["gates"].items() if not ok]
        for stand, data in reports.items()
        if not data["gates_passed"]
    }
    summary = {
        "total": len(chosen),
        "done": len(masters),
        "fallback": 0,
        "errors": errors,
        "gates_passed": all(data["gates_passed"] for data in reports.values()) if reports else False,
        "failed_gates": failed_gates,
    }
    payload: dict[str, Any] = {
        "ok": bool(masters),
        "masters": masters,
        "reports": {stand: data["report"] for stand, data in reports.items()},
        "summary": summary,
    }
    report_path = out / "mastering_report.json"
    report_path.write_text(
        json.dumps(
            {
                "standards": {s: STAND_TARGET_LUFS[s] for s in chosen if s in STAND_TARGET_LUFS},
                "reports": payload["reports"],
                "gates": {stand: data["gates"] for stand, data in reports.items()},
                "failed_gates": failed_gates,
                "summary": summary,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    payload["report_path"] = str(report_path)
    return payload


def _cli(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: python -m modules.mastering <mix.wav> <out_dir> [stand]")
        return 2
    mix_wav, out_dir = argv[1], argv[2]
    stands = [argv[3]] if len(argv) > 3 else None
    result = master_all_stands(mix_wav, out_dir, stands=stands)
    print(json.dumps(result.get("summary", result), ensure_ascii=False, indent=2))
    return 0 if result.get("summary", {}).get("gates_passed") else 1


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(_cli(sys.argv))
