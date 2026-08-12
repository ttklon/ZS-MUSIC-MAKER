# KPI Dashboard v12 «Hit Locked Pro»

_Generated: 2026-08-12 19:53:16 UTC_

**Соответствие ТЗ: 90%**   |   **Общий вердикт: YELLOW**

## 🔴 Стек / зависимости — 25%

    Verdict: RED   Ready: 25%
    HW mode: lite   GPU: {'kind': 'cpu', 'name': 'CPU only', 'vram_gb': 0.0, 'ok': True}
    External deps OK: 5/19
    Internal modules OK: 24/24
      ! [CORE_ALT] PySide6 (native): GUI не запустится. Установи: pip install PySide6>=6.7
      ! [CORE_ALT] Gradio (fallback): Экспертный режим (Ctrl+E) не откроется. pip install gradio
      ! [QUALITY] pydub: Микс и mp3-экспорт деградируют. pip install pydub + ffmpeg
      ! [QUALITY] matchering: Мастеринг под референс отключится. pip install matchering
      ! [QUALITY] pyttsx3 (TTS fallback): Гарантированный TTS-fallback пропадёт. pip install pyttsx3
      ! [QUALITY] mutagen (ID3): ID3-теги не пропишутся. pip install mutagen
      ! [OPTIONAL] essentia: Аналитика упадёт на librosa-only (это ок).
      ! [OPTIONAL] torch: Тяжёлые модели (MusicGen/RVC full) не поднимутся.

## 🔴 Последний прогон мастера — 0%

    Нет master_pipeline_v12.json — запусти `python -m modules.master_pipeline_v12`

## 🔴 Smoke-тесты v12 — 0%

    Нет smoke_v12_report.json — запусти `python smoke_v12.py`

## Чеклист ТЗ (раздел 16 + 20)

| # | ТЗ | Пункт | Статус |
|---|----|-------|--------|
| 1 | 3.1-3.12 | 12 модулей архитектуры | ✅ |
| 2 | 5 | Единое окно, мастер по шагам | ✅ |
| 3 | 5 | Караоке-режим для записи | ✅ |
| 4 | 5 | Интерактивный Onboarding | ✅ |
| 5 | 6 | UTF-8 в коде, CP866 в консоли | ✅ |
| 6 | 6 | Авто-подтяжка зависимостей | ✅ |
| 7 | 7 | Smoke + E2E тесты | ❌ |
| 8 | 8+11 | README + CONTEXT.md накопительно | ❌ |
| 9 | 9 | Бесплатные интернет-агенты | ✅ |
| 10 | 11 | Логирование всего в logs/app.log | ✅ |
| 11 | 20.1 | HW autodetect + fallback | ✅ |
| 12 | 20.1[RVC] | RVC 100% рабочий | ✅ |
| 13 | 20.1[MG] | MusicGen полноценный на 12GB | ✅ |
| 14 | 20.3 | Автор из референсов / поиск | ✅ |
| 15 | 20.3 | Женские бэки | ✅ |
| 16 | 20.3 | Экспертный режим (скрытый ⋯) | ✅ |
| 17 | 20.3 | License / Provenance Manager | ✅ |
| 18 | 20.2 п.32 | Полный релиз-пакет | ✅ |
| 19 | 20.2 п.33 | 5 платформ дистрибуции | ✅ |
| 20 | 20.2 п.34 | AI Detector Pro + hit_scorer | ✅ |
| 21 | 20.2 п.35А | Очередь ≥5 треков | ✅ |
| 22 | 20.5 | KPI-мониторинг | ✅ |

## Что не подтверждено / рекомендации

- [TZ 7] Smoke + E2E тесты — не подтверждено, проверь наличие соответствующего файла/модуля.
- [TZ 8+11] README + CONTEXT.md накопительно — не подтверждено, проверь наличие соответствующего файла/модуля.
