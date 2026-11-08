# -*- coding: utf-8 -*-
"""app/core/license_manager.py: единственный фильтр лицензий сэмплов.

Тесты держат политику: CC0/PD/RF/CC-BY проходят, NC/SA/unknown блокируются,
и «пояснение в скобках» не превращает законную лицензию в неизвестную.
"""

from __future__ import annotations

import pytest

from app.core import license_manager as lm


class TestNormalize:
    @pytest.mark.parametrize(
        "raw",
        [
            "https://creativecommons.org/publicdomain/zero/1.0/",
            "http://creativecommons.org/publicdomain/mark/1.0/",
        ],
    )
    def test_public_domain_urls(self, raw) -> None:
        assert lm.normalize(raw) == "public domain"

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("https://creativecommons.org/licenses/by/4.0/", "cc-by"),
            ("https://creativecommons.org/licenses/by-nc/4.0/", "cc-by-nc"),
            ("https://creativecommons.org/licenses/by-sa/3.0/", "cc-by-sa"),
            ("https://creativecommons.org/licenses/by-nc-sa/4.0/", "cc-by-nc"),
            ("https://creativecommons.org/licenses/by-nc-nd/4.0/", "cc-by-nc"),
            ("https://creativecommons.org/publicdomain/zero/1.0/", "public domain"),
        ],
    )
    def test_creative_commons_urls(self, raw, expected) -> None:
        assert lm.normalize(raw) == expected

    def test_cc0_with_version_suffix(self) -> None:
        # API иногда отдают "CC0/1.0": слэш уводит в ветку URL, но лицензия
        # остаётся CC0 и не должна становиться "unknown".
        assert lm.normalize("CC0/1.0") == "cc0"

    def test_unknown_url_is_unknown(self) -> None:
        assert lm.normalize("https://example.com/terms") == "unknown"

    def test_underscores_become_spaces(self) -> None:
        assert lm.normalize("public_domain") == "public domain"

    def test_parentheses_are_not_part_of_the_name(self) -> None:
        # Именно этот вид отдаёт agents/sample_hunter/web.py для Pixabay.
        assert lm.normalize("Royalty-Free (Pixabay)") == "royalty-free"

    def test_attribution_note_in_parentheses_is_dropped(self) -> None:
        assert lm.normalize("CC0 (public domain, no attribution)") == "cc0"

    def test_none_is_empty(self) -> None:
        assert lm.normalize(None) == ""


class TestIsFreeCommercial:
    @pytest.mark.parametrize(
        "lic",
        ["CC0", "cc0", "Creative Commons 0", "Public Domain", "royalty-free",
         "Royalty Free", "CC-BY", "cc by", "Royalty-Free (Pixabay)"],
    )
    def test_allowed_licenses(self, lic) -> None:
        assert lm.is_free_commercial(lic) is True

    @pytest.mark.parametrize(
        "lic",
        ["CC-BY-NC", "CC-BY-SA", "unknown", "", "All rights reserved",
         "https://example.com/custom"],
    )
    def test_blocked_licenses(self, lic) -> None:
        assert lm.is_free_commercial(lic) is False

    def test_user_override_opens_everything(self) -> None:
        assert lm.is_free_commercial("CC-BY-NC", allow_user_override=True) is True

    def test_blocked_reason_names_the_license(self) -> None:
        result = lm.check("CC-BY-NC")

        assert result.ok is False
        assert result.reason == "requires user confirmation"

    def test_cc_by_needs_attribution(self) -> None:
        result = lm.check("https://creativecommons.org/licenses/by/4.0/")

        assert result.ok is True and result.needs_attribution is True

    def test_cc0_needs_no_attribution(self) -> None:
        assert lm.check("CC0").needs_attribution is False

    def test_unknown_licence_is_named_in_reason(self) -> None:
        assert lm.check("Musicbed EULA").reason == "unknown license: Musicbed EULA"

    def test_override_is_recorded_for_unknown(self) -> None:
        assert lm.check("Musicbed EULA", allow_user_override=True).ok is True
