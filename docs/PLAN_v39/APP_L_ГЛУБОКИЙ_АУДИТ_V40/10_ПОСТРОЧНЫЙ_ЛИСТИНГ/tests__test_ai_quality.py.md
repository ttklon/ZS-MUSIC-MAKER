# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_ai_quality.py`

**Всего строк:** 332

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 108 | 32.5 |
| blank | 99 | 29.8 |
| stmt | 59 | 17.8 |
| def | 31 | 9.3 |
| import | 20 | 6.0 |
| class | 6 | 1.8 |
| return | 6 | 1.8 |
| comment | 1 | 0.3 |
| docstring | 1 | 0.3 |
| raise | 1 | 0.3 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """Качественные контракты outputs LLM и генерации аудио."""
    3 [import    ] from __future__ import annotations
    4 [blank     ] 
    5 [import    ] import json
    6 [import    ] from pathlib import Path
    7 [blank     ] 
    8 [import    ] import numpy as np
    9 [import    ] import soundfile as sf
   10 [blank     ] 
   11 [import    ] from app.ai.quality import validate_audio_artifact, validate_metadata_json
   12 [blank     ] 
   13 [blank     ] 
   14 [def       ] def test_metadata_quality_accepts_complete_release_payload() -> None:
   15 [code      ]     payload = {
   16 [code      ]         "title": "Ночной маршрут",
   17 [code      ]         "spotify_desc": "Динамичный phonk-трек для ночной дороги.",
   18 [code      ]         "youtube_desc": "Премьера независимого трека.",
   19 [code      ]         "tags_tiktok": ["phonk", "newmusic"],
   20 [code      ]         "tags_instagram": ["music"],
   21 [code      ]     }
   22 [blank     ] 
   23 [code      ]     result = validate_metadata_json(payload)
   24 [blank     ] 
   25 [stmt      ]     assert result["ok"] is True
   26 [stmt      ]     assert result["metrics"]["tags"] == 3
   27 [blank     ] 
   28 [blank     ] 
   29 [def       ] def test_metadata_quality_rejects_incomplete_payload() -> None:
   30 [code      ]     result = validate_metadata_json({"title": "x", "tags_tiktok": []})
   31 [blank     ] 
   32 [stmt      ]     assert result["ok"] is False
   33 [stmt      ]     assert "title" in result["reason"]
   34 [stmt      ]     assert "description" in result["reason"]
   35 [stmt      ]     assert "tags" in result["reason"]
   36 [blank     ] 
   37 [blank     ] 
   38 [def       ] def test_audio_quality_accepts_signal_and_rejects_silence(tmp_path) -> None:
   39 [code      ]     sample_rate = 8_000
   40 [code      ]     t = np.arange(sample_rate * 2) / sample_rate
   41 [code      ]     signal = (0.2 * np.sin(2 * np.pi * 220 * t)).astype("float32")
   42 [code      ]     valid_path = tmp_path / "signal.wav"
   43 [code      ]     silent_path = tmp_path / "silent.wav"
   44 [code      ]     sf.write(valid_path, np.column_stack([signal, signal]), sample_rate)
   45 [code      ]     sf.write(silent_path, np.zeros((sample_rate * 2, 2), dtype="float32"), sample_rate)
   46 [blank     ] 
   47 [code      ]     valid = validate_audio_artifact(valid_path, min_duration_sec=1.5)
   48 [code      ]     silent = validate_audio_artifact(silent_path, min_duration_sec=1.0)
   49 [blank     ] 
   50 [stmt      ]     assert valid["ok"] is True
   51 [stmt      ]     assert valid["metrics"]["channels"] == 2
   52 [stmt      ]     assert silent["ok"] is False
   53 [stmt      ]     assert silent["reason"] == "audio is silent"
   54 [blank     ] 
   55 [blank     ] 
   56 [def       ] def test_ai_dry_run_persists_valid_metadata_fallback(tmp_path) -> None:
   57 [import    ]     from app.core.orchestrator_ai import run_ai_pipeline
   58 [blank     ] 
   59 [code      ]     run_ai_pipeline("metadata_quality", out_root=tmp_path, dry_run=True)
   60 [code      ]     metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
   61 [blank     ] 
   62 [stmt      ]     assert metadata["ok"] is True
   63 [stmt      ]     assert metadata["source"] == "dry"
   64 [stmt      ]     assert metadata["quality"]["ok"] is True
   65 [blank     ] 
   66 [blank     ] 
   67 [class     ] class _FakeTensor:
   68 [def       ]     def __init__(self, value):
   69 [code      ]         self.value = value
   70 [blank     ] 
   71 [def       ]     def detach(self):
   72 [return    ]         return self
   73 [blank     ] 
   74 [def       ]     def cpu(self):
   75 [return    ]         return self
   76 [blank     ] 
   77 [def       ]     def numpy(self):
   78 [return    ]         return self.value
   79 [blank     ] 
   80 [blank     ] 
   81 [class     ] class _FakeStereoMusicGen:
   82 [code      ]     sample_rate = 8_000
   83 [blank     ] 
   84 [def       ]     def __init__(self):
   85 [code      ]         self.params = None
   86 [blank     ] 
   87 [def       ]     def set_generation_params(self, **kwargs):
   88 [code      ]         self.params = kwargs
   89 [blank     ] 
   90 [def       ]     def generate(self, prompts, progress=False):
   91 [stmt      ]         assert prompts and progress is False
   92 [code      ]         signal = np.vstack([
   93 [code      ]             0.1 * np.sin(np.linspace(0, 100, 8_000)),
   94 [code      ]             0.1 * np.cos(np.linspace(0, 100, 8_000)),
   95 [code      ]         ])
   96 [return    ]         return [_FakeTensor(signal)]
   97 [blank     ] 
   98 [blank     ] 
   99 [def       ] def test_music_stereo_handle_renders_separate_stereo_texture(tmp_path) -> None:
  100 [import    ]     from app.core.orchestrator_ai import render_stereo_texture
  101 [blank     ] 
  102 [code      ]     handle = _FakeStereoMusicGen()
  103 [code      ]     output = tmp_path / "texture.wav"
  104 [code      ]     result = render_stereo_texture(handle, "wide transition texture", 4, str(output))
  105 [blank     ] 
  106 [stmt      ]     assert result["ok"] is True
  107 [stmt      ]     assert output.exists()
  108 [stmt      ]     assert handle.params["duration"] == 4
  109 [code      ]     quality = validate_audio_artifact(output, min_duration_sec=0.5)
  110 [stmt      ]     assert quality["ok"] is True
  111 [stmt      ]     assert quality["metrics"]["channels"] == 2
  112 [blank     ] 
  113 [blank     ] 
  114 [blank     ] 
  115 [def       ] def test_ai_pipeline_includes_music_stereo_stage_in_dry_run(tmp_path) -> None:
  116 [import    ]     from app.core.orchestrator_ai import run_ai_pipeline
  117 [blank     ] 
  118 [code      ]     result = run_ai_pipeline("stereo_stage", out_root=tmp_path, dry_run=True)
  119 [code      ]     stages = {item["name"]: item for item in result["report"]["stages"]}
  120 [blank     ] 
  121 [stmt      ]     assert "music_stereo" in stages
  122 [stmt      ]     assert stages["music_stereo"]["skipped_reason"] is not None
  123 [blank     ] 
  124 [blank     ] 
  125 [blank     ] 
  126 [def       ] def test_stereo_texture_quality_rejects_mono_like_audio(tmp_path) -> None:
  127 [import    ]     from app.ai.quality import validate_stereo_texture
  128 [blank     ] 
  129 [code      ]     sample_rate = 8_000
  130 [code      ]     t = np.arange(sample_rate * 2) / sample_rate
  131 [code      ]     left = 0.15 * np.sin(2 * np.pi * 220 * t)
  132 [code      ]     right = 0.15 * np.cos(2 * np.pi * 330 * t)
  133 [code      ]     valid_path = tmp_path / "independent_stereo.wav"
  134 [code      ]     mono_like_path = tmp_path / "duplicated_channels.wav"
  135 [code      ]     sf.write(valid_path, np.column_stack([left, right]), sample_rate)
  136 [code      ]     sf.write(mono_like_path, np.column_stack([left, left]), sample_rate)
  137 [blank     ] 
  138 [code      ]     valid = validate_stereo_texture(valid_path, min_duration_sec=1.0)
  139 [code      ]     mono_like = validate_stereo_texture(mono_like_path, min_duration_sec=1.0)
  140 [blank     ] 
  141 [stmt      ]     assert valid["ok"] is True
  142 [stmt      ]     assert abs(valid["metrics"]["stereo_correlation"]) < 0.995
  143 [stmt      ]     assert mono_like["ok"] is False
  144 [stmt      ]     assert mono_like["reason"] in {"stereo side energy too low", "stereo channels are over-correlated"}
  145 [blank     ] 
  146 [blank     ] 
  147 [class     ] class _FakeXTTS:
  148 [def       ]     def __init__(self):
  149 [code      ]         self.kwargs = None
  150 [blank     ] 
  151 [def       ]     def tts_to_file(self, **kwargs):
  152 [code      ]         self.kwargs = kwargs
  153 [code      ]         sample_rate = 8_000
  154 [code      ]         t = np.arange(sample_rate) / sample_rate
  155 [code      ]         signal = 0.1 * np.sin(2 * np.pi * 180 * t)
  156 [code      ]         sf.write(kwargs["file_path"], signal, sample_rate)
  157 [blank     ] 
  158 [blank     ] 
  159 [class     ] class _EmptyXTTS:
  160 [def       ]     def tts_to_file(self, **kwargs):
  161 [code      ]         Path(kwargs["file_path"]).write_bytes(b"")
  162 [blank     ] 
  163 [blank     ] 
  164 [def       ] def test_xtts_handle_saves_vocal_artifact_and_propagates_speaker(tmp_path) -> None:
  165 [import    ]     from app.core.orchestrator_ai import render_xtts_vocal
  166 [blank     ] 
  167 [code      ]     speaker = tmp_path / "speaker.wav"
  168 [code      ]     sf.write(speaker, np.zeros(800), 8_000)
  169 [code      ]     output = tmp_path / "voice.wav"
  170 [code      ]     handle = _FakeXTTS()
  171 [code      ]     result = render_xtts_vocal(handle, "Тестовый вокальный текст", str(output), str(speaker))
  172 [blank     ] 
  173 [stmt      ]     assert result["ok"] is True
  174 [stmt      ]     assert result["vocal_path"] == str(output)
  175 [stmt      ]     assert handle.kwargs["speaker_wav"] == str(speaker)
  176 [stmt      ]     assert handle.kwargs["language"] == "ru"
  177 [blank     ] 
  178 [blank     ] 
  179 [def       ] def test_xtts_handle_rejects_empty_output(tmp_path) -> None:
  180 [import    ]     from app.core.orchestrator_ai import render_xtts_vocal
  181 [blank     ] 
  182 [code      ]     result = render_xtts_vocal(_EmptyXTTS(), "Текст", str(tmp_path / "empty.wav"))
  183 [blank     ] 
  184 [stmt      ]     assert result["ok"] is False
  185 [stmt      ]     assert result["reason"] == "XTTS did not produce an audio file"
  186 [blank     ] 
  187 [blank     ] 
  188 [blank     ] 
  189 [def       ] def test_vocal_quality_accounts_for_text_length(tmp_path) -> None:
  190 [import    ]     from app.ai.quality import validate_vocal_artifact
  191 [blank     ] 
  192 [code      ]     sample_rate = 8_000
  193 [code      ]     valid = tmp_path / "voice_valid.wav"
  194 [code      ]     short = tmp_path / "voice_short.wav"
  195 [code      ]     signal = 0.1 * np.sin(2 * np.pi * 180 * np.arange(sample_rate) / sample_rate)
  196 [code      ]     sf.write(valid, signal, sample_rate)
  197 [code      ]     sf.write(short, signal[:500], sample_rate)
  198 [code      ]     long_text = "слово " * 10
  199 [blank     ] 
  200 [stmt      ]     assert validate_vocal_artifact(valid, long_text)["ok"] is True
  201 [code      ]     rejected = validate_vocal_artifact(short, long_text)
  202 [stmt      ]     assert rejected["ok"] is False
  203 [stmt      ]     assert rejected["reason"] == "audio duration below minimum"
  204 [blank     ] 
  205 [blank     ] 
  206 [def       ] def test_voice_synth_fallback_validates_and_copies_audio(tmp_path) -> None:
  207 [import    ]     from app.core.orchestrator_ai import render_voice_synth_fallback
  208 [blank     ] 
  209 [code      ]     source = tmp_path / "draft.wav"
  210 [code      ]     target = tmp_path / "project" / "vocal_xtts.wav"
  211 [code      ]     sample_rate = 8_000
  212 [code      ]     signal = 0.1 * np.sin(2 * np.pi * 160 * np.arange(sample_rate) / sample_rate)
  213 [code      ]     sf.write(source, signal, sample_rate)
  214 [blank     ] 
  215 [def       ]     def fake_synth(text, engine, out_name):
  216 [stmt      ]         assert engine == "auto"
  217 [stmt      ]         assert out_name == target.name
  218 [return    ]         return str(source)
  219 [blank     ] 
  220 [code      ]     result = render_voice_synth_fallback("проверочный голос", str(target), synth_fn=fake_synth)
  221 [blank     ] 
  222 [stmt      ]     assert result["ok"] is True
  223 [stmt      ]     assert result["engine"] == "voice_synth_fallback"
  224 [stmt      ]     assert target.exists()
  225 [blank     ] 
  226 [blank     ] 
  227 [def       ] def test_voice_synth_fallback_reports_absence_of_engine(tmp_path) -> None:
  228 [import    ]     from app.core.orchestrator_ai import render_voice_synth_fallback
  229 [blank     ] 
  230 [code      ]     result = render_voice_synth_fallback(
  231 [code      ]         "текст", str(tmp_path / "voice.wav"), synth_fn=lambda *_, **__: ""
  232 [code      ]     )
  233 [blank     ] 
  234 [stmt      ]     assert result["ok"] is False
  235 [stmt      ]     assert result["reason"] == "no fallback TTS engine produced audio"
  236 [blank     ] 
  237 [blank     ] 
  238 [class     ] class _FakeRVCManager:
  239 [def       ]     def __init__(self, output_path):
  240 [code      ]         self.output_path = output_path
  241 [code      ]         self.kwargs = None
  242 [blank     ] 
  243 [def       ]     def infer(self, **kwargs):
  244 [code      ]         self.kwargs = kwargs
  245 [code      ]         sample_rate = 8_000
  246 [code      ]         signal = 0.1 * np.sin(2 * np.pi * 190 * np.arange(sample_rate) / sample_rate)
  247 [code      ]         sf.write(self.output_path, signal, sample_rate)
  248 [return    ]         return str(self.output_path)
  249 [blank     ] 
  250 [blank     ] 
  251 [class     ] class _FailingRVCManager:
  252 [def       ]     def infer(self, **kwargs):
  253 [raise     ]         raise RuntimeError("rvc-python unavailable")
  254 [blank     ] 
  255 [blank     ] 
  256 [def       ] def test_rvc_handle_uses_public_infer_contract_and_copies_result(tmp_path) -> None:
  257 [import    ]     from app.core.orchestrator_ai import render_rvc_vocal
  258 [blank     ] 
  259 [code      ]     input_wav = tmp_path / "input.wav"
  260 [code      ]     source_output = tmp_path / "rvc_engine.wav"
  261 [code      ]     project_output = tmp_path / "project" / "vocal_rvc.wav"
  262 [code      ]     sf.write(input_wav, np.zeros(8_000), 8_000)
  263 [code      ]     handle = _FakeRVCManager(source_output)
  264 [blank     ] 
  265 [code      ]     result = render_rvc_vocal(handle, str(input_wav), str(project_output), "artist_voice", pitch_shift=-2)
  266 [blank     ] 
  267 [stmt      ]     assert result["ok"] is True
  268 [stmt      ]     assert result["vocal_path"] == str(project_output)
  269 [stmt      ]     assert project_output.exists()
  270 [stmt      ]     assert handle.kwargs["input_wav"] == str(input_wav)
  271 [stmt      ]     assert handle.kwargs["voice_name"] == "artist_voice"
  272 [stmt      ]     assert handle.kwargs["pitch_shift"] == -2
  273 [blank     ] 
  274 [blank     ] 
  275 [def       ] def test_rvc_handle_reports_runtime_error_without_pitch_fallback(tmp_path) -> None:
  276 [import    ]     from app.core.orchestrator_ai import render_rvc_vocal
  277 [blank     ] 
  278 [code      ]     result = render_rvc_vocal(
  279 [code      ]         _FailingRVCManager(), str(tmp_path / "input.wav"), str(tmp_path / "out.wav"), "artist"
  280 [code      ]     )
  281 [blank     ] 
  282 [stmt      ]     assert result["ok"] is False
  283 [stmt      ]     assert "rvc-python unavailable" in result["reason"]
  284 [blank     ] 
  285 [blank     ] 
  286 [blank     ] 
  287 [def       ] def test_rvc_quality_requires_duration_preservation(tmp_path) -> None:
  288 [import    ]     from app.ai.quality import validate_rvc_artifact
  289 [blank     ] 
  290 [code      ]     sample_rate = 8_000
  291 [code      ]     input_path = tmp_path / "input.wav"
  292 [code      ]     valid_output = tmp_path / "valid.wav"
  293 [code      ]     short_output = tmp_path / "short.wav"
  294 [code      ]     signal = 0.1 * np.sin(2 * np.pi * 180 * np.arange(sample_rate) / sample_rate)
  295 [code      ]     sf.write(input_path, signal, sample_rate)
  296 [code      ]     sf.write(valid_output, signal, sample_rate)
  297 [code      ]     sf.write(short_output, signal[:4_000], sample_rate)
  298 [blank     ] 
  299 [stmt      ]     assert validate_rvc_artifact(input_path, valid_output)["ok"] is True
  300 [code      ]     shortened = validate_rvc_artifact(input_path, short_output)
  301 [stmt      ]     assert shortened["ok"] is False
  302 [stmt      ]     assert shortened["reason"] == "RVC output duration diverges from input"
  303 [blank     ] 
  304 [blank     ] 
  305 [blank     ] 
  306 [def       ] def test_stem_quality_requires_near_input_duration(tmp_path) -> None:
  307 [import    ]     from app.ai.quality import validate_stem_artifact
  308 [blank     ] 
  309 [code      ]     sample_rate = 8_000
  310 [code      ]     original = tmp_path / "original.wav"
  311 [code      ]     stem = tmp_path / "vocals.wav"
  312 [code      ]     truncated = tmp_path / "vocals_truncated.wav"
  313 [code      ]     signal = 0.1 * np.sin(2 * np.pi * 220 * np.arange(sample_rate) / sample_rate)
  314 [code      ]     sf.write(original, signal, sample_rate)
  315 [code      ]     sf.write(stem, signal, sample_rate)
  316 [code      ]     sf.write(truncated, signal[:7_000], sample_rate)
  317 [blank     ] 
  318 [stmt      ]     assert validate_stem_artifact(original, stem)["ok"] is True
  319 [code      ]     rejected = validate_stem_artifact(original, truncated)
  320 [stmt      ]     assert rejected["ok"] is False
  321 [stmt      ]     assert rejected["reason"] == "stem duration diverges from input"
  322 [blank     ] 
  323 [blank     ] 
  324 [blank     ] 
  325 [def       ] def test_asr_transcript_quality_rejects_empty_and_repetitive_text() -> None:
  326 [import    ]     from app.ai.quality import validate_asr_transcript
  327 [blank     ] 
  328 [stmt      ]     assert validate_asr_transcript("в городе горят огни")["ok"] is True
  329 [stmt      ]     assert validate_asr_transcript(" ")["reason"] == "ASR transcript is empty or too short"
  330 [code      ]     repeated = validate_asr_transcript("эй эй эй эй эй")
  331 [stmt      ]     assert repeated["ok"] is False
  332 [stmt      ]     assert repeated["reason"] == "ASR transcript is excessively repetitive"
```