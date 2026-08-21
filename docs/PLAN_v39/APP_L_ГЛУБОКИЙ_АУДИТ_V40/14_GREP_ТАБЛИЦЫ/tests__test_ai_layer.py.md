# grep-таблицы `tests/test_ai_layer.py`

## `import` — 41 совпадений
```
    3 | from __future__ import annotations
    5 | import ast
    6 | import shutil
    7 | import tempfile
    8 | import unittest
    9 | from pathlib import Path
  186 |         from app.ai.registry import MODEL_REGISTRY, registry
  194 |         from app.ai.registry import registry
  200 |         from unittest.mock import patch
  202 |         from app.ai.registry import registry
  213 |         from app.ai.sequential_runner import SequentialAIRunner, AIStage
  220 |         from app.ai.sequential_runner import SequentialAIRunner, AIStage
  228 |         from app.ai.sequential_runner import SequentialAIRunner, AIStage
  246 |         from modules.artist_dossier import DossierManager
  258 |         from modules.artist_dossier import DossierManager
  267 |         from app.core.orchestrator_ai import run_ai_pipeline
  280 |     import builtins
  281 |     from unittest.mock import patch
  283 |     import main
  304 |     import main
  319 |     import sys
  320 |     import types
  322 |     import modules
  323 |     from app.core import orchestrator
  340 |     from app.core.pipeline_core import ZSPipeline
  359 |     from app.ai.quality import validate_lyrics
  377 |     from app.ai.quality import validate_lyrics
  386 |     from app.ai.quality import validate_analysis_json
  398 |     from types import SimpleNamespace
  400 |     from modules.artist_dossier.manager import resolve_vocal_source_index
  406 |     from types import SimpleNamespace
  408 |     import pytest
  409 |     from modules.artist_dossier.manager import resolve_vocal_source_index
  417 |     from types import SimpleNamespace
  419 |     from modules.artist_dossier.manager import transcribe_reference_audio
  441 |     from modules.artist_dossier.manager import transcribe_reference_audio
  455 |     from types import SimpleNamespace
  457 |     from modules.artist_dossier.manager import transcribe_reference_audio
  474 |     from modules.artist_dossier.manager import rank_clap_tags
  482 |     import pytest
  484 |     from modules.artist_dossier.manager import rank_clap_tags
```

## `def` — 41 совпадений
```
   20 | def _module_name(path: Path) -> str:
   29 | def _is_scoped_module(module_name: str) -> bool:
   36 | def _collect_scoped_modules() -> dict[str, Path]:
   46 | def _relative_import_base(
   65 | def _targets_from_statement(
  102 | def _build_top_level_import_graph() -> dict[str, set[str]]:
  126 | def _canonical_cycle(cycle: list[str]) -> tuple[str, ...]:
  133 | def _find_cycles(graph: dict[str, set[str]]) -> list[tuple[str, ...]]:
  139 |     def visit(node: str) -> None:
  157 | def test_cycle_detector_reports_full_path() -> None:
  169 | def test_no_import_cycles() -> None:
  185 |     def test_roles(self):
  193 |     def test_status(self):
  199 |     def test_essentia_role_detects_library_presence(self):
  212 |     def test_pure(self):
  219 |     def test_skip(self):
  227 |     def test_fallback(self):
  239 |     def setUp(self):
  242 |     def tearDown(self):
  245 |     def test_add_list(self):
  257 |     def test_dossier_deferred(self):
  266 |     def test_dry(self):
  278 | def test_legacy_off_skips_patch_imports(monkeypatch) -> None:
  288 |     def guarded_import(name, *args, **kwargs):
  302 | def test_main_wires_legacy_off_to_patch_loader(monkeypatch) -> None:
  317 | def test_stage_polish_marks_successful_legacy_v10(monkeypatch, tmp_path: Path) -> None:
  338 | def test_pipeline_uses_explicit_checkpoint_directory(tmp_path: Path) -> None:
  358 | def test_lyrics_quality_accepts_structured_non_repetitive_text() -> None:
  376 | def test_lyrics_quality_rejects_empty_short_and_looped_text() -> None:
  385 | def test_analysis_quality_requires_schema_for_artist_and_track() -> None:
  397 | def test_demucs_resolves_vocals_by_declared_source_name() -> None:
  405 | def test_demucs_refuses_model_without_vocals_source() -> None:
  416 | def test_asr_transcribes_reference_with_faster_whisper_contract(tmp_path) -> None:
  422 |         def __init__(self):
  425 |         def transcribe(self, audio_path, **kwargs):
  440 | def test_asr_reports_runtime_failure() -> None:
  444 |         def transcribe(self, *args, **kwargs):
  454 | def test_asr_rejects_invalid_transcript_without_writing_file(tmp_path) -> None:
  460 |         def transcribe(self, *args, **kwargs):
  473 | def test_clap_tag_ranking_uses_score_order_and_candidate_vocabulary() -> None:
  481 | def test_clap_tag_ranking_rejects_mismatched_scores() -> None:
```

## `class` — 7 совпадений
```
  184 | class TestRegistry(unittest.TestCase):
  211 | class TestRunner(unittest.TestCase):
  238 | class TestDossier(unittest.TestCase):
  265 | class TestOrchestrator(unittest.TestCase):
  421 |     class FakeASR:
  443 |     class FailingASR:
  459 |     class RepetitiveASR:
```

## `raise` — 1 совпадений
```
  445 |             raise RuntimeError("model load failed")
```

## `return` — 15 совпадений
```
   26 |     return ".".join(parts)
   30 |     return any(
   43 |     return modules
   53 |         return node.module or ""
   62 |     return ".".join(part for part in base_parts if part)
   77 |         return targets
   80 |         return targets
   84 |         return targets
   99 |     return targets
  123 |     return graph
  130 |     return min(rotations)
  154 |     return sorted(cycles)
  291 |         return original_import(name, *args, **kwargs)
  427 |             return iter([SimpleNamespace(text=" первая строка "), SimpleNamespace(text="вторая строка")]), SimpleNamespace(language="ru")
  461 |             return iter([SimpleNamespace(text="эй эй эй эй")]), SimpleNamespace(language="ru")
```

## `if` — 17 совпадений
```
   24 |     if parts[-1] == "__init__":
   41 |             if "__pycache__" not in path.parts:
   52 |     if node.level == 0:
   56 |     if not source_is_package:
   59 |     if trim:
   73 |     if isinstance(statement, ast.Import):
   75 |             if alias.name in known_modules:
   79 |     if not isinstance(statement, ast.ImportFrom):
   83 |     if not base:
   87 |         if alias.name == "*":
   88 |             if base in known_modules:
   95 |         if child in known_modules:
  121 |                 if _is_scoped_module(target)
  143 |             if state[target] == 0:
  152 |         if state[node] == 0:
  289 |         if name.startswith("app.core.orchestrator_v"):
  353 | if __name__ == "__main__":
```

## `for` — 11 совпадений
```
   32 |         for prefix in SCOPED_PACKAGE_PREFIXES
   39 |     for relative_root in (Path("app/core"), Path("modules"), Path("agents")):
   40 |         for path in sorted((PROJECT_ROOT / relative_root).rglob("*.py")):
   74 |         for alias in statement.names:
   86 |     for alias in statement.names:
  112 |     for source_module, path in module_paths.items():
  115 |         for statement in tree.body:
  118 |                 for target in _targets_from_statement(
  142 |         for target in sorted(graph[node]):
  151 |     for node in sorted(graph):
  273 |         for st in out["report"]["stages"]:
```

## `with` — 4 совпадений
```
  207 |         with patch.dict("sys.modules", {"librosa": object()}):
  293 |     with patch("builtins.__import__", side_effect=guarded_import):
  411 |     with pytest.raises(ValueError, match="does not expose"):
  486 |     with pytest.raises(ValueError, match="do not match"):
```

## `assert` — 35 совпадений
```
  164 |     assert _find_cycles(graph) == [
  177 |     assert not unexpected, "\n".join(
  296 |     assert report["enabled"] is False
  297 |     assert report["loaded"] == []
  298 |     assert report["skipped"] == list(main.LEGACY_PATCH_MODULES)
  299 |     assert imported_legacy_modules == []
  313 |     assert main.main() == 0
  314 |     assert calls == [False]
  333 |     assert result["ok"] is True
  334 |     assert result["stage_marker"] == "LEGACY"
  335 |     assert result["legacy_stage"] == "anti_neuro_v10"
  348 |     assert result["status"] == "completed"
  349 |     assert pipeline.checkpoint_dir == checkpoint_dir
  350 |     assert (checkpoint_dir / "ready.json").exists()
  372 |     assert result["ok"] is True
  373 |     assert result["metrics"]["tokens"] >= 12
  379 |     assert validate_lyrics("")["reason"] == "empty lyrics"
  380 |     assert validate_lyrics("слишком коротко")["ok"] is False
  382 |     assert validate_lyrics(loop, min_characters=1)["reason"] == "line repetition exceeds hook limit"
  391 |     assert validate_analysis_json(artist)["ok"] is True
  392 |     assert validate_analysis_json(track, track_level=True)["ok"] is True
  393 |     assert validate_analysis_json({"core_themes": []})["ok"] is False
  402 |     assert resolve_vocal_source_index(SimpleNamespace(sources=["bass", "vocals", "drums"])) == 1
  433 |     assert result["ok"] is True
  434 |     assert result["lyrics"] == "первая строка\nвторая строка"
  435 |     assert result["language"] == "ru"
  436 |     assert transcript.read_text(encoding="utf-8") == result["lyrics"]
  437 |     assert handle.kwargs == {"audio_path": "reference.wav", "language": "ru", "beam_size": 5}
  449 |     assert result["ok"] is False
  450 |     assert "model load failed" in result["reason"]
  466 |     assert result["ok"] is False
  467 |     assert result["reason"] == "ASR transcript is excessively repetitive"
  468 |     assert result["fallback"] == "reference audio retained; transcript is not used"
  469 |     assert not transcript.exists()
  478 |     assert tags == ["trap", "rock", "phonk"]
```

## `path_home` — 1 совпадений
```
  447 |     result = transcribe_reference_audio(FailingASR(), "reference.wav", "/tmp/unused.txt")
```
