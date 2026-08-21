from __future__ import annotations

from app.ai import prompts


def test_every_versioned_prompt_asset_is_mapped_and_renderable() -> None:
    disk_names = {path.name for path in prompts.PROMPTS_DIR.glob("*.prompt.txt")}

    assert disk_names == set(prompts.prompt_asset_names())
    assert prompts.validate_prompt_catalog() == []
    for name in prompts.prompt_asset_names():
        rendered = prompts.render_prompt_asset(name)
        assert rendered
        assert "{" not in rendered
        assert "}" not in rendered


def test_prompt_assets_have_current_role_owners() -> None:
    roles = {prompts.PROMPT_ASSETS[name] for name in prompts.prompt_asset_names()}

    assert roles == {"analysis", "cover_art", "lyrics", "metadata", "trend_analysis"}
    assert len(prompts.prompt_assets_for_role("lyrics")) == 4
    assert len(prompts.prompt_assets_for_role("metadata")) == 8


def test_builders_include_versioned_role_assets_without_losing_user_lines() -> None:
    lyrics = prompts.build_lyrics_prompt(
        theme="night drive",
        genre="phonk",
        bpm=130,
        n_verses=2,
        bilingual=False,
        user_lines=["Мой свет горит в окне"],
    )
    metadata = prompts.build_metadata_prompt("night drive", "phonk", "short lyric")
    cover = prompts.build_cover_prompt("Night", "Artist", "phonk", "dark")

    assert "Мой свет горит в окне" in lyrics
    assert prompts.load_prompt_asset("lyrics_verse.prompt.txt").splitlines()[3] in lyrics
    assert prompts.render_prompt_asset(
        "track_title.prompt.txt", theme="night drive", genre="phonk", language="ru"
    ) in metadata
    assert "Album cover for song 'Night'" in cover


def test_unknown_prompt_asset_is_rejected() -> None:
    try:
        prompts.load_prompt_asset("../../secret.txt")
    except KeyError as exc:
        assert "Unknown prompt asset" in str(exc)
    else:
        raise AssertionError("path traversal name must be rejected")
