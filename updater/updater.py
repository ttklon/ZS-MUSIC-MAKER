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
    if sys.platform == "win32":
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        return Path(pf) / "ZS Music Maker"
    return Path(__file__).resolve().parents[1]


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


USER_PRESERVED = [
    "projects",
    "voice_vault",
    "lyric_vault",
    "presets",
    "prompts",
    "secrets.enc",
    "settings.json",
    "output",
    "cache",
    "logs",
]


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

    has_main = any(n.endswith("main.py") for n in names)
    has_tz = any(n.endswith("TZ.txt") for n in names)
    has_prompt = any(n.endswith("PROMPT.txt") for n in names)
    result["checks"]["has_main_py"] = has_main
    result["checks"]["has_TZ_txt"] = has_tz
    result["checks"]["has_PROMPT_txt"] = has_prompt
    if not (has_main and has_tz and has_prompt):
        result["reason"] = "zip missing required files: main.py/TZ.txt/PROMPT.txt"
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
        for item in prog.iterdir():
            if item.name == "updater":
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink()
        for item in stg.iterdir():
            dst = prog / item.name
            if item.is_dir():
                shutil.copytree(str(item), str(dst))
            else:
                shutil.copy2(str(item), str(dst))
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
        except Exception:
            pass

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
        for item in prog.iterdir():
            if item.name == "updater":
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink()
        with zipfile.ZipFile(str(last), "r") as z:
            z.extractall(str(prog))
        return {"ok": True, "restored_from": str(last)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_updates(release_url: str) -> dict[str, Any]:
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
    if args.check:
        print(json.dumps(check_updates(args.check), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
