# -*- coding: utf-8 -*-
"""
updater/updater.py — публичный фасад движка обновлений.

Исторически вся логика лежала в этом одном модуле; теперь она разложена по
ответственностям, а здесь остаются только ре-экспорты — чтобы
`from updater.updater import install_from_zip` продолжал работать:

  * `paths`    — каталоги программы/данных, opt-in сетевых проверок;
  * `userdata` — неприкосновенные данные пользователя и их миграция;
  * `archive`  — проверка ZIP и ротация резервных копий;
  * `install`  — установка из ZIP и откат;
  * `checks`   — проверка доступных обновлений;
  * `cli`      — `python -m updater`.

Обновление из ZIP: verify → backup → extract → stash → replace → restore →
smoke → версия. Любая ошибка после замены файлов завершается откатом.
"""

from __future__ import annotations

from updater.archive import (  # noqa: F401
    compute_sha256,
    list_backups,
    make_backup,
    prune_old_backups,
    verify_zip,
)
from updater.checks import check_git_update_status, check_updates  # noqa: F401
from updater.cli import main  # noqa: F401
from updater.install import install_from_zip, rollback_last  # noqa: F401
from updater.paths import (  # noqa: F401
    backup_dir,
    online_enabled,
    program_dir,
    staging_dir,
    user_data_dir,
)
from updater.userdata import (  # noqa: F401
    USER_PRESERVED,
    _restore_user_data,
    _stash_user_data,
    ensure_user_dirs,
    migrate_settings,
)

if __name__ == "__main__":
    raise SystemExit(main())
