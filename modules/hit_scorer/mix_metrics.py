# -*- coding: utf-8 -*-
"""
modules/hit_scorer/mix_metrics.py — метрики микса и формы: громкость (LUFS с
честной прованс-диагностикой), стерео-ширина, низ, читаемость вокала,
читаемость структуры и новизна звучания.
"""

from __future__ import annotations

import logging

from modules.hit_scorer.audio import (
    HAS_LIBROSA,
    HAS_PYLOUDNORM,
    HAS_SF,
    librosa,
    np,
    pyln,
    sf,
)
from modules.hit_scorer.hook_metrics import (
    _bpm_dance_fitness,
    _chorus_catchiness,
    _db,
    _drop_impact,
    _hook_energy,
    _hook_repeatability,
    _rms,
    _tiktok_hookability,
)

_LOG = logging.getLogger("modules.hit_scorer")


def _loudness_rms_estimate(y) -> tuple[float, float]:
    """Возвращает существующую RMS-based pseudo-LUFS оценку."""
    rms = _rms(y)
    dbfs = _db(rms)
    if -14.0 <= dbfs <= -10.0:
        score = 95.0
    elif -17.0 <= dbfs < -14.0:
        score = 75.0
    elif -10.0 < dbfs <= -7.0:
        score = 80.0
    elif -7.0 < dbfs <= -4.0:
        score = 60.0
    else:
        score = 40.0
    return score, dbfs


def _loudness_lufs_status(
    y, sr, stereo_path: str | None = None
) -> tuple[tuple[float, float], dict[str, str]]:
    """Возвращает loudness score и provenance optional pyloudnorm метрики.

    `y` — моно (так его отдаёт `_load_audio`), а интегрированная громкость
    стерео-трека в моно не равна: для этой связи LUFS = 10·lg(ΣE_LR / E_моно),
    и у мастера движка моно-сумма даёт ровно те же сэмплы, что и микс L/R,
    поэтому LUFS = 10·lg(2·(1+corr)·E_L/E_моно). Замер на живом мастере:
    стерео −14,0 LUFS (так его и свели), моно −17,9 — разница 3,9 дБ, и
    оценка честный мастер считала тихим.

    Если передан `stereo_path`, громкость меряется по настоящему стерео;
    иначе остаётся прежний путь по моно (и в провенансе это видно).
    """
    stereo = _load_stereo(stereo_path) if stereo_path else None
    if stereo is not None:
        st_y, st_sr = stereo
        result, provenance = _measure_lufs(st_y, st_sr)
        if provenance.get("engine") == "pyloudnorm":
            provenance["channels"] = int(st_y.shape[1])
            return result, provenance
    return _measure_lufs(y, sr)


def _load_stereo(path: str | None):
    """Прочитать файл как стерео для замера громкости (или None)."""
    if not path or not HAS_SF or np is None:
        return None
    try:
        data, sr = sf.read(path, always_2d=True)
    except Exception:
        return None
    y = np.asarray(data, dtype=np.float64)
    if y.ndim != 2 or y.shape[1] < 2 or y.size == 0:
        return None
    return y[:, :2], int(sr)


def _measure_lufs(y, sr) -> tuple[tuple[float, float], dict[str, str]]:
    if np is None:
        return (60.0, -14.0), {"engine": "default_estimate", "status": "unavailable"}
    if HAS_PYLOUDNORM:
        try:
            # Обычно моно из _load_audio; стерео приходит из _load_stereo,
            # когда громкость меряется по файлу, а не по моно-сумме.
            meter = pyln.Meter(sr)
            lufs = float(meter.integrated_loudness(y))
            # Для LUFS таргет обычно -14..-9
            if -14.0 <= lufs <= -9.0:
                score = 98.0
            elif -16.0 <= lufs < -14.0:
                score = 80.0
            elif -9.0 < lufs <= -7.0:
                score = 85.0
            else:
                score = 50.0
            return (score, lufs), {"engine": "pyloudnorm"}
        except Exception as exc:
            _LOG.warning("pyloudnorm analysis failed; using RMS estimate: %s", exc)
            estimate = _loudness_rms_estimate(y)
            return estimate, {
                "engine": "rms_estimate",
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
    return _loudness_rms_estimate(y), {"engine": "rms_estimate", "status": "unavailable"}


def _loudness_lufs(y, sr) -> tuple[float, float]:
    """Совместимый loudness API без изменения score/raw tuple контракта."""
    return _loudness_lufs_status(y, sr)[0]


def _stereo_width(path: str) -> tuple[float, float]:
    """Требуется стерео-файл. Считает корреляцию каналов."""
    if not HAS_SF or np is None:
        return 60.0, 1.0
    try:
        y, _ = sf.read(path, always_2d=True)
        if y.shape[1] < 2:
            return 30.0, 1.0
        l, r = y[:, 0], y[:, 1]
        corr = float(np.corrcoef(l, r)[0, 1])
        if np.isnan(corr):  # один канал в тишине — это не картинка
            return 40.0, 1.0
        # Шкала различает не только «норма / не норма»: раньше всё, что шире
        # 0,55, получало одну и ту же 70,0 — и «широко, но в фазе», и каналы,
        # разъехавшиеся почти в противофазу. Теперь промежуточные ступени.
        if 0.55 <= corr <= 0.85:
            score = 90.0
        elif 0.40 <= corr < 0.55:
            score = 74.0  # широко, но в фазе
        elif 0.20 <= corr < 0.40:
            score = 56.0  # слишком широко: микс разваливается в моно
        elif corr < 0.20:
            score = 34.0  # каналы почти противофазны
        elif corr < 0.95:
            score = 65.0
        else:
            score = 40.0  # почти моно
        return score, corr
    except Exception:
        return 60.0, 1.0


def _low_end_power(y, sr) -> tuple[float, float]:
    """Сколько в миксе саба — по доле энергии, а не по сырому отношению.

    Раньше считалось отношение средних амплитуд STFT низа (20–80 Гц) к
    середине (200–2000 Гц), и любое отношение больше 1,3 получало ровно
    70,0. У живых битов движка это отношение 6,6–7,5 у phonk, trap, house,
    lo_fi, drill и hyperpop — то есть вырожденная ветка была обычным путём:
    саб на +24 дБ и саб, утопленный в ноль, оценивались одинаково.

    Сырое отношение к тому же несравнимо между жанрами: линейный STFT и
    разная ширина полос делают его произвольным (у «только саб» 1826).
    Поэтому считаем долю энергии ниже 120 Гц в общей энергии микса и
    смотрим, где лежит сама середина: у dance/trap низ живёт в 40–80 Гц, и
    микс без ничего ниже 100 Гц — это уже не «мало саба», а его отсутствие.

    Возвращает `(баллы, доля низа)`. Доля — честное число, по ней видно,
    нормальный саб у трека или его нет.
    """
    if not HAS_LIBROSA:
        return 60.0, 0.0
    try:
        S = np.abs(librosa.stft(y, n_fft=2048)) ** 2
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        # Ниже 120 Гц: саб и основной удар бас-бочки. Полосу ниже 20 Гц
        # выбрасываем — там только постоянка и инфразвук.
        duck = (freqs >= 20) & (freqs < 120)
        share = float(S[duck, :].sum() / max(S.sum(), 1e-12))

        # Где лежит энергия саба: настоящий 808 смещён к 40–80 Гц, а не к 20.
        band = S[duck, :].sum(axis=1)
        peak_hz = float(freqs[duck][int(np.argmax(band))]) if duck.any() else 0.0

        # Границы сняты с живых мастеров движка: у восьми жанров доля низа
        # 0,48–0,67 (у dnb 0,67 — это не «гул», а жанр). Поэтому «нормально»
        # широкое, а наказывается то, что действительно ломает микс: низа нет
        # вовсе или в нём почти вся энергия трека.
        if 0.10 <= share <= 0.70 and 30.0 <= peak_hz <= 90.0:
            score = 92.0
        elif 0.10 <= share <= 0.70:
            score = 78.0  # доля нормальная, но центр саба не тот
        elif 0.04 <= share < 0.10:
            score = 64.0  # саба мало
        elif 0.70 < share <= 0.80:
            score = 62.0  # саб перевешивает микс
        elif share < 0.04:
            score = 30.0  # низа нет: микс из одной середины
        else:
            score = 38.0  # больше 80 % энергии в низе — это гул, а не микс
        return score, share
    except Exception:
        return 60.0, 0.0


def _distortion(y, sr) -> tuple[float, float]:
    """Сколько сэмплов упёрлось в потолок: клиппинг — это брак, а не стиль.

    Замер на настоящем бите: `клиппинг ×6` давал −0,12 балла к оценке хита,
    то есть трек, вдавленный в потолок, проходил как чистый. Здесь считается
    доля сэмплов у потолка и «плоских» верхушек: у клиппированного сигнала
    соседние сэмплы равны максимуму, у чистого — нет.
    """
    if np is None or y is None or len(y) == 0:
        return 60.0, {"clipped_share": 0.0, "flat_top_share": 0.0}
    peak = float(np.max(np.abs(y)))
    if peak <= 0.0:
        return 60.0, {"clipped_share": 0.0, "flat_top_share": 0.0}
    # Потолок — это 0 dBFS (−0.2 дБ), а не максимум файла. Считать от
    # максимума нельзя: `librosa.load` ресемплит на 22050, и кольцевые
    # артефакты передискретизации уходят выше 1.0 (замер: пик 1.25 у
    # клиппированного бита). Тогда «потолок» уезжал вместе с ними, и реальный
    # клиппинг давал долю 1e-05 вместо 0.63.
    ceiling = min(0.977, peak * 0.977)
    at_ceiling = np.abs(y) >= ceiling
    clipped_share = float(np.mean(at_ceiling))
    # Плоские верхушки: два сэмпла подряд на потолке. В чистом сигнале такое
    # почти не встречается, у клиппированного — на каждом пике.
    flat = at_ceiling[1:] & at_ceiling[:-1]
    flat_share = float(np.mean(flat)) if flat.size else 0.0
    bad = max(clipped_share - 0.005, 0.0) + flat_share
    score = float(max(0.0, min(100.0, 100.0 - bad * 900.0)))
    return score, {"clipped_share": round(clipped_share, 5), "flat_top_share": round(flat_share, 5)}


def _vocal_presence(y, sr) -> tuple[float, float]:
    if not HAS_LIBROSA:
        return 60.0, 0.0
    try:
        S = np.abs(librosa.stft(y, n_fft=2048))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        voc_mask = (freqs >= 2000) & (freqs <= 5000)
        all_energy = float(S.mean())
        voc_energy = float(S[voc_mask, :].mean())
        ratio = voc_energy / max(all_energy, 1e-9)
        score = min(100.0, ratio * 90.0 + 25.0)
        return score, ratio
    except Exception:
        return 60.0, 0.0


def _structure_clarity(y, sr) -> tuple[float, int]:
    """Есть ли у трека секции — по сменам плотности, а не по порогу из головы.

    Как было: кривая RMS нормировалась (mean/std), искались точки, где
    |ΔRMS| > 1.2. При шаге STFT 1024 (≈46 мс) соседние кадры различаются на
    проценты, порог не достигался никогда — на ровном бите находилось 0
    смен, а на треке с контрастными секциями в тесте тоже 0. Метрика отдавала
    значение по умолчанию: 50,0 длинным трекам и 55,0 через исключение.

    Теперь трек делится на секции по 2 % длины (максимум 24, минимум 6), для
    каждой считается RMS, и структура оценивается по тому, сколько раз
    уровень меняется заметно (в 1.8 раза — это уже куплет/припев, а не
    колебания внутри секции) и насколько ровно держится уровень внутри
    секций. Ровный бит без секций получает низко, трек с контрастом — высоко.
    """
    if not HAS_LIBROSA or len(y) < sr * 20:
        return 55.0, 0
    try:
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=1024)[0]
        if rms.size < 8:
            return 55.0, 0
        sections = int(np.clip(round(rms.size * 0.02), 6, 24))
        levels = np.array(
            [float(np.mean(part)) for part in np.array_split(rms, sections)]
        )
        if levels.min() <= 1e-9:
            return 40.0, 0
        # Смена секции: соседние уровни различаются в 1.8 раза.
        ratio = np.maximum(levels[:-1], levels[1:]) / np.minimum(levels[:-1], levels[1:])
        changes = int(np.sum(ratio >= 1.8))
        # Ровность внутри секций: разброс уровней относительно среднего.
        jitter = float(np.std(ratio)) if ratio.size else 0.0
        score = 45.0 + 9.0 * min(changes, 4) - min(jitter, 2.0) * 5.0
        return round(float(np.clip(score, 20.0, 95.0)), 2), changes
    except Exception:
        return 55.0, 0


def _novelty(y, sr) -> tuple[float, float]:
    """Спектральное разнообразие трека — в человеческих единицах.

    Как было: `combined_var = (col_var + row_var·0.1)/1.1`,
    `score = min(100, combined_var·8e5 + 40)`. Дисперсия амплитуд STFT на
    настоящей музыке — порядка 10, поэтому `var·8e5` уходит в миллионы и
    `min(100, …)` даёт **100,0 всегда**: у восьми мастеров движка, у чистого
    синуса 440 Гц и у «одного клика в тишине». Метрика с весом 0,8 (6 %
    итогового балла) стояла в максимуме и сработать не могла.

    Теперь берётся профиль кадра (спектр, нормированный на громкость кадра —
    «краска», а не «громче/тише») и считается, насколько он гуляет во
    времени: среднее |профиль − средний профиль|, делённое на средний
    профиль. Замеры:

        чистое синусоида           0,03…0,05
        один такт по кругу         0,03
        белый шум                  0,40
        живые биты движка          0,70…0,87
        трек со свипом и сменой    1,26

    Шкала `100·(1 − e^(−rel/0.6))` — монотонная, без насыщения в максимум.
    """
    if not HAS_LIBROSA or np is None:
        return 60.0, 0.0
    try:
        S = np.abs(librosa.stft(y, n_fft=2048))
        if S.size == 0:
            return 40.0, 0.0
        energy = np.sum(S, axis=0, keepdims=True) + 1e-9
        profile = np.log1p(S / energy * 100.0)
        step = max(profile.shape[1] // 200, 1)
        profile = profile[:, ::step]
        mean = profile.mean(axis=1, keepdims=True)
        spread = float(np.mean(np.abs(profile - mean)))
        relative = spread / max(float(np.mean(np.abs(mean))), 1e-9)
        score = 100.0 * (1.0 - float(np.exp(-relative / 0.6)))
        return round(score, 2), round(relative, 3)
    except Exception:
        return 60.0, 0.0


def _metric_set(path: str, y, sr) -> dict:
    """Все метрики, которые не зависят от сборки отчёта.

    Вынесено из `score_track`: функция упиралась в бюджет 60 строк, а это
    ровно список независимых измерений — ему место рядом с самими метриками.
    Значения — `(score, raw)` или просто score, как их отдают функции выше.
    """
    tt_score, tt_slice = _tiktok_hookability(y, sr)
    loudness_result, loudness_provenance = _loudness_lufs_status(y, sr, stereo_path=path)
    return {
        "hook_energy": _hook_energy(y, sr),
        "hook_repeatability": _hook_repeatability(y, sr),
        "chorus_catchiness": _chorus_catchiness(y, sr),
        "drop_impact": _drop_impact(y, sr),
        "tiktok_hookability": (tt_score, tt_slice),
        "bpm_dance_fitness": _bpm_dance_fitness(y, sr),
        "loudness_lufs": loudness_result,
        "stereo_width": _stereo_width(path),
        "low_end_power": _low_end_power(y, sr),
        "vocal_presence": _vocal_presence(y, sr),
        "structure_clarity": _structure_clarity(y, sr),
        "novelty": _novelty(y, sr),
        "distortion": _distortion(y, sr),
        "_provenance": {"loudness_lufs": loudness_provenance},
        "_slice": tt_slice,
    }
