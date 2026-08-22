from __future__ import annotations

import json

import modules.user_profile as profile_module
from app.ai import prompts


def _profile_payload() -> dict:
    return {
        "artist_name": "Private Artist Name",
        "history": [{"email": "private@example.test", "phone": "+79991234567"}],
        "creative_preferences": {
            "genres": ["drift phonk", "trap"],
            "language": "en",
            "text_style": "cinematic street poetry",
            "default_beat": {"bpm": 144, "key": "D minor", "mood": "neon, urgent"},
        },
    }


def test_creative_preferences_persist_without_needing_artist_identity(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(profile_module, "PROFILE_FILE", tmp_path / "user_profile.json")

    saved = profile_module.set_creative_preferences(
        genres=["drift phonk", "trap"],
        language="en",
        text_style="cinematic street poetry",
        default_beat={"bpm": 144, "key": "D minor", "mood": "neon, urgent"},
    )
    reloaded = profile_module.get_creative_preferences()
    persisted = json.loads(profile_module.PROFILE_FILE.read_text(encoding="utf-8"))

    assert saved == reloaded
    assert reloaded["genres"] == ["drift phonk", "trap"]
    assert reloaded["language"] == "en"
    assert reloaded["default_beat"]["bpm"] == 144
    assert "artist_name" not in persisted["creative_preferences"]


def test_prompts_change_from_preferences_but_exclude_pii_profile_fields() -> None:
    profile = _profile_payload()
    lyrics = prompts.build_lyrics_prompt("night", "phonk", 130, 2, False, user_profile=profile)
    metadata = prompts.build_metadata_prompt("night", "phonk", "short lyric", user_profile=profile)
    music = prompts.build_music_prompt("phonk", 130, "A minor", "dark", user_profile=profile)

    combined = "\n".join((lyrics, metadata, music))
    assert "drift phonk, trap" in combined
    assert "cinematic street poetry" in combined
    assert "144 BPM, D minor, neon, urgent" in combined
    assert "Private Artist Name" not in combined
    assert "private@example.test" not in combined
    assert "+79991234567" not in combined


def test_direct_identifiers_are_rejected_from_creative_preference_projection() -> None:
    profile = {
        "creative_preferences": {
            "genres": ["real@example.test", "phonk"],
            "language": "ru",
            "text_style": "call 79991234567",
            "default_beat": {"bpm": 130, "key": "A minor", "mood": "https://secret.example"},
        }
    }

    context = prompts.prompt_profile_context(profile)

    assert context["preferred_genres"] == "phonk"
    assert context["text_style"] == "direct, vivid, concise"
    assert context["default_mood"] == "dark, energetic"
