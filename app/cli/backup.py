# -*- coding: utf-8 -*-
"""
app/cli/backup.py — preflight-снимок проекта перед тяжёлым запуском.

Бэкап защищает работу пользователя, но не имеет права молча сорвать
запрошенный рендер: при ошибке снимка печатается честное предупреждение и
процесс продолжается.
"""

from __future__ import annotations

from app.cli.env import safe_print


def preflight_backup(mode: str) -> dict:
    """Создать ограниченный по размеру восстановимый снимок перед запуском."""
    try:
        from app.core.auto_backup import create_snapshot

        report = create_snapshot(mode)
        safe_print(
            f"[backup] files={report['files']} bytes={report['total_bytes']} path={report['path']}"
        )
        return report
    except Exception as exc:
        safe_print(f"[backup] WARNING: preflight snapshot failed: {exc}")
        return {"ok": False, "reason": str(exc)}
