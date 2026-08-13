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
