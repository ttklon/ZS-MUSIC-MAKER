# -*- coding: utf-8 -*-
"""
License / Provenance Manager v6.
Жёсткий фильтр CC0 / Royalty-Free / CC-BY по умолчанию.
Всё остальное блокируется до подтверждения пользователем.
"""
from __future__ import annotations
from dataclasses import dataclass

ALLOW_DEFAULT = {"cc0", "public domain", "royalty-free", "royalty free",
                 "cc-by", "cc by", "creative commons 0"}
NEEDS_ATTRIBUTION = {"cc-by", "cc by"}
BLOCK_UNLESS_CONFIRMED = {"cc-by-nc", "cc by-nc", "cc-by-sa", "unknown"}

@dataclass
class LicenseCheck:
    ok: bool
    needs_attribution: bool
    reason: str

def normalize(lic: str) -> str:
    return (lic or "").strip().lower().replace("_", " ")

def is_free_commercial(lic: str, allow_user_override: bool = False) -> bool:
    n = normalize(lic)
    if n in ALLOW_DEFAULT: return True
    if allow_user_override: return True
    return False

def check(lic: str, allow_user_override: bool = False) -> LicenseCheck:
    n = normalize(lic)
    if n in ALLOW_DEFAULT:
        return LicenseCheck(True, n in NEEDS_ATTRIBUTION, "allowed")
    if n in BLOCK_UNLESS_CONFIRMED:
        return LicenseCheck(allow_user_override, False,
                            "requires user confirmation")
    return LicenseCheck(allow_user_override, False, f"unknown license: {lic}")
