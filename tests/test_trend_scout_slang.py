"""T10: источником локального сленга служит файл пользователя, а не призрак.

`scout_trends_with_diagnostics` импортировал `modules.lyrics_gen`, которого не
существует: сленг всегда «не находился», а причина складывалась в диагностику
как будто это сбой среды. Файл `lyric_vault/slang.txt` (он же указан в
докстринге модуля) не читался вообще.
"""

from __future__ import annotations

import pytest

from agents import trend_scout


@pytest.fixture
def no_network(monkeypatch, tmp_path):
    """Сеть и кэш отключены: проверяется именно локальный источник."""
    monkeypatch.setattr(trend_scout, "_duckduckgo_search", lambda *a, **k: [])
    monkeypatch.setattr(trend_scout, "CACHE_FILE", tmp_path / "trends_cache.json")
    monkeypatch.setattr(trend_scout, "_load_cache", lambda: {})
    monkeypatch.setattr(trend_scout, "_save_cache", lambda *_: None)
    return tmp_path


def test_slang_file_is_read(no_network, monkeypatch) -> None:
    slang = no_network / "slang.txt"
    slang.write_text("# комментарий\nкраш\nвайб\n\nхайп\n", encoding="utf-8")
    monkeypatch.setattr(trend_scout, "SLANG_FILE", slang)

    report = trend_scout.scout_trends_with_diagnostics("drift phonk")

    assert "краш" in report["trends"]
    assert "вайб" in report["trends"]
    assert "#" not in " ".join(report["trends"]), "комментарии не должны попадать в тренды"
    assert report["diagnostics"] == []


def test_missing_slang_file_is_diagnosed(no_network, monkeypatch) -> None:
    monkeypatch.setattr(trend_scout, "SLANG_FILE", no_network / "absent.txt")

    report = trend_scout.scout_trends_with_diagnostics("drift phonk")

    entry = next(d for d in report["diagnostics"] if d["source"] == "local_slang")
    assert entry["ok"] is False
    assert "FileNotFoundError" in entry["error"]
    # встроенный словарь продолжает работать
    assert report["trends"]


def test_builtin_dictionary_is_the_fallback(no_network, monkeypatch) -> None:
    monkeypatch.setattr(trend_scout, "SLANG_FILE", no_network / "absent.txt")

    report = trend_scout.scout_trends_with_diagnostics("drift phonk")

    assert report["source"] in ("built_in_fallback", "live_or_local")


def test_no_dependency_on_nonexistent_lyrics_gen() -> None:
    """`modules.lyrics_gen` не существует и не должен упоминаться."""
    from pathlib import Path

    source = Path(trend_scout.__file__).read_text(encoding="utf-8")

    assert "lyrics_gen" not in source


def test_slang_entries_are_trimmed_and_deduplicated(no_network, monkeypatch) -> None:
    slang = no_network / "slang.txt"
    slang.write_text("  краш  \nкраш\nвайб\n", encoding="utf-8")
    monkeypatch.setattr(trend_scout, "SLANG_FILE", slang)

    entries = trend_scout._load_local_slang()

    assert entries == ["краш", "вайб"]
