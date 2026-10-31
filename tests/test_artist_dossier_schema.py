from __future__ import annotations

import json

import pytest

from modules.artist_dossier import (
    ArtistEntry,
    DossierManager,
    artist_dossier_schema,
    normalize_artist_dossier,
    validate_artist_dossier,
)


def _valid_dossier() -> dict[str, object]:
    return {
        "bio": "Независимый артист с ночной phonk эстетикой.",
        "themes": ["night drive"],
        "slang": ["ride"],
        "flow": "Ритмичный речитатив",
        "analogs": ["underground phonk"],
        "core_themes": ["night drive"],
        "lexicon": ["ride"],
        "signature_tricks": ["короткий хук"],
        "avoid": ["копирование референса"],
    }


def test_versioned_schema_and_normalized_dossier_validate() -> None:
    schema = artist_dossier_schema()
    normalized = normalize_artist_dossier(_valid_dossier())

    assert schema["properties"]["schema_version"]["const"] == 1
    assert validate_artist_dossier(normalized)["ok"] is True


def test_incomplete_completed_dossier_is_rejected_with_reason() -> None:
    result = validate_artist_dossier({"schema_version": 1, "bio": "only bio"})

    assert result["ok"] is False
    assert "missing artist dossier fields" in result["reason"]


def test_legacy_incomplete_dossier_migrates_to_explicit_deferred(tmp_path) -> None:
    root = tmp_path / "artist_dossier"
    legacy_dir = root / "legacy"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "artist.json").write_text(
        json.dumps(
            {
                "artist": "Legacy",
                "slug": "legacy",
                "dossier": {"bio": "incomplete historic payload"},
            }
        ),
        encoding="utf-8",
    )

    entry = DossierManager(root=root)._load_artist("legacy")

    assert entry is not None
    assert entry.dossier["deferred"] is True
    assert "legacy artist dossier deferred" in entry.dossier["note"]


def test_manager_rejects_invalid_new_completed_dossier_on_save(tmp_path) -> None:
    manager = DossierManager(root=tmp_path / "artist_dossier")
    entry = ArtistEntry(artist="Bad", slug="bad", dossier={"bio": "missing fields"})

    with pytest.raises(ValueError, match="artist dossier save rejected"):
        manager._save_artist(entry)
