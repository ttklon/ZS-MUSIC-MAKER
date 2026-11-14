# -*- coding: utf-8 -*-
"""
Громкость должна мериться по стерео, а не по моно-сумме.

Замер на живом мастере движка (phonk, 30 с, стенд streaming):

    pyloudnorm по стерео 44,1 кГц : -14,00 LUFS   ← так мастер и сведён
    pyloudnorm по моно (то же)    : -17,88 LUFS
    librosa mono 22050 в оценке   : -17,92        ← это и видел `_loudness_lufs`

`_load_audio` грузит моно, и интегрированная громкость моно-суммы не равна
стерео-громкости: моно = (L+R)/2, поэтому E_моно = E_L·(1+corr)/2·2, и при
корреляции 0,86 разница 3,9 дБ. Ниже −16 LUFS оценка ставила 50 баллов из
100 — то есть честно сведённый под −14 мастер наказывался за то, что его
померили в моно. Проверка `tests/test_master_format.py` при этом проходила:
она читает стерео и видит правильные −14,0.

Вторая, тихая проблема того же места: шкала ставила 98 баллов за коридор
[-14,0; -9,0], а движок целится ровно в −14,0 ± 0,5 — верхняя часть шкалы
была недостижима для собственных мастеров.
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.hit_scorer.mix_metrics import _loudness_lufs_status
from modules.hit_scorer.scoring import score_track

SR = 44_100
SECONDS = 12


def _stereo_noise(seed: int = 5) -> np.ndarray:
    """Разведённый по каналам шум: корреляция ≈ 0,6, как у живого микса."""
    rng = np.random.RandomState(seed)
    n = SR * SECONDS
    common = rng.randn(n) * 0.4
    left = common + rng.randn(n) * 0.5
    right = common * 0.9 + rng.randn(n) * 0.5
    return np.stack([left, right], axis=1)


def _write_at_lufs(path, stereo, target_lufs: float) -> str:
    """Записать сигнал ровно на заданной интегрированной громкости."""
    import pyloudnorm as pyln

    meter = pyln.Meter(SR)
    current = float(meter.integrated_loudness(stereo))
    scaled = stereo * (10.0 ** ((target_lufs - current) / 20.0))
    sf.write(str(path), np.asarray(scaled, dtype=np.float32), SR)
    return str(path)


def test_stereo_master_is_measured_in_stereo(tmp_path) -> None:
    """Мастер, сведённый под −14 LUFS, не должен читаться как −18."""
    import pyloudnorm as pyln

    path = _write_at_lufs(tmp_path / "master.wav", _stereo_noise(), -14.0)
    stereo = sf.read(path, always_2d=True)[0]
    true_lufs = float(pyln.Meter(SR).integrated_loudness(stereo))
    (score, lufs), provenance = _loudness_lufs_status(
        stereo.mean(axis=1), SR, stereo_path=path
    )

    assert abs(lufs - true_lufs) < 0.05, (lufs, true_lufs)
    assert provenance["channels"] == 2, provenance
    assert score >= 80.0, (score, lufs)


def test_mono_fallback_still_works(tmp_path) -> None:
    """Без пути к файлу остаётся прежний замер по моно — и это видно."""
    samples = _stereo_noise() * 0.1  # не в потолок: шум 1,0 в моно шумит над 0 dBFS
    (score, lufs), provenance = _loudness_lufs_status(samples.mean(axis=1), SR)

    assert provenance["engine"] == "pyloudnorm"
    assert "channels" not in provenance, provenance
    assert lufs < -14.0, lufs  # моно тише стерео — ожидаемо
    assert 0.0 <= score <= 100.0


def test_loudness_band_is_reachable_for_engine_targets(tmp_path) -> None:
    """Коридор громкости должен покрывать собственные цели мастеринга."""
    quiet = score_track(_write_at_lufs(tmp_path / "a.wav", _stereo_noise(6), -14.0))
    loud = score_track(_write_at_lufs(tmp_path / "b.wav", _stereo_noise(7), -13.6))

    for report in (quiet, loud):
        metric = report["metrics"]["loudness_lufs"]
        assert abs(metric["raw"] + 14.0) <= 0.5, metric
        assert metric["score"] >= 80.0, metric

    assert loud["metrics"]["loudness_lufs"]["score"] >= quiet["metrics"][
        "loudness_lufs"
    ]["score"], "чуть более громкий мастер не должен оцениваться хуже"


def test_quiet_master_is_still_punished(tmp_path) -> None:
    """Правка не должна прощать действительно тихий мастер."""
    report = score_track(_write_at_lufs(tmp_path / "q.wav", _stereo_noise(8), -22.0))

    assert report["metrics"]["loudness_lufs"]["raw"] < -20.0
    assert report["metrics"]["loudness_lufs"]["score"] < 60.0
