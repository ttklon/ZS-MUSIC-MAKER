# ZS Music Maker — SESSION_LOG (канонический журнал ошибок и доработок)

> Правило 11 ТЗ: единый файл со ВСЕМИ выявленными ошибками, доработками и планами.
> Каждая сессия: прочитать этот файл → исправить новые проблемы → дописать находки → обновить статусы.
> Легенда статусов: REAL_PASS / PARTIAL / FALLBACK_ONLY / BLOCKED / FAILED / MISSING / NOT_TESTED.
> Исправленные пункты помечаются ✅ и переносятся в архив внизу файла (не удаляются — история важна).

---

## АКТИВНЫЙ БЭКЛОГ (по приоритету)

### P0 — ломает запуск/продукт
- [x] ✅ v29: **God Mode E2E падал на `midi_generation` — `TypeError: 'NoneType' object is not callable`** (mido отсутствует, guard был только в `generate_drum_pattern`, а `generate_melody_pattern` пытался вызвать `MidiFile()` → крах всего pipeline). → Добавлен guard, honest BLOCKED-return `""`, расширены жанровые паттерны (phonk/trap/techno/hiphop), `get_status()`. Требование `mido>=1.3.0` внесено в `requirements.txt`. E2E теперь доходит до `master_god.wav`.

### P1 — критично для пайплайна/голоса/бита
- [x] ✅ v29: **mastering_pro: pyloudnorm clipping warning + возможные NaN/Inf + моно-даунмикс на выходе** → добавлен true-peak ceiling `-1 dBTP` (streaming-стенд), `_sanitize()` (NaN/Inf → 0), auto mono→stereo up-mix, honest output-метрики (`output_lufs`, `output_peak_db`, `channels`, `sample_rate`).
- [ ] **P1: Windows EXE build не верифицирован** — GitHub Actions `build.yml` есть, но первый прогон через Actions не подтверждён (в sandbox нет Windows). После push v29 → следить за https://github.com/ttklon/ZS-MUSIC-MAKER/actions.
- [ ] **P1: `voice_cleaner` = FALLBACK_ONLY** — noisereduce опционален, не проверен на Windows. Установить на целевой ПК, перевести в REAL_PASS.
- [ ] **P1: `musicgen_texture` = BLOCKED** — audiocraft heavy, не установлен. Подготовить честную инструкцию установки + авто-проверку при старте (сейчас молча падает в лог).

### P2 — качество результата
- [ ] **P2: `voice_synth` = FALLBACK_ONLY** — только pyttsx3/gtts scaffold. Цель: Silero TTS v3.1 RU на CPU (~50MB, реально для RX580/16GB). Обвязка есть, движок не подтверждён. **v30: честность исправлена** — `synth()` больше не возвращает путь к несуществующему файлу.
- [ ] **P2: RVC-конверсия тембра = NOT_TESTED** — `rvc_manager.py` обвязка есть (Applio/Mangio форки), но конверсия на реальной модели не прогонялась. Проверить inference на готовой .pth без обучения.
- [ ] **P2: 449 `except`-блоков в modules/ + app/core/** — большинство легитимны (опциональные heavy-deps), часть — скрытые падения. Точечно: master_pipeline_v12.py, release_pack_full.py.
- [x] ✅ **v30: Вокальная стадия God Mode `vocal_cleaning`** — теперь при отсутствии TTS-движка кладёт в отчёт честный `vocal_status=BLOCKED` + `vocal_reason=no_vocal_engine` (раньше молча возвращала None).

### P3 — UI/полировка/cleanup
- [x] ✅ v29: **Устаревшие smoke_v14..v25 (11 файлов) + AUDIT_50_DEEP / AUDIT_AND_IMPROVEMENT_REPORT / AIDER_GENERATION_AUDIT** — перенесены в `docs/legacy/` (не удалены, история сохранена). Активный smoke: `tools/smoke_v26.py` (аудио-качество) + `tools/smoke_v29.py` (God Mode E2E).
- [ ] **P3: PySide6 GUI = NOT_TESTED на Windows** — в sandbox невозможно. Проверить `main.py --desktop` на целевом ПК.

---

## ЖУРНАЛ СЕССИЙ

### v30 (2026-08-12) — session-full-audit-fix-restore
**Что проверено (полный аудит 276 файлов, 31.5k строк Python):**
- `python3 -m py_compile` всех .py → 0 синтаксических ошибок
- `pytest tests/` → **7/7 PASS**
- `tools/smoke_v29.py` → **8/8 PASS** (God Mode E2E, master_god.wav стерео 120с -1 dBTP)
- `tools/smoke_v26.py` → **6/6 PASS** (аудио-качество: stereo/loudness/drop/hit-score)
- `main.py --version/--list-genres/--health/--readiness/--dashboard/--self-diag/--dry-run/--e2e` → все CLI работают
- Импорт-проверка 44 ключевых модулей → после восстановления 0 падений

**Найдено и исправлено:**
1. **[P0] 5 модулей ошибочно удалены** в коммите f862aaf («Category D: remove dead code») — но они до сих пор импортировались health_v12/kpi_dashboard_v12/master_pipeline_v12/orchestrator_v10_patch. Это роняло health до RED и ломало KPI-пайплайн. → **Восстановлены из git-истории**: `lyrics_gen_v8`, `mastering_v9`, `release_pack_v9`, `hit_kpi_monitor_v11`, `lyric_vault_v10`. Все компилируются и импортируются, self-test KPI-модуля PASS.
2. **[P0-честность] `voice_synth.synth()` возвращал путь к несуществующему файлу**, когда ни один TTS-движок недоступен — вызывающий код получал «лживый» путь. → Теперь honest empty return `""` + проверка `_produced()` (файл >100 байт).
3. **[P0] Отсутствовал `run.bat`** — на него ссылались README («главный запуск»), INSTALL.md, create_desktop_shortcut.ps1, verify.bat. Двойной клик по ярлыку вёл в никуда. → Создан (тонкая обёртка над main.py, ищет venv → py → python).
4. **[P1] `self_diag_v13` падал** `FileNotFoundError: logs/self_diag_v13.txt` на свежем clone (нет каталога logs/). → Ленивое создание LOGS перед записью.
5. **[P1] Чекпоинты pipeline_core жили вечно** — старый fail-чекпоинт блокировал пайплайн навсегда даже после исправления кода. → TTL 24ч + env `ZSMM_NO_CHECKPOINTS=1` для полного отключения.
6. **[P1] `verify.bat` вызывал несуществующие** `smoke_test.py` / `bootstrap_e2e_test.py` → переписан на реальные: pytest + smoke_v26 + smoke_v29.
7. **[P2] God Mode отчёт терял статус вокала** → добавлены честные `vocal_status` / `vocal_reason` в итоговый project_meta.json.
8. **[P3] `main.py --smoke` не включал smoke_v29** → добавлен первым в цепочку.

**Результат после исправлений:**
- health_v12: missing internals = **[]** (было 4), ready 22→25%, dashboard «Соответствие ТЗ: 90% YELLOW»
- God Mode E2E: status=completed, vocal_status=BLOCKED (честно, т.к. нет TTS в sandbox)
- Все smoke и pytest — зелёные

**Что не удалось (честно):**
- Windows EXE build через GitHub Actions — в sandbox нет Windows, статус NOT_TESTED до прогона в Actions.
- Реальные TTS (silero/xtts/bark/pyttsx3/gtts) не установлены в sandbox — вокальная стадия честно BLOCKED, не сломана.
- health verdict остаётся RED из-за отсутствия в sandbox тяжёлых GUI/TTS-зависимостей (PySide6, gradio, pydub, pyttsx3) — на целевом ПК с `python install.py` они подтянутся.

**Оценка:** проект стал **измеримо лучше**. Устранён главный источник RED-health (мёртвые ссылки на удалённые модули), починена честность вокального fallback, восстановлен главный Windows-лаунчер. Приложение реально ближе к «полностью работающему»: единственные оставшиеся BLOCKED — это опциональные тяжёлые зависимости, которые подтягиваются install.py на пользовательской машине.

---

### v29 (2026-08-12) — session-god-mode-e2e-midi-fix-truepeak
**Что проверено:**
- `main.py --version` → **REAL_PASS** (v29.0.0)
- `pytest tests/` → **7/7 PASS**
- `tools/smoke_v26.py` → **6/6 PASS** (регрессия чиста)
- `tools/smoke_v29.py` (новый) → **8/8 PASS** — God Mode E2E доходит до `master_god.wav`, stereo, 120с, peak = -1.0 dBTP, RMS в норме
- Прямой прогон `run_god_pipeline(project_id, wizard_state=None)` → **status=completed** (5 стадий: ai_arrangement → midi_generation → audio_generation → vocal_cleaning → god_mastering_pro)

**Что исправлено:**
1. **[P0] `midi_generator.generate_melody_pattern` TypeError без mido** → добавлен guard `if not _HAS_MIDO: return ""`, расширены жанровые паттерны (phonk/trap/techno с музыкально осмысленной ритмикой), добавлена `get_status()` для честного отчёта. Убран дубликат guard в drum-версии.
2. **[P1] `mastering_pro` clipping/NaN/mono-риск** → true-peak ceiling -1 dBTP, `_sanitize()` для NaN/Inf, auto mono→stereo, honest output-метрики (`output_lufs`, `output_peak_db`, `channels`, `sample_rate`). Подавлен ClippingWarning — теперь всегда strict `-1 dBTP` на выходе.
3. **[P0] `mido` не в requirements** → добавлен `mido>=1.3.0`. Без него God Mode не создаёт MIDI-стемы (честный BLOCKED, но pipeline не валится).
4. **[P3] Cleanup** → 11 устаревших smoke-скриптов + 3 старых аудита архивированы в `docs/legacy/`. Активная папка `tools/` уменьшена до релевантных инструментов.
5. **[Правило 11]** SESSION_LOG актуализирован.

**Что не удалось:**
- Windows EXE build через GitHub Actions в sandbox проверить нельзя — статус NOT_TESTED до реального прогона в Actions.
- Реальный TTS (Silero/pyttsx3/gtts) не установлен в sandbox — вокальная стадия работает как honest FALLBACK_ONLY.

**Оценка:** проект стал **реально лучше**. God Mode впервые в истории проекта завершается `status=completed` с валидным `master_god.wav` (стерео 44.1 кГц, 120 с, ceiling -1 dBTP). Появилась honest E2E-проверка `smoke_v29`. Убран мусор из `tools/` и корня.

**Артефакты:** `output/smoke_v29/god/masters/master_god.wav` (стерео, 120с, -1 dBTP), `output/smoke_v29/midi/*.mid`.

### v28 (2026-08-12) — session-cleanup-godmode-ci-build
**Что исправлено:**
1. [P0] Репо очищено от 72 output-артефактов (~262MB), `.gitignore` расширен.
2. [P0→P1] God Mode `wizard_state=None` защищён Optional+default.
3. [P1] Добавлен `.github/workflows/build.yml` (Windows EXE, PyInstaller).
4. Создан SESSION_LOG.md.

### v27 (2026-08-12) — mastering-module-stereo-import-fallback
- Создан отсутствующий `modules/mastering.py` (мастеринг всегда падал) ✅
- voice_cleaner: noisereduce → ленивый импорт + fallback ✅
- plugins/advanced: pedalboard/audiomentations ленивые ✅
- mastering_stands: убран монодаунмикс ✅

---

## ПЛАН СЛЕДУЮЩЕЙ СЕССИИ (v31)
1. Проверить результат build.yml в Actions после push v30 → если EXE собрался, статус REAL_PASS; если упал — чинить spec/пути.
2. voice_synth: подтвердить Silero на CPU baseline → REAL_PASS.
3. musicgen_texture: honest instruction + BLOCKED-детектор на старте.
4. RVC: реальная inference-проверка на готовой .pth.
5. Точечно почистить `except: pass` в master_pipeline_v12.py (449 блоков — приоритет скрытым падениям).

---

### v31 (2026-08-13) — session-deep-audit-only (БЕЗ ПРАВОК, только находки)

> Режим сессии: **ГЛУБОКИЙ АУДИТ БЕЗ ВНЕСЕНИЯ ИЗМЕНЕНИЙ В КОД**. Ни один .py/.bat/.json-файл продукта не правился. Единственная запись — этот блок в SESSION_LOG.md.

**Что проверено (полный повторный аудит, Python 3.12.3, sandbox Linux):**
- `python3 -m compileall` всех 137 .py → **0 синтаксических ошибок**
- `pytest tests/` → **7/7 PASS**
- `tools/smoke_v29.py` → **8/8 PASS** (God Mode E2E, master_god.wav стерео 120с, -1 dBTP)
- `tools/smoke_v26.py` → **6/6 PASS** (аудио-качество)
- `main.py --version/--list-genres/--readiness/--dashboard/--self-diag/--console/--dry-run/--e2e/--onboarding` → все запускаются
- Импорт-проверка всех 137 модулей (modules/app/app.core/app.gui/app.plugins/agents/ui/tools/updater/docs.legacy) → **134 OK / 3 FAIL**
- `tools/fallback_audit.py` → 132 файла, **red_flags: pitch_shift_as_rvc = 2**
- `main.py --health` → **verdict: RED, percent_ready=35, core_ok=False**
- `main.py --e2e` (real_e2e_v14) → **Verdict: PARTIAL, 13/15 стадий, red flags: pitch_shift_as_rvc=2**

---

#### НОВЫЕ НАХОДКИ v31 (не перечислены выше в активном бэклоге — вносятся впервые)

**P0 — дезинформация пользователя / битый onboarding-путь:**

1. **[P0] INSTALL.md ведёт в никуда (инструкция установки полностью битая).** Шаг «Двойной клик по `windows_build.bat`» — файла **НЕТ в репозитории**. Раздел «Проверка после установки» требует `smoke_test.py` и `bootstrap_e2e_test.py` — **обоих НЕТ**. Linux-раздел требует `python smoke_test.py` — **НЕТ**. На эти несуществующие файлы также ссылаются `autodetect_python.bat` (строка 4: «Используется windows_build.bat как fallback»), `modules/rvc_manager.py:146` («pip install rvc-python (в windows_build.bat)»), `modules/kpi_dashboard_v12.py:183` («auto_deps — есть windows_build.bat»), `docs/v11/DEPLOYMENT_CHECKLIST_v11.md`. **Следствие:** новый пользователь, строго следующий INSTALL.md, не может ни установить, ни проверить продукт — первый же шаг (windows_build.bat) отсутствует. Это БЛОКЕР первого запуска на целевой Windows-машине. (v30 починил `run.bat`, но НЕ починил INSTALL.md, который на него ссылается через несуществующий windows_build.bat.)

2. **[P0] `health: RED / percent_ready=35 / core_ok=False` на свежем окружении.** Причина — 12 EXTERNAL-MISS (PySide6, Gradio, matchering, pyttsx3, essentia, torch, torch-directml, demucs, openai-whisper, Coqui XTTS-v2, suno-bark, rvc-python). На машине без `install.py`/весов это держит health в RED даже когда ядро (beat/mix/mastering) полностью работоспособно. Проблема НЕ в коде, а в **пороге RED**: core_ok=False из-за отсутствия опциональных heavy-deps, хотя они помечены «опционально». Пользователь видит RED и считает продукт сломанным, хотя dry-run и God Mode работают.

3. **[P0] `requirements.txt` пин `numpy>=1.26.0,<2.0` конфликтует с реальным рантаймом.** В текущей среде (и, вероятно, у части пользователей Python 3.12) уже стоит **numpy 2.4.6**, librosa 1.0.0 тянет numpy>=2. Жёсткий верхний пин `<2.0` либо заставит pip ломать окружение (downgrade numpy, конфликт с современными librosa/scipy), либо pip откажется резолвить. Нужна проверка: реально ли код несовместим с numpy 2.x, или пин устарел.

**P1 — ложные/подозрительные флаги качества и рассинхрон версий:**

4. **[P1] `fallback_audit` и `--e2e` поднимают `pitch_shift_as_rvc=2`, но оба срабатывания — ЛОЖНЫЕ.** Оба вызова `librosa.effects.pitch_shift` — это легитимный DSP, а не подмена RVC: `modules/anti_neuro_v10.py:363` (формантный трюк resample+pitch-back в anti-neuro polish) и `modules/female_backing.py:127` (питч-шифт бэк-вокальной гармонии, помечен комментарием «NOT RVC substitute», но маркер стоит как `# noqa: ZSMM_NOT_RVC` **после** выражения, а детектор ищет маркер в **той же строке, что и совпадение** — для многострочного вызова `pitch_shift(\n...` маркер на строке закрывающей скобки не попадает в snippet первой строки → ложный флаг). **Дефект именно в детекторе** `tools/fallback_audit.py`: он не ловит многострочные вызовы с маркером. Из-за этого `--e2e` всегда завершается PARTIAL с red_flag, а не PASS.

5. **[P1] Рассинхрон версий (три источника правды расходятся).** `version.json` = **30.0.0**; `pyproject.toml` = **26.0.0**; заголовок `README.md` = **v18** (хотя внутри «Актуальная версия: v26.0.0»); `CHANGELOG.md` застыл на **v9** («текущая финальная сборка»). PROJECT_STATE.md = **v29** (не обновлён до v30). Т.е. ни один человек не может однозначно ответить «какая сейчас версия» — 5 файлов показывают 5 разных значений (9/18/26/29/30).

6. **[P1] README ссылается на перенесённые/несуществующие тесты.** Раздел «Тесты v17» требует `python3 tools/smoke_v14.py` и `python3 tools/smoke_v17.py` — оба **перенесены в `docs/legacy/`** в v29 (по путям из README их больше нет → команда падает). README упоминает `tools/quality_gate.sh` (существует), но `quality_gate` требует `pylint`/`mypy`, которых **нет ни в requirements.txt, ни в CI** — Quality Gate не запускается «из коробки» ни локально, ни в Actions.

7. **[P1] ТЗ-пункты 7 и 8+11 навсегда «не подтверждены».** И `--dashboard`, и `--self-diag`, и `tools/readiness.py` помечают `[ ] 7 Smoke + E2E тесты` и `[ ] 8+11 README + CONTEXT.md` как НЕ выполненные, хотя smoke/E2E реально существуют и зелёные, а README написан. Причина: чек-логика ищет `smoke_v12.py` в корне / `smoke_v12_report.json` / файл `CONTEXT.md` — **ни одного из этих артефактов нет в репо** (CONTEXT.md отсутствует физически, smoke_v12 давно заменён на v26/v29). Т.е. дашборд занижает % готовности и вводит в заблуждение («🟡 Smoke ещё не гонялся — запусти smoke_v12.py» — файла нет).

**P2 — скрытые/тихие дефекты и архитектурный мусор:**

8. **[P2] 3 модуля не импортируются на чистом окружении** (137 проверено): `app.core.model_manager` (требует torch на верхнем уровне), `app.gui.onboarding`, `app.gui.wizard` (требуют PySide6 на верхнем уровне). Для GUI-файлов это ожидаемо, но `app.core.model_manager` — это CORE-слой, и его жёсткая зависимость от torch роняет `install.py` (шаг 5 «Initializing Model Manager» молча уходит в WARNING) и любой импорт core-графа без torch.

9. **[P2] Дубли лаунчеров-призраков.** В корне лежат **4 Windows-лаунчера с идентичным телом**: `run.bat`, `run_v8.bat`, `run_v9.bat`, `run_v11.bat` (все четыре сведены к `%PY% main.py %*`) + `run_v14.sh`. Пользователь не понимает, какой запускать; README зовёт `run.bat`, остальные — мёртвый шум, создающий путаницу версий («а v11 — это новее run.bat?»).

10. **[P2] Архитектурный распад оркестраторов (5 параллельных пайплайнов).** Сосуществуют и все импортируются: `app/core/orchestrator.py` (2037 строк — монстр), `orchestrator_async.py`, `orchestrator_god.py` (реально используется в `--god` и smoke_v29), и 5 патчей `orchestrator_v8/v9/v10/v11/v12_patch.py`, плюс отдельный `modules/master_pipeline_v12.py` и `app/runtime_orchestrator.py`. Нет одного канонического пайплайна — непонятно, какой путь «production», какой — legacy. Это главный источник риска регрессий: фикс в одном оркестраторе не попадает в другой (именно так в f862aaf удалили 5 живых модулей).

11. **[P2] `tools/validate_final_track.py` содержит жёстко зашитый чужой путь** `/home/ubuntu/ZS-MUSIC-MAKER/output/god_cli/masters/master_god.wav` → на любой другой машине всегда печатает `STATUS: FAIL ❌ / File not found`. Инструмент «финальной проверки качества» по сути сломан по умолчанию (путь не параметризован, нет argv).

12. **[P2] Монолитные модули-«боги».** `app/core/orchestrator.py` = 2037 строк, `modules/master_pipeline_v12.py`, `modules/release_pack_full.py` (ISRC/ID3/5 платформ в одном файле ~900 строк). Нет разделения на подмодули → высокая цикломатическая сложность, почти не покрыто тестами (в `tests/` всего 4 файла: test_audio_quality, test_genre_and_audit, test_mastering_results, test_pro_audio_dsp).

13. **[P2] 497 `except`-блоков в modules/ + app/** (было заявлено 449 — реально больше). Подавляющее большинство — легитимные lazy-import heavy-deps, но среди них есть и молчаливые `except: continue` (`app/core/cover_gen.py:39`) и `except: pass` (`app/plugins/base.py:48`), а также десятки `except Exception: pass` в критичных `master_pipeline_v12.py` / `release_pack_full.py`, которые скрывают реальные падения стадий (стадия «успешно» завершается пустым результатом).

**P3 — покрытие тестами и честность метрик:**

14. **[P3] Тестовое покрытие тонкое.** В `tests/` только 4 тест-файла на 137 модулей. Нет тестов на: voice_synth, rvc_manager, lyrics_gen, release_pack_full, master_pipeline_v12, все 5 оркестратор-патчей, updater, cover_gen, karaoke_engine. Полагаемся на smoke_v26/v29, но они не ловят регрессии вокала/RVC/лирики/релиз-пакета.

15. **[P3] `--dry-run` возвращает `verdict=PARTIAL` (а не PASS) и занимает 137 секунд.** PARTIAL на dry-run — это нормально для отсутствующих TTS, но пользователь читает PARTIAL как «что-то сломано». Нет разделения «PARTIAL из-за опциональных heavy-deps» vs «PARTIAL из-за реального бага» — единый вердикт без разбора причины в заголовке.

16. **[P3] Onboarding честно сообщает `real_recording_possible: false`** в среде без звуковой карты (sounddevice/numpy=False) — это хорошо (честность), но `--onboarding` **не возвращает ненулевой код** и не помечает в manifest причину недоступности микрофона для downstream-стадий.

---

#### ЧТО ПОДТВЕРЖДЕНО РАБОЧИМ в v31 (повторная верификация, не из SESSION_LOG, а реальный прогон)
- Ядро аудио-пайплайна: beat_constructor (стерео corr≈0.96, drop-fade), mixdown, mastering_pro (true-peak -1 dBTP, NaN/Inf-guard, mono→stereo), pro_audio_dsp — **REAL_PASS**
- God Mode E2E (orchestrator_god): 5 стадий → master_god.wav стерео 120с — **REAL_PASS**
- midi_generator: guard + mido-паттерны phonk/trap/techno — **REAL_PASS**
- CLI: version/list-genres(119 жанров)/readiness/dashboard/self-diag/console/dry-run/e2e/onboarding — **запускаются, exit 0** (кроме осознанных PARTIAL)
- Жанровая база: `--list-genres` = 119 жанров; `config/genres_100.json` валиден (6 категорий)
- JSON-конфиги (health_v12, hw_profile, kpi_dashboard_v12, tutorial_settings) — валидны
- Секреты в коде не захардкожены (API-ключи только из env: OPENROUTER/XAI/GEMINI/GOOGLE); `shell=True`/`os.system`/`eval`/`exec` в продакт-коде не найдены (только PySide6 `.exec()` диалогов)
- RVC pitch-shift fallback корректно ЗАПРЕЩЁН и бросает RuntimeError (TZ 33.5 соблюдено) — **REAL_PASS по честности**

#### РЕЗЮМЕ v31 (честное)
Приложение **функционально ближе к рабочему, чем сообщает health-RED**: ядро (бит→микс→мастеринг→God Mode) реально работает и подтверждено зелёными smoke. Главные реальные проблемы — **не в аудио-ядре, а вокруг него**: (а) битая инструкция установки INSTALL.md (P0-блокер первого запуска), (б) заниженный/ложный health-RED из-за опциональных heavy-deps, (в) рассинхрон версий в 5 файлах, (г) ложный флаг pitch_shift_as_rvc, (в) архитектурный распад на 5+ оркестраторов. До состояния «полностью работает» осталось устранить пункты 1-8 выше — они НЕ требуют переписывания DSP, это в основном wiring/документация/пороги/детекторы.

**Приоритет для следующей сессии (правки):** сначала P0.1 (INSTALL.md+windows_build.bat), P0.3 (numpy-пин), P1.4 (детектор fallback_audit), P1.5 (version unification), P1.7 (CONTEXT.md+smoke_v12 refs), затем P2.8/P2.9 (model_manager lazy-torch, дубли лаунчеров).

---

### v32 (2026-08-13) — session-deep-audit-v2-only (БЕЗ ПРАВОК, только находки)

> Режим сессии: **ВТОРОЙ ГЛУБОКИЙ АУДИТ БЕЗ ИЗМЕНЕНИЙ КОДА**. Ни один .py/.bat/.json/.yml продукта не правился. Единственная запись — этот блок. Находки v31 (пп.1–16) НЕ дублируются — здесь только НОВЫЕ, не перечисленные выше.

**Проверено в этой сессии (Python 3.12, sandbox):**
- `compileall` всех .py → 0 ошибок; `pytest tests/` → 7/7 PASS
- Полный чит-скан: main.py, INSTALL.md, requirements.txt, pyproject.toml, .gitignore, ci.yml, build.yml, run.bat, run_all_smoke.bat/.sh, voice_synth.py, orchestrator_god.py, install.py, updater.py, license_manager.py, app/main.py
- `git ls-files` (что реально в репо) + проверка ссылок INSTALL.md против диска
- Стат-анализ: 497 `except` в modules/app, 92 многострочных `except: pass`, 172 `print()` в modules/app, 1 захардкоженный путь, 0 mutable-defaults, 0 `import *`

---

#### НОВЫЕ НАХОДКИ v32 (впервые, не повторяют v31)

**P0 — битые обещания пользователю:**

1. **[P0] `run_all_smoke.bat` вызывает ЧЕТЫРЕ несуществующих файла.** `.bat` запускает `smoke_v9.py`, `smoke_v10.py`, `smoke_v11.py` (корень — их нет) и `tools\smoke_v17.py`, `tools\smoke_v18.py` (перенесены в `docs/legacy/` в v29). Linux-брат `run_all_smoke.sh` исправлен («AUDIT-FIX… раньше скрипт вызывал несуществующие»), а Windows-версия **оставлена битой** — асимметрия платформ. На Windows прогон smoke падает сразу.

2. **[P0] INSTALL.md и README обещают НЕсуществующий функционал вокала/RVC как готовый.** INSTALL.md §5 прямо пишет: «voice_convert.convert() автоматически переключится на offline pitch-shift fallback», а v31 зафиксировал, что pitch-shift-как-RVC **ЗАПРЕЩЁН и бросает RuntimeError** (TZ 33.5). INSTALL.md обещает порт-фолбэк 7861 в run.bat — в run.bat этой логики **нет**. INSTALL.md шаг 1 говорит «Распакуй ZIP» и «Откроется http://127.0.0.1:7860» — но run.bat без аргументов ведёт в PySide6-desktop (не Gradio на 7860). Пользователь читает одно, получает другое.

3. **[P0] `voice_synth` обрезает вокал до 200 символов.** В `orchestrator_god.py` stage_vocal: `voice_synth.synth(text_content[:200])` — сгенерированная лирика (куплет+припев) насильно урезается до 200 знаков ≈ 2-3 строки речи. В итоге в God Mode «вокал» — это одна фраза на 120-секундный трек. Не ошибка синтаксиса, а логический дефект результата: трек технически «с вокалом», фактически без слов.

4. **[P0] `voice_synth` молча перезаписывает `out_name` без проверки коллизии и возвращает дефолт `draft.wav`.** `synth()` пишет всегда в `OUT_DIR/draft.wav`, если не передан `out_name`. Параллельные/повторные вызовы затирают друг друга. Нет уникализации (timestamp/uid) — как в `voice_vault`, так и в `output/voice_draft/`.

**P1 — качество кода и сборка:**

5. **[P1] `install.py` использует `shell=True` на каждой команде pip/apt** — единственный файл в продакте с `subprocess.check_call(cmd, shell=True)` на строках с интерполяцией `sys.executable`. Риск injection + несовместимо с путями с пробелами (которые INSTALL.md сам запрещает, но install.py не проверяет). На пути с пробелом `subprocess`+`shell=True` ломается.

6. **[P1] `requirements.txt` противоречит INSTALL.md по numpy.** requirements пин `numpy>=1.26.0,<2.0` (v31 уже отметил конфликт), а INSTALL.md §2 обещает «numpy<2» но §4 (Linux) ставит `pip install -r requirements.txt` + современные librosa/audiocraft, которые тянут numpy≥2 — pip-резолвер на Linux встанет в конфликт. Инструкция и пин не согласованы.

7. **[P1] `pyproject.toml` и `requirements.txt` — два разных списка зависимостей.** pyproject.dependencies = 10 пакетов (нет PySide6/gradio/pyloudnorm… хотя pyloudnorm там ЕСТЬ, а PySide6 нет), requirements.txt = 30+. `pip install -e .` и `pip install -r requirements.txt` дают разное окружение. CI ставит requirements.txt, а build.yml — requirements.txt; но если кто-то сделает `pip install .` — получит половину.

8. **[P1] `build.yml` (PyInstaller) почти гарантированно НЕ соберёт рабочий EXE.** `--add-data "lyric_vault;lyric_vault"` и `voice_vault` тянут user-data в EXE; **нет** `--add-data "models;models"`, `data/genre_presets`, `data/prompts` (критично для lyrics/cover). `--hidden-import modules` бесполезен — PyInstaller не собирает динамические `__import__("app.core.orchestrator_vN_patch")` и `from modules import ...` внутри функций (а они ВСЕ ленивые). Результат: EXE соберётся, но упадёт в рантайме на первом же ленивом импорте. Smoke-шаг `--version` имеет `continue-on-error: true` → сборка «зелёная» даже при мёртвом EXE.

9. **[P1] `--async-mode` CLI не проверяет результат пайплайна.** `main.py --async-mode` вызывает `AsyncOrchestrator(...).run_pipeline()` и всегда возвращает 0, даже если пайплайн упал. Нет try/except, нет проверки статуса — exit code врёт CI/пользователю.

10. **[P1] `ci.yml` не запускает smoke/E2E вообще.** CI гоняет только `pytest tests/` (7 тестов). Реальные регрессионные проверки (smoke_v26, smoke_v29, fallback_audit, real_e2e_v14) в CI отсутствуют — пуш, ломающий God Mode, пройдёт зелёным. CI защищает только 4 тест-файла из 137 модулей.

11. **[P1] `app/main.py` — дубль-обёртка, расходящаяся с корневым main.py.** `app/main.py` делает `import main as root_main` и вызывает `root_main.main()` — но корневой `main.py` уже имеет свой `_setup_console_encoding()` и `sys.path.insert`. Двойная инициализация кодировки + двойной sys.path. Пользователь не понимает, какой из двух main.py «настоящий» (README зовёт корневой).

**P2 — архитектура и тихие дефекты:**

12. **[P2] 172 вызова `print()` в modules/app вместо logger.** При наличии `app/core/logger.py` (app_logger) почти все модули (voice_synth, orchestrator_god, cyber_synth…) пишут через `print()`. В desktop-режиме (PySide6, `--windowed` EXE без консоли) эти сообщения **теряются** — отладка на Windows-EXE невозможна.

13. **[P2] `time.sleep()` в аудио-потоках karaoke_engine / render_queue.** `karaoke_engine.py:93` спит `beat_ms/1000` в цикле воспроизведения (дрейф синхронизации), `render_queue.py:139` `time.sleep(3)` в цикле опроса. Блокирующие sleep в реалтайм-контексте = заикающийся караоке/очередь.

14. **[P2] `hit_kpi_monitor_v11` портит пути `os.sep`-хаком.** Строки 138/140: `.replace("\\","/")` — ручная нормализация слэшей вместо `Path.as_posix()`. Ломается на путях, где `\` — легитимный символ, и дублирует то, что pathlib делает сам.

15. **[P2] `config/genres_100.json` — это НЕ 100 жанров, а 6 категорий-метаданных.** Файл — dict из 6 ключей. Реальные пресеты лежат в `data/genre_presets/` (50 файлов). `--list-genres` показывает 119 (StyleRegistry из кода). Три источника «сколько жанров»: 6 / 50 / 119 — рассинхрон имени файла, пресетов и реестра.

16. **[P2] `safe_import.py` — мёртвый модуль.** Единственный файл, импортирующий safe_import — `docs/legacy/smoke_v23.py`. Ни один продакт-модуль не использует эту обёртку, хотя 497 except-блоков вручную делают то же самое. Дублирующая инфраструктура, которая не применяется.

17. **[P2] `updater.user_data_dir()` и `program_dir()` расходятся с реальным layout репо.** updater считает program_dir = `C:\Program Files\ZS Music Maker` на win32, но репо ставится клонированием в любую папку; USER_PRESERVED перечисляет `presets`/`prompts`, а в репо они — `data/genre_presets` и `data/prompts`. Откат/backup updater-а сохранит не те каталоги.

18. **[P2] `license_manager.py` не используется пайплайном.** Фильтр CC0/RF существует, но ни sample_hunter, ни freesound_client не вызывают `is_free_commercial()` перед скачиванием сэмпла (проверено grep — нет кросс-ссылки). Лицензионный gate написан, но не подключён → легальный риск на сэмплах.

19. **[P2] `data/health_v12.json` и `data/kpi_dashboard_v12.json` — зашитые в репо снапшоты чужой машины.** `platform: Linux-6.1.158`, `python: 3.13.14`, `ram_gb: 1.9` — это sandbox-артефакт, закоммичен как «данные». `.gitignore` имеет `*.json` с исключением только version.json/config — но эти data/*.json почему-то в репо. Пользователь видит чужой health-профиль как свой.

20. **[P2] God Mode игнорирует `theme` для большинства жанров.** stage_vocal берёт `state.get("theme")`, но stage_arr использует только `genre`, а lyrics_gen получает theme=`"Владимирский централ"` по дефолту независимо от `--theme` аргумента CLI (theme передаётся в wizard_state, но stage_vocal читает `state["theme"]` который ai_arranger не пробрасывает). `--theme` пользователя теряется.

**P3 — честность метрик и UX:**

21. **[P3] `voice_synth` bark/pyttsx3 дефолт-speaker захардкожены** (`aidar`, `v2/ru_speaker_0`) без выбора пола/тональности — для female-трека всё равно синтезируется мужской aidar. Нет параметра gender в synth().

22. **[P3] `--god` CLI игнорирует большинство аргументов.** `_cli_god` читает genre/theme, но `--genre` дефолт `drift_phonk` зашит и в argparse, и в orchestrator_god.setdefault — два дефолта могут разойтись. Нет валидации genre против StyleRegistry: `--genre=foobar` молча уйдёт в пайплайн.

23. **[P3] `run_v14.sh` — единственный v14-лаунчер без пары .bat** (есть run_v8/v9/v11.bat, но v14 только .sh). Ассиметрия ОС в лаунчерах + усиливает путаницу версий (v31 п.9 про дубли).

24. **[P3] CHANGELOG/README/INSTALL расходятся о «текущей» версии жанрового движка.** README v18-заголовок, CHANGELOG v9, INSTALL v4, version.json v30. Пользователь не может понять, какие фичи реально доступны (v31 п.5 про версии — здесь дополнение: **INSTALL.md сам озаглавлен «v4»**, что в 7 версий ниже реальной).

25. **[P3] Нет `.env.example` / документации env-переменных.** Код читает `OPENROUTER_*`, `XAI_*`, `GEMINI_*`, `GOOGLE_*`, `ZSMM_NO_CHECKPOINTS`, `ZSMM_PROGRAM_DIR`, `ZSMM_USER_DIR` — но ни один файл не перечисляет их для пользователя. LLM-фичи молча не работают без ключей, о которых пользователь не знает.

26. **[P3] `tutorial_settings.json` в корне, остальные конфиги — в data/.** Разброс конфигов: tutorial_settings.json (корень), data/*.json, config/genres_100.json, voice_vault/*.json. Нет единого config-слоя; модули читают конфиги отовсюду.

27. **[P3] Тесты не покрывают CLI-режимы main.py.** 7 pytest-тестов — только аудио-DSP. Ни один не дёргает `--version/--god/--dry-run/--readiness` (проверено — tests/ не импортирует main). Регрессия argparse (как P0 в v17 с неподключёнными флагами) пройдёт незамеченной.

28. **[P3] `models/rvc/training_jobs/*.json` закоммичены** — 3 файла реальных training-job (rvc_1786009365…) с user-путями внутри. Репо несёт артефакты чужих RVC-тренировок. `.gitignore` игнорит `models/rvc/*.pth` но не `training_jobs/`.

29. **[P3] `orchestrator_god` пишет meta через `json.dump(default=str)`** — маскирует несериализуемые объекты (Path, numpy-типы) в строки молча. Отчёт project_meta.json может содержать `"123.456"` вместо числа для метрик, что ломает downstream-парсинг KPI.

30. **[P3] `.gitignore` содержит мёртвые исключения** `!AUDIT_50_DEEP.md`, `!GLOBAL_AUDIT_ULTIMATUM_V7.md` — файлов нет (AUDIT_50_DEEP уехал в docs/legacy/). Плюс `*.json` в корне игнорит, но `version.json` — единственное реальное исключение; остальные whitelist-строки — шум.

---

#### СВОДКА НАКОПЛЕННОГО БЭКЛОГА (v31 + v32, итого ~46 открытых пунктов)
- **P0:** INSTALL/windows_build (v31.1), run_all_smoke.bat (v32.1), voice 200-char clip (v32.3), health-RED порог (v31.2), numpy-пин (v31.3 + v32.6), INSTALL обещания pitch-shift/7860 (v32.2), voice draft.wav коллизия (v32.4)
- **P1:** fallback_audit детектор (v31.4), version unification (v31.5), CONTEXT.md/smoke_v12 refs (v31.7), install.py shell=True (v32.5), pyproject≠requirements (v32.7), build.yml EXE мёртв (v32.8), async exit code (v32.9), CI без smoke (v32.10), app/main.py дубль (v32.11)
- **P2:** 3 не-импорта (v31.8), дубли лаунчеров (v31.9+v32.23), 5 оркестраторов (v31.10), hardcoded path (v31.11), монолиты (v31.12), 497 except (v31.13+v32.16), print-vs-logger (v32.12), sleep в RT (v32.13), sep-хак (v32.14), genres 6/50/119 (v32.15), updater layout (v32.17), license gate off (v32.18), stale health json (v32.19), god theme теряется (v32.20)
- **P3:** покрытие тестами (v31.14+v32.27), dry-run PARTIAL (v31.15), onboarding rc (v31.16), bark speaker (v32.21), god args (v32.22), версии док (v32.24), env не документированы (v32.25), конфиги разбросаны (v32.26), training_jobs в репо (v32.28), meta default=str (v32.29), gitignore мёртв (v32.30)

#### РЕЗЮМЕ v32 (честное)
Аудио-ядро (beat→mix→mastering→God Mode) по-прежнему REAL_PASS и подтверждено зелёными smoke. Но второй проход вскрыл **системный слой проблем ВОКРУГ ядра**, которых v31 не видел: (а) Windows-smoke полностью бит, (б) voice-стадия урезает текст до 200 символов, (в) PyInstaller-EXE — мёртворождённый (нет hidden-imports для ленивых импортов), (г) CI не гоняет ни одного реального smoke, (д) лицензионный фильтр сэмплов написан, но не подключён. До «полностью работает» — закрыть P0 (пп.1–7 сводки), это wiring/доки/пороги, НЕ переписывание DSP.

**Приоритет следующей сессии (правки):** сначала P0.1/P0.2/P0.3 (INSTALL+windows_build+run_all_smoke.bat+voice 200-char), затем P1.5/P1.8/P1.10 (version unify, build.yml hidden-imports, CI+smoke), затем P1.4 (fallback_audit детектор).
