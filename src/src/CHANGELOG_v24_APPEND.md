# CHANGELOG v24 (append) — 2026-08-11

Build: `v24-wizard-recipe-mapping-2026-08-11`, based_on `v23`.

Цель сессии: устранить P0-дефект «фальшивой готовности» GUI → пайплайна,
не ломая существующий пайплайн (v23 остаётся рабочим, регрессий нет).

## Найдено аудитом (targeted, не полный)

* **P0 — рецепт визарда терялся целиком.** `app/gui/wizard.py` собирает recipe
  с ключами `preset`, `artist_name`, `bpm_override`, `aggression`,
  `duration_sec`, `user_lyrics_lines`, `voice_mode`, `quality_mode` и др.,
  но `run_full_pipeline` читал ТОЛЬКО `references`, `theme`, `genre`,
  `artist`. Итог: пользователь выбирал в GUI пресет, имя артиста, BPM,
  агрессию, длительность и вводил свой текст — а трек всегда собирался
  с дефолтами `drift_phonk` / `ZS Producer` / 128 bpm / LLM-текстом.
  Классическая «функция формально есть, реально не работает».

## Исправлено (app/core/orchestrator.py, run_full_pipeline)

1. **preset → genre + style_vector.** `preset` (tamam_like, brazilian_phonk,
   hyperpop_edit, lofi_drift, trap_ru) теперь маппится через
   `modules/presets.preset_to_style_vector()`: задаёт жанр, целевой BPM,
   тональность и prompt_hint. Если явный `genre` не задан — берётся из
   ключа пресета.

2. **artist_name → artist.** Имя артиста из первого шага визарда теперь
   попадает в `metadata.json` релиз-пакета (и на обложку/ID3/distrokid.xml).

3. **bpm_override пробивает всё.** Явный BPM из экспертных опций важнее
   и пресета, и авто-анализа: пишется в `_sv["target_bpm"]` и в `analysis`.

4. **aggression / duration_sec доезжают до бита.** Значения из визарда
   прокидываются в `plan` → `beat_constructor.construct_beat(...)`
   (агрессия ограничена 0..1, длительность — int).

5. **user_lyrics_lines имеет приоритет над генерацией.** Если пользователь
   ввёл свой текст на шаге «Текст», `_stage_lyrics` не дёргает LLM/template,
   а возвращает `provider='user_lyrics'` — свой текст идёт в voice_synth,
   metadata и lyrics.txt/lrc/srt как есть.

## Добавлено

* **tools/smoke_v24.py** — 7 проверок: preset применён, bpm_override побеждает,
  user_lyrics приоритетнее LLM, artist в metadata.json, duration доехала,
  регрессия пустого рецепта (дефолты 130 bpm / lyrics ok), версия 24.0.0.

## Проверка

* `smoke_v24.py`: **7/7 PASS** (см. вывод прогона).
* Ручной E2E-прогон с рецептом (preset=brazilian_phonk, bpm_override=150,
  duration=12, user_lyrics): beat.bpm=150, beat.duration≈12,
  lyrics.provider=user_lyrics, metadata.artist='Smoke Artist v24',
  verdict=PASS_WITH_FALLBACK, 15/15 стадий ok.

## Статусы (честно)

* wizard→pipeline mapping: **REAL_PASS** (было: молчаливая потеря рецепта)
* beat_constructor: REAL_PASS (numpy synth structured beat)
* mastering (numpy_dsp): REAL_PASS (K-weighted + EQ + limiter)
* texture: FALLBACK_ONLY (scaffold, не MusicGen; audiocraft недоступен в среде)
* voice_synth: FALLBACK_ONLY (rap_scaffold_numpy_v22; нет TTS/torch в среде)
* RVC: BLOCKED (нет .pth модели; честный блок, не pitch-shift-за-RVC)
* release_pack mp3/clips: FALLBACK_ONLY в песочнице (нет pydub/ffmpeg;
  на ПК с pydub+ffmpeg ветки отработают полноценно — код не тронут)
