# -*- coding: utf-8 -*-
"""
updater/userdata.py — неприкосновенные данные пользователя.

Здесь живёт список `USER_PRESERVED`, стэширование/возврат пользовательских
каталогов при установке и откате, создание дерева каталогов данных и миграция
настроек. Ни один из этих путей не должен теряться при обновлении.
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from updater.paths import user_data_dir


# удалял всё подряд. Плюс 'presets'/'prompts' в реальном layout репо лежат в
# data/genre_presets и data/prompts — старые имена сохранить было невозможно.
USER_PRESERVED = [
    "projects",
    "voice_vault",
    "lyric_vault",
    "data/genre_presets",
    "data/prompts",
    "data/tutorial_settings.json",
    # реальный layout: ключи и настройки лежат внутри data/
    "data/secrets.enc",
    "data/settings.json",
    # старые имена оставлены для миграции: у части установок файлы в корне
    "secrets.enc",
    "settings.json",
    "output",
    "cache",
    "logs",
]


def _stash_user_data(prog: Path, stg: Path) -> dict[str, Path]:
    """Перед заменой: переносим USER_PRESERVED из prog в staging-зону.

    v37: раньше USER_PRESERVED игнорировался — install просто делал rmtree
    всего каталога и пользователь терял voice_vault/lyric_vault/output.
    Возвращает мапу rel_path -> stash_path, чтобы _restore_user_data вернул всё назад.
    """
    stash_root = stg / ".user_stash"
    moved: dict[str, Path] = {}
    failures: list[str] = []
    for rel in USER_PRESERVED:
        src = prog / rel
        if not src.exists():
            continue
        dst = stash_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dst))
            moved[rel] = dst
        except Exception as exc:
            # Continuing would let the replacement loop delete a user path that
            # was never safely moved.  The caller rolls back from its preinstall
            # backup instead of reporting a successful update with data loss.
            failures.append(f"{rel}: {type(exc).__name__}: {exc}")
    if failures:
        raise RuntimeError("user data preservation failed: " + "; ".join(failures))
    return moved


def _restore_user_data(prog: Path, moved: dict[str, Path]) -> list[str]:
    """Вернуть сохранённые данные поверх новой версии (merge, не затирание)."""
    """После распаковки новой версии: возвращаем сохранённые данные на место.

    v37: MERGE-семантика вместо затирания. Если новая версия принесла свой
    каталог (например свежие дефолтные пресеты в data/genre_presets) — юзерские
    файлы накладываются ПОВЕРХ, а новые дефолтные СОХРАНЯЮТСЯ. Так не теряются
    ни пользовательские данные, ни обновлённые пресеты из дистрибутива.
    Возвращает список rel-путей, которые удалось восстановить.
    """
    restored: list[str] = []
    for rel, stash in moved.items():
        dst = prog / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            if stash.is_dir():
                # merge: копируем юзерское содержимое поверх нового каталога
                # (dirs_exist_ok=True — не удаляем новые дефолтные файлы)
                shutil.copytree(str(stash), str(dst), dirs_exist_ok=True)
                shutil.rmtree(str(stash), ignore_errors=True)
            else:
                # файл: юзерский приоритетнее нового дефолтного
                if dst.exists():
                    dst.unlink()
                shutil.move(str(stash), str(dst))
            restored.append(rel)
        except Exception:
            pass
    return restored


def ensure_user_dirs() -> None:
    root = user_data_dir()
    root.mkdir(parents=True, exist_ok=True)
    for sub in (
        "projects",
        "voice_vault",
        "lyric_vault",
        "presets",
        "prompts",
        "output",
        "cache",
        "logs",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)


def migrate_settings(old_path: Path, new_path: Path) -> dict[str, Any]:
    conflicts = []
    try:
        old = (
            json.loads(old_path.read_text(encoding="utf-8"))
            if old_path.exists()
            else {}
        )
    except Exception as e:
        old = {}
        conflicts.append(f"read old: {e}")
    merged = dict(old)
    try:
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        conflicts.append(f"write new: {e}")
    log_p = user_data_dir() / "logs" / "migration_conflicts.log"
    if conflicts:
        log_p.parent.mkdir(parents=True, exist_ok=True)
        with open(log_p, "a", encoding="utf-8") as f:
            f.write(f"=== migration @ {time.ctime()} ===\n")
            f.writelines(c + "\n" for c in conflicts)
    return {"ok": len(conflicts) == 0, "conflicts": conflicts}
