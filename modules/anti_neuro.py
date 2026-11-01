# -*- coding: utf-8 -*-
"""modules/anti_neuro.py — вокальная «не-нейроношная» полировка вокала (4.7).

Одна реализация на numpy + soundfile: pydub/ffmpeg здесь не нужен (на чистой
Windows-машине ffmpeg отсутствует, и старая pydub-ветка молча уходила в
fallback). Все стадии детерминированы по `seed` и **не меняют длину трека** —
вокальный файл должен оставаться на сетке микса.

Стадии (выбираются пресетом):

* ``consonant_boost``     — +3 дБ к 3–10 кГц только в моменты атак: согласные
  читаются, «пластиковый» верх не поднимается;
* ``de_plastic``          — мягкий срез выше 15.5 кГц и лёгкое сглаживание
  ультразвукового «шипения» нейросетевого синтеза;
* ``human_error``         — редкие микропровалы уровня (−6…−10 дБ, 40 мс,
  3 % шанс) и микро-детюн: живой вокал никогда не идеален;
* ``breaths_in_pauses``   — вдохи добавляются **в существующие паузы** между
  фразами (аддитивно, длина сохраняется), а не клеятся в начало файла;
* ``entropy_boost``       — у второй половины трека подрезается низ ниже 120 Гц:
  «второй куплет» перестаёт быть копией первого, но без сдвига тайминга.

Трековая пост-обработка микса живёт отдельно — `modules.anti_neuro_track`.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

__all__ = ["PRESETS", "polish_vocal", "apply_polish", "capability_report"]

try:
    import numpy as np
    import soundfile as sf

    NP_OK = True
except Exception:  # pragma: no cover - soundfile в зависимостях проекта
    np = None
    sf = None
    NP_OK = False

PRESETS: dict[str, tuple[str, ...]] = {
    "gentle": ("consonant_boost",),
    "standard": ("consonant_boost", "de_plastic", "human_error", "breaths_in_pauses"),
    "aggressive": (
        "consonant_boost",
        "de_plastic",
        "human_error",
        "breaths_in_pauses",
        "entropy_boost",
    ),
}


def _read(path: str | Path) -> tuple[Any, int]:
    data, sample_rate = sf.read(str(path), always_2d=True)
    return np.asarray(data, dtype=np.float64), int(sample_rate)


def _write(path: str | Path, audio: Any, sample_rate: int) -> None:
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0.999:
        audio = audio / peak * 0.999
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio.astype(np.float32), sample_rate)


def _band(audio: Any, sample_rate: int, low: float, high: float | None) -> Any:
    """Нулевая фаза, идеальная полоса (FFT): сумма полос = исходник."""
    from modules.vocal_fx.desser import _band as band_split

    return band_split(audio, sample_rate, low, high if high is not None else sample_rate / 2 * 0.98)


def _consonant_boost(audio: Any, sample_rate: int, rng: random.Random) -> tuple[Any, dict[str, Any]]:
    """Поднять верх только на атаках (по огибающей ВЧ), не в теле гласных."""
    air = _band(audio, sample_rate, 3000.0, 10000.0)
    envelope = np.max(np.abs(air), axis=1)
    from scipy.signal import lfilter

    smooth = lfilter([0.002], [1.0, -0.998], envelope)
    threshold = float(np.percentile(smooth, 80)) if smooth.size else 0.0
    mask = np.clip((smooth - threshold) / max(threshold, 1e-9), 0.0, 1.0)
    gain = 1.0 + (10.0 ** (3.0 / 20.0) - 1.0) * mask
    return audio + air * (gain[:, None] - 1.0), {
        "hi_boost_db": 3.0,
        "transient_only_pct": round(float(np.mean(mask > 0.5) * 100.0), 1),
    }


def _de_plastic(audio: Any, sample_rate: int) -> tuple[Any, dict[str, Any]]:
    """Срезать ультразвук нейросети и смягчить «стеклянный» верх."""
    high = _band(audio, sample_rate, 15500.0, None)
    cleaned = audio - high
    # мягкий «воздух»: возвращаем половину полосы, но без резкого края
    cleaned = cleaned + high * 0.5
    return cleaned, {"cut_from_hz": 15500.0, "kept_pct": 50.0}


def _human_error(audio: Any, sample_rate: int, rng: random.Random) -> tuple[Any, dict[str, Any]]:
    """Редкие микропровалы и микро-детюн: живая запись не бывает идеальной."""
    out = np.array(audio, copy=True)
    chunk = max(1, int(sample_rate * 0.04))
    dips = 0
    for start in range(0, max(1, out.shape[0] - chunk), chunk):
        if rng.random() < 0.03:
            depth_db = -6.0 - rng.random() * 4.0
            out[start : start + chunk] *= 10.0 ** (depth_db / 20.0)
            dips += 1
    detune_cents = rng.uniform(-4.0, 4.0)
    if abs(detune_cents) > 0.5:
        # лёгкий «плывущий» питч: ресемпл по коротким блокам с кроссфейдом
        out = _micro_detune(out, sample_rate, detune_cents)
    return out, {"micro_dips": dips, "detune_cents": round(detune_cents, 2)}


def _micro_detune(audio: Any, sample_rate: int, cents: float, block_sec: float = 0.25) -> Any:
    """Плавный сдвиг на несколько центов блоками с кроссфейдом (длина та же).

    Каждый блок читается с длиной `block · ratio` вокруг своего центра и
    укладывается обратно в те же `block` сэмплов: локальная высота меняется,
    таймлайн не плывёт, стыки сглажены окном Ханна (75 % перекрытие).
    """
    ratio = 2.0 ** (cents / 1200.0)
    block = max(64, int(block_sec * sample_rate))
    hop = max(8, block // 4)
    window = np.hanning(block + 2)[1:-1]
    out = np.zeros_like(audio)
    weight = np.zeros(audio.shape[0])
    for start in range(0, max(1, audio.shape[0]), hop):
        center = start + block // 2
        source_len = max(16, int(round(block * ratio)))
        source_start = center - source_len // 2
        indices = np.arange(source_start, source_start + source_len)
        clipped = np.clip(indices, 0, audio.shape[0] - 1)
        segment = audio[clipped]
        piece = np.stack(
            [
                np.interp(
                    np.linspace(0.0, segment.shape[0] - 1.0, block),
                    np.arange(segment.shape[0]),
                    segment[:, channel],
                )
                for channel in range(audio.shape[1])
            ],
            axis=1,
        )
        stop = min(audio.shape[0], start + block)
        length = stop - start
        if length <= 0:
            break
        out[start:stop] += piece[:length] * window[:length, None]
        weight[start:stop] += window[:length]
    return out / np.maximum(weight[:, None], 1e-3)


def _breaths_in_pauses(audio: Any, sample_rate: int, rng: random.Random) -> tuple[Any, dict[str, Any]]:
    """Добавить вдохи в паузы между фразами (аддитивно, длина та же)."""
    from modules.vocal_fx.prosody import detect_phrases

    phrases = detect_phrases(audio, sample_rate)
    if len(phrases) < 2:
        return audio, {"breaths": 0, "reason": "no pauses between phrases"}
    out = np.array(audio, copy=True)
    level = float(np.sqrt(np.mean(audio**2)) + 1e-9) * 10.0 ** (-18.0 / 20.0)
    inserted = 0
    for (_, previous_stop), (next_start, _) in zip(phrases[:-1], phrases[1:]):
        gap = next_start - previous_stop
        if gap < int(0.12 * sample_rate):
            continue
        length = min(int(0.16 * sample_rate), max(8, int(gap * 0.6)))
        rng_state = np.random.RandomState(rng.randrange(1 << 30))
        breath = rng_state.randn(length, audio.shape[1]) * level
        taper = np.hanning(length + 2)[1:-1][:, None]
        start = previous_stop + (gap - length) // 2
        out[start : start + length] += breath * taper
        inserted += 1
    return out, {"breaths": inserted, "level_rel_db": -18.0, "length_preserved": True}


def _entropy_boost(audio: Any, sample_rate: int) -> tuple[Any, dict[str, Any]]:
    """У второй половины подрезать низ: «второй куплет» ≠ копия первого."""
    out = np.array(audio, copy=True)
    middle = out.shape[0] // 2
    low = _band(out[middle:], sample_rate, 0.0, 120.0)
    out[middle:] = out[middle:] - low
    return out, {"mid_highpass_hz": 120.0}


def polish_vocal(
    vocal_wav: str, out_wav: str, preset: str = "standard", seed: int | None = None
) -> dict[str, Any]:
    """Полировать вокал (длина сохраняется) и вернуть честный отчёт по стадиям."""
    if not NP_OK:
        return {"ok": False, "reason": "numpy/soundfile unavailable", "engine": "none"}
    stages = PRESETS.get(preset, PRESETS["standard"])
    rng = random.Random(seed if seed is not None else 42)
    try:
        audio, sample_rate = _read(vocal_wav)
    except Exception as exc:  # noqa: BLE001 - вызывающий код должен увидеть причину
        return {"ok": False, "reason": f"read failed: {type(exc).__name__}: {exc}", "engine": "none"}
    if audio.size == 0:
        return {"ok": False, "reason": "input is empty", "engine": "none"}

    done: list[str] = []
    metrics: dict[str, Any] = {}
    skipped: list[dict[str, str]] = []
    for stage in stages:
        try:
            if stage == "consonant_boost":
                audio, info = _consonant_boost(audio, sample_rate, rng)
            elif stage == "de_plastic":
                audio, info = _de_plastic(audio, sample_rate)
            elif stage == "human_error":
                audio, info = _human_error(audio, sample_rate, rng)
            elif stage == "breaths_in_pauses":
                audio, info = _breaths_in_pauses(audio, sample_rate, rng)
            elif stage == "entropy_boost":
                audio, info = _entropy_boost(audio, sample_rate)
            else:
                skipped.append({"stage": stage, "reason": "unknown stage"})
                continue
            done.append(stage)
            metrics[stage] = info
        except Exception as exc:  # noqa: BLE001 - одна стадия не должна рушить цепочку
            skipped.append({"stage": stage, "reason": f"{type(exc).__name__}: {exc}"})

    if not done:
        return {
            "ok": False,
            "engine": "numpy_anti_neuro",
            "reason": "all vocal polish stages failed",
            "skipped": skipped,
        }

    _write(out_wav, audio, sample_rate)
    return {
        "ok": True,
        "engine": "numpy_anti_neuro",
        "preset": preset,
        "stages_applied": done,
        "skipped": skipped,
        "metrics": metrics,
        "length_preserved": bool(
            sf.info(str(out_wav)).frames == sf.info(str(vocal_wav)).frames
        ),
        "out_wav": out_wav,
        "path": out_wav,
        "sample_rate": sample_rate,
    }


def apply_polish(
    input_wav: str,
    out_wav: str,
    intensity: float = 0.5,
    preset: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """Совместимость с мастеринг-стадией: `intensity` → `preset`."""
    if preset is None:
        preset = "gentle" if intensity < 0.35 else ("standard" if intensity < 0.7 else "aggressive")
    result = polish_vocal(input_wav, out_wav, preset=preset, seed=seed)
    if isinstance(result, dict):
        result.setdefault("intensity", intensity)
    return result


def capability_report() -> dict[str, Any]:
    """Честный отчёт о цепочках: без «всё работает» по умолчанию."""
    from modules import anti_neuro_track

    return {
        "numpy_available": NP_OK,
        "ffmpeg_required": False,
        "vocal_chain": NP_OK,
        "track_chain": anti_neuro_track.NP_OK,
        "presets": sorted(PRESETS),
        "polish_track": callable(getattr(anti_neuro_track, "polish_track", None)),
    }
