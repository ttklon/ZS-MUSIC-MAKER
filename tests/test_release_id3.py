"""T18: релизный мастер получает ID3-теги, проектный мастер не меняется.

Обещание «теги в мастере» жило в документации и health-пробах, но `import
mutagen` в коде отсутствовал полностью: пользователь получал WAV без
метаданных, а отчёт этого не замечал.

Решение владельца — вариант A: тегировать копию мастера внутри релизного
пакета. Файл в каталоге проекта остаётся бит-в-бит прежним.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from modules.release import export


def _write_wav(path: Path, seconds: float = 1.0, sr: int = 22050) -> Path:
    t = np.arange(int(sr * seconds)) / sr
    sf.write(path, 0.2 * np.sin(2 * np.pi * 220 * t), sr)
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def master(tmp_path) -> Path:
    return _write_wav(tmp_path / "project_master.wav")


def _export(tmp_path, master, **kwargs):
    return export.export_release(
        beat_path="",
        vocal_path="",
        master_path=str(master),
        lyrics="строка",
        recipe={"genre": "drift_phonk", "bpm": 140, "key": "A minor"},
        project_name="night_drive",
        artist_name="ZS Producer",
        title="Night Drive",
        out_dir=tmp_path / "release",
        **kwargs,
    )


def test_release_master_carries_tags(tmp_path, master) -> None:
    pytest.importorskip("mutagen")
    from mutagen import File as MutagenFile

    result = _export(tmp_path, master)

    assert result["ok"] is True, result
    assert result["id3"]["ok"] is True, result["id3"]
    tags = MutagenFile(result["files"]["master.wav"]).tags
    assert tags is not None
    assert str(tags["TIT2"]) == "Night Drive"
    assert str(tags["TPE1"]) == "ZS Producer"
    assert str(tags["TCON"]) == "drift_phonk"


def test_project_master_is_not_mutated(tmp_path, master) -> None:
    before = _sha(master)

    result = _export(tmp_path, master)

    assert _sha(master) == before, "тегирование изменило мастер в каталоге проекта"
    assert result["files"]["master.wav"] != str(master)


def test_manifest_records_the_id3_result(tmp_path, master) -> None:
    result = _export(tmp_path, master)

    manifest = json.loads((Path(result["release_dir"]) / "manifest.json").read_text(encoding="utf-8"))
    assert "id3" in manifest
    assert manifest["id3"]["ok"] is True


def test_missing_mutagen_is_an_honest_refusal(tmp_path, master, monkeypatch) -> None:
    monkeypatch.setattr(export, "HAS_MUTAGEN", False, raising=False)

    result = _export(tmp_path, master)

    assert result["ok"] is True, "пакет собирается и без тегов"
    assert result["id3"]["ok"] is False
    assert result["id3"]["reason"]
    manifest = json.loads((Path(result["release_dir"]) / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["id3"]["ok"] is False


def test_tags_contain_a_date_and_track_number(tmp_path, master) -> None:
    pytest.importorskip("mutagen")
    from mutagen import File as MutagenFile

    result = _export(tmp_path, master)

    tags = MutagenFile(result["files"]["master.wav"]).tags
    assert tags.get("TDRC")
    assert tags.get("TRCK")


def test_written_tag_file_is_still_valid_audio(tmp_path, master) -> None:
    result = _export(tmp_path, master)

    data, sr = sf.read(result["files"]["master.wav"])

    assert len(data) > 0 and sr > 0
