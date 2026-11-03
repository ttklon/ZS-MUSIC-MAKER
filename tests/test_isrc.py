"""ISRC syntax is not proof of assignment; never invent codes."""
from app.core import isrc as I


def test_isrc_syntax_and_placeholders():
    assert I.is_valid_isrc("RU-ZSM-26-00042")
    assert I.is_valid_isrc("ruzsm2600042")
    for invalid in ("XX-XXX-00-00000", "RU-ZS-26-00042", "R-ZSM-26-00042", "", None, "RU-ZSM2600042"):
        assert not I.is_valid_isrc(invalid)
    assert I.is_placeholder_isrc("XX-XXX-00-00000")


def test_only_explicit_code_is_returned():
    assert I.get_isrc({"title": "T", "artist": "A", "year": 2026}) == ""
    assert I.get_isrc({"isrc": "XX-XXX-00-00000"}) == ""
    assert I.get_isrc({}, fallback="UNREGISTERED") == "UNREGISTERED"
    assert I.get_isrc({"isrc": "ruzsm2600042"}) == "RU-ZSM-26-00042"
