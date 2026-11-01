# -*- coding: utf-8 -*-
"""
Гейты релизного пакета: манифест покрывает все файлы, ISRC валиден,
ZIP открывается, площадки получают свои артефакты.

Пакет — последнее, что видит пользователь перед публикацией. Поэтому здесь
проверяется не «функция вернула dict», а содержимое: каждый файл из пакета
обязан быть в манифесте с SHA-256.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf

from modules.release import build_pack, build_all_channels, export_release, sha256_file
from modules.release.channels import CHANNELS


def _tone(path: Path, seconds: float = 2.0, freq: float = 220.0, sr: int = 8_000) -> str:
    time_axis = np.arange(int(sr * seconds)) / sr
    sf.write(path, 0.1 * np.sin(2 * np.pi * freq * time_axis), sr)
    return str(path)


def test_manifest_covers_every_artifact_with_sha256(tmp_path) -> None:
    master = _tone(tmp_path / "master.wav")
    stem = _tone(tmp_path / "stem.wav", 2.0, 110.0)

    result = build_pack(
        master,
        str(tmp_path / "pack"),
        meta={"title": "Тест", "artist": "Артист", "duration_sec": 2},
        masters_map={"streaming": master},
        stems_map={"drums": stem},
        lyrics_text="[Куплет]\nПервая строка\nВторая строка",
        hit_metrics={"hit_score": 71.5, "verdict": "PASS"},
    )

    assert result["ok"] is True
    manifest = json.loads((Path(result["path"]) / "manifest.json").read_text(encoding="utf-8"))
    artifacts = manifest["artifacts_sha256"]

    for name in ("master.wav", "streaming.wav", "drums.wav", "lyrics.lrc", "lyrics.srt", "hit_report.md"):
        assert name in artifacts, f"{name} отсутствует в манифесте"
        assert len(artifacts[name]) == 64
    assert artifacts["master.wav"] == sha256_file(Path(master))
    assert Path(result["path"], "release.zip").is_file()


def test_release_zip_is_readable_and_contains_manifest(tmp_path) -> None:
    master = _tone(tmp_path / "master.wav")
    exported = export_release(
        beat_path="",
        vocal_path="",
        master_path=master,
        lyrics="строка",
        recipe={"duration_sec": 2},
        project_name="zip_test",
        artist_name="Artist",
        title="Track",
    )

    assert exported["ok"] is True
    with zipfile.ZipFile(exported["files"]["release.zip"]) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "master.wav" in names
        assert archive.testzip() is None


def test_isrc_is_valid_or_honestly_unregistered(tmp_path) -> None:
    master = _tone(tmp_path / "master.wav")
    exported = export_release(
        beat_path="",
        vocal_path="",
        master_path=master,
        lyrics="",
        recipe={},
        project_name="isrc_test",
        artist_name="Artist",
        title="Track",
    )

    assert exported["isrc_status"] in {"REGISTERED", "UNREGISTERED"}
    if exported["isrc_status"] == "REGISTERED":
        compact = exported["isrc"].replace("-", "")
        assert len(compact) == 12
        assert not compact.startswith("XX")
    else:
        assert exported["isrc"] == ""


def test_every_channel_package_is_written(tmp_path) -> None:
    result = build_all_channels(
        {"title": "Трек", "artist": "Артист", "duration_sec": 120, "hook_start_sec": 15}, tmp_path
    )

    assert result["ok"] is True
    assert result["failed"] == []
    assert set(result["channels"]) == set(CHANNELS)
    assert len(result["files"]) == len(CHANNELS)
    for path in result["files"]:
        assert Path(path).stat().st_size > 0


def test_unknown_channel_is_rejected_not_silently_ignored(tmp_path) -> None:
    from modules.release.channels import build_channel_package

    result = build_channel_package("myspace", {"title": "x"}, tmp_path)

    assert result["ok"] is False
    assert "unknown channel" in result["reason"]


def test_missing_master_is_a_failure_not_an_empty_pack(tmp_path) -> None:
    result = build_pack(str(tmp_path / "nope.wav"), str(tmp_path / "pack"))

    assert result["ok"] is False
    assert "master not found" in result["reason"]
    assert not (tmp_path / "pack" / "manifest.json").exists()


def test_zip_manifest_matches_the_release_folder(tmp_path) -> None:
    """Архив не должен содержать устаревший манифест после сборки пакета."""
    master = _tone(tmp_path / "master.wav")
    stem = _tone(tmp_path / "stem.wav", 2.0, 110.0)

    result = build_pack(
        master,
        str(tmp_path / "pack"),
        meta={"title": "Тест", "artist": "Артист", "duration_sec": 2},
        stems_map={"drums": stem},
        lyrics_text="строка",
    )

    release_dir = Path(result["path"])
    folder_manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(release_dir / "release.zip") as archive:
        zip_manifest = json.loads(archive.read("manifest.json"))

    assert set(folder_manifest["artifacts_sha256"]) == set(zip_manifest["artifacts_sha256"])
    assert "drums.wav" in zip_manifest["artifacts_sha256"]
