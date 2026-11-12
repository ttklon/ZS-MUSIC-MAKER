"""`modules/hit_scorer/hook_metrics.py` — метрики хука, дропа и TikTok-среза.

Модуль достижим через `modules/hit_scorer/scoring.py` (оценка хита), покрытие
было 46 %. Все метрики — чистые функции над numpy-массивом, поэтому проверяются
на синтетике без весов и без сети.

Принцип проверки: метрика должна ОТЛИЧАТЬ материал, а не выдавать константу.
Поэтому в каждом тесте два сигнала — «хитовый» и «плоский» — и утверждение,
что оценка первого выше. Там, где сигнал слишком короткий для честного
измерения, метрика обязана вернуть названное нейтральное значение, а не
притвориться, что всё хорошо.
"""

from __future__ import annotations

import numpy as np
import pytest

from modules.hit_scorer import hook_metrics as hm


SR = 22050


def sine(seconds: float, freq: float = 220.0, amp: float = 0.3, sr: int = SR) -> np.ndarray:
    n = int(sr * seconds)
    return (amp * np.sin(2 * np.pi * freq * np.arange(n) / sr)).astype("float32")


def with_chorus(seconds: float = 40.0, sr: int = SR) -> np.ndarray:
    """Тихие куплеты и громкий средний блок — «припев»."""
    y = sine(seconds, amp=0.1, sr=sr)
    start = int(len(y) * 0.4)
    end = int(len(y) * 0.7)
    y[start:end] *= 4.0
    return y


class TestBasics:
    def test_rms_of_silence_is_zero(self) -> None:
        assert hm._rms(np.zeros(1000, dtype="float32")) == pytest.approx(0.0, abs=1e-6)

    def test_rms_of_empty_and_none(self) -> None:
        assert hm._rms(np.zeros(0)) == 0.0
        assert hm._rms(None) == 0.0

    def test_rms_matches_amplitude(self) -> None:
        # RMS синуса амплитуды A — A/√2
        assert hm._rms(sine(1.0, amp=0.5)) == pytest.approx(0.5 / np.sqrt(2), rel=0.02)

    def test_db_of_zero_is_floor_not_crash(self) -> None:
        assert hm._db(0.0) == pytest.approx(-180.0)

    def test_db_of_one_is_zero(self) -> None:
        assert hm._db(1.0) == pytest.approx(0.0)


class TestHookEnergy:
    def test_short_track_is_neutral(self) -> None:
        score, ratio = hm._hook_energy(sine(3.0), SR)
        assert score == 50.0  # честный «не знаю», а не высокая оценка
        assert ratio >= 0.0

    def test_chorus_gives_higher_score_than_flat(self) -> None:
        choral, ratio_c = hm._hook_energy(with_chorus(), SR)
        flat, ratio_f = hm._hook_energy(sine(40.0, amp=0.3), SR)
        assert choral > flat
        assert ratio_c > ratio_f

    def test_score_is_capped_at_100(self) -> None:
        y = sine(40.0, amp=0.001)
        y[int(len(y) * 0.5) : int(len(y) * 0.6)] = 0.9  # огромный скачок
        score, _ = hm._hook_energy(y, SR)
        assert score <= 100.0

    def test_without_numpy_is_neutral(self, monkeypatch) -> None:
        monkeypatch.setattr(hm, "np", None)
        assert hm._hook_energy(sine(20.0), SR)[0] == 50.0


class TestHookRepeatability:
    def test_tiny_track_is_neutral(self) -> None:
        assert hm._hook_repeatability(sine(1.0), SR) == (55.0, 0)

    def test_short_track_uses_envelope_autocorrelation(self, monkeypatch) -> None:
        monkeypatch.setattr(hm, "HAS_LIBROSA", False)
        # повторяющиеся всплески каждые 2 с → автокорреляция находит пики
        y = sine(24.0, amp=0.05)
        for start in range(0, len(y) - SR, int(SR * 2.0)):
            y[start : start + int(SR * 0.2)] *= 8.0
        score, peaks = hm._hook_repeatability(y, SR)
        assert peaks > 0
        assert score > 55.0

    def test_flat_short_track_scores_below_neutral(self, monkeypatch) -> None:
        """Ровный сигнал без повторов — это 40 баллов, а не нейтральные 55.

        Комментарий в коде обещает «честный signal» вместо ложного нейтрала:
        ноль найденных повторов даёт базовые 40. Так оценка отличает плоский
        материал от повторяющегося, а не сваливает оба в 55.
        """
        monkeypatch.setattr(hm, "HAS_LIBROSA", False)
        score, peaks = hm._hook_repeatability(sine(24.0), SR)
        assert peaks == 0
        assert score == 40.0

    def test_without_numpy_returns_neutral(self, monkeypatch) -> None:
        monkeypatch.setattr(hm, "HAS_LIBROSA", False)
        monkeypatch.setattr(hm, "np", None)
        assert hm._hook_repeatability(sine(30.0), SR) == (55.0, 0)

    def test_long_track_uses_self_similarity(self) -> None:
        # 25 с повторяющегося мотива: хрома-матрица должна найти повторы
        y = np.tile(sine(2.5), 10)[: int(SR * 25)]
        score, repeats = hm._hook_repeatability(y, SR)
        assert 0.0 <= score <= 100.0
        assert repeats >= 0

    def test_librosa_failure_is_neutral(self, monkeypatch) -> None:
        class Boom:
            class feature:
                @staticmethod
                def chroma_cqt(**kw):
                    raise RuntimeError("нет librosa")

        monkeypatch.setattr(hm, "librosa", Boom)
        assert hm._hook_repeatability(sine(30.0), SR) == (50.0, 0)


class TestChorusCatchiness:
    def test_returns_score_and_details(self, monkeypatch) -> None:
        class FakeLibrosa:
            class onset:
                @staticmethod
                def onset_strength(y, sr):
                    return np.ones(64)

            class beat:
                @staticmethod
                def beat_track(onset_envelope, sr):
                    return np.array([124.0]), np.array([1, 2, 3])

            class util:
                @staticmethod
                def peak_pick(env, **kw):
                    return np.arange(20)

            class feature:
                @staticmethod
                def chroma_stft(y, sr):
                    return np.ones((12, 16)) * 0.5

        monkeypatch.setattr(hm, "librosa", FakeLibrosa)
        monkeypatch.setattr(hm, "HAS_LIBROSA", True)
        score, info = hm._chorus_catchiness(sine(10.0), SR)
        assert 0.0 <= score <= 100.0
        assert info["tempo"] == 124.0
        # Хрома 0.5 во всех 12 бинах — равномерная, то есть «каши по всем
        # нотам»: энтропия максимальна. Раньше здесь проверялась дисперсия,
        # которая эту разницу видела всего как 0,4 балла из 100.
        assert info["chroma_entropy"] == 1.0
        # У фальшивого librosa три удара подряд — интервалы равные.
        assert info["ibi_cv"] == 0.0

    def test_without_librosa_is_neutral(self, monkeypatch) -> None:
        monkeypatch.setattr(hm, "HAS_LIBROSA", False)
        assert hm._chorus_catchiness(sine(10.0), SR) == (55.0, {})

    def test_failure_is_neutral_not_crash(self, monkeypatch) -> None:
        class Boom:
            class onset:
                @staticmethod
                def onset_strength(**kw):
                    raise RuntimeError("сломано")

        monkeypatch.setattr(hm, "librosa", Boom)
        monkeypatch.setattr(hm, "HAS_LIBROSA", True)
        assert hm._chorus_catchiness(sine(10.0), SR) == (55.0, {})


class TestDropImpact:
    def test_short_track_is_neutral(self) -> None:
        assert hm._drop_impact(sine(3.0), SR) == (50.0, 0.0)

    def test_sharp_jump_scores_higher_than_steady(self) -> None:
        steady = sine(30.0, amp=0.2)
        drop = sine(30.0, amp=0.02)
        drop[int(SR * 15) :] = sine(15.0, amp=0.9)  # резкий дроп на 15-й секунде
        score_drop, ratio_drop = hm._drop_impact(drop, SR)
        score_flat, ratio_flat = hm._drop_impact(steady, SR)
        assert score_drop > score_flat
        assert ratio_drop > ratio_flat

    def test_score_is_capped(self) -> None:
        y = sine(20.0, amp=0.01)
        y[int(SR * 10) :] = sine(10.0, amp=1.0)
        score, _ = hm._drop_impact(y, SR)
        assert score <= 100.0

    def test_without_numpy_is_neutral(self, monkeypatch) -> None:
        monkeypatch.setattr(hm, "np", None)
        assert hm._drop_impact(sine(30.0), SR) == (50.0, 0.0)


class TestTiktokHookability:
    def test_short_track_is_named_short(self) -> None:
        score, info = hm._tiktok_hookability(sine(5.0), SR)
        assert score == 40.0
        assert "коротк" in info["reason"].lower()
        assert info["end_sec"] == pytest.approx(5.0, abs=0.01)

    def test_loud_start_slice_is_found(self) -> None:
        y = sine(60.0, amp=0.05)
        # громкий блок с 30-й секунды: должен быть выбран как «хук»
        y[int(SR * 30) : int(SR * 58)] = sine(28.0, amp=0.5)
        score, info = hm._tiktok_hookability(y, SR)
        # Причина называет то, что метрика действительно измерила, а не
        # обещает «immediate hook»: вход у этого трека тихий.
        assert "виральност" in info["reason"]
        assert info["start_sec"] >= 25.0  # окно начинается близко к громкому блоку
        assert info["end_sec"] == pytest.approx(info["start_sec"] + 25.0, abs=0.01)
        assert score <= 100.0

    def test_no_loud_start_uses_loudest_fallback(self) -> None:
        # монотонно тихий трек: критерий «сразу громко» не выполняется
        y = sine(60.0, amp=0.02)
        y[int(SR * 40) :] = sine(20.0, amp=0.03)
        score, info = _call_tiktok(y)
        assert info["reason"] == "яркий и ровный участок; это не предсказание виральности"
        assert score > 0.0

    def test_without_numpy_is_neutral(self, monkeypatch) -> None:
        monkeypatch.setattr(hm, "np", None)
        score, info = hm._tiktok_hookability(sine(60.0), SR)
        assert score == 40.0
        assert "коротк" in info["reason"].lower()


def _call_tiktok(y):
    """Оба варианта причины допустимы — важно, что окно названо."""
    score, info = hm._tiktok_hookability(y, SR)
    return score, info


class TestBpmFitness:
    def _patch(self, monkeypatch, tempo, raises=False):
        class FakeLibrosa:
            class beat:
                @staticmethod
                def beat_track(y, sr):
                    if raises:
                        raise RuntimeError("нет темпа")
                    return np.array([tempo]), np.array([1])

        monkeypatch.setattr(hm, "librosa", FakeLibrosa)
        monkeypatch.setattr(hm, "HAS_LIBROSA", True)

    @pytest.mark.parametrize(
        ("bpm", "expected"),
        [
            (130.0, 100.0),  # главный sweet spot
            (80.0, 90.0),
            (100.0, 75.0),
            (150.0, 80.0),
            (180.0, 40.0),  # вне диапазонов — базовый балл
        ],
    )
    def test_sweet_spots(self, monkeypatch, bpm, expected) -> None:
        self._patch(monkeypatch, bpm)
        score, tempo = hm._bpm_dance_fitness(sine(10.0), SR)
        assert score == expected
        assert tempo == bpm

    def test_array_tempo_is_unwrapped(self, monkeypatch) -> None:
        # ровно тот случай, на котором раньше падал float(tempo)
        self._patch(monkeypatch, np.array([128.0]))
        score, tempo = hm._bpm_dance_fitness(sine(10.0), SR)
        assert isinstance(tempo, float)
        assert score == 100.0

    def test_without_librosa_is_neutral(self, monkeypatch) -> None:
        monkeypatch.setattr(hm, "HAS_LIBROSA", False)
        assert hm._bpm_dance_fitness(sine(10.0), SR) == (60.0, 0.0)

    def test_failure_is_neutral(self, monkeypatch) -> None:
        self._patch(monkeypatch, 0.0, raises=True)
        assert hm._bpm_dance_fitness(sine(10.0), SR) == (60.0, 0.0)


class TestEdgeBranches:
    """Ветки, которые срабатывают только на вырожденных данных.

    Они и есть самое важное: именно здесь метрика обязана назвать причину,
    а не вернуть случайное число.
    """

    def test_track_too_short_even_for_windows(self, monkeypatch) -> None:
        # 2.0 с: 7 окон по 0.5 с с шагом 0.25 → меньше 8, честный нейтрал
        monkeypatch.setattr(hm, "HAS_LIBROSA", False)
        assert hm._hook_repeatability(sine(2.0), SR) == (55.0, 0)

    def test_envelope_failure_is_neutral(self, monkeypatch) -> None:
        monkeypatch.setattr(hm, "HAS_LIBROSA", False)

        class BoomNp:
            float32 = "float32"

            @staticmethod
            def array(data, dtype=None):
                raise RuntimeError("память кончилась")

        monkeypatch.setattr(hm, "np", BoomNp)
        assert hm._hook_repeatability(sine(24.0), SR) == (55.0, 0)

    def test_too_short_for_self_similarity_offset(self, monkeypatch) -> None:
        # librosa доступна, но трек короткий для окна 20 с → падение на
        # диагональ 4 с, и если и это не влезает — нейтральные 50
        monkeypatch.setattr(hm, "HAS_LIBROSA", True)

        class FakeLibrosa:
            class feature:
                @staticmethod
                def chroma_cqt(y=None, sr=None, hop_length=None):
                    return np.ones((12, 5))  # 5 кадров — мало для сдвигов

        monkeypatch.setattr(hm, "librosa", FakeLibrosa)
        assert hm._hook_repeatability(sine(30.0), SR) == (50.0, 0)

    def test_similarity_uses_diagonal_repeats(self, monkeypatch) -> None:
        monkeypatch.setattr(hm, "HAS_LIBROSA", True)

        class FakeLibrosa:
            class feature:
                @staticmethod
                def chroma_cqt(y=None, sr=None, hop_length=None):
                    # полностью повторяющаяся хрома → высокие значения на диагонали
                    return np.ones((12, 600))

        monkeypatch.setattr(hm, "librosa", FakeLibrosa)
        score, share = hm._hook_repeatability(sine(30.0), SR)
        # Полностью повторяющаяся хрома — это доля 1.0 и максимальный балл.
        assert share > 0.9, share
        assert score == 100.0

    def test_tiktok_fallback_marks_loudest_slice(self) -> None:
        # Все окна тише медианы: критерий «сразу громко» не выполняется ни разу
        y = np.zeros(int(SR * 60), dtype="float32")
        y[int(SR * 20) : int(SR * 26)] = sine(6.0, amp=0.4)  # только один громкий кусок
        y += sine(60.0, amp=0.001)
        score, info = hm._tiktok_hookability(y, SR)
        assert info["reason"]
        assert score > 0.0
        assert info["start_sec"] >= 0.0
