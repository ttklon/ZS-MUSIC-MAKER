# PLAN_v39 execution report

Status is derived only from local `git log` subjects containing `ШАГ NNN`; `PENDING` does not assess code quality and `COMMITTED` is not a substitute for documented acceptance evidence.

Plan headings: **100**. Git-evidenced commits: **85**. Pending headings: **15**.

| Step | Plan item | Git-evidence status | Commit evidence |
|---:|---|---|---|
| 001 | Фикс неиспользуемых импортов во всех .py | COMMITTED | `77cfc122` v39.4 PLAN_v39 ШАГИ 001-005: dead-imports cleanup, font_utils (no hardcoded C:\Windows\Fonts), real ISRC generator (no XX-XXX-00-00000), unified stage-logging (stage=/duration_ms=), honest except-logs; +tests/test_isrc.py +tests/test_font_utils.py (30/30 PASS) |
| 002 | Устранение hardcoded путей | COMMITTED | `77cfc122` v39.4 PLAN_v39 ШАГИ 001-005: dead-imports cleanup, font_utils (no hardcoded C:\Windows\Fonts), real ISRC generator (no XX-XXX-00-00000), unified stage-logging (stage=/duration_ms=), honest except-logs; +tests/test_isrc.py +tests/test_font_utils.py (30/30 PASS) |
| 003 | ISRC: генерация вместо заглушек XX-XXX-00-00000 | COMMITTED | `77cfc122` v39.4 PLAN_v39 ШАГИ 001-005: dead-imports cleanup, font_utils (no hardcoded C:\Windows\Fonts), real ISRC generator (no XX-XXX-00-00000), unified stage-logging (stage=/duration_ms=), honest except-logs; +tests/test_isrc.py +tests/test_font_utils.py (30/30 PASS) |
| 004 | Логирование: единый app_logger через весь код | COMMITTED | `77cfc122` v39.4 PLAN_v39 ШАГИ 001-005: dead-imports cleanup, font_utils (no hardcoded C:\Windows\Fonts), real ISRC generator (no XX-XXX-00-00000), unified stage-logging (stage=/duration_ms=), honest except-logs; +tests/test_isrc.py +tests/test_font_utils.py (30/30 PASS) |
| 005 | Обработка исключений: убрать молчаливые except | COMMITTED | `77cfc122` v39.4 PLAN_v39 ШАГИ 001-005: dead-imports cleanup, font_utils (no hardcoded C:\Windows\Fonts), real ISRC generator (no XX-XXX-00-00000), unified stage-logging (stage=/duration_ms=), honest except-logs; +tests/test_isrc.py +tests/test_font_utils.py (30/30 PASS) |
| 006 | Зависимости: дифф requirements vs реальные импорты | COMMITTED | `8ea54fb5` v39.5 PLAN_v39 ШАГИ 006-010: requirements sync by AST audit, config/settings.py (env+.env, wired into --version/orchestrator_ai), CI audit job, version single-source via app/version_info.py, tools/ast_dead_imports.py + full cleanup (0 dead-imports), +12 tests (46 total PASS) |
| 007 | Конфиг: .env и конфиг-схема вместо разбросанных констант | COMMITTED | `8ea54fb5` v39.5 PLAN_v39 ШАГИ 006-010: requirements sync by AST audit, config/settings.py (env+.env, wired into --version/orchestrator_ai), CI audit job, version single-source via app/version_info.py, tools/ast_dead_imports.py + full cleanup (0 dead-imports), +12 tests (46 total PASS) |
| 008 | CI: покрыть тесты в GitHub Actions | COMMITTED | `8ea54fb5` v39.5 PLAN_v39 ШАГИ 006-010: requirements sync by AST audit, config/settings.py (env+.env, wired into --version/orchestrator_ai), CI audit job, version single-source via app/version_info.py, tools/ast_dead_imports.py + full cleanup (0 dead-imports), +12 tests (46 total PASS) |
| 009 | Версионирование: версия из одного источника | COMMITTED | `8ea54fb5` v39.5 PLAN_v39 ШАГИ 006-010: requirements sync by AST audit, config/settings.py (env+.env, wired into --version/orchestrator_ai), CI audit job, version single-source via app/version_info.py, tools/ast_dead_imports.py + full cleanup (0 dead-imports), +12 tests (46 total PASS) |
| 010 | Мёртвый код: повторный AST-замер и добивка | COMMITTED | `8ea54fb5` v39.5 PLAN_v39 ШАГИ 006-010: requirements sync by AST audit, config/settings.py (env+.env, wired into --version/orchestrator_ai), CI audit job, version single-source via app/version_info.py, tools/ast_dead_imports.py + full cleanup (0 dead-imports), +12 tests (46 total PASS) |
| 011 | Граф импортов: тест на циклы | COMMITTED | `74c457b6` v39.6 PLAN_v39 ШАГ 011: import-cycle guard и stereo smoke fix |
| 012 | Структура: вынести тяжёлые модули из веток-легаси | COMMITTED | `88233ea3` v39.7 PLAN_v39 ШАГ 012: legacy-off и God checkpoints |
| 013 | Индексы и кэши: сборка и валидация | COMMITTED | `89b16b08` v39.8 PLAN_v39 ШАГИ 013-017: data audit и LLM quality |
| 014 | Репозиторий: .gitignore-полировка, размер | COMMITTED | `89b16b08` v39.8 PLAN_v39 ШАГИ 013-017: data audit и LLM quality |
| 015 | РОЛЬ lyrics_llm: интеграция (Qwen2.5-14B-Instruct GGUF Q4_K_M) | COMMITTED | `89b16b08` v39.8 PLAN_v39 ШАГИ 013-017: data audit и LLM quality |
| 016 | РОЛЬ lyrics_llm: метрики, fallback, валидация выхода (Qwen2.5-14B-Instruct GGUF Q4_K_M) | COMMITTED | `89b16b08` v39.8 PLAN_v39 ШАГИ 013-017: data audit и LLM quality |
| 017 | РОЛЬ analysis_llm: интеграция (Qwen2.5-14B-Instruct GGUF Q4_K_M) | COMMITTED | `89b16b08` v39.8 PLAN_v39 ШАГИ 013-017: data audit и LLM quality |
| 018 | РОЛЬ analysis_llm: метрики, fallback, валидация выхода (Qwen2.5-14B-Instruct GGUF Q4_K_M) | COMMITTED | `a47440ca` v39.9 PLAN_v39 ШАГИ 018-022: metadata и audio quality |
| 019 | РОЛЬ metadata_llm: интеграция (Llama-3.1-8B-Instruct Q5_K_M) | COMMITTED | `a47440ca` v39.9 PLAN_v39 ШАГИ 018-022: metadata и audio quality |
| 020 | РОЛЬ metadata_llm: метрики, fallback, валидация выхода (Llama-3.1-8B-Instruct Q5_K_M) | COMMITTED | `a47440ca` v39.9 PLAN_v39 ШАГИ 018-022: metadata и audio quality |
| 021 | РОЛЬ music_generation: интеграция (MusicGen-large 3.3B) | COMMITTED | `a47440ca` v39.9 PLAN_v39 ШАГИ 018-022: metadata и audio quality |
| 022 | РОЛЬ music_generation: метрики, fallback, валидация выхода (MusicGen-large 3.3B) | COMMITTED | `a47440ca` v39.9 PLAN_v39 ШАГИ 018-022: metadata и audio quality |
| 023 | РОЛЬ music_stereo: интеграция (MusicGen-stereo-medium) | COMMITTED | `c55344fd` PLAN_v39 ШАГ 023: интеграция music_stereo |
| 024 | РОЛЬ music_stereo: метрики, fallback, валидация выхода (MusicGen-stereo-medium) | COMMITTED | `b14e5451` PLAN_v39 ШАГ 024: quality gate music_stereo |
| 025 | РОЛЬ tts_vocal: интеграция (XTTS-v2 (Coqui TTS)) | COMMITTED | `3decb0a0` PLAN_v39 ШАГ 025: интеграция XTTS-v2 |
| 026 | РОЛЬ tts_vocal: метрики, fallback, валидация выхода (XTTS-v2 (Coqui TTS)) | COMMITTED | `63f9e59b` PLAN_v39 ШАГ 026: quality и fallback XTTS-v2 |
| 027 | РОЛЬ vocal_rvc: интеграция (RVC v2 (файл .pth в models/rvc)) | COMMITTED | `488163dd` PLAN_v39 ШАГ 027: интеграция RVC v2 |
| 028 | РОЛЬ vocal_rvc: метрики, fallback, валидация выхода (RVC v2 (файл .pth в models/rvc)) | COMMITTED | `fa4656d8` PLAN_v39 ШАГ 028: quality gate RVC v2 |
| 029 | РОЛЬ stem_splitter: интеграция (Demucs htdemucs) | COMMITTED | `08272c49` PLAN_v39 ШАГ 029: интеграция Demucs htdemucs |
| 030 | РОЛЬ stem_splitter: метрики, fallback, валидация выхода (Demucs htdemucs) | COMMITTED | `5fdab625` PLAN_v39 ШАГ 030: quality gate Demucs |
| 031 | РОЛЬ asr: интеграция (faster-whisper large-v3) | COMMITTED | `65e39fb7` PLAN_v39 ШАГ 031: интеграция faster-whisper ASR |
| 032 | РОЛЬ asr: метрики, fallback, валидация выхода (faster-whisper large-v3) | COMMITTED | `0c3788c1` PLAN_v39 ШАГ 032: quality и fallback ASR |
| 033 | РОЛЬ audio_tagger: интеграция (CLAP (laion/clap)) | COMMITTED | `5fd368f0` PLAN_v39 ШАГ 033: интеграция CLAP audio_tagger |
| 034 | РОЛЬ audio_tagger: метрики, fallback, валидация выхода (CLAP (laion/clap)) | COMMITTED | `18ceb8ef` PLAN_v39 ШАГ 034: quality и fallback CLAP |
| 035 | РОЛЬ essentia: интеграция (essentia-tensorflow) | COMMITTED | `3623c52b` PLAN_v39 ШАГ 035: интеграция essentia DSP |
| 036 | РОЛЬ essentia: метрики, fallback, валидация выхода (essentia-tensorflow) | COMMITTED | `8fe96c87` PLAN_v39 ШАГ 036: quality и fallback DSP |
| 037 | РОЛЬ cover_art: интеграция (SDXL Base 1.0 fp16) | COMMITTED | `0dc4251b` PLAN_v39 ШАГ 037: интеграция SDXL cover_art |
| 038 | РОЛЬ cover_art: метрики, fallback, валидация выхода (SDXL Base 1.0 fp16) | COMMITTED | `baa52757` PLAN_v39 ШАГ 038: quality и fallback SDXL cover |
| 039 | РОЛЬ mastering_ai: интеграция (matchering 2.0) | COMMITTED | `87222727` PLAN_v39 ШАГ 039: интеграция mastering_ai matchering |
| 040 | РОЛЬ mastering_ai: метрики, fallback, валидация выхода (matchering 2.0) | COMMITTED | `833b7a3b` PLAN_v39 ШАГ 040: quality gate mastering_ai |
| 041 | Оркестратор: sequential runner с OOM-защитой и таймаутами | COMMITTED | `43e2252c` PLAN_v39 ШАГ 041: timeout и OOM защита runner |
| 042 | Pull-скрипт: полный разбор весов всех 13 ролей | COMMITTED | `5cf90f9c` PLAN_v39 ШАГ 042: pull и verify 13 AI ролей |
| 043 | Досье артиста: полный конвейер demucs→whisper→librosa→CLAP→LLM | COMMITTED | `3a3d610c` PLAN_v39 ШАГ 043: полный artist dossier pipeline |
| 044 | Тексты: AI-first через lyrics_gen_ai + досье | COMMITTED | `73bf8035` PLAN_v39 ШАГ 044: AI-first lyrics и quality gate |
| 045 | Бит: beat_gen_ai как основная ветка stage_music | COMMITTED | `684304cb` PLAN_v39 ШАГ 045: интеграция beat_gen_ai |
| 046 | Вокал: voice_synth_ai + RVC-конверсия | COMMITTED | `ec4d3db8` PLAN_v39 ШАГ 046: XTTS и RVC интеграция |
| 047 | Обложка: SDXL fp16 + шрифт fallback | COMMITTED | `c55f4392` PLAN_v39 ШАГ 047: production SDXL cover fallback |
| 048 | Мастеринг: matchering + loudness-нормализация | COMMITTED | `07a2cb1f` PLAN_v39 ШАГ 048: loudness normalization mastering |
| 049 | ASR/демикс/теги: замыкание досье-конвейера | COMMITTED | `8266dd5b` PLAN_v39 ШАГ 049: persistence dossier pipeline |
| 050 | Стерео-текстуры: интро/пэды/переходы | COMMITTED | `8b766234` PLAN_v39 ШАГ 050: стерео текстуры в mix |
| 051 | GUI: главное окно и статус моделей | COMMITTED | `f1bcd706` PLAN_v39 ШАГ 051: GUI статус AI ролей |
| 052 | Очереди и параллельность: render_queue | COMMITTED | `676260d6` PLAN_v39 ШАГ 052: render queue и отмена |
| 053 | Сохранение сессий и треков: schema + миграции | COMMITTED | `3f741df7` PLAN_v39 ШАГ 053: schema сессий и manifest |
| 054 | Пресеты жанров: валидация и расширение | COMMITTED | `83620c18` PLAN_v39 ШАГ 054: валидация genre presets |
| 055 | Phonk-движок: v1 vs v2 унификация | COMMITTED | `a4b9676c` PLAN_v39 ШАГ 055: унификация phonk engine |
| 056 | Kараоке/вокал-банк: voice_vault и karaoke_reсorder | COMMITTED | `ecd59997` PLAN_v39 ШАГ 056: Voice Vault и speaker WAV |
| 057 | Ремиксы и сепарация: качество стемов | COMMITTED | `6a72be82` PLAN_v39 ШАГ 057: безопасный remix workflow |
| 058 | Экспорт и релиз: multitrack, WAV/MP3/FLAC, ID3 | COMMITTED | `24185590` PLAN_v39 ШАГ 058: релиз экспорт и fingerprints |
| 059 | Обучение RVC-моделей: rvc_trainer pipeline | COMMITTED | `892d9366` PLAN_v39 ШАГ 059: честный RVC training pipeline |
| 060 | Хит-скоринг: метрики и фидбек | COMMITTED | `66914a88` PLAN_v39 ШАГ 060: hit scoring CLI |
| 061 | AI-детектор и полировка достоверности | COMMITTED | `27018051` PLAN_v39 ШАГ 061: AI detector risk contract |
| 062 | Установщик: install.py и .bat-обвязка | COMMITTED | `4147512a` PLAN_v39 ШАГ 062: hardening installer |
| 063 | Апдейтер: самопроверка и автообновление | COMMITTED | `012bdecd` PLAN_v39 ШАГ 063: безопасный update status |
| 064 | Безопасность: запрет shell, валидация путей, secret-ы | COMMITTED | `c4d69bc7` PLAN_v39 ШАГ 064: security path и redaction |
| 065 | Перф: профилирование и кэши | COMMITTED | `221ade78` PLAN_v39 ШАГ 065: cache hit scorer |
| 066 | Тесты: расширить с 16 до >= 60 | COMMITTED | `9e95b64b` PLAN_v39 ШАГ 066: расширение test suite |
| 067 | CI+CD: бинарники и артефакты | COMMITTED | `ae9155c7` PLAN_v39 ШАГ 067: CI CD release artifacts |
| 068 | Документация: README/INSTALL/CHANGELOG/DEVELOPER_GUIDE | COMMITTED | `a1ee88d4` PLAN_v39 ШАГ 068: v39 documentation |
| 069 | Roadmap и метрики проекта: PROJECT_STATE | COMMITTED | `65c57c9e` PLAN_v39 ШАГ 069: factual project state |
| 070 | Регресс-сценарии: 15 сквозных прогонов | COMMITTED | `5d3b850f` PLAN_v39 ШАГ 070: app g regression matrix |
| 071 | Golden-тесты звука: waveform-сравнение | COMMITTED | `278be241` PLAN_v39 ШАГ 071: audio golden regression |
| 072 | Релиз v39: чеклист и тег | PENDING | — |
| 073 | Отчёт по исполнению плана | PENDING | — |
| 074 | Память плана: замер и финализация | PENDING | — |
| 075 | Ревизия tools/: единый CLI-стиль (argparse + exit-коды + логи) | COMMITTED | `d3df415d` PLAN_v39 ШАГ 075: unify tools cli contracts |
| 076 | Ревизия data/prompts: привязка к ролям | COMMITTED | `aa7e90a3` PLAN_v39 ШАГ 076: bind prompt assets to roles |
| 077 | lyrics_gen_v8: deprecated-флаг, код оставить (wizard-совместимость) | COMMITTED | `529fc057` PLAN_v39 ШАГ 077: deprecate legacy lyrics adapter |
| 078 | llm_clients_v15: общий клиент с retry и таймаутом | COMMITTED | `b1ef3275` PLAN_v39 ШАГ 078: resilient shared llm service |
| 079 | analysis_llm: контракт досье artist.json (схема + валидатор) | COMMITTED | `780dcda0` PLAN_v39 ШАГ 079: validate artist dossier schema |
| 080 | metadata_llm: валидатор названий/описаний/хэштегов | COMMITTED | `b7c62690` PLAN_v39 ШАГ 080: enforce metadata release quality |
| 081 | music_stereo: склейка интро/аутро в stage_music | COMMITTED | `b4671e3a` PLAN_v39 ШАГ 081: extend beats with stereo sections |
| 082 | voice_cleaner: шумоподавление и де-эссер до полировки | COMMITTED | `50e4e5db` PLAN_v39 ШАГ 082: add vocal cleanup chain |
| 083 | beat_constructor: слоты kick/snare/hat/bass/melody из пресетов | COMMITTED | `2c4855d5` PLAN_v39 ШАГ 083: add five-slot beat patterns |
| 084 | render_queue: отмена, приоритеты, persisted-очередь | COMMITTED | `d89a6d66` PLAN_v39 ШАГ 084: persist render queue priorities |
| 085 | user_profile: хранение предпочтений пользователя | COMMITTED | `c9062579` PLAN_v39 ШАГ 085: add non-PII creative preferences |
| 086 | i18n: двухъязычные локали (RU/EN) заново | COMMITTED | `36c203b0` PLAN_v39 ШАГ 086: restore RU EN i18n |
| 087 | auto_backup: снапшот перед God Mode прогоном (заново) | COMMITTED | `ac977fe4` PLAN_v39 ШАГ 087: add AI preflight backups |
| 088 | LICENSES.md: таблица лицензий зависимостей | COMMITTED | `efe116ac` PLAN_v39 ШАГ 088: generate dependency license report |
| 089 | Манифест исполнения: автоотчёт по каждому шагу | PENDING | — |
| 090 | DSP: спектральная приёмка и golden-файлы (pro_audio_dsp) | PENDING | — |
| 091 | Детерминизм классического пайплайна (seed) | PENDING | — |
| 092 | requirements-профили base/ai/amd + pyproject extras | PENDING | — |
| 093 | Промпты обложек для всех 50 жанров | PENDING | — |
| 094 | Телеметрия KPI без PII | PENDING | — |
| 095 | Офлайн-режим: явные флаги для сетевых вызовов | PENDING | — |
| 096 | LEGACY-отчёт: что держит патчи v8..v12 | PENDING | — |
| 097 | Сборка колеса и проверка установки | PENDING | — |
| 098 | Терминальный прогресс стадий AI (lazy, без GUI) | PENDING | — |
| 099 | Регресс-база: классический пайплайн без torch | PENDING | — |
| 100 | Финализация v39.0.0: версия, CHANGELOG, тег, EXEC_REPORT | PENDING | — |
