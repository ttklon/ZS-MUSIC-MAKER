"""T23: покрытие `updater/` — целиком, включая откат и границы пакета.

`docs/IMPROVEMENT_PLAN.md` (T23) требует ≥ 60 % для `updater/`, где было 15 %:
проверка пакета, бэкапы, CLI и восстановление данных были «написанными, но
непроверенными». Здесь они проверяются на настоящих zip-файлах и настоящих
каталогах, без сети и без Windows.

Всё, что трогает файловую систему, работает во временном каталоге: тесты не
должны ни читать, ни портить реальную установку.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from updater import archive, cli, paths, userdata
from updater.checks import check_git_update_status, check_updates


def _package(path: Path, entries: dict[str, bytes] | None = None) -> Path:
    """Настоящий zip с маркерами проекта."""
    payload = entries if entries is not None else {
        "main.py": b"print('hi')\n",
        "version.json": b'{"version": "1.0.0"}\n',
        "modules/x.py": b"X = 1\n",
        # порог verify_zip — 1 KB: реальный дистрибутив всегда больше
        "modules/padding.py": b"# " + b"x" * 4096 + b"\n",
    }
    with zipfile.ZipFile(path, "w") as z:
        for name, data in payload.items():
            z.writestr(name, data)
    return path


# --------------------------------------------------------------------------- #
#  verify_zip: границы и честные причины отказа
# --------------------------------------------------------------------------- #

def test_verify_zip_accepts_real_package(tmp_path) -> None:
    package = _package(tmp_path / "pkg.zip")

    result = archive.verify_zip(package)

    assert result["ok"] is True
    assert result["size"] > 0
    assert len(result["sha256"]) == 64
    assert result["checks"]["has_main_py"] and result["checks"]["has_modules"]


def test_verify_zip_reports_missing_file(tmp_path) -> None:
    result = archive.verify_zip(tmp_path / "nope.zip")

    assert result["ok"] is False and "not found" in result["reason"]


def test_verify_zip_rejects_tiny_file(tmp_path) -> None:
    tiny = tmp_path / "tiny.zip"
    tiny.write_bytes(b"PK\x05\x06" + b"\0" * 10)

    result = archive.verify_zip(tiny)

    assert result["ok"] is False and "too small" in result["reason"]


def test_verify_zip_rejects_corrupted_archive(tmp_path) -> None:
    broken = tmp_path / "broken.zip"
    broken.write_bytes(b"not a zip" * 300)

    result = archive.verify_zip(broken)

    assert result["ok"] is False
    assert "corrupted" in result["reason"]


def test_verify_zip_checks_expected_sha256(tmp_path) -> None:
    package = _package(tmp_path / "pkg.zip")
    good = archive.compute_sha256(package)

    assert archive.verify_zip(package, good)["ok"] is True
    mismatch = archive.verify_zip(package, "0" * 64)
    assert mismatch["ok"] is False and mismatch["reason"] == "sha256 mismatch"


def test_verify_zip_rejects_package_without_project_markers(tmp_path) -> None:
    package = _package(tmp_path / "other.zip", {"readme.txt": b"hello" * 400})

    result = archive.verify_zip(package)

    assert result["ok"] is False
    assert "missing required files" in result["reason"]


# --------------------------------------------------------------------------- #
#  Бэкапы: создание, обрезка, список
# --------------------------------------------------------------------------- #

@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Изолированная «установка» и каталог бэкапов."""
    program = tmp_path / "program"
    (program / "modules").mkdir(parents=True)
    (program / "main.py").write_text("print('x')\n", encoding="utf-8")
    (program / "modules" / "a.py").write_text("A = 1\n", encoding="utf-8")
    backups = tmp_path / "backups"
    backups.mkdir()
    monkeypatch.setenv("ZSMM_PROGRAM_DIR", str(program))
    monkeypatch.setenv("ZSMM_BACKUP_DIR", str(backups))
    return program, backups


def test_make_backup_copies_program_files(sandbox) -> None:
    program, backups = sandbox

    created = archive.make_backup("test")

    assert created is not None and created.is_file()
    with zipfile.ZipFile(created) as z:
        names = set(z.namelist())
    assert "main.py" in names
    assert any(name.endswith("a.py") for name in names)


def test_backup_dir_can_be_relocated(sandbox) -> None:
    """Каталог бэкапов задаётся окружением: тест не пишет в установку."""
    _, backups = sandbox

    assert paths.backup_dir() == backups


def test_make_backup_keeps_only_three(sandbox, monkeypatch) -> None:
    _, backups = sandbox

    created = []
    for index in range(5):
        monkeypatch.setenv("ZSMM_PROGRAM_DIR", str(sandbox[0]))
        item = backups / f"backup_2026010{index}_120000_old.zip"
        item.write_bytes(b"PK" + b"\0" * 2000)
        created.append(item)

    removed = archive.prune_old_backups(keep=3)

    assert len(removed) == 2
    assert len(list(backups.glob("backup_*.zip"))) == 3


def test_list_backups_is_newest_first(sandbox) -> None:
    _, backups = sandbox
    for index, name in enumerate(("a", "b", "c")):
        (backups / f"backup_2026010{index}_{name}.zip").write_bytes(b"PK" + b"\0" * 100)

    listed = archive.list_backups()

    assert len(listed) == 3
    assert listed == sorted(listed, key=lambda item: item["mtime"], reverse=True)


# --------------------------------------------------------------------------- #
#  Пути: program vs user data (обновление не трогает данные)
# --------------------------------------------------------------------------- #

def test_program_dir_from_environment(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ZSMM_PROGRAM_DIR", str(tmp_path))

    assert paths.program_dir() == tmp_path


def test_user_data_dir_is_separate_from_program(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ZSMM_USER_DIR", str(tmp_path / "user"))
    monkeypatch.setenv("ZSMM_PROGRAM_DIR", str(tmp_path / "program"))

    assert paths.user_data_dir() != paths.program_dir()
    assert paths.user_data_dir().name == "user"


def test_online_flag_is_off_by_default(monkeypatch) -> None:
    """T15: без явного согласия апдейтер не ходит в сеть."""
    monkeypatch.delenv("ZSMM_ONLINE", raising=False)
    monkeypatch.delenv("ZSMM_ALLOW_NETWORK", raising=False)

    assert paths.online_enabled() is False


# --------------------------------------------------------------------------- #
#  Сеть: отказ без согласия, а не молчаливый запрос
# --------------------------------------------------------------------------- #

def test_check_updates_refuses_without_opt_in(sandbox) -> None:
    """`ok: True` здесь означает «проверка выполнена и отказалась», а не успех."""
    result = check_updates("https://example.invalid/version.json")

    assert result["offline"] is True
    assert "allow_online" in result["reason"] or "--online" in result["reason"]


def test_git_status_refuses_network_without_opt_in(sandbox) -> None:
    result = check_git_update_status(allow_online=False)

    assert result["offline"] is True
    assert result["apply_performed"] is False


# --------------------------------------------------------------------------- #
#  Восстановление пользовательских данных
# --------------------------------------------------------------------------- #

def test_user_preserved_lists_secrets_and_settings() -> None:
    assert "data/secrets.enc" in userdata.USER_PRESERVED
    assert "data/settings.json" in userdata.USER_PRESERVED


def test_stash_and_restore_return_user_files(tmp_path) -> None:
    """Установка кладёт данные в staging и возвращает их поверх новой версии."""
    program = tmp_path / "program"
    (program / "voice_vault").mkdir(parents=True)
    (program / "voice_vault" / "take1.wav").write_bytes(b"RIFF")
    (program / "data").mkdir()
    (program / "data" / "secrets.enc").write_bytes(b"secret")
    staging = tmp_path / "staging"
    staging.mkdir()

    moved = userdata._stash_user_data(program, staging)
    assert not (program / "voice_vault").exists()

    # новая версия принесла свой файл в тот же каталог
    (program / "voice_vault").mkdir()
    (program / "voice_vault" / "default.wav").write_bytes(b"NEW")
    restored = userdata._restore_user_data(program, moved)

    assert set(restored) == set(moved)
    assert (program / "voice_vault" / "take1.wav").read_bytes() == b"RIFF"
    assert (program / "voice_vault" / "default.wav").read_bytes() == b"NEW"
    assert (program / "data" / "secrets.enc").read_bytes() == b"secret"


def test_restore_reports_failures_instead_of_swallowing_them(tmp_path, monkeypatch) -> None:
    """Ошибка возврата данных — это потеря данных, её нельзя проглатывать."""
    program = tmp_path / "program"
    program.mkdir()
    stash = tmp_path / "stash"
    stash.mkdir()
    (stash / "voice_vault").mkdir()
    (stash / "voice_vault" / "take1.wav").write_bytes(b"RIFF")

    def broken(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(userdata.shutil, "copytree", broken)

    report = userdata.restore_user_data_report(program, {"voice_vault": stash / "voice_vault"})

    assert report["ok"] is False
    assert report["failed"] and "voice_vault" in report["failed"][0]


# --------------------------------------------------------------------------- #
#  CLI: каждый флаг отвечает и не падает
# --------------------------------------------------------------------------- #

def _run_cli(monkeypatch, *args: str) -> int:
    monkeypatch.setattr("sys.argv", ["zsmm-updater", *args])
    return cli.main()


def test_cli_info_prints_paths(monkeypatch, capsys, sandbox) -> None:
    code = _run_cli(monkeypatch, "--info")

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert "program_dir" in payload and "user_data_dir" in payload
    assert "user_preserved" in payload


def test_cli_list_backups(monkeypatch, capsys, sandbox) -> None:
    code = _run_cli(monkeypatch, "--list-backups")

    assert code == 0
    assert isinstance(json.loads(capsys.readouterr().out), list)


def test_cli_without_arguments_prints_help(monkeypatch, capsys) -> None:
    code = _run_cli(monkeypatch)

    assert code == 0
    assert "zsmm-updater" in capsys.readouterr().out


def test_cli_install_rejects_broken_package(monkeypatch, capsys, tmp_path, sandbox) -> None:
    broken = tmp_path / "broken.zip"
    broken.write_bytes(b"not a zip" * 300)

    code = _run_cli(monkeypatch, "--install", str(broken))

    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload["ok"] is False


def test_cli_git_status_without_online(monkeypatch, capsys) -> None:
    monkeypatch.setenv("ZSMM_ONLINE", "0")

    code = _run_cli(monkeypatch, "--git-status")

    out = capsys.readouterr().out
    assert code in (0, 1)
    assert out.strip(), "флаг обязан что-то ответить, а не молчать"
