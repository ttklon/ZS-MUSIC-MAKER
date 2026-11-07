"""`modules/beat/samples.py` — классификация, банк и загрузка сэмплов бита.

Модуль достижим через `modules/beat/constructor.py` (миксин в бит-конструкторе),
но покрыт не был. При написании тестов нашёлся дефект, который слышно:

`_load_audio` читал только через `pydub`. На чистой установке без ffmpeg
(requirements разрешают `pydub>=0.25.1`, но ffmpeg — отдельная зависимость)
ЛЮБОЙ сэмпл — включая обычный wav — молча заменялся секундой тишины, и в консоль
уходила строка `load fail`. Пользователь слышал, что пропала бочка, и не видел
причины. Теперь порядок такой: soundfile (wav/flac/ogg читаются без ffmpeg) →
pydub (mp3) → отказ, записанный в `sample_load_errors` конструктора.
"""

from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf

from modules.beat.samples import SampleBankMixin


class FakeBeat(SampleBankMixin):
    """Минимальный носитель миксина: только то, что он реально читает."""

    sr = 22050

    def __init__(self, samples=None, root_freq=440.0):
        self.samples = samples or []
        self.kick_samples: list[str] = []
        self.snare_samples: list[str] = []
        self.clap_samples: list[str] = []
        self.hihat_samples: list[str] = []
        self.open_hat_samples: list[str] = []
        self.bass_samples: list[str] = []
        self.melody_samples: list[str] = []
        self.fx_samples: list[str] = []
        self.sample_load_errors: list[dict] = []
        self._np_rng = np.random.default_rng(7)
        self._root = root_freq

    def _root_freq(self) -> float:
        return self._root

    def inject_bank(self, bank):
        """Подставить банк так же, как это сделала бы ленивая загрузка."""
        self._sample_bank = bank
        self._sample_bank_tried = True
        return bank


def wav(tmp_path, name: str, seconds: float = 0.5, sr: int = 22050, stereo=False):
    path = tmp_path / name
    n = int(sr * seconds)
    y = (0.5 * np.sin(2 * np.pi * 220 * np.arange(n) / sr)).astype("float32")
    data = np.stack([y, y], axis=1) if stereo else y
    sf.write(str(path), data, sr)
    return str(path)


class TestClassify:
    @pytest.mark.parametrize(
        ("name", "bucket"),
        [
            ("kick_deep.wav", "kick_samples"),
            ("BD_909.wav", "kick_samples"),
            ("bass_drum_hit.wav", "kick_samples"),
            ("808_boom.wav", "kick_samples"),
            ("clap_stack.wav", "clap_samples"),
            ("openhat_01.wav", "open_hat_samples"),
            ("open_hat_02.wav", "open_hat_samples"),
            ("oh_tight.wav", "open_hat_samples"),
            ("snare_crack.wav", "snare_samples"),
            ("rim_shot.wav", "snare_samples"),
            ("hihat_closed.wav", "hihat_samples"),
            ("ride_cymbal.wav", "hihat_samples"),
            ("bass_sub.wav", "bass_samples"),
            ("sitar_phrase.wav", "melody_samples"),
            ("fx_riser.wav", "fx_samples"),
            ("что_то_непонятное.wav", "melody_samples"),
        ],
    )
    def test_name_goes_to_right_bucket(self, name, bucket) -> None:
        beat = FakeBeat(samples=[f"/x/{name}"])
        beat._classify_samples()
        assert getattr(beat, bucket) == [f"/x/{name}"]

    def test_case_insensitive_and_directory_ignored(self) -> None:
        beat = FakeBeat(samples=["/KICKS/OFFICIAL/KICK_Deep.WAV"])
        beat._classify_samples()
        assert beat.kick_samples == ["/KICKS/OFFICIAL/KICK_Deep.WAV"]

    def test_kick_wins_over_bass_substring(self) -> None:
        # "808" содержит оба маркера; порядок ветвей должен давать кик
        beat = FakeBeat(samples=["/x/808_bass.wav"])
        beat._classify_samples()
        assert beat.kick_samples == ["/x/808_bass.wav"]
        assert beat.bass_samples == []

    def test_clap_is_not_snare(self) -> None:
        beat = FakeBeat(samples=["/x/clap.wav", "/x/snare.wav"])
        beat._classify_samples()
        assert beat.clap_samples == ["/x/clap.wav"]
        assert beat.snare_samples == ["/x/snare.wav"]

    def test_open_hat_is_not_closed_hat(self) -> None:
        beat = FakeBeat(samples=["/x/openhat.wav", "/x/hihat.wav"])
        beat._classify_samples()
        assert beat.open_hat_samples == ["/x/openhat.wav"]
        assert beat.hihat_samples == ["/x/hihat.wav"]

    def test_empty_list_is_noop(self) -> None:
        beat = FakeBeat()
        beat._classify_samples()
        assert beat.kick_samples == []


class TestLoadAudio:
    def test_wav_reads_without_pydub(self, tmp_path) -> None:
        # регрессия: раньше без pydub возвращалась секунда тишины
        beat = FakeBeat()
        out = beat._load_audio(wav(tmp_path, "kick.wav", seconds=0.5))
        assert len(out) == pytest.approx(11025, abs=2)
        assert np.max(np.abs(out)) > 0.4
        assert beat.sample_load_errors == []

    def test_stereo_is_mixed_to_mono(self, tmp_path) -> None:
        beat = FakeBeat()
        out = beat._load_audio(wav(tmp_path, "s.wav", stereo=True))
        assert out.ndim == 1
        assert np.max(np.abs(out)) > 0.4

    def test_sample_rate_is_converted(self, tmp_path) -> None:
        beat = FakeBeat()  # self.sr = 22050
        out = beat._load_audio(wav(tmp_path, "k44.wav", seconds=0.5, sr=44100))
        assert len(out) == pytest.approx(11025, abs=5)

    def test_unreadable_file_is_reported(self, tmp_path) -> None:
        bad = tmp_path / "bad.wav"
        bad.write_bytes(b"not audio")
        beat = FakeBeat()
        out = beat._load_audio(str(bad))
        assert len(out) == 0  # не тишина вместо звука, а явно «ничего»
        assert beat.sample_load_errors
        assert beat.sample_load_errors[0]["path"] == str(bad)
        # в причине видны ОБА движка: soundfile и pydub
        assert "soundfile:" in beat.sample_load_errors[0]["error"]
        assert "pydub:" in beat.sample_load_errors[0]["error"]

    def test_missing_file_is_reported(self, tmp_path) -> None:
        beat = FakeBeat()
        assert len(beat._load_audio(str(tmp_path / "nope.wav"))) == 0
        assert beat.sample_load_errors

    def test_pydub_used_when_soundfile_fails(self, tmp_path, monkeypatch) -> None:
        beat = FakeBeat()
        path = wav(tmp_path, "kick.wav")

        import soundfile

        monkeypatch.setattr(
            soundfile, "read", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("mp3?"))
        )

        class Seg:
            channels = 2

            def set_channels(self, n):
                return self

            def set_frame_rate(self, sr):
                return self

            def get_array_of_samples(self):
                return [0, 16000, -16000, 8000]

        class FakePydub:
            class AudioSegment:
                @staticmethod
                def from_file(p):
                    return Seg()

        import sys
        import types

        mod = types.ModuleType("pydub")
        mod.AudioSegment = FakePydub.AudioSegment
        monkeypatch.setitem(sys.modules, "pydub", mod)

        out = beat._load_audio(path)
        assert out.dtype == np.float32
        assert np.max(np.abs(out)) == pytest.approx(16000 / 32768, abs=1e-6)
        assert beat.sample_load_errors == []


class TestBank:
    def test_absent_bank_is_none_and_cached(self, monkeypatch) -> None:
        beat = FakeBeat()
        import app.audio.samples as samples_mod

        calls = []

        def boom(*a, **k):
            calls.append(1)
            raise RuntimeError("нет манифеста")

        monkeypatch.setattr(samples_mod, "load_bank", boom)
        assert beat._bank() is None
        assert beat._bank() is None  # второй раз — из кэша, без нового импорта
        assert len(calls) == 1  # неудача тоже кэшируется

    def test_bank_audio_none_without_bank(self, monkeypatch) -> None:
        beat = FakeBeat()
        import app.audio.samples as samples_mod

        monkeypatch.setattr(
            samples_mod, "load_bank", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x"))
        )
        assert beat._bank_audio("kick") is None

    def test_bank_audio_reads_and_returns_mono(self, tmp_path, monkeypatch) -> None:
        import app.audio.samples as samples_mod

        path = wav(tmp_path, "kick.wav")

        class Entry:
            tuning_hz = 0

            def __init__(self):
                self.path = path

        class Bank:
            def choose(self, instrument, rng=None, velocity=1.0):
                assert instrument == "kick"
                return Entry()

        beat = FakeBeat()
        beat.inject_bank(Bank())
        audio = beat._bank_audio("kick", 0.8)
        assert audio is not None and len(audio) > 0
        assert audio.ndim == 1

    def test_bank_entry_missing_is_none(self) -> None:
        class Bank:
            def choose(self, *a, **k):
                return None

        beat = FakeBeat()
        beat.inject_bank(Bank())
        assert beat._bank_audio("snare") is None

    def test_unreadable_entry_is_none(self) -> None:
        class Entry:
            tuning_hz = 0
            path = "/nope/missing.wav"

        class Bank:
            def choose(self, *a, **k):
                return Entry()

        beat = FakeBeat()
        beat.inject_bank(Bank())
        assert beat._bank_audio("hat") is None

    def test_tuning_applies_to_kick_only(self, tmp_path, monkeypatch) -> None:
        import app.audio.samples as samples_mod

        path = wav(tmp_path, "kick.wav")
        shifts: list[float] = []

        class Entry:
            tuning_hz = 220.0

            def __init__(self):
                self.path = path

        class Bank:
            def choose(self, *a, **k):
                return Entry()

        monkeypatch.setattr(
            samples_mod, "pitch_shift", lambda audio, semitones, sr: shifts.append(semitones) or audio
        )
        beat = FakeBeat(root_freq=440.0)
        beat.inject_bank(Bank())

        beat._bank_audio("kick")
        assert shifts and shifts[0] == pytest.approx(12.0, abs=1e-6)  # 440/220 → +12

        shifts.clear()
        beat._bank_audio("snare")  # не kick/808 — подстройка не нужна
        assert shifts == []

    def test_tuning_ratio_clamped(self, tmp_path, monkeypatch) -> None:
        import app.audio.samples as samples_mod

        path = wav(tmp_path, "kick.wav")
        shifts: list[float] = []

        class Entry:
            tuning_hz = 1.0  # абсурдно низкая «тональность»

            def __init__(self):
                self.path = path

        class Bank:
            def choose(self, *a, **k):
                return Entry()

        monkeypatch.setattr(
            samples_mod, "pitch_shift", lambda a, s, sr: shifts.append(s) or a
        )
        beat = FakeBeat(root_freq=440.0)
        beat.inject_bank(Bank())
        beat._bank_audio("808")
        # ratio ограничен 2.0 сверху
        assert shifts[0] == pytest.approx(12.0, abs=1e-6)


class TestLoadErrorsAreVisible:
    def test_unreadable_sample_appears_in_engine_report(self, tmp_path) -> None:
        """Сэмпл, который не прочитался, не должен исчезать из отчёта."""
        from modules.beat.constructor import BeatConstructor

        bad = tmp_path / "kick_broken.wav"
        bad.write_bytes(b"garbage")
        beat = BeatConstructor(genre="drift_phonk", seed=1, samples=[str(bad)])
        beat._load_audio(str(bad))
        report = beat._drum_engine_report()
        assert report.get("sample_load_errors")
        assert report["sample_load_errors"][0]["path"] == str(bad)

    def test_readable_sample_leaves_report_clean(self, tmp_path) -> None:
        from modules.beat.constructor import BeatConstructor

        good = wav(tmp_path, "kick_fine.wav", sr=44100)
        beat = BeatConstructor(genre="drift_phonk", seed=1, samples=[good])
        assert beat._load_audio(good).size > 0
        report = beat._drum_engine_report()
        assert "sample_load_errors" not in report
