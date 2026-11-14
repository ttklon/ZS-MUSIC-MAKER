"""Темп из librosa: массив вместо числа.

`librosa.beat.beat_track` начиная с 0.11 возвращает tempo массивом формы (1,),
а не скаляром. Требование проекта — `librosa>=0.10.2`, значит такие версии
допустимы, и `float(tempo)` падает `TypeError: only 0-dimensional arrays can be
converted to Python scalars`.

Дефект был найден в четырёх местах сразу. Тесты ниже держат и сам разбор, и
каждое место вызова: если кто-то вернёт `float(tempo)`, упадут они, а не
пользовательский запуск анализа.
"""

from __future__ import annotations

import numpy as np
import pytest

from modules.tempo import tempo_scalar
from modules.hit_scorer import hook_metrics


class TestTempoScalar:
    def test_plain_float(self) -> None:
        assert tempo_scalar(128.5) == 128.5

    def test_int(self) -> None:
        assert tempo_scalar(120) == 120.0

    def test_one_element_array(self) -> None:
        # ровно тот случай, на котором падал float(tempo)
        assert tempo_scalar(np.array([112.34714674])) == pytest.approx(112.34714674)

    def test_two_dimensional_single(self) -> None:
        assert tempo_scalar(np.array([[97.0]])) == 97.0

    def test_first_of_several(self) -> None:
        assert tempo_scalar(np.array([97.0, 194.0])) == 97.0

    def test_numpy_scalar(self) -> None:
        assert tempo_scalar(np.float64(90.25)) == 90.25

    def test_empty_array_uses_default(self) -> None:
        assert tempo_scalar(np.array([]), 130.0) == 130.0

    def test_none_uses_default(self) -> None:
        assert tempo_scalar(None, 55.0) == 55.0

    def test_garbage_uses_default(self) -> None:
        assert tempo_scalar("быстро", 60.0) == 60.0

    def test_nan_uses_default(self) -> None:
        assert tempo_scalar(np.array([np.nan]), 70.0) == 70.0

    def test_inf_uses_default(self) -> None:
        assert tempo_scalar(np.array([np.inf]), 80.0) == 80.0

    def test_float_of_array_would_fail(self) -> None:
        """Проверка причины: без разбора падает, с разбором — нет."""
        arr = np.array([128.0])
        with pytest.raises(TypeError):
            float(arr)  # type: ignore[arg-type]
        assert tempo_scalar(arr) == 128.0


class TestCallSites:
    def test_essentia_fallback_accepts_array_tempo(self, monkeypatch) -> None:
        from modules import essentia_analyzer

        class FakeLibrosa:
            @staticmethod
            def load(path, sr=22050, mono=True):
                return np.zeros(22050, dtype="float32"), 22050

            class _F:
                @staticmethod
                def rms(y):
                    return np.array([[0.1, 0.2]])

                @staticmethod
                def spectral_centroid(y, sr):
                    return np.array([[1800.0, 1900.0]])

                @staticmethod
                def spectral_flatness(y):
                    return np.array([[0.01, 0.02]])

                @staticmethod
                def chroma_cqt(y, sr):
                    chroma = np.zeros((12, 4))
                    chroma[9] = 1.0
                    return chroma

            feature = _F

            class _B:
                @staticmethod
                def beat_track(y, sr):
                    return np.array([118.7]), np.array([10, 20, 30])

            beat = _B

            class _O:
                @staticmethod
                def onset_strength(y, sr):
                    return np.ones(16)

            onset = _O

            @staticmethod
            def frames_to_time(frames, sr):
                return np.asarray(frames, dtype=float) / 2.0

        monkeypatch.setattr(essentia_analyzer, "librosa", FakeLibrosa)
        monkeypatch.setattr(essentia_analyzer, "np", np)
        res = essentia_analyzer._analyze_librosa_fallback("x.wav", 22050)
        assert res["ok"] is True
        assert res["bpm"] == pytest.approx(118.7)
        assert res["key"] == "A"

    def test_hook_chorus_reports_scalar_tempo(self, monkeypatch) -> None:
        class FakeLibrosa:
            class onset:
                @staticmethod
                def onset_strength(y, sr):
                    return np.ones(32)

            class beat:
                @staticmethod
                def beat_track(onset_envelope, sr):
                    return np.array([121.0]), np.array([1, 2])

            class util:
                @staticmethod
                def peak_pick(env, **kw):
                    return np.array([1, 5, 9])

            class feature:
                @staticmethod
                def chroma_stft(y, sr):
                    return np.ones((12, 8))

        monkeypatch.setattr(hook_metrics, "librosa", FakeLibrosa)
        monkeypatch.setattr(hook_metrics, "HAS_LIBROSA", True)
        monkeypatch.setattr(hook_metrics, "np", np)
        score, info = hook_metrics._chorus_catchiness(np.zeros(100), 22050)
        assert isinstance(score, float)
        assert info["tempo"] == pytest.approx(121.0)

    def test_hook_bpm_fitness_reports_scalar(self, monkeypatch) -> None:
        class FakeLibrosa:
            class beat:
                @staticmethod
                def beat_track(y, sr):
                    return np.array([130.0]), np.array([1])

        monkeypatch.setattr(hook_metrics, "librosa", FakeLibrosa)
        monkeypatch.setattr(hook_metrics, "HAS_LIBROSA", True)
        score, bpm = hook_metrics._bpm_dance_fitness(np.zeros(100), 22050)
        assert bpm == pytest.approx(130.0)
        assert score > 0.0
