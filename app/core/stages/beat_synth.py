# -*- coding: utf-8 -*-
"""
app/core/stages/beat_synth.py — процедурный синтез бита (fallback конструктора).

`_synth_beat` в `beat.py` занимал 258 строк: секции, драм-лейны, 808, ризеры,
стерео-расширение и запись файла жили в одной функции, хотя это независимые
шаги. Здесь те же шаги по отдельности — и тот же результат: набор паттернов,
уровни секций и моно-основа ниже 200 Гц сохранены побайтно, тесты на бит
проходят без изменения ожиданий.

Модуль не является «новым движком»: это тот же fallback, разложенный на
функции, каждая из которых умеет быть проверенной отдельно.
"""

from __future__ import annotations

from typing import Any

# Секционная структура: intro / verse / pre / chorus / verse / pre / chorus / outro.
BASE_SECTIONS = (
    ("intro", 4),
    ("verse", 8),
    ("pre", 4),
    ("chorus", 8),
    ("verse", 8),
    ("pre", 4),
    ("chorus", 8),
    ("outro", 4),
)

KEY_HZ = {
    "C": 261.63,
    "C#": 277.18,
    "D": 293.66,
    "D#": 311.13,
    "E": 329.63,
    "F": 349.23,
    "F#": 369.99,
    "G": 392.00,
    "G#": 415.30,
    "A": 440.00,
    "A#": 466.16,
    "B": 493.88,
}

# Паттерны (16 шагов). Припев ритмически плотнее куплета — иначе бит
# «формульный» и hit_scorer ставит needs_work.
KICK_PAT = [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0]
SNARE_PAT = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
HIHAT_PAT = [1] * 16
OPENHAT_STEP = 10
KICK_PAT_CHORUS = [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0]
KICK_PAT_VERSE = [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
HIHAT_PAT_CHORUS = [1] * 16
HIHAT_PAT_VERSE = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]

SECTION_GAINS = {
    "intro": (0.55, 0.0, 0.35, 0.4),
    "verse": (0.9, 0.75, 0.7, 0.85),
    "pre": (0.85, 0.7, 0.9, 0.8),
    "chorus": (1.0, 0.95, 0.75, 1.0),
    "outro": (0.7, 0.4, 0.5, 0.5),
}


def scale_sections(duration: float, bar_sec: float) -> list[tuple[str, int]]:
    """Подогнать структуру под запрошенную длительность."""
    sections = list(BASE_SECTIONS)
    total_bars = sum(nb for _, nb in sections)
    target_bars = max(4, int(round(duration / bar_sec)))
    if target_bars < total_bars:
        scale = target_bars / float(total_bars)
        return [(name, max(1, int(round(nb * scale)))) for name, nb in sections]
    if target_bars > total_bars * 1.4:
        extra = target_bars - total_bars
        return [(name, nb + (extra // 2 if name == "chorus" else 0)) for name, nb in sections]
    return sections


def _kick(np: Any, sr: int, dur: float = 0.16) -> Any:
    t = np.arange(int(sr * dur)) / sr
    f = 90.0 * np.exp(-t * 18) + 45.0
    env = np.exp(-t * 11)
    body = np.sin(2 * np.pi * np.cumsum(f) / sr) * env
    click = (
        np.random.randn(int(sr * 0.004)).astype("float32")
        * np.exp(-np.arange(int(sr * 0.004)) / sr * 400)
        * 0.6
    )
    out = body.astype("float32")
    out[: len(click)] += click * 0.35
    return out


def _snare(np: Any, sr: int, dur: float = 0.18) -> Any:
    t = np.arange(int(sr * dur)) / sr
    env = np.exp(-t * 17)
    noise = np.random.randn(len(t)).astype("float32")
    body = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 30)
    air = np.concatenate([[0], np.diff(noise)])
    return (body * 0.35 + air * 0.75) * env * 0.75


def _hat(np: Any, sr: int, dur: float = 0.045, open_: bool = False) -> Any:
    t = np.arange(int(sr * dur)) / sr
    env = np.exp(-t * (30 if open_ else 90))
    noise = np.random.randn(len(t)).astype("float32")
    hp = np.concatenate([[0], np.diff(noise)])
    return hp * env * (0.5 if open_ else 0.32)


def _808(np: Any, sr: int, dur: float, freq: float) -> Any:
    t = np.arange(int(sr * dur)) / sr
    env = np.exp(-t * 2.2) * (1.0 - np.exp(-t * 80.0))
    f = freq * (1.0 + 0.03 * np.exp(-t * 20))
    osc = np.sin(2 * np.pi * np.cumsum(f) / sr)
    return np.tanh(osc * 1.6) * env * 0.85


def _riser(np: Any, sr: int, dur: float, kind: str = "white") -> Any:
    t = np.arange(int(sr * dur)) / sr
    if kind == "white":
        env = (t / dur) ** 1.3
        n = np.random.randn(len(t)).astype("float32")
        n = np.concatenate([[0], np.diff(n)])
        return n * env * 0.35
    env = (t / dur) ** 1.6
    f = 80.0 + 800.0 * (t / dur) ** 2
    return np.sin(2 * np.pi * np.cumsum(f) / sr).astype("float32") * env * 0.5


def _write_slice(target: Any, source: Any, start: int, total: int, gain: float = 1.0) -> None:
    """Сложить кусок источника в буфер, не выходя за его длину."""
    end = min(start + len(source), total)
    if end <= start:
        return
    target[start:end] += source[: end - start] * gain


def _bar_patterns(section_name: str) -> tuple[list[int], list[int]]:
    """Паттерны кика и хэта: припев плотнее куплета, остальное — базовые."""
    if section_name == "chorus":
        return KICK_PAT_CHORUS, HIHAT_PAT_CHORUS
    if section_name == "verse":
        return KICK_PAT_VERSE, HIHAT_PAT_VERSE
    return KICK_PAT, HIHAT_PAT


def _write_bar(
    y: Any,
    np: Any,
    sr: int,
    bar_pos: int,
    section_name: str,
    gains: tuple[float, float, float, float],
    beat_sec: float,
    step_sec: float,
    root_hz: float,
) -> None:
    """Один такт драм-лейна: kick → snare → hat → 808.

    Порядок генераторов сохранён прежним (kick → snare → hat → 808): от него
    зависит поток ГПСЧ, а значит и бит при том же seed.
    """
    kick_gain, snare_gain, hat_gain, bass_gain = gains
    total = len(y)
    kick_pattern, hat_pattern = _bar_patterns(section_name)
    for step in range(16):
        step_pos = bar_pos + int(step * step_sec * sr)
        if kick_pattern[step] and section_name != "intro":
            _write_slice(y, _kick(np, sr), step_pos, total, kick_gain)
        if SNARE_PAT[step] and section_name != "intro":
            _write_slice(y, _snare(np, sr), step_pos, total, snare_gain)
        if hat_pattern[step]:
            is_open = step == OPENHAT_STEP and section_name != "intro"
            _write_slice(y, _hat(np, sr, open_=is_open), step_pos, total, hat_gain)
        if kick_pattern[step] and section_name != "intro":
            _write_slice(
                y, _808(np, sr, beat_sec * 1.5, root_hz), step_pos, total, bass_gain * 0.65
            )


def render_drum_lane(
    y: Any,
    np: Any,
    sr: int,
    sections: list[tuple[str, int]],
    bar_sec: float,
    step_sec: float,
    beat_sec: float,
    root_hz: float,
) -> list[dict[str, Any]]:
    """Драм-лейн и 808 по секциям; возвращает карту секций."""
    pos = 0
    section_info: list[dict[str, Any]] = []
    for section_name, n_bars in sections:
        sec_start_sec = pos / sr
        sec_len = int(n_bars * bar_sec * sr)
        gains = SECTION_GAINS.get(section_name, SECTION_GAINS["outro"])
        for bar in range(n_bars):
            bar_pos = pos + bar * int(bar_sec * sr)
            _write_bar(
                y, np, sr, bar_pos, section_name, gains, beat_sec, step_sec, root_hz
            )
            if section_name == "pre" and bar == n_bars - 1:
                _write_pre_roll(y, np, sr, bar_pos, beat_sec)
        if section_name == "pre":
            # Стоп-тайм перед хуком: последние 2 шага pre приглушаются.
            cut = int(step_sec * 2 * sr)
            if sec_len > cut:
                y[pos + sec_len - cut : pos + sec_len] *= 0.15
        pos += sec_len
        section_info.append(
            {
                "name": section_name,
                "bars": n_bars,
                "start_sec": round(sec_start_sec, 2),
                "duration_sec": round(n_bars * bar_sec, 2),
            }
        )
    return section_info


def _write_pre_roll(y: Any, np: Any, sr: int, bar_pos: int, beat_sec: float) -> None:
    """Снейр-ролл и два ризера в последнем баре pre-chorus."""
    roll_start = bar_pos + int(2 * beat_sec * sr)
    n_hits = 8
    hit_sec = (2 * beat_sec) / n_hits
    for index in range(n_hits):
        hp = roll_start + int(index * hit_sec * sr)
        _write_slice(y, _snare(np, sr, dur=0.09), hp, len(y), 0.4 + 0.06 * index)
    riser_dur = 2 * beat_sec
    _write_slice(y, _riser(np, sr, riser_dur, "white"), roll_start, len(y))
    _write_slice(y, _riser(np, sr, riser_dur, "sub"), roll_start, len(y))


def stereoize(y: Any, np: Any, sr: int) -> Any:
    """Стерео без Haas на низ: <200 Гц остаётся моно-основой.

    Раньше задержка 12 мс применялась ко всему треку, включая кик и 808:
    фазовые проблемы внизу и рыхлый саб в моно-сумме.
    """
    try:
        from scipy.signal import butter as _butter
        from scipy.signal import sosfilt as _sosfilt

        hp200 = _butter(4, 200, btype="high", fs=sr, output="sos")
        mid_hi = _sosfilt(hp200, y)
        low_mid = y - mid_hi
        delay_samples = int(sr * 0.010)
        mid_hi_r = np.concatenate([np.zeros(delay_samples, dtype="float32"), mid_hi[:-delay_samples]])
        hp5k = _butter(2, 5000, btype="high", fs=sr, output="sos")
        hi = _sosfilt(hp5k, y)
        d2 = int(sr * 0.007)
        hi_r = np.concatenate([np.zeros(d2, dtype="float32"), hi[:-d2]])
        left = low_mid + mid_hi + hi * 0.25
        right = low_mid + mid_hi_r + hi_r * 0.35
        return np.stack([left, right], axis=1)
    except Exception:
        delay_samples = int(sr * 0.012)
        left = y.copy()
        right = np.concatenate([np.zeros(delay_samples, dtype="float32"), y[:-delay_samples]])
        return np.stack([left, right], axis=1)
