# -*- coding: utf-8 -*-
"""
agents/sample_hunter/license.py — лицензионный gate.

Пропускаются только CC0 / PD / CC-BY / royalty-free. Всё остальное, включая
`unknown`, блокируется. Если валидатор лицензий недоступен — онлайн-результаты
не выдаются вообще (fail closed).
"""

from __future__ import annotations


def _license_gate(items: list[dict], allow_user_override: bool = False) -> list[dict]:
    """Пропустить только CC0 / PD / CC-BY / RF. NC/SA/unknown — блокируются."""
    try:
        from app.core.license_manager import is_free_commercial
    except Exception:  # менеджер недоступен — не выдаём непроверенное
        return [item for item in items if item.get("source") == "local"]

    passed: list[dict] = []
    for item in items:
        if item.get("source") == "local":
            passed.append(item)
            continue
        license_name = str(item.get("license", "unknown"))
        if is_free_commercial(license_name, allow_user_override=allow_user_override):
            passed.append(item)
        else:
            item["license_blocked"] = True
            item["license_reason"] = f"blocked by license gate: {license_name}"
    return passed
