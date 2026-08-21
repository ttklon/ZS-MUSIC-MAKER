# PLAN_v39 — ШАГ 061: AI detector и достоверность отчёта

`ai_detector_pro.analyze_track()` теперь возвращает `ai_risk_percent` (0–100) как явное преобразование существующей 9-metric audio heuristic score. В output добавлен `metric_type=internal_audio_heuristic_not_ai_attribution`, поэтому отчёт не выдаёт spectral/RMS/dynamics признаки за способность определить происхождение аудио или доказать, что трек создан AI.

Synthetic WAV regression проверяет bounded risk percentage, declared metric type и наличие vocal liveliness metric. На момент приёмки: `pytest tests/test_ai_detector.py -q` — **1 passed**; полный `pytest tests/ -q` — **129 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.

> Цель внутренней метрики — подсказать, где mix/вокал выглядит излишне ровным или шаблонным. Порог «≤30%» может служить internal quality target, но не является объективным доказательством «человечности» или гарантирующим результатом humanization.
