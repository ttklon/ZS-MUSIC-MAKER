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
        self.assertGreaterEqual(registry.hw.vram_gb, 0.0)

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
        track = mgr.list_tracks("Artist Y")[0]
        self.assertEqual(track["status"], "partial")
        raw = mgr._load_track("artist_y", track["track_id"])
        stages = {item["name"]: item for item in raw.dossier["report"]["stages"]}
        self.assertIn("analysis_llm unavailable", stages["llm_breakdown"]["skipped_reason"])


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


def test_stage_polish_reports_engine_and_falls_back_honestly(monkeypatch, tmp_path: Path) -> None:
    """Полировка мастера идёт одной канонической веткой anti_neuro."""
    import sys
    import types

    import modules
    from app.core import orchestrator

    fake = types.SimpleNamespace(
        polish_vocal=lambda source, output, preset: {"ok": True, "path": output}
    )
    monkeypatch.setitem(sys.modules, "modules.anti_neuro", fake)
    monkeypatch.setattr(modules, "anti_neuro", fake, raising=False)

    result = orchestrator._stage_polish("input.wav", tmp_path)

    assert result["ok"] is True
    assert result["engine"] == "anti_neuro.polish_vocal"


def test_stage_polish_falls_back_to_copy_when_engines_missing(monkeypatch, tmp_path: Path) -> None:
    import sys

    from app.core import orchestrator

    source = tmp_path / "in.wav"
    source.write_bytes(b"RIFF0000WAVE")
    monkeypatch.setitem(sys.modules, "modules.anti_neuro", None)

    result = orchestrator._stage_polish(str(source), tmp_path)

    assert result["ok"] is True
    assert result["fallback_used"] is True
    assert Path(result["path"]).exists()


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


def test_analysis_quality_requires_rich_schema_for_artist_and_track() -> None:
    from app.ai.quality import validate_analysis_json

    artist = {
        "bio": "Биографические данные не предоставлены; профиль построен по текстам.",
        "themes": ["ночь"], "slang": ["неон"], "flow": "плотный", "analogs": ["dark trap"],
    }
    track = {
        "theme": "побег из города", "storyline": "герой уезжает ночью",
        "key_lines": ["выше"], "analysis": "движение противопоставлено застою",
        "hook": "выше", "reusable_elements": ["cowbell"],
    }

    assert validate_analysis_json(artist)["ok"] is True
    assert validate_analysis_json(track, track_level=True)["ok"] is True
    assert validate_analysis_json({"core_themes": ["ночь"], "flow": "плотный"})["ok"] is False
    assert validate_analysis_json({"storyline": "x", "hook": "y"}, track_level=True)["ok"] is False


def test_artist_dossier_aggregate_preserves_rich_schema_and_prompt_aliases(tmp_path, monkeypatch) -> None:
    from contextlib import nullcontext

    import modules.artist_dossier.manager as dossier_manager

    mgr = dossier_manager.DossierManager(root=tmp_path)
    mgr.add_artist("Artist Rich", tracks=[{"title": "Night", "lyrics": "Ночь и неон ведут домой"}])
    entry = mgr._load_artist("artist_rich")
    response = {
        "bio": "Биографические данные не предоставлены; профиль построен по текстам.",
        "themes": ["ночная дорога"], "slang": ["неон"], "flow": "рубленый", "analogs": ["dark phonk"],
    }
    monkeypatch.setattr(dossier_manager.registry, "is_available", lambda key: key == "analysis_llm")
    monkeypatch.setattr(dossier_manager.registry, "use", lambda _key: nullcontext(type("M", (), {"handle": object()})()))
    monkeypatch.setattr(dossier_manager.LLM, "complete_json", lambda *_args, **_kwargs: response)

    dossier = mgr._aggregate_artist_dossier("artist_rich", entry)

    assert {"bio", "themes", "slang", "flow", "analogs"}.issubset(dossier)
    assert dossier["core_themes"] == dossier["themes"]
    assert dossier["lexicon"] == dossier["slang"]



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



def test_dsp_feature_extraction_returns_reference_audio_metadata(tmp_path) -> None:
    import numpy as np
    import soundfile as sf

    from modules.artist_dossier.manager import extract_dsp_features

    sample_rate = 22_050
    seconds = 4
    t = np.arange(sample_rate * seconds) / sample_rate
    signal = 0.15 * np.sin(2 * np.pi * 440 * t)
    audio = tmp_path / "reference.wav"
    sf.write(audio, signal, sample_rate)

    result = extract_dsp_features(str(audio), engine="librosa_dsp")

    assert result["ok"] is True
    assert result["engine"] == "librosa_dsp"
    assert abs(result["duration_sec"] - seconds) <= 0.05
    assert result["key"] in {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"}
    assert result["loudness_rms"] > 0



def test_runner_watchdog_marks_timeout_and_continues() -> None:
    import time

    from app.ai.sequential_runner import AIStage, SequentialAIRunner

    runner = SequentialAIRunner(vram_probe=lambda: 0.0)
    runner.add(AIStage("slow", None, lambda _handle, _ctx: time.sleep(0.2), timeout_sec=0.05))
    runner.add(AIStage("after_timeout", None, lambda _handle, _ctx: {"ok": True}, timeout_sec=0.5))

    report = runner.run({}).to_dict()

    assert report["stages"][0]["ok"] is False
    assert "timed out after 0.1s" in report["stages"][0]["error"]
    assert report["stages"][0]["timeout_sec"] == 0.05
    assert report["stages"][1]["ok"] is True
    assert report["stages"][1]["vram_before_gb"] == 0.0


def test_runner_rejects_vram_over_budget_before_stage_execution() -> None:
    from app.ai.sequential_runner import AIStage, SequentialAIRunner

    calls = []
    runner = SequentialAIRunner(vram_budget_gb=12.0, vram_probe=lambda: 13.0)
    runner.add(AIStage("over_budget", None, lambda _handle, _ctx: calls.append(True)))

    report = runner.run({}).to_dict()

    assert calls == []
    assert report["stages"][0]["ok"] is False
    assert report["stages"][0]["error"].startswith("oom: 13.000 GB exceeds 12.000 GB budget")
    assert report["stages"][0]["vram_before_gb"] == 13.0


def test_runner_assigns_extended_default_timeout_to_music_roles() -> None:
    from app.ai.sequential_runner import AIStage, MUSIC_STAGE_TIMEOUT_SEC, SequentialAIRunner

    runner = SequentialAIRunner(vram_probe=lambda: 0.0)

    assert runner._timeout_for(AIStage("music", "music_generation", lambda _h, _c: None)) == MUSIC_STAGE_TIMEOUT_SEC
    assert runner._timeout_for(AIStage("pure", None, lambda _h, _c: None)) == 600.0



def test_local_folder_collector_merges_audio_and_txt_lyrics(tmp_path) -> None:
    from modules.artist_dossier.collectors import LocalFolderCollector

    (tmp_path / "Artist Smoke - Night.txt").write_text("Ночь ведёт домой", encoding="utf-8")
    (tmp_path / "Artist Smoke - Night.wav").write_bytes(b"wav placeholder")

    tracks = LocalFolderCollector(str(tmp_path)).collect("Artist Smoke")

    assert tracks == [{
        "title": "Night",
        "lyrics": "Ночь ведёт домой",
        "audio_path": str(tmp_path / "Artist Smoke - Night.wav"),
    }]



def test_ai_pipeline_writes_versioned_session_manifest(tmp_path) -> None:
    import json

    from app.core.orchestrator_ai import run_ai_pipeline

    result = run_ai_pipeline(
        "manifest_contract", {"genre": "phonk", "theme": "session"},
        out_root=tmp_path, dry_run=True,
    )

    manifest_path = Path(result["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["project_id"] == "manifest_contract"
    assert len(manifest["stages"]) >= 8
    assert len(manifest["model_roles"]) == 13
    assert manifest["artefacts"]["cover"].endswith("cover.png")



def test_main_score_cli_wires_hit_scorer(monkeypatch, capsys) -> None:
    import main
    import modules.hit_scorer as scorer

    monkeypatch.setattr(main.sys, "argv", ["main.py", "--score", "master.wav"])
    monkeypatch.setattr(scorer, "score_track", lambda path: {
        "hit_score": 71.5, "verdict": "solid", "metrics": {"energy": {"score": 80}},
        "actions": ["refine hook"], "meta": {"file": path},
    })

    assert main.main() == 0
    assert '"hit_score": 71.5' in capsys.readouterr().out
