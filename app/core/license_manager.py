"""
License / Provenance Manager v6.
Жёсткий фильтр CC0 / Royalty-Free / CC-BY по умолчанию.
Всё остальное блокируется до подтверждения пользователем.
"""

from __future__ import annotations

from dataclasses import dataclass

ALLOW_DEFAULT = {
    "cc0",
    "public domain",
    "royalty-free",
    "royalty free",
    "cc-by",
    "cc by",
    "creative commons 0",
}
NEEDS_ATTRIBUTION = {"cc-by", "cc by"}
BLOCK_UNLESS_CONFIRMED = {"cc-by-nc", "cc by-nc", "cc-by-sa", "unknown"}


@dataclass
class LicenseCheck:
    ok: bool
    needs_attribution: bool
    reason: str


def normalize(lic: str) -> str:
    n = (lic or "").strip().lower().replace("_", " ")
    # Пояснение в скобках — не часть названия: Pixabay отдаётся как
    # "Royalty-Free (Pixabay)", и такой хит блокировался собственным гейтом
    # sample_hunter, то есть источник не мог дать ни одного результата.
    if "(" in n:
        n = n.split("(", 1)[0].strip()
    # v34 FIX: лицензии часто приходят как URL (archive.org licenseurl,
    # freesound API). Нормализуем URL → каноническое имя, иначе
    # publicdomain-URL ошибочно попадал в «unknown» и блокировался.
    if "/" in n or "creativecommons.org" in n or "licenses" in n:
        if "publicdomain" in n or "public-domain" in n:
            return "public domain"
        if "by-nc-sa" in n or "by-nc-nd" in n or "by-nc" in n:
            return "cc-by-nc"
        if "by-sa" in n:
            return "cc-by-sa"
        if n.rstrip("/").endswith("/by") or "/by/" in n:
            return "cc-by"
        if "zero" in n or "cc0" in n:
            return "cc0"
        return "unknown"
    return n


def is_free_commercial(lic: str, allow_user_override: bool = False) -> bool:
    n = normalize(lic)
    if n in ALLOW_DEFAULT:
        return True
    if allow_user_override:
        return True
    return False


def check(lic: str, allow_user_override: bool = False) -> LicenseCheck:
    n = normalize(lic)
    if n in ALLOW_DEFAULT:
        return LicenseCheck(True, n in NEEDS_ATTRIBUTION, "allowed")
    if n in BLOCK_UNLESS_CONFIRMED:
        return LicenseCheck(allow_user_override, False, "requires user confirmation")
    return LicenseCheck(allow_user_override, False, f"unknown license: {lic}")
