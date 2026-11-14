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
    master_sha_before = sha256_file(Path(master))

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

    # Стенд стриминга лежит в пакете один раз: его роль играет `master.wav`.
    # Копия `masters/streaming.wav` с тем же звуком — это лишние 42 МБ в
    # пакете и в архиве (так и было в живом прогоне).
    for name in ("master.wav", "drums.wav", "lyrics.txt", "hit_report.md"):
        assert name in artifacts, f"{name} отсутствует в манифесте"
        assert len(artifacts[name]) == 64
    assert not (Path(result["path"]) / "masters" / "streaming.wav").exists()
    assert result["masters"] == [str(Path(result["path"]) / "master.wav")]
    # T18: пакетный мастер — копия с ID3-тегами, поэтому его SHA-256
    # обязан совпадать с манифестом, но не с проектом (оригинал не мутируется,
    # это отдельно проверяет tests/test_release_id3.py).
    assert artifacts["master.wav"] == sha256_file(Path(result["path"]) / "master.wav")
    assert sha256_file(Path(master)) == master_sha_before, "мастер проекта изменён тегированием"
    assert manifest["id3"]["ok"] is True
    assert "timed_lyrics" in result["missing"]
    assert "timed_lyrics" in manifest["missing"]
    assert not (Path(result["path"]) / "lyrics.lrc").exists()
    assert not (Path(result["path"]) / "lyrics.srt").exists()
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

    assert exported["isrc_status"] == "UNREGISTERED"
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
    master_sha_before = sha256_file(Path(master))

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


def test_supplied_isrc_is_unverified_not_registered(tmp_path) -> None:
    master = _tone(tmp_path / "master.wav")
    result = export_release("", "", master, recipe={"isrc": "US-ABC-25-12345"}, out_dir=tmp_path / "pack")
    assert result["isrc"] == "US-ABC-25-12345"
    assert result["isrc_status"] == "USER_SUPPLIED_UNVERIFIED"
    assert result["manifest"]["metadata"]["isrc_status"] == "USER_SUPPLIED_UNVERIFIED"


def test_existing_timed_lyrics_are_not_overwritten_or_silently_archived(tmp_path) -> None:
    master = _tone(tmp_path / "master.wav")
    out = tmp_path / "pack"
    out.mkdir()
    stale = out / "lyrics.lrc"
    stale.write_text("user content", encoding="utf-8")
    result = build_pack(master, str(out), lyrics_text="строка")
    assert result["ok"] is False
    assert "fresh release directory" in result["reason"]
    assert stale.read_text(encoding="utf-8") == "user content"
    assert not (out / "release.zip").exists()


def test_streaming_master_is_not_duplicated_as_master_wav(tmp_path) -> None:
    """Мастер стриминга лежит в пакете один раз.

    Живой прогон дал `master.wav` и `masters/streaming.wav` с одинаковым
    SHA-256 — это 42 МБ дважды в пакете и в архиве (из 363 МБ распакованного
    объёма 40 МБ были ровно этим дублем). `master.wav` нужен: его читает
    плеер и по нему считается отпечаток, — поэтому копия стенда с тем же
    содержимым не создаётся.
    """
    import json

    master = tmp_path / "streaming.wav"
    sf.write(master, np.zeros(800, dtype=np.float32), 8_000)

    packed = build_pack(
        str(master),
        str(tmp_path / "release"),
        meta={"title": "Тест", "artist": "Артист", "duration_sec": 2},
        masters_map={"streaming": str(master)},
        lyrics_text="",
    )

    assert packed["ok"] is True, packed.get("reason")
    release_dir = Path(packed["release_dir"])
    assert (release_dir / "master.wav").is_file()
    assert not (release_dir / "masters" / "streaming.wav").exists()
    manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    # Звук в пакете тот же: сравнение по размеру, а не по SHA — пакетный
    # мастер перетегируется ID3, и байты отличаются от исходника.
    assert (release_dir / "master.wav").stat().st_size >= master.stat().st_size
    assert "master.wav" in manifest["artifacts_sha256"]
    assert "streaming.wav" not in manifest["artifacts_sha256"]
