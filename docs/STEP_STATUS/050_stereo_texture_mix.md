# PLAN_v39 — ШАГ 050: stereo textures в mix

`stage_music_stereo` уже создавал отдельный validated `texture_stereo.wav`, но этот артефакт не попадал в финальный mix. `stage_mix` теперь читает texture, при необходимости ресемплирует к beat sample rate, гарантирует stereo, смешивает пересечение длительностей и рассчитывает gain как **−18 dB относительно RMS beat**. После texture blend и после vocal blend сохраняется peak ceiling 0.98.

| Состояние | Result |
|---|---|
| Texture output существует | Добавляется в beat mix; `texture_mixed=True`. |
| Texture отсутствует/skipped | Beat/vocal mix сохраняет прежнее поведение; `texture_mixed=False`. |
| Sample-rate/channel mismatch | Texture ресемплируется и upmix-ится до stereo до gain staging. |

Проверка: `pytest tests/ -q` — **116 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**. MusicGen stereo weights в sandbox отсутствуют, поэтому real texture generation остаётся **BLOCKED**; mix contract реализован для любого валидного stereo texture artifact.
