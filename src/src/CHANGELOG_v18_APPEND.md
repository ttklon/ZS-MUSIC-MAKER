# CHANGELOG v18 — 2026-08-09

База: v17-consolidated. Правило сессии: умный инкрементальный аудит,
не полный endless-audit. Ничего не удалено, только добавлено/исправлено.

## Что сделано (реальный прогресс, не описание)

1. **NEW modules/vocal_fx.py** — настоящий vocal double-tracking +
   delay throw. Честный numpy-DSP (линейный ресемпл для детюна/растяжения,
   VAD для концов фраз, ping-pong delay). НЕ имитация, НЕ нейросеть.
   Закрывает backlog-задачу «vocal harmonizer/doubling для хитовости хука».
   Без soundfile -> ok=False + reason (никакого скрытого copy).

2. **orchestrator: новая стадия `_stage_vocal_fx`** — встроена между
   RVC и миксом. Если модуль недоступен/входа нет — честный bypass с
   пометкой fallback_used, пайплайн НЕ ломается, микс идёт на исходном
   вокале. Вокал до микса получает плотность double + воздух throw.

3. **sidechain.py: scipy отделён от numpy-импорта.** Раньше без scipy
   весь numpy-DSP отваливался и ducking-метрика молча становилась 0.
   Теперь: scipy есть -> butter/sosfilt; scipy нет -> честный numpy FFT
   brick-wall bandpass 30-200 Гц для onset-детекции бочки. Проверено:
   ducking 7.4 dB со scipy, 6.6 dB без scipy (оба > порога 3 dB из ТЗ).

4. **mixdown.py: честный статус matchering.** Раньше отсутствие
   matchering давало скрытый shutil.copy, который выглядел как мастеринг.
   Теперь full_mixdown/master_with_matchering_status возвращают
   used_matchering/fallback_used/engine — UI и логи не выдадут copy
   за мастеринг.

5. **tools/fallback_audit.py усилен:**
   - регресс-страж `sidechain_self_duck` (apply_sidechain(x,x)) — баг
     v16, когда бит дакался сам собой, больше не пройдёт незамеченным;
   - понимание метки ZSMM_NOT_RVC (легитимный pitch-shift для
     бэкинг-гармонии, НЕ подмена RVC) — убран ложный красный флаг;
   - детекция hard-refusal (deprecated-функция, которая raise
     RuntimeError и не вызывается) — pink-noise страж больше не флаг.
   **Итог аудита: red_flags = 0.**

6. **tools/smoke_v18.py** — 6 целевых проверок: vocal_fx реальный,
   vocal_fx встроен в оркестратор, sidechain без scipy, нет self-duck
   регресса, mixdown отдаёт честный статус, аудитор ловит self-duck
   и уважает маркеры. Результат: 6 PASS / 0 FAIL.

7. **smoke_v17: version-тест сделан версионно-нейтральным** — проверяет
   отсутствие drift (чтение из version.json через _load_version_info),
   а не конкретный номер версии. Иначе ломался бы при каждом бампе.

8. **run_all_smoke.sh/.bat** — добавлены smoke_v17 и smoke_v18
   (ранее раннеры гоняли только v9–v11).

## Честные статусы модулей после v18

| Модуль | Статус |
|--------|--------|
| main / CLI | REAL_PASS |
| analyzer / groove_extractor | REAL_PASS |
| arrangement_engine | REAL_PASS |
| beat_constructor | REAL_PASS |
| musicgen_texture | BLOCKED без audiocraft (hard-refusal, не stub) |
| lyrics_gen (LLMRouter) | PARTIAL (fallback = punch-lib, помечен) |
| voice_synth | PARTIAL (нужен silero/xtts/pyttsx3) |
| RVC | BLOCKED без .pth (pitch-shift fallback ЗАПРЕЩЁН) |
| **vocal_fx (double+throw)** | **REAL_PASS (NEW v18)** |
| mix + sidechain | REAL_PASS (+ numpy-fallback без scipy v18) |
| mastering (8 стендов) | REAL_PASS/PARTIAL |
| mixdown (legacy) | PARTIAL — честный статус (v18) |
| anti-neuro polish | REAL_PASS |
| stems (demucs) | BLOCKED без demucs |
| hit_scorer | REAL_PASS |
| release_pack | REAL_PASS |

## Smoke

- smoke_v17: 6/6 PASS (регрессий нет)
- smoke_v18: 6/6 PASS (новые функции)
- fallback_audit: red_flags = 0
- E2E non-dry: 10/15 стадий ok, 8/8 мастеров, 19 файлов релиза,
  verdict PARTIAL (честно: torch/audiocraft/demucs отсутствуют
  в песочнице, на ПК пользователя они ставятся через windows_build.bat)
