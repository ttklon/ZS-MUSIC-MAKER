# PLAN_v39 — ШАГ 031: интеграция faster-whisper ASR

## Реализованный контракт

Роль `asr` уже зарегистрирована для `faster_whisper` и поддерживается общим загрузчиком Hugging Face. В dossier-обработке вызов вынесен в `transcribe_reference_audio()`, который вызывает handle с `language="ru"` и `beam_size=5`, объединяет сегменты и сохраняет transcript в `lyrics/<track_id>.txt`.

| Сценарий | Поведение |
|---|---|
| Пользователь уже предоставил lyrics | Они сохраняют приоритет; ASR не вызывается. |
| ASR handle доступен | Вызывается `transcribe`, transcript сохраняется с UTF-8. |
| ASR model unavailable | Optional path возвращает `skipped: asr unavailable`. |
| Нет audio/vocal stem | Возвращается `skipped: no audio for ASR`. |
| Handle выбросил ошибку | Возвращается `ok=False` с контекстом `ASR transcription failed`. |

## Доказательства

Fake ASR handle подтвердил точную передачу параметров, сбор двух сегментов в transcript и сохранение результата. Отдельный runtime-error test подтвердил честный failure. На момент приёмки: `pytest tests/` — **78 passed**, `compileall` — успешно, AST-аудит — **0**.

> `faster-whisper` и large-v3 weights не установлены в sandbox. Реальная транскрипция не заявляется как выполненная; интеграционный путь и надёжный отказ проверены отдельно.
