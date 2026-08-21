# PLAN_v39 — ШАГ 058: release export, fingerprints и archive

`export_release()` дополнен криптографическим artifact inventory. После формирования master/instrumental/acapella/metadata/lyrics/release notes вычисляется SHA-256 каждого существующего package file, хэши сохраняются в `manifest.json`, затем папка релиза архивируется в `release.zip`. Existing metadata JSON по-прежнему содержит сгенерированный ISRC, а MP3/FLAC ID3 tagging сохраняется как optional capability.

Новый test собирает release из реального test WAV и проверяет ZIP, presence 64-character SHA-256 для master WAV и non-empty ISRC. Test не требует ffmpeg/MP3 encoder: optional transcodes могут отсутствовать, не подменяя обязательные WAV/metadata/manifest/archive артефакты.

На момент приёмки: `pytest tests/test_release_export.py -q` — **1 passed**; полный `pytest tests/ -q` — **126 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.
