# -*- coding: utf-8 -*-
"""app/core/net_policy.py — единственная политика сетевого доступа.

Правило проекта: сеть выключена по умолчанию. До этой доработки три модуля
(`modules/freesound_client.py`, `updater/paths.py`, `agents/sample_hunter`)
решали это независимо и по-разному, а поиск сэмплов открывался в GUI заранее
включённой галочкой — то есть «выключено по умолчанию» не выполнялось.

Разрешение задаётся явным флагом вызова (`allow_online=True`) или настройкой
пользователя `{"network": {"online": true}}`. Строка `"true"`, число `1` и
прочие «почти истинные» значения не считаются согласием: это должна быть
буквально `True`.
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_SETTINGS = Path("data/settings.json")


def network_allowed(
    allow_online: bool = False,
    settings_path: "str | Path | None" = None,
) -> bool:
    """Разрешён ли удалённый запрос прямо сейчас."""
    if allow_online is True:
        return True
    path = Path(settings_path) if settings_path else DEFAULT_SETTINGS
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return False
    if not isinstance(settings, dict):
        return False
    network = settings.get("network")
    if not isinstance(network, dict):
        return False
    return network.get("online") is True


def offline_reason(allow_online: bool = False, settings_path=None) -> str:
    """Готовая причина отказа — чтобы отчёты не придумывали текст заново."""
    if network_allowed(allow_online, settings_path):
        return ""
    return "remote access requires explicit opt-in (allow_online=True or network.online=true)"
