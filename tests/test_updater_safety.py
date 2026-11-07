"""T14: апдейтер не выпускает файлы за пределы цели и не теряет данные.

Две проблемы:
1. `zip.extractall()` доверял содержимому архива. Имена с `..` и абсолютные
   пути — классический zip-slip: запись попадает вне каталога установки.
2. `USER_PRESERVED` перечислял `secrets.enc` и `settings.json`, а реальный
   layout — `data/secrets.enc` и `data/settings.json`: ключи и настройки
   удалялись при обновлении.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from updater import install, userdata


def _make_zip(path: Path, entries: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in entries.items():
            archive.writestr(name, payload)
    return path


# ------------------------------------------------------------------ имя записи
@pytest.mark.parametrize(
    "name",
    [
        "../evil.txt",
        "../../evil.txt",
        "/abs/evil.txt",
        "sub/../../evil.txt",
        "C:/windows/evil.txt",
        "..\\evil.txt",
    ],
)
def test_unsafe_entry_names_are_rejected(name: str) -> None:
    assert install._is_safe_entry(name) is False, name


@pytest.mark.parametrize(
    "name",
    ["app/main.py", "data/genre_presets/phonk.json", "updater/install.py", "ZSMM.exe"],
)
def test_normal_entry_names_are_allowed(name: str) -> None:
    assert install._is_safe_entry(name) is True


# ------------------------------------------------------------------ распаковка
def test_safe_extract_blocks_traversal(tmp_path) -> None:
    archive = _make_zip(
        tmp_path / "evil.zip",
        {"../evil.txt": b"pwned", "app/ok.py": b"print(1)"},
    )
    target = tmp_path / "target"
    target.mkdir()

    result = install._safe_extract(archive, target)

    assert result["ok"] is False
    assert "evil.txt" in " ".join(result["rejected"])
    assert not (tmp_path / "evil.txt").exists(), "файл создан вне каталога установки"
    assert (target / "app" / "ok.py").read_bytes() == b"print(1)"


def test_safe_extract_blocks_absolute_paths(tmp_path) -> None:
    archive = tmp_path / "abs.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("/tmp/zsmm_absolute_evil.txt", b"x")
    target = tmp_path / "t"
    target.mkdir()

    result = install._safe_extract(archive, target)

    assert result["ok"] is False


def test_safe_extract_allows_normal_archive(tmp_path) -> None:
    archive = _make_zip(tmp_path / "good.zip", {"app/main.py": b"x", "data/a.json": b"{}"})
    target = tmp_path / "t"

    result = install._safe_extract(archive, target)

    assert result["ok"] is True
    assert result["rejected"] == []
    assert (target / "data" / "a.json").read_bytes() == b"{}"


# ------------------------------------------------------------------ USER_PRESERVED
def test_secrets_and_settings_live_under_data() -> None:
    assert "data/secrets.enc" in userdata.USER_PRESERVED
    assert "data/settings.json" in userdata.USER_PRESERVED


def test_legacy_names_are_kept_for_migration() -> None:
    """Старые имена остаются: у кого-то файл лежит в корне установки."""
    assert "secrets.enc" in userdata.USER_PRESERVED
    assert "settings.json" in userdata.USER_PRESERVED


def test_stash_and_restore_keep_nested_secrets(tmp_path) -> None:
    prog = tmp_path / "prog"
    staging = tmp_path / "staging"
    (prog / "data").mkdir(parents=True)
    (prog / "data" / "secrets.enc").write_bytes(b"KEY")
    staging.mkdir()

    moved = userdata._stash_user_data(prog, staging)
    assert not (prog / "data" / "secrets.enc").exists()

    (prog / "data").mkdir(parents=True, exist_ok=True)
    (prog / "data" / "defaults.json").write_text("{}", encoding="utf-8")
    restored = userdata._restore_user_data(prog, moved)

    assert "data/secrets.enc" in restored
    assert (prog / "data" / "secrets.enc").read_bytes() == b"KEY"
    assert (prog / "data" / "defaults.json").exists(), "новые дефолты не должны теряться"


# --------------------------------------------------- откат: та же защита, что и установка
def test_rollback_does_not_use_raw_extractall() -> None:
    """T14 закрыл установку, но `rollback_last` продолжал звать `extractall`.

    Откат запускается по тому же принципу «архив из папки бэкапов», и если
    туда попал подменённый файл, путь `../` уводил запись за пределы установки.
    """
    source = Path(install.__file__).read_text(encoding="utf-8")

    assert "extractall" not in source.replace(
        "`zipfile.extractall()`", ""
    ).replace("extractall() сам по себе", ""), "raw extractall вернулся в updater/install.py"


def test_rollback_refuses_unsafe_backup_archive(tmp_path, monkeypatch) -> None:
    program = tmp_path / "program"
    program.mkdir()
    (program / "main.py").write_text("print('old')\n", encoding="utf-8")
    backups = tmp_path / "backups"
    backups.mkdir()
    evil = _make_zip(
        backups / "backup_20260101_120000_pre_update.zip",
        {"../escaped.txt": b"pwned", "main.py": b"print('new')\n"},
    )
    monkeypatch.setenv("ZSMM_PROGRAM_DIR", str(program))
    monkeypatch.setenv("ZSMM_BACKUP_DIR", str(backups))

    result = install.rollback_last()

    assert result["ok"] is False
    assert "unsafe" in json.dumps(result).lower() or "rejected" in json.dumps(result).lower()
    assert not (tmp_path / "escaped.txt").exists(), "файл записан вне каталога установки"
    assert (program / "main.py").read_text(encoding="utf-8") == "print('old')\n"


def test_rollback_restores_safe_archive(tmp_path, monkeypatch) -> None:
    program = tmp_path / "program"
    program.mkdir()
    (program / "main.py").write_text("print('current')\n", encoding="utf-8")
    backups = tmp_path / "backups"
    backups.mkdir()
    _make_zip(
        backups / "backup_20260101_120000_pre_update.zip",
        {"main.py": b"print('restored')\n", "version.json": b'{"version": "0.9.0"}'},
    )
    monkeypatch.setenv("ZSMM_PROGRAM_DIR", str(program))
    monkeypatch.setenv("ZSMM_BACKUP_DIR", str(backups))

    result = install.rollback_last()

    assert result["ok"] is True, result
    assert (program / "main.py").read_text(encoding="utf-8") == "print('restored')\n"
