"""Format checking for user-supplied ISRCs; this does not verify assignment.

An ISRC must be supplied by an authorized registrant or distributor. A
syntactically valid string is not evidence that it belongs to a recording.
"""
from __future__ import annotations

import re

_ISRC_RE = re.compile(r"^[A-Z]{2}(?:[A-Z0-9]{3}\d{7}|-[A-Z0-9]{3}-\d{2}-\d{5})$")


def is_valid_isrc(isrc: str | None) -> bool:
    """Check syntax and obvious placeholders, not ownership or registration."""
    if not isrc:
        return False
    value = str(isrc).upper().strip()
    if not _ISRC_RE.fullmatch(value):
        return False
    core = value.replace("-", "")
    return not (core.startswith("XX") or (core.endswith("00000") and core[5:7] == "00"))


def is_placeholder_isrc(isrc: str | None) -> bool:
    if not isrc:
        return True
    value = str(isrc).upper().replace("-", "").replace(" ", "")
    return "XXXXX" in value or value.startswith("XX") or (value.endswith("00000") and "00" in value[5:7])


def get_isrc(meta: dict, fallback: str = "") -> str:
    """Return only an explicitly supplied, syntactically valid code."""
    value = meta.get("isrc") or ""
    if not is_valid_isrc(value):
        return fallback
    core = str(value).upper().strip().replace("-", "")
    return f"{core[:2]}-{core[2:5]}-{core[5:7]}-{core[7:12]}"
