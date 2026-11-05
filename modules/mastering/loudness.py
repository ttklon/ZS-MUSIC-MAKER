# -*- coding: utf-8 -*-
"""modules/mastering/loudness.py — сходимость по LUFS без «магии».

Ответ громкости на усиление нелинейный (после клиппера он растёт скачком),
поэтому здесь бисекция по усилению на активном фрагменте + доводки на полном
рендере. Всё, что делает этот файл, измеряется `modules.dsp.metrics`.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from modules.dsp import limiter, metrics
from modules.mastering.targets import TRUE_PEAK_CEILING


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
