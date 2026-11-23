"""Long lyrics must not be truncated, and failed renders must not reuse old audio."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf

from modules.dsp.wavio import write_wav
from modules.voice_output import render_atomic, usable_voice
from modules.voice_text import silero_audio, speech_chunks


def test_long_lyrics_preserve_every_word_and_obey_limit():
    text = "[verse 1]\n" + "Очень длинная строка о ночном городе. " * 200 + "\n[hook]\nПоследний припев!"
    chunks = speech_chunks(text)
    assert len(chunks) > 5
    assert all(0 < len(c) <= 600 for c in chunks)
    expected = text.replace("[verse 1]", "").replace("[hook]", "").split()
    assert " ".join(chunks).split() == expected


def test_labels_are_not_read_as_lyrics():
    assert speech_chunks("[Куплет 2]\nНочь.\n[припев]\nГород!") == ["Ночь. Город!"]
    assert speech_chunks("[verse 1]\n[hook]") == []
    assert speech_chunks("[эй] Настоящая строка") == ["[эй] Настоящая строка"]


class Audio:
    def __init__(self, data):
        self.data = data

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.data


def test_silero_synthesizes_all_chunks_in_order():
    calls = []
    text = "Это полноценная строка песни. " * 100

    def apply_tts(**kw):
        calls.append(kw["text"])
        return Audio(np.ones(4800, dtype=np.float32) * 0.1)

    audio = silero_audio(SimpleNamespace(apply_tts=apply_tts), text, "aidar")
    assert calls == speech_chunks(text)
    assert len(audio) == len(calls) * 4800 + (len(calls) - 1) * 3840
    assert np.isfinite(audio).all()
    assert audio[0] == audio[-1] == 0


@pytest.mark.parametrize("data", [np.zeros(100), np.full(100, np.nan), np.ones((1, 100)), np.array([])])
def test_bad_chunk_is_not_published_as_a_partial_song(data):
    model = SimpleNamespace(apply_tts=lambda **kw: Audio(data))
    with pytest.raises(ValueError):
        silero_audio(model, "Текст песни.", "aidar")


def test_failed_render_keeps_previous_master_and_cleans_temporary_files(tmp_path):
    target = tmp_path / "voice.wav"
    write_wav(target, np.ones(1000, dtype=np.float32) * 0.1, 8000)
    previous = target.read_bytes()

    def broken(path):
        Path(path).write_bytes(b"not audio" * 1000)
        return True

    assert not render_atomic(str(target), broken)
    assert target.read_bytes() == previous
    assert not list(tmp_path.glob(".voice-*"))


def test_valid_render_publishes_decodable_wav(tmp_path):
    target = tmp_path / "nested" / "voice.wav"

    def render(path):
        write_wav(path, np.ones(1000, dtype=np.float32) * 0.1, 8000)
        return True

    assert render_atomic(str(target), render)
    audio, sr = sf.read(target)
    assert sr == 8000 and len(audio) == 1000
    assert usable_voice(str(target))
    assert not list(target.parent.glob(".voice-*"))


def test_failed_backend_cannot_reuse_output_from_previous_backend(tmp_path):
    from modules.voice_synth import _run_candidates

    path = tmp_path / "partial.wav"

    def partial_failure():
        write_wav(path, np.ones(1000, dtype=np.float32) * 0.1, 8000)
        return False

    assert not _run_candidates(
        ("partial", "false_success"),
        {"partial": partial_failure, "false_success": lambda: True}, str(path),
    )


def test_raising_backend_does_not_abort_fallback(tmp_path):
    from modules.voice_synth import _run_candidates

    path = tmp_path / "voice.wav"

    def broken():
        raise RuntimeError("engine crashed")

    def good():
        write_wav(path, np.ones(1000, dtype=np.float32) * 0.1, 8000)
        return True

    assert _run_candidates(("bad", "good"), {"bad": broken, "good": good}, str(path))


def test_absolute_project_output_does_not_touch_install_directory(tmp_path, monkeypatch):
    import modules.voice_synth as voice

    # An installed application may have a read-only default output location.
    blocked_root = tmp_path / "not_a_directory"
    blocked_root.write_bytes(b"read-only installation stand-in")
    monkeypatch.setattr(voice, "OUT_DIR", blocked_root / "voice_draft")

    def synthesize(text, path, **kwargs):
        write_wav(path, np.ones(1000, dtype=np.float32) * 0.1, 8000)
        return True

    monkeypatch.setattr(voice, "_synth_silero", synthesize)
    target = tmp_path / "user_project" / "voice.wav"
    assert voice.synth("Текст", out_name=str(target)) == str(target)
    assert usable_voice(str(target))
