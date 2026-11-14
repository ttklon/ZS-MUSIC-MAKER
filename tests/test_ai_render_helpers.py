"""`app/core/ai/render.py` — рендер-хелперы AI-пайплайна (покрытие было 9 %).

Функции здесь чистые: модель приходит аргументом (`handle`), состояния
пайплайна нет. Поэтому проверять их можно без весов — на подставных handle,
которые ведут себя как настоящие: пишут файл, отдают тензор, бросают ошибку.

Логика, которую легко сломать при рефакторинге и которая проверяется здесь:
склейка интро/бит/аутро через equal-power кроссфейд, передискретизация при
разной частоте, защита пика до записи, и обязательное подтверждение того, что
файл действительно появился (`did not produce an audio file`).
"""

from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf

from app.core.ai import render


def write_wav(path, seconds=2.0, sr=22050, freq=220.0, amp=0.3, channels=1):
    from pathlib import Path

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    n = int(sr * seconds)
    y = amp * np.sin(2 * np.pi * freq * np.arange(n) / sr)
    data = np.column_stack([y, y]) if channels == 2 else y
    sf.write(str(path), data.astype("float32"), sr)
    return str(path)


# --------------------------------------------------------------------------- #
#  стерео-текстура
# --------------------------------------------------------------------------- #
class FakeTensor:
    def __init__(self, array):
        self._array = array

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self._array


class FakeMusicGen:
    def __init__(self, array, sample_rate=32000):
        self._array = array
        self.sample_rate = sample_rate
        self.params = None

    def set_generation_params(self, **kw):
        self.params = kw

    def generate(self, prompts, progress=False):
        assert isinstance(prompts, list) and prompts
        return [FakeTensor(self._array)]


class TestRenderStereoTexture:
    def test_mono_output_is_duplicated_to_stereo(self, tmp_path) -> None:
        out = tmp_path / "t.wav"
        handle = FakeMusicGen(np.linspace(-0.5, 0.5, 3200, dtype="float32"))
        res = render.render_stereo_texture(handle, "prompt", 4, str(out))
        assert res["ok"] is True
        assert handle.params["duration"] == 4
        data, sr = sf.read(res["texture_path"], always_2d=True)
        assert data.shape[1] == 2
        assert sr == 32000

    def test_two_dimensional_tensor_is_transposed(self, tmp_path) -> None:
        # (channels, samples) → (samples, channels)
        arr = np.zeros((2, 640), dtype="float32")
        arr[0] = 0.4
        out = tmp_path / "t.wav"
        handle = FakeMusicGen(arr)
        res = render.render_stereo_texture(handle, "p", 2, str(out))
        assert res["ok"] is True
        data, _ = sf.read(res["texture_path"], always_2d=True)
        assert data.shape[0] == 640
        assert data.shape[1] == 2

    def test_single_channel_matrix_is_repeated(self, tmp_path) -> None:
        # Музыкальная модель отдаёт (samples, channels). Матрица (1, N) после
        # транспонирования даёт один канал и дублируется в стерео.
        arr = np.zeros((1, 640), dtype="float32")
        arr[0, :] = 0.3
        out = tmp_path / "t.wav"
        handle = FakeMusicGen(arr)
        res = render.render_stereo_texture(handle, "p", 2, str(out))
        assert res["ok"] is True
        data, _ = sf.read(res["texture_path"], always_2d=True)
        assert data.shape == (640, 2)
        # оба канала идентичны — это и есть дублирование моно
        assert np.allclose(data[:, 0], data[:, 1])

    def test_three_dimensional_tensor_is_refused(self, tmp_path) -> None:
        handle = FakeMusicGen(np.zeros((2, 2, 2), dtype="float32"))
        res = render.render_stereo_texture(handle, "p", 2, str(tmp_path / "t.wav"))
        assert res["ok"] is False
        assert "unexpected MusicGen stereo tensor shape" in res["reason"]

    def test_handle_failure_names_the_stage(self, tmp_path) -> None:
        class Boom:
            sample_rate = 32000

            def set_generation_params(self, **kw):
                raise RuntimeError("нет VRAM")

        res = render.render_stereo_texture(Boom(), "p", 2, str(tmp_path / "t.wav"))
        assert res["ok"] is False
        assert res["reason"].startswith("music_stereo generation failed")
        assert "нет VRAM" in res["reason"]


# --------------------------------------------------------------------------- #
#  склейка интро/бит/аутро
# --------------------------------------------------------------------------- #
class TestExtendBeat:
    def test_stitches_three_parts_into_stereo(self, tmp_path) -> None:
        base = write_wav(tmp_path / "beat.wav", seconds=2.0)
        intro = write_wav(tmp_path / "intro.wav", seconds=1.0)
        outro = write_wav(tmp_path / "outro.wav", seconds=1.0, freq=330)
        out = tmp_path / "out" / "beat_stereo.wav"
        res = render.extend_beat_with_stereo_sections(base, intro, outro, str(out), fade_sec=0.2)
        assert res["ok"] is True
        assert res["channels"] == 2
        assert res["fade_sec"] == 0.2
        data, sr = sf.read(res["beat_path"], always_2d=True)
        assert data.shape[1] == 2
        # кроссфейды по 0.2 с съедают часть перекрытия
        expected = (2.0 + 1.0 + 1.0 - 2 * 0.2)
        assert res["duration_sec"] == pytest.approx(expected, abs=0.1)
        assert res["sample_rate"] == sr

    def test_different_sample_rates_are_resampled(self, tmp_path) -> None:
        base = write_wav(tmp_path / "beat.wav", seconds=1.5, sr=22050)
        intro = write_wav(tmp_path / "intro.wav", seconds=0.8, sr=44100)
        outro = write_wav(tmp_path / "outro.wav", seconds=0.8, sr=48000)
        res = render.extend_beat_with_stereo_sections(
            base, intro, outro, str(tmp_path / "o.wav"), fade_sec=0.1
        )
        assert res["ok"] is True
        assert res["sample_rate"] == 22050

    def test_zero_fade_concatenates(self, tmp_path) -> None:
        base = write_wav(tmp_path / "beat.wav", seconds=1.0)
        intro = write_wav(tmp_path / "intro.wav", seconds=0.5)
        outro = write_wav(tmp_path / "outro.wav", seconds=0.5)
        res = render.extend_beat_with_stereo_sections(
            base, intro, outro, str(tmp_path / "o.wav"), fade_sec=0.0
        )
        assert res["ok"] is True
        assert res["duration_sec"] == pytest.approx(2.0, abs=0.02)

    def test_loud_input_is_peak_limited(self, tmp_path) -> None:
        base = write_wav(tmp_path / "beat.wav", seconds=1.0, amp=0.95)
        intro = write_wav(tmp_path / "intro.wav", seconds=0.5, amp=0.95)
        outro = write_wav(tmp_path / "outro.wav", seconds=0.5, amp=0.95)
        out = tmp_path / "o.wav"
        res = render.extend_beat_with_stereo_sections(base, intro, outro, str(out), fade_sec=0.1)
        data, _ = sf.read(out, always_2d=True)
        assert float(np.max(np.abs(data))) <= 0.98 + 1e-3

    def test_missing_file_is_refused_with_reason(self, tmp_path) -> None:
        res = render.extend_beat_with_stereo_sections(
            str(tmp_path / "нет.wav"),
            str(tmp_path / "a.wav"),
            str(tmp_path / "b.wav"),
            str(tmp_path / "o.wav"),
        )
        assert res["ok"] is False
        assert res["reason"].startswith("stereo beat extension failed")

    def test_stereo_sources_are_kept(self, tmp_path) -> None:
        base = write_wav(tmp_path / "beat.wav", seconds=1.0, channels=2)
        intro = write_wav(tmp_path / "intro.wav", seconds=0.5, channels=2)
        outro = write_wav(tmp_path / "outro.wav", seconds=0.5, channels=2)
        res = render.extend_beat_with_stereo_sections(
            base, intro, outro, str(tmp_path / "o.wav"), fade_sec=0.1
        )
        assert res["ok"] is True
        assert res["channels"] == 2


# --------------------------------------------------------------------------- #
#  XTTS
# --------------------------------------------------------------------------- #
class FakeXtts:
    def __init__(self, write=True, loud=True):
        self.write = write
        self.loud = loud
        self.kwargs = None

    def tts_to_file(self, **kw):
        self.kwargs = kw
        if self.write:
            amp = 0.5 if self.loud else 0.0001
            n = 22050
            sf.write(kw["file_path"], (amp * np.sin(np.arange(n) / 10)).astype("float32"), 22050)


class TestRenderXttsVocal:
    def test_speaker_wav_passed_only_when_exists(self, tmp_path, monkeypatch) -> None:
        out = tmp_path / "v.wav"
        speaker = write_wav(tmp_path / "spk.wav", seconds=1.0)
        handle = FakeXtts()
        monkeypatch.setattr(
            render, "validate_vocal_artifact", lambda p, t: {"ok": True, "reason": None}
        )
        res = render.render_xtts_vocal(handle, "текст песни", str(out), speaker_wav=speaker)
        assert res["ok"] is True
        assert handle.kwargs["speaker_wav"] == speaker
        assert handle.kwargs["language"] == "ru"

    def test_missing_speaker_is_not_passed(self, tmp_path, monkeypatch) -> None:
        handle = FakeXtts()
        monkeypatch.setattr(
            render, "validate_vocal_artifact", lambda p, t: {"ok": True, "reason": None}
        )
        render.render_xtts_vocal(
            handle, "текст", str(tmp_path / "v.wav"), speaker_wav=str(tmp_path / "нет.wav")
        )
        assert "speaker_wav" not in handle.kwargs

    def test_no_file_is_refused(self, tmp_path) -> None:
        res = render.render_xtts_vocal(FakeXtts(write=False), "текст", str(tmp_path / "v.wav"))
        assert res["ok"] is False
        assert res["reason"] == "XTTS did not produce an audio file"

    def test_quality_verdict_is_reported(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(
            render,
            "validate_vocal_artifact",
            lambda p, t: {"ok": False, "reason": "тишина"},
        )
        res = render.render_xtts_vocal(FakeXtts(), "текст", str(tmp_path / "v.wav"))
        assert res["ok"] is False
        assert res["reason"] == "тишина"
        assert res["engine"] == "xtts_v2"

    def test_handle_exception_is_named(self, tmp_path) -> None:
        class Boom:
            def tts_to_file(self, **kw):
                raise RuntimeError("нет модели")

        res = render.render_xtts_vocal(Boom(), "т", str(tmp_path / "v.wav"))
        assert res["ok"] is False
        assert res["reason"].startswith("XTTS synthesis failed")


# --------------------------------------------------------------------------- #
#  фоллбек TTS
# --------------------------------------------------------------------------- #
class TestRenderVoiceSynthFallback:
    def test_copies_source_into_project(self, tmp_path, monkeypatch) -> None:
        source = write_wav(tmp_path / "tts" / "out.wav", seconds=1.0)
        out = tmp_path / "project" / "vocal.wav"
        monkeypatch.setattr(
            render, "validate_vocal_artifact", lambda p, t: {"ok": True, "reason": None}
        )
        res = render.render_voice_synth_fallback("текст", str(out), synth_fn=lambda t, **k: source)
        assert res["ok"] is True
        assert out.exists()
        assert res["engine"] == "voice_synth_fallback"

    def test_same_path_is_not_copied_onto_itself(self, tmp_path, monkeypatch) -> None:
        out = tmp_path / "vocal.wav"
        write_wav(out, seconds=1.0)
        monkeypatch.setattr(
            render, "validate_vocal_artifact", lambda p, t: {"ok": True, "reason": None}
        )
        res = render.render_voice_synth_fallback("т", str(out), synth_fn=lambda t, **k: str(out))
        assert res["ok"] is True

    def test_no_engine_output_is_refused(self, tmp_path) -> None:
        res = render.render_voice_synth_fallback(
            "т", str(tmp_path / "v.wav"), synth_fn=lambda t, **k: None
        )
        assert res["ok"] is False
        assert res["reason"] == "no fallback TTS engine produced audio"

    def test_missing_file_is_refused(self, tmp_path) -> None:
        res = render.render_voice_synth_fallback(
            "т", str(tmp_path / "v.wav"), synth_fn=lambda t, **k: str(tmp_path / "нет.wav")
        )
        assert res["ok"] is False
        assert "no fallback TTS engine" in res["reason"]

    def test_engine_exception_is_named(self, tmp_path) -> None:
        def boom(t, **k):
            raise RuntimeError("нет espeak")

        res = render.render_voice_synth_fallback("т", str(tmp_path / "v.wav"), synth_fn=boom)
        assert res["ok"] is False
        assert res["reason"].startswith("fallback TTS failed")


# --------------------------------------------------------------------------- #
#  RVC
# --------------------------------------------------------------------------- #
class FakeRvc:
    def __init__(self, produce=True):
        self.produce = produce
        self.kwargs = None

    def infer(self, input_wav, voice_name, pitch_shift, out_name):
        self.kwargs = dict(voice_name=voice_name, pitch_shift=pitch_shift, out_name=out_name)
        if not self.produce:
            return None
        from pathlib import Path
        import tempfile

        target = Path(tempfile.mkdtemp()) / out_name
        sf.write(str(target), np.zeros(22050, dtype="float32"), 22050)
        return str(target)


class TestRenderRvcVocal:
    def test_inference_copies_artifact(self, tmp_path, monkeypatch) -> None:
        src = write_wav(tmp_path / "vocal.wav", seconds=1.0)
        out = tmp_path / "project" / "vocal_rvc.wav"
        handle = FakeRvc()
        monkeypatch.setattr(
            render, "validate_rvc_artifact", lambda a, b: {"ok": True, "reason": None}
        )
        res = render.render_rvc_vocal(handle, src, str(out), "my_voice", pitch_shift=-3)
        assert res["ok"] is True
        assert out.exists()
        assert res["engine"] == "rvc"
        assert res["voice_name"] == "my_voice"
        assert handle.kwargs["pitch_shift"] == -3

    def test_voice_name_is_sanitised_to_basename(self, tmp_path, monkeypatch) -> None:
        src = write_wav(tmp_path / "vocal.wav")
        handle = FakeRvc()
        monkeypatch.setattr(
            render, "validate_rvc_artifact", lambda a, b: {"ok": True, "reason": None}
        )
        res = render.render_rvc_vocal(
            handle, src, str(tmp_path / "o.wav"), "../../etc/passwd"
        )
        # попытка выйти из каталога отсекается до вызова модели
        assert handle.kwargs["voice_name"] == "passwd"
        assert res["voice_name"] == "passwd"

    def test_no_output_is_refused(self, tmp_path) -> None:
        src = write_wav(tmp_path / "vocal.wav")
        res = render.render_rvc_vocal(
            FakeRvc(produce=False), src, str(tmp_path / "o.wav"), "voice"
        )
        assert res["ok"] is False
        assert res["reason"] == "RVC did not produce an audio file"

    def test_failure_is_named(self, tmp_path) -> None:
        class Boom:
            def infer(self, **kw):
                raise RuntimeError("нет весов")

        src = write_wav(tmp_path / "vocal.wav")
        res = render.render_rvc_vocal(Boom(), src, str(tmp_path / "o.wav"), "voice")
        assert res["ok"] is False
        assert res["reason"].startswith("RVC inference failed")

    def test_quality_verdict_is_reported(self, tmp_path, monkeypatch) -> None:
        src = write_wav(tmp_path / "vocal.wav")
        monkeypatch.setattr(
            render,
            "validate_rvc_artifact",
            lambda a, b: {"ok": False, "reason": "длина не совпала"},
        )
        res = render.render_rvc_vocal(FakeRvc(), src, str(tmp_path / "o.wav"), "v")
        assert res["ok"] is False
        assert res["reason"] == "длина не совпала"


class TestSlug:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("My Voice", "my_voice"),
            ("  spaced  ", "spaced"),
            ("путь/с/слэшами", "путь_с_слэшами"),
            ("", "unknown"),
            ("!!!", "unknown"),
        ],
    )
    def test_slug(self, raw, expected) -> None:
        assert render._slug(raw) == expected
