# PLAN_v39 — ШАГ 069: PROJECT_STATE и readiness

`tools/readiness.py` перестроен на фактические сигналы. Он получает список versioned production `.py` через `git ls-files` (с filesystem fallback для source archive), строит статическую AST inventory, сохраняет совместимый `compute() -> (percent, details)` JSON и добавляет `module_inventory`. Новый режим `--inventory-markdown` воспроизводимо формирует matrix для PROJECT_STATE.

Пустые `try: status=REAL_PASS` dependency probes удалены. Audio/release runtime теперь реально проверяют import optional packages; MusicGen/Demucs/Matchering/Pedalboard/pyloudnorm остаются BLOCKED в sandbox, а не ошибочно зелёными. Устаревшие v14 markers в testing probes заменены существующими `smoke_v26`, `smoke_v29`, pytest и AST audit.

PROJECT_STATE полностью заменён snapshot-ом v39.9.0. Его matrix содержит **147/147** tracked production modules: 140 `REAL_PASS` (static signal), 0 `REAL_FAIL`, 7 `PLANNED`; runtime statuses отдельно описывают BLOCKED optional engines. Это не утверждает реальный inference без weights.

Приёмка: `python tools/readiness.py` вернул валидный JSON, `tracked_modules=147` совпал с 147 module rows PROJECT_STATE; новые inventory tests прошли. Полный `pytest tests/ -q` — **141 passed**; `compileall` успешно; AST-аудит — **0 dead imports**.
