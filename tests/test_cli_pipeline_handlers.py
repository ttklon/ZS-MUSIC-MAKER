"""CLI-обработчики пайплайнов, досье и проб: `main.py --run/--god/--dossier-*`.

`app/cli/pipeline.py` (21 %), `app/cli/dossier.py` (22 %), `app/cli/probes.py`
(25 %) достижимы прямо из `main.py`, но проверялся только разбор флагов.
Тяжёлые стадии здесь подменяются: тест держит контракт «код возврата + что
напечатано», а не работу оркестратора (её проверяют свои тесты и гейты).

Живой прогон `--run --seed 42` даёт `PASS_BLOCKED`, percent 83: честно
заблокированные стадии не дают «PASS», и код возврата для такого прогона — 1.
"""

from __future__ import annotations

import json
import types

import pytest

from app.cli import dossier as dossier_cmds
from app.cli import pipeline as pipeline_cmds
from app.cli import probes as probe_cmds


@pytest.fixture()
def printed(monkeypatch, capsys):
    """Все строки, ушедшие в safe_print, — так проверяются сообщения."""
    seen: list[str] = []
    for mod in (pipeline_cmds, dossier_cmds, probe_cmds):
        monkeypatch.setattr(
            mod, "safe_print", lambda msg, _s=seen: (seen.append(str(msg)), print(msg))
        )
    return seen


def make_args(**kw) -> types.SimpleNamespace:
    base = dict(
        genre="drift_phonk",
        theme="night drive",
        dossier_artist="",
        seed=None,
        only=None,
        dry_run=False,
        resume=False,
    )
    base.update(kw)
    return types.SimpleNamespace(**base)


class TestParseOnly:
    def test_empty_is_none(self) -> None:
        assert pipeline_cmds.parse_only("") is None

    def test_none_is_none(self) -> None:
        assert pipeline_cmds.parse_only(None) is None

    def test_single(self) -> None:
        assert pipeline_cmds.parse_only("beat") == {"beat"}

    def test_list_trims_spaces(self) -> None:
        assert pipeline_cmds.parse_only(" beat , lyrics ,, master ") == {
            "beat",
            "lyrics",
            "master",
        }


class TestRunPipeline:
    def _patch_run(self, monkeypatch, result=None, raises=None):
        import app.core.orchestrator as orch

        calls = {}

        def fake(project_id, state, **kw):
            calls["project_id"] = project_id
            calls["state"] = state
            calls["kw"] = kw
            if raises:
                raise raises
            return result or {}

        monkeypatch.setattr(orch, "run_full_pipeline", fake)
        return calls

    def test_success_returns_zero_for_pass(self, monkeypatch, printed) -> None:
        self._patch_run(
            monkeypatch,
            {"verdict": "PASS", "percent": 100, "master_path": "out/m.wav", "seed": 42},
        )
        assert pipeline_cmds.run_pipeline(make_args()) == 0
        payload = json.loads("\n".join(printed))
        assert payload["verdict"] == "PASS"
        assert payload["master"] == "out/m.wav"
        assert payload["seed"] == 42  # печатается то, что вернул пайплайн

    def test_blocked_verdict_returns_one(self, monkeypatch, printed) -> None:
        self._patch_run(monkeypatch, {"verdict": "PASS_BLOCKED", "percent": 83})
        assert pipeline_cmds.run_pipeline(make_args(seed=42)) == 1
        assert "PASS_BLOCKED" in "\n".join(printed)

    def test_missing_verdict_is_not_pass(self, monkeypatch, printed) -> None:
        self._patch_run(monkeypatch, {})
        assert pipeline_cmds.run_pipeline(make_args()) == 1

    def test_flag_mapping(self, monkeypatch) -> None:
        calls = self._patch_run(monkeypatch, {"verdict": "PASS"})
        pipeline_cmds.run_pipeline(
            make_args(
                dossier_artist="kalash", seed=7, only="beat,lyrics", dry_run=True, resume=True
            )
        )
        assert calls["project_id"] == "cli_drift_phonk"
        assert calls["state"] == {
            "genre": "drift_phonk",
            "theme": "night drive",
            "artist": "kalash",
            "seed": 7,
        }
        assert calls["kw"] == {"dry_run": True, "only": {"beat", "lyrics"}, "resume": True}

    def test_seed_none_not_in_state(self, monkeypatch) -> None:
        calls = self._patch_run(monkeypatch, {"verdict": "PASS"})
        pipeline_cmds.run_pipeline(make_args())
        assert "seed" not in calls["state"]

    def test_value_error_returns_two_with_message(self, monkeypatch, printed) -> None:
        self._patch_run(monkeypatch, raises=ValueError("жанр не найден"))
        assert pipeline_cmds.run_pipeline(make_args()) == 2
        assert "жанр не найден" in "\n".join(printed)

    def test_unexpected_error_returns_two(self, monkeypatch, printed) -> None:
        self._patch_run(monkeypatch, raises=RuntimeError("упало"))
        assert pipeline_cmds.run_pipeline(make_args()) == 2
        assert "упало" in "\n".join(printed)


class TestListStages:
    def test_lists_keys(self, printed) -> None:
        from app.core.pipeline_runtime import STAGE_KEYS

        assert pipeline_cmds.run_list_stages() == 0
        text = "\n".join(printed)
        assert "Stages usable with --only" in text
        for key in STAGE_KEYS:
            assert key in text


class TestAiPipeline:
    def _patched(self, monkeypatch, result=None, raises=None):
        import app.core.orchestrator_ai as oa

        backups: list[str] = []
        import app.cli.backup as backup_mod

        monkeypatch.setattr(backup_mod, "preflight_backup", backups.append)

        def fake(run_id, workspace, dry_run=False, terminal_progress=False):
            if raises:
                raise raises
            return result or {"report": {"stages": {"a": "ok"}}, "artefacts": {"m": "x.wav"}}

        monkeypatch.setattr(oa, "run_ai_pipeline", fake)
        return backups

    def test_ai_runs_and_prints_stages(self, monkeypatch, printed) -> None:
        backups = self._patched(monkeypatch)
        assert pipeline_cmds.run_ai(make_args()) == 0
        assert backups == ["ai"]
        payload = json.loads("\n".join(printed))
        assert payload["stages"] == {"a": "ok"}
        assert payload["artefacts"] == {"m": "x.wav"}

    def test_dry_run_has_no_artefacts(self, monkeypatch, printed) -> None:
        backups = self._patched(monkeypatch)
        assert pipeline_cmds.run_ai_dry_run(make_args()) == 0
        assert backups == ["ai_dry_run"]
        payload = json.loads("\n".join(printed))
        assert "artefacts" not in payload

    def test_failure_returns_two(self, monkeypatch, printed) -> None:
        self._patched(monkeypatch, raises=RuntimeError("нет модели"))
        assert pipeline_cmds.run_ai(make_args()) == 2
        assert "нет модели" in "\n".join(printed)

    def test_artist_passed_as_slug(self, monkeypatch) -> None:
        import app.core.orchestrator_ai as oa

        seen = {}
        monkeypatch.setattr(
            oa,
            "run_ai_pipeline",
            lambda run_id, workspace, **kw: seen.update(
                {"ws": workspace, "dry": kw.get("dry_run")}
            )
            or {"report": {"stages": {}}},
        )
        pipeline_cmds._run_ai_pipeline(make_args(dossier_artist="kalash"), dry_run=True, run_id="r")
        assert seen["ws"]["artist_slug"] == "kalash"
        assert seen["dry"] is True


class TestRunGod:
    def test_unknown_genre_refused_with_hint(self, monkeypatch, printed) -> None:
        assert pipeline_cmds.run_god(make_args(genre="drift_phonkz")) == 2
        text = "\n".join(printed)
        assert "unknown genre" in text
        assert "did you mean" in text
        assert "--list-genres" in text

    def test_unknown_genre_without_close_match(self, monkeypatch, printed) -> None:
        assert pipeline_cmds.run_god(make_args(genre="zzzzqqqq")) == 2
        assert "did you mean" not in "\n".join(printed)

    def test_known_genre_runs_pipeline(self, monkeypatch, printed) -> None:
        import app.core.orchestrator_god as og
        import app.cli.backup as backup_mod

        backups: list[str] = []
        monkeypatch.setattr(backup_mod, "preflight_backup", backups.append)
        monkeypatch.setattr(
            og,
            "run_god_pipeline",
            lambda rid, ws: {"elapsed_sec": 12.5, "master_path": "out/god.wav"},
        )
        assert pipeline_cmds.run_god(make_args()) == 0
        text = "\n".join(printed)
        assert "GOD MODE COMPLETED" in text
        assert "out/god.wav" in text
        assert backups == ["god"]

    def test_partial_verdict_says_so_instead_of_master_none(self, monkeypatch, printed) -> None:
        """Вердикт PARTIAL не должен выглядеть как «мастера нет».

        Живой прогон `--god --genre phonk` закончился строкой
        `GOD MODE COMPLETED: elapsed=513.401s master=None`, хотя мастер лежал
        в `output/god_cli/masters/master_streaming.wav`: оркестратор отдаёт
        `master_path` только при статусе `completed`, а консоль печатала
        `None` без причины. Шесть стадий были BLOCKED (нет TTS, RVC, demucs),
        и человек не мог понять, где искать файл.
        """
        import app.cli.backup as backup_mod
        import app.core.orchestrator_god as og

        monkeypatch.setattr(backup_mod, "preflight_backup", lambda mode: None)
        monkeypatch.setattr(
            og,
            "run_god_pipeline",
            lambda rid, ws: {
                "elapsed_sec": 12.5,
                "status": "partial",
                "master_path": None,
                "report_path": "out/god_cli/report.json",
                "blocked": ["_stage_voice_synth", "_stage_stems"],
            },
        )
        assert pipeline_cmds.run_god(make_args()) == 0
        text = "\n".join(printed)
        assert "master=None" not in text, "нет мастера — так и надо писать, а не None"
        assert "частично" in text.lower()
        assert "report.json" in text

    def test_pipeline_failure_returns_two(self, monkeypatch, printed) -> None:
        import app.core.orchestrator_god as og
        import app.cli.backup as backup_mod

        monkeypatch.setattr(backup_mod, "preflight_backup", lambda mode: None)

        def boom(rid, ws):
            raise RuntimeError("нет GPU")

        monkeypatch.setattr(og, "run_god_pipeline", boom)
        assert pipeline_cmds.run_god(make_args()) == 2
        assert "нет GPU" in "\n".join(printed)

    def test_genre_registry_unavailable_falls_through(self, monkeypatch, printed) -> None:
        # Импорт реестра может упасть (нет зависимостей) — прогон не должен
        # превращаться в отказ: проверка жанра необязательна.
        import builtins

        import app.core.orchestrator_god as og
        import app.cli.backup as backup_mod

        monkeypatch.setattr(backup_mod, "preflight_backup", lambda mode: None)
        monkeypatch.setattr(og, "run_god_pipeline", lambda rid, ws: {"master_path": "m"})
        real_import = builtins.__import__

        def guard(name, *a, **k):
            if name == "modules.genre_engine":
                raise ImportError("нет модуля")
            return real_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", guard)
        assert pipeline_cmds.run_god(make_args()) == 0
        assert "GOD MODE COMPLETED" in "\n".join(printed)


class TestRunAsync:
    def test_success_returns_zero(self, monkeypatch) -> None:
        import app.core.orchestrator_async as oa

        class Fake:
            def __init__(self, rid, out):
                self.out = out

            async def run_pipeline(self, ws):
                return {"status": "done"}

        monkeypatch.setattr(oa, "AsyncOrchestrator", Fake)
        assert pipeline_cmds.run_async(make_args()) == 0

    def test_failed_status_returns_one(self, monkeypatch, printed) -> None:
        import app.core.orchestrator_async as oa

        class Fake:
            def __init__(self, rid, out):
                pass

            async def run_pipeline(self, ws):
                return {"status": "failed"}

        monkeypatch.setattr(oa, "AsyncOrchestrator", Fake)
        assert pipeline_cmds.run_async(make_args()) == 1
        assert "status=failed" in "\n".join(printed)

    def test_exception_returns_one(self, monkeypatch, printed) -> None:
        import app.core.orchestrator_async as oa

        class Fake:
            def __init__(self, rid, out):
                pass

            async def run_pipeline(self, ws):
                raise RuntimeError("нет цикла событий")

        monkeypatch.setattr(oa, "AsyncOrchestrator", Fake)
        assert pipeline_cmds.run_async(make_args()) == 1
        assert "PIPELINE FAILED" in "\n".join(printed)

    def test_non_dict_result_is_not_a_failure(self, monkeypatch) -> None:
        import app.core.orchestrator_async as oa

        class Fake:
            def __init__(self, rid, out):
                pass

            async def run_pipeline(self, ws):
                return None

        monkeypatch.setattr(oa, "AsyncOrchestrator", Fake)
        assert pipeline_cmds.run_async(make_args()) == 0


class TestDossier:
    def test_add_collects_local_and_vault(self, monkeypatch, printed, tmp_path) -> None:
        from modules import artist_dossier
        from modules.artist_dossier import collectors

        source = tmp_path / "src"
        source.mkdir()
        seen = {}

        class Local:
            def __init__(self, path):
                seen["local"] = path

            def collect(self, artist):
                return ["t1"]

        class Vault:
            def __init__(self, path):
                seen["vault"] = path

            def collect(self, artist):
                return ["t2"]

        class Manager:
            def add_artist(self, artist, tracks=None):
                seen["added"] = (artist, tracks)
                return True

        monkeypatch.setattr(collectors, "LocalFolderCollector", Local)
        monkeypatch.setattr(collectors, "LyricVaultCollector", Vault)
        monkeypatch.setattr(artist_dossier, "DossierManager", Manager)

        assert dossier_cmds.run_dossier_add("kalash", str(source)) == 0
        assert seen["added"] == ("kalash", ["t1", "t2"])
        assert "tracks_added=2" in "\n".join(printed)

    def test_add_skips_missing_source_dir(self, monkeypatch, printed, tmp_path) -> None:
        from modules import artist_dossier
        from modules.artist_dossier import collectors

        seen = {}

        class Vault:
            def __init__(self, path):
                pass

            def collect(self, artist):
                return []

        class Manager:
            def add_artist(self, artist, tracks=None):
                seen["tracks"] = tracks
                return True

        monkeypatch.setattr(collectors, "LyricVaultCollector", Vault)
        monkeypatch.setattr(artist_dossier, "DossierManager", Manager)
        assert dossier_cmds.run_dossier_add("kalash", str(tmp_path / "нет")) == 0
        assert seen["tracks"] == []
        assert "tracks_added=0" in "\n".join(printed)

    def test_add_failure_returns_two(self, monkeypatch, printed) -> None:
        from modules import artist_dossier

        def boom(*a, **k):
            raise RuntimeError("индекс битый")

        monkeypatch.setattr(artist_dossier, "DossierManager", boom)
        assert dossier_cmds.run_dossier_add("kalash", "/tmp") == 2
        assert "индекс битый" in "\n".join(printed)

    def test_build_prints_dossier(self, monkeypatch, printed) -> None:
        from modules import artist_dossier

        class Manager:
            def build_full_dossier(self, artist, progress_cb=None):
                if progress_cb:
                    progress_cb("track-1", "features")
                return {"artist": artist, "tracks": 3}

        monkeypatch.setattr(artist_dossier, "DossierManager", Manager)
        assert dossier_cmds.run_dossier_build("kalash") == 0
        text = "\n".join(printed)
        assert "[track-1] features" in text
        assert '"tracks": 3' in text

    def test_build_failure_returns_two(self, monkeypatch, printed) -> None:
        from modules import artist_dossier

        def boom(*a, **k):
            raise RuntimeError("нет модели")

        monkeypatch.setattr(artist_dossier, "DossierManager", boom)
        assert dossier_cmds.run_dossier_build("kalash") == 2
        assert "нет модели" in "\n".join(printed)


class TestProbes:
    def test_health_snapshot_prints_verdict(self, monkeypatch, printed) -> None:
        from modules import health

        rep = types.SimpleNamespace(verdict="OK", percent_ready=72, core_ok=True)
        monkeypatch.setattr(health, "collect", lambda: rep)
        out = probe_cmds.health_snapshot()
        assert out == {"verdict": "OK", "percent": 72}
        text = "\n".join(printed)
        assert "ready=72%" in text
        assert "not verified" in text  # оговорка про непроверенное остаётся

    def test_health_unavailable_is_unknown_not_ok(self, monkeypatch, printed) -> None:
        from modules import health

        def boom():
            raise RuntimeError("нет модуля")

        monkeypatch.setattr(health, "collect", boom)
        out = probe_cmds.health_snapshot()
        assert out == {"verdict": "UNKNOWN", "percent": 0}
        assert "not available" in "\n".join(printed)
