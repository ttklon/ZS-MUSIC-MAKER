# -*- coding: utf-8 -*-
"""
updater/cli.py — `python -m updater` : установка, откат, проверка, инвентарь.
"""

from __future__ import annotations

import json

from updater.archive import list_backups
from updater.checks import check_git_update_status, check_updates
from updater.install import install_from_zip, rollback_last
from updater.paths import backup_dir, program_dir, user_data_dir
from updater.userdata import USER_PRESERVED


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser("zsmm-updater")
    ap.add_argument("--install", help="Установить из ZIP")
    ap.add_argument("--sha256", help="Ожидаемый SHA-256")
    ap.add_argument("--rollback", action="store_true")
    ap.add_argument("--list-backups", action="store_true")
    ap.add_argument("--check", help="URL проверки обновлений")
    ap.add_argument("--git-status", action="store_true", help="Проверить Git revision без обновления")
    ap.add_argument("--online", action="store_true", help="Разрешить сетевой запрос для --check/--git-status")
    ap.add_argument("--info", action="store_true")
    args = ap.parse_args()

    if args.info:
        print(
            json.dumps(
                {
                    "program_dir": str(program_dir()),
                    "user_data_dir": str(user_data_dir()),
                    "backup_dir": str(backup_dir()),
                    "user_preserved": USER_PRESERVED,
                },
                indent=2,
            )
        )
        return 0
    if args.install:
        r = install_from_zip(args.install, args.sha256, smoke_test=False)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0 if r.get("ok") else 1
    if args.rollback:
        r = rollback_last()
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0 if r.get("ok") else 1
    if args.list_backups:
        print(json.dumps(list_backups(), indent=2))
        return 0
    if args.git_status:
        result = check_git_update_status(allow_online=args.online)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1
    if args.check:
        print(json.dumps(check_updates(args.check, allow_online=args.online), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
