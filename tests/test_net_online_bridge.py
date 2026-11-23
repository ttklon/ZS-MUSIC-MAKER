# -*- coding: utf-8 -*-
"""Мост «галочка сети в окне → Python»: `ZSMM_ONLINE=1`.

Галочка `networkOnline` жила только в настройках Electron
(`userData/settings.json`), а пайплайн читает `data/settings.json` в каталоге
проекта. Значит, включить сеть из приложения было нельзя: `--rvc-setup`,
`--bootstrap --online` и облачные LLM всегда получали `network disabled`,
хотя пользователь явно согласился.

Теперь окно передаёт `ZSMM_ONLINE=1` в окружение запущенной задачи. Здесь
проверяется пограничное поведение: только литерал `1`, никакого «почти да», и
настройки по-прежнему работают.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core import net_policy


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("ZSMM_ONLINE", raising=False)
    return monkeypatch


def test_env_flag_grants_access_without_settings_file(tmp_path: Path) -> None:
    assert net_policy.network_allowed(settings_path=tmp_path / "missing.json") is False
    assert net_policy.network_allowed(allow_online=True) is True


def test_env_online_bridge(monkeypatch) -> None:
    monkeypatch.setenv("ZSMM_ONLINE", "1")

    assert net_policy.network_allowed() is True
    assert net_policy.offline_reason() == ""


@pytest.mark.parametrize("value", ["true", "yes", "on", "0", "01", " true", ""])
def test_env_flag_is_literal_one_only(monkeypatch, value: str) -> None:
    """`true`, `yes`, `on` — не согласие: политика не должна угадывать."""
    monkeypatch.setenv("ZSMM_ONLINE", value)

    assert net_policy.network_allowed() is False
    assert "ZSMM_ONLINE=1" in net_policy.offline_reason()


def test_settings_file_still_works(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"network": {"online": True}}), encoding="utf-8")

    assert net_policy.network_allowed(settings_path=path) is True


def test_offline_reason_names_every_way_to_opt_in() -> None:
    reason = net_policy.offline_reason()

    for token in ("allow_online=True", "network.online=true", "ZSMM_ONLINE=1"):
        assert token in reason, reason


def test_bootstrap_online_flag_goes_through_the_policy(monkeypatch) -> None:
    """`--bootstrap --online` не должен обходить политику: только еввар/настройка."""
    from app.core import bootstrap

    assert bootstrap._network_allowed() is False
    monkeypatch.setenv("ZSMM_ONLINE", "1")
    assert bootstrap._network_allowed() is True
