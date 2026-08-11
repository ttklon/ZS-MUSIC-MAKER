# CHANGELOG v21 APPEND

- P0: verdict-логика больше не путает honest BLOCKED (нет demucs/RVC/TTS/MusicGen) с симуляцией. Раньше любой baseline-прогон давал ложный BLOCKED_SIMULATION + percent=60.
- P0: `_stage_rvc` и `_stage_stems` при честном BLOCKED отдают ok=True + blocked=True.
- P0: если RVC blocked, downstream берёт исходный voice_wav — vocal_fx/mix не теряют вокал.
- P1: beat_constructor не создаёт output/beats при импорте (убран side-effect).
- P1: release_pack_full помечает placeholder ISRC/UPC в production_notes.
- P1: production_notes показывает [fallback]/[BLOCKED]/[synthetic] теги по стадиям.
- Добавлен tools/smoke_v21.py.
