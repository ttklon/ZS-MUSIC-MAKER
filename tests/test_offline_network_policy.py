from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from modules import freesound_client
from updater import updater


class _NoNetwork:
    def get(self, *args, **kwargs):  # pragma: no cover - assertion is the test
        raise AssertionError("unexpected remote request")


def test_freesound_default_is_offline_even_when_credentials_are_available(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(freesound_client, "requests", _NoNetwork())
    monkeypatch.setattr(freesound_client, "_load_key", lambda: "test-key")

    result = freesound_client.search("kick")

    assert result["offline"] is True
    assert result["results"] == []
    assert freesound_client.download_preview({"preview_mp3": "https://example.invalid/a.mp3"}) is None


def test_freesound_explicit_online_and_persisted_setting_are_supported(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    calls: list[str] = []

    def fake_get(url: str, **_kwargs):
        calls.append(url)
        return SimpleNamespace(
            status_code=200,
            json=lambda: {"results": [{"id": 1, "name": "kick", "previews": {}}]},
        )

    monkeypatch.setattr(freesound_client, "requests", SimpleNamespace(get=fake_get))
    monkeypatch.setattr(freesound_client, "_load_key", lambda: "test-key")

    explicit = freesound_client.search("kick", allow_online=True)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "settings.json").write_text(
        json.dumps({"network": {"online": True}}), encoding="utf-8"
    )
    persisted = freesound_client.search("snare")

    assert explicit["offline"] is False and persisted["offline"] is False
    assert len(calls) == 2


def test_updater_network_checks_are_noop_offline_and_opt_in_when_requested(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_output(command, text=True):
        args = tuple(command[3:])
        calls.append(args)
        return {
            ("branch", "--show-current"): "main\n",
            ("rev-parse", "HEAD"): "abc123\n",
            ("status", "--porcelain"): "",
            ("ls-remote", "origin", "refs/heads/main"): "abc123\trefs/heads/main\n",
        }[args]

    monkeypatch.setattr(subprocess, "check_output", fake_output)
    offline = updater.check_git_update_status(tmp_path)
    release = updater.check_updates("https://example.invalid/release.json")
    online = updater.check_git_update_status(tmp_path, allow_online=True)

    assert offline == {
        "ok": True,
        "offline": True,
        "reason": "remote update check requires --online or network.online=true",
        "apply_performed": False,
    }
    assert release["offline"] is True
    assert online["relation"] == "up_to_date"
    assert calls[-1] == ("ls-remote", "origin", "refs/heads/main")


def test_network_settings_require_exact_true(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text('{"network": {"online": "yes"}}', encoding="utf-8")
    assert freesound_client.online_enabled(settings_path=settings) is False
    assert updater.online_enabled(settings_path=settings) is False

    settings.write_text('{"network": {"online": true}}', encoding="utf-8")
    assert freesound_client.online_enabled(settings_path=settings) is True
    assert updater.online_enabled(settings_path=settings) is True


# --------------------------------------------------------------- единая политика
def test_net_policy_is_the_single_source_of_truth(tmp_path: Path) -> None:
    """Все три потребителя делегируют в один хелпер и согласны между собой."""
    from agents.sample_hunter import hunter
    from app.core.net_policy import network_allowed

    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"network": {"online": True}}), encoding="utf-8")

    assert network_allowed(False, settings) is True
    assert freesound_client.online_enabled(settings_path=settings) is True
    assert updater.online_enabled(settings_path=settings) is True
    assert network_allowed in (hunter.network_allowed,)


def test_hunt_is_offline_by_default_and_does_not_touch_network(monkeypatch, tmp_path) -> None:
    from agents.sample_hunter import hunter, web

    monkeypatch.chdir(tmp_path)  # нет data/settings.json → нет согласия
    called: list[str] = []

    def forbidden(url, timeout: float = 6.0):
        called.append(url)
        raise AssertionError("сеть вызвана без явного согласия")

    monkeypatch.setattr(web, "_http_get", forbidden)
    monkeypatch.setattr(hunter, "list_local", lambda *a, **k: [])

    result = hunter.hunt("kick")

    assert result["offline"] is True
    assert result["online"] == []
    assert called == []


def test_hunt_goes_online_when_explicitly_allowed(monkeypatch, tmp_path) -> None:
    from agents.sample_hunter import hunter, web

    monkeypatch.chdir(tmp_path)
    called: list[str] = []

    def fake_get(url, timeout: float = 6.0):
        called.append(url)
        return None

    monkeypatch.setattr(web, "_http_get", fake_get)
    monkeypatch.setattr(web, "HAS_REQ", True)
    monkeypatch.setattr(hunter, "list_local", lambda *a, **k: [])

    result = hunter.hunt("kick", allow_online=True)

    assert result["offline"] is False
    assert called, "онлайн-поиск разрешён, но сеть не использована"


def test_string_true_in_settings_does_not_enable_network(tmp_path: Path) -> None:
    from app.core.net_policy import network_allowed

    settings = tmp_path / "settings.json"
    for payload in ('{"network": {"online": "true"}}', '{"network": {"online": 1}}', '{"online": true}'):
        settings.write_text(payload, encoding="utf-8")
        assert network_allowed(settings_path=settings) is False, payload
