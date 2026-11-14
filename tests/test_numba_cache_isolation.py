# -*- coding: utf-8 -*-
"""`app/core/numba_cache.py`: изоляция JIT-кэша Numba.

Модуль стоит на входе каждого запуска (`main.py`) и 0 % покрытия не имел.
Ошибка здесь ломает не стадию, а весь процесс до его начала, поэтому проверяется
контракт окружения: что выставляется, что восстанавливается и что не
затирается чужое.

Реальный Numba не нужен и не вызывается: проверяется только работа с
переменными окружения и каталогом. Имитация `numba` в `sys.modules` — это
проверка нашего запрета, а не JIT.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

from app.core import numba_cache

MARKER = "ZSMM_NUMBA_CACHE_ISOLATED"
BASE = "ZSMM_NUMBA_CACHE_BASE"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Предпосылка блока: Numba ещё не импортирована и переменных нет.

    В полном наборе `numba` попадает в `sys.modules` через librosa (его тянет
    анализатор), и блок обязан отказать — поэтому здесь предпосылка
    выставляется явно, а не подразумевается. Сам отказ проверяется отдельным
    тестом.
    """
    monkeypatch.delitem(sys.modules, "numba", raising=False)
    for key in ("NUMBA_CACHE_DIR", MARKER, BASE):
        monkeypatch.delenv(key, raising=False)
    yield


def test_cache_dir_is_set_inside_the_block_and_gone_after() -> None:
    assert "NUMBA_CACHE_DIR" not in os.environ

    with numba_cache.isolated_numba_cache() as directory:
        assert os.environ["NUMBA_CACHE_DIR"] == directory
        assert os.environ[MARKER] == "1"
        assert Path(directory).is_dir()
        created = Path(directory)

    assert not created.exists(), "временный каталог обязан удаляться на выходе"
    assert "NUMBA_CACHE_DIR" not in os.environ
    assert MARKER not in os.environ


def test_previous_values_are_restored(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("NUMBA_CACHE_DIR", str(tmp_path / "какой-то-кэш"))
    monkeypatch.setenv(MARKER, "0")
    monkeypatch.setenv(BASE, str(tmp_path / "база"))
    (tmp_path / "какой-то-кэш").mkdir()

    with numba_cache.isolated_numba_cache():
        assert os.environ["NUMBA_CACHE_DIR"] != str(tmp_path / "какой-то-кэш")

    assert os.environ["NUMBA_CACHE_DIR"] == str(tmp_path / "какой-то-кэш")
    assert os.environ[MARKER] == "0"
    assert os.environ[BASE] == str(tmp_path / "база")


def test_marker_from_parent_selects_base(tmp_path, monkeypatch) -> None:
    """Маркер родителя + база = каталог рядом с базой (не внутри кэша родителя)."""
    monkeypatch.setenv(MARKER, "1")
    base = tmp_path / "base"
    base.mkdir()
    monkeypatch.setenv(BASE, str(base))

    with numba_cache.isolated_numba_cache() as directory:
        assert Path(directory).parent == base


def test_child_process_uses_sibling_directory(tmp_path, monkeypatch) -> None:
    """Дочерний процесс не должен писать внутрь кэша родителя: его удалят первым."""
    monkeypatch.setenv(MARKER, "1")
    monkeypatch.setenv(BASE, str(tmp_path))
    monkeypatch.setenv("NUMBA_CACHE_DIR", str(tmp_path / "parent-cache"))

    with numba_cache.isolated_numba_cache() as directory:
        assert Path(directory).parent == tmp_path
        assert Path(directory) != tmp_path / "parent-cache"


def test_child_without_base_does_not_reuse_parent_cache(tmp_path, monkeypatch) -> None:
    """Без базы дочерний процесс берёт системный tmp, а не кэш родителя.

    Это защита от того, что родитель удалит свой каталог первым.
    """
    monkeypatch.setenv(MARKER, "1")
    monkeypatch.delenv(BASE, raising=False)
    parent_cache = tmp_path / "parent-cache"
    parent_cache.mkdir()
    monkeypatch.setenv("NUMBA_CACHE_DIR", str(parent_cache))

    with numba_cache.isolated_numba_cache() as directory:
        assert Path(directory).parent != tmp_path
        assert Path(directory).parent == Path(tempfile.gettempdir())


def test_relative_base_is_exported_as_absolute(tmp_path, monkeypatch) -> None:
    """Дочерний процесс не должен зависеть от своего cwd — база абсолютная."""
    monkeypatch.delenv(MARKER, raising=False)
    monkeypatch.setenv("NUMBA_CACHE_DIR", "relative-base")
    (tmp_path / "relative-base").mkdir()
    monkeypatch.chdir(tmp_path)

    with numba_cache.isolated_numba_cache() as directory:
        assert os.environ[BASE] == str(tmp_path / "relative-base")
        assert Path(directory).parent == tmp_path / "relative-base"


def test_numba_already_imported_is_refused(monkeypatch) -> None:
    """Поздно изолировать кэш после импорта Numba — это честный отказ."""
    monkeypatch.setitem(sys.modules, "numba", object())

    with pytest.raises(RuntimeError, match="after Numba was imported"):
        with numba_cache.isolated_numba_cache():
            pass

    assert "NUMBA_CACHE_DIR" not in os.environ


def test_vanished_base_falls_back_to_system_temp(tmp_path, monkeypatch, caplog) -> None:
    """Устаревший NUMBA_CACHE_DIR не должен лишать пользователя запуска."""
    blocked = tmp_path / "file-not-dir"
    blocked.write_text("x", encoding="utf-8")
    monkeypatch.setenv(MARKER, "1")  # база учитывается только у дочерних процессов
    monkeypatch.setenv(BASE, str(blocked))

    with caplog.at_level("WARNING", logger="app.core.numba_cache"):
        with numba_cache.isolated_numba_cache() as directory:
            assert Path(directory).parent == Path(tempfile.gettempdir())

    assert "not usable" in caplog.text


def test_missing_temp_root_is_a_hard_error(tmp_path, monkeypatch) -> None:
    """Если и системный tmp недоступен — честный RuntimeError, а не тихая работа."""
    monkeypatch.setenv(MARKER, "1")
    monkeypatch.setenv(BASE, str(tmp_path / "nope"))
    monkeypatch.setattr(
        numba_cache.tempfile,
        "TemporaryDirectory",
        lambda **kwargs: (_ for _ in ()).throw(PermissionError("tmp недоступен")),
    )

    with pytest.raises(RuntimeError, match="cannot create private Numba cache"):
        with numba_cache.isolated_numba_cache():
            pass


def test_caller_changes_are_not_overwritten(monkeypatch) -> None:
    """Если внутри блока кто-то сознательно сменил кэш — не возвращаем старое."""
    with numba_cache.isolated_numba_cache():
        os.environ["NUMBA_CACHE_DIR"] = "/tmp/выбран-вручную"

    assert os.environ["NUMBA_CACHE_DIR"] == "/tmp/выбран-вручную"
    os.environ.pop("NUMBA_CACHE_DIR", None)


def test_exception_inside_block_still_cleans_up() -> None:
    with pytest.raises(ValueError):
        with numba_cache.isolated_numba_cache() as directory:
            created = Path(directory)
            raise ValueError("сбой внутри блока")

    assert not created.exists()
    assert "NUMBA_CACHE_DIR" not in os.environ


def test_two_sequential_blocks_get_different_directories() -> None:
    with numba_cache.isolated_numba_cache() as first:
        pass
    with numba_cache.isolated_numba_cache() as second:
        pass

    assert first != second


def test_base_defaults_to_system_temp(monkeypatch) -> None:
    with numba_cache.isolated_numba_cache():
        directory = os.environ["NUMBA_CACHE_DIR"]
        parent = Path(directory).parent

    assert parent == Path(tempfile.gettempdir()) or str(parent).startswith("/tmp")


def test_broken_system_tmp_without_base_is_reported(monkeypatch) -> None:
    """Базы нет вовсе и системный tmp недоступен — отказ с внятной причиной."""
    monkeypatch.setattr(
        numba_cache.tempfile,
        "TemporaryDirectory",
        lambda **kwargs: (_ for _ in ()).throw(PermissionError("tmp недоступен")),
    )

    with pytest.raises(RuntimeError, match="cannot create private Numba cache"):
        with numba_cache.isolated_numba_cache():
            pass
