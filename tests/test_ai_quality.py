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



def test_asr_transcript_quality_rejects_empty_and_repetitive_text() -> None:
    from app.ai.quality import validate_asr_transcript

    assert validate_asr_transcript("в городе горят огни")["ok"] is True
    assert validate_asr_transcript(" ")["reason"] == "ASR transcript is empty or too short"
    repeated = validate_asr_transcript("эй эй эй эй эй")
    assert repeated["ok"] is False
    assert repeated["reason"] == "ASR transcript is excessively repetitive"



def test_audio_tag_quality_requires_unique_known_subset() -> None:
    from app.ai.quality import validate_audio_tags

    candidates = ["phonk", "trap", "pop"]
    assert validate_audio_tags(["trap", "phonk"], candidates)["ok"] is True
    duplicate = validate_audio_tags(["trap", "trap"], candidates)
    assert duplicate["reason"] == "audio tag output contains duplicates"
    unknown = validate_audio_tags(["trap", "jazz"], candidates)
    assert unknown["reason"] == "audio tag output contains unknown labels"



def test_dsp_feature_quality_requires_musical_complete_metadata() -> None:
    from app.ai.quality import validate_dsp_features

    valid = {"bpm": 128.0, "key": "A", "duration_sec": 180.0, "loudness_rms": 0.12}
    assert validate_dsp_features(valid)["ok"] is True
    assert validate_dsp_features({**valid, "bpm": 0})["reason"] == "DSP BPM is outside musical range"
    assert validate_dsp_features({**valid, "key": "H"})["reason"] == "DSP key is invalid"
    assert validate_dsp_features({**valid, "loudness_rms": 0.0})["reason"] == "DSP audio metrics are invalid"



def test_sdxl_handle_renders_cover_without_nested_registry_load(tmp_path) -> None:
    from types import SimpleNamespace

    from PIL import Image
    from modules.cover_art_ai import render_cover_with_pipeline

    class FakePipeline:
        def __init__(self):
            self.kwargs = None

        def __call__(self, **kwargs):
            self.kwargs = kwargs
            return SimpleNamespace(images=[Image.new("RGB", (64, 64), color=(12, 34, 56))])

    handle = FakePipeline()
    output = tmp_path / "cover.png"
    result = render_cover_with_pipeline(handle, "dark neon artwork", str(output), size=64)

    assert result["ok"] is True
    assert output.exists()
    assert handle.kwargs["width"] == 64
    assert handle.kwargs["height"] == 64


def test_sdxl_handle_reports_generation_failure(tmp_path) -> None:
    from modules.cover_art_ai import render_cover_with_pipeline

    class FailingPipeline:
        def __call__(self, **kwargs):
            raise RuntimeError("scheduler failed")

    result = render_cover_with_pipeline(FailingPipeline(), "prompt", str(tmp_path / "cover.png"))

    assert result["ok"] is False
    assert "scheduler failed" in result["reason"]



def test_cover_quality_requires_readable_large_rgb_artifact(tmp_path) -> None:
    from PIL import Image

    from app.ai.quality import validate_cover_artifact

    valid = tmp_path / "valid.png"
    small = tmp_path / "small.png"
    grayscale = tmp_path / "gray.png"
    Image.new("RGB", (512, 512), color=(1, 2, 3)).save(valid)
    Image.new("RGB", (128, 128), color=(1, 2, 3)).save(small)
    Image.new("L", (512, 512), color=120).save(grayscale)

    assert validate_cover_artifact(valid)["ok"] is True
    assert validate_cover_artifact(small)["reason"] == "cover resolution is below minimum"
    assert validate_cover_artifact(grayscale)["reason"] == "cover color mode is unsupported"



def test_matchering_handle_processes_reference_without_registry_reload(tmp_path) -> None:
    from pathlib import Path

    from modules.mastering_ai import master_with_matchering

    class FakeMatchering:
        def __init__(self):
            self.calls = []

        def pcm16(self, path):
            return path

        def process(self, **kwargs):
            self.calls.append(kwargs)
            Path(kwargs["results"][0]).write_bytes(b"mastered-audio")

    output = tmp_path / "master.wav"
    handle = FakeMatchering()
    result = master_with_matchering(handle, "mix.wav", str(output), "reference.wav")

    assert result["ok"] is True
    assert result["engine"] == "matchering"
    assert output.exists()
    assert handle.calls[0]["target"] == "mix.wav"
    assert handle.calls[0]["reference"] == "reference.wav"


def test_matchering_handle_rejects_missing_output(tmp_path) -> None:
    from modules.mastering_ai import master_with_matchering

    class SilentMatchering:
        def pcm16(self, path):
            return path

        def process(self, **kwargs):
            return None

    result = master_with_matchering(SilentMatchering(), "mix.wav", str(tmp_path / "master.wav"), "reference.wav")

    assert result["ok"] is False
    assert result["reason"] == "matchering completed without output"



def _write_master_candidate(path, *, seconds=2.0, amplitude=0.5, stereo=True) -> None:
    sample_rate = 8_000
    t = np.arange(int(sample_rate * seconds)) / sample_rate
    left = amplitude * np.sin(2 * np.pi * 220 * t)
    right = amplitude * np.sin(2 * np.pi * 330 * t)
    audio = np.column_stack([left, right]) if stereo else left
    sf.write(path, audio.astype("float32"), sample_rate)


def test_master_quality_accepts_stereo_loudness_and_true_peak_within_contract(tmp_path) -> None:
    from app.ai.quality import validate_master_artifact

    mix = tmp_path / "mix.wav"
    master = tmp_path / "master.wav"
    _write_master_candidate(mix)
    _write_master_candidate(master)

    result = validate_master_artifact(mix, master)

    assert result["ok"] is True
    assert result["metrics"]["channels"] == 2
    assert result["metrics"]["true_peak_dbtp"] <= -0.5
    assert -20.0 <= result["metrics"]["rms_dbfs"] <= -5.0


def test_master_quality_rejects_true_peak_above_ceiling(tmp_path) -> None:
    from app.ai.quality import validate_master_artifact

    mix = tmp_path / "mix.wav"
    too_loud = tmp_path / "too_loud.wav"
    _write_master_candidate(mix)
    _write_master_candidate(too_loud, amplitude=0.99)

    result = validate_master_artifact(mix, too_loud)

    assert result["ok"] is False
    assert result["reason"] == "master true peak exceeds ceiling"


def test_master_quality_rejects_mono_output(tmp_path) -> None:
    from app.ai.quality import validate_master_artifact

    mix = tmp_path / "mix.wav"
    mono_master = tmp_path / "mono_master.wav"
    _write_master_candidate(mix)
    _write_master_candidate(mono_master, stereo=False)

    result = validate_master_artifact(mix, mono_master)

    assert result["ok"] is False
    assert result["reason"] == "master is not stereo"


def test_master_quality_rejects_duration_divergence(tmp_path) -> None:
    from app.ai.quality import validate_master_artifact

    mix = tmp_path / "mix.wav"
    short_master = tmp_path / "short_master.wav"
    _write_master_candidate(mix, seconds=2.0)
    _write_master_candidate(short_master, seconds=1.0)

    result = validate_master_artifact(mix, short_master)

    assert result["ok"] is False
    assert result["reason"] == "master duration diverges from mix"


def test_master_quality_rejects_rms_outside_target_range(tmp_path) -> None:
    from app.ai.quality import validate_master_artifact

    mix = tmp_path / "mix.wav"
    quiet_master = tmp_path / "quiet_master.wav"
    _write_master_candidate(mix)
    _write_master_candidate(quiet_master, amplitude=0.03)

    result = validate_master_artifact(mix, quiet_master)

    assert result["ok"] is False
    assert result["reason"] == "master RMS is outside target range"


def test_master_quality_rejects_missing_output(tmp_path) -> None:
    from app.ai.quality import validate_master_artifact

    mix = tmp_path / "mix.wav"
    _write_master_candidate(mix)

    result = validate_master_artifact(mix, tmp_path / "missing.wav")

    assert result["ok"] is False
    assert result["reason"] == "audio file missing"



def test_song_lyrics_quality_requires_release_structure_and_user_lines() -> None:
    from app.ai.quality import validate_song_lyrics

    verse_one = [f"Ночной маршрут {index} несёт меня через кварталы города" for index in range(40)]
    verse_two = [f"Неоновый ритм {index} помогает не терять направление" for index in range(40)]
    hook = [
        "Мы летим выше огней и не теряем свой путь",
        "Сквозь холодный воздух город оставляет свой след",
    ] * 2
    text = "\n".join([
        "[Куплет 1]", *verse_one, "[Hook]", *hook,
        "[Куплет 2]", *verse_two, "[Hook]", *hook,
        "Моя обязательная строка",
    ])

    result = validate_song_lyrics(text, user_lines=["Моя обязательная строка"])

    assert result["ok"] is True
    assert 200 <= result["metrics"]["words"] <= 800
    assert result["metrics"]["hook_headers"] == 2


def test_song_lyrics_quality_rejects_missing_structure_or_ai_filler() -> None:
    from app.ai.quality import validate_song_lyrics

    short = "[Куплет 1]\n" + "\n".join(
        f"Уникальная строка номер {index} звучит в темноте" for index in range(80)
    )
    assert validate_song_lyrics(short)["reason"] == "lyrics require at least two verses"

    def section(start: int) -> str:
        return "\n".join(
            f"Уникальная строка номер {index} звучит в темноте" for index in range(start, start + 25)
        )

    filler = "\n".join([
        "[Куплет 1]", section(0), "[Hook]", section(25),
        "[Куплет 2]", section(50), "[Hook]", section(75), "как ии",
    ])
    assert validate_song_lyrics(filler)["reason"] == "lyrics contain prohibited AI filler"


def test_punch_library_fallback_meets_release_lyrics_contract(monkeypatch) -> None:
    import modules.lyrics_gen as lyrics_gen
    from app.ai.quality import validate_song_lyrics

    monkeypatch.setattr(lyrics_gen, "_try_ollama", lambda _prompt: None)
    monkeypatch.setattr(lyrics_gen, "_save_lyric_memory", lambda _entry: None)
    generated = lyrics_gen.generate_lyrics(
        "ночь город скорость", n_verses=2, bilingual=True,
        user_lyrics_lines=["Моя обязательная строка"],
    )

    quality = validate_song_lyrics(generated["lyrics"], user_lines=["Моя обязательная строка"])

    assert generated["source"] == "template"
    assert quality["ok"] is True



class _FakeBeatTensor:
    def __init__(self, value):
        self.value = value

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.value


class _FakeBeatMusicGen:
    sample_rate = 8_000

    def __init__(self, *, samples=8_000):
        self.samples = samples
        self.params = None
        self.generate_calls = 0

    def set_generation_params(self, **kwargs):
        self.params = kwargs

    def generate(self, prompts, progress=False):
        assert prompts and progress is False
        self.generate_calls += 1
        t = np.arange(self.samples) / self.sample_rate
        audio = np.vstack([
            0.25 * np.sin(2 * np.pi * 180 * t),
            0.25 * np.sin(2 * np.pi * 230 * t),
        ])
        return [_FakeBeatTensor(audio)]


def test_beat_gen_ai_uses_runner_handle_and_writes_exact_duration(tmp_path) -> None:
    from modules.beat_gen_ai import render_beat_ai

    handle = _FakeBeatMusicGen()
    output = tmp_path / "beat.wav"
    result = render_beat_ai(
        "dark phonk 140 BPM", bpm=140, duration_sec=2, out_path=str(output),
        chunk_sec=1, reference_wav="reference.wav", handle=handle,
    )

    assert result["ok"] is True
    assert result["chunks"] == 2
    assert result["reference_wav"] == "reference.wav"
    assert result["reference_applied"] is False
    assert handle.params["duration"] == 1
    quality = validate_audio_artifact(output, min_duration_sec=1.9)
    assert quality["ok"] is True
    assert quality["metrics"]["duration_sec"] == 2.0
    assert quality["metrics"]["peak"] < 0.99


def test_beat_gen_ai_rejects_short_generator_output(tmp_path) -> None:
    from modules.beat_gen_ai import render_beat_ai

    result = render_beat_ai(
        "short", duration_sec=2, out_path=str(tmp_path / "short.wav"), chunk_sec=2,
        handle=_FakeBeatMusicGen(samples=8_000),
    )

    assert result["ok"] is False
    assert result["reason"] == "music generator returned fewer samples than requested duration"



def test_voice_synth_ai_uses_xtts_and_public_rvc_infer_contract(tmp_path) -> None:
    from modules.voice_synth_ai import synth_vocal_ai

    xtts_output = tmp_path / "vocal_xtts.wav"
    rvc_engine_output = tmp_path / "rvc_engine.wav"
    result = synth_vocal_ai(
        "Проверочный вокальный текст для RVC",
        str(xtts_output),
        tts_handle=_FakeXTTS(),
        rvc_handle=_FakeRVCManager(rvc_engine_output),
        rvc_voice_name="artist_voice",
        pitch_shift=2,
    )

    assert result["ok"] is True
    assert result["engine"] == "xtts_v2"
    assert result["rvc_applied"] is True
    assert result["rvc"]["voice_name"] == "artist_voice"
    assert result["rvc"]["pitch_shift"] == 2
    assert Path(result["vocal_path"]).exists()


def test_rvc_quality_rejects_dc_offset(tmp_path) -> None:
    from app.ai.quality import validate_rvc_artifact

    sample_rate = 8_000
    samples = np.arange(sample_rate) / sample_rate
    source = 0.1 * np.sin(2 * np.pi * 180 * samples)
    input_wav = tmp_path / "input.wav"
    offset_wav = tmp_path / "offset.wav"
    sf.write(input_wav, source, sample_rate)
    sf.write(offset_wav, source + 0.03, sample_rate)

    result = validate_rvc_artifact(input_wav, offset_wav)

    assert result["ok"] is False
    assert result["reason"] == "RVC output DC offset is too high"
