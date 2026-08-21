# АУДИТ ФАЙЛА: `app/core/orchestrator_ai.py`

**LOC:** 470  |  **Размер:** 22517 байт  |  **Проблем:** 13  |  **Risk score:** 9

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 3 | `__future__.annotations` | from |
| 4 | `json` | import |
| 4 | `math` | import |
| 4 | `shutil` | import |
| 5 | `pathlib.Path` | from |
| 6 | `app.core.logger.app_logger` | from |
| 7 | `app.ai.sequential_runner.SequentialAIRunner` | from |
| 7 | `app.ai.sequential_runner.AIStage` | from |
| 8 | `app.ai.prompts` | from |
| 9 | `app.ai.llm_service` | from |
| 10 | `app.ai.quality.validate_audio_artifact` | from |
| 10 | `app.ai.quality.validate_lyrics` | from |
| 10 | `app.ai.quality.validate_metadata_json` | from |
| 10 | `app.ai.quality.validate_rvc_artifact` | from |
| 10 | `app.ai.quality.validate_stereo_texture` | from |
| 10 | `app.ai.quality.validate_vocal_artifact` | from |
| 18 | `modules.artist_dossier.DossierManager` | from |
| 22 | `re` | import |
| 30 | `soundfile` | import |
| 134 | `config.settings.get_settings` | from |
| 260 | `numpy` | import |
| 260 | `soundfile` | import |
| 260 | `torch` | import |
| 333 | `re` | import |
| 404 | `modules.mastering_ai.master_ai` | from |
| 412 | `modules.cover_art_ai.render_cover_ai` | from |
| 77 | `modules.voice_synth.synth` | from |
| 157 | `app.core.hw_autodetect.get_hardware_profile` | from |
| 375 | `numpy` | import |
| 375 | `soundfile` | import |
| 424 | `torch` | import |
| 424 | `librosa` | import |
| 424 | `numpy` | import |
| 186 | `modules.lyrics_gen` | from |
| 238 | `modules.cyber_synth.CyberSynth` | from |
| 384 | `librosa` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 21 | `_slug` | 3 | 2 | ❌ |
| 27 | `render_stereo_texture` | 21 | 4 | ✅ |
| 51 | `render_xtts_vocal` | 19 | 5 | ✅ |
| 73 | `render_voice_synth_fallback` | 22 | 5 | ✅ |
| 98 | `render_rvc_vocal` | 30 | 5 | ✅ |
| 131 | `run_ai_pipeline` | 339 | 78 | ❌ |
| 155 | `stage_hw` | 5 | 1 | ❌ |
| 162 | `stage_dossier_load` | 5 | 1 | ❌ |
| 169 | `stage_lyrics` | 32 | 8 | ❌ |
| 203 | `stage_metadata` | 28 | 7 | ❌ |
| 233 | `stage_music` | 65 | 16 | ❌ |
| 300 | `stage_music_stereo` | 25 | 3 | ✅ |
| 327 | `stage_vocal` | 18 | 6 | ❌ |
| 347 | `stage_rvc` | 18 | 8 | ❌ |
| 367 | `stage_mix` | 30 | 13 | ❌ |
| 399 | `stage_master` | 7 | 2 | ❌ |
| 408 | `stage_cover` | 6 | 3 | ❌ |
| 416 | `stage_tag` | 24 | 7 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 8 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 131** — public function 'run_ai_pipeline' без docstring

  ```
        129 | 
        130 | 
  >>>   131 | def run_ai_pipeline(project_id, wizard_state=None, out_root=None, dry_run=False):
        132 |     ws = dict(wizard_state or {})
        133 |     try:
  ```

- **строка 169** — public function 'stage_lyrics' без docstring

  ```
        167 |                 "track_dossier": mgr.get_track_dossier(artist_slug, ref_track_id) if ref_track_id else None}
        168 | 
  >>>   169 |     def stage_lyrics(handle, ctx):
        170 |         if dry_run:
        171 |             return {"ok": True, "lyrics": "[dry-run]", "source": "dry"}
  ```

- **строка 203** — public function 'stage_metadata' без docstring

  ```
        201 |                 "reason": quality["reason"]}
        202 | 
  >>>   203 |     def stage_metadata(handle, ctx):
        204 |         lyrics = (ctx["sink"].get("lyrics") or {}).get("lyrics") or ""
        205 |         fallback = {
  ```

- **строка 233** — public function 'stage_music' без docstring

  ```
        231 |         return js
        232 | 
  >>>   233 |     def stage_music(handle, ctx):
        234 |         if dry_run:
        235 |             return {"ok": True, "beat_path": "[dry]"}
  ```

- **строка 327** — public function 'stage_vocal' без docstring

  ```
        325 |         return result
        326 | 
  >>>   327 |     def stage_vocal(handle, ctx):
        328 |         if dry_run:
        329 |             return {"skipped": "dry-run"}
  ```

- **строка 347** — public function 'stage_rvc' без docstring

  ```
        345 |         return fallback
        346 | 
  >>>   347 |     def stage_rvc(handle, ctx):
        348 |         if dry_run:
        349 |             return {"skipped": "dry-run"}
  ```

- **строка 367** — public function 'stage_mix' без docstring

  ```
        365 |         )
        366 | 
  >>>   367 |     def stage_mix(_, ctx):
        368 |         beat = (ctx["sink"].get("music") or {}).get("beat_path")
        369 |         vocal = ((ctx["sink"].get("rvc") or {}).get("vocal_path")
  ```

- **строка 416** — public function 'stage_tag' без docstring

  ```
        414 |                                mood=ws["mood"], out_path=str(out_root / "cover.png"))
        415 | 
  >>>   416 |     def stage_tag(bundle, ctx):
        417 |         if bundle is None:
        418 |             return {"skipped": "no clap"}
  ```

### HIGH_COMPLEXITY — 2 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 131** — run_ai_pipeline: сложность ≈ 78 (>15)

  ```
        129 | 
        130 | 
  >>>   131 | def run_ai_pipeline(project_id, wizard_state=None, out_root=None, dry_run=False):
        132 |     ws = dict(wizard_state or {})
        133 |     try:
  ```

- **строка 233** — stage_music: сложность ≈ 16 (>15)

  ```
        231 |         return js
        232 | 
  >>>   233 |     def stage_music(handle, ctx):
        234 |         if dry_run:
        235 |             return {"ok": True, "beat_path": "[dry]"}
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 3** — import 'annotations' не используется в теле файла

  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - app/core/orchestrator_ai.py (v38 GOD MODE 4.0 AI)"""
  >>>     3 | from __future__ import annotations
          4 | import json, math, shutil
          5 | from pathlib import Path
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 131** — run_ai_pipeline: 339 LOC (>100) — декомпозиция

  ```
        129 | 
        130 | 
  >>>   131 | def run_ai_pipeline(project_id, wizard_state=None, out_root=None, dry_run=False):
        132 |     ws = dict(wizard_state or {})
        133 |     try:
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 265** — except: pass — тихое подавление ошибок

  ```
        263 |         try:
        264 |             model.set_generation_params(duration=20, top_k=250, temperature=1.0, cfg_coef=3.0)
  >>>   265 |         except Exception:
        266 |             pass
        267 |         n_chunks = max(1, math.ceil(ws["duration_sec"] / 20))
  ```
