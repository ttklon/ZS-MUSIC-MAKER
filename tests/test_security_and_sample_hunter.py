"""`app/core/security_utils.py` и `agents/sample_hunter/{planner,local}.py`.

Все три достижимы (`REAL_PASS`): `redact_secrets` зовётся логгером,
`download_file`/`safe_hash` — загрузкой сэмплов, `plan_queries` —
`hunter.hunt`, `list_local`/`save_manifest` — локальной библиотекой.

Здесь важна не «покрытость», а обещания безопасности:
- `safe_identifier` не пропускает `..`, слэши и абсолютные компоненты;
- `redact_secrets` вычищает токены до записи в лог;
- `download_file` отвергает схемы, отличные от http/https;
- `save_manifest` не обещает лицензию, которой у сэмпла нет.

Найденный дефект: `download_file(url, "file.wav")` — цель без каталога —
падал `FileNotFoundError` на `os.makedirs(os.path.dirname(...), "")` и
возвращал `False`, хотя файл мог быть записан рядом. Скачивание при этом уже
состоялось: сеть потрачена, результат потерян.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core import security_utils as su
from agents.sample_hunter import local as hunter_local
from agents.sample_hunter import planner as hunter_planner


# --------------------------------------------------------------------------- #
#  security_utils
# --------------------------------------------------------------------------- #
class TestSafeIdentifier:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("my_track", "my_track"),
            ("Трек 1", "Трек_1"),
            ("  spaced  ", "spaced"),
            ("dots...", "unknown"),  # содержит ".." — отвергается целиком
            ("a/b", "unknown"),
            ("a\\b", "unknown"),
            ("..", "unknown"),
            (".", "unknown"),
            ("", "unknown"),
            ("   ", "unknown"),
        ],
    )
    def test_sanitises(self, raw, expected) -> None:
        assert su.safe_identifier(raw) == expected

    def test_traversal_inside_name_is_rejected(self) -> None:
        # "../../etc/passwd" содержит и ".." и слэши
        assert su.safe_identifier("../../etc/passwd") == "unknown"

    def test_max_length_is_enforced(self) -> None:
        assert len(su.safe_identifier("a" * 500)) == 96

    def test_custom_fallback_and_length(self) -> None:
        assert su.safe_identifier("", fallback="anon") == "anon"
        assert len(su.safe_identifier("b" * 20, max_length=5)) == 5

    def test_only_punctuation_falls_back(self) -> None:
        assert su.safe_identifier("!!!") == "unknown"


class TestSafeChildPath:
    def test_child_is_under_root(self, tmp_path) -> None:
        child = su.safe_child_path(tmp_path, "track 1")
        assert child.parent == tmp_path.resolve()
        assert child.name == "track_1"

    def test_traversal_becomes_fallback_inside_root(self, tmp_path) -> None:
        child = su.safe_child_path(tmp_path, "../../etc/passwd")
        assert child.parent == tmp_path.resolve()
        assert ".." not in str(child)


class TestRedactSecrets:
    def test_github_token_is_redacted(self) -> None:
        text = "token: github_pat_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
        assert "github_pat_" not in su.redact_secrets(text)
        assert "[REDACTED]" in su.redact_secrets(text)

    def test_api_key_is_redacted(self) -> None:
        assert "sk-abcdefghijklmnop1234" not in su.redact_secrets(
            "ключ sk-abcdefghijklmnop1234 в логе"
        )

    def test_bearer_is_redacted(self) -> None:
        assert "[REDACTED]" in su.redact_secrets("Authorization: Bearer abc.def-123_4567890")

    def test_plain_text_is_untouched(self) -> None:
        assert su.redact_secrets("обычный текст без секретов") == "обычный текст без секретов"

    def test_non_string_input_is_stringified(self) -> None:
        assert su.redact_secrets(None) == "None"

    def test_short_token_is_not_a_secret(self) -> None:
        # порог длины: "sk-1" не должен превращаться в [REDACTED]
        assert su.redact_secrets("sk-1") == "sk-1"


class TestSafeHash:
    def test_is_sha256_not_md5(self) -> None:
        digest = su.safe_hash("hello")
        assert len(digest) == 64
        assert digest == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_stable_and_input_sensitive(self) -> None:
        assert su.safe_hash("a") == su.safe_hash("a")
        assert su.safe_hash("a") != su.safe_hash("b")


class FakeResponse:
    def __init__(self, status=200, chunks=(), raise_status=None):
        self.status_code = status
        self._chunks = chunks
        self._raise = raise_status

    def raise_for_status(self):
        if self._raise:
            raise self._raise

    def iter_content(self, chunk_size=8192):
        yield from self._chunks


class TestDownloadFile:
    def test_writes_nested_target(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(
            su.requests, "get", lambda *a, **k: FakeResponse(chunks=[b"abc", b"def"])
        )
        target = tmp_path / "deep" / "dir" / "s.wav"
        assert su.download_file("https://example.com/s.wav", str(target)) is True
        assert target.read_bytes() == b"abcdef"

    def test_target_without_directory_works(self, tmp_path, monkeypatch) -> None:
        """Регрессия: `os.path.dirname("file.wav")` == "" → FileNotFoundError.

        Скачивание уже состоялось, а результат терялся с `Download failed`.
        """
        monkeypatch.setattr(su.requests, "get", lambda *a, **k: FakeResponse(chunks=[b"x"]))
        monkeypatch.chdir(tmp_path)
        assert su.download_file("https://example.com/s.wav", "file.wav") is True
        assert (tmp_path / "file.wav").read_bytes() == b"x"

    @pytest.mark.parametrize("url", ["ftp://example.com/a.wav", "file:///etc/passwd", "javascript:1"])
    def test_unsupported_scheme_raises(self, url) -> None:
        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            su.download_file(url, "x.wav")

    def test_network_error_returns_false(self, tmp_path, monkeypatch) -> None:
        def boom(*a, **k):
            raise ConnectionError("нет сети")

        monkeypatch.setattr(su.requests, "get", boom)
        assert su.download_file("https://example.com/s.wav", str(tmp_path / "s.wav")) is False

    def test_http_error_returns_false(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(
            su.requests,
            "get",
            lambda *a, **k: FakeResponse(raise_status=RuntimeError("404")),
        )
        assert su.download_file("https://example.com/s.wav", str(tmp_path / "s.wav")) is False

    def test_timeout_is_passed(self, tmp_path, monkeypatch) -> None:
        seen = {}

        def spy(url, timeout=None, stream=None):
            seen["timeout"] = timeout
            return FakeResponse(chunks=[b"ok"])

        monkeypatch.setattr(su.requests, "get", spy)
        su.download_file("https://example.com/s.wav", str(tmp_path / "s.wav"), timeout=7)
        assert seen["timeout"] == 7


class TestGetJson:
    def test_returns_parsed_json(self, monkeypatch) -> None:
        class R:
            @staticmethod
            def raise_for_status():
                return None

            @staticmethod
            def json():
                return {"a": 1}

        monkeypatch.setattr(su.requests, "get", lambda *a, **k: R())
        assert su.get_json("https://example.com/api") == {"a": 1}

    def test_bad_scheme_returns_none_without_network(self, monkeypatch) -> None:
        def fail(*a, **k):
            raise AssertionError("сеть не должна вызываться")

        monkeypatch.setattr(su.requests, "get", fail)
        assert su.get_json("ftp://example.com/api") is None

    def test_error_returns_none(self, monkeypatch) -> None:
        def boom(*a, **k):
            raise TimeoutError("нет ответа")

        monkeypatch.setattr(su.requests, "get", boom)
        assert su.get_json("https://example.com/api") is None


# --------------------------------------------------------------------------- #
#  planner
# --------------------------------------------------------------------------- #
class TestPlanner:
    def test_known_genre_uses_its_keywords(self) -> None:
        queries = hunter_planner.plan_queries({"genre_hint": "phonk / drift", "bpm": 140})
        assert any("phonk" in q for q in queries)
        # при лимите по умолчанию (8) сохраняются два bpm-запроса, а не все три
        assert "loop 140 bpm" in queries
        assert "drum loop 140 bpm" in queries

    def test_all_bpm_queries_survive_when_limit_allows(self) -> None:
        queries = hunter_planner.plan_queries(
            {"genre_hint": "phonk / drift", "bpm": 140}, max_queries=100
        )
        assert "loop 140 bpm" in queries
        assert "drum loop 140 bpm" in queries
        assert "bass 140 bpm sample" in queries

    def test_unknown_genre_falls_back_to_generic(self) -> None:
        queries = hunter_planner.plan_queries({"genre_hint": "неизвестный жанр", "bpm": 120})
        assert "loop 120 bpm" in queries
        assert queries  # список не пуст даже для незнакомого жанра

    def test_genre_key_fallback(self) -> None:
        queries = hunter_planner.plan_queries({"genre": "trap / hip-hop", "bpm": 90})
        assert any("trap" in q for q in queries)
        assert "loop 90 bpm" in queries

    def test_default_bpm_when_absent(self) -> None:
        queries = hunter_planner.plan_queries({})
        assert "loop 130 bpm" in queries

    def test_none_style_vector_does_not_crash(self) -> None:
        assert hunter_planner.plan_queries(None)

    def test_bpm_as_string_and_none(self) -> None:
        assert "loop 128 bpm" in hunter_planner.plan_queries({"bpm": "128"})
        # None и 0 считаются отсутствием значения
        assert "loop 130 bpm" in hunter_planner.plan_queries({"bpm": None})
        assert "loop 130 bpm" in hunter_planner.plan_queries({"bpm": 0})

    def test_max_queries_is_respected(self) -> None:
        for limit in (1, 3, 8, 100):
            queries = hunter_planner.plan_queries({"bpm": 140}, max_queries=limit)
            assert len(queries) <= limit
            # регрессия: при max_queries=8 bpm-запросы отрезались все до одного
            assert any("140 bpm" in q for q in queries)

    def test_no_duplicates(self) -> None:
        queries = hunter_planner.plan_queries({"genre_hint": "dance / edm", "bpm": 126})
        assert len(queries) == len(set(queries))


# --------------------------------------------------------------------------- #
#  local library
# --------------------------------------------------------------------------- #
@pytest.fixture()
def lib(tmp_path, monkeypatch):
    """Локальная библиотека, кэш и manifest — в tmp."""
    local_dir = tmp_path / "samples_cache"
    manifest_dir = tmp_path / "manifests"
    monkeypatch.setattr(hunter_local, "LOCAL_LIB", local_dir)
    monkeypatch.setattr(hunter_local, "CACHE", local_dir)
    monkeypatch.setattr(hunter_local, "MANIFEST_DIR", manifest_dir)
    return local_dir


def touch_audio(root: Path, name: str, size: int = 2048) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    path.write_bytes(b"\0" * size)
    return path


class TestListLocal:
    def test_missing_library_gives_empty_list(self, lib, tmp_path) -> None:
        assert hunter_local.list_local() == []

    def test_finds_audio_recursively(self, lib) -> None:
        touch_audio(lib, "kick.wav")
        touch_audio(lib / "nested", "snare.FLAC")
        (lib / "notes.txt").write_text("не аудио", encoding="utf-8")

        items = hunter_local.list_local()
        names = sorted(item["name"] for item in items)
        assert names == ["kick.wav", "snare.FLAC"]

    def test_item_has_provenance_fields(self, lib) -> None:
        touch_audio(lib, "kick.wav", size=2048)
        item = hunter_local.list_local()[0]
        assert item["source"] == "local"
        assert item["license"] == "user_supplied"
        assert item["url"] is None
        assert item["size"] == 2048
        assert item["size_kb"] == 2.0
        assert item["path"].endswith("kick.wav")

    def test_query_filters_by_substring_case_insensitive(self, lib) -> None:
        touch_audio(lib, "Deep_Kick.wav")
        touch_audio(lib, "snare.wav")
        assert [i["name"] for i in hunter_local.list_local("kick")] == ["Deep_Kick.wav"]
        assert [i["name"] for i in hunter_local.list_local("SNARE")] == ["snare.wav"]

    def test_empty_query_returns_all(self, lib) -> None:
        touch_audio(lib, "a.wav")
        touch_audio(lib, "b.wav")
        assert len(hunter_local.list_local("")) == 2
        assert len(hunter_local.list_local(None)) == 2

    def test_no_match_returns_empty(self, lib) -> None:
        touch_audio(lib, "a.wav")
        assert hunter_local.list_local("zzz") == []

    def test_directories_are_skipped(self, lib) -> None:
        (lib / "folder.wav").mkdir(parents=True)
        assert hunter_local.list_local() == []


class TestDownloadToCache:
    def test_local_item_returns_its_path(self, lib) -> None:
        path = touch_audio(lib, "mine.wav")
        assert hunter_local.download_to_cache(
            {"source": "local", "path": str(path), "name": "mine.wav"}
        ) == str(path)

    def test_item_without_url_is_refused(self, lib) -> None:
        assert hunter_local.download_to_cache({"source": "freesound", "name": "x"}) is None

    def test_download_writes_sanitised_name(self, lib, monkeypatch) -> None:
        seen = {}

        def fake_download(url, target, timeout=30):
            seen["url"] = url
            seen["target"] = target
            path = Path(target)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"data")
            return True

        monkeypatch.setattr(su, "download_file", fake_download)
        result = hunter_local.download_to_cache(
            {"source": "../evil source", "url": "https://example.com/a.wav", "name": "../../x.wav"}
        )
        assert result is not None
        name = Path(result).name
        assert ".." not in name
        assert "/" not in name
        assert seen["url"] == "https://example.com/a.wav"

    def test_cached_file_is_returned_without_network(self, lib, monkeypatch) -> None:
        calls = []
        monkeypatch.setattr(su, "download_file", lambda *a, **k: calls.append(1) or True)

        item = {"source": "freesound", "url": "https://example.com/a.wav", "name": "a.wav"}
        digest = su.safe_hash(item["url"])[:10]
        existing = lib / f"freesound_{digest}_a.wav"
        lib.mkdir(parents=True, exist_ok=True)
        existing.write_bytes(b"cached")

        assert hunter_local.download_to_cache(item) == str(existing)
        assert calls == []  # сеть не трогали вовсе

    def test_second_call_reuses_downloaded_file(self, lib, monkeypatch) -> None:
        calls = []

        def fake_download(url, target, **k):
            calls.append(1)
            Path(target).write_bytes(b"RIFF")
            return True

        monkeypatch.setattr(su, "download_file", fake_download)
        item = {"source": "freesound", "url": "https://example.com/b.wav", "name": "b.wav"}
        first = hunter_local.download_to_cache(item)
        second = hunter_local.download_to_cache(item)
        assert first is not None
        assert second == first
        assert len(calls) == 1  # второй раз — из кэша

    def test_zero_byte_download_is_refused(self, lib, monkeypatch) -> None:
        """Файл создан, но пуст — путь отдавать нельзя."""

        def fake_download(url, target, **k):
            Path(target).write_bytes(b"")
            return True

        monkeypatch.setattr(su, "download_file", fake_download)
        assert (
            hunter_local.download_to_cache(
                {"source": "s", "url": "https://example.com/a.wav", "name": "a.wav"}
            )
            is None
        )

    def test_failed_download_returns_none(self, lib, monkeypatch) -> None:
        monkeypatch.setattr(su, "download_file", lambda *a, **k: False)
        assert (
            hunter_local.download_to_cache(
                {"source": "freesound", "url": "https://example.com/a.wav", "name": "a.wav"}
            )
            is None
        )

    def test_name_is_truncated_and_safe(self, lib, monkeypatch) -> None:
        def fake_download(url, target, **k):
            Path(target).write_bytes(b"RIFF")
            return True

        monkeypatch.setattr(su, "download_file", fake_download)
        result = hunter_local.download_to_cache(
            {"source": "s", "url": "https://example.com/a.wav", "name": "x" * 200}
        )
        name = Path(result).name
        # 96 символов — предел safe_identifier, и ".."" внутрь не проходит
        assert len(name) <= 96
        assert ".." not in name

    def test_downloaded_file_keeps_audio_extension(self, lib, monkeypatch) -> None:
        """Регрессия: safe_identifier убирал точку → файл пропадал из list_local.

        Санитизация основы имени обязана сохранять `.wav`, иначе скачанный
        сэмпл лежит на диске, но локальная библиотека его не видит.
        """

        def fake_download(url, target, **k):
            Path(target).write_bytes(b"RIFF")  # 4 байта — файл есть
            return True

        monkeypatch.setattr(su, "download_file", fake_download)
        result = hunter_local.download_to_cache(
            {"source": "../../evil", "url": "https://example.com/a.wav", "name": "../../Pick.wav"}
        )
        assert Path(result).suffix == ".wav"
        assert ".." not in Path(result).name
        # ".." в основе означает отказ от имени целиком → fallback sample_<hash>,
        # но расширение сохранено, поэтому библиотека файл видит
        assert Path(result).name.startswith("sample_")
        assert [i["name"] for i in hunter_local.list_local()] == [Path(result).name]


class TestManifest:
    def test_manifest_is_written_with_notice(self, tmp_path, monkeypatch) -> None:
        target = tmp_path / "manifests"
        monkeypatch.setattr(hunter_local, "MANIFEST_DIR", target)
        items = [{"name": "a.wav", "license": "CC0"}]
        path = hunter_local.save_manifest(items, "proj_1")

        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        assert payload["project_id"] == "proj_1"
        assert payload["total"] == 1
        assert payload["items"] == items
        assert "CC0" in payload["notice"]
        assert payload["ts"] > 0

    def test_manifest_overwrites_same_project(self, tmp_path, monkeypatch) -> None:
        target = tmp_path / "manifests"
        monkeypatch.setattr(hunter_local, "MANIFEST_DIR", target)
        hunter_local.save_manifest([{"name": "a"}], "p")
        path = hunter_local.save_manifest([{"name": "b"}], "p")
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        assert payload["total"] == 1
        assert payload["items"] == [{"name": "b"}]

    def test_empty_list_is_recorded_honestly(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(hunter_local, "MANIFEST_DIR", tmp_path / "m")
        path = hunter_local.save_manifest([], "empty")
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        assert payload["total"] == 0
        assert payload["items"] == []
