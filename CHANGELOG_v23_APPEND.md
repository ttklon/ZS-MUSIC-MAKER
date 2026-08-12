# CHANGELOG v23 (append) — 2026-08-11

Build: `v23-honest-dsp-lazy-import-2026-08-11`, based_on `v22`.

Цель сессии: убрать фальшивую готовность и скрытые дефекты запуска/импорта,
не ломая существующий пайплайн (v22 остаётся рабочим, регрессий нет).

## Исправлено

1. **modules/voice_convert.py — lazy-mkdir (P2, скрытый дефект).**
   Раньше `import voice_convert` создавал каталоги `voice_vault/`, `models/rvc/`,
   `output/voice_final/` как побочный эффект — это нарушало собственную политику
   v22 «no import side effects» и засоряло диск при любом импорте. Каталоги теперь
   создаются лениво через `_ensure_dirs()` в точках записи (`_save_index`,
   `add_recording`, `polish_vocal_offline`). Проверено smoke: `CREATED: []`.

2. **tools/real_e2e_v14.py — sys.path fix (P1, ломал запуск).**
   При прямом запуске `python3 tools/real_e2e_v14.py` падал с
   `ModuleNotFoundError: No module named 'app'` (tools/ попадал в sys.path вместо
   корня). Добавлен `sys.path.insert(0, str(ROOT))` ДО импорта `app`. Прямой
   запуск теперь работает: 15/15 стадий, verdict PASS_WITH_FALLBACK.

3. **modules/mastering.py — честный статус + K-взвешенная громкость (P0, качество).**
   * Реальный numpy-DSP путь (EQ + loudness + limiter) больше НЕ помечается
     `fallback_used=True` — это честная обработка, а не заглушка. Теперь
     `fallback_used=False` с пояснением движка. Fallback-стадий в E2E: 6 → 5.
   * Оценка громкости заменена с наивного `RMS − 3 dB` (занижал громкость и
     загонял сигнал в избыточный гейн перед tanh-лимитером) на упрощённое
     K-взвешивание ITU-R BS.1770 (high-shelf пред-фильтр + HP38 перед RMS).
     На тестовом тоне 1 кГц: было −12.03, стало −10.61 (истинное ~ −9 LUFS).

4. **app/core/orchestrator.py — честный texture-scaffold (P1, честность).**
   Раньше при недоступном MusicGen `_stage_texture` отдавал пустой `path=""` при
   `fallback_used=True` — в трек не попадало ничего, хотя отчёт намекал на
   наличие текстуры. Теперь `_texture_scaffold()` синтезирует реальный
   низкоуровневый ambient-scaffold (drone-пэд 110 Hz + noise-bed + огибающая),
   записывает WAV и честно помечает `synthetic=True, engine='texture_scaffold_v23'`.
   Это скелет атмосферы, НЕ выдаётся за нейро-текстуру.

## Добавлено

* **tools/smoke_v23.py** — 6 проверок пакета (lazy-import, sys.path, K-weighted,
  honest mastering label, real texture wav, version). Результат: 6/6 PASS.

## Проверка

* `smoke_v23.py`: **6/6 PASS**.
* `smoke_v22.py` (регрессия): 7/8 PASS; единственный FAIL — `version_v22`,
  который жёстко закреплён за `version.json==22.0.0` и по определению не проходит
  после честного бампа до 23.0.0 (не является дефектом логики).
* `tools/real_e2e_v14.py` прямой запуск: PASS_WITH_FALLBACK, 15/15 стадий,
  8/8 мастеров, 27 файлов релиз-пакета, red flags: {}.

## Статусы (честно)

* beat_constructor: REAL_PASS (numpy synth structured beat)
* mastering (numpy_dsp): REAL_PASS (K-weighted + EQ + limiter), не fallback
* texture: FALLBACK_ONLY (scaffold, не MusicGen; audiocraft недоступен в среде)
* voice_synth: FALLBACK_ONLY (rap_scaffold_numpy_v22; нет TTS/torch в среде)
* RVC: BLOCKED (нет .pth модели; честный блок, не pitch-shift-за-RVC)
* stems (demucs): BLOCKED (тяжёлая зависимость; честный блок)

## Осталось на следующий прогон (приоритет)

1. Поднять реальный TTS (silero/pyttsx3) на ПК — снять BLOCKED с вокала.
2. Установить и проверить RVC-инференс с реальной .pth моделью.
3. Проверить pedalboard/pyloudnorm для точного LUFS-мастеринга (сейчас numpy).
4. Прогнать полный E2E с реальными heavy-движками (musicgen/demucs) на целевом
   железе (RX 580) и снять соответствующие caps в readiness (59% -> выше).
