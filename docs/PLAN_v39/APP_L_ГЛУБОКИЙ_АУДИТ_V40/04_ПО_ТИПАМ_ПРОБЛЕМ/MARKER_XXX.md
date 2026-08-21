# MARKER_XXX — XXX в коде — требуется внимание

**Severity:** 🟡 MEDIUM
**Всего:** 2
**Как чинить:** Закрыть отдельным шагом.

## Все вхождения

### `app/core/isrc.py` — 1 шт.
- **строка 37** — # плейсхолдеры вида XX-XXX-00-00000 отбраковываем
  ```
         35 |     if not _ISRC_RE.match(s):
         36 |         return False
  >>>    37 |     # плейсхолдеры вида XX-XXX-00-00000 отбраковываем
         38 |     core = s.replace("-", "")
         39 |     if core.startswith("XX") or (core.endswith("00000") and core[5:7] == "00"):
  ```

### `modules/release_pack_full.py` — 1 шт.
- **строка 395** — # v39.4 (ШАГ 003): реальный ISRC вместо заглушки XX-XXX-00-00000
  ```
        393 |     title = meta.get("title", "ZS Track")
        394 |     artist = meta.get("artist", "ZS Artist")
  >>>   395 |     # v39.4 (ШАГ 003): реальный ISRC вместо заглушки XX-XXX-00-00000
        396 |     from app.core.isrc import get_isrc
        397 |     isrc = get_isrc(meta, fallback="UNREGISTERED")
  ```
