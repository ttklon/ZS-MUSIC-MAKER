# ПОСТРОЧНЫЙ ЛИСТИНГ: `tests/test_ai_layer.py`

**Всего строк:** 487

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 152 | 31.2 |
| blank | 123 | 25.3 |
| import | 41 | 8.4 |
| def | 41 | 8.4 |
| stmt | 39 | 8.0 |
| docstring | 29 | 6.0 |
| branch | 19 | 3.9 |
| return | 15 | 3.1 |
| loop | 11 | 2.3 |
| comment | 9 | 1.8 |
| class | 7 | 1.4 |
| raise | 1 | 0.2 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker — smoke-тесты AI-слоя и архитектурные инварианты импортов."""
    3 [import    ] from __future__ import annotations
    4 [blank     ] 
    5 [import    ] import ast
    6 [import    ] import shutil
    7 [import    ] import tempfile
    8 [import    ] import unittest
    9 [import    ] from pathlib import Path
   10 [blank     ] 
   11 [blank     ] 
   12 [code      ] PROJECT_ROOT = Path(__file__).resolve().parents[1]
   13 [code      ] SCOPED_PACKAGE_PREFIXES = ("app.core", "modules", "agents")
   14 [comment   ] # Lazy imports внутри функций намеренно не попадают в граф. Если в будущем
   15 [comment   ] # потребуется временно допустить именно top-level цикл, добавляется его
   16 [comment   ] # каноническое представление без повторяющегося последнего узла.
   17 [code      ] ALLOWED_TOP_LEVEL_CYCLES: frozenset[tuple[str, ...]] = frozenset()
   18 [blank     ] 
   19 [blank     ] 
   20 [def       ] def _module_name(path: Path) -> str:
   21 [docstring ]     """Преобразовать путь Python-файла проекта в импортируемое имя модуля."""
   22 [code      ]     relative = path.relative_to(PROJECT_ROOT).with_suffix("")
   23 [code      ]     parts = list(relative.parts)
   24 [branch    ]     if parts[-1] == "__init__":
   25 [code      ]         parts.pop()
   26 [return    ]     return ".".join(parts)
   27 [blank     ] 
   28 [blank     ] 
   29 [def       ] def _is_scoped_module(module_name: str) -> bool:
   30 [return    ]     return any(
   31 [code      ]         module_name == prefix or module_name.startswith(f"{prefix}.")
   32 [loop      ]         for prefix in SCOPED_PACKAGE_PREFIXES
   33 [code      ]     )
   34 [blank     ] 
   35 [blank     ] 
   36 [def       ] def _collect_scoped_modules() -> dict[str, Path]:
   37 [docstring ]     """Собрать фактические модули, которые участвуют в архитектурной проверке."""
   38 [code      ]     modules: dict[str, Path] = {}
   39 [loop      ]     for relative_root in (Path("app/core"), Path("modules"), Path("agents")):
   40 [loop      ]         for path in sorted((PROJECT_ROOT / relative_root).rglob("*.py")):
   41 [branch    ]             if "__pycache__" not in path.parts:
   42 [code      ]                 modules[_module_name(path)] = path
   43 [return    ]     return modules
   44 [blank     ] 
   45 [blank     ] 
   46 [def       ] def _relative_import_base(
   47 [code      ]     source_module: str,
   48 [code      ]     source_is_package: bool,
   49 [code      ]     node: ast.ImportFrom,
   50 [code      ] ) -> str:
   51 [docstring ]     """Разрешить базовое имя ``from .x import y`` без выполнения импортов."""
   52 [branch    ]     if node.level == 0:
   53 [return    ]         return node.module or ""
   54 [blank     ] 
   55 [code      ]     package_parts = source_module.split(".")
   56 [branch    ]     if not source_is_package:
   57 [code      ]         package_parts.pop()
   58 [code      ]     trim = node.level - 1
   59 [branch    ]     if trim:
   60 [code      ]         package_parts = package_parts[:-trim]
   61 [code      ]     base_parts = package_parts + ((node.module or "").split(".") if node.module else [])
   62 [return    ]     return ".".join(part for part in base_parts if part)
   63 [blank     ] 
   64 [blank     ] 
   65 [def       ] def _targets_from_statement(
   66 [code      ]     source_module: str,
   67 [code      ]     source_is_package: bool,
   68 [code      ]     statement: ast.stmt,
   69 [code      ]     known_modules: set[str],
   70 [code      ] ) -> set[str]:
   71 [docstring ]     """Вернуть внутренние импорты, выполняемые прямым оператором модуля."""
   72 [code      ]     targets: set[str] = set()
   73 [branch    ]     if isinstance(statement, ast.Import):
   74 [loop      ]         for alias in statement.names:
   75 [branch    ]             if alias.name in known_modules:
   76 [code      ]                 targets.add(alias.name)
   77 [return    ]         return targets
   78 [blank     ] 
   79 [branch    ]     if not isinstance(statement, ast.ImportFrom):
   80 [return    ]         return targets
   81 [blank     ] 
   82 [code      ]     base = _relative_import_base(source_module, source_is_package, statement)
   83 [branch    ]     if not base:
   84 [return    ]         return targets
   85 [blank     ] 
   86 [loop      ]     for alias in statement.names:
   87 [branch    ]         if alias.name == "*":
   88 [branch    ]             if base in known_modules:
   89 [code      ]                 targets.add(base)
   90 [code      ]             continue
   91 [code      ]         child = f"{base}.{alias.name}"
   92 [comment   ]         # ``from modules import lyrics_gen`` загружает дочерний модуль, в то
   93 [comment   ]         # время как ``from modules.artist_dossier import DossierManager``
   94 [comment   ]         # загружает сам пакет, чей __init__.py уже формирует дальнейшие рёбра.
   95 [branch    ]         if child in known_modules:
   96 [code      ]             targets.add(child)
   97 [branch    ]         elif base in known_modules:
   98 [code      ]             targets.add(base)
   99 [return    ]     return targets
  100 [blank     ] 
  101 [blank     ] 
  102 [def       ] def _build_top_level_import_graph() -> dict[str, set[str]]:
  103 [docstring ]     """Построить граф только из прямых импортов app.core, modules и agents.
  104 [blank     ] 
  105 [docstring ]     Вложенные imports (например, в функции stage_* оркестратора) намеренно не
  106 [docstring ]     обходятся: они являются lazy-imports и не создают циклов при импорте модуля.
  107 [docstring ]     """
  108 [code      ]     module_paths = _collect_scoped_modules()
  109 [code      ]     known_modules = set(module_paths)
  110 [code      ]     graph: dict[str, set[str]] = {module_name: set() for module_name in module_paths}
  111 [blank     ] 
  112 [loop      ]     for source_module, path in module_paths.items():
  113 [code      ]         tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
  114 [code      ]         source_is_package = path.name == "__init__.py"
  115 [loop      ]         for statement in tree.body:
  116 [code      ]             graph[source_module].update(
  117 [code      ]                 target
  118 [loop      ]                 for target in _targets_from_statement(
  119 [code      ]                     source_module, source_is_package, statement, known_modules
  120 [code      ]                 )
  121 [branch    ]                 if _is_scoped_module(target)
  122 [code      ]             )
  123 [return    ]     return graph
  124 [blank     ] 
  125 [blank     ] 
  126 [def       ] def _canonical_cycle(cycle: list[str]) -> tuple[str, ...]:
  127 [docstring ]     """Нормализовать цикл, чтобы одна и та же петля не дублировалась в отчёте."""
  128 [code      ]     body = tuple(cycle[:-1])
  129 [code      ]     rotations = [body[index:] + body[:index] for index in range(len(body))]
  130 [return    ]     return min(rotations)
  131 [blank     ] 
  132 [blank     ] 
  133 [def       ] def _find_cycles(graph: dict[str, set[str]]) -> list[tuple[str, ...]]:
  134 [docstring ]     """Найти все направленные циклы DFS и вернуть их в каноническом виде."""
  135 [code      ]     state: dict[str, int] = {node: 0 for node in graph}
  136 [code      ]     active_path: list[str] = []
  137 [code      ]     cycles: set[tuple[str, ...]] = set()
  138 [blank     ] 
  139 [def       ]     def visit(node: str) -> None:
  140 [code      ]         state[node] = 1
  141 [code      ]         active_path.append(node)
  142 [loop      ]         for target in sorted(graph[node]):
  143 [branch    ]             if state[target] == 0:
  144 [code      ]                 visit(target)
  145 [branch    ]             elif state[target] == 1:
  146 [code      ]                 start = active_path.index(target)
  147 [code      ]                 cycles.add(_canonical_cycle(active_path[start:] + [target]))
  148 [code      ]         active_path.pop()
  149 [code      ]         state[node] = 2
  150 [blank     ] 
  151 [loop      ]     for node in sorted(graph):
  152 [branch    ]         if state[node] == 0:
  153 [code      ]             visit(node)
  154 [return    ]     return sorted(cycles)
  155 [blank     ] 
  156 [blank     ] 
  157 [def       ] def test_cycle_detector_reports_full_path() -> None:
  158 [docstring ]     """Детектор обязан найти искусственный цикл и показать все его звенья."""
  159 [code      ]     graph = {
  160 [code      ]         "app.core.alpha": {"modules.beta"},
  161 [code      ]         "modules.beta": {"agents.gamma"},
  162 [code      ]         "agents.gamma": {"app.core.alpha"},
  163 [code      ]     }
  164 [stmt      ]     assert _find_cycles(graph) == [
  165 [code      ]         ("agents.gamma", "app.core.alpha", "modules.beta"),
  166 [code      ]     ]
  167 [blank     ] 
  168 [blank     ] 
  169 [def       ] def test_no_import_cycles() -> None:
  170 [docstring ]     """Запретить top-level циклы между app.core, modules и agents.
  171 [blank     ] 
  172 [docstring ]     Тест запускается без импорта проверяемых модулей, поэтому не требует тяжёлых
  173 [docstring ]     зависимостей и диагностирует цикл до его проявления как частичного импорта.
  174 [docstring ]     """
  175 [code      ]     cycles = _find_cycles(_build_top_level_import_graph())
  176 [code      ]     unexpected = [cycle for cycle in cycles if cycle not in ALLOWED_TOP_LEVEL_CYCLES]
  177 [stmt      ]     assert not unexpected, "\n".join(
  178 [code      ]         ["Обнаружены запрещённые циклические top-level импорты:"]
  179 [code      ]         + [f"  - {' -> '.join(cycle + (cycle[0],))}" for cycle in unexpected]
  180 [code      ]         + ["Перенесите одну из зависимостей в lazy-import или устраните архитектурную петлю."]
  181 [code      ]     )
  182 [blank     ] 
  183 [blank     ] 
  184 [class     ] class TestRegistry(unittest.TestCase):
  185 [def       ]     def test_roles(self):
  186 [import    ]         from app.ai.registry import MODEL_REGISTRY, registry
  187 [code      ]         exp = {"lyrics_llm","analysis_llm","metadata_llm","music_generation",
  188 [code      ]                "music_stereo","tts_vocal","vocal_rvc","stem_splitter","asr",
  189 [code      ]                "audio_tagger","essentia","cover_art","mastering_ai"}
  190 [code      ]         self.assertTrue(exp.issubset(set(MODEL_REGISTRY.keys())))
  191 [code      ]         self.assertGreaterEqual(registry.hw.vram_gb, 8.0)
  192 [blank     ] 
  193 [def       ]     def test_status(self):
  194 [import    ]         from app.ai.registry import registry
  195 [code      ]         st = registry.status()
  196 [code      ]         self.assertIn("registry", st)
  197 [code      ]         self.assertIsNone(st["current"])
  198 [blank     ] 
  199 [def       ]     def test_essentia_role_detects_library_presence(self):
  200 [import    ]         from unittest.mock import patch
  201 [blank     ] 
  202 [import    ]         from app.ai.registry import registry
  203 [blank     ] 
  204 [code      ]         self.assertFalse(registry.is_available("not-a-model-role"))
  205 [comment   ]         # librosa — опциональная зависимость; тестируем контракт детектора,
  206 [comment   ]         # а не состав пакетов конкретной машины/CI-образа.
  207 [stmt      ]         with patch.dict("sys.modules", {"librosa": object()}):
  208 [code      ]             self.assertTrue(registry.is_available("essentia"))
  209 [blank     ] 
  210 [blank     ] 
  211 [class     ] class TestRunner(unittest.TestCase):
  212 [def       ]     def test_pure(self):
  213 [import    ]         from app.ai.sequential_runner import SequentialAIRunner, AIStage
  214 [code      ]         r = SequentialAIRunner()
  215 [code      ]         r.add(AIStage("pure", None, lambda h,c: {"v":1}))
  216 [code      ]         rep = r.run({}).to_dict()
  217 [code      ]         self.assertTrue(rep["stages"][0]["ok"])
  218 [blank     ] 
  219 [def       ]     def test_skip(self):
  220 [import    ]         from app.ai.sequential_runner import SequentialAIRunner, AIStage
  221 [code      ]         r = SequentialAIRunner()
  222 [code      ]         r.add(AIStage("x", "lyrics_llm", lambda h,c: "nope", optional=True, fallback_fn=False))
  223 [code      ]         rep = r.run({}).to_dict()
  224 [code      ]         self.assertTrue(rep["stages"][0]["ok"])
  225 [code      ]         self.assertIn("unavailable", rep["stages"][0]["skipped_reason"])
  226 [blank     ] 
  227 [def       ]     def test_fallback(self):
  228 [import    ]         from app.ai.sequential_runner import SequentialAIRunner, AIStage
  229 [code      ]         calls = []
  230 [code      ]         r = SequentialAIRunner()
  231 [code      ]         r.add(AIStage("y", "lyrics_llm", lambda h,c: calls.append(h) or "ok",
  232 [code      ]                       optional=True, fallback_fn=True))
  233 [code      ]         rep = r.run({}).to_dict()
  234 [code      ]         self.assertTrue(rep["stages"][0]["ok"])
  235 [code      ]         self.assertEqual(calls, [None])
  236 [blank     ] 
  237 [blank     ] 
  238 [class     ] class TestDossier(unittest.TestCase):
  239 [def       ]     def setUp(self):
  240 [code      ]         self.tmp = Path(tempfile.mkdtemp(prefix="zsmm_d_"))
  241 [blank     ] 
  242 [def       ]     def tearDown(self):
  243 [code      ]         shutil.rmtree(self.tmp, ignore_errors=True)
  244 [blank     ] 
  245 [def       ]     def test_add_list(self):
  246 [import    ]         from modules.artist_dossier import DossierManager
  247 [code      ]         mgr = DossierManager(root=self.tmp)
  248 [code      ]         mgr.add_artist("Artist X", tracks=[
  249 [code      ]             {"title":"A","lyrics":"ветер северный"},
  250 [code      ]             {"title":"B","lyrics":"ночь горит"}])
  251 [code      ]         arts = mgr.list_artists()
  252 [code      ]         self.assertEqual(len(arts), 1)
  253 [code      ]         self.assertEqual(arts[0]["tracks"], 2)
  254 [code      ]         titles = sorted(t["title"] for t in mgr.list_tracks("Artist X"))
  255 [code      ]         self.assertEqual(titles, ["A","B"])
  256 [blank     ] 
  257 [def       ]     def test_dossier_deferred(self):
  258 [import    ]         from modules.artist_dossier import DossierManager
  259 [code      ]         mgr = DossierManager(root=self.tmp)
  260 [code      ]         mgr.add_artist("Artist Y", tracks=[{"title":"S1","lyrics":"движ и жизнь"}])
  261 [code      ]         d = mgr.build_full_dossier("Artist Y")
  262 [code      ]         self.assertIn("note", d)
  263 [blank     ] 
  264 [blank     ] 
  265 [class     ] class TestOrchestrator(unittest.TestCase):
  266 [def       ]     def test_dry(self):
  267 [import    ]         from app.core.orchestrator_ai import run_ai_pipeline
  268 [code      ]         out = run_ai_pipeline("test_ai_dry",
  269 [code      ]             {"genre":"phonk","theme":"dry","bpm":130,"duration_sec":5},
  270 [code      ]             dry_run=True)
  271 [code      ]         self.assertIn("report", out)
  272 [code      ]         self.assertGreaterEqual(len(out["report"]["stages"]), 8)
  273 [loop      ]         for st in out["report"]["stages"]:
  274 [code      ]             self.assertTrue(st["ok"] or st["skipped_reason"],
  275 [code      ]                 msg=f"stage {st['name']} unexpected fail: {st}")
  276 [blank     ] 
  277 [blank     ] 
  278 [def       ] def test_legacy_off_skips_patch_imports(monkeypatch) -> None:
  279 [docstring ]     """--legacy-off не должен импортировать или регистрировать v8–v12 патчи."""
  280 [import    ]     import builtins
  281 [import    ]     from unittest.mock import patch
  282 [blank     ] 
  283 [import    ]     import main
  284 [blank     ] 
  285 [code      ]     imported_legacy_modules: list[str] = []
  286 [code      ]     original_import = builtins.__import__
  287 [blank     ] 
  288 [def       ]     def guarded_import(name, *args, **kwargs):
  289 [branch    ]         if name.startswith("app.core.orchestrator_v"):
  290 [code      ]             imported_legacy_modules.append(name)
  291 [return    ]         return original_import(name, *args, **kwargs)
  292 [blank     ] 
  293 [stmt      ]     with patch("builtins.__import__", side_effect=guarded_import):
  294 [code      ]         report = main._register_patches(enabled=False)
  295 [blank     ] 
  296 [stmt      ]     assert report["enabled"] is False
  297 [stmt      ]     assert report["loaded"] == []
  298 [stmt      ]     assert report["skipped"] == list(main.LEGACY_PATCH_MODULES)
  299 [stmt      ]     assert imported_legacy_modules == []
  300 [blank     ] 
  301 [blank     ] 
  302 [def       ] def test_main_wires_legacy_off_to_patch_loader(monkeypatch) -> None:
  303 [docstring ]     """CLI флаг передаёт False в loader до запуска runtime-пайплайна."""
  304 [import    ]     import main
  305 [blank     ] 
  306 [code      ]     calls: list[bool] = []
  307 [code      ]     monkeypatch.setattr(main.sys, "argv", ["main.py", "--legacy-off", "--dry-run"])
  308 [code      ]     monkeypatch.setattr(
  309 [code      ]         main, "_register_patches", lambda enabled: calls.append(enabled) or {}
  310 [code      ]     )
  311 [code      ]     monkeypatch.setattr(main, "_cli_dry_run", lambda: 0)
  312 [blank     ] 
  313 [stmt      ]     assert main.main() == 0
  314 [stmt      ]     assert calls == [False]
  315 [blank     ] 
  316 [blank     ] 
  317 [def       ] def test_stage_polish_marks_successful_legacy_v10(monkeypatch, tmp_path: Path) -> None:
  318 [docstring ]     """Успешная compatibility-ветка возвращает явный LEGACY marker."""
  319 [import    ]     import sys
  320 [import    ]     import types
  321 [blank     ] 
  322 [import    ]     import modules
  323 [import    ]     from app.core import orchestrator
  324 [blank     ] 
  325 [code      ]     legacy_module = types.SimpleNamespace(
  326 [code      ]         polish_vocal=lambda source, output, preset: {"ok": True, "path": output}
  327 [code      ]     )
  328 [code      ]     monkeypatch.setitem(sys.modules, "modules.anti_neuro_v10", legacy_module)
  329 [code      ]     monkeypatch.setattr(modules, "anti_neuro_v10", legacy_module, raising=False)
  330 [blank     ] 
  331 [code      ]     result = orchestrator._stage_polish("input.wav", tmp_path)
  332 [blank     ] 
  333 [stmt      ]     assert result["ok"] is True
  334 [stmt      ]     assert result["stage_marker"] == "LEGACY"
  335 [stmt      ]     assert result["legacy_stage"] == "anti_neuro_v10"
  336 [blank     ] 
  337 [blank     ] 
  338 [def       ] def test_pipeline_uses_explicit_checkpoint_directory(tmp_path: Path) -> None:
  339 [docstring ]     """Изолированный запуск хранит checkpoints рядом с собственными артефактами."""
  340 [import    ]     from app.core.pipeline_core import ZSPipeline
  341 [blank     ] 
  342 [code      ]     checkpoint_dir = tmp_path / "isolated" / "checkpoints"
  343 [code      ]     pipeline = ZSPipeline("shared-id", {}, checkpoint_dir=checkpoint_dir)
  344 [code      ]     pipeline.add_stage("ready", lambda context: {"ok": True, "value": 1})
  345 [blank     ] 
  346 [code      ]     result = pipeline.run(use_checkpoints=True)
  347 [blank     ] 
  348 [stmt      ]     assert result["status"] == "completed"
  349 [stmt      ]     assert pipeline.checkpoint_dir == checkpoint_dir
  350 [stmt      ]     assert (checkpoint_dir / "ready.json").exists()
  351 [blank     ] 
  352 [blank     ] 
  353 [branch    ] if __name__ == "__main__":
  354 [code      ]     unittest.main()
  355 [blank     ] 
  356 [blank     ] 
  357 [blank     ] 
  358 [def       ] def test_lyrics_quality_accepts_structured_non_repetitive_text() -> None:
  359 [import    ]     from app.ai.quality import validate_lyrics
  360 [blank     ] 
  361 [docstring ]     text = """[Куплет 1]
  362 [docstring ] Ночной проспект отражает неон в окне
  363 [docstring ] Мы считаем минуты на скорости в тишине
  364 [docstring ] Двигатель шепчет, город держит ритм
  365 [docstring ] Я пишу этот маршрут, пока свет не остыл
  366 [docstring ] [Припев]
  367 [docstring ] Выше, выше, держим линию огней
  368 [docstring ] Выше, выше, не теряем своих дней
  369 [docstring ] """
  370 [code      ]     result = validate_lyrics(text)
  371 [blank     ] 
  372 [stmt      ]     assert result["ok"] is True
  373 [stmt      ]     assert result["metrics"]["tokens"] >= 12
  374 [blank     ] 
  375 [blank     ] 
  376 [def       ] def test_lyrics_quality_rejects_empty_short_and_looped_text() -> None:
  377 [import    ]     from app.ai.quality import validate_lyrics
  378 [blank     ] 
  379 [stmt      ]     assert validate_lyrics("")["reason"] == "empty lyrics"
  380 [stmt      ]     assert validate_lyrics("слишком коротко")["ok"] is False
  381 [code      ]     loop = "\n".join(["одна и та же строка"] * 5)
  382 [stmt      ]     assert validate_lyrics(loop, min_characters=1)["reason"] == "line repetition exceeds hook limit"
  383 [blank     ] 
  384 [blank     ] 
  385 [def       ] def test_analysis_quality_requires_schema_for_artist_and_track() -> None:
  386 [import    ]     from app.ai.quality import validate_analysis_json
  387 [blank     ] 
  388 [code      ]     artist = {"core_themes": ["ночь"], "lexicon": ["неон"], "flow": "плотный"}
  389 [code      ]     track = {"storyline": "побег из города", "hook": "выше", "reusable_elements": ["cowbell"]}
  390 [blank     ] 
  391 [stmt      ]     assert validate_analysis_json(artist)["ok"] is True
  392 [stmt      ]     assert validate_analysis_json(track, track_level=True)["ok"] is True
  393 [stmt      ]     assert validate_analysis_json({"core_themes": []})["ok"] is False
  394 [blank     ] 
  395 [blank     ] 
  396 [blank     ] 
  397 [def       ] def test_demucs_resolves_vocals_by_declared_source_name() -> None:
  398 [import    ]     from types import SimpleNamespace
  399 [blank     ] 
  400 [import    ]     from modules.artist_dossier.manager import resolve_vocal_source_index
  401 [blank     ] 
  402 [stmt      ]     assert resolve_vocal_source_index(SimpleNamespace(sources=["bass", "vocals", "drums"])) == 1
  403 [blank     ] 
  404 [blank     ] 
  405 [def       ] def test_demucs_refuses_model_without_vocals_source() -> None:
  406 [import    ]     from types import SimpleNamespace
  407 [blank     ] 
  408 [import    ]     import pytest
  409 [import    ]     from modules.artist_dossier.manager import resolve_vocal_source_index
  410 [blank     ] 
  411 [stmt      ]     with pytest.raises(ValueError, match="does not expose"):
  412 [code      ]         resolve_vocal_source_index(SimpleNamespace(sources=["bass", "drums", "other"]))
  413 [blank     ] 
  414 [blank     ] 
  415 [blank     ] 
  416 [def       ] def test_asr_transcribes_reference_with_faster_whisper_contract(tmp_path) -> None:
  417 [import    ]     from types import SimpleNamespace
  418 [blank     ] 
  419 [import    ]     from modules.artist_dossier.manager import transcribe_reference_audio
  420 [blank     ] 
  421 [class     ]     class FakeASR:
  422 [def       ]         def __init__(self):
  423 [code      ]             self.kwargs = None
  424 [blank     ] 
  425 [def       ]         def transcribe(self, audio_path, **kwargs):
  426 [code      ]             self.kwargs = {"audio_path": audio_path, **kwargs}
  427 [return    ]             return iter([SimpleNamespace(text=" первая строка "), SimpleNamespace(text="вторая строка")]), SimpleNamespace(language="ru")
  428 [blank     ] 
  429 [code      ]     handle = FakeASR()
  430 [code      ]     transcript = tmp_path / "lyrics" / "reference.txt"
  431 [code      ]     result = transcribe_reference_audio(handle, "reference.wav", str(transcript))
  432 [blank     ] 
  433 [stmt      ]     assert result["ok"] is True
  434 [stmt      ]     assert result["lyrics"] == "первая строка\nвторая строка"
  435 [stmt      ]     assert result["language"] == "ru"
  436 [stmt      ]     assert transcript.read_text(encoding="utf-8") == result["lyrics"]
  437 [stmt      ]     assert handle.kwargs == {"audio_path": "reference.wav", "language": "ru", "beam_size": 5}
  438 [blank     ] 
  439 [blank     ] 
  440 [def       ] def test_asr_reports_runtime_failure() -> None:
  441 [import    ]     from modules.artist_dossier.manager import transcribe_reference_audio
  442 [blank     ] 
  443 [class     ]     class FailingASR:
  444 [def       ]         def transcribe(self, *args, **kwargs):
  445 [raise     ]             raise RuntimeError("model load failed")
  446 [blank     ] 
  447 [code      ]     result = transcribe_reference_audio(FailingASR(), "reference.wav", "/tmp/unused.txt")
  448 [blank     ] 
  449 [stmt      ]     assert result["ok"] is False
  450 [stmt      ]     assert "model load failed" in result["reason"]
  451 [blank     ] 
  452 [blank     ] 
  453 [blank     ] 
  454 [def       ] def test_asr_rejects_invalid_transcript_without_writing_file(tmp_path) -> None:
  455 [import    ]     from types import SimpleNamespace
  456 [blank     ] 
  457 [import    ]     from modules.artist_dossier.manager import transcribe_reference_audio
  458 [blank     ] 
  459 [class     ]     class RepetitiveASR:
  460 [def       ]         def transcribe(self, *args, **kwargs):
  461 [return    ]             return iter([SimpleNamespace(text="эй эй эй эй")]), SimpleNamespace(language="ru")
  462 [blank     ] 
  463 [code      ]     transcript = tmp_path / "lyrics" / "invalid.txt"
  464 [code      ]     result = transcribe_reference_audio(RepetitiveASR(), "reference.wav", str(transcript))
  465 [blank     ] 
  466 [stmt      ]     assert result["ok"] is False
  467 [stmt      ]     assert result["reason"] == "ASR transcript is excessively repetitive"
  468 [stmt      ]     assert result["fallback"] == "reference audio retained; transcript is not used"
  469 [stmt      ]     assert not transcript.exists()
  470 [blank     ] 
  471 [blank     ] 
  472 [blank     ] 
  473 [def       ] def test_clap_tag_ranking_uses_score_order_and_candidate_vocabulary() -> None:
  474 [import    ]     from modules.artist_dossier.manager import rank_clap_tags
  475 [blank     ] 
  476 [code      ]     tags = rank_clap_tags(["phonk", "trap", "pop", "rock"], [0.2, 0.9, -0.1, 0.5], limit=3)
  477 [blank     ] 
  478 [stmt      ]     assert tags == ["trap", "rock", "phonk"]
  479 [blank     ] 
  480 [blank     ] 
  481 [def       ] def test_clap_tag_ranking_rejects_mismatched_scores() -> None:
  482 [import    ]     import pytest
  483 [blank     ] 
  484 [import    ]     from modules.artist_dossier.manager import rank_clap_tags
  485 [blank     ] 
  486 [stmt      ]     with pytest.raises(ValueError, match="do not match"):
  487 [code      ]         rank_clap_tags(["phonk", "trap"], [0.1])
```