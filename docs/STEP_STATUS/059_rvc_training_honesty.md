# PLAN_v39 — ШАГ 059: RVC trainer pipeline

Проверен `rvc_trainer_v9` и исправлены два реальных состояния. Training jobs directory теперь создаётся до первой JSON записи; dry run завершает job как `done_dry` с явной записью, что **.pth model не произведён**. Ветка, где доступный trainer API завершился без верифицированного exported checkpoint, теперь возвращает `done_unverified`, а не `done`.

Это сохраняет dry CI/UI plan и progress callbacks, но исключает ложное заявление о готовой RVC model. Real RVC training по-прежнему требует external RVC runtime, GPU dataset preprocessing и верифицированный `.pth` output; они отсутствуют в sandbox.

На момент приёмки: `pytest tests/test_rvc_trainer.py -q` — **1 passed**; полный `pytest tests/ -q` — **127 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.
