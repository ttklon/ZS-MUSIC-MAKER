"""Regression coverage for legacy lyrics author-style fallback diagnostics."""

from modules.lyrics import author as lyrics_v8


def test_author_style_diagnostics_report_failed_reference_ingestion(monkeypatch):
    def fail_profile(author):
        raise OSError("reference store unavailable")

    monkeypatch.setattr(lyrics_v8.author_ref_lyrics, "get_style_profile", fail_profile)

    prompt, used, diagnostics = lyrics_v8._author_style_prompt_with_diagnostics(
        "Reference Artist", "night ride", [], [], 130, 16
    )

    assert prompt == ""
    assert used is False
    assert diagnostics == {
        "ok": False,
        "status": "failed",
        "author": "Reference Artist",
        "error": "OSError: reference store unavailable",
    }
    assert lyrics_v8._author_style_prompt(
        "Reference Artist", "night ride", [], [], 130, 16
    ) == ("", False)


def test_generate_lyrics_includes_author_style_provenance(monkeypatch):
    monkeypatch.setattr(lyrics_v8, "_fetch_slang", lambda theme: [])
    monkeypatch.setattr(
        lyrics_v8,
        "_author_style_prompt_with_diagnostics",
        lambda *args: ("", False, {"ok": False, "status": "profile_unavailable", "author": "Reference Artist"}),
    )
    monkeypatch.setattr(
        lyrics_v8,
        "_generate_raw_lyrics",
        lambda *args: "[Куплет 1]\nночной город\n[Припев]\nnight ride",
    )

    result = lyrics_v8.generate_lyrics_v8("night ride", author="Reference Artist")

    assert result["author_style_used"] is False
    assert result["author_style"] == {
        "ok": False,
        "status": "profile_unavailable",
        "author": "Reference Artist",
    }
