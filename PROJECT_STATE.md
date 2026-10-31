# PROJECT_STATE — ZS Music Maker

> **Версия:** 41.0.0-alpha.1 (alpha-рефакторинг v41)
> **Источник цифр:** `python tools/readiness.py --json` + `git ls-files`.

## Инвентаризация

| Показатель | Значение |
|---|---:|
| Версионированных файлов в git | 320 |
| Production Python-модулей | 127 |
| `REAL_PASS` (парсится + есть статическая ссылка) | 125 |
| `PLANNED` (нет статической ссылки) | 2 |
| `REAL_FAIL` (syntax error) | 0 |
| Тестов (`pytest tests/`) | 287 passed |
| Smoke: аудио / God Mode | 6/6 / 8/8 |
| Честная готовность (`--readiness`) | 65% |

`REAL_PASS` здесь — статическая связность (парсится + есть ссылка), а не
утверждение о реальном inference тяжёлых моделей.

## Состояние по областям

| Область | Статус | Основание |
|---|---|---|
| CLI, визард, оркестраторы | работает | 287 тестов, smoke_god 8/8 |
| Аудио-ядро (mix, sidechain, mastering) | работает | smoke_audio 6/6, true-peak ≤ −1 dBTP |
| Вокал: своя запись + чистка + FX | работает | `modules/voice_recording`, `voice_cleaner`, `vocal_fx` |
| TTS-движки (Silero/XTTS/bark/pyttsx3) | работает при установке | `modules/voice_synth`, честный BLOCKED |
| RVC | BLOCKED | нет `.pth` весов в репозитории |
| MusicGen / Demucs / SDXL / CLAP / LLM | BLOCKED | тяжёлые пакеты и веса не входят в базовую установку |
| Windows EXE (PyInstaller) | NOT_TESTED в Linux-сэндбоксе | собирается на windows-latest CI |
| Релиз-пакет, ISRC, дистрибуция | работает | `release_pack_full`, `distribution` |

## Что удалено в v41 (без потери функций)

- Legacy-патчи `orchestrator_v8..v12_patch` и весь их каскад.
- 1168 файлов `docs/` (52 МБ сгенерированных дампов): `PLAN_v38_AI_MEGA.txt` (11 МБ),
  `PLAN_v39/**` (1017 файлов, 37 МБ), `STEP_STATUS` (144), `LICENSES`, `WIKI`,
  `REGRESS_v39`, `PLAN_v39_EXEC_REPORT`, `SESSION_LOG.md`.
- Мёртвые модули без ссылок: `training_texts`, `cover_gen`, `model_manager`,
  `wizard_v8_extensions`, `beat_gen`, `phonk_engine_v2`, `musical_intelligence`,
  `genre_expansion_100`, `global_audit_fixer`, `provenance`, `ui/tutorial`,
  `master_pipeline_v12`, `wizard_v12_integration`, `release_pack_v9`, `mastering_v9`,
  `orchestrator_v*_patch`.
- Инструменты, существовавшие только ради удалённых документов: `plan_integrity`,
  `regress_v39`, `release_preflight`, `deep_audit_v40*`, `ab_compare`, `lazy_dirs_patch`,
  `p0_truth_test`, `populate_cover_prompts`, `validate_final_track`.
- Трекаемое пользовательское состояние (`lyric_vault/*`, `voice_vault/*`,
  `data/hw_profile.json`, `data/tutorial_settings.json`, `training_texts/progress.json`,
  `data/kpi_history_seed`).
- 6 корневых bat/ps1/sh-скриптов → `scripts/setup.cmd`, `scripts/run.cmd`,
  `scripts/verify.cmd`, `scripts/make_shortcut.ps1`, `scripts/run.sh`.

## Переименования (v-суффиксы убраны)

`anti_neuro_v10→anti_neuro`, `llm_clients_v15→llm`, `lyric_vault_v10→lyric_vault`,
`voice_vault_v9→voice_vault`, `rvc_trainer_v9→rvc_trainer`, `tiktok_edit_v9→tiktok_edit`,
`video_edit_v11→video_edit`, `distribution_export_v11→distribution`,
`expert_mode_v11→expert_mode`, `health_v12→health`, `kpi_dashboard_v12→kpi_dashboard`,
`hit_kpi_monitor_v11→kpi_monitor`, `self_diag_v13→self_diag`, `onboarding_tour→onboarding`,
`theme_v12→theme`, `real_e2e_v14→tools/e2e`, `smoke_v26→tools/smoke_audio`,
`smoke_v29→tools/smoke_god`, `cli_contract→tools/cli`.

## Дальше (по `docs/PLAN_v41_MASTER.md`)

1. Семантическое слияние семейств: mastering (5 файлов → 1), release (3 → 1),
   lyrics (3 → 1), sources (4 → 2), anti-neuro (2 → 1).
2. Ядро пайплайна: единый `StageResult`, кэш стадий, `--seed/--resume/--only`.
3. Качество звука: сэмпловая база, humanize-грув, аранжировка, вокал своего голоса.
4. UX Windows 11: 5-шаговый визард, EXE, прогресс по стадиям.
