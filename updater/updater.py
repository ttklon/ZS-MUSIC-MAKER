r"""
ZS Music Maker v14 — updater/updater.py (P0.10..P0.13, TZ 31)
==============================================================

  P0.10 — разделение program vs user data.
  P0.11 — автообновление из ZIP.
  P0.12 — резервное копирование перед обновлением (последние 3).
  P0.13 — автоматический откат при сбое.

Реализовано:
  install_from_zip(zip_path)   — установка новой версии из ZIP;
  rollback_last()              — откат к предыдущей версии;
  check_updates(url)           — проверка новой версии;
  verify_zip(path, sha256)     — проверка SHA-256;
  user_data_dir()              — путь к %LOCALAPPDATA%\ZS Music Maker;
  program_dir()                — путь установки программы.

Пользовательские данные (voice_vault, lyric_vault, projects, settings.json,
secrets.enc, presets, prompts, output, cache, logs) НЕ ТРОГАЕМ при обновлении.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any


def program_dir() -> Path:
    env = os.environ.get("ZSMM_PROGRAM_DIR")
    if env:
        return Path(env)
    # v37 FIX: раньше на win32 всегда возвращался 'C:\Program Files\ZS Music Maker',
    # хотя репо ставится клонированием в ЛЮБУЮ папку. Это приводило к тому, что
    # backup/rollback/install работали с несуществующим каталогом.
    # Теперь: если текущий корень проекта (рядом с updater/) выглядит как установка
    # (есть main.py) — используем ЕГО; 'Program Files' остаётся только для случая,
    # когда updater вызван не из дерева проекта.
    root = Path(__file__).resolve().parents[1]
    if (root / "main.py").exists():
        return root
    if sys.platform == "win32":
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        return Path(pf) / "ZS Music Maker"
    return root


def user_data_dir() -> Path:
    env = os.environ.get("ZSMM_USER_DIR")
    if env:
        return Path(env)
    if sys.platform == "win32":
        appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))
        return Path(appdata) / "ZS Music Maker"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ZS Music Maker"
    xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(xdg) / "zsmm"


def backup_dir() -> Path:
    d = program_dir() / "updater" / "backup"
    d.mkdir(parents=True, exist_ok=True)
    return d


def staging_dir() -> Path:
    d = program_dir() / "updater" / "backup" / "staging"
    d.mkdir(parents=True, exist_ok=True)
    return d


def online_enabled(allow_online: bool = False, settings_path: Path | None = None) -> bool:
    """Allow remote updater traffic only after an explicit user opt-in."""
    if allow_online:
        return True
    path = Path(settings_path) if settings_path else program_dir() / "data" / "settings.json"
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return False
    network = settings.get("network", {}) if isinstance(settings, dict) else {}
    return isinstance(network, dict) and network.get("online") is True


# Каталоги/файлы ПОЛЬЗОВАТЕЛЯ, которые НЕЛЬЗЯ затирать при обновлении из ZIP.
# v37 FIX: раньше список только объявлялся, но НИГДЕ не применялся — install
# удалял всё подряд. Плюс 'presets'/'prompts' в реальном layout репо лежат в
# data/genre_presets и data/prompts — старые имена сохранить было невозможно.
USER_PRESERVED = [
    "projects",
    "voice_vault",
    "lyric_vault",
    "data/genre_presets",
    "data/prompts",
    "data/tutorial_settings.json",
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


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_zip(zip_path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "sha256": None, "size": 0, "checks": {}}
    p = Path(zip_path)
    if not p.exists():
        result["reason"] = "zip not found"
        return result
    result["size"] = p.stat().st_size
    if result["size"] < 1024:
        result["reason"] = "zip too small (<1KB)"
        return result
    if result["size"] > 5 * 1024**3:
        result["reason"] = "zip too large (>5GB)"
        return result
    sha = compute_sha256(p)
    result["sha256"] = sha
    result["checks"]["sha256_computed"] = True
    if expected_sha256:
        if sha.lower() != expected_sha256.lower():
            result["reason"] = "sha256 mismatch"
            return result
        result["checks"]["sha256_match"] = True

    try:
        with zipfile.ZipFile(str(p), "r") as z:
            names = set(z.namelist())
    except zipfile.BadZipFile:
        result["reason"] = "corrupted zip"
        return result

    # v37 FIX: раньше verify требовал TZ.txt/PROMPT.txt — этих файлов НЕТ
    # в репозитории, поэтому updater отвергал ЛЮБОЙ реальный дистрибутив.
    # Проверяем реальные маркеры проекта: main.py, version.json, modules/.
    has_main = any(n.endswith("main.py") and not n.startswith("docs/") for n in names)
    has_version = any(n.endswith("version.json") for n in names)
    has_modules = any(n.startswith("modules/") and n.endswith(".py") for n in names)
    result["checks"]["has_main_py"] = has_main
    result["checks"]["has_version_json"] = has_version
    result["checks"]["has_modules"] = has_modules
    if not (has_main and has_version and has_modules):
        result["reason"] = "zip missing required files: main.py/version.json/modules/"
        return result

    result["ok"] = True
    return result


def make_backup(reason: str = "pre_update") -> Path | None:
    src = program_dir()
    if not src.exists():
        return None
    ts = time.strftime("%Y%m%d_%H%M%S")
    dst = backup_dir() / f"backup_{ts}_{reason}.zip"
    with zipfile.ZipFile(str(dst), "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(src):
            if "updater/backup" in root.replace("\\", "/"):
                continue
            if "__pycache__" in root:
                continue
            for f in files:
                fp = Path(root) / f
                try:
                    z.write(str(fp), fp.relative_to(src))
                except Exception:
                    pass
    prune_old_backups(keep=3)
    return dst


def prune_old_backups(keep: int = 3) -> list[Path]:
    bd = backup_dir()
    backups = sorted(
        bd.glob("backup_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    removed = []
    for old in backups[keep:]:
        try:
            old.unlink()
            removed.append(old)
        except Exception:
            pass
    return removed


def list_backups() -> list[dict[str, Any]]:
    bd = backup_dir()
    return [
        {"path": str(p), "size": p.stat().st_size, "mtime": p.stat().st_mtime}
        for p in sorted(
            bd.glob("backup_*.zip"), key=lambda x: x.stat().st_mtime, reverse=True
        )
    ]


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


def check_git_update_status(
    repo: Path | None = None, allow_online: bool = False
) -> dict[str, Any]:
    """Проверить remote revision without changing the working tree.

    ``git ls-remote`` is a network call, so it is skipped until ``--online``
    or ``network.online=true`` in settings explicitly permits it.
    """
    repo = Path(repo or program_dir())
    if not online_enabled(allow_online):
        return {
            "ok": True,
            "offline": True,
            "reason": "remote update check requires --online or network.online=true",
            "apply_performed": False,
        }
    try:
        def git(*args: str) -> str:
            return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
        branch = git("branch", "--show-current") or "main"
        local = git("rev-parse", "HEAD")
        dirty = bool(git("status", "--porcelain"))
        remote_line = git("ls-remote", "origin", f"refs/heads/{branch}")
        remote = remote_line.split()[0] if remote_line else None
        relation = "unknown" if not remote else ("up_to_date" if remote == local else "update_available")
        return {"ok": True, "branch": branch, "local": local, "remote": remote,
                "relation": relation, "working_tree_clean": not dirty,
                "apply_performed": False}
    except Exception as exc:
        return {"ok": False, "reason": str(exc), "apply_performed": False}


def check_updates(release_url: str, allow_online: bool = False) -> dict[str, Any]:
    if not online_enabled(allow_online):
        return {
            "ok": True,
            "offline": True,
            "reason": "release check requires --online or network.online=true",
        }
    try:
        import urllib.request as urlreq

        with urlreq.urlopen(release_url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "reason": str(e)}
    return {"ok": True, "data": data}


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
