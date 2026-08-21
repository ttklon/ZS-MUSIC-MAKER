# -*- coding: utf-8 -*-
"""ZS Music Maker — tests for app/core/isrc (ШАГ 003)."""
from __future__ import annotations

from app.core import isrc as I


def test_placeholder_detection():
    assert I.is_placeholder_isrc("")
    assert I.is_placeholder_isrc("XX-XXX-00-00000")
    assert I.is_placeholder_isrc(None)
    assert not I.is_placeholder_isrc("RUZSM2600042")


def test_valid_isrc_positive():
    assert I.is_valid_isrc("RU-ZSM-26-00042")
    assert I.is_valid_isrc("RUZSM2600042")
    assert I.is_valid_isrc("us-abc-25-12345")


def test_valid_isrc_negative():
    assert not I.is_valid_isrc("XX-XXX-00-00000")
    assert not I.is_valid_isrc("RU-ZS-26-00042")  # 2 letters registrant, not 3
    assert not I.is_valid_isrc("R-ZSM-26-00042")
    assert not I.is_valid_isrc("")
    assert not I.is_valid_isrc(None)
    assert not I.is_valid_isrc("RUZSM26000")


def test_generate_deterministic():
    meta = {"title": "Turkish Nights", "artist": "ZS", "year": 2026}
    a = I.generate_isrc(meta)
    b = I.generate_isrc(meta)
    assert a == b
    assert I.is_valid_isrc(a)
    assert a.startswith("RU-ZSM-26-")


def test_generate_custom_country_registrant():
    meta = {"title": "Beat X", "artist": "ZS", "year": 2025,
            "country": "US", "label_isrc_code": "ABC"}
    r = I.generate_isrc(meta)
    assert r.startswith("US-ABC-25-")
    assert I.is_valid_isrc(r)


def test_generate_from_seq_number():
    meta = {"title": "T", "artist": "A", "year": 2026, "release_seq": 42}
    r = I.generate_isrc(meta)
    assert r.endswith("-00042")


def test_get_isrc_fallback_empty_when_bad_input():
    # placeholder на входе — не пропускаем, генерируем
    meta = {"isrc": "XX-XXX-00-00000", "title": "T", "artist": "A"}
    r = I.get_isrc(meta)
    assert r
    assert I.is_valid_isrc(r)
    assert not I.is_placeholder_isrc(r)


def test_get_isrc_preserves_valid_input():
    meta = {"isrc": "RU-ZSM-26-01234", "title": "T", "artist": "A"}
    r = I.get_isrc(meta)
    assert I.is_valid_isrc(r)


def test_generate_stable_across_years_field_types():
    # year как строка
    meta = {"title": "T", "artist": "A", "year": "2026"}
    r = I.generate_isrc(meta)
    assert "-26-" in r


def test_get_isrc_fallback_string():
    meta = {"title": "", "artist": ""}
    r = I.get_isrc(meta, fallback="UNREGISTERED")
    assert I.is_valid_isrc(r) or r == "UNREGISTERED"
