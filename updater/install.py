# -*- coding: utf-8 -*-
"""
updater/install.py — установка обновления из ZIP и откат к предыдущей версии.

Контракт: любая ошибка на любой стадии возвращает `{ok: False, stage: ...}`;
после частично применённого обновления обязателен откат из бэкапа.
Пользовательские данные (`USER_PRESERVED`) стэшатся до очистки каталога и
возвращаются поверх новой версии с merge-семантикой.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

from updater.archive import make_backup, verify_zip
from updater.paths import backup_dir, program_dir, staging_dir
from updater.userdata import USER_PRESERVED, _restore_user_data, _stash_user_data


def install_from_zip(
    zip_path: str, expected_sha256: str | None = None, smoke_test: bool = True
) -> dict[str, Any]:
    zip_p = Path(zip_path)
    prog = program_dir()

    v = verify_zip(zip_p, expected_sha256)
    if not v.get("ok"):
        return {
            "ok": False,
            "stage": "verify",
            "error": v.get("reason", "verification failed"),
            "verify": v,
        }

    bak = make_backup(reason="pre_install")
    if bak is None:
        return {"ok": False, "stage": "backup", "error": "backup failed"}

    stg = staging_dir()
    if stg.exists():
        shutil.rmtree(stg)
    stg.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(str(zip_p), "r") as z:
            z.extractall(str(stg))
    except Exception as e:
        return {"ok": False, "stage": "extract", "error": str(e), "backup": str(bak)}

    try:
        # v37 FIX: сохраняем пользовательские данные ДО очистки каталога.
        moved = _stash_user_data(prog, stg)
        for item in prog.iterdir():
            if item.name == "updater":
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink()
        for item in stg.iterdir():
            if item.name == ".user_stash":  # это наши же сохранённые данные, не копируем как часть дистрибутива
                continue
            dst = prog / item.name
            if item.is_dir():
                shutil.copytree(str(item), str(dst))
            else:
                shutil.copy2(str(item), str(dst))
        # v37 FIX: возвращаем пользовательские данные поверх новой версии.
        restored = _restore_user_data(prog, moved)
        if restored:
            print(f"[updater] пользовательские данные сохранены: {', '.join(restored)}")
    except Exception as e:
        rb = rollback_last()
        return {
            "ok": False,
            "stage": "replace",
            "error": str(e),
            "rolled_back": rb.get("ok", False),
            "backup": str(bak),
        }

    if smoke_test:
        try:
            r = subprocess.run(
                [sys.executable, str(prog / "main.py"), "--smoke"],
                capture_output=True,
                timeout=180,
            )
            if r.returncode != 0:
                rb = rollback_last()
                return {
                    "ok": False,
                    "stage": "smoke_test",
                    "error": f"smoke failed rc={r.returncode}",
                    "rolled_back": rb.get("ok", False),
                    "backup": str(bak),
                }
        except subprocess.TimeoutExpired:
            rb = rollback_last()
            return {
                "ok": False,
                "stage": "smoke_test",
                "error": "smoke timeout",
                "rolled_back": rb.get("ok", False),
                "backup": str(bak),
            }
        except Exception as exc:
            rb = rollback_last()
            return {
                "ok": False,
                "stage": "smoke_test",
                "error": f"smoke launch failed: {type(exc).__name__}: {exc}",
                "rolled_back": rb.get("ok", False),
                "backup": str(bak),
            }

    ver_p = prog / "version.json"
    ver = "unknown"
    try:
        if ver_p.exists():
            ver = json.loads(ver_p.read_text(encoding="utf-8")).get(
                "version", "unknown"
            )
    except Exception:
        pass
    return {"ok": True, "version": ver, "backup": str(bak)}


def rollback_last() -> dict[str, Any]:
    bd = backup_dir()
    backups = sorted(
        bd.glob("backup_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not backups:
        return {"ok": False, "error": "no backups"}
    last = backups[0]
    prog = program_dir()
    try:
        # v37 FIX: rollback тоже не должен затирать пользовательские данные.
        # Стэшим во временный каталог РЯДОМ с prog (не в backup_dir — туда rollback не смотрит).
        stash_root = prog / ".rollback_stash"
        if stash_root.exists():
            shutil.rmtree(stash_root, ignore_errors=True)
        moved: dict[str, Path] = {}
        for rel in USER_PRESERVED:
            src = prog / rel
            if not src.exists():
                continue
            dst = stash_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(src), str(dst))
                moved[rel] = dst
            except Exception:
                pass
        for item in prog.iterdir():
            if item.name in ("updater", ".rollback_stash"):
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink()
        with zipfile.ZipFile(str(last), "r") as z:
            z.extractall(str(prog))
        restored = _restore_user_data(prog, moved)
        shutil.rmtree(stash_root, ignore_errors=True)
        return {"ok": True, "restored_from": str(last), "user_data_preserved": restored}
    except Exception as e:
        return {"ok": False, "error": str(e)}
