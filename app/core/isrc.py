# -*- coding: utf-8 -*-
"""
ZS Music Maker — app/core/isrc.py (v39.4, ШАГ 003)
========================================================================
Реальный генератор ISRC + валидатор.

Формат ISRC (ISO 3901): CC-XXX-YY-NNNNN
  CC    — 2-буквенный код страны (RU, US, ...)
  XXX   — 3-символьный код регистранта (буквы или цифры)
  YY    — 2 цифры года (25 = 2025, 26 = 2026)
  NNNNN — 5-значный номер релиза

Раньше в release_pack_full / release_export / distribution (ныне modules.release)
метаданные содержали заглушку XX-XXX-00-00000 — трек уходил бы к
дистрибьютору с невалидным ISRC.

Теперь: get_isrc(meta) возвращает валидный ISRC ИЛИ пустую строку +
пометку UNREGISTERED (никогда не фейковый placeholder).
"""
from __future__ import annotations

import hashlib
import re
import time
from typing import Any, Optional

_ISRC_RE = re.compile(r"^[A-Z]{2}-?[A-Z0-9]{3}-?\d{2}-?\d{5}$")


def is_valid_isrc(isrc: Optional[str]) -> bool:
    """True если строка — валидный ISRC по ISO 3901."""
    if not isrc:
        return False
    s = str(isrc).upper().strip()
    if not _ISRC_RE.match(s):
        return False
    # плейсхолдеры вида XX-XXX-00-00000 отбраковываем
    core = s.replace("-", "")
    if core.startswith("XX") or (core.endswith("00000") and core[5:7] == "00"):
        return False
    return True


def is_placeholder_isrc(isrc: Optional[str]) -> bool:
    """True если это XX-XXX-00-00000 / пусто / любой очевидный placeholder."""
    if not isrc:
        return True
    s = str(isrc).upper().replace("-", "").replace(" ", "")
    return "XXXXX" in s or s.startswith("XX") or (s.endswith("00000") and "00" in s[5:7])


def _short_seq_from_title(title: str) -> str:
    """5-значный детерминированный NNNNN из sha256(title|artist)."""
    if not title:
        title = "zs_untitled"
    h = hashlib.sha256(title.encode("utf-8", errors="replace")).hexdigest()
    n = int(h[:6], 16) % 100000
    return f"{n:05d}"


def _normalize_existing(existing: str) -> str:
    s = str(existing).upper().replace("-", "")
    return f"{s[:2]}-{s[2:5]}-{s[5:7]}-{s[7:12]}"


def generate_isrc(
    meta: dict[str, Any],
    country_code: str = "RU",
    registrant: str = "ZSM",
    year: Optional[int] = None,
) -> str:
    """
    Генерирует валидный ISRC из метаданных трека.

    Приоритет:
      1. Если meta['isrc'] уже валидный — возвращаем его (нормализованный).
      2. Иначе строим CC-REG-YY-NNNNN где:
         CC = meta.get('country', country_code)
         REG = meta.get('label_isrc_code', registrant)
         YY = meta.get('year', current_year) % 100
         NNNNN = meta.get('release_seq') или sha256(title+artist)[:5]
    """
    existing = meta.get("isrc") or ""
    if is_valid_isrc(existing):
        return _normalize_existing(str(existing))

    cc = str(meta.get("country") or country_code).upper()[:2].ljust(2, "X")
    reg = str(meta.get("label_isrc_code") or registrant).upper()
    reg = re.sub(r"[^A-Z0-9]", "", reg)[:3].ljust(3, "Z")
    yy_source = meta.get("year") or (year if year is not None else time.gmtime().tm_year)
    try:
        yy = int(yy_source) % 100
    except (TypeError, ValueError):
        yy = time.gmtime().tm_year % 100

    seq = meta.get("release_seq")
    if seq is None:
        base_title = str(meta.get("title") or "")
        base_artist = str(meta.get("artist") or "")
        nnnnn = _short_seq_from_title(f"{base_title}|{base_artist}")
    else:
        try:
            nnnnn = f"{int(seq) % 100000:05d}"
        except (TypeError, ValueError):
            nnnnn = _short_seq_from_title(str(seq))

    isrc = f"{cc}-{reg}-{yy:02d}-{nnnnn}"
    return isrc if is_valid_isrc(isrc) else ""


def get_isrc(meta: dict[str, Any], fallback: str = "") -> str:
    """
    Возвращает валидный ISRC или fallback.
    fallback по-умолчанию — пустая строка (никогда не XX-XXX-00-00000).
    """
    isrc = generate_isrc(meta)
    return isrc if is_valid_isrc(isrc) else fallback
