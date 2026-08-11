# ZS Music Maker v16 — CHANGELOG APPEND

**Дата:** 2026-08-08
**База:** v15 (i59f3u.zip, SHA-256 06ca4b5c…fee14b2, 37 МБ, 511 файлов)

## Режим сессии

Сессия выполнена в **режиме ограниченного объёма** (см. PROMPT.txt, раздел
«РЕЖИМ ОГРАНИЧЕННОГО ОБЪЁМА НА 1 СЕССИЮ»): взят и доведён до конца ОДИН
пакет работ — аудит + реальный прогон + закрытие P0-дефекта честности KPI.
Новые большие фронты (RVC/Demucs/MusicGen/запись) в этой сессии
**не начинались** — они оформлены как следующая очередь работ.

## Что сделано в v16

### P0 — Фикс честности KPI: sys.path-баг в tools/*.py ✅

**Симптом:** при запуске любого инструмента напрямую
(`python3 tools/readiness.py` и т.п.) в `sys.path` попадает каталог
`tools/`, а не корень проекта. Все проверки модулей через
`__import__("modules.*")` / `from modules import ...` ложно падали в
`ModuleNotFoundError` → `MISSING`.

**Доказательство бага (реальный прогон, песочница):**
- `python3 tools/readiness.py` → **22%**, `analyzer: MISSING`,
  `updater_module: MISSING`, `voice_vault: MISSING` — ложно;
- `python3 tools/smoke_v14.py` → **21/28 FAIL** — ложно;
- `python3 tools/p0_truth_test.py` → `ModuleNotFoundError` — падение.

**Исправление** (в существующие файлы, без плодения версий):
- `tools/readiness.py` — добавлен bootstrap: корень проекта вставляется
  в `sys.path` до любых импортов `modules.*`;
- `tools/smoke_v14.py` — тот же bootstrap;
- `tools/p0_truth_test.py` — тот же bootstrap.

**Доказательство фикса (реальный прогон, прямой запуск без PYTHONPATH):**
- `python3 tools/readiness.py` → **60.0%**, `analyzer/updater/voice_vault:
  REAL_PASS` — совпадает с запуском через `PYTHONPATH=.`;
- `python3 tools/smoke_v14.py` → **28/28 PASS**;
- `python3 tools/p0_truth_test.py` → **DRY_RUN_PASS 100%** (13/13 стадий ok).

**Почему это P0:** принцип 1.9 ТЗ — «честность прогресса». Заниженный KPI
(22% вместо 60%) — та же ложь, только в другую сторону. Инструмент
самодиагностики обязан работать при стандартном запуске.

### P1 — Восстановление потерянного доказательства tools/smoke_v15.py ✅

**Проблема:** `CHANGELOG_v15_APPEND.md` заявлял `tools/smoke_v15.py` как
доказательство v15-функций, но **файл в архиве отсутствовал** — доказательство
было потеряно.

**Действие:** файл восстановлен (`tools/smoke_v15.py`, 9.3 КБ). Smoke реально
вызывает v15-модули, а не проверяет их наличие:
- импорт `release_pack_full`, `llm_clients_v15.LLMRouter`, `tools/ab_compare`,
  `agents/github_scout`;
- **реальный прогон** `release_pack_full.build_pack` на синтезированном
  тестовом WAV (не тишина — синус с гармониками и огибающей);
- **реальный прогон** `LLMRouter.complete` без ключей — честная цепочка
  `openrouter→grok→gemini→ollama→local_template`, `fallback_used=True`;
- **реальный прогон** `ab_compare.compare` на двух синтетических WAV
  (440 Гц vs 330 Гц) — посчитаны LUFS, построены спектрограммы;
- `github_scout.scan(offline_fallback=True)` — офлайн-безопасность.

**Результат прогона:** **13/13 PASS**, отчёт
`output/audit_v15/smoke_v15_report.json`.

**Честные оговорки по прогону (FALLBACK_USED, не скрываю):**
- релиз-пакет собрал **23 реальных файла** (не ~38): в песочнице нет
  `ffmpeg` и генератора клипов → категории клипов/m4a ушли в fallback,
  помечены в отчёте `fallback_used=True`;
- LLMRouter без API-ключей и Ollama честно вернул `local_template` —
  это ожидаемое поведение, а не «LLM работает».

## Попутные исправления

- В песочнице доустановлены `pyloudnorm` и `matplotlib` — без них
  `tools/ab_compare.py` падал на импорте. В коде проекта ничего не менялось
  (зависимость уже была задекларирована в `requirements.txt`); на машине
  пользователя `install.bat` ставит их сам.

## Что НЕ сделано в этой сессии (честно)

- RVC / Demucs / MusicGen / реальная запись с микрофона — **не начинались**
  (тяжёлые зависимости, отдельный крупный этап, см. раздел 40 ТЗ).
- `modules/female_backing.py:113` — `librosa.pitch_shift` вместо RVC
  (красный флаг `pitch_shift_as_rvc` из fallback_audit) — **не закрыт**,
  вынесен в следующую очередь.
- Полный E2E с реальным аудио — остаётся PARTIAL (dry-run проходит,
  реальный рендер требует torch/MusicGen).
- `modules/release_pack_v13.py:189` — незакрытый TODO — не тронут.

## Следующая очередь работ (приоритет)

1. **P0:** заменить `pitch_shift` в `female_backing.py` на честный
   RVC-вызов с явным FALLBACK_USED-маркером (закрыть красный флаг аудита).
2. **P0:** полный реальный E2E-прогон с генерацией WAV через весь пайплайн
   (требует установки torch/MusicGen в песочнице — отдельная сессия).
3. **P1:** закрыть TODO в `release_pack_v13.py:189`.

## Размер архива

- До (v15): 37 МБ, 511 файлов.
- После (v16): размер **не уменьшился** — добавлены `tools/smoke_v15.py`
  (9.3 КБ) и `CHANGELOG_v16_APPEND.md`; изменены 3 существующих файла
  (`readiness.py`, `smoke_v14.py`, `p0_truth_test.py`) — только добавление
  bootstrap-блока, ничего не удалено. Накопительность соблюдена.
