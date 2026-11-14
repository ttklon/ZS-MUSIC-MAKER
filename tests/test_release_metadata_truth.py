# -*- coding: utf-8 -*-
"""
Релизный пакет: метаданные говорят правду о треке.

В живом прогоне `main.py --god --genre phonk` пакет для площадок утверждал,
что трек длится `PT0S`, а тональность в `metadata.json` была пустой строкой:
оркестратор собирал `meta` без `duration_sec`, `key` и `key_root`, хотя отчёт
стадии бита эти числа уже знал. Для Spotify/Shazam это не косметика: пустая
длительность и тональность уходят в структурированные данные площадки.

Тесты пакета этого не видели, потому что каждый передавал `duration_sec` сам.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

from modules.release import export as release_export
from modules.release import pack as release_pack


def _master(tmp_path: Path, seconds: float = 2.0) -> Path:
    path = tmp_path / "master.wav"
    sample_rate = 8_000
    axis = np.arange(int(sample_rate * seconds)) / sample_rate
    sf.write(path, 0.1 * np.sin(2 * np.pi * 220 * axis), sample_rate)
    return path


def test_duration_is_measured_from_master_when_meta_has_none(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(release_export, "RELEASES_DIR", tmp_path / "releases")
    master = _master(tmp_path, seconds=3.0)

    # Метаданные без длительности — ровно то, что собрал оркестратор.
    result = release_export.export_release(
        beat_path=str(master),
        vocal_path="",
        master_path=str(master),
        lyrics="строка",
        recipe={"genre": "phonk", "bpm": 130, "key": ""},
        project_name="meta_truth",
        artist_name="Test Artist",
        title="Test Track",
    )

    release_dir = Path(result["release_dir"])
    metadata = json.loads((release_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["duration_sec"] == 3.0, "длительность не измерена по мастеру"


def test_meta_key_root_and_mode_become_one_key(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(release_export, "RELEASES_DIR", tmp_path / "releases")
    master = _master(tmp_path)

    result = release_export.export_release(
        beat_path=str(master),
        vocal_path="",
        master_path=str(master),
        recipe={"genre": "phonk", "bpm": 130, "key_root": "A", "mode": "minor"},
        project_name="meta_key",
        artist_name="Test Artist",
        title="Test Track",
    )

    metadata = json.loads(
        (Path(result["release_dir"]) / "metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["key"] == "A minor"


def test_release_notes_name_duration_instead_of_na(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(release_export, "RELEASES_DIR", tmp_path / "releases")
    master = _master(tmp_path, seconds=3.0)

    result = release_export.export_release(
        beat_path=str(master),
        vocal_path="",
        master_path=str(master),
        recipe={"genre": "phonk", "bpm": 130},
        project_name="notes",
        artist_name="Test Artist",
        title="Test Track",
    )

    notes = (Path(result["release_dir"]) / "release_notes.txt").read_text(encoding="utf-8")
    assert "Длительность: n/a" not in notes
    assert "Длительность: 3.0 с" in notes


def test_pack_measures_duration_from_master(tmp_path) -> None:
    master = _master(tmp_path, seconds=2.0)
    packed = release_pack.build_pack(
        str(master),
        str(tmp_path / "release"),
        meta={"title": "Тест", "artist": "Артист", "genre": "phonk", "bpm": 130},
        lyrics_text="",
    )

    assert packed["ok"] is True, packed.get("reason")
    metadata = json.loads(
        (Path(packed["release_dir"]) / "metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["duration_sec"] == 2.0

    # Структурированные данные площадки не должны утверждать «0 секунд»:
    # именно это ушло в пакет живого прогона (`"duration": "PT0S"`).
    shazam = json.loads(
        (Path(packed["release_dir"]) / "channels" / "shazam" / "shazam.jsonld").read_text(
            encoding="utf-8"
        )
    )
    assert shazam["duration"] == "PT2S"
