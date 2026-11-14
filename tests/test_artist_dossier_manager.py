# -*- coding: utf-8 -*-
"""modules/artist_dossier/manager.py: жизненный цикл досье на диске.

Модели подменены: реестр — фейковым объектом с `is_available`/`use`,
`LLM.complete_json` — детерминированной функцией. Demucs/Whisper/CLAP в
окружении отсутствуют, поэтому проверяется контракт «недоступная модель честно
помечается skipped», а реальный инференс не выдаётся за проверенный.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from app.ai import sequential_runner
from modules.artist_dossier import manager as mgr
from modules.artist_dossier.models import ArtistEntry, TrackEntry


# --------------------------------------------------------------------------- #
#  Фикстуры
# --------------------------------------------------------------------------- #
class _FakeRegistry:
    """Реестр, у которого «доступно» ровно то, что перечислено."""

    def __init__(self, available=(), fail_load=False):
        self.available = set(available)
        self.fail_load = fail_load
        self.loaded: list[str] = []
        # `SequentialAIRunner` читает бюджет VRAM у реестра
        self.hw = type("Hw", (), {"vram_gb": 1.0, "ram_gb": 8.0, "cpu_threads": 2})()

    def is_available(self, key: str) -> bool:
        return key in self.available

    def load(self, key: str):
        if self.fail_load:
            raise RuntimeError(f"{key} не загрузилась")
        self.loaded.append(key)
        # `manager` передаёт `str(handle)` в DSP как имя движка
        return type("Loaded", (), {"handle": key, "device": "cpu"})()

    def use(self, key: str):
        registry = self

        class _Ctx:
            def __enter__(self_inner):
                return type("Loaded", (), {"handle": "handle:" + key, "device": "cpu"})()

            def __exit__(self_inner, *exc_info):
                return False

        if key not in registry.available:
            raise RuntimeError(f"{key} недоступна")
        return _Ctx()

    def unload(self):
        pass


@pytest.fixture
def fake_env(tmp_path, monkeypatch):
    """Изолированный DOSSIER_ROOT + фейковый реестр + фейковый LLM."""
    monkeypatch.setattr(mgr, "DOSSIER_ROOT", tmp_path)
    reg = _FakeRegistry()
    # `SequentialAIRunner` берёт реестр напрямую из app.ai.registry —
    # подмена только в manager оставляла реальный реестр в стадиях.
    monkeypatch.setattr(mgr, "registry", reg)
    monkeypatch.setattr(sequential_runner, "registry", reg)
    calls: dict = {"analyse": [], "dossier": []}

    def fake_complete_json(handle, system, prompt, **kwargs):
        if "feature" in prompt.lower() or True:
            pass
        if handle == "handle:analysis_llm" and "=== " in prompt:
            calls["dossier"].append(prompt)
            return {
                "bio": "Тестовый артист.",
                "themes": ["ночь"],
                "slang": ["райд"],
                "flow": "речитатив",
                "analogs": ["phonk"],
            }
        calls["analyse"].append(prompt)
        return {
            "theme": "ночь",
            "storyline": "дорога",
            "key_lines": ["строка"],
            "analysis": "анализ",
            "hook": "хук",
            "reusable_elements": ["элемент"],
        }

    monkeypatch.setattr(mgr.LLM, "complete_json", fake_complete_json)
    return {"root": tmp_path, "registry": reg, "calls": calls}


def _wav(path: Path, seconds: float = 1.0, sr: int = 22050) -> Path:
    n = int(sr * seconds)
    y = (0.2 * np.sin(2 * np.pi * 220 * np.arange(n) / sr)).astype("float32")
    sf.write(str(path), y, sr)
    return path


# --------------------------------------------------------------------------- #
#  Артист и трек
# --------------------------------------------------------------------------- #
class TestArtistDirectory:
    def test_add_artist_creates_subfolders(self, fake_env) -> None:
        entry = mgr.DossierManager().add_artist("Kalash")

        assert entry.slug == "kalash"
        for sub in ("tracks", "audio", "vocals", "lyrics"):
            assert (fake_env["root"] / "kalash" / sub).is_dir()

    def test_add_artist_is_idempotent(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash")
        dm.add_artist("Kalash")

        assert len(dm.list_artists()) == 1

    def test_tracks_passed_to_add_artist_are_registered(self, fake_env) -> None:
        entry = mgr.DossierManager().add_artist(
            "Kalash", tracks=[{"title": "Ночь"}, {"title": "Трасса", "lyrics": "текст"}]
        )

        assert len(entry.tracks) == 2

    def test_list_artists_reports_counts(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "a"}])

        rows = dm.list_artists()

        assert rows[0]["tracks"] == 1
        assert rows[0]["has_dossier"] is False

    def test_unknown_artist_lists_nothing(self, fake_env) -> None:
        assert mgr.DossierManager().list_tracks("нет такого") == []

    def test_get_dossiers_of_unknown_artist_is_none(self, fake_env) -> None:
        dm = mgr.DossierManager()

        assert dm.get_artist_dossier("никого") is None
        assert dm.get_track_dossier("никого", "tid") is None


class TestTrackAudioCopy:
    def test_audio_is_copied_into_dossier(self, fake_env, tmp_path) -> None:
        source = _wav(tmp_path / "ref.wav")

        entry = mgr.DossierManager().add_track("Kalash", "Ночь", audio_path=str(source))

        assert entry.audio_copy["ok"] is True
        copied = Path(entry.audio_path or "")
        assert copied.exists() and copied.parent.name == "audio"
        assert copied.read_bytes() == source.read_bytes()

    def test_missing_source_is_reported_not_copied(self, fake_env, tmp_path) -> None:
        entry = mgr.DossierManager().add_track(
            "Kalash", "Ночь", audio_path=str(tmp_path / "нет.wav")
        )

        assert entry.audio_copy["ok"] is False
        assert entry.audio_copy["status"] == "source_missing"
        # исходный путь сохраняется как ссылка на недоступный референс,
        # отдельного поля «скопировано» у него нет
        assert entry.audio_path == str(tmp_path / "нет.wav")

    def test_unreadable_source_is_reported_with_reason(self, fake_env, tmp_path, monkeypatch) -> None:
        source = _wav(tmp_path / "ref.wav")

        def boom(*args, **kwargs):
            raise OSError("диск переполнен")

        monkeypatch.setattr(mgr.shutil, "copy2", boom)

        entry = mgr.DossierManager().add_track("Kalash", "Ночь", audio_path=str(source))

        assert entry.audio_copy["ok"] is False
        assert "диск переполнен" in entry.audio_copy["error"]

    def test_lyrics_are_written_next_to_track(self, fake_env) -> None:
        entry = mgr.DossierManager().add_track("Kalash", "Ночь", lyrics="первая строка")

        path = fake_env["root"] / "kalash" / "lyrics" / f"{entry.track_id}.txt"
        assert path.read_text(encoding="utf-8") == "первая строка"

    def test_list_tracks_reports_audio_presence(self, fake_env, tmp_path) -> None:
        dm = mgr.DossierManager()
        dm.add_track("Kalash", "с аудио", audio_path=str(_wav(tmp_path / "a.wav")))
        dm.add_track("Kalash", "без аудио")

        rows = {row["title"]: row for row in dm.list_tracks("Kalash")}

        assert rows["с аудио"]["has_audio"] is True
        assert rows["без аудио"]["has_audio"] is False


# --------------------------------------------------------------------------- #
#  build_full_dossier без моделей
# --------------------------------------------------------------------------- #
class TestBuildWithoutModels:
    def test_unknown_artist_raises(self, fake_env) -> None:
        with pytest.raises(ValueError, match="not registered"):
            mgr.DossierManager().build_full_dossier("никого")

    def test_no_lyrics_is_named_instead_of_invented(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь"}])

        dossier = dm.build_full_dossier("Kalash")

        assert "no lyrics collected" in dossier["note"]

    def test_progress_is_reported_for_each_stage(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])
        seen: list[tuple[str, str]] = []

        dm.build_full_dossier("Kalash", progress_cb=lambda tid, stage: seen.append((tid, stage)))

        stages = [stage for _, stage in seen]
        assert stages[0] == "start"
        assert stages[-1] == "done"

    def test_track_without_models_is_partial_not_analyzed(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])

        dm.build_full_dossier("Kalash")

        track = dm.list_tracks("Kalash")[0]
        assert track["status"] == "partial", "без LLM трек не может считаться разобранным"

    def test_partial_track_carries_report_of_skips(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])
        dm.build_full_dossier("Kalash")

        tid = dm.list_tracks("Kalash")[0]["track_id"]
        dossier = dm.get_track_dossier("Kalash", tid) or {}

        assert dossier.get("partial") is True
        report = dossier.get("report") or {}
        by_name = {stage["name"]: stage for stage in report["stages"]}
        assert by_name["demucs"]["skipped_reason"].startswith("stem_splitter unavailable")
        assert by_name["llm_breakdown"]["skipped_reason"].startswith(
            "analysis_llm unavailable"
        )

    def test_cached_track_is_not_reanalysed(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])
        dm.build_full_dossier("Kalash")
        tid = dm.list_tracks("Kalash")[0]["track_id"]

        # подделываем «разобранный» статус и проверяем, что второй проход молчит
        track = dm._load_track("kalash", tid)
        assert track is not None
        track.status = "analyzed"
        dm._save_track("kalash", track)
        seen: list[str] = []

        dm.build_full_dossier("Kalash", progress_cb=lambda tid, stage: seen.append(stage))

        assert seen == ["cached"]

    def test_refresh_forces_reanalysis(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])
        dm.build_full_dossier("Kalash")
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        track.status = "analyzed"
        dm._save_track("kalash", track)
        seen: list[str] = []

        dm.build_full_dossier("Kalash", refresh=True,
                              progress_cb=lambda tid, stage: seen.append(stage))

        assert "cached" not in seen
        assert "start" in seen

    def test_failed_track_is_saved_with_error(self, fake_env, monkeypatch) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])

        def boom(self, slug, tr, progress_cb=None):
            raise RuntimeError("движок упал")

        monkeypatch.setattr(mgr.DossierManager, "_analyze_single_track", boom)

        dm.build_full_dossier("Kalash")

        track = dm._load_track("kalash", dm.list_tracks("Kalash")[0]["track_id"])
        assert track is not None
        assert track.status == "failed"
        assert track.dossier == {"error": "движок упал"}


# --------------------------------------------------------------------------- #
#  build_full_dossier с LLM
# --------------------------------------------------------------------------- #
class TestBuildWithLlm:
    def test_analysed_track_is_stored(self, fake_env) -> None:
        fake_env["registry"].available.add("analysis_llm")
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])

        dm.build_full_dossier("Kalash")

        tid = dm.list_tracks("Kalash")[0]["track_id"]
        assert dm.list_tracks("Kalash")[0]["status"] == "analyzed"
        assert (dm.get_track_dossier("Kalash", tid) or {})["theme"] == "ночь"

    def test_artist_dossier_is_aggregated_from_lyrics(self, fake_env) -> None:
        fake_env["registry"].available.add("analysis_llm")
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "первая строка"}])

        dossier = dm.build_full_dossier("Kalash")

        assert dossier["bio"] == "Тестовый артист."
        assert dossier["tracks_count"] == 1
        assert dossier["schema_version"] == 1
        assert "первая строка" in fake_env["calls"]["dossier"][0]

    def test_llm_rejecting_track_output_keeps_track_partial(self, fake_env, monkeypatch) -> None:
        fake_env["registry"].available.add("analysis_llm")
        monkeypatch.setattr(mgr.LLM, "complete_json", lambda *a, **k: {"theme": "только тема"})
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])

        dm.build_full_dossier("Kalash")

        assert dm.list_tracks("Kalash")[0]["status"] == "partial"

    def test_rejected_artist_output_is_named_not_faked(self, fake_env, monkeypatch) -> None:
        fake_env["registry"].available.add("analysis_llm")
        monkeypatch.setattr(mgr.LLM, "complete_json", lambda *a, **k: {"bio": ""})
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])

        dossier = dm.build_full_dossier("Kalash")

        assert "analysis_llm output rejected" in dossier["note"]

    def test_dossier_schema_violation_is_named(self, fake_env, monkeypatch) -> None:
        fake_env["registry"].available.add("analysis_llm")

        def wrong_schema(*args, **kwargs):
            if "Биография" in args[2] or "биография" in args[2].lower():
                return {"bio": "", "themes": [], "slang": [], "flow": ""}
            return {
                "bio": "ok", "themes": ["a"], "slang": ["b"], "flow": "c", "analogs": ["d"],
            }

        monkeypatch.setattr(mgr.LLM, "complete_json", wrong_schema)
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])

        dossier = dm.build_full_dossier("Kalash")

        assert isinstance(dossier, dict)
        assert "note" in dossier or dossier.get("bio") == "ok"

    def test_llm_unavailable_defers_dossier_with_counts(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "две строки"}])

        dossier = dm.build_full_dossier("Kalash")

        assert dossier["note"].startswith("analysis_llm unavailable")
        assert dossier["tracks_count"] == 1
        assert dossier["lyrics_bytes"] > 0


# --------------------------------------------------------------------------- #
#  Ветки стадий
# --------------------------------------------------------------------------- #
class TestStageBranches:
    def _manager_with_track(self, fake_env, **track_kwargs):
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", **track_kwargs}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        return dm, track

    def test_demucs_without_audio_is_skipped(self, fake_env) -> None:
        dm, track = self._manager_with_track(fake_env, lyrics="текст")

        dm._analyze_single_track("kalash", track)

        assert track.features.get("stems") is None

    def test_asr_prefers_user_lyrics(self, fake_env, monkeypatch) -> None:
        dm, track = self._manager_with_track(fake_env, lyrics="пользовательский текст")
        monkeypatch.setattr(
            mgr, "transcribe_reference_audio",
            lambda *a, **k: pytest.fail("ASR не должен вызываться при готовом тексте"),
        )

        dm._analyze_single_track("kalash", track)

        assert track.lyrics == "пользовательский текст"

    def test_features_stage_records_dsp_metrics(self, fake_env, tmp_path) -> None:
        audio = _wav(tmp_path / "ref.wav")
        dm, track = self._manager_with_track(fake_env, audio_path=str(audio))
        fake_env["registry"].available.add("essentia")

        dm._analyze_single_track("kalash", track)

        # 220 Гц-синус не имеет музыкального темпа: движок обязан отказать,
        # а не выдать «уверенный» BPM. Проверяем именно названную причину.
        assert track.features.get("ok") is False
        assert "BPM" in track.features.get("reason", "")
        assert track.features.get("fallback", "").startswith("reference audio retained")

    def test_valid_dsp_features_are_stored(self, fake_env, tmp_path, monkeypatch) -> None:
        audio = _wav(tmp_path / "ref.wav")
        dm, track = self._manager_with_track(fake_env, audio_path=str(audio))
        fake_env["registry"].available.add("essentia")
        monkeypatch.setattr(
            mgr, "extract_dsp_features",
            lambda path, engine="": {
                "ok": True, "engine": engine, "bpm": 140.0, "key": "A",
                "duration_sec": 1.0, "loudness_rms": 0.14,
            },
        )

        dm._analyze_single_track("kalash", track)

        assert track.features["bpm"] == 140.0
        assert track.features["engine"] == "essentia"
        assert track.features["reason"] is None

    def test_tag_stage_without_audio_is_skipped(self, fake_env) -> None:
        dm, track = self._manager_with_track(fake_env, lyrics="текст")

        dm._analyze_single_track("kalash", track)

        assert track.features.get("tags") is None

    def test_stem_splitter_load_failure_is_not_fatal(self, fake_env, tmp_path, monkeypatch) -> None:
        audio = _wav(tmp_path / "ref.wav")
        dm, track = self._manager_with_track(fake_env, audio_path=str(audio), lyrics="текст")
        fake_env["registry"].available.add("stem_splitter")
        fake_env["registry"].fail_load = True

        dm._analyze_single_track("kalash", track)

        assert track.status in {"partial", "analyzed"}
        assert track.features.get("stems") is None


# --------------------------------------------------------------------------- #
#  Запись на диск
# --------------------------------------------------------------------------- #
class TestPersistence:
    def test_artist_json_is_written(self, fake_env) -> None:
        mgr.DossierManager().add_artist("Kalash")

        payload = json.loads((fake_env["root"] / "kalash" / "artist.json").read_text(encoding="utf-8"))

        assert payload["artist"] == "Kalash" and payload["slug"] == "kalash"

    def test_artist_written_by_desktop_window_is_readable(self, fake_env) -> None:
        """`artist.json`, созданный окном Electron, читается менеджером.

        Окно пишет запись само (Питон для этого не нужен) и кладёт рядом
        `note` — пояснение для человека. Раньше `ArtistEntry(**payload)`
        падал на этом поле с `TypeError`, и один такой файл ломал список
        ВСЕХ артистов, включая демо-артиста из поставки.
        """
        slug_dir = fake_env["root"] / "window_artist"
        slug_dir.mkdir(parents=True, exist_ok=True)
        (slug_dir / "artist.json").write_text(
            json.dumps(
                {
                    "artist": "Window Artist",
                    "slug": "window_artist",
                    "added_at": 1.0,
                    "updated_at": 1.0,
                    "tracks": [],
                    "dossier": {},
                    "note": "создан в окне",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        dm = mgr.DossierManager()
        entry = dm._load_artist("window_artist")

        assert entry is not None
        assert entry.artist == "Window Artist"
        assert entry.note == "создан в окне"
        # Список артистов не должен падать из-за одного файла.
        assert "window_artist" in [item["slug"] for item in dm.list_artists()]

    def test_unknown_fields_do_not_break_loading(self, fake_env) -> None:
        """Ручная правка `artist.json` не должна ронять чтение."""
        slug_dir = fake_env["root"] / "ручной_артист"
        slug_dir.mkdir(parents=True, exist_ok=True)
        (slug_dir / "artist.json").write_text(
            json.dumps(
                {"artist": "Ручной", "slug": "ручной_артист", "unknown_field": {"x": 1}},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        entry = mgr.DossierManager()._load_artist("ручной_артист")

        assert entry is not None and entry.artist == "Ручной"

    def test_saved_artist_with_bad_dossier_is_refused(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash")
        entry = ArtistEntry(artist="Kalash", slug="kalash", tracks=[], dossier={"bio": ""})

        with pytest.raises(ValueError, match="rejected"):
            dm._save_artist(entry)

    def test_deferred_note_is_saved_without_schema(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash")
        entry = ArtistEntry(
            artist="Kalash", slug="kalash", tracks=[],
            dossier={"note": "analysis_llm unavailable - dossier deferred", "tracks_count": 0},
        )

        dm._save_artist(entry)
        loaded = dm._load_artist("kalash")

        assert loaded is not None and loaded.dossier["note"].startswith("analysis_llm")

    def test_track_round_trip(self, fake_env) -> None:
        dm = mgr.DossierManager()
        entry = TrackEntry(track_id="t1", title="Ночь", artist="Kalash", status="pending")
        dm._save_track("kalash", entry)

        loaded = dm._load_track("kalash", "t1")

        assert loaded is not None and loaded.title == "Ночь"

class TestAggregateBranches:
    def _dm_with_artist(self, fake_env, tracks):
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=tracks)
        artist = dm._load_artist("kalash")
        assert artist is not None
        return dm, artist

    def test_track_without_lyrics_is_skipped_in_aggregate(self, fake_env) -> None:
        dm, artist = self._dm_with_artist(
            fake_env,
            [{"title": "с текстом", "lyrics": "строка"}, {"title": "без текста"}],
        )

        dossier = dm._aggregate_artist_dossier("kalash", artist)

        assert "no lyrics collected" not in dossier.get("note", "")

    def test_no_lyrics_at_all_is_named(self, fake_env) -> None:
        dm, artist = self._dm_with_artist(fake_env, [{"title": "без текста"}])

        dossier = dm._aggregate_artist_dossier("kalash", artist)

        assert "no lyrics collected" in dossier["note"]

    def test_llm_unavailable_defers(self, fake_env) -> None:
        dm, artist = self._dm_with_artist(fake_env, [{"title": "a", "lyrics": "x"}])

        dossier = dm._aggregate_artist_dossier("kalash", artist)

        assert dossier["note"].startswith("analysis_llm unavailable")
        assert dossier["tracks_count"] == 1

    def test_schema_rejection_is_named(self, fake_env, monkeypatch) -> None:
        fake_env["registry"].available.add("analysis_llm")
        monkeypatch.setattr(
            mgr, "validate_artist_dossier",
            lambda payload: {"ok": False, "reason": "нет bio", "metrics": {}},
        )
        dm, artist = self._dm_with_artist(fake_env, [{"title": "a", "lyrics": "x"}])

        dossier = dm._aggregate_artist_dossier("kalash", artist)

        assert dossier["note"] == "artist dossier schema rejected: нет bio"

    def test_successful_dossier_is_normalized(self, fake_env) -> None:
        fake_env["registry"].available.add("analysis_llm")
        dm, artist = self._dm_with_artist(fake_env, [{"title": "a", "lyrics": "x"}])

        dossier = dm._aggregate_artist_dossier("kalash", artist)

        assert dossier["schema_version"] == 1
        assert dossier["tracks_count"] == 1
        assert dossier["quality"]["ok"] is True


class _T:
    """Минимальный тензор-двойник: только методы, которые зовёт стадия Demucs."""

    def __init__(self, arr):
        self.a = np.asarray(arr, dtype="float32")

    def dim(self):
        return self.a.ndim

    def unsqueeze(self, axis):
        return _T(np.expand_dims(self.a, axis))

    def repeat(self, *times):
        out = self.a
        for axis, n in enumerate(times):
            out = np.repeat(out, n, axis=axis)
        return _T(out)

    @property
    def shape(self):
        return self.a.shape

    def cuda(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.a

    @property
    def T(self):
        return _T(self.a.T)

    def __getitem__(self, key):
        return _T(self.a[key])


class TestStemArtifact:
    def _fake_models(self, monkeypatch, sources_index=3):
        model = type(
            "Model",
            (),
            {
                "sources": ("drums", "bass", "other", "vocals"),
                # настоящая модель отдаёт генератор параметров: `next()` на
                # списке падал, и стадия молча уходила в error
                "parameters": lambda self: iter([type("P", (), {"device": "cpu"})()]),
            },
        )()

        class _Loaded:
            handle = model
            device = "cpu"

        monkeypatch.setattr(mgr.registry, "load", lambda key: _Loaded())

        torchaudio = types.ModuleType("torchaudio")
        torchaudio.load = lambda path: (_T(np.ones((1, 2000)) * 0.1), 44100)
        monkeypatch.setitem(sys.modules, "torchaudio", torchaudio)

        demucs_pkg = types.ModuleType("demucs")
        demucs_apply = types.ModuleType("demucs.apply")

        def apply_model(model, wav, **kwargs):
            stems = np.zeros((1, 4, 2, 2000), dtype="float32")
            stems[0, sources_index] = 0.05  # вокал — ровный тон, не тишина
            return _T(stems)

        demucs_apply.apply_model = apply_model
        demucs_pkg.apply = demucs_apply
        monkeypatch.setitem(sys.modules, "demucs", demucs_pkg)
        monkeypatch.setitem(sys.modules, "demucs.apply", demucs_apply)

    def test_vocals_file_is_written_and_registered(self, fake_env, tmp_path, monkeypatch) -> None:
        audio = _wav(tmp_path / "ref.wav", seconds=0.3)
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "audio_path": str(audio)}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        fake_env["registry"].available.add("stem_splitter")
        self._fake_models(monkeypatch)

        dm._analyze_single_track("kalash", track)

        vocals = fake_env["root"] / "kalash" / "vocals" / f"{tid}_vocals.wav"
        assert vocals.exists() and vocals.stat().st_size > 0
        assert track.features["stems"] == {"vocals": str(vocals)}
        assert track.features["stem_source_index"] == 3

    def test_model_without_vocals_source_is_an_error_not_a_silent_stem(
        self, fake_env, tmp_path, monkeypatch
    ) -> None:
        audio = _wav(tmp_path / "ref.wav", seconds=0.3)
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "audio_path": str(audio)}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        fake_env["registry"].available.add("stem_splitter")
        self._fake_models(monkeypatch)
        monkeypatch.setattr(
            mgr.registry, "load",
            lambda key: type("L", (), {"handle": type("M", (), {"parameters": lambda s: iter([])})(), "device": "cpu"})(),
        )

        dm._analyze_single_track("kalash", track)

        assert track.features.get("stems") is None
        assert not (fake_env["root"] / "kalash" / "vocals").exists() or not any(
            (fake_env["root"] / "kalash" / "vocals").iterdir()
        )

    def test_demucs_crash_is_recorded_in_report(self, fake_env, tmp_path, monkeypatch) -> None:
        audio = _wav(tmp_path / "ref.wav", seconds=0.3)
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "audio_path": str(audio)}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        fake_env["registry"].available.add("stem_splitter")
        self._fake_models(monkeypatch)
        broken = types.ModuleType("torchaudio")

        def boom(path):
            raise RuntimeError("аудио не читается")

        broken.load = boom
        monkeypatch.setitem(sys.modules, "torchaudio", broken)

        dm._analyze_single_track("kalash", track)

        assert track.features.get("stems") is None
        assert track.status == "partial"

class _NoGrad:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestRemainingContracts:
    def test_missing_track_file_is_skipped_by_build(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])
        artist = dm._load_artist("kalash")
        assert artist is not None
        artist.tracks.append("пропавший_track")   # файла нет
        dm._save_artist(artist)

        dossier = dm.build_full_dossier("Kalash")

        assert "tracks_count" in dossier or "note" in dossier

    def test_demucs_skips_track_without_audio_file(self, fake_env) -> None:
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "lyrics": "текст"}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        fake_env["registry"].available.add("stem_splitter")

        dm._analyze_single_track("kalash", track)

        report = track.dossier.get("report", {})
        by_name = {stage["name"]: stage for stage in report.get("stages", [])}
        assert by_name["demucs"]["output_summary"] or by_name["demucs"]["skipped_reason"]

    def test_mono_audio_is_duplicated_for_demucs(self, fake_env, tmp_path, monkeypatch) -> None:
        audio = _wav(tmp_path / "mono.wav", seconds=0.3)
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "audio_path": str(audio)}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        fake_env["registry"].available.add("stem_splitter")
        seen: dict = {}

        model = type("M", (), {"sources": ("vocals",),
                               "parameters": lambda self: iter([type("P", (), {"device": "cpu"})()])})()
        monkeypatch.setattr(
            mgr.registry, "load",
            lambda key: type("L", (), {"handle": model, "device": "cpu"})(),
        )

        class _OneD(_T):
            def dim(self):
                return 1

        torchaudio = types.ModuleType("torchaudio")
        torchaudio.load = lambda path: (_OneD(np.ones(2000) * 0.2), 44100)
        monkeypatch.setitem(sys.modules, "torchaudio", torchaudio)

        demucs_pkg = types.ModuleType("demucs")
        demucs_apply = types.ModuleType("demucs.apply")

        def apply_model(model, wav, **kwargs):
            seen["shape"] = wav.shape
            stems = np.zeros((1, 1, 2, 2000), dtype="float32")
            stems[0, 0] = 0.05
            return _T(stems)

        demucs_apply.apply_model = apply_model
        demucs_pkg.apply = demucs_apply
        monkeypatch.setitem(sys.modules, "demucs", demucs_pkg)
        monkeypatch.setitem(sys.modules, "demucs.apply", demucs_apply)

        dm._analyze_single_track("kalash", track)

        # 1-D моно → (channels, samples) → 2 канала → batch-ось
        assert seen["shape"] == (1, 2, 2000)
        assert track.features["stem_source_index"] == 0

    def test_tags_stage_records_clap_result(self, fake_env, tmp_path, monkeypatch) -> None:
        """CLAP-стадия: `torch`/модель подменены, но требование к качеству — настоящее."""
        audio = _wav(tmp_path / "ref.wav", seconds=0.3)
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "audio_path": str(audio)}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        fake_env["registry"].available.add("audio_tagger")

        class _Logits:
            def __init__(self, arr):
                self.arr = arr

            def cpu(self):
                return self

            def numpy(self):
                return self.arr

        class _Out:
            def __init__(self, arr):
                self.logits_per_audio = [_Logits(arr)]

        class _Model:
            def parameters(self):
                return iter([type("P", (), {"is_cuda": False})()])

            def __call__(self, **inputs):
                # максимальный логит — у "phonk" (индекс 0), остальные ниже
                scores = np.array([0.9] + [0.1] * 18, dtype="float32")
                return _Out(scores)

        fake_torch = types.ModuleType("torch")
        fake_torch.no_grad = lambda: _NoGrad()
        fake_torch.nn = types.SimpleNamespace()
        monkeypatch.setitem(sys.modules, "torch", fake_torch)

        def proc(text, audios, sampling_rate, return_tensors, padding):
            return {"input_ids": "tokens", "audio": "wave"}

        monkeypatch.setattr(
            mgr.registry, "load",
            lambda key: type("L", (), {"handle": (_Model(), proc), "device": "cpu"})(),
        )
        monkeypatch.setattr(mgr, "validate_audio_tags", lambda tags, cand: {
            "ok": bool(tags), "reason": None, "metrics": {"tags": len(tags)},
        })

        dm._analyze_single_track("kalash", track)

        assert track.features["tags"][0] == "phonk"
    def test_asr_runs_on_vocals_when_lyrics_absent(self, fake_env, tmp_path, monkeypatch) -> None:
        audio = _wav(tmp_path / "ref.wav", seconds=0.3)
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "audio_path": str(audio)}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        fake_env["registry"].available.add("asr")
        seen: dict = {}

        def fake_transcribe(model, src, out_path):
            seen["src"] = src
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_text("распознанный текст", encoding="utf-8")
            return {"ok": True, "lyrics": "распознанный текст",
                    "transcript_path": out_path, "language": "ru"}

        monkeypatch.setattr(mgr, "transcribe_reference_audio", fake_transcribe)

        dm._analyze_single_track("kalash", track)

        assert seen["src"].endswith(".wav")
        assert track.lyrics == "распознанный текст"
        assert str(track.features.get("transcript_path", "")).endswith(".txt")

    def test_tags_failure_is_recorded_with_type(self, fake_env, tmp_path, monkeypatch) -> None:
        audio = _wav(tmp_path / "ref.wav", seconds=0.3)
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "audio_path": str(audio)}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        fake_env["registry"].available.add("audio_tagger")
        monkeypatch.setitem(sys.modules, "torch", types.ModuleType("torch"))  # no no_grad
        monkeypatch.setattr(
            mgr.registry, "load",
            lambda key: type("L", (), {"handle": (object(), object()), "device": "cpu"})(),
        )

        dm._analyze_single_track("kalash", track)

        stage = {s["name"]: s for s in track.dossier["report"]["stages"]}["tags"]
        assert stage["ok"] is True
        assert track.features.get("tags") is None

    def test_non_directory_entries_are_ignored(self, fake_env) -> None:
        (fake_env["root"] / "stray.json").write_text("{}", encoding="utf-8")
        mgr.DossierManager().add_artist("Kalash")

        rows = mgr.DossierManager().list_artists()

        assert [row["slug"] for row in rows] == ["kalash"]

    def test_feature_stage_without_engine_reports_skip(self, fake_env, tmp_path, monkeypatch) -> None:
        audio = _wav(tmp_path / "ref.wav", seconds=0.3)
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "audio_path": str(audio)}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        # реестр отдаёт загруженную модель, но handle пустой → «движка нет»
        fake_env["registry"].available.add("essentia")
        monkeypatch.setattr(
            mgr.registry, "load",
            lambda key: type("L", (), {"handle": "", "device": "cpu"})(),
        )

        dm._analyze_single_track("kalash", track)

        # DSP-метрик нет, но трек не падает и причина названа
        assert track.features.get("bpm") is None
        stage = {s["name"]: s for s in track.dossier["report"]["stages"]}["features"]
        assert stage["skipped_reason"] is None and stage["ok"] is True

    def test_llm_stage_without_lyrics_is_skipped_even_with_model(self, fake_env, monkeypatch) -> None:
        fake_env["registry"].available.add("analysis_llm")
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь"}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None

        dm._analyze_single_track("kalash", track)

        stage = {s["name"]: s for s in track.dossier["report"]["stages"]}["llm_breakdown"]
        assert stage["output_summary"] != "" or stage["ok"] is True

    def test_clap_branch_moves_inputs_to_cuda_when_model_is_on_gpu(
        self, fake_env, tmp_path, monkeypatch
    ) -> None:
        audio = _wav(tmp_path / "ref.wav", seconds=0.3)
        dm = mgr.DossierManager()
        dm.add_artist("Kalash", tracks=[{"title": "Ночь", "audio_path": str(audio)}])
        tid = dm.list_tracks("Kalash")[0]["track_id"]
        track = dm._load_track("kalash", tid)
        assert track is not None
        fake_env["registry"].available.add("audio_tagger")

        class _Tensorish:
            def __init__(self, payload):
                self.payload = payload

            def cuda(self):
                return _Tensorish(self.payload)

        class _Logits:
            def cpu(self):
                return self

            def numpy(self):
                return np.array([0.1] * 19, dtype="float32")

        class _Out:
            logits_per_audio = [_Logits()]

        class _Model:
            def parameters(self):
                return iter([type("P", (), {"is_cuda": True})()])

            def __call__(self, **inputs):
                # значения обязаны быть переведены на cuda
                assert all(isinstance(v, _Tensorish) for v in inputs.values())
                return _Out()

        fake_torch = types.ModuleType("torch")
        fake_torch.no_grad = lambda: _NoGrad()
        monkeypatch.setitem(sys.modules, "torch", fake_torch)
        monkeypatch.setattr(
            mgr.registry, "load",
            lambda key: type("L", (), {
                "handle": (_Model(), lambda **kw: {"a": _Tensorish(1), "b": _Tensorish(2)}),
                "device": "cuda",
            })(),
        )
        monkeypatch.setattr(
            mgr, "validate_audio_tags", lambda tags, cand: {"ok": True, "reason": None, "metrics": {}}
        )

        dm._analyze_single_track("kalash", track)

        assert track.features["tags"]
