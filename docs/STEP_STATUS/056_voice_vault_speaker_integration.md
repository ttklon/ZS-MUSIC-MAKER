# PLAN_v39 — ШАГ 056: Voice Vault и XTTS speaker WAV

Voice Vault получил безопасный `select_speaker_wav(style=None)`: он выбирает существующий clean clip по SNR, исключает clipped recordings и при отсутствии style match делает fallback к любому допустимому clip. `stage_vocal` теперь использует явный `wizard_state.speaker_wav` приоритетно, иначе запрашивает лучший Voice Vault clip для `vocal_style` и передаёт его в XTTS adapter.

В ходе проверки найден и исправлен реальный intake defect: при первом добавлении записи `add_recording()` пытался копировать WAV до создания `voice_vault/`. Каталог теперь создаётся до copy; index persist остаётся отдельной гарантией.

Добавлены real WAV regressions для intake/index creation, speaker selection и reject clipped entry. На момент приёмки: `pytest tests/test_voice_vault.py -q` — **2 passed**; полный `pytest tests/ -q` — **123 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.
