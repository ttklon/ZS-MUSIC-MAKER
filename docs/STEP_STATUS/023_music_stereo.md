# PLAN_v39 — ШАГ 023: music_stereo

## Решение

В AI-пайплайн добавлена отдельная optional-стадия `music_stereo`. Она получает только handle роли `music_stereo` из `SequentialAIRunner`, создаёт независимый файл `texture_stereo.wav` и не изменяет основной beat или mix на этапе интеграции. После завершения стадии runner выполняет штатный `registry.unload()`, поэтому модель не удерживается для следующих TTS/RVC-стадий.

| Проверяемый элемент | Фактическое состояние |
|---|---|
| Роль в реестре | Уже существовала: `audiocraft_musicgen`, `facebook/musicgen-stereo-medium`, оценка 8 GB VRAM. |
| Связь с pipeline | Добавлена `AIStage("music_stereo", "music_stereo", ...)` непосредственно после основной music-стадии. |
| Контракт handle | Вызываются `set_generation_params()` и `generate()`; tensor нормализуется к stereo WAV. |
| Артефакт | `output/<project>/texture_stereo.wav`, указан в `artefacts.texture_stereo`. |
| Отсутствующая модель | Возвращается явный `skipped` с reason; синтетическая подмена текстуры не создаётся. |

## Доказательства приёмки

Тест с контролируемым fake MusicGen handle подтвердил фактический вызов параметров, создание stereo WAV и корректный sample rate. Dry-run пайплайна подтвердил присутствие стадии в `RunReport` без загрузки модели. Расширенная проверка завершилась: `pytest tests/` — **64 passed**, `compileall` — успешно, AST-аудит импортов — **0**.

> Runtime-модель `audiocraft` в sandbox отсутствует. Поэтому **реальная генерация моделью не заявляется как выполненная**; она останется BLOCKED до установки зависимости и весов на целевом компьютере. Следующий ШАГ 024 добавит отдельную quality-валидацию и acceptance criteria для полученного файла.
