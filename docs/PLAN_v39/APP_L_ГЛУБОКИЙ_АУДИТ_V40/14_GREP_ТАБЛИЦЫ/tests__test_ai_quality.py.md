# grep-таблицы `tests/test_ai_quality.py`

## `import` — 20 совпадений
```
    3 | from __future__ import annotations
    5 | import json
    6 | from pathlib import Path
    8 | import numpy as np
    9 | import soundfile as sf
   11 | from app.ai.quality import validate_audio_artifact, validate_metadata_json
   57 |     from app.core.orchestrator_ai import run_ai_pipeline
  100 |     from app.core.orchestrator_ai import render_stereo_texture
  116 |     from app.core.orchestrator_ai import run_ai_pipeline
  127 |     from app.ai.quality import validate_stereo_texture
  165 |     from app.core.orchestrator_ai import render_xtts_vocal
  180 |     from app.core.orchestrator_ai import render_xtts_vocal
  190 |     from app.ai.quality import validate_vocal_artifact
  207 |     from app.core.orchestrator_ai import render_voice_synth_fallback
  228 |     from app.core.orchestrator_ai import render_voice_synth_fallback
  257 |     from app.core.orchestrator_ai import render_rvc_vocal
  276 |     from app.core.orchestrator_ai import render_rvc_vocal
  288 |     from app.ai.quality import validate_rvc_artifact
  307 |     from app.ai.quality import validate_stem_artifact
  326 |     from app.ai.quality import validate_asr_transcript
```

## `def` — 31 совпадений
```
   14 | def test_metadata_quality_accepts_complete_release_payload() -> None:
   29 | def test_metadata_quality_rejects_incomplete_payload() -> None:
   38 | def test_audio_quality_accepts_signal_and_rejects_silence(tmp_path) -> None:
   56 | def test_ai_dry_run_persists_valid_metadata_fallback(tmp_path) -> None:
   68 |     def __init__(self, value):
   71 |     def detach(self):
   74 |     def cpu(self):
   77 |     def numpy(self):
   84 |     def __init__(self):
   87 |     def set_generation_params(self, **kwargs):
   90 |     def generate(self, prompts, progress=False):
   99 | def test_music_stereo_handle_renders_separate_stereo_texture(tmp_path) -> None:
  115 | def test_ai_pipeline_includes_music_stereo_stage_in_dry_run(tmp_path) -> None:
  126 | def test_stereo_texture_quality_rejects_mono_like_audio(tmp_path) -> None:
  148 |     def __init__(self):
  151 |     def tts_to_file(self, **kwargs):
  160 |     def tts_to_file(self, **kwargs):
  164 | def test_xtts_handle_saves_vocal_artifact_and_propagates_speaker(tmp_path) -> None:
  179 | def test_xtts_handle_rejects_empty_output(tmp_path) -> None:
  189 | def test_vocal_quality_accounts_for_text_length(tmp_path) -> None:
  206 | def test_voice_synth_fallback_validates_and_copies_audio(tmp_path) -> None:
  215 |     def fake_synth(text, engine, out_name):
  227 | def test_voice_synth_fallback_reports_absence_of_engine(tmp_path) -> None:
  239 |     def __init__(self, output_path):
  243 |     def infer(self, **kwargs):
  252 |     def infer(self, **kwargs):
  256 | def test_rvc_handle_uses_public_infer_contract_and_copies_result(tmp_path) -> None:
  275 | def test_rvc_handle_reports_runtime_error_without_pitch_fallback(tmp_path) -> None:
  287 | def test_rvc_quality_requires_duration_preservation(tmp_path) -> None:
  306 | def test_stem_quality_requires_near_input_duration(tmp_path) -> None:
  325 | def test_asr_transcript_quality_rejects_empty_and_repetitive_text() -> None:
```

## `class` — 6 совпадений
```
   67 | class _FakeTensor:
   81 | class _FakeStereoMusicGen:
  147 | class _FakeXTTS:
  159 | class _EmptyXTTS:
  238 | class _FakeRVCManager:
  251 | class _FailingRVCManager:
```

## `raise` — 1 совпадений
```
  253 |         raise RuntimeError("rvc-python unavailable")
```

## `return` — 6 совпадений
```
   72 |         return self
   75 |         return self
   78 |         return self.value
   96 |         return [_FakeTensor(signal)]
  218 |         return str(source)
  248 |         return str(self.output_path)
```

## `assert` — 59 совпадений
```
   25 |     assert result["ok"] is True
   26 |     assert result["metrics"]["tags"] == 3
   32 |     assert result["ok"] is False
   33 |     assert "title" in result["reason"]
   34 |     assert "description" in result["reason"]
   35 |     assert "tags" in result["reason"]
   50 |     assert valid["ok"] is True
   51 |     assert valid["metrics"]["channels"] == 2
   52 |     assert silent["ok"] is False
   53 |     assert silent["reason"] == "audio is silent"
   62 |     assert metadata["ok"] is True
   63 |     assert metadata["source"] == "dry"
   64 |     assert metadata["quality"]["ok"] is True
   91 |         assert prompts and progress is False
  106 |     assert result["ok"] is True
  107 |     assert output.exists()
  108 |     assert handle.params["duration"] == 4
  110 |     assert quality["ok"] is True
  111 |     assert quality["metrics"]["channels"] == 2
  121 |     assert "music_stereo" in stages
  122 |     assert stages["music_stereo"]["skipped_reason"] is not None
  141 |     assert valid["ok"] is True
  142 |     assert abs(valid["metrics"]["stereo_correlation"]) < 0.995
  143 |     assert mono_like["ok"] is False
  144 |     assert mono_like["reason"] in {"stereo side energy too low", "stereo channels are over-correlated"}
  173 |     assert result["ok"] is True
  174 |     assert result["vocal_path"] == str(output)
  175 |     assert handle.kwargs["speaker_wav"] == str(speaker)
  176 |     assert handle.kwargs["language"] == "ru"
  184 |     assert result["ok"] is False
  185 |     assert result["reason"] == "XTTS did not produce an audio file"
  200 |     assert validate_vocal_artifact(valid, long_text)["ok"] is True
  202 |     assert rejected["ok"] is False
  203 |     assert rejected["reason"] == "audio duration below minimum"
  216 |         assert engine == "auto"
  217 |         assert out_name == target.name
  222 |     assert result["ok"] is True
  223 |     assert result["engine"] == "voice_synth_fallback"
  224 |     assert target.exists()
  234 |     assert result["ok"] is False
  235 |     assert result["reason"] == "no fallback TTS engine produced audio"
  267 |     assert result["ok"] is True
  268 |     assert result["vocal_path"] == str(project_output)
  269 |     assert project_output.exists()
  270 |     assert handle.kwargs["input_wav"] == str(input_wav)
  271 |     assert handle.kwargs["voice_name"] == "artist_voice"
  272 |     assert handle.kwargs["pitch_shift"] == -2
  282 |     assert result["ok"] is False
  283 |     assert "rvc-python unavailable" in result["reason"]
  299 |     assert validate_rvc_artifact(input_path, valid_output)["ok"] is True
  301 |     assert shortened["ok"] is False
  302 |     assert shortened["reason"] == "RVC output duration diverges from input"
  318 |     assert validate_stem_artifact(original, stem)["ok"] is True
  320 |     assert rejected["ok"] is False
  321 |     assert rejected["reason"] == "stem duration diverges from input"
  328 |     assert validate_asr_transcript("в городе горят огни")["ok"] is True
  329 |     assert validate_asr_transcript(" ")["reason"] == "ASR transcript is empty or too short"
  331 |     assert repeated["ok"] is False
  332 |     assert repeated["reason"] == "ASR transcript is excessively repetitive"
```

## `np` — 21 совпадений
```
   40 |     t = np.arange(sample_rate * 2) / sample_rate
   41 |     signal = (0.2 * np.sin(2 * np.pi * 220 * t)).astype("float32")
   44 |     sf.write(valid_path, np.column_stack([signal, signal]), sample_rate)
   45 |     sf.write(silent_path, np.zeros((sample_rate * 2, 2), dtype="float32"), sample_rate)
   92 |         signal = np.vstack([
   93 |             0.1 * np.sin(np.linspace(0, 100, 8_000)),
   94 |             0.1 * np.cos(np.linspace(0, 100, 8_000)),
  130 |     t = np.arange(sample_rate * 2) / sample_rate
  131 |     left = 0.15 * np.sin(2 * np.pi * 220 * t)
  132 |     right = 0.15 * np.cos(2 * np.pi * 330 * t)
  135 |     sf.write(valid_path, np.column_stack([left, right]), sample_rate)
  136 |     sf.write(mono_like_path, np.column_stack([left, left]), sample_rate)
  154 |         t = np.arange(sample_rate) / sample_rate
  155 |         signal = 0.1 * np.sin(2 * np.pi * 180 * t)
  168 |     sf.write(speaker, np.zeros(800), 8_000)
  195 |     signal = 0.1 * np.sin(2 * np.pi * 180 * np.arange(sample_rate) / sample_rate)
  212 |     signal = 0.1 * np.sin(2 * np.pi * 160 * np.arange(sample_rate) / sample_rate)
  246 |         signal = 0.1 * np.sin(2 * np.pi * 190 * np.arange(sample_rate) / sample_rate)
  262 |     sf.write(input_wav, np.zeros(8_000), 8_000)
  294 |     signal = 0.1 * np.sin(2 * np.pi * 180 * np.arange(sample_rate) / sample_rate)
  313 |     signal = 0.1 * np.sin(2 * np.pi * 220 * np.arange(sample_rate) / sample_rate)
```

## `sf` — 17 совпадений
```
   44 |     sf.write(valid_path, np.column_stack([signal, signal]), sample_rate)
   45 |     sf.write(silent_path, np.zeros((sample_rate * 2, 2), dtype="float32"), sample_rate)
  135 |     sf.write(valid_path, np.column_stack([left, right]), sample_rate)
  136 |     sf.write(mono_like_path, np.column_stack([left, left]), sample_rate)
  156 |         sf.write(kwargs["file_path"], signal, sample_rate)
  168 |     sf.write(speaker, np.zeros(800), 8_000)
  196 |     sf.write(valid, signal, sample_rate)
  197 |     sf.write(short, signal[:500], sample_rate)
  213 |     sf.write(source, signal, sample_rate)
  247 |         sf.write(self.output_path, signal, sample_rate)
  262 |     sf.write(input_wav, np.zeros(8_000), 8_000)
  295 |     sf.write(input_path, signal, sample_rate)
  296 |     sf.write(valid_output, signal, sample_rate)
  297 |     sf.write(short_output, signal[:4_000], sample_rate)
  314 |     sf.write(original, signal, sample_rate)
  315 |     sf.write(stem, signal, sample_rate)
  316 |     sf.write(truncated, signal[:7_000], sample_rate)
```
