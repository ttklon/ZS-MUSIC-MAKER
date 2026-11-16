# -*- coding: utf-8 -*-
"""Архив источника для кнопки «Обновить» — лёгкий и пригодный к установке.

Поводом стал реальный дефект релизного шага: архив писался внутрь
`_artifacts/`, а архивировался весь каталог — то есть zip глатал уже собранные
EXE и сам себя. В релизах 42.0.x это давало **632 МБ** вместо ~16 МБ, и именно
этот файл скачивает кнопка «Обновить»: пользователь каждый раз тянул лишние
600 МБ.

Тест держит обе стороны: архив проходит проверку `updater.archive.verify_zip`
(иначе обновление не установится) и не содержит артефактов рендера.
"""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

from updater.archive import verify_zip

ROOT = Path(__file__).resolve().parents[1]


def _source_zip(tmp_path: Path) -> Path:
    """Собрать архив содержимого репозитория той же формой, что и релиз."""
    out = tmp_path / "source.zip"
    subprocess.run(
        ["git", "archive", "--format=zip", "-o", str(out), "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return out


def test_source_zip_passes_updater_verification(tmp_path: Path) -> None:
    """Без этого кнопка «Обновить» отвергнет собственный релиз."""
    result = verify_zip(_source_zip(tmp_path))
    assert result["ok"], result.get("reason")
    assert result["checks"]["has_main_py"]
    assert result["checks"]["has_version_json"]
    assert result["checks"]["has_modules"]


def test_source_zip_has_no_render_artifacts(tmp_path: Path) -> None:
    """Собранные EXE и демо-WAV в архиве источника не нужны никому."""
    names = zipfile.ZipFile(_source_zip(tmp_path)).namelist()
    assert not [name for name in names if name.lower().endswith(".exe")], "в архиве источника есть EXE"
    assert not [
        name for name in names if name.startswith("demo_site/") and name.endswith(".wav")
    ], "в архиве источника вернулись демо-WAV"
