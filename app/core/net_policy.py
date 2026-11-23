# -*- coding: utf-8 -*-
"""app/core/net_policy.py — единственная политика сетевого доступа.

Правило проекта: сеть выключена по умолчанию. До этой доработки три модуля
(`modules/freesound_client.py`, `updater/paths.py`, `agents/sample_hunter`)
решали это независимо и по-разному, а поиск сэмплов открывался в GUI заранее
включённой галочкой — то есть «выключено по умолчанию» не выполнялось.

Разрешение задаётся явным флагом вызова (`allow_online=True`), настройкой
пользователя `{"network": {"online": true}}` или переменной окружения
`ZSMM_ONLINE=1`. Строка `"true"`, число `1` и прочие «почти истинные» значения
не считаются согласием: это должна быть буквально `True`.

Переменная окружения — мост из окна: галочка «сеть» живёт в настройках
Electron (`userData/settings.json`), а пайплайн читает `data/settings.json` в
каталоге проекта. Без моста пользователь включал сеть в приложении и получал
`network disabled` от `--rvc-setup` и `--bootstrap --online`. Переменная
действует ровно на запущенную задачу и не переписывает чужой конфиг.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_SETTINGS = Path("data/settings.json")


def network_allowed(
    allow_online: bool = False,
    settings_path: "str | Path | None" = None,
) -> bool:
    """Разрешён ли удалённый запрос прямо сейчас."""
    boundary = os.environ.get("ZSMM_ONLINE", "").strip()
    # An explicit desktop off-boundary cannot be resurrected by stale settings/flags.
    if boundary == "0":
        return False
    if allow_online is True:
        return True
    # Явное согласие окна: только литерал "1", как и у настроек — только `True`.
    if os.environ.get("ZSMM_ONLINE", "").strip() == "1":
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
    return (
        "remote access requires explicit opt-in "
        "(allow_online=True, network.online=true or ZSMM_ONLINE=1)"
    )
