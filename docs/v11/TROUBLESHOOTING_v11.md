# ZS Music Maker v11 — Troubleshooting

## Кодировка Windows cmd
Симптом: кракозябры, `UnicodeEncodeError: 'charmap'`.
Решение: `run_v11.bat` уже делает `chcp 866` + `PYTHONIOENCODING=utf-8`.
Ручной запуск: `set PYTHONIOENCODING=utf-8 && set PYTHONUTF8=1 && chcp 65001`.

## moviepy / ffmpeg
Симптом: `[video_edit_v11] moviepy not available` в логе.
Решение: `pip install moviepy imageio-ffmpeg`.
Fallback: v11 сам режет HOOK.wav + пишет ffmpeg-инструкцию.

## PySide6 не запускается
Симптом: `_try_pyside_wizard` = -1, каскад в v10.
Решение: `pip install PySide6==6.6.*`.

## KPI HARD_FAIL с missing files
Симптом: `release_files_missing: [flac, instrumental, ...]`.
Причина: v10 pipeline не создал часть форматов (или запустился fallback).
Решение: проверь `release_pack_v9.py`, установи `pydub`.

## RVC training слишком долго
Причина: неправильный HW-detect.
Решение: удали `data/hw_profile_v10.json`, запусти `python -m modules.hw_directml`.
