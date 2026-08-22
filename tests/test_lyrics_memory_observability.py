from __future__ import annotations

from pathlib import Path

import modules.lyrics_gen as lyrics


def test_lyric_memory_diagnostics_preserves_valid_jsonl_entries(tmp_path: Path, monkeypatch) -> None:
    memory_path = tmp_path / "lyrics_memory.jsonl"
    memory_path.write_text(
        '{"theme": "first"}\nnot-json\n{"theme": "second"}\n', encoding="utf-8"
    )
    monkeypatch.setattr(lyrics, "LYRIC_MEMORY", memory_path)

    assert lyrics.get_lyric_memory() == [{"theme": "second"}, {"theme": "first"}]
    diagnostics = lyrics.get_lyric_memory_diagnostics()

    assert diagnostics["memories"] == [{"theme": "second"}, {"theme": "first"}]
    assert len(diagnostics["read_errors"]) == 1
    assert diagnostics["read_errors"][0].startswith("line 2: JSONDecodeError:")
