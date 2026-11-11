# -*- coding: utf-8 -*-
"""
Оценка хита не должна хвалить почти пустой файл.

Замер на синтетике показал, что «один клик в 20 секундах тишины» получал
61,85 и вердикт `needs_work`, то есть «почти нормально». Причина: метрики
делят на почти-ноль и выдают максимум на тишине.

- `_hook_energy`: отношение пик/медиана RMS в тишине уходит в бесконечность
  (медиана ≈ 1e-6) → 100 баллов за «динамику припева».
- `_novelty`: дисперсия спектра в тишине ≈ 0, а формула `var*8e5 + 40`
  превращает её в 100.
- `_low_end_power` и `_vocal_presence`: отношение двух почти-нулевых средних
  даёт 1.0 → «низ есть» и «вокал читается».

Оценка хитовости не обязана быть точной, но она обязана быть честной: файл,
в котором нет музыки, не может проходить как трек, которому «нужно немного
поработать».
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.hit_scorer.scoring import score_track

SR = 22_050
SECONDS = 20


def _write(path, stereo) -> str:
    sf.write(str(path), np.asarray(stereo, dtype=np.float32), SR)
    return str(path)


def _stereo(signal) -> np.ndarray:
    return np.stack([signal, signal], axis=1)


def test_single_click_in_silence_is_not_a_track(tmp_path) -> None:
    click = np.zeros(SR * SECONDS)
    click[0] = 1.0
    report = score_track(_write(tmp_path / "click.wav", _stereo(click)))

    assert report["verdict"] in ("flop_risk", "invalid_audio"), report["verdict"]
    assert report["hit_score"] < 50, f"почти пустой файл получил {report['hit_score']}"


def test_silence_is_not_scored_as_a_track(tmp_path) -> None:
    silence = np.zeros(SR * SECONDS)
    report = score_track(_write(tmp_path / "silence.wav", _stereo(silence)))

    assert report["verdict"] in ("flop_risk", "invalid_audio"), report["verdict"]
    assert report["hit_score"] < 40, report["hit_score"]


def test_empty_audio_is_named_as_such() -> None:
    """Молчание — это не «плохой хит», а отсутствие звука."""
    import tempfile
    from pathlib import Path

    report = _empty_report(Path(tempfile.mkdtemp()) / "silence.wav")
    assert report["verdict"] == "invalid_audio"
    assert "reason" in report and report["reason"]


def _empty_report(path) -> dict:
    silence = np.zeros(SR * SECONDS)
    return score_track(_write(path, _stereo(silence)))


def test_real_music_still_scores_well(tmp_path) -> None:
    """Правка не должна ронять оценку настоящему треку: у него есть звук."""
    rng = np.random.RandomState(7)
    t = np.arange(SR * SECONDS) / SR
    music = 0.25 * np.sin(2 * np.pi * 55 * t)
    music += 0.15 * np.sin(2 * np.pi * 220 * t) * (np.sin(2 * np.pi * 2 * t) > 0)
    music += 0.05 * rng.randn(len(t))
    report = score_track(_write(tmp_path / "music.wav", _stereo(music)))

    assert report["verdict"] != "invalid_audio"
    assert report["hit_score"] > 40, report["hit_score"]
