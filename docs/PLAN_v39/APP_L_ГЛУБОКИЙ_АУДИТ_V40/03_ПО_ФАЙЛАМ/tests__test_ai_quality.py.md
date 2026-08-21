# АУДИТ ФАЙЛА: `tests/test_ai_quality.py`

**LOC:** 332  |  **Размер:** 11613 байт  |  **Проблем:** 11  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 5 | `json` | import |
| 6 | `pathlib.Path` | from |
| 8 | `numpy` | import |
| 9 | `soundfile` | import |
| 11 | `app.ai.quality.validate_audio_artifact` | from |
| 11 | `app.ai.quality.validate_metadata_json` | from |
| 57 | `app.core.orchestrator_ai.run_ai_pipeline` | from |
| 100 | `app.core.orchestrator_ai.render_stereo_texture` | from |
| 116 | `app.core.orchestrator_ai.run_ai_pipeline` | from |
| 127 | `app.ai.quality.validate_stereo_texture` | from |
| 165 | `app.core.orchestrator_ai.render_xtts_vocal` | from |
| 180 | `app.core.orchestrator_ai.render_xtts_vocal` | from |
| 190 | `app.ai.quality.validate_vocal_artifact` | from |
| 207 | `app.core.orchestrator_ai.render_voice_synth_fallback` | from |
| 228 | `app.core.orchestrator_ai.render_voice_synth_fallback` | from |
| 257 | `app.core.orchestrator_ai.render_rvc_vocal` | from |
| 276 | `app.core.orchestrator_ai.render_rvc_vocal` | from |
| 288 | `app.ai.quality.validate_rvc_artifact` | from |
| 307 | `app.ai.quality.validate_stem_artifact` | from |
| 326 | `app.ai.quality.validate_asr_transcript` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 14 | `test_metadata_quality_accepts_complete_release_payload` | 12 | 0 | ❌ |
| 29 | `test_metadata_quality_rejects_incomplete_payload` | 6 | 0 | ❌ |
| 38 | `test_audio_quality_accepts_signal_and_rejects_silence` | 15 | 0 | ❌ |
| 56 | `test_ai_dry_run_persists_valid_metadata_fallback` | 8 | 0 | ❌ |
| 99 | `test_music_stereo_handle_renders_separate_stereo_texture` | 12 | 0 | ❌ |
| 115 | `test_ai_pipeline_includes_music_stereo_stage_in_dry_run` | 7 | 0 | ❌ |
| 126 | `test_stereo_texture_quality_rejects_mono_like_audio` | 18 | 0 | ❌ |
| 164 | `test_xtts_handle_saves_vocal_artifact_and_propagates_speaker` | 12 | 0 | ❌ |
| 179 | `test_xtts_handle_rejects_empty_output` | 6 | 0 | ❌ |
| 189 | `test_vocal_quality_accounts_for_text_length` | 14 | 0 | ❌ |
| 206 | `test_voice_synth_fallback_validates_and_copies_audio` | 18 | 0 | ❌ |
| 227 | `test_voice_synth_fallback_reports_absence_of_engine` | 8 | 0 | ❌ |
| 256 | `test_rvc_handle_uses_public_infer_contract_and_copies_result` | 16 | 0 | ❌ |
| 275 | `test_rvc_handle_reports_runtime_error_without_pitch_fallback` | 8 | 0 | ❌ |
| 287 | `test_rvc_quality_requires_duration_preservation` | 15 | 0 | ❌ |
| 306 | `test_stem_quality_requires_near_input_duration` | 15 | 0 | ❌ |
| 325 | `test_asr_transcript_quality_rejects_empty_and_repetitive_text` | 7 | 0 | ❌ |
| 68 | `__init__` | 1 | 0 | ❌ |
| 71 | `detach` | 1 | 0 | ❌ |
| 74 | `cpu` | 1 | 0 | ❌ |
| 77 | `numpy` | 1 | 0 | ❌ |
| 84 | `__init__` | 1 | 0 | ❌ |
| 87 | `set_generation_params` | 1 | 0 | ❌ |
| 90 | `generate` | 6 | 1 | ❌ |
| 148 | `__init__` | 1 | 0 | ❌ |
| 151 | `tts_to_file` | 5 | 0 | ❌ |
| 160 | `tts_to_file` | 1 | 0 | ❌ |
| 215 | `fake_synth` | 3 | 0 | ❌ |
| 239 | `__init__` | 2 | 0 | ❌ |
| 243 | `infer` | 5 | 0 | ❌ |
| 252 | `infer` | 1 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 67 | `_FakeTensor` | ❌ |
| 81 | `_FakeStereoMusicGen` | ❌ |
| 147 | `_FakeXTTS` | ❌ |
| 159 | `_EmptyXTTS` | ❌ |
| 238 | `_FakeRVCManager` | ❌ |
| 251 | `_FailingRVCManager` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 10 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 14** — public function 'test_metadata_quality_accepts_complete_release_payload' без docstring

  ```
         12 | 
         13 | 
  >>>    14 | def test_metadata_quality_accepts_complete_release_payload() -> None:
         15 |     payload = {
         16 |         "title": "Ночной маршрут",
  ```

- **строка 38** — public function 'test_audio_quality_accepts_signal_and_rejects_silence' без docstring

  ```
         36 | 
         37 | 
  >>>    38 | def test_audio_quality_accepts_signal_and_rejects_silence(tmp_path) -> None:
         39 |     sample_rate = 8_000
         40 |     t = np.arange(sample_rate * 2) / sample_rate
  ```

- **строка 99** — public function 'test_music_stereo_handle_renders_separate_stereo_texture' без docstring

  ```
         97 | 
         98 | 
  >>>    99 | def test_music_stereo_handle_renders_separate_stereo_texture(tmp_path) -> None:
        100 |     from app.core.orchestrator_ai import render_stereo_texture
        101 | 
  ```

- **строка 126** — public function 'test_stereo_texture_quality_rejects_mono_like_audio' без docstring

  ```
        124 | 
        125 | 
  >>>   126 | def test_stereo_texture_quality_rejects_mono_like_audio(tmp_path) -> None:
        127 |     from app.ai.quality import validate_stereo_texture
        128 | 
  ```

- **строка 164** — public function 'test_xtts_handle_saves_vocal_artifact_and_propagates_speaker' без docstring

  ```
        162 | 
        163 | 
  >>>   164 | def test_xtts_handle_saves_vocal_artifact_and_propagates_speaker(tmp_path) -> None:
        165 |     from app.core.orchestrator_ai import render_xtts_vocal
        166 | 
  ```

- **строка 189** — public function 'test_vocal_quality_accounts_for_text_length' без docstring

  ```
        187 | 
        188 | 
  >>>   189 | def test_vocal_quality_accounts_for_text_length(tmp_path) -> None:
        190 |     from app.ai.quality import validate_vocal_artifact
        191 | 
  ```

- **строка 206** — public function 'test_voice_synth_fallback_validates_and_copies_audio' без docstring

  ```
        204 | 
        205 | 
  >>>   206 | def test_voice_synth_fallback_validates_and_copies_audio(tmp_path) -> None:
        207 |     from app.core.orchestrator_ai import render_voice_synth_fallback
        208 | 
  ```

- **строка 256** — public function 'test_rvc_handle_uses_public_infer_contract_and_copies_result' без docstring

  ```
        254 | 
        255 | 
  >>>   256 | def test_rvc_handle_uses_public_infer_contract_and_copies_result(tmp_path) -> None:
        257 |     from app.core.orchestrator_ai import render_rvc_vocal
        258 | 
  ```

- **строка 287** — public function 'test_rvc_quality_requires_duration_preservation' без docstring

  ```
        285 | 
        286 | 
  >>>   287 | def test_rvc_quality_requires_duration_preservation(tmp_path) -> None:
        288 |     from app.ai.quality import validate_rvc_artifact
        289 | 
  ```

- **строка 306** — public function 'test_stem_quality_requires_near_input_duration' без docstring

  ```
        304 | 
        305 | 
  >>>   306 | def test_stem_quality_requires_near_input_duration(tmp_path) -> None:
        307 |     from app.ai.quality import validate_stem_artifact
        308 | 
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """Качественные контракты outputs LLM и генерации аудио."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import json
  ```
