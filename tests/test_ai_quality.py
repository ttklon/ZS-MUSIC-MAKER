# -*- coding: utf-8 -*-
"""Качественные контракты outputs LLM и генерации аудио."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

from app.ai.quality import validate_audio_artifact, validate_metadata_json


def test_metadata_quality_accepts_complete_release_payload() -> None:
    payload = {
        "title": "Ночной маршрут",
        "spotify_desc": "Динамичный phonk-трек для ночной дороги.",
        "youtube_desc": "Премьера независимого трека.",
        "tags_tiktok": ["phonk", "newmusic"],
        "tags_instagram": ["music"],
    }

    result = validate_metadata_json(payload)

    assert result["ok"] is True
    assert result["metrics"]["tags"] == 3


def test_metadata_quality_rejects_incomplete_payload() -> None:
    result = validate_metadata_json({"title": "x", "tags_tiktok": []})

    assert result["ok"] is False
    assert "title" in result["reason"]
    assert "description" in result["reason"]
    assert "tags" in result["reason"]


def test_audio_quality_accepts_signal_and_rejects_silence(tmp_path) -> None:
    sample_rate = 8_000
    t = np.arange(sample_rate * 2) / sample_rate
    signal = (0.2 * np.sin(2 * np.pi * 220 * t)).astype("float32")
    valid_path = tmp_path / "signal.wav"
    silent_path = tmp_path / "silent.wav"
    sf.write(valid_path, np.column_stack([signal, signal]), sample_rate)
    sf.write(silent_path, np.zeros((sample_rate * 2, 2), dtype="float32"), sample_rate)

    valid = validate_audio_artifact(valid_path, min_duration_sec=1.5)
    silent = validate_audio_artifact(silent_path, min_duration_sec=1.0)

    assert valid["ok"] is True
    assert valid["metrics"]["channels"] == 2
    assert silent["ok"] is False
    assert silent["reason"] == "audio is silent"


def test_ai_dry_run_persists_valid_metadata_fallback(tmp_path) -> None:
    from app.core.orchestrator_ai import run_ai_pipeline

    run_ai_pipeline("metadata_quality", out_root=tmp_path, dry_run=True)
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))

    assert metadata["ok"] is True
    assert metadata["source"] == "dry"
    assert metadata["quality"]["ok"] is True


class _FakeTensor:
    def __init__(self, value):
        self.value = value

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.value


class _FakeStereoMusicGen:
    sample_rate = 8_000

    def __init__(self):
        self.params = None

    def set_generation_params(self, **kwargs):
        self.params = kwargs

    def generate(self, prompts, progress=False):
        assert prompts and progress is False
        signal = np.vstack([
            0.1 * np.sin(np.linspace(0, 100, 8_000)),
            0.1 * np.cos(np.linspace(0, 100, 8_000)),
        ])
        return [_FakeTensor(signal)]


def test_music_stereo_handle_renders_separate_stereo_texture(tmp_path) -> None:
    from app.core.orchestrator_ai import render_stereo_texture

    handle = _FakeStereoMusicGen()
    output = tmp_path / "texture.wav"
    result = render_stereo_texture(handle, "wide transition texture", 4, str(output))

    assert result["ok"] is True
    assert output.exists()
    assert handle.params["duration"] == 4
    quality = validate_audio_artifact(output, min_duration_sec=0.5)
    assert quality["ok"] is True
    assert quality["metrics"]["channels"] == 2



def test_ai_pipeline_includes_music_stereo_stage_in_dry_run(tmp_path) -> None:
    from app.core.orchestrator_ai import run_ai_pipeline

    result = run_ai_pipeline("stereo_stage", out_root=tmp_path, dry_run=True)
    stages = {item["name"]: item for item in result["report"]["stages"]}

    assert "music_stereo" in stages
    assert stages["music_stereo"]["skipped_reason"] is not None



def test_stereo_texture_quality_rejects_mono_like_audio(tmp_path) -> None:
    from app.ai.quality import validate_stereo_texture

    sample_rate = 8_000
    t = np.arange(sample_rate * 2) / sample_rate
    left = 0.15 * np.sin(2 * np.pi * 220 * t)
    right = 0.15 * np.cos(2 * np.pi * 330 * t)
    valid_path = tmp_path / "independent_stereo.wav"
    mono_like_path = tmp_path / "duplicated_channels.wav"
    sf.write(valid_path, np.column_stack([left, right]), sample_rate)
    sf.write(mono_like_path, np.column_stack([left, left]), sample_rate)

    valid = validate_stereo_texture(valid_path, min_duration_sec=1.0)
    mono_like = validate_stereo_texture(mono_like_path, min_duration_sec=1.0)

    assert valid["ok"] is True
    assert abs(valid["metrics"]["stereo_correlation"]) < 0.995
    assert mono_like["ok"] is False
    assert mono_like["reason"] in {"stereo side energy too low", "stereo channels are over-correlated"}


class _FakeXTTS:
    def __init__(self):
        self.kwargs = None

    def tts_to_file(self, **kwargs):
        self.kwargs = kwargs
        sample_rate = 8_000
        t = np.arange(sample_rate) / sample_rate
        signal = 0.1 * np.sin(2 * np.pi * 180 * t)
        sf.write(kwargs["file_path"], signal, sample_rate)


class _EmptyXTTS:
    def tts_to_file(self, **kwargs):
        Path(kwargs["file_path"]).write_bytes(b"")


def test_xtts_handle_saves_vocal_artifact_and_propagates_speaker(tmp_path) -> None:
    from app.core.orchestrator_ai import render_xtts_vocal

    speaker = tmp_path / "speaker.wav"
    sf.write(speaker, np.zeros(800), 8_000)
    output = tmp_path / "voice.wav"
    handle = _FakeXTTS()
    result = render_xtts_vocal(handle, "Тестовый вокальный текст", str(output), str(speaker))

    assert result["ok"] is True
    assert result["vocal_path"] == str(output)
    assert handle.kwargs["speaker_wav"] == str(speaker)
    assert handle.kwargs["language"] == "ru"


def test_xtts_handle_rejects_empty_output(tmp_path) -> None:
    from app.core.orchestrator_ai import render_xtts_vocal

    result = render_xtts_vocal(_EmptyXTTS(), "Текст", str(tmp_path / "empty.wav"))

    assert result["ok"] is False
    assert result["reason"] == "XTTS did not produce an audio file"



def test_vocal_quality_accounts_for_text_length(tmp_path) -> None:
    from app.ai.quality import validate_vocal_artifact

    sample_rate = 8_000
    valid = tmp_path / "voice_valid.wav"
    short = tmp_path / "voice_short.wav"
    signal = 0.1 * np.sin(2 * np.pi * 180 * np.arange(sample_rate) / sample_rate)
    sf.write(valid, signal, sample_rate)
    sf.write(short, signal[:500], sample_rate)
    long_text = "слово " * 10

    assert validate_vocal_artifact(valid, long_text)["ok"] is True
    rejected = validate_vocal_artifact(short, long_text)
    assert rejected["ok"] is False
    assert rejected["reason"] == "audio duration below minimum"


def test_voice_synth_fallback_validates_and_copies_audio(tmp_path) -> None:
    from app.core.orchestrator_ai import render_voice_synth_fallback

    source = tmp_path / "draft.wav"
    target = tmp_path / "project" / "vocal_xtts.wav"
    sample_rate = 8_000
    signal = 0.1 * np.sin(2 * np.pi * 160 * np.arange(sample_rate) / sample_rate)
    sf.write(source, signal, sample_rate)

    def fake_synth(text, engine, out_name):
        assert engine == "auto"
        assert out_name == target.name
        return str(source)

    result = render_voice_synth_fallback("проверочный голос", str(target), synth_fn=fake_synth)

    assert result["ok"] is True
    assert result["engine"] == "voice_synth_fallback"
    assert target.exists()


def test_voice_synth_fallback_reports_absence_of_engine(tmp_path) -> None:
    from app.core.orchestrator_ai import render_voice_synth_fallback

    result = render_voice_synth_fallback(
        "текст", str(tmp_path / "voice.wav"), synth_fn=lambda *_, **__: ""
    )

    assert result["ok"] is False
    assert result["reason"] == "no fallback TTS engine produced audio"


class _FakeRVCManager:
    def __init__(self, output_path):
        self.output_path = output_path
        self.kwargs = None

    def infer(self, **kwargs):
        self.kwargs = kwargs
        sample_rate = 8_000
        signal = 0.1 * np.sin(2 * np.pi * 190 * np.arange(sample_rate) / sample_rate)
        sf.write(self.output_path, signal, sample_rate)
        return str(self.output_path)


class _FailingRVCManager:
    def infer(self, **kwargs):
        raise RuntimeError("rvc-python unavailable")


def test_rvc_handle_uses_public_infer_contract_and_copies_result(tmp_path) -> None:
    from app.core.orchestrator_ai import render_rvc_vocal

    input_wav = tmp_path / "input.wav"
    source_output = tmp_path / "rvc_engine.wav"
    project_output = tmp_path / "project" / "vocal_rvc.wav"
    sf.write(input_wav, np.zeros(8_000), 8_000)
    handle = _FakeRVCManager(source_output)

    result = render_rvc_vocal(handle, str(input_wav), str(project_output), "artist_voice", pitch_shift=-2)

    assert result["ok"] is True
    assert result["vocal_path"] == str(project_output)
    assert project_output.exists()
    assert handle.kwargs["input_wav"] == str(input_wav)
    assert handle.kwargs["voice_name"] == "artist_voice"
    assert handle.kwargs["pitch_shift"] == -2


def test_rvc_handle_reports_runtime_error_without_pitch_fallback(tmp_path) -> None:
    from app.core.orchestrator_ai import render_rvc_vocal

    result = render_rvc_vocal(
        _FailingRVCManager(), str(tmp_path / "input.wav"), str(tmp_path / "out.wav"), "artist"
    )

    assert result["ok"] is False
    assert "rvc-python unavailable" in result["reason"]



def test_rvc_quality_requires_duration_preservation(tmp_path) -> None:
    from app.ai.quality import validate_rvc_artifact

    sample_rate = 8_000
    input_path = tmp_path / "input.wav"
    valid_output = tmp_path / "valid.wav"
    short_output = tmp_path / "short.wav"
    signal = 0.1 * np.sin(2 * np.pi * 180 * np.arange(sample_rate) / sample_rate)
    sf.write(input_path, signal, sample_rate)
    sf.write(valid_output, signal, sample_rate)
    sf.write(short_output, signal[:4_000], sample_rate)

    assert validate_rvc_artifact(input_path, valid_output)["ok"] is True
    shortened = validate_rvc_artifact(input_path, short_output)
    assert shortened["ok"] is False
    assert shortened["reason"] == "RVC output duration diverges from input"



def test_stem_quality_requires_near_input_duration(tmp_path) -> None:
    from app.ai.quality import validate_stem_artifact

    sample_rate = 8_000
    original = tmp_path / "original.wav"
    stem = tmp_path / "vocals.wav"
    truncated = tmp_path / "vocals_truncated.wav"
    signal = 0.1 * np.sin(2 * np.pi * 220 * np.arange(sample_rate) / sample_rate)
    sf.write(original, signal, sample_rate)
    sf.write(stem, signal, sample_rate)
    sf.write(truncated, signal[:7_000], sample_rate)

    assert validate_stem_artifact(original, stem)["ok"] is True
    rejected = validate_stem_artifact(original, truncated)
    assert rejected["ok"] is False
    assert rejected["reason"] == "stem duration diverges from input"
