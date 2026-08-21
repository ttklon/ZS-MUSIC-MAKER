# АУДИТ ФАЙЛА: `tests/test_ai_layer.py`

**LOC:** 487  |  **Размер:** 19337 байт  |  **Проблем:** 12  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 5 | `ast` | import |
| 6 | `shutil` | import |
| 7 | `tempfile` | import |
| 8 | `unittest` | import |
| 9 | `pathlib.Path` | from |
| 280 | `builtins` | import |
| 281 | `unittest.mock.patch` | from |
| 283 | `main` | import |
| 304 | `main` | import |
| 319 | `sys` | import |
| 320 | `types` | import |
| 322 | `modules` | import |
| 323 | `app.core.orchestrator` | from |
| 340 | `app.core.pipeline_core.ZSPipeline` | from |
| 359 | `app.ai.quality.validate_lyrics` | from |
| 377 | `app.ai.quality.validate_lyrics` | from |
| 386 | `app.ai.quality.validate_analysis_json` | from |
| 398 | `types.SimpleNamespace` | from |
| 400 | `modules.artist_dossier.manager.resolve_vocal_source_index` | from |
| 406 | `types.SimpleNamespace` | from |
| 408 | `pytest` | import |
| 409 | `modules.artist_dossier.manager.resolve_vocal_source_index` | from |
| 417 | `types.SimpleNamespace` | from |
| 419 | `modules.artist_dossier.manager.transcribe_reference_audio` | from |
| 441 | `modules.artist_dossier.manager.transcribe_reference_audio` | from |
| 455 | `types.SimpleNamespace` | from |
| 457 | `modules.artist_dossier.manager.transcribe_reference_audio` | from |
| 474 | `modules.artist_dossier.manager.rank_clap_tags` | from |
| 482 | `pytest` | import |
| 484 | `modules.artist_dossier.manager.rank_clap_tags` | from |
| 186 | `app.ai.registry.MODEL_REGISTRY` | from |
| 186 | `app.ai.registry.registry` | from |
| 194 | `app.ai.registry.registry` | from |
| 200 | `unittest.mock.patch` | from |
| 202 | `app.ai.registry.registry` | from |
| 213 | `app.ai.sequential_runner.SequentialAIRunner` | from |
| 213 | `app.ai.sequential_runner.AIStage` | from |
| 220 | `app.ai.sequential_runner.SequentialAIRunner` | from |
| 220 | `app.ai.sequential_runner.AIStage` | from |
| 228 | `app.ai.sequential_runner.SequentialAIRunner` | from |
| 228 | `app.ai.sequential_runner.AIStage` | from |
| 246 | `modules.artist_dossier.DossierManager` | from |
| 258 | `modules.artist_dossier.DossierManager` | from |
| 267 | `app.core.orchestrator_ai.run_ai_pipeline` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 20 | `_module_name` | 6 | 1 | ✅ |
| 29 | `_is_scoped_module` | 4 | 1 | ❌ |
| 36 | `_collect_scoped_modules` | 7 | 3 | ✅ |
| 46 | `_relative_import_base` | 16 | 5 | ✅ |
| 65 | `_targets_from_statement` | 34 | 10 | ✅ |
| 102 | `_build_top_level_import_graph` | 21 | 2 | ✅ |
| 126 | `_canonical_cycle` | 4 | 0 | ✅ |
| 133 | `_find_cycles` | 21 | 5 | ✅ |
| 157 | `test_cycle_detector_reports_full_path` | 9 | 0 | ✅ |
| 169 | `test_no_import_cycles` | 12 | 0 | ✅ |
| 278 | `test_legacy_off_skips_patch_imports` | 21 | 2 | ✅ |
| 302 | `test_main_wires_legacy_off_to_patch_loader` | 12 | 1 | ✅ |
| 317 | `test_stage_polish_marks_successful_legacy_v10` | 18 | 0 | ✅ |
| 338 | `test_pipeline_uses_explicit_checkpoint_directory` | 12 | 0 | ✅ |
| 358 | `test_lyrics_quality_accepts_structured_non_repetitive_text` | 15 | 0 | ❌ |
| 376 | `test_lyrics_quality_rejects_empty_short_and_looped_text` | 6 | 0 | ❌ |
| 385 | `test_analysis_quality_requires_schema_for_artist_and_track` | 8 | 0 | ❌ |
| 397 | `test_demucs_resolves_vocals_by_declared_source_name` | 5 | 0 | ❌ |
| 405 | `test_demucs_refuses_model_without_vocals_source` | 7 | 1 | ❌ |
| 416 | `test_asr_transcribes_reference_with_faster_whisper_contract` | 21 | 0 | ❌ |
| 440 | `test_asr_reports_runtime_failure` | 10 | 0 | ❌ |
| 454 | `test_asr_rejects_invalid_transcript_without_writing_file` | 15 | 0 | ❌ |
| 473 | `test_clap_tag_ranking_uses_score_order_and_candidate_vocabulary` | 5 | 0 | ❌ |
| 481 | `test_clap_tag_ranking_rejects_mismatched_scores` | 6 | 1 | ❌ |
| 139 | `visit` | 10 | 3 | ❌ |
| 185 | `test_roles` | 6 | 0 | ❌ |
| 193 | `test_status` | 4 | 0 | ❌ |
| 199 | `test_essentia_role_detects_library_presence` | 9 | 1 | ❌ |
| 212 | `test_pure` | 5 | 0 | ❌ |
| 219 | `test_skip` | 6 | 0 | ❌ |
| 227 | `test_fallback` | 8 | 1 | ❌ |
| 239 | `setUp` | 1 | 0 | ❌ |
| 242 | `tearDown` | 1 | 0 | ❌ |
| 245 | `test_add_list` | 10 | 0 | ❌ |
| 257 | `test_dossier_deferred` | 5 | 0 | ❌ |
| 266 | `test_dry` | 9 | 2 | ❌ |
| 288 | `guarded_import` | 3 | 1 | ❌ |
| 422 | `__init__` | 1 | 0 | ❌ |
| 425 | `transcribe` | 2 | 0 | ❌ |
| 444 | `transcribe` | 1 | 0 | ❌ |
| 460 | `transcribe` | 1 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 184 | `TestRegistry` | ❌ |
| 211 | `TestRunner` | ❌ |
| 238 | `TestDossier` | ❌ |
| 265 | `TestOrchestrator` | ❌ |
| 421 | `FakeASR` | ❌ |
| 443 | `FailingASR` | ❌ |
| 459 | `RepetitiveASR` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_CLASS_DOCSTRING — 7 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 184** — public class 'TestRegistry' без docstring

  ```
        182 | 
        183 | 
  >>>   184 | class TestRegistry(unittest.TestCase):
        185 |     def test_roles(self):
        186 |         from app.ai.registry import MODEL_REGISTRY, registry
  ```

- **строка 211** — public class 'TestRunner' без docstring

  ```
        209 | 
        210 | 
  >>>   211 | class TestRunner(unittest.TestCase):
        212 |     def test_pure(self):
        213 |         from app.ai.sequential_runner import SequentialAIRunner, AIStage
  ```

- **строка 238** — public class 'TestDossier' без docstring

  ```
        236 | 
        237 | 
  >>>   238 | class TestDossier(unittest.TestCase):
        239 |     def setUp(self):
        240 |         self.tmp = Path(tempfile.mkdtemp(prefix="zsmm_d_"))
  ```

- **строка 265** — public class 'TestOrchestrator' без docstring

  ```
        263 | 
        264 | 
  >>>   265 | class TestOrchestrator(unittest.TestCase):
        266 |     def test_dry(self):
        267 |         from app.core.orchestrator_ai import run_ai_pipeline
  ```

- **строка 421** — public class 'FakeASR' без docstring

  ```
        419 |     from modules.artist_dossier.manager import transcribe_reference_audio
        420 | 
  >>>   421 |     class FakeASR:
        422 |         def __init__(self):
        423 |             self.kwargs = None
  ```

- **строка 443** — public class 'FailingASR' без docstring

  ```
        441 |     from modules.artist_dossier.manager import transcribe_reference_audio
        442 | 
  >>>   443 |     class FailingASR:
        444 |         def transcribe(self, *args, **kwargs):
        445 |             raise RuntimeError("model load failed")
  ```

- **строка 459** — public class 'RepetitiveASR' без docstring

  ```
        457 |     from modules.artist_dossier.manager import transcribe_reference_audio
        458 | 
  >>>   459 |     class RepetitiveASR:
        460 |         def transcribe(self, *args, **kwargs):
        461 |             return iter([SimpleNamespace(text="эй эй эй эй")]), SimpleNamespace(language="ru")
  ```

### MISSING_DOCSTRING — 3 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 358** — public function 'test_lyrics_quality_accepts_structured_non_repetitive_text' без docstring

  ```
        356 | 
        357 | 
  >>>   358 | def test_lyrics_quality_accepts_structured_non_repetitive_text() -> None:
        359 |     from app.ai.quality import validate_lyrics
        360 | 
  ```

- **строка 416** — public function 'test_asr_transcribes_reference_with_faster_whisper_contract' без docstring

  ```
        414 | 
        415 | 
  >>>   416 | def test_asr_transcribes_reference_with_faster_whisper_contract(tmp_path) -> None:
        417 |     from types import SimpleNamespace
        418 | 
  ```

- **строка 454** — public function 'test_asr_rejects_invalid_transcript_without_writing_file' без docstring

  ```
        452 | 
        453 | 
  >>>   454 | def test_asr_rejects_invalid_transcript_without_writing_file(tmp_path) -> None:
        455 |     from types import SimpleNamespace
        456 | 
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — smoke-тесты AI-слоя и архитектурные инварианты импортов."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import ast
  ```

### HARDCODED_POSIX_PATH — 1 шт. — 🟠 HIGH
**Смысл:** Захардкоженный POSIX-путь (/home/... /Users/...)
**Fix:** Path из config.settings/tempfile.gettempdir().

- **строка 447** — /tmp/unused.txt

  ```
        445 |             raise RuntimeError("model load failed")
        446 | 
  >>>   447 |     result = transcribe_reference_audio(FailingASR(), "reference.wav", "/tmp/unused.txt")
        448 | 
        449 |     assert result["ok"] is False
  ```
