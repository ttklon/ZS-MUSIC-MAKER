# v39 — APP_G регрессионная приёмка

Дата прогона: 2026-08-22. Воспроизводимый runner: `python tools/regress_v39.py`. Он выполняет команды и выбранные contract tests, генерирует локальное machine-readable evidence `docs/REGRESS_v39.results.json` (игнорируемый runtime output) и возвращает non-zero при любом фактическом FAIL. Результат прогона: **13 PASS, 2 BLOCKED, 0 FAIL**.

> **Важно:** `PASS` у contract scenario означает, что указанная CLI/fallback/quality гарантия действительно выполнилась в sandbox. Это не означает real heavy-model inference. `BLOCKED` означает отсутствие runtime packages в среде; соответствующий command/status probe всё равно был выполнен.

| № | APP_G сценарий | Выполненная проверка | Итог | Фактическая граница |
|---:|---|---|---|---|
| 01 | Холодный старт | `main.py --ai-status` | PASS | Registry запускается и показывает availability без загрузки weights. |
| 02 | Новый AI-трек без models | `main.py --ai --dry-run --genre phonk --theme "night drive"` | PASS | Sequential dry-run завершился с явными fallbacks. |
| 03 | Полная установка 13 ролей | `main.py --ai-status` + heavy-runtime probe | BLOCKED | Нет `torch/audiocraft/demucs/TTS/diffusers/transformers/llama_cpp`; weights/GPU не проверялись. |
| 04 | Досье c локальными media/text | `test_local_folder_collector_merges_audio_and_txt_lyrics` | PASS | Collection contract подтверждён. |
| 05 | Досье без audio inference | `test_artist_dossier_aggregate_preserves_rich_schema_and_prompt_aliases` | PASS | Schema/aggregate сохраняются без fake ASR/Demucs output. |
| 06 | OOM/timeout stress | watchdog + VRAM-ceiling tests | PASS | Runner timeout и pre-stage budget rejection проверены; это не GPU 5-run measurement. |
| 07 | CPU-preferred mode | `ZSMM_PREFER_GPU=0 main.py --ai --dry-run` | PASS | CPU dry-run завершился без crash. |
| 08 | Прерванный pipeline | render queue cancellation boundary test | PASS | Pending/running cancellation обрабатывается без ложного completion. |
| 09 | Пустая тема | `main.py --ai --dry-run --theme ""` | PASS | Input прошёл diagnostic/fallback path без crash. |
| 10 | Трек 300 s через MusicGen | exact-duration beat adapter test + heavy probe | BLOCKED | Нет MusicGen runtime/weights; fake-handle contract не заменяет 300-second real generation. |
| 11 | Билингвал выключен | release lyrics rejection test | PASS | Invalid/filler structure отклоняется quality gate. |
| 12 | User lines | release lyrics user-lines contract test | PASS | Release lyric validator требует структуру и user-lines. |
| 13 | RVC без model | RVC runtime-error/no-pitch-fallback test | PASS | Absence model не заменяется pitch-shift обманом. |
| 14 | CLAP mismatch | mismatched logits/vocabulary test | PASS | Неконсистентный tag output отклоняется. Real CLAP inference остаётся BLOCKED. |
| 15 | Регенерация/session recovery | versioned manifest persistence test | PASS | AI run сохраняет resumable manifest contract. |

## Блокеры окружения

| Сценарий | Почему BLOCKED | Как снять блокировку на целевой машине |
|---|---|---|
| 03 | Heavy Python runtimes и model weights отсутствуют; sandbox не имеет GPU. | Установить documented optional dependencies, pull/verify role-scoped weights, выполнить на GPU host с достаточной VRAM. |
| 10 | MusicGen runtime/weights отсутствуют. | Установить `audiocraft`, корректные torch/CUDA packages и approved MusicGen weights; выполнить отдельный 300-second soak test с VRAM telemetry. |

## Результат

Критерий плана «не менее 10 из 15 зелёные» превышен: **13 из 15** проверок завершились PASS и **0** дали unexpected FAIL. Два сценария не выданы за реальные: они записаны BLOCKED с environment reasons. Детальный stdout/stderr tail и return code каждого вызова доступны в локально генерируемом `REGRESS_v39.results.json`; versioned evidence — эта таблица, STEP_STATUS и SESSION_LOG.
