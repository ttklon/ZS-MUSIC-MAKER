# -*- coding: utf-8 -*-
"""ZS Music Maker — smoke-тесты AI-слоя и архитектурные инварианты импортов."""
from __future__ import annotations

import ast
import shutil
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOPED_PACKAGE_PREFIXES = ("app.core", "modules", "agents")
# Lazy imports внутри функций намеренно не попадают в граф. Если в будущем
# потребуется временно допустить именно top-level цикл, добавляется его
# каноническое представление без повторяющегося последнего узла.
ALLOWED_TOP_LEVEL_CYCLES: frozenset[tuple[str, ...]] = frozenset()


def _module_name(path: Path) -> str:
    """Преобразовать путь Python-файла проекта в импортируемое имя модуля."""
    relative = path.relative_to(PROJECT_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _is_scoped_module(module_name: str) -> bool:
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for prefix in SCOPED_PACKAGE_PREFIXES
    )


def _collect_scoped_modules() -> dict[str, Path]:
    """Собрать фактические модули, которые участвуют в архитектурной проверке."""
    modules: dict[str, Path] = {}
    for relative_root in (Path("app/core"), Path("modules"), Path("agents")):
        for path in sorted((PROJECT_ROOT / relative_root).rglob("*.py")):
            if "__pycache__" not in path.parts:
                modules[_module_name(path)] = path
    return modules


def _relative_import_base(
    source_module: str,
    source_is_package: bool,
    node: ast.ImportFrom,
) -> str:
    """Разрешить базовое имя ``from .x import y`` без выполнения импортов."""
    if node.level == 0:
        return node.module or ""

    package_parts = source_module.split(".")
    if not source_is_package:
        package_parts.pop()
    trim = node.level - 1
    if trim:
        package_parts = package_parts[:-trim]
    base_parts = package_parts + ((node.module or "").split(".") if node.module else [])
    return ".".join(part for part in base_parts if part)


def _targets_from_statement(
    source_module: str,
    source_is_package: bool,
    statement: ast.stmt,
    known_modules: set[str],
) -> set[str]:
    """Вернуть внутренние импорты, выполняемые прямым оператором модуля."""
    targets: set[str] = set()
    if isinstance(statement, ast.Import):
        for alias in statement.names:
            if alias.name in known_modules:
                targets.add(alias.name)
        return targets

    if not isinstance(statement, ast.ImportFrom):
        return targets

    base = _relative_import_base(source_module, source_is_package, statement)
    if not base:
        return targets

    for alias in statement.names:
        if alias.name == "*":
            if base in known_modules:
                targets.add(base)
            continue
        child = f"{base}.{alias.name}"
        # ``from modules import lyrics_gen`` загружает дочерний модуль, в то
        # время как ``from modules.artist_dossier import DossierManager``
        # загружает сам пакет, чей __init__.py уже формирует дальнейшие рёбра.
        if child in known_modules:
            targets.add(child)
        elif base in known_modules:
            targets.add(base)
    return targets


def _build_top_level_import_graph() -> dict[str, set[str]]:
    """Построить граф только из прямых импортов app.core, modules и agents.

    Вложенные imports (например, в функции stage_* оркестратора) намеренно не
    обходятся: они являются lazy-imports и не создают циклов при импорте модуля.
    """
    module_paths = _collect_scoped_modules()
    known_modules = set(module_paths)
    graph: dict[str, set[str]] = {module_name: set() for module_name in module_paths}

    for source_module, path in module_paths.items():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        source_is_package = path.name == "__init__.py"
        for statement in tree.body:
            graph[source_module].update(
                target
                for target in _targets_from_statement(
                    source_module, source_is_package, statement, known_modules
                )
                if _is_scoped_module(target)
            )
    return graph


def _canonical_cycle(cycle: list[str]) -> tuple[str, ...]:
    """Нормализовать цикл, чтобы одна и та же петля не дублировалась в отчёте."""
    body = tuple(cycle[:-1])
    rotations = [body[index:] + body[:index] for index in range(len(body))]
    return min(rotations)


def _find_cycles(graph: dict[str, set[str]]) -> list[tuple[str, ...]]:
    """Найти все направленные циклы DFS и вернуть их в каноническом виде."""
    state: dict[str, int] = {node: 0 for node in graph}
    active_path: list[str] = []
    cycles: set[tuple[str, ...]] = set()

    def visit(node: str) -> None:
        state[node] = 1
        active_path.append(node)
        for target in sorted(graph[node]):
            if state[target] == 0:
                visit(target)
            elif state[target] == 1:
                start = active_path.index(target)
                cycles.add(_canonical_cycle(active_path[start:] + [target]))
        active_path.pop()
        state[node] = 2

    for node in sorted(graph):
        if state[node] == 0:
            visit(node)
    return sorted(cycles)


def test_cycle_detector_reports_full_path() -> None:
    """Детектор обязан найти искусственный цикл и показать все его звенья."""
    graph = {
        "app.core.alpha": {"modules.beta"},
        "modules.beta": {"agents.gamma"},
        "agents.gamma": {"app.core.alpha"},
    }
    assert _find_cycles(graph) == [
        ("agents.gamma", "app.core.alpha", "modules.beta"),
    ]


def test_no_import_cycles() -> None:
    """Запретить top-level циклы между app.core, modules и agents.

    Тест запускается без импорта проверяемых модулей, поэтому не требует тяжёлых
    зависимостей и диагностирует цикл до его проявления как частичного импорта.
    """
    cycles = _find_cycles(_build_top_level_import_graph())
    unexpected = [cycle for cycle in cycles if cycle not in ALLOWED_TOP_LEVEL_CYCLES]
    assert not unexpected, "\n".join(
        ["Обнаружены запрещённые циклические top-level импорты:"]
        + [f"  - {' -> '.join(cycle + (cycle[0],))}" for cycle in unexpected]
        + ["Перенесите одну из зависимостей в lazy-import или устраните архитектурную петлю."]
    )


class TestRegistry(unittest.TestCase):
    def test_roles(self):
        from app.ai.registry import MODEL_REGISTRY, registry
        exp = {"lyrics_llm","analysis_llm","metadata_llm","music_generation",
               "music_stereo","tts_vocal","vocal_rvc","stem_splitter","asr",
               "audio_tagger","essentia","cover_art","mastering_ai"}
        self.assertTrue(exp.issubset(set(MODEL_REGISTRY.keys())))
        self.assertGreaterEqual(registry.hw.vram_gb, 8.0)

    def test_status(self):
        from app.ai.registry import registry
        st = registry.status()
        self.assertIn("registry", st)
        self.assertIsNone(st["current"])

    def test_essentia_role_detects_library_presence(self):
        from unittest.mock import patch

        from app.ai.registry import registry

        self.assertFalse(registry.is_available("not-a-model-role"))
        # librosa — опциональная зависимость; тестируем контракт детектора,
        # а не состав пакетов конкретной машины/CI-образа.
        with patch.dict("sys.modules", {"librosa": object()}):
            self.assertTrue(registry.is_available("essentia"))


class TestRunner(unittest.TestCase):
    def test_pure(self):
        from app.ai.sequential_runner import SequentialAIRunner, AIStage
        r = SequentialAIRunner()
        r.add(AIStage("pure", None, lambda h,c: {"v":1}))
        rep = r.run({}).to_dict()
        self.assertTrue(rep["stages"][0]["ok"])

    def test_skip(self):
        from app.ai.sequential_runner import SequentialAIRunner, AIStage
        r = SequentialAIRunner()
        r.add(AIStage("x", "lyrics_llm", lambda h,c: "nope", optional=True, fallback_fn=False))
        rep = r.run({}).to_dict()
        self.assertTrue(rep["stages"][0]["ok"])
        self.assertIn("unavailable", rep["stages"][0]["skipped_reason"])

    def test_fallback(self):
        from app.ai.sequential_runner import SequentialAIRunner, AIStage
        calls = []
        r = SequentialAIRunner()
        r.add(AIStage("y", "lyrics_llm", lambda h,c: calls.append(h) or "ok",
                      optional=True, fallback_fn=True))
        rep = r.run({}).to_dict()
        self.assertTrue(rep["stages"][0]["ok"])
        self.assertEqual(calls, [None])


class TestDossier(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="zsmm_d_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_add_list(self):
        from modules.artist_dossier import DossierManager
        mgr = DossierManager(root=self.tmp)
        mgr.add_artist("Artist X", tracks=[
            {"title":"A","lyrics":"ветер северный"},
            {"title":"B","lyrics":"ночь горит"}])
        arts = mgr.list_artists()
        self.assertEqual(len(arts), 1)
        self.assertEqual(arts[0]["tracks"], 2)
        titles = sorted(t["title"] for t in mgr.list_tracks("Artist X"))
        self.assertEqual(titles, ["A","B"])

    def test_dossier_deferred(self):
        from modules.artist_dossier import DossierManager
        mgr = DossierManager(root=self.tmp)
        mgr.add_artist("Artist Y", tracks=[{"title":"S1","lyrics":"движ и жизнь"}])
        d = mgr.build_full_dossier("Artist Y")
        self.assertIn("note", d)


class TestOrchestrator(unittest.TestCase):
    def test_dry(self):
        from app.core.orchestrator_ai import run_ai_pipeline
        out = run_ai_pipeline("test_ai_dry",
            {"genre":"phonk","theme":"dry","bpm":130,"duration_sec":5},
            dry_run=True)
        self.assertIn("report", out)
        self.assertGreaterEqual(len(out["report"]["stages"]), 8)
        for st in out["report"]["stages"]:
            self.assertTrue(st["ok"] or st["skipped_reason"],
                msg=f"stage {st['name']} unexpected fail: {st}")


def test_legacy_off_skips_patch_imports(monkeypatch) -> None:
    """--legacy-off не должен импортировать или регистрировать v8–v12 патчи."""
    import builtins
    from unittest.mock import patch

    import main

    imported_legacy_modules: list[str] = []
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.startswith("app.core.orchestrator_v"):
            imported_legacy_modules.append(name)
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=guarded_import):
        report = main._register_patches(enabled=False)

    assert report["enabled"] is False
    assert report["loaded"] == []
    assert report["skipped"] == list(main.LEGACY_PATCH_MODULES)
    assert imported_legacy_modules == []


def test_main_wires_legacy_off_to_patch_loader(monkeypatch) -> None:
    """CLI флаг передаёт False в loader до запуска runtime-пайплайна."""
    import main

    calls: list[bool] = []
    monkeypatch.setattr(main.sys, "argv", ["main.py", "--legacy-off", "--dry-run"])
    monkeypatch.setattr(
        main, "_register_patches", lambda enabled: calls.append(enabled) or {}
    )
    monkeypatch.setattr(main, "_cli_dry_run", lambda: 0)

    assert main.main() == 0
    assert calls == [False]


def test_stage_polish_marks_successful_legacy_v10(monkeypatch, tmp_path: Path) -> None:
    """Успешная compatibility-ветка возвращает явный LEGACY marker."""
    import sys
    import types

    import modules
    from app.core import orchestrator

    legacy_module = types.SimpleNamespace(
        polish_vocal=lambda source, output, preset: {"ok": True, "path": output}
    )
    monkeypatch.setitem(sys.modules, "modules.anti_neuro_v10", legacy_module)
    monkeypatch.setattr(modules, "anti_neuro_v10", legacy_module, raising=False)

    result = orchestrator._stage_polish("input.wav", tmp_path)

    assert result["ok"] is True
    assert result["stage_marker"] == "LEGACY"
    assert result["legacy_stage"] == "anti_neuro_v10"


def test_pipeline_uses_explicit_checkpoint_directory(tmp_path: Path) -> None:
    """Изолированный запуск хранит checkpoints рядом с собственными артефактами."""
    from app.core.pipeline_core import ZSPipeline

    checkpoint_dir = tmp_path / "isolated" / "checkpoints"
    pipeline = ZSPipeline("shared-id", {}, checkpoint_dir=checkpoint_dir)
    pipeline.add_stage("ready", lambda context: {"ok": True, "value": 1})

    result = pipeline.run(use_checkpoints=True)

    assert result["status"] == "completed"
    assert pipeline.checkpoint_dir == checkpoint_dir
    assert (checkpoint_dir / "ready.json").exists()


if __name__ == "__main__":
    unittest.main()



def test_lyrics_quality_accepts_structured_non_repetitive_text() -> None:
    from app.ai.quality import validate_lyrics

    text = """[Куплет 1]
Ночной проспект отражает неон в окне
Мы считаем минуты на скорости в тишине
Двигатель шепчет, город держит ритм
Я пишу этот маршрут, пока свет не остыл
[Припев]
Выше, выше, держим линию огней
Выше, выше, не теряем своих дней
"""
    result = validate_lyrics(text)

    assert result["ok"] is True
    assert result["metrics"]["tokens"] >= 12


def test_lyrics_quality_rejects_empty_short_and_looped_text() -> None:
    from app.ai.quality import validate_lyrics

    assert validate_lyrics("")["reason"] == "empty lyrics"
    assert validate_lyrics("слишком коротко")["ok"] is False
    loop = "\n".join(["одна и та же строка"] * 5)
    assert validate_lyrics(loop, min_characters=1)["reason"] == "line repetition exceeds hook limit"


def test_analysis_quality_requires_schema_for_artist_and_track() -> None:
    from app.ai.quality import validate_analysis_json

    artist = {"core_themes": ["ночь"], "lexicon": ["неон"], "flow": "плотный"}
    track = {"storyline": "побег из города", "hook": "выше", "reusable_elements": ["cowbell"]}

    assert validate_analysis_json(artist)["ok"] is True
    assert validate_analysis_json(track, track_level=True)["ok"] is True
    assert validate_analysis_json({"core_themes": []})["ok"] is False



def test_demucs_resolves_vocals_by_declared_source_name() -> None:
    from types import SimpleNamespace

    from modules.artist_dossier.manager import resolve_vocal_source_index

    assert resolve_vocal_source_index(SimpleNamespace(sources=["bass", "vocals", "drums"])) == 1


def test_demucs_refuses_model_without_vocals_source() -> None:
    from types import SimpleNamespace

    import pytest
    from modules.artist_dossier.manager import resolve_vocal_source_index

    with pytest.raises(ValueError, match="does not expose"):
        resolve_vocal_source_index(SimpleNamespace(sources=["bass", "drums", "other"]))



def test_asr_transcribes_reference_with_faster_whisper_contract(tmp_path) -> None:
    from types import SimpleNamespace

    from modules.artist_dossier.manager import transcribe_reference_audio

    class FakeASR:
        def __init__(self):
            self.kwargs = None

        def transcribe(self, audio_path, **kwargs):
            self.kwargs = {"audio_path": audio_path, **kwargs}
            return iter([SimpleNamespace(text=" первая строка "), SimpleNamespace(text="вторая строка")]), SimpleNamespace(language="ru")

    handle = FakeASR()
    transcript = tmp_path / "lyrics" / "reference.txt"
    result = transcribe_reference_audio(handle, "reference.wav", str(transcript))

    assert result["ok"] is True
    assert result["lyrics"] == "первая строка\nвторая строка"
    assert result["language"] == "ru"
    assert transcript.read_text(encoding="utf-8") == result["lyrics"]
    assert handle.kwargs == {"audio_path": "reference.wav", "language": "ru", "beam_size": 5}


def test_asr_reports_runtime_failure() -> None:
    from modules.artist_dossier.manager import transcribe_reference_audio

    class FailingASR:
        def transcribe(self, *args, **kwargs):
            raise RuntimeError("model load failed")

    result = transcribe_reference_audio(FailingASR(), "reference.wav", "/tmp/unused.txt")

    assert result["ok"] is False
    assert "model load failed" in result["reason"]



def test_asr_rejects_invalid_transcript_without_writing_file(tmp_path) -> None:
    from types import SimpleNamespace

    from modules.artist_dossier.manager import transcribe_reference_audio

    class RepetitiveASR:
        def transcribe(self, *args, **kwargs):
            return iter([SimpleNamespace(text="эй эй эй эй")]), SimpleNamespace(language="ru")

    transcript = tmp_path / "lyrics" / "invalid.txt"
    result = transcribe_reference_audio(RepetitiveASR(), "reference.wav", str(transcript))

    assert result["ok"] is False
    assert result["reason"] == "ASR transcript is excessively repetitive"
    assert result["fallback"] == "reference audio retained; transcript is not used"
    assert not transcript.exists()



def test_clap_tag_ranking_uses_score_order_and_candidate_vocabulary() -> None:
    from modules.artist_dossier.manager import rank_clap_tags

    tags = rank_clap_tags(["phonk", "trap", "pop", "rock"], [0.2, 0.9, -0.1, 0.5], limit=3)

    assert tags == ["trap", "rock", "phonk"]


def test_clap_tag_ranking_rejects_mismatched_scores() -> None:
    import pytest

    from modules.artist_dossier.manager import rank_clap_tags

    with pytest.raises(ValueError, match="do not match"):
        rank_clap_tags(["phonk", "trap"], [0.1])
