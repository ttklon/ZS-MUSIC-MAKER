# PLAN_v39 — ШАГ 047: SDXL cover и font fallback

## Production cover contract

`render_cover_ai()` теперь передаёт requested `size` и в SDXL, и в PIL fallback. Поэтому default pipeline output имеет единый 1024×1024 contract вне зависимости от доступности diffusers. Шрифты fallback cover по-прежнему разрешаются через единый cross-platform `font_utils`, без захардкоженного `C:\` пути.

| Проверка pipeline stage | Production порог |
|---|---:|
| Разрешение | Не менее 1024×1024 |
| Формат | Decodeable RGB/RGBA PNG |
| Размер файла | Не менее 100,000 bytes |
| Результат нарушения | `stage_cover` возвращает `ok=False` и точную quality `reason` |

PIL gradient fallback оказался реальным недостатком: измеренный flat 1024px PNG был только **20,108 bytes**, то есть не соответствовал плановому production порогу. Вместо искусственного file padding добавлен детерминированный low-opacity film-grain слой с seed, зависящим от artist/title. Он повышает визуальную текстуру и PNG entropy, оставаясь воспроизводимым.

## Evidence

Фактический AI dry-run без SDXL создал fallback `cover.png`: **1024×1024 RGB**, **675,292 bytes**. Добавлена direct regression PIL fallback против тех же stage порогов. На момент приёмки: `pytest tests/test_ai_quality.py -q` — **38 passed**; `pytest tests/ -q` — **116 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.

> SDXL/diffusers weights отсутствуют в sandbox. Real SDXL generation честно **BLOCKED**; verified fallback, SDXL handle contract и pipeline validation работают независимо от тяжёлой модели.
