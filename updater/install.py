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
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

from updater.archive import make_backup, verify_zip
from updater.paths import backup_dir, program_dir, staging_dir
from updater import userdata
from updater.userdata import USER_PRESERVED, _stash_user_data


def _is_safe_entry(name: str) -> bool:
    """Имя записи архива не выводит за пределы каталога установки.

    Отклоняются абсолютные пути (`/abs/x`, `C:/windows/x`), подъём по `..`,
    пустые имена и любые буквы диска. Проверка не зависит от ОС: архив может
    быть собран на другой платформе.
    """
    raw = str(name or "").replace("\\", "/")
    if not raw or raw.endswith("/"):
        return not raw
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        return False
    return ".." not in raw.split("/")


def _safe_extract(zip_path: Path, target: Path) -> dict[str, Any]:
    """Распаковать архив, отказавшись от небезопасных записей.

    `zipfile.extractall()` сам по себе нормализует имена, но молча пропускает
    опасные записи — установка «проходит», а часть файлов просто не появляется.
    Здесь такие записи сначала отсеиваются, а результат сообщается вызывающей
    стороне: обновление с `../` в архиве считается неудачным, а не частичным.
    """
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    rejected: list[str] = []
    extracted = 0
    with zipfile.ZipFile(str(zip_path), "r") as archive:
        for info in archive.infolist():
            name = info.filename
            if info.is_dir():
                if _is_safe_entry(name + "x"):  # каталог безопасен, если безопасен путь внутри
                    (target / name).mkdir(parents=True, exist_ok=True)
                continue
            if not _is_safe_entry(name):
                rejected.append(name)
                continue
            destination = (target / name).resolve()
            try:
                destination.relative_to(target.resolve())
            except ValueError:
                rejected.append(name)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as source, open(destination, "wb") as sink:
                shutil.copyfileobj(source, sink)
            extracted += 1
    return {
        "ok": not rejected,
        "extracted": extracted,
        "rejected": rejected,
        "reason": ("unsafe archive entries: " + ", ".join(rejected)) if rejected else "",
    }


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
        extraction = _safe_extract(zip_p, stg)
    except Exception as e:
        return {"ok": False, "stage": "extract", "error": str(e), "backup": str(bak)}
    if not extraction["ok"]:
        # Небезопасный архив отвергается целиком: ничего не заменяем.
        return {
            "ok": False,
            "stage": "extract",
            "error": extraction["reason"],
            "rejected": extraction["rejected"],
            "backup": str(bak),
        }

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
        report = userdata.restore_user_data_report(prog, moved)
        restored = report["restored"]
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


def _rejected_entries(zip_path: Path) -> list[str]:
    """Небезопасные имена записей архива (проверка без распаковки)."""
    with zipfile.ZipFile(str(zip_path), "r") as archive:
        return [name for name in archive.namelist() if not _is_safe_entry(name)]


def _stash_before_rollback(prog: Path) -> tuple[Path, dict[str, Path]]:
    """Убрать пользовательские данные из установки перед заменой файлов."""
    stash_root = prog / ".rollback_stash"
    if stash_root.exists():
        shutil.rmtree(stash_root, ignore_errors=True)
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
        except Exception as exc:  # noqa: BLE001 - причина уходит в отказ
            failures.append(f"{rel}: {type(exc).__name__}: {exc}")
    if failures:
        # Продолжать нельзя: следующий шаг удаляет каталоги установки, и
        # невынесенные данные исчезнут вместе с ними.
        raise RuntimeError("user data preservation failed: " + "; ".join(failures))
    return stash_root, moved


def _clear_install_dir(prog: Path) -> None:
    """Удалить файлы установки, оставив сам апдейтер и стэш данных."""
    for item in prog.iterdir():
        if item.name in ("updater", ".rollback_stash"):
            continue
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            item.unlink()


def rollback_last() -> dict[str, Any]:
    """Откат на последний бэкап — с той же проверкой путей, что и установка.

    Порядок важен: сначала проверяется архив, и только потом что-либо меняется
    на диске. Раньше файлы установки удалялись ДО распаковки, поэтому
    подменённый бэкап оставлял пользователя без программы.
    """
    bd = backup_dir()
    backups = sorted(
        bd.glob("backup_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not backups:
        return {"ok": False, "error": "no backups"}
    last = backups[0]
    prog = program_dir()

    try:
        rejected = _rejected_entries(last)
    except Exception as exc:  # noqa: BLE001 - битый архив важнее стека
        return {
            "ok": False,
            "stage": "verify",
            "error": f"backup archive unreadable: {type(exc).__name__}: {exc}",
            "restored_from": str(last),
        }
    if rejected:
        return {
            "ok": False,
            "stage": "verify",
            "error": "unsafe entries in backup archive; nothing was changed",
            "rejected": rejected,
            "restored_from": str(last),
        }

    stash_root: Path | None = None
    try:
        stash_root, moved = _stash_before_rollback(prog)
        _clear_install_dir(prog)
        extraction = _safe_extract(last, prog)
        if not extraction.get("ok"):
            return {
                "ok": False,
                "stage": "extract",
                "error": extraction.get("reason", "extraction failed"),
                "rejected": extraction.get("rejected", []),
                "restored_from": str(last),
            }
        report = userdata.restore_user_data_report(prog, moved)
        shutil.rmtree(stash_root, ignore_errors=True)
        return {
            "ok": report["ok"],
            "restored_from": str(last),
            "user_data_preserved": report["restored"],
            "user_data_failed": report["failed"],
        }
    except Exception as e:  # noqa: BLE001 - отчёт важнее стека
        return {"ok": False, "error": str(e), "restored_from": str(last)}
