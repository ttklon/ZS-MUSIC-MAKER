# PLAN_v39 — ШАГ 070: 15 APP_G регресс-сценариев

Добавлен `tools/regress_v39.py`, который детерминированно запускает 15 закреплённых CLI/pytest контрактов, сохраняет return code и output tail в `docs/REGRESS_v39.results.json`, а при unexpected failure возвращает non-zero. Machine report использует переносимые `python …` commands без sandbox-specific absolute paths.

Фактический прогон: **13 PASS, 2 BLOCKED, 0 FAIL**. Два BLOCKED случая — полный 13-role runtime и 300-second MusicGen generation — не имитировались: `torch/audiocraft/demucs/TTS/diffusers/transformers/llama_cpp` отсутствуют, а model weights/GPU в sandbox не заявлены. Все PASS сценарии перечислены с точной командой и границей contract в `docs/REGRESS_v39.md`.

Приёмка: `pytest tests/test_regress_v39.py -q` — 3 passed; runner — 13 PASS / 2 BLOCKED / 0 FAIL; report JSON валиден и portable. Полный `pytest tests/ -q` — **144 passed**; `compileall` успешно; AST-аудит — **0 dead imports**.
