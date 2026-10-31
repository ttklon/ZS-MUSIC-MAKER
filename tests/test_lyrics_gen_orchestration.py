from __future__ import annotations

import modules.lyrics.author as lyrics_v8


def test_generate_lyrics_v8_orchestrates_optional_helpers_without_network(monkeypatch) -> None:
    monkeypatch.setattr(lyrics_v8, "_fetch_slang", lambda _theme: ["drift"])
    monkeypatch.setattr(
        lyrics_v8,
        "_author_style_prompt",
        lambda author, theme, words, slang, bpm, target: ("style", True),
    )
    calls: dict[str, object] = {}

    def fake_raw(seed, words, bpm, style_prompt, target_lines, slang):
        calls.update(seed=seed, words=words, bpm=bpm, style_prompt=style_prompt, target_lines=target_lines, slang=slang)
        return "[Куплет 1]\nночь и мотор\n[Припев]\nride forever\n"

    monkeypatch.setattr(lyrics_v8, "_generate_raw_lyrics", fake_raw)

    result = lyrics_v8.generate_lyrics_v8(
        "ночной заезд", user_words=["  turbo  ", ""], bpm=140,
        author="Reference", target_lines=8, want_female_backing=True, lang_mix="ru",
    )

    assert calls == {
        "seed": "ночной заезд — turbo · слэнг: drift",
        "words": ["turbo"],
        "bpm": 140,
        "style_prompt": "style",
        "target_lines": 8,
        "slang": ["drift"],
    }
    assert "[Куплет 1]" in result["text"]
    assert result["chorus_lines"] == ["ride forever"]
    assert result["used_slang"] == ["drift"]
    assert result["author_style_used"] is True
    assert result["want_female_backing"] is True
    assert result["author"] == "Reference"
