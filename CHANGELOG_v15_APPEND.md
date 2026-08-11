# ZS Music Maker v15 — CHANGELOG APPEND

**Дата:** 2026-08-08
**База:** v14-consolidated (ceruv5.zip, SHA-256 8eecd55c…)

## P1 закрытые в v15

### P1.34 / P1.35 — Полный релиз-пакет (~38 файлов) ✅
Новый модуль `modules/release_pack_full.py` (756 строк).
Прогон в песочнице: **29 файлов без masters_map**, ~37 с полным набором
мастеров:
- audio: full_master_streaming.wav, hires 48/24, FLAC, MP3 320
- 8 стендов мастеринга (streaming/car/club/tiktok/airpods/bt/hp/mon)
- stems/{drums,bass,vocals,other}.wav (band-split fallback если demucs нет)
- instrumental.wav + acapella.wav
- tiktok_15/30/60.m4a, reels_30.m4a, shorts_60.m4a (fallback: mp3 в m4a)
- lyrics.txt / .lrc / .srt
- metadata.json, licenses.txt, hit_report.md, production_notes.md,
  distrokid.xml, spotify_description.txt, youtube_description.html,
  vk_prefill.txt, shazam.jsonld
- cover.png 3000×3000 + cover.jpg 1400×1400
- ID3v2.4 теги (TIT2, TPE1, TALB, TCON, TBPM, TKEY, TSRC, TPUB, TDRC, APIC)

### P1.19-P1.22 — LLM модуль ✅
Новый `modules/llm_clients_v15.py` (388 строк).
Роутер `LLMRouter`: OpenRouter → Grok → Gemini → Ollama → local_template.
- Реальные HTTP-вызовы к 4 провайдерам
- Шифрование ключей `cryptography.fernet` (PBKDF2 200k)
- Логирование попыток (без ключей!)
- Local fallback: punch-lib RU/EN + template
- Прогон в песочнице: все 4 провайдера честно ответили `no_api_key`
  / `connection_refused`, отработал local_template

### P1.10 — 15 обязательных промптов ✅
`data/prompts/*.prompt.txt` × 15:
lyrics_verse, lyrics_chorus, lyrics_hook, lyrics_adlibs,
track_title, track_description_short/long, hashtags_tiktok/insta/youtube,
cover_art_prompt, youtube_description, spotify_description,
trend_analysis, slang_extraction.

### P1.20 — A/B сравнение ✅
`tools/ab_compare.py` (193 строки).
LUFS, True Peak, RMS, stereo width, spectrogram PNG.
Прогон: сравнение user vs ref → JSON + spec_user.png/spec_ref.png/ab_combined.png.

### P2.47 — GitHub scout ✅
`agents/github_scout.py` (191 строка).
Реальный API GitHub, ищет 10 тем (rvc, musicgen, demucs, samples, mastering,
hit_score, tts, accel, stt, dataset). Кэширует в `data/github_cache.json`.
Прогон в песочнице: **реально нашёл Applio (3566★), TTS-Audio-Suite (1143★)** и др.
+ хардкод `MANDATORY_REPOS` (11 репо: Applio/audiocraft/demucs/matchering/
pedalboard/faster-whisper/TTS/bark/silero/rnnoise/onnxruntime-directml).

## Патчи оркестратора

- `_stage_lyrics` теперь идёт через `LLMRouter` → template fallback
- `_stage_release_pack` вызывает `release_pack_full.build_pack` (~38 файлов),
  fallback → `release_pack_v13` → `_minimal_release_pack`
- Прокидываются `masters_map`, `stems_map`, `lyrics_text`, `stages`, `hit_metrics`

## Результат E2E (реальный, non-dry)

verdict: PARTIAL (audiocraft/demucs/TTS всё ещё BLOCKED в песочнице)
duration: 6.4 сек, 14 стадий.

Артефакты:
- output/audit_v14/v15_final_e2e_*/release/ — 29 файлов
- output/audit_v15/e2e_final.json
- output/audit_v15/ab/ab_report.json + spec_*.png
- data/github_cache.json (реальные данные с GitHub)

## Файлы добавлены (v15)

| Файл | Строк |
|------|-------|
| modules/release_pack_full.py | 756 |
| modules/llm_clients_v15.py | 388 |
| agents/github_scout.py | 191 |
| tools/ab_compare.py | 193 |
| data/prompts/*.prompt.txt | 15 файлов |
| CHANGELOG_v15_APPEND.md | этот |
| version.json | обновлён 14→15 |

**Ничего не удалено, ничего не переименовано.** Все v14 файлы на месте.
