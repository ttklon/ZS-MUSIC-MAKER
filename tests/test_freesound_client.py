# -*- coding: utf-8 -*-
"""modules/freesound_client.py: поиск, офлайн-кэш, скачивание превью, manifest.

Сеть не нужна: `requests` подменяется объектом-заглушкой, политика сети
включается явно через `online_enabled`. Проверяется то, что видит
пользователь: найденные сэмплы, существование скачанного файла и запись о
лицензии в manifest.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modules import freesound_client as fc


class _Response:
    def __init__(self, status_code=200, payload=None, text="", chunks=(b"RIFF",)):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self._chunks = chunks

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload

    def iter_content(self, size):
        return iter(self._chunks)


class _Get:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    def __call__(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        if self.error:
            raise self.error
        return self.response


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Изолированное окружение: кэш, manifest и ключ внутри tmp_path."""
    cache = tmp_path / "samples_cache"
    cache.mkdir()
    monkeypatch.setattr(fc, "DEFAULT_CACHE", cache)
    monkeypatch.setattr(fc, "DEFAULT_MANIFEST", tmp_path / "data" / "manifest.json")
    monkeypatch.setattr(fc, "online_enabled", lambda *a, **k: True)
    monkeypatch.setattr(fc, "_load_key", lambda: "test-key")
    return cache


# --------------------------------------------------------------------------- #
#  Поиск
# --------------------------------------------------------------------------- #
class TestSearch:
    def test_offline_policy_never_touches_network(self, env, monkeypatch) -> None:
        get = _Get(error=AssertionError("сеть запрещена"))
        monkeypatch.setattr(fc, "requests", type("R", (), {"get": staticmethod(get)}))
        monkeypatch.setattr(fc, "online_enabled", lambda *a, **k: False)

        result = fc.search("kick")

        assert result["offline"] is True
        assert get.calls == []

    def test_online_results_are_mapped(self, env, monkeypatch) -> None:
        payload = {
            "results": [
                {
                    "id": 7,
                    "name": "kick.wav",
                    "tags": ["kick"],
                    "license": "Creative Commons 0",
                    "duration": 1.5,
                    "bpm": 140,
                    "username": "demo",
                    "previews": {"preview-hq-mp3": "https://cdn/x.mp3"},
                }
            ]
        }
        get = _Get(_Response(payload=payload))
        monkeypatch.setattr(fc, "requests", type("R", (), {"get": staticmethod(get)}))

        result = fc.search("kick", bpm_min=120, bpm_max=150, allow_online=True)

        assert result["offline"] is False
        assert result["count"] == 1
        item = result["results"][0]
        assert item["id"] == 7 and item["author"] == "demo"
        assert item["preview_mp3"] == "https://cdn/x.mp3"
        assert item["preview_ogg"] is None
        assert get.calls[0]["url"] == fc.FS_ENDPOINT
        assert get.calls[0]["params"]["token"] == "test-key"
        assert "bpm:[120 TO 150]" in get.calls[0]["params"]["filter"]

    def test_cc0_filter_is_on_by_default(self, env, monkeypatch) -> None:
        get = _Get(_Response(payload={"results": []}))
        monkeypatch.setattr(fc, "requests", type("R", (), {"get": staticmethod(get)}))

        fc.search("kick", allow_online=True)

        assert 'license:"Creative Commons 0"' in get.calls[0]["params"]["filter"]

    def test_http_error_falls_back_to_cache(self, env, monkeypatch) -> None:
        (env / "kick_cached.wav").write_bytes(b"x")
        get = _Get(_Response(status_code=403, text="forbidden"))
        monkeypatch.setattr(fc, "requests", type("R", (), {"get": staticmethod(get)}))

        result = fc.search("kick", allow_online=True)

        assert result["offline"] is True
        assert [r["name"] for r in result["results"]] == ["kick_cached.wav"]

    def test_network_exception_falls_back_to_cache(self, env, monkeypatch) -> None:
        monkeypatch.setattr(
            fc, "requests", type("R", (), {"get": staticmethod(_Get(error=OSError("DNS"))) })
        )

        result = fc.search("kick", allow_online=True)

        assert result["offline"] is True
        assert result["count"] == 0

    def test_missing_key_means_offline(self, env, monkeypatch) -> None:
        monkeypatch.setattr(fc, "_load_key", lambda: None)
        monkeypatch.setattr(
            fc, "requests", type("R", (), {"get": staticmethod(_Get(error=AssertionError("сеть")))})
        )

        assert fc.search("kick", allow_online=True)["offline"] is True

    def test_missing_requests_means_offline(self, env, monkeypatch) -> None:
        monkeypatch.setattr(fc, "requests", None)

        assert fc.search("kick", allow_online=True)["offline"] is True


class TestOfflineSearch:
    def test_missing_cache_is_empty_not_crash(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(fc, "DEFAULT_CACHE", tmp_path / "нет")

        result = fc._offline_search("kick")

        assert result == {"ok": True, "count": 0, "results": [], "offline": True}

    def test_wav_and_mp3_are_both_found(self, env) -> None:
        (env / "deep").mkdir()
        (env / "Kick_808.wav").write_bytes(b"x")
        (env / "deep" / "kick_loop.mp3").write_bytes(b"x")
        (env / "snare.wav").write_bytes(b"x")

        result = fc._offline_search("KICK")

        names = sorted(r["name"] for r in result["results"])
        assert names == ["Kick_808.wav", "kick_loop.mp3"]
        assert all(r["source"] == "local_cache" for r in result["results"])

    def test_cache_result_hashes_are_stable(self, env) -> None:
        (env / "kick.wav").write_bytes(b"x")

        first = fc._offline_search("kick")["results"][0]
        second = fc._offline_search("kick")["results"][0]

        assert first["id"] == second["id"] and len(first["id"]) == 8


# --------------------------------------------------------------------------- #
#  Скачивание превью
# --------------------------------------------------------------------------- #
class TestDownloadPreview:
    def test_offline_returns_local_path(self, env, monkeypatch) -> None:
        monkeypatch.setattr(fc, "online_enabled", lambda *a, **k: False)

        assert fc.download_preview({"local_path": "/tmp/a.wav"}) == "/tmp/a.wav"

    def test_item_without_preview_is_skipped(self, env) -> None:
        assert fc.download_preview({"id": 1}, dest_dir=str(env)) is None

    def test_mp3_is_downloaded_and_manifest_written(self, env) -> None:
        get = _Get(_Response(chunks=(b"ID3", b"data")))
        fc.requests = type("R", (), {"get": staticmethod(get)})  # type: ignore[assignment]

        path = fc.download_preview(
            {"id": 7, "name": "kick", "license": "CC0", "author": "demo",
             "preview_mp3": "https://cdn/x.mp3"},
            dest_dir=str(env),
            allow_online=True,
        )

        assert path is not None
        assert Path(path).exists() and Path(path).read_bytes() == b"ID3data"
        assert Path(path).suffix == ".mp3"
        manifest = json.loads(fc.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        assert manifest[0]["license"] == "CC0"
        assert manifest[0]["local_path"] == path
        assert manifest[0]["source"] == "freesound"

    def test_server_id_cannot_escape_cache_dir(self, env) -> None:
        # id приходит из ответа сервера: "../../x" раньше делал путь вне кэша
        # и open() падал, а ошибка уходила только в лог.
        fc.requests = type("R", (), {"get": staticmethod(_Get(_Response()))})  # type: ignore[assignment]

        path = fc.download_preview(
            {"id": "../../escaped", "preview_mp3": "https://cdn/x.mp3"},
            dest_dir=str(env / "cache"),
            allow_online=True,
        )

        assert path is not None
        assert Path(path).parent == env / "cache"
        assert not (env.parent / "escaped").exists() or (env.parent / "escaped").is_dir()

    def test_ogg_extension_follows_preview_kind(self, env) -> None:
        fc.requests = type("R", (), {"get": staticmethod(_Get(_Response()))})  # type: ignore[assignment]

        path = fc.download_preview(
            {"id": 1, "preview_ogg": "https://cdn/x.ogg"}, dest_dir=str(env), allow_online=True
        )

        assert path is not None and path.endswith(".ogg")

    def test_non_200_is_not_saved(self, env) -> None:
        fc.requests = type("R", (), {"get": staticmethod(_Get(_Response(status_code=404)))})

        path = fc.download_preview(
            {"id": 1, "preview_mp3": "https://cdn/x.mp3"}, dest_dir=str(env), allow_online=True
        )

        assert path is None
        assert list(env.glob("fs_*.mp3")) == []

    def test_download_exception_returns_none(self, env) -> None:
        fc.requests = type("R", (), {"get": staticmethod(_Get(error=OSError("timeout")))})

        assert fc.download_preview(
            {"id": 1, "preview_mp3": "https://cdn/x.mp3"}, dest_dir=str(env), allow_online=True
        ) is None


# --------------------------------------------------------------------------- #
#  Manifest
# --------------------------------------------------------------------------- #
class TestManifest:
    def test_entries_accumulate(self, env) -> None:
        fc._append_manifest({"id": 1, "name": "a"}, "/tmp/a.mp3")
        fc._append_manifest({"id": 2, "name": "b"}, "/tmp/b.mp3")

        manifest = json.loads(fc.DEFAULT_MANIFEST.read_text(encoding="utf-8"))

        assert [entry["id"] for entry in manifest] == [1, 2]

    def test_broken_manifest_is_backed_up_not_silently_lost(self, env) -> None:
        fc.DEFAULT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        fc.DEFAULT_MANIFEST.write_text("{битый json", encoding="utf-8")

        fc._append_manifest({"id": 9, "name": "n"}, "/tmp/n.mp3")

        broken = fc.DEFAULT_MANIFEST.with_suffix(".json.broken")
        assert broken.exists(), "испорченный manifest исчез без следа"
        assert "битый json" in broken.read_text(encoding="utf-8")
        manifest = json.loads(fc.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        assert [entry["id"] for entry in manifest] == [9]

    def test_manifest_that_is_not_a_list_is_replaced(self, env) -> None:
        fc.DEFAULT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        fc.DEFAULT_MANIFEST.write_text(json.dumps({"oops": True}), encoding="utf-8")

        fc._append_manifest({"id": 3, "name": "n"}, "/tmp/n.mp3")

        manifest = json.loads(fc.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        assert [entry["id"] for entry in manifest] == [3]

    def test_non_ascii_names_survive(self, env) -> None:
        fc._append_manifest({"id": 1, "name": "тёмный кит"}, "/tmp/a.mp3")

        text = fc.DEFAULT_MANIFEST.read_text(encoding="utf-8")

        assert "тёмный кит" in text


# --------------------------------------------------------------------------- #
#  Ключ и CLI
# --------------------------------------------------------------------------- #
class TestKeyAndCli:
    def test_env_key_wins_and_is_stripped(self, monkeypatch) -> None:
        monkeypatch.setenv("FREESOUND_API_KEY", "  abc  ")
        assert fc._load_key() == "abc"

    def test_key_file_is_used(self, tmp_path, monkeypatch) -> None:
        monkeypatch.delenv("FREESOUND_API_KEY", raising=False)
        monkeypatch.chdir(tmp_path)
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "freesound.key").write_text("from-file\n", encoding="utf-8")

        assert fc._load_key() == "from-file"

    def test_no_key_anywhere(self, tmp_path, monkeypatch) -> None:
        monkeypatch.delenv("FREESOUND_API_KEY", raising=False)
        monkeypatch.chdir(tmp_path)

        assert fc._load_key() is None

    def test_cli_prints_search_result(self, tmp_path, monkeypatch, capsys) -> None:
        import runpy

        monkeypatch.setattr("sys.argv", ["freesound_client.py", "kick"])
        runpy.run_module("modules.freesound_client", run_name="__main__")

        out = capsys.readouterr().out
        assert '"offline"' in out
