# PLAN_v39 — ШАГ 038: метрики, fallback и валидация SDXL cover_art

## Quality contract

`validate_cover_artifact()` проверяет готовый PNG независимо от его источника. Успешный SDXL-рендер или явно маркированный PIL fallback не может считаться готовым, пока файл не существует, не декодируется, не имеет минимум 512×512 пикселей и не использует RGB/RGBA mode.

| Проверка | Причина отклонения |
|---|---|
| Файл существует и содержит данные | `cover file is missing or too small` |
| Pillow декодирует изображение | `cover file is unreadable` |
| Ширина и высота ≥ 512 | `cover resolution is below minimum` |
| Цветовой режим RGB/RGBA | `cover color mode is unsupported` |

## Доказательства

Регрессии проверяют валидный RGB 512×512 PNG, недостаточное разрешение 128×128 и grayscale PNG. На момент приёмки: `pytest tests/` — **88 passed**, `compileall` — успешно, AST-аудит — **0**.

> SDXL weights отсутствуют в sandbox. Gate проверяет фактический PNG output и не служит заявлением о доступности диффузионной модели.
